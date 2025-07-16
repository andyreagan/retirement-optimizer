from django.urls import path
from . import views

urlpatterns = [
    path('projection/', views.run_projection, name='run_projection'),
    path('monte-carlo/', views.run_monte_carlo, name='run_monte_carlo'),
    path('scenarios/', views.get_scenarios, name='get_scenarios'),
    path('scenarios/<int:scenario_id>/', views.delete_scenario, name='delete_scenario'),
    path('scenarios/<int:scenario_id>/results/', views.get_scenario_results, name='get_scenario_results'),
    path('export/excel/', views.export_to_excel, name='export_to_excel'),
    path('scenarios/<int:scenario_id>/export/excel/', views.export_scenario_to_excel, name='export_scenario_to_excel'),
]