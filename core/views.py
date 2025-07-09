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

from .models import DFA, NFA, DFAState, NFAState, DFATransition, NFATransition
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
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('core:automaton_detail', kwargs={'pk': self.object.pk})

class NFACreateView(LoginRequiredMixin, CreateView):
    model = NFA
    form_class = NFACreateForm
    template_name = 'automaton/create_nfa.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

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
    state_name = data.get('name')

    if not state_name:
        return JsonResponse({'status': 'error', 'message': 'State name cannot be empty.'}, status=400)

    try:
        # If no other states exist, make this the start state
        is_start = not StateModel.objects.filter(automaton=automaton).exists()
        StateModel.objects.create(automaton=automaton, name=state_name, is_start=is_start)
        automaton.update_json_representation()
        return JsonResponse({'status': 'ok', 'message': 'State added successfully.'})
    except IntegrityError:
        return JsonResponse({'status': 'error', 'message': f"A state with the name '{state_name}' already exists."}, status=400)

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
    
    state.automaton.update_json_representation()
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def delete_state(request, pk):
    data = json.loads(request.body)
    StateModel, _ = get_automaton_related_models(get_automaton_instance(pk, request.user))
    state = get_object_or_404(StateModel, pk=data.get('state_pk'))
    automaton = state.automaton
    state.delete()
    automaton.update_json_representation()
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
        automaton.update_json_representation()
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
    automaton.update_json_representation()
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
