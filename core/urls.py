from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('exercises/', views.ExercisesListView.as_view(), name='exercises_list'),
    
    # Automaton CRUD
    path('create/', views.AutomatonCreateView.as_view(), name='create_automaton'),
    path('create/dfa/', views.AutomatonCreateView.as_view(), name='create_dfa'),  # Legacy - redirects to unified create
    path('create/nfa/', views.AutomatonCreateView.as_view(), name='create_nfa'),  # Legacy - redirects to unified create
    path('automaton/<int:pk>/', views.AutomatonDetailView.as_view(), name='automaton_detail'),
    path('dfa/<int:pk>/', views.AutomatonDetailView.as_view(), name='dfa_detail'),  # Legacy - redirects to unified detail
    path('nfa/<int:pk>/', views.AutomatonDetailView.as_view(), name='nfa_detail'),  # Legacy - redirects to unified detail
    path('automaton/<int:pk>/edit/', views.AutomatonUpdateView.as_view(), name='automaton_update'),
    path('automaton/<int:pk>/delete/', views.AutomatonDeleteView.as_view(), name='automaton_delete'),
    
    # AJAX API endpoints
    path('api/automaton/<int:pk>/json/', views.get_automaton_json, name='get_automaton_json'),
    path('api/automaton/<int:pk>/symbols/', views.get_alphabet_symbols, name='get_alphabet_symbols'),
    path('api/automaton/<int:pk>/simulate/', views.simulate_string, name='simulate_string'),
    path('api/automaton/<int:pk>/add-state/', views.add_state, name='add_state'),
    path('api/automaton/<int:pk>/update-state/', views.update_state, name='update_state'),
    path('api/automaton/<int:pk>/delete-state/', views.delete_state, name='delete_state'),
    path('api/automaton/<int:pk>/add-transition/', views.add_transition, name='add_transition'),
    path('api/automaton/<int:pk>/delete-transition/', views.delete_transition, name='delete_transition'),
    
    # Advanced operations
    path('api/automaton/<int:pk>/to-dfa/', views.convert_nfa_to_dfa, name='convert_nfa_to_dfa'),
    path('api/automaton/<int:pk>/minimize/', views.minimize_dfa, name='minimize_dfa'),
    path('api/automaton/<int:pk>/is-dfa/', views.check_if_nfa_is_dfa, name='check_if_nfa_is_dfa'),
    path('api/automaton/<int:pk>/check-type/', views.check_fa_type, name='check_fa_type'),
    path('api/automaton/<int:pk>/enable-epsilon/', views.enable_epsilon, name='enable_epsilon'),
    # Legacy endpoints
    path('api/nfa/<int:pk>/to-dfa/', views.convert_nfa_to_dfa, name='convert_nfa_to_dfa_legacy'),
    path('api/dfa/<int:pk>/minimize/', views.minimize_dfa, name='minimize_dfa_legacy'),
    path('api/nfa/<int:pk>/is-dfa/', views.check_if_nfa_is_dfa, name='check_if_nfa_is_dfa_legacy'),
    path('api/automaton/<int:pk>/check-fa-type/', views.check_fa_type, name='check_fa_type_legacy'),
    
    # New standalone pages
    path('fa-checker/', views.FATypeCheckerView.as_view(), name='fa_type_checker'),
    path('conversion-tools/', views.ConversionToolsView.as_view(), name='conversion_tools'),
    
    # Result pages
    path('automaton/<int:pk>/minimization-result/', views.MinimizationResultView.as_view(), name='minimization_result'),
    path('automaton/<int:pk>/conversion-result/', views.ConversionResultView.as_view(), name='conversion_result'),
]
