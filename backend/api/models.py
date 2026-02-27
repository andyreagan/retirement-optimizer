from django.db import models
from django.contrib.auth.models import User
import json

class Person(models.Model):
    """Model to represent a person in the retirement scenario"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    name = models.CharField(max_length=100)
    current_age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    birth_year = models.IntegerField()  # Calculated field for calendar year tracking
    
    def save(self, *args, **kwargs):
        # Calculate birth year if not provided
        if not self.birth_year:
            from datetime import datetime
            current_year = datetime.now().year
            self.birth_year = current_year - self.current_age
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.gender}, age {self.current_age})"

class RetirementScenario(models.Model):
    """Model to store retirement scenario parameters"""
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Planning parameters
    start_year = models.IntegerField(default=2025)  # Calendar year to start projection
    filing_status = models.CharField(max_length=50, choices=[
        ('single', 'Single'),
        ('married_filing_jointly', 'Married Filing Jointly')
    ], default='single')
    
    # Legacy fields for backward compatibility
    start_age = models.IntegerField(null=True, blank=True)
    death_age = models.IntegerField(null=True, blank=True)
    annual_income = models.TextField(default='[]')  # JSON array
    annual_expenses = models.TextField(default='[]')  # JSON array
    
    # Store complete request data for reloading
    request_data = models.TextField(default='{}')  # JSON object of full request
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_annual_income(self):
        return json.loads(self.annual_income)
    
    def set_annual_income(self, value):
        self.annual_income = json.dumps(value)
    
    def get_annual_expenses(self):
        return json.loads(self.annual_expenses)
    
    def set_annual_expenses(self, value):
        self.annual_expenses = json.dumps(value)
    
    def get_request_data(self):
        return json.loads(self.request_data)
    
    def set_request_data(self, value):
        self.request_data = json.dumps(value)
    
    def __str__(self):
        return f"{self.name} - Age {self.start_age} to {self.death_age}"

class AccountConfiguration(models.Model):
    """Model to store account configurations for a scenario"""
    ACCOUNT_TYPES = [
        ('401k', '401k'),
        ('roth_ira', 'Roth IRA'),
        ('brokerage', 'Brokerage'),
        ('hsa', 'HSA'),
    ]
    
    scenario = models.ForeignKey(RetirementScenario, on_delete=models.CASCADE, related_name='accounts')
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Account-specific parameters stored as JSON
    parameters = models.TextField(default='{}')  # JSON object
    
    def get_parameters(self):
        return json.loads(self.parameters)
    
    def set_parameters(self, value):
        self.parameters = json.dumps(value)
    
    def __str__(self):
        return f"{self.scenario.name} - {self.account_type}: ${self.initial_balance}"

class ScenarioPerson(models.Model):
    """Model to link people to scenarios"""
    scenario = models.ForeignKey(RetirementScenario, on_delete=models.CASCADE, related_name='people')
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)  # For tax filing purposes
    
    class Meta:
        unique_together = ['scenario', 'person']

class CashFlowItem(models.Model):
    """Model to store individual income/expense items"""
    CASH_FLOW_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    scenario = models.ForeignKey(RetirementScenario, on_delete=models.CASCADE, related_name='cash_flow_items')
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=CASH_FLOW_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_age = models.IntegerField()
    end_age = models.IntegerField()
    
    # Link to a specific person (optional, for person-specific cash flows)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True)
    
    # Optional: inflation adjustment, growth rate, etc.
    annual_adjustment = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)  # e.g., 0.03 for 3%
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        person_str = f" ({self.person.name})" if self.person else ""
        return f"{self.scenario.name} - {self.name}{person_str} ({self.type}): ${self.amount} from age {self.start_age} to {self.end_age}"
    
    class Meta:
        ordering = ['start_age', 'type', 'name']

class UsageEvent(models.Model):
    """Track feature usage events (no limits enforced, just analytics)"""
    EVENT_TYPES = [
        ('projection_run', 'Projection Run'),
        ('scenario_saved', 'Scenario Saved'),
        ('monte_carlo_run', 'Monte Carlo Run'),
        ('excel_export', 'Excel Export'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    metadata = models.TextField(default='{}')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_metadata(self):
        return json.loads(self.metadata)
    
    def set_metadata(self, value):
        self.metadata = json.dumps(value)
    
    def __str__(self):
        return f"{self.user.username} - {self.event_type} at {self.created_at}"


class ProjectionResult(models.Model):
    """Model to store projection results"""
    scenario = models.OneToOneField(RetirementScenario, on_delete=models.CASCADE, related_name='result')
    
    # Results stored as JSON
    yearly_data = models.TextField()  # JSON array of yearly results
    summary_stats = models.TextField()  # JSON object with summary statistics
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_yearly_data(self):
        return json.loads(self.yearly_data)
    
    def set_yearly_data(self, value):
        self.yearly_data = json.dumps(value)
    
    def get_summary_stats(self):
        return json.loads(self.summary_stats)
    
    def set_summary_stats(self, value):
        self.summary_stats = json.dumps(value)
    
    def __str__(self):
        return f"Results for {self.scenario.name}"
