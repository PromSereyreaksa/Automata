from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('exercises/', views.ExercisesListView.as_view(), name='exercises_list'),
    
    # Automaton CRUD
    path('create/dfa/', views.DFACreateView.as_view(), name='create_dfa'),
    path('create/nfa/', views.NFACreateView.as_view(), name='create_nfa'),
    path('dfa/<int:pk>/', views.DFADetailView.as_view(), name='dfa_detail'),
    path('nfa/<int:pk>/', views.NFADetailView.as_view(), name='nfa_detail'),
    path('automaton/<int:pk>/', views.AutomatonDetailView.as_view(), name='automaton_detail'),  # Keep for backwards compatibility
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
    
    # Advanced operations (placeholders)
    path('api/nfa/<int:pk>/to-dfa/', views.convert_nfa_to_dfa, name='convert_nfa_to_dfa'),
    path('api/dfa/<int:pk>/minimize/', views.minimize_dfa, name='minimize_dfa'),
    path('api/nfa/<int:pk>/is-dfa/', views.check_if_nfa_is_dfa, name='check_if_nfa_is_dfa'),
]
