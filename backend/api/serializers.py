from rest_framework import serializers
from .models import RetirementScenario, AccountConfiguration, ProjectionResult, CashFlowItem, Person, ScenarioPerson

class AccountConfigurationSerializer(serializers.ModelSerializer):
    parameters = serializers.JSONField()
    
    class Meta:
        model = AccountConfiguration
        fields = ['account_type', 'initial_balance', 'parameters']

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['name', 'current_age', 'gender', 'birth_year']
        read_only_fields = ['birth_year']

class CashFlowItemSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source='person.name', read_only=True, required=False)
    
    class Meta:
        model = CashFlowItem
        fields = ['name', 'type', 'amount', 'start_age', 'end_age', 'annual_adjustment', 'person_name']

class RetirementScenarioSerializer(serializers.ModelSerializer):
    accounts = AccountConfigurationSerializer(many=True, required=False)
    cash_flow_items = CashFlowItemSerializer(many=True, required=False)
    people = PersonSerializer(many=True, required=False)
    annual_income = serializers.JSONField(required=False)
    annual_expenses = serializers.JSONField(required=False)
    
    class Meta:
        model = RetirementScenario
        fields = ['id', 'name', 'start_year', 'filing_status', 
                 'start_age', 'death_age', 'annual_income', 'annual_expenses', 
                 'accounts', 'cash_flow_items', 'people']
    
    def create(self, validated_data):
        accounts_data = validated_data.pop('accounts', [])
        cash_flow_items_data = validated_data.pop('cash_flow_items', [])
        people_data = validated_data.pop('people', [])
        scenario = RetirementScenario.objects.create(**validated_data)
        
        for account_data in accounts_data:
            AccountConfiguration.objects.create(scenario=scenario, **account_data)
        
        for person_data in people_data:
            person, created = Person.objects.get_or_create(**person_data)
            ScenarioPerson.objects.create(scenario=scenario, person=person)
        
        for cash_flow_data in cash_flow_items_data:
            CashFlowItem.objects.create(scenario=scenario, **cash_flow_data)
        
        return scenario

class ProjectionResultSerializer(serializers.ModelSerializer):
    yearly_data = serializers.JSONField()
    summary_stats = serializers.JSONField()
    
    class Meta:
        model = ProjectionResult
        fields = ['yearly_data', 'summary_stats', 'created_at']

class ProjectionRequestSerializer(serializers.Serializer):
    """Serializer for projection requests"""
    name = serializers.CharField(max_length=200)
    start_year = serializers.IntegerField(min_value=2020, max_value=2100, required=False)
    filing_status = serializers.ChoiceField(choices=[
        ('single', 'Single'),
        ('married_filing_jointly', 'Married Filing Jointly')
    ])
    
    # People in the scenario
    people = PersonSerializer(many=True, required=False)
    
    # Support both old and new formats for backward compatibility
    start_age = serializers.IntegerField(min_value=18, max_value=100, required=False)
    death_age = serializers.IntegerField(min_value=18, max_value=120, required=False)
    annual_income = serializers.ListField(child=serializers.FloatField(), required=False)
    annual_expenses = serializers.ListField(child=serializers.FloatField(), required=False)
    
    # New format
    cash_flow_items = CashFlowItemSerializer(many=True, required=False)
    accounts = AccountConfigurationSerializer(many=True)
    
    def validate(self, data):
        # Determine if using new multi-person format or old single-person format
        using_people = 'people' in data  # Check if people key exists (even if empty)
        using_old_format = 'start_age' in data and 'death_age' in data
        
        if using_people:
            # New multi-person format validation
            if not data.get('start_year'):
                from datetime import datetime
                data['start_year'] = datetime.now().year
            
            # Validate people - if empty, use default single person with defaults
            if len(data['people']) == 0:
                # Fall back to default single person format
                data['start_age'] = 25
                data['death_age'] = 100
            
            # Validate cash flow items against people ages
            if 'cash_flow_items' in data and data['cash_flow_items']:
                for item in data['cash_flow_items']:
                    # For now, allow any age range - we'll handle it in the projection logic
                    if item['start_age'] > item['end_age']:
                        raise serializers.ValidationError(
                            f"Cash flow item '{item['name']}' start age must be <= end age"
                        )
        
        elif using_old_format:
            # Old single-person format validation
            if data['death_age'] <= data['start_age']:
                raise serializers.ValidationError("Death age must be greater than start age")
            
            # If using old cash flow items format, validate them
            if 'cash_flow_items' in data and data['cash_flow_items']:
                for item in data['cash_flow_items']:
                    if item['start_age'] < data['start_age'] or item['end_age'] > data['death_age']:
                        raise serializers.ValidationError(
                            f"Cash flow item '{item['name']}' age range ({item['start_age']}-{item['end_age']}) "
                            f"must be within scenario age range ({data['start_age']}-{data['death_age']})"
                        )
                    if item['start_age'] > item['end_age']:
                        raise serializers.ValidationError(
                            f"Cash flow item '{item['name']}' start age must be <= end age"
                        )
            
            # If using old array format, validate arrays
            if 'annual_income' in data and data['annual_income']:
                num_years = data['death_age'] - data['start_age'] + 1
                if len(data['annual_income']) != num_years:
                    raise serializers.ValidationError(f"Annual income must have {num_years} values")
            
            if 'annual_expenses' in data and data['annual_expenses']:
                num_years = data['death_age'] - data['start_age'] + 1
                if len(data['annual_expenses']) != num_years:
                    raise serializers.ValidationError(f"Annual expenses must have {num_years} values")
        
        else:
            raise serializers.ValidationError("Either 'people' or 'start_age'/'death_age' must be provided")
        
        return data