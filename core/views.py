import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, Http404, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Automaton, State, Transition, UserHistory

# --- Helper Function ---
def get_automaton_instance(pk, user):
    """Fetches the automaton instance, ensuring ownership or system access."""
    try:
        # Try to get user's own automaton first
        return Automaton.objects.get(pk=pk, owner=user)
    except Automaton.DoesNotExist:
        # Try to get system examples (owner=None or system user)
        try:
            return Automaton.objects.get(pk=pk, owner=None)
        except Automaton.DoesNotExist:
            # Try system user examples
            try:
                system_user = User.objects.get(username='system')
                return Automaton.objects.get(pk=pk, owner=system_user)
            except (User.DoesNotExist, Automaton.DoesNotExist):
                raise Http404("No Automaton found matching the query or you don't have permission.")

def get_automaton_related_models(automaton):
    """Gets the State and Transition models for a given automaton instance."""
    return State, Transition

# --- Class-Based Views for Pages ---
class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'automaton/dashboard.html'
    context_object_name = 'automatons'

    def get_queryset(self):
        # Get user's own automata
        user_automatons = Automaton.objects.filter(owner=self.request.user)
        
        # Get system examples (examples for everyone)
        system_automatons = Automaton.objects.filter(owner=None)
        
        # Try to get examples from system user if exists
        try:
            system_user = User.objects.get(username='system')
            system_automatons = system_automatons.union(Automaton.objects.filter(owner=system_user))
        except User.DoesNotExist:
            pass
        
        # Combine user's automata with system examples
        all_automatons = user_automatons.union(system_automatons)
        
        # Separate by type
        dfas = [a for a in all_automatons if a.get_type() == 'DFA']
        nfas = [a for a in all_automatons if a.get_type() == 'NFA']
        
        return {'dfas': dfas, 'nfas': nfas}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add user history for dashboard
        recent_history = UserHistory.objects.filter(
            user=self.request.user
        ).select_related('user')[:10]
        
        context['recent_history'] = recent_history
        
        # Add statistics
        user_automatons = Automaton.objects.filter(owner=self.request.user)
        context['stats'] = {
            'total_created': UserHistory.objects.filter(
                user=self.request.user, 
                action='create'
            ).count(),
            'total_simulations': UserHistory.objects.filter(
                user=self.request.user, 
                action='simulate'
            ).count(),
            'dfas_count': len([a for a in user_automatons if a.get_type() == 'DFA']),
            'nfas_count': len([a for a in user_automatons if a.get_type() == 'NFA']),
        }
        
        return context

class ExercisesListView(ListView):
    template_name = 'automaton/exercises_list.html'
    context_object_name = 'exercises'

    def get_queryset(self):
        try:
            system_user = User.objects.get(username='system')
            automatons = Automaton.objects.filter(owner=system_user)
            dfas = [a for a in automatons if a.get_type() == 'DFA']
            nfas = [a for a in automatons if a.get_type() == 'NFA']
            return {'dfas': dfas, 'nfas': nfas}
        except User.DoesNotExist:
            return {'dfas': [], 'nfas': []}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exercises = self.get_queryset()
        context['dfas'] = exercises['dfas']
        context['nfas'] = exercises['nfas']
        return context

class AutomatonDetailView(LoginRequiredMixin, DetailView):
    template_name = 'automaton/automaton_detail.html'
    context_object_name = 'automaton'

    def get_object(self, queryset=None):
        return get_automaton_instance(self.kwargs.get('pk'), self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        automaton = self.get_object()
        automaton_type = automaton.get_type()
        context['is_nfa'] = automaton_type == 'NFA'
        context['is_dfa'] = automaton_type == 'DFA'
        
        # Removed view logging for better UX
        
        # Add FA type check
        context['fa_type'] = automaton_type
        is_dfa_valid, dfa_message = automaton.is_dfa()
        is_nfa_valid, nfa_message = automaton.is_nfa()
        context['fa_type_valid'] = is_dfa_valid or is_nfa_valid
        context['fa_type_message'] = dfa_message if is_dfa_valid else nfa_message
        
        # Add a simple filter for use in templates
        from django.template.defaultfilters import register
        @register.filter
        def class_name(value):
            return value.__class__.__name__
        context['class_name_filter'] = class_name
        return context

class AutomatonCreateView(LoginRequiredMixin, CreateView):
    model = Automaton
    template_name = 'automaton/create_automaton.html'
    fields = ['name', 'alphabet']

    def form_valid(self, form):
        # Create the automaton immediately and redirect to editing
        automaton = form.save(commit=False)
        automaton.owner = self.request.user
        automaton.is_example = False
        automaton.has_epsilon = self.request.POST.get('has_epsilon') == 'on'
        
        # Add initial start state to make it valid from the beginning
        automaton.save()
        
        # Create initial start state
        initial_state = automaton.states.create(
            name='q0',
            is_start=True,
            is_final=False
        )
        
        # Update JSON representation
        automaton.update_json_representation()
        
        # Log creation action
        automaton_type = 'NFA' if automaton.has_epsilon else 'DFA'
        UserHistory.log_action(
            user=self.request.user,
            automaton=automaton,
            action='create',
            details={'automaton_type': automaton_type, 'has_epsilon': automaton.has_epsilon}
        )
        
        return redirect('core:automaton_detail', pk=automaton.pk)

    def get_success_url(self):
        return reverse_lazy('core:automaton_detail', kwargs={'pk': self.object.pk})


class AutomatonUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'automaton/automaton_form.html'
    context_object_name = 'automaton'

    def get_object(self, queryset=None):
        return get_automaton_instance(self.kwargs.get('pk'), self.request.user)

    def get_form_class(self):
        from django import forms
        class AutomatonForm(forms.ModelForm):
            class Meta:
                model = Automaton
                fields = ['name', 'alphabet']
                widgets = {
                    'name': forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'e.g., Even Number of A\'s'
                    }),
                    'alphabet': forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'e.g., a,b'
                    }),
                }
        return AutomatonForm

    def form_valid(self, form):
        # Handle epsilon field
        automaton = form.save(commit=False)
        automaton.has_epsilon = self.request.POST.get('has_epsilon') == 'on'
        automaton.cached_type = ''  # Clear cached type when properties change
        automaton.save()
        
        # Update JSON representation
        automaton.update_json_representation()
        
        # Log edit action
        UserHistory.log_action(
            user=self.request.user,
            automaton=automaton,
            action='edit',
            details={'action_type': 'update_properties', 'has_epsilon': automaton.has_epsilon}
        )
        
        return redirect('core:automaton_detail', pk=automaton.pk)

    def get_success_url(self):
        return reverse_lazy('core:automaton_detail', kwargs={'pk': self.object.pk})

class AutomatonDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'automaton/confirm_delete.html'
    success_url = reverse_lazy('core:dashboard')
    context_object_name = 'automaton'

    def get_object(self, queryset=None):
        return get_automaton_instance(self.kwargs.get('pk'), self.request.user)


# --- API-like Function-Based Views for AJAX calls ---

@login_required
@require_POST
def add_state(request, pk):
    automaton = get_automaton_instance(pk, request.user)
    StateModel, _ = get_automaton_related_models(automaton)
    data = json.loads(request.body)
    state_names_input = data.get('name')

    if not state_names_input:
        return JsonResponse({'status': 'error', 'message': 'State name cannot be empty.'}, status=400)

    # Handle multiple states separated by commas
    state_names = [name.strip() for name in state_names_input.split(',') if name.strip()]
    
    if not state_names:
        return JsonResponse({'status': 'error', 'message': 'No valid state names provided.'}, status=400)

    try:
        # Check if no other states exist to determine if first state should be start state
        is_first_state = not StateModel.objects.filter(automaton=automaton).exists()
        
        created_states = []
        existing_states = []
        
        for i, state_name in enumerate(state_names):
            try:
                # Only make the first state in the list the start state if no states exist
                is_start = is_first_state and i == 0
                new_state = StateModel.objects.create(
                    automaton=automaton, 
                    name=state_name, 
                    is_start=is_start
                )
                created_states.append(state_name)
            except IntegrityError:
                existing_states.append(state_name)
        
        # Auto-save: update JSON representation and save
        automaton.update_json_representation()
        automaton.save()
        
        # Log edit action only when states are actually created
        if created_states:
            UserHistory.log_action(
                user=request.user,
                automaton=automaton,
                action='edit',
                details={
                    'action_type': 'add_states',
                    'states_added': created_states
                }
            )
        
        # Prepare response message
        if created_states and existing_states:
            message = f"Created states: {', '.join(created_states)}. States already exist: {', '.join(existing_states)}."
        elif created_states:
            message = f"Created {len(created_states)} state(s): {', '.join(created_states)}."
        else:
            message = f"All states already exist: {', '.join(existing_states)}."
        
        # Return success even if some states already existed
        return JsonResponse({
            'status': 'ok' if created_states else 'warning',
            'message': message,
            'created_count': len(created_states),
            'existing_count': len(existing_states)
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error creating states: {str(e)}'}, status=500)

@login_required
@require_POST
def update_state(request, pk):
    data = json.loads(request.body)
    action = data.get('action')
    StateModel, _ = get_automaton_related_models(get_automaton_instance(pk, request.user))
    state = get_object_or_404(StateModel, pk=data.get('state_pk'))
    
    with transaction.atomic():
        if action == 'toggle_final':
            state.is_final = not state.is_final
            state.save()
        elif action == 'set_start':
            # Ensure only one start state
            state.automaton.states.update(is_start=False)
            state.is_start = True
            state.save()
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)
    
    # Auto-save: update JSON representation and save
    state.automaton.update_json_representation()
    state.automaton.save()
    
    # Log edit action
    UserHistory.log_action(
        user=request.user,
        automaton=state.automaton,
        action='edit',
        details={
            'action_type': f'update_state_{action}',
            'state_name': state.name
        }
    )
    
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def delete_state(request, pk):
    data = json.loads(request.body)
    StateModel, _ = get_automaton_related_models(get_automaton_instance(pk, request.user))
    state = get_object_or_404(StateModel, pk=data.get('state_pk'))
    automaton = state.automaton
    state.delete()
    
    # Auto-save: update JSON representation and save
    automaton.update_json_representation()
    automaton.save()
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def add_transition(request, pk):
    automaton = get_automaton_instance(pk, request.user)
    StateModel, TransitionModel = get_automaton_related_models(automaton)
    data = json.loads(request.body)
    
    try:
        from_state = StateModel.objects.get(pk=data.get('from_state'), automaton=automaton)
        to_state = StateModel.objects.get(pk=data.get('to_state'), automaton=automaton)
        symbol = data.get('symbol')

        # Handle empty symbol as epsilon for NFA
        if not symbol and automaton.get_type() == 'NFA':
            symbol = 'ε'
        elif not symbol:
            return JsonResponse({'status': 'error', 'message': 'Symbol cannot be empty.'}, status=400)

        # For NFA, allow epsilon transitions
        if automaton.get_type() == 'NFA':
            if symbol == 'ε' or symbol == '':
                # Epsilon transition is always valid for NFA
                pass
            else:
                # Handle multiple symbols (a,b format)
                if ',' in symbol:
                    symbols = [s.strip() for s in symbol.split(',') if s.strip()]
                    for s in symbols:
                        if s not in automaton.get_alphabet_as_set():
                            return JsonResponse({'status': 'error', 'message': f"Symbol '{s}' is not in the alphabet."}, status=400)
                else:
                    if symbol not in automaton.get_alphabet_as_set():
                        return JsonResponse({'status': 'error', 'message': f"Symbol '{symbol}' is not in the alphabet."}, status=400)
        else:
            # For DFA, check single symbol in alphabet
            if symbol not in automaton.get_alphabet_as_set():
                return JsonResponse({'status': 'error', 'message': f"Symbol '{symbol}' is not in the alphabet."}, status=400)

        # For DFAs, ensure no two transitions from the same state have the same symbol
        if automaton.get_type() == 'DFA':
            existing_transitions = TransitionModel.objects.filter(
                automaton=automaton, 
                from_state=from_state
            )
            for trans in existing_transitions:
                if trans.matches_symbol(symbol):
                    return JsonResponse({'status': 'error', 'message': 'This DFA already has a transition for this state and symbol.'}, status=400)

        TransitionModel.objects.create(automaton=automaton, from_state=from_state, to_state=to_state, symbol=symbol)
        
        # Auto-save: update JSON representation and save
        automaton.update_json_representation()
        automaton.save()
        
        # Log edit action
        UserHistory.log_action(
            user=request.user,
            automaton=automaton,
            action='edit',
            details={
                'action_type': 'add_transition',
                'from_state': from_state.name,
                'to_state': to_state.name,
                'symbol': symbol
            }
        )
        
        return JsonResponse({'status': 'ok', 'message': 'Transition added.'})
    except StateModel.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'State not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def delete_transition(request, pk):
    data = json.loads(request.body)
    _, TransitionModel = get_automaton_related_models(get_automaton_instance(pk, request.user))
    transition = get_object_or_404(TransitionModel, pk=data.get('transition_pk'))
    automaton = transition.automaton
    transition.delete()
    
    # Auto-save: update JSON representation and save
    automaton.update_json_representation()
    automaton.save()
    return JsonResponse({'status': 'ok'})

# --- Core Functionality Views ---

@login_required
def get_automaton_json(request, pk):
    automaton = get_automaton_instance(pk, request.user)
    automaton.update_json_representation()
    return JsonResponse(automaton.json_representation)

@login_required
def simulate_string(request, pk):
    automaton = get_automaton_instance(pk, request.user)
    input_string = request.GET.get('input_string', '')
    
    # The simulate method now returns detailed path information
    simulation_result = automaton.simulate(input_string)
    accepted, message = simulation_result[:2]
    path = simulation_result[2] if len(simulation_result) > 2 else []
    detailed_path = simulation_result[3] if len(simulation_result) > 3 else {}
    
    # Removed simulation logging for better UX - only log create/edit actions

    return JsonResponse({
        'accepted': accepted, 
        'message': message, 
        'path': path,
        'detailed_path': detailed_path
    })

@login_required
def get_alphabet_symbols(request, pk):
    """Return alphabet symbols for the automaton."""
    automaton = get_automaton_instance(pk, request.user)
    alphabet = list(automaton.get_alphabet_as_set())
    
    # If has_epsilon is True, always include epsilon option
    if automaton.has_epsilon:
        symbols = [{'value': 'ε', 'label': 'ε (epsilon)'}]
        symbols.extend([{'value': symbol, 'label': symbol} for symbol in sorted(alphabet)])
    else:
        symbols = [{'value': symbol, 'label': symbol} for symbol in sorted(alphabet)]
    
    return JsonResponse({'symbols': symbols})

# --- Placeholder Views for Future Implementation ---
@login_required
def convert_nfa_to_dfa(request, pk):
    try:
        automaton = get_automaton_instance(pk, request.user)
        
        if automaton.get_type() != 'NFA':
            return JsonResponse({'status': 'error', 'message': 'Only NFA can be converted to DFA.'}, status=400)
        
        dfa, detailed_steps = automaton.to_dfa()
        
        # Store the detailed steps in the session for the result page
        request.session[f'conversion_steps_{dfa.id}'] = detailed_steps
        
        # Log conversion action
        UserHistory.log_action(
            user=request.user,
            automaton=automaton,
            action='convert',
            details={
                'from_type': 'NFA',
                'to_type': 'DFA',
                'result_dfa_id': dfa.id,
                'result_dfa_name': dfa.name,
                'original_states': detailed_steps['nfa_state_count'],
                'result_states': detailed_steps['dfa_state_count']
            }
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'NFA successfully converted to DFA.',
            'dfa_id': dfa.id,
            'dfa_name': dfa.name,
            'conversion_steps_url': f'/automata/automaton/{dfa.id}/conversion-result/'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def minimize_dfa(request, pk):
    try:
        automaton = get_automaton_instance(pk, request.user)
        
        if automaton.get_type() != 'DFA':
            return JsonResponse({'status': 'error', 'message': 'Only DFA can be minimized.'}, status=400)
        
        minimized_dfa, detailed_steps = automaton.minimize()
        
        # Store the detailed steps in the session for the result page
        request.session[f'minimization_steps_{minimized_dfa.id}'] = detailed_steps
        
        # Log minimization action
        UserHistory.log_action(
            user=request.user,
            automaton=automaton,
            action='minimize',
            details={
                'original_states': detailed_steps['original_state_count'],
                'minimized_states': detailed_steps['minimized_state_count'],
                'was_already_minimal': minimized_dfa == automaton,
                'result_dfa_id': minimized_dfa.id if minimized_dfa != automaton else automaton.id,
                'reduction_percentage': detailed_steps.get('reduction_percentage', 0)
            }
        )
        
        if minimized_dfa == automaton:
            return JsonResponse({
                'status': 'info',
                'message': 'DFA is already minimal.',
                'minimization_steps_url': f'/automata/automaton/{automaton.id}/minimization-result/'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': 'DFA successfully minimized.',
                'minimized_dfa_id': minimized_dfa.id,
                'minimized_dfa_name': minimized_dfa.name,
                'minimization_steps_url': f'/automata/automaton/{minimized_dfa.id}/minimization-result/'
            })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def check_if_nfa_is_dfa(request, pk):
    automaton = get_automaton_instance(pk, request.user)
    is_dfa, message = automaton.is_dfa()
    return JsonResponse({'is_dfa': is_dfa, 'message': message})

@login_required
def check_fa_type(request, pk):
    """Generic FA type checker for any automaton."""
    automaton = get_automaton_instance(pk, request.user)
    fa_type = automaton.get_type()
    is_dfa_valid, dfa_message = automaton.is_dfa()
    is_nfa_valid, nfa_message = automaton.is_nfa()
    
    return JsonResponse({
        'fa_type': fa_type,
        'is_valid': is_dfa_valid or is_nfa_valid,
        'message': dfa_message if is_dfa_valid else nfa_message,
        'current_type': fa_type
    })

@login_required
@require_POST
def enable_epsilon(request, pk):
    """Enable epsilon transitions for an automaton, converting DFA to NFA."""
    try:
        automaton = get_automaton_instance(pk, request.user)
        
        if automaton.has_epsilon:
            return JsonResponse({'status': 'error', 'message': 'Epsilon transitions already enabled.'}, status=400)
        
        # Enable epsilon transitions
        automaton.has_epsilon = True
        automaton.cached_type = ''  # Clear cached type to force re-evaluation
        automaton.save()
        
        # Log the action
        UserHistory.log_action(
            user=request.user,
            automaton=automaton,
            action='edit',
            details={
                'action_type': 'enable_epsilon',
                'converted_from': 'DFA',
                'converted_to': 'NFA'
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Epsilon transitions enabled. Automaton is now an NFA.',
            'new_type': 'NFA'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class FATypeCheckerView(LoginRequiredMixin, ListView):
    template_name = 'automaton/fa_type_checker.html'
    context_object_name = 'automatons'
    
    def get_queryset(self):
        user_automatons = Automaton.objects.filter(owner=self.request.user)
        system_automatons = Automaton.objects.filter(owner=None)
        
        try:
            system_user = User.objects.get(username='system')
            system_automatons = system_automatons.union(Automaton.objects.filter(owner=system_user))
        except User.DoesNotExist:
            pass
        
        return user_automatons.union(system_automatons)

class ConversionToolsView(LoginRequiredMixin, ListView):
    template_name = 'automaton/conversion_tools.html'
    context_object_name = 'automatons'
    
    def get_queryset(self):
        user_automatons = Automaton.objects.filter(owner=self.request.user)
        system_automatons = Automaton.objects.filter(owner=None)
        
        try:
            system_user = User.objects.get(username='system')
            system_automatons = system_automatons.union(Automaton.objects.filter(owner=system_user))
        except User.DoesNotExist:
            pass
        
        all_automatons = user_automatons.union(system_automatons)
        
        dfas = [a for a in all_automatons if a.get_type() == 'DFA']
        nfas = [a for a in all_automatons if a.get_type() == 'NFA']
        
        return {'dfas': dfas, 'nfas': nfas}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        automatons = self.get_queryset()
        context['dfas'] = automatons['dfas']
        context['nfas'] = automatons['nfas']
        return context


class MinimizationResultView(LoginRequiredMixin, DetailView):
    """View for displaying detailed minimization results."""
    template_name = 'automaton/minimization_result.html'
    context_object_name = 'automaton'
    
    def get_object(self, queryset=None):
        return get_automaton_instance(self.kwargs.get('pk'), self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        automaton = self.get_object()
        
        # Get detailed steps from session
        steps_key = f'minimization_steps_{automaton.id}'
        detailed_steps = self.request.session.get(steps_key, {})
        
        context['detailed_steps'] = detailed_steps
        context['has_steps'] = bool(detailed_steps)
        
        return context


class ConversionResultView(LoginRequiredMixin, DetailView):
    """View for displaying detailed NFA to DFA conversion results."""
    template_name = 'automaton/conversion_result.html'
    context_object_name = 'automaton'
    
    def get_object(self, queryset=None):
        return get_automaton_instance(self.kwargs.get('pk'), self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        automaton = self.get_object()
        
        # Get detailed steps from session
        steps_key = f'conversion_steps_{automaton.id}'
        detailed_steps = self.request.session.get(steps_key, {})
        
        context['detailed_steps'] = detailed_steps
        context['has_steps'] = bool(detailed_steps)
        
        return context
