import json
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Automaton(models.Model):
    """
    Abstract base model for all finite automata.
    It holds the common properties of DFAs and NFAs.
    """
    name = models.CharField(max_length=255)
    alphabet = models.CharField(
        max_length=255,
        help_text="Enter all symbols of the alphabet, separated by commas (e.g., a,b,c)",
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    json_representation = models.JSONField(null=True, blank=True, help_text="JSON representation for graph visualization")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def get_alphabet_as_set(self):
        """Returns the alphabet as a set of strings."""
        return set(s.strip() for s in self.alphabet.split(',') if s.strip())

    def update_json_representation(self):
        """
        Updates the json_representation field with the current state of the automaton
        for visualization with Cytoscape.js.
        """
        nodes = []
        edges = []

        for state in self.states.all():
            nodes.append({
                'data': {
                    'id': state.name,
                    'name': state.name,
                    'pk': state.pk,  # Add primary key for AJAX operations
                    'is_start': state.is_start,
                    'is_final': state.is_final,
                }
            })

        for transition in self.transitions.all():
            symbol_display = transition.symbol if transition.symbol else 'ε'
            edges.append({
                'data': {
                    'source': transition.from_state.name,
                    'target': transition.to_state.name,
                    'label': symbol_display,
                    'pk': transition.pk,  # Add primary key for AJAX operations
                }
            })

        self.json_representation = {'nodes': nodes, 'edges': edges}
        self.save()

    def __str__(self):
        return self.name


class State(models.Model):
    """Represents a single state in an automaton."""
    automaton = models.ForeignKey('Automaton', related_name='states', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_start = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    class Meta:
        abstract = True
        # Remove unique_together constraint to allow multiple transitions

    def __str__(self):
        return f"{self.name} ({'start, ' if self.is_start else ''}{'final' if self.is_final else ''})"


class Transition(models.Model):
    """Represents a transition between two states on a given symbol."""
    automaton = models.ForeignKey('Automaton', related_name='transitions', on_delete=models.CASCADE)
    from_state = models.ForeignKey('State', related_name='from_transitions', on_delete=models.CASCADE)
    to_state = models.ForeignKey('State', related_name='to_transitions', on_delete=models.CASCADE)
    symbol = models.CharField(max_length=50, blank=True)  # Increased length for multiple symbols

    class Meta:
        abstract = True

    def get_symbols_as_set(self):
        """Returns the symbols in this transition as a set."""
        if not self.symbol:
            return {'ε'}  # Epsilon transition
        if self.symbol == 'ε':
            return {'ε'}
        # Handle comma-separated symbols like "a,b"
        return set(s.strip() for s in self.symbol.split(',') if s.strip())

    def clean(self):
        # Ensure the symbols are in the automaton's alphabet (except for epsilon transitions)
        if self.symbol and self.symbol != 'ε':
            alphabet = self.automaton.get_alphabet_as_set()
            symbols = self.get_symbols_as_set()
            for symbol in symbols:
                if symbol not in alphabet:
                    raise ValidationError(f"Symbol '{symbol}' is not in the automaton's alphabet.")

    def matches_symbol(self, input_symbol):
        """Check if this transition can be taken with the given input symbol."""
        transition_symbols = self.get_symbols_as_set()
        return input_symbol in transition_symbols

    def __str__(self):
        symbol_display = self.symbol if self.symbol else 'ε'
        return f"({self.from_state.name}) --{symbol_display}--> ({self.to_state.name})"


class DFAState(State):
    automaton = models.ForeignKey('DFA', related_name='states', on_delete=models.CASCADE)


class DFATransition(Transition):
    automaton = models.ForeignKey('DFA', related_name='transitions', on_delete=models.CASCADE)
    from_state = models.ForeignKey(DFAState, related_name='from_transitions', on_delete=models.CASCADE)
    to_state = models.ForeignKey(DFAState, related_name='to_transitions', on_delete=models.CASCADE)


class NFAState(State):
    automaton = models.ForeignKey('NFA', related_name='states', on_delete=models.CASCADE)


class NFATransition(Transition):
    automaton = models.ForeignKey('NFA', related_name='transitions', on_delete=models.CASCADE)
    from_state = models.ForeignKey(NFAState, related_name='from_transitions', on_delete=models.CASCADE)
    to_state = models.ForeignKey(NFAState, related_name='to_transitions', on_delete=models.CASCADE)


class DFA(Automaton):
    """Represents a Deterministic Finite Automaton."""

    def is_valid(self):
        """
        Checks if the DFA is valid:
        1. Exactly one start state.
        2. For each state and each symbol in the alphabet, there is exactly one transition.
        """
        start_states_count = self.states.filter(is_start=True).count()
        if start_states_count != 1:
            return False, "A DFA must have exactly one start state."

        alphabet = self.get_alphabet_as_set()
        for state in self.states.all():
            for symbol in alphabet:
                # Count transitions that can handle this symbol
                matching_transitions = []
                for trans in self.transitions.filter(from_state=state):
                    if trans.matches_symbol(symbol):
                        matching_transitions.append(trans)
                
                if len(matching_transitions) != 1:
                    return False, f"State '{state.name}' must have exactly one transition for symbol '{symbol}', found {len(matching_transitions)}."
        return True, "DFA is valid."

    def simulate(self, input_string):
        """Simulates the DFA on a given input string."""
        if not self.states.filter(is_start=True).exists():
            return False, "No start state defined.", []

        current_state = self.states.get(is_start=True)
        path = [current_state.name]

        for symbol in input_string:
            if symbol not in self.get_alphabet_as_set():
                return False, f"Input symbol '{symbol}' is not in the alphabet.", path
            try:
                # Find transition that matches this symbol
                transitions = self.transitions.filter(from_state=current_state)
                matching_transition = None
                for trans in transitions:
                    if trans.matches_symbol(symbol):
                        matching_transition = trans
                        break
                
                if not matching_transition:
                    return False, f"No transition found from state '{current_state.name}' on symbol '{symbol}'.", path
                
                current_state = matching_transition.to_state
                path.append(current_state.name)
            except Exception as e:
                return False, f"Error during simulation: {str(e)}", path

        return current_state.is_final, "Simulation completed.", path

    def minimize(self):
        """
        Minimizes the DFA using the table-filling algorithm.
        """
        states = list(self.states.all())
        n = len(states)
        
        if n <= 1:
            return self  # Already minimal
        
        # Create a 2D table for distinguishable pairs
        distinguishable = [[False for _ in range(n)] for _ in range(n)]
        
        # Step 1: Mark pairs where one is final and one is not
        for i in range(n):
            for j in range(i + 1, n):
                if states[i].is_final != states[j].is_final:
                    distinguishable[i][j] = True
        
        # Step 2: Iteratively mark distinguishable pairs
        alphabet = self.get_alphabet_as_set()
        changed = True
        
        while changed:
            changed = False
            for i in range(n):
                for j in range(i + 1, n):
                    if not distinguishable[i][j]:
                        # Check if this pair should be marked
                        for symbol in alphabet:
                            try:
                                trans_i = self.transitions.get(from_state=states[i], symbol=symbol)
                                trans_j = self.transitions.get(from_state=states[j], symbol=symbol)
                                
                                # Find indices of destination states
                                dest_i_idx = states.index(trans_i.to_state)
                                dest_j_idx = states.index(trans_j.to_state)
                                
                                # Check if destinations are distinguishable
                                if dest_i_idx != dest_j_idx:
                                    min_idx = min(dest_i_idx, dest_j_idx)
                                    max_idx = max(dest_i_idx, dest_j_idx)
                                    if distinguishable[min_idx][max_idx]:
                                        distinguishable[i][j] = True
                                        changed = True
                                        break
                            except:
                                # If transition doesn't exist, states are distinguishable
                                distinguishable[i][j] = True
                                changed = True
                                break
        
        # Step 3: Group equivalent states
        equivalence_classes = []
        processed = [False] * n
        
        for i in range(n):
            if not processed[i]:
                equiv_class = [i]
                processed[i] = True
                
                for j in range(i + 1, n):
                    if not processed[j] and not distinguishable[i][j]:
                        equiv_class.append(j)
                        processed[j] = True
                
                equivalence_classes.append(equiv_class)
        
        # If no reduction possible, return original DFA
        if len(equivalence_classes) == n:
            return self
        
        # Step 4: Create minimized DFA
        minimized_dfa = DFA.objects.create(
            name=f"{self.name}_minimized",
            alphabet=self.alphabet,
            owner=self.owner
        )
        
        # Create mapping from old states to new states
        state_map = {}
        new_states = []
        
        for i, equiv_class in enumerate(equivalence_classes):
            # Create representative state name
            repr_names = sorted([states[idx].name for idx in equiv_class])
            new_state_name = "{" + ",".join(repr_names) + "}"
            
            # Check if any state in class is start/final
            is_start = any(states[idx].is_start for idx in equiv_class)
            is_final = any(states[idx].is_final for idx in equiv_class)
            
            new_state = minimized_dfa.states.create(
                name=new_state_name,
                is_start=is_start,
                is_final=is_final
            )
            new_states.append(new_state)
            
            # Map all old states in this class to the new state
            for idx in equiv_class:
                state_map[states[idx]] = new_state
        
        # Step 5: Create transitions for minimized DFA
        created_transitions = set()
        
        for old_state in states:
            new_from_state = state_map[old_state]
            
            for symbol in alphabet:
                try:
                    old_transition = self.transitions.get(from_state=old_state, symbol=symbol)
                    new_to_state = state_map[old_transition.to_state]
                    
                    # Avoid duplicate transitions
                    transition_key = (new_from_state.id, new_to_state.id, symbol)
                    if transition_key not in created_transitions:
                        minimized_dfa.transitions.create(
                            from_state=new_from_state,
                            to_state=new_to_state,
                            symbol=symbol
                        )
                        created_transitions.add(transition_key)
                except:
                    pass  # Skip if transition doesn't exist
        
        # Update JSON representation
        minimized_dfa.update_json_representation()
        return minimized_dfa


class NFA(Automaton):
    """Represents a Nondeterministic Finite Automaton."""

    def is_valid(self):
        """
        Checks if the NFA is valid:
        1. At least one start state.
        2. At least one final state.
        3. All transitions reference valid states.
        """
        start_states_count = self.states.filter(is_start=True).count()
        if start_states_count == 0:
            return False, "NFA must have at least one start state."

        final_states_count = self.states.filter(is_final=True).count()
        if final_states_count == 0:
            return False, "NFA should have at least one final state."

        # Check if all transitions reference valid states
        for transition in self.transitions.all():
            if transition.from_state not in self.states.all():
                return False, f"Transition references invalid from_state: {transition.from_state.name}"
            if transition.to_state not in self.states.all():
                return False, f"Transition references invalid to_state: {transition.to_state.name}"

        return True, "NFA is valid."

    def is_dfa(self):
        """
        Checks if the NFA is also a DFA.
        1. No epsilon transitions.
        2. For each state and symbol, there is at most one transition.
        3. Exactly one start state.
        """
        # Check for epsilon transitions (empty string or 'ε')
        if self.transitions.filter(symbol='').exists() or self.transitions.filter(symbol='ε').exists():
            return False, "NFA has epsilon transitions."

        # Check for multiple start states
        start_states_count = self.states.filter(is_start=True).count()
        if start_states_count != 1:
            return False, "NFA has multiple start states."

        # Check for nondeterministic transitions
        alphabet = self.get_alphabet_as_set()
        for state in self.states.all():
            for symbol in alphabet:
                # Count transitions that can handle this symbol
                matching_transitions = []
                for trans in self.transitions.filter(from_state=state):
                    if trans.matches_symbol(symbol):
                        matching_transitions.append(trans)
                
                if len(matching_transitions) > 1:
                    return False, f"State '{state.name}' has multiple transitions for symbol '{symbol}'."
        return True, "NFA is deterministic."

    def simulate(self, input_string):
        """Simulates the NFA on a given input string."""
        
        def epsilon_closure(states):
            """Calculates the epsilon closure for a set of states."""
            closure = set(states)
            stack = list(states)
            while stack:
                state = stack.pop()
                # Check for epsilon transitions (empty string or 'ε')
                epsilon_transitions = self.transitions.filter(from_state=state)
                for trans in epsilon_transitions:
                    if trans.matches_symbol('ε') or (not trans.symbol):
                        if trans.to_state not in closure:
                            closure.add(trans.to_state)
                            stack.append(trans.to_state)
            return closure

        # Check if there are any start states
        start_states = self.states.filter(is_start=True)
        if not start_states.exists():
            return False, "No start state defined.", []

        # Get all start states and their epsilon closure
        initial_states = set(start_states)
        current_states = epsilon_closure(initial_states)
        
        # Create path tracking with sets of states
        path = [sorted([state.name for state in current_states])]

        for symbol in input_string:
            if symbol not in self.get_alphabet_as_set():
                return False, f"Input symbol '{symbol}' is not in the alphabet.", path

            next_states = set()
            for state in current_states:
                transitions = self.transitions.filter(from_state=state)
                for trans in transitions:
                    if trans.matches_symbol(symbol):
                        next_states.add(trans.to_state)
            
            if not next_states:
                return False, "Simulation stuck. No transition found.", path

            current_states = epsilon_closure(next_states)
            if current_states:
                path.append(sorted([state.name for state in current_states]))

        # Check if any of the final states is in the set of current states
        for state in current_states:
            if state.is_final:
                return True, "String accepted.", path
        
        return False, "String rejected.", path

    def to_dfa(self):
        """
        Converts the NFA to an equivalent DFA using the subset construction algorithm.
        """
        from collections import defaultdict
        
        # Get epsilon closure for start states
        def epsilon_closure(states):
            closure = set(states)
            stack = list(states)
            while stack:
                state = stack.pop()
                for trans in self.transitions.filter(from_state=state):
                    if trans.matches_symbol('ε') or not trans.symbol:
                        if trans.to_state not in closure:
                            closure.add(trans.to_state)
                            stack.append(trans.to_state)
            return closure
        
        # Get all start states and their epsilon closure
        start_states = set(self.get_start_states())
        if not start_states:
            raise ValueError("NFA must have at least one start state")
        
        initial_state_set = epsilon_closure(start_states)
        
        # Create the DFA
        dfa = DFA.objects.create(
            name=f"{self.name}_DFA",
            alphabet=self.alphabet,
            owner=self.owner
        )
        
        # Map from frozenset of NFA states to DFA state
        state_map = {}
        # Queue of state sets to process
        queue = [initial_state_set]
        # Set of processed state sets
        processed = set()
        
        # Create initial DFA state
        initial_state_name = "{" + ",".join(sorted(s.name for s in initial_state_set)) + "}"
        initial_dfa_state = dfa.states.create(
            name=initial_state_name,
            is_start=True,
            is_final=any(s.is_final for s in initial_state_set)
        )
        state_map[frozenset(initial_state_set)] = initial_dfa_state
        
        while queue:
            current_state_set = queue.pop(0)
            current_state_set_frozen = frozenset(current_state_set)
            
            if current_state_set_frozen in processed:
                continue
            processed.add(current_state_set_frozen)
            
            current_dfa_state = state_map[current_state_set_frozen]
            
            # For each symbol in alphabet
            for symbol in self.get_alphabet_as_set():
                next_state_set = set()
                
                # Find all states reachable by this symbol
                for nfa_state in current_state_set:
                    for trans in self.transitions.filter(from_state=nfa_state):
                        if trans.matches_symbol(symbol):
                            next_state_set.add(trans.to_state)
                
                if next_state_set:
                    # Add epsilon closure
                    next_state_set = epsilon_closure(next_state_set)
                    next_state_set_frozen = frozenset(next_state_set)
                    
                    # Create new DFA state if it doesn't exist
                    if next_state_set_frozen not in state_map:
                        next_state_name = "{" + ",".join(sorted(s.name for s in next_state_set)) + "}"
                        next_dfa_state = dfa.states.create(
                            name=next_state_name,
                            is_start=False,
                            is_final=any(s.is_final for s in next_state_set)
                        )
                        state_map[next_state_set_frozen] = next_dfa_state
                        queue.append(next_state_set)
                    
                    # Create transition in DFA
                    dfa.transitions.create(
                        from_state=current_dfa_state,
                        to_state=state_map[next_state_set_frozen],
                        symbol=symbol
                    )
        
        # Update JSON representation
        dfa.update_json_representation()
        return dfa

    def add_epsilon_transition(self, from_state, to_state):
        """
        Helper method to add an epsilon transition between two states.
        """
        epsilon_transition = self.transitions.create(
            from_state=from_state,
            to_state=to_state,
            symbol='ε'
        )
        return epsilon_transition

    def get_epsilon_transitions(self):
        """
        Returns all epsilon transitions in the NFA.
        """
        epsilon_transitions = []
        for trans in self.transitions.all():
            if trans.matches_symbol('ε') or not trans.symbol:
                epsilon_transitions.append(trans)
        return epsilon_transitions

    def get_start_states(self):
        """
        Returns all start states in the NFA.
        """
        return self.states.filter(is_start=True)

    def get_final_states(self):
        """
        Returns all final states in the NFA.
        """
        return self.states.filter(is_final=True)

    def add_transition(self, from_state, to_state, symbols):
        """
        Helper method to add a transition with multiple symbols.
        symbols can be a string like "a,b" or a list like ['a', 'b']
        """
        if isinstance(symbols, list):
            symbol_str = ','.join(symbols)
        else:
            symbol_str = symbols
        
        # Check if transition already exists
        existing_transitions = self.transitions.filter(
            from_state=from_state, 
            to_state=to_state, 
            symbol=symbol_str
        )
        
        if existing_transitions.exists():
            return existing_transitions.first()
        
        transition = self.transitions.create(
            from_state=from_state,
            to_state=to_state,
            symbol=symbol_str
        )
        return transition

    def remove_transition(self, from_state, to_state, symbols=None):
        """
        Helper method to remove transitions.
        If symbols is None, removes all transitions between the states.
        """
        if symbols is None:
            # Remove all transitions between these states
            self.transitions.filter(from_state=from_state, to_state=to_state).delete()
        else:
            if isinstance(symbols, list):
                symbol_str = ','.join(symbols)
            else:
                symbol_str = symbols
            self.transitions.filter(
                from_state=from_state, 
                to_state=to_state, 
                symbol=symbol_str
            ).delete()
