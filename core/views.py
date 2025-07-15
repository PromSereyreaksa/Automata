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

from .models import DFA, NFA, DFAState, NFAState, DFATransition, NFATransition, UserHistory
from .forms import DFACreateForm, NFACreateForm

# --- Helper Function ---
def get_automaton_instance(pk, user):
    """Fetches the correct DFA or NFA instance, ensuring ownership or system access."""
    try:
        # Try to get user's own automaton first
        return DFA.objects.get(pk=pk, owner=user)
    except DFA.DoesNotExist:
        try:
            return NFA.objects.get(pk=pk, owner=user)
        except NFA.DoesNotExist:
            # Try to get system examples (owner=None or system user)
            try:
                return DFA.objects.get(pk=pk, owner=None)
            except DFA.DoesNotExist:
                try:
                    return NFA.objects.get(pk=pk, owner=None)
                except NFA.DoesNotExist:
                    # Try system user examples
                    try:
                        system_user = User.objects.get(username='system')
                        try:
                            return DFA.objects.get(pk=pk, owner=system_user)
                        except DFA.DoesNotExist:
                            return NFA.objects.get(pk=pk, owner=system_user)
                    except (User.DoesNotExist, DFA.DoesNotExist, NFA.DoesNotExist):
                        raise Http404("No Automaton found matching the query or you don't have permission.")

def get_automaton_related_models(automaton):
    """Gets the concrete State and Transition models for a given automaton instance."""
    if isinstance(automaton, DFA):
        return DFAState, DFATransition
    elif isinstance(automaton, NFA):
        return NFAState, NFATransition
    raise Http404("Automaton type not found")

# --- Class-Based Views for Pages ---
class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'automaton/dashboard.html'
    context_object_name = 'automatons'

    def get_queryset(self):
        # Get user's own automata
        user_dfas = DFA.objects.filter(owner=self.request.user)
        user_nfas = NFA.objects.filter(owner=self.request.user)
        
        # Get system examples (examples for everyone)
        system_dfas = DFA.objects.filter(owner=None)
        system_nfas = NFA.objects.filter(owner=None)
        
        # Try to get examples from system user if exists
        try:
            system_user = User.objects.get(username='system')
            system_dfas = system_dfas.union(DFA.objects.filter(owner=system_user))
            system_nfas = system_nfas.union(NFA.objects.filter(owner=system_user))
        except User.DoesNotExist:
            pass
        
        # Combine user's automata with system examples
        all_dfas = user_dfas.union(system_dfas)
        all_nfas = user_nfas.union(system_nfas)
        
        return {'dfas': all_dfas, 'nfas': all_nfas}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add user history for dashboard
        recent_history = UserHistory.objects.filter(
            user=self.request.user
        ).select_related('user')[:10]
        
        context['recent_history'] = recent_history
        
        # Add statistics
        context['stats'] = {
            'total_created': UserHistory.objects.filter(
                user=self.request.user, 
                action='create'
            ).count(),
            'total_simulations': UserHistory.objects.filter(
                user=self.request.user, 
                action='simulate'
            ).count(),
            'dfas_count': DFA.objects.filter(owner=self.request.user).count(),
            'nfas_count': NFA.objects.filter(owner=self.request.user).count(),
        }
        
        return context

class ExercisesListView(ListView):
    template_name = 'automaton/exercises_list.html'
    context_object_name = 'exercises'

    def get_queryset(self):
        try:
            system_user = User.objects.get(username='system')
            dfas = DFA.objects.filter(owner=system_user)
            nfas = NFA.objects.filter(owner=system_user)
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
        context['is_nfa'] = isinstance(automaton, NFA)
        context['is_dfa'] = isinstance(automaton, DFA)
        
        # Removed view logging for better UX
        
        # Add FA type check
        fa_type, is_valid, message = automaton.check_fa_type()
        context['fa_type'] = fa_type
        context['fa_type_valid'] = is_valid
        context['fa_type_message'] = message
        
        # Add a simple filter for use in templates
        from django.template.defaultfilters import register
        @register.filter
        def class_name(value):
            return value.__class__.__name__
        context['class_name_filter'] = class_name
        return context

class DFACreateView(LoginRequiredMixin, CreateView):
    model = DFA
    form_class = DFACreateForm
    template_name = 'automaton/create_dfa.html'

    def form_valid(self, form):
        # Create the DFA immediately and redirect to editing
        dfa = form.save(commit=False)
        dfa.owner = self.request.user
        dfa.is_example = False
        dfa.save()
        
        # Log creation action
        UserHistory.log_action(
            user=self.request.user,
            automaton=dfa,
            action='create',
            details={'automaton_type': 'DFA'}
        )
        
        return redirect('core:automaton_detail', pk=dfa.pk)

    def get_success_url(self):
        return reverse_lazy('core:automaton_detail', kwargs={'pk': self.object.pk})

class NFACreateView(LoginRequiredMixin, CreateView):
    model = NFA
    form_class = NFACreateForm
    template_name = 'automaton/create_nfa.html'

    def form_valid(self, form):
        # Create the NFA immediately and redirect to editing
        nfa = form.save(commit=False)
        nfa.owner = self.request.user
        nfa.is_example = False
        nfa.save()
        
        # Log creation action
        UserHistory.log_action(
            user=self.request.user,
            automaton=nfa,
            action='create',
            details={'automaton_type': 'NFA'}
        )
        
        return redirect('core:automaton_detail', pk=nfa.pk)

    def get_success_url(self):
        return reverse_lazy('core:automaton_detail', kwargs={'pk': self.object.pk})

class AutomatonUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'automaton/automaton_form.html'
    context_object_name = 'automaton'

    def get_object(self, queryset=None):
        return get_automaton_instance(self.kwargs.get('pk'), self.request.user)

    def get_form_class(self):
        return DFACreateForm if isinstance(self.object, DFA) else NFACreateForm

    def get_success_url(self):
        return reverse_lazy('core:automaton_detail', kwargs={'pk': self.object.pk})

class AutomatonDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'automaton/confirm_delete.html'
    success_url = reverse_lazy('core:dashboard')
    context_object_name = 'automaton'

    def get_object(self, queryset=None):
        return get_automaton_instance(self.kwargs.get('pk'), self.request.user)

class DFADetailView(LoginRequiredMixin, DetailView):
    model = DFA
    template_name = 'automaton/automaton_detail.html'
    context_object_name = 'automaton'

    def get_queryset(self):
        return DFA.objects.filter(owner=self.request.user) | DFA.objects.filter(owner__username='system')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_nfa'] = False
        context['is_dfa'] = True
        return context

class NFADetailView(LoginRequiredMixin, DetailView):
    model = NFA
    template_name = 'automaton/automaton_detail.html'
    context_object_name = 'automaton'

    def get_queryset(self):
        return NFA.objects.filter(owner=self.request.user) | NFA.objects.filter(owner__username='system')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_nfa'] = True
        context['is_dfa'] = False
        return context

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
        if not symbol and isinstance(automaton, NFA):
            symbol = 'ε'
        elif not symbol:
            return JsonResponse({'status': 'error', 'message': 'Symbol cannot be empty.'}, status=400)

        # For NFA, allow epsilon transitions
        if isinstance(automaton, NFA):
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
        if isinstance(automaton, DFA):
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
    
    # The simulate method needs to be updated to return a path
    accepted, message, *path_data = automaton.simulate(input_string)
    path = path_data[0] if path_data else []
    
    # Removed simulation logging for better UX - only log create/edit actions

    return JsonResponse({'accepted': accepted, 'message': message, 'path': path})

@login_required
def get_alphabet_symbols(request, pk):
    """Return alphabet symbols for the automaton."""
    automaton = get_automaton_instance(pk, request.user)
    alphabet = list(automaton.get_alphabet_as_set())
    
    # For NFA, add epsilon option
    if isinstance(automaton, NFA):
        symbols = [{'value': 'ε', 'label': 'ε (epsilon)'}]
        symbols.extend([{'value': symbol, 'label': symbol} for symbol in sorted(alphabet)])
    else:
        symbols = [{'value': symbol, 'label': symbol} for symbol in sorted(alphabet)]
    
    return JsonResponse({'symbols': symbols})

# --- Placeholder Views for Future Implementation ---
@login_required
def convert_nfa_to_dfa(request, pk):
    try:
        nfa = get_object_or_404(NFA, pk=pk)
        # Allow owner or system examples
        if nfa.owner != request.user and nfa.owner.username != 'system':
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
        
        dfa = nfa.to_dfa()
        
        # Log conversion action
        UserHistory.log_action(
            user=request.user,
            automaton=nfa,
            action='convert',
            details={
                'from_type': 'NFA',
                'to_type': 'DFA',
                'result_dfa_id': dfa.id,
                'result_dfa_name': dfa.name
            }
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'NFA successfully converted to DFA.',
            'dfa_id': dfa.id,
            'dfa_name': dfa.name
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def minimize_dfa(request, pk):
    try:
        dfa = get_object_or_404(DFA, pk=pk)
        # Allow owner or system examples
        if dfa.owner != request.user and dfa.owner.username != 'system':
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
        
        minimized_dfa = dfa.minimize()
        
        # Log minimization action
        UserHistory.log_action(
            user=request.user,
            automaton=dfa,
            action='minimize',
            details={
                'original_states': dfa.states.count(),
                'minimized_states': minimized_dfa.states.count(),
                'was_already_minimal': minimized_dfa == dfa,
                'result_dfa_id': minimized_dfa.id if minimized_dfa != dfa else dfa.id
            }
        )
        
        if minimized_dfa == dfa:
            return JsonResponse({
                'status': 'info',
                'message': 'DFA is already minimal.'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': 'DFA successfully minimized.',
                'minimized_dfa_id': minimized_dfa.id,
                'minimized_dfa_name': minimized_dfa.name
            })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def check_if_nfa_is_dfa(request, pk):
    nfa = get_object_or_404(NFA, pk=pk, owner=request.user)
    is_dfa, message = nfa.is_dfa()
    return JsonResponse({'is_dfa': is_dfa, 'message': message})

@login_required
def check_fa_type(request, pk):
    """Generic FA type checker for any automaton."""
    automaton = get_automaton_instance(pk, request.user)
    fa_type, is_valid, message = automaton.check_fa_type()
    
    return JsonResponse({
        'fa_type': fa_type,
        'is_valid': is_valid,
        'message': message,
        'current_type': 'DFA' if isinstance(automaton, DFA) else 'NFA'
    })
