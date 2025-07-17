import json
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Automaton(models.Model):
    """
    Model for finite automata that can be either DFA or NFA.
    The type is determined by the is_dfa() and is_nfa() methods.
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
    is_example = models.BooleanField(default=False, help_text="True if this is a system example automaton")
    has_epsilon = models.BooleanField(default=False, help_text="True if this automaton has epsilon transitions")
    cached_type = models.CharField(max_length=10, blank=True, help_text="Cached automaton type for performance")

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
            is_self_loop = transition.from_state.name == transition.to_state.name
            edges.append({
                'data': {
                    'source': transition.from_state.name,
                    'target': transition.to_state.name,
                    'label': symbol_display,
                    'pk': transition.pk,  # Add primary key for AJAX operations
                    'is_self_loop': is_self_loop,
                }
            })

        self.json_representation = {'nodes': nodes, 'edges': edges}
        # Clear cached type when automaton structure changes
        self.cached_type = ''
        self.save()

    def is_dfa(self):
        """
        Checks if the automaton is a valid DFA.
        A DFA must have:
        - Exactly one start state
        - At least one final state (can have multiple)
        - No epsilon transitions
        - For every state and every symbol, exactly one transition (deterministic)
        Returns tuple: (is_dfa, message)
        """
        # Basic validation checks
        start_states = self.states.filter(is_start=True)
        if not start_states.exists():
            return False, "No start state defined"
        
        if start_states.count() > 1:
            return False, "DFA must have exactly one start state"
        
        final_states = self.states.filter(is_final=True)
        if not final_states.exists():
            return False, "No final state defined"
        
        # Check for epsilon transitions
        for transition in self.transitions.all():
            if not transition.symbol or transition.symbol == 'ε':
                return False, "DFA cannot have epsilon transitions"
        
        # Check for nondeterministic transitions
        alphabet = self.get_alphabet_as_set()
        for state in self.states.all():
            for symbol in alphabet:
                matching_transitions = []
                for trans in self.transitions.filter(from_state=state):
                    if trans.matches_symbol(symbol):
                        matching_transitions.append(trans)
                
                if len(matching_transitions) > 1:
                    return False, f"State '{state.name}' has multiple transitions for symbol '{symbol}'"
                elif len(matching_transitions) == 0:
                    return False, f"State '{state.name}' missing transition for symbol '{symbol}'"
        
        return True, "Valid DFA"

    def is_nfa(self):
        """
        Checks if the automaton is a valid NFA.
        An NFA can have:
        - One or more start states
        - One or more final states
        - Epsilon transitions (allowed)
        - Multiple transitions for the same state and symbol (non-deterministic)
        - Missing transitions for some state-symbol pairs
        Returns tuple: (is_nfa, message)
        """
        # Basic validation checks
        start_states = self.states.filter(is_start=True)
        if not start_states.exists():
            return False, "No start state defined"
        
        final_states = self.states.filter(is_final=True)
        if not final_states.exists():
            return False, "No final state defined"
        
        # Check if all transitions reference valid states
        for transition in self.transitions.all():
            if transition.from_state not in self.states.all():
                return False, f"Transition references invalid from_state: {transition.from_state.name}"
            if transition.to_state not in self.states.all():
                return False, f"Transition references invalid to_state: {transition.to_state.name}"
        
        return True, "Valid NFA"

    def get_type(self):
        """
        Returns the type of automaton: 'DFA', 'NFA', or 'INVALID'
        Rule: If NFA is exactly the same as DFA, assume it to be DFA because NFA can be DFA but DFA cannot be NFA.
        Uses caching for performance.
        """
        if self.cached_type:
            return self.cached_type
            
        is_dfa_result, dfa_message = self.is_dfa()
        if is_dfa_result:
            self.cached_type = 'DFA'
            self.save(update_fields=['cached_type'])
            return 'DFA'
        
        is_nfa_result, nfa_message = self.is_nfa()
        if is_nfa_result:
            self.cached_type = 'NFA'
            self.save(update_fields=['cached_type'])
            return 'NFA'
        
        self.cached_type = 'INVALID'
        self.save(update_fields=['cached_type'])
        return 'INVALID'

    def is_valid(self):
        """
        Checks if the automaton is valid based on its type.
        """
        automaton_type = self.get_type()
        if automaton_type == 'DFA':
            return self.is_dfa()
        elif automaton_type == 'NFA':
            return self.is_nfa()
        else:
            return False, "Invalid automaton"

    def simulate(self, input_string):
        """Simulates the automaton on a given input string."""
        automaton_type = self.get_type()
        if automaton_type == 'DFA':
            return self._simulate_dfa(input_string)
        elif automaton_type == 'NFA':
            return self._simulate_nfa(input_string)
        else:
            return False, "Cannot simulate invalid automaton", []

    def _simulate_dfa(self, input_string):
        """Simulates DFA on input string."""
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

    def _simulate_nfa(self, input_string):
        """Simulates NFA on input string."""
        
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
        Returns a tuple: (dfa, detailed_steps)
        """
        if self.get_type() != 'NFA':
            raise ValueError("Can only convert NFA to DFA")
        
        from collections import defaultdict, deque
        
        steps = []
        state_construction_log = []
        
        # Helper function to compute epsilon closure
        def epsilon_closure(states):
            """
            Calculates the epsilon closure for a set of states.
            Returns the set of all states reachable by epsilon transitions.
            """
            if not states:
                return set()
            
            closure = set(states)
            stack = list(states)
            
            while stack:
                state = stack.pop()
                # Find all epsilon transitions from this state
                for trans in self.transitions.filter(from_state=state):
                    if trans.matches_symbol('ε') or not trans.symbol:
                        if trans.to_state not in closure:
                            closure.add(trans.to_state)
                            stack.append(trans.to_state)
            
            return closure
        
        # Step 1: Get NFA transition table
        alphabet = self.get_alphabet_as_set()
        steps.append({
            "step": 1,
            "description": "NFA Transition Table Analysis",
            "nfa_table": self._create_transition_table(self),
            "alphabet": sorted(alphabet),
            "explanation": "Analyze the original NFA structure and alphabet"
        })
        
        # Step 2: Create the DFA's start state
        start_states = set(self.states.filter(is_start=True))
        if not start_states:
            raise ValueError("NFA must have at least one start state")
        
        # Get epsilon closure of start states
        initial_state_set = epsilon_closure(start_states)
        
        steps.append({
            "step": 2,
            "description": "Create DFA start state",
            "start_states": [s.name for s in start_states],
            "epsilon_closure": sorted([s.name for s in initial_state_set]),
            "explanation": "DFA start state is the ε-closure of NFA start states"
        })
        
        # Create the DFA
        dfa = Automaton.objects.create(
            name=f"{self.name}_DFA",
            alphabet=self.alphabet,
            owner=self.owner
        )
        
        # Map from frozenset of NFA states to DFA state
        state_map = {}
        # Queue of state sets to process
        queue = deque([initial_state_set])
        # Set of processed state sets
        processed = set()
        
        # Better state naming
        state_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        state_counter = 0
        
        # Create initial DFA state
        initial_state_name = state_names[state_counter] if state_counter < len(state_names) else f"S{state_counter}"
        initial_dfa_state = dfa.states.create(
            name=initial_state_name,
            is_start=True,
            is_final=any(s.is_final for s in initial_state_set)
        )
        state_map[frozenset(initial_state_set)] = initial_dfa_state
        
        state_construction_log.append({
            "dfa_state": initial_state_name,
            "nfa_states": sorted([s.name for s in initial_state_set]),
            "is_start": True,
            "is_final": any(s.is_final for s in initial_state_set)
        })
        
        state_counter += 1
        
        # Step 3: Create the DFA's transition table
        transition_log = []
        
        while queue:
            current_state_set = queue.popleft()
            current_state_set_frozen = frozenset(current_state_set)
            
            if current_state_set_frozen in processed:
                continue
            processed.add(current_state_set_frozen)
            
            current_dfa_state = state_map[current_state_set_frozen]
            
            # For each symbol in alphabet
            for symbol in alphabet:
                next_state_set = set()
                
                # Find all states reachable by this symbol from current state set
                for nfa_state in current_state_set:
                    for trans in self.transitions.filter(from_state=nfa_state):
                        if trans.matches_symbol(symbol):
                            next_state_set.add(trans.to_state)
                
                if next_state_set:
                    # Step 3 continued: Add epsilon closure of the destination states
                    next_state_set = epsilon_closure(next_state_set)
                    next_state_set_frozen = frozenset(next_state_set)
                    
                    # Create new DFA state if it doesn't exist
                    if next_state_set_frozen not in state_map:
                        next_state_name = state_names[state_counter] if state_counter < len(state_names) else f"S{state_counter}"
                        
                        # Step 4: Create DFA final states
                        # A DFA state is final if it contains at least one NFA final state
                        is_final = any(s.is_final for s in next_state_set)
                        
                        next_dfa_state = dfa.states.create(
                            name=next_state_name,
                            is_start=False,
                            is_final=is_final
                        )
                        state_map[next_state_set_frozen] = next_dfa_state
                        queue.append(next_state_set)
                        
                        state_construction_log.append({
                            "dfa_state": next_state_name,
                            "nfa_states": sorted([s.name for s in next_state_set]),
                            "is_start": False,
                            "is_final": is_final
                        })
                        
                        state_counter += 1
                    
                    # Create transition in DFA
                    dfa.transitions.create(
                        from_state=current_dfa_state,
                        to_state=state_map[next_state_set_frozen],
                        symbol=symbol
                    )
                    
                    transition_log.append({
                        "from_state": current_dfa_state.name,
                        "to_state": state_map[next_state_set_frozen].name,
                        "symbol": symbol,
                        "nfa_computation": f"δ({[s.name for s in current_state_set]}, {symbol}) = ε-closure({[s.name for s in next_state_set]})"
                    })
        
        steps.append({
            "step": 3,
            "description": "State Construction Process",
            "state_construction": state_construction_log,
            "explanation": "Each DFA state represents a set of NFA states"
        })
        
        steps.append({
            "step": 4,
            "description": "Transition Construction",
            "transitions": transition_log,
            "explanation": "DFA transitions computed using ε-closure of NFA transitions"
        })
        
        # Step 5: Remove unreachable states (already handled by our construction)
        # Since we only create states that are reachable from the start state,
        # unreachable states are automatically avoided
        
        # Update JSON representation
        dfa.update_json_representation()
        
        # Create detailed result
        detailed_steps = {
            "steps": steps,
            "message": f"Successfully converted NFA to DFA ({self.states.count()} NFA states → {dfa.states.count()} DFA states)",
            "original_nfa_table": self._create_transition_table(self),
            "final_dfa_table": self._create_transition_table(dfa),
            "state_mapping": state_construction_log,
            "nfa_state_count": self.states.count(),
            "dfa_state_count": dfa.states.count(),
            "has_epsilon_transitions": self.has_epsilon
        }
        
        return dfa, detailed_steps
    
    def _remove_dead_states(self, dfa):
        """
        Helper method to remove dead states from DFA.
        Dead states are states that cannot reach any final state.
        """
        # Find all states that can reach a final state
        reachable_to_final = set()
        final_states = set(dfa.states.filter(is_final=True))
        
        # Start with final states
        reachable_to_final.update(final_states)
        
        # Work backwards to find all states that can reach final states
        changed = True
        while changed:
            changed = False
            for state in dfa.states.all():
                if state not in reachable_to_final:
                    # Check if this state has a path to any reachable state
                    for trans in dfa.transitions.filter(from_state=state):
                        if trans.to_state in reachable_to_final:
                            reachable_to_final.add(state)
                            changed = True
                            break
        
        # Remove states that cannot reach final states
        dead_states = []
        for state in dfa.states.all():
            if state not in reachable_to_final:
                dead_states.append(state)
        
        for state in dead_states:
            state.delete()

    def minimize(self):
        """
        Minimizes the automaton if it's a DFA using the Myhill-Nerode Theorem.
        Returns a tuple: (minimized_automaton, detailed_steps)
        """
        if self.get_type() != 'DFA':
            raise ValueError("Can only minimize DFA")
        
        states = list(self.states.all())
        n = len(states)
        
        if n <= 1:
            return self, {"steps": [], "message": "Already minimal - single state"}
        
        alphabet = self.get_alphabet_as_set()
        steps = []
        
        # Step 1: Initial partition P0 - separate final and non-final states
        final_states = []
        non_final_states = []
        
        for state in states:
            if state.is_final:
                final_states.append(state)
            else:
                non_final_states.append(state)
        
        # Create initial partition P0
        current_partition = []
        if final_states:
            current_partition.append(final_states)
        if non_final_states:
            current_partition.append(non_final_states)
        
        # Record Step 1
        steps.append({
            "step": 1,
            "description": "Initial partition P₀: Separate final and non-final states",
            "partition": [[state.name for state in group] for group in current_partition],
            "explanation": "States are initially grouped by their acceptance status"
        })
        
        # Step 2-4: Iteratively refine partitions
        k = 0
        while True:
            k += 1
            new_partition = []
            
            # For each set in current partition, check if it can be split
            for state_set in current_partition:
                if len(state_set) == 1:
                    # Single state sets cannot be split
                    new_partition.append(state_set)
                    continue
                
                # Check all pairs in this set for distinguishability
                sub_partitions = []
                remaining_states = list(state_set)
                
                while remaining_states:
                    # Start new sub-partition with first remaining state
                    current_sub = [remaining_states.pop(0)]
                    
                    # Check which other states are equivalent to this one
                    i = 0
                    while i < len(remaining_states):
                        state1 = current_sub[0]
                        state2 = remaining_states[i]
                        
                        # Check if state1 and state2 are distinguishable
                        are_distinguishable = False
                        distinguishing_symbol = None
                        
                        for symbol in alphabet:
                            # Find transitions for both states
                            trans1 = None
                            trans2 = None
                            
                            for trans in self.transitions.filter(from_state=state1):
                                if trans.matches_symbol(symbol):
                                    trans1 = trans
                                    break
                            
                            for trans in self.transitions.filter(from_state=state2):
                                if trans.matches_symbol(symbol):
                                    trans2 = trans
                                    break
                            
                            if not trans1 or not trans2:
                                # Missing transition means states are distinguishable
                                are_distinguishable = True
                                distinguishing_symbol = symbol
                                break
                            
                            # Find which partition sets the destination states belong to
                            dest1 = trans1.to_state
                            dest2 = trans2.to_state
                            
                            # Find partition sets for destinations
                            dest1_partition = None
                            dest2_partition = None
                            
                            for j, partition_set in enumerate(current_partition):
                                if dest1 in partition_set:
                                    dest1_partition = j
                                if dest2 in partition_set:
                                    dest2_partition = j
                            
                            # If destinations are in different partitions, states are distinguishable
                            if dest1_partition != dest2_partition:
                                are_distinguishable = True
                                distinguishing_symbol = symbol
                                break
                        
                        if not are_distinguishable:
                            # States are equivalent, add to current sub-partition
                            current_sub.append(remaining_states.pop(i))
                        else:
                            i += 1
                    
                    sub_partitions.append(current_sub)
                
                # Add all sub-partitions to new partition
                new_partition.extend(sub_partitions)
            
            # Record this step
            steps.append({
                "step": k + 1,
                "description": f"Partition P₍{k}₎: Check distinguishability",
                "partition": [[state.name for state in group] for group in new_partition],
                "explanation": f"States are grouped by equivalent behavior on alphabet {list(alphabet)}"
            })
            
            # Check if partition changed
            if len(new_partition) == len(current_partition):
                # Check if sets are the same
                partition_changed = False
                for new_set in new_partition:
                    found_match = False
                    for old_set in current_partition:
                        if set(new_set) == set(old_set):
                            found_match = True
                            break
                    if not found_match:
                        partition_changed = True
                        break
                
                if not partition_changed:
                    break  # No change, we're done
            
            current_partition = new_partition
        
        # Step 5: Check if minimization is possible
        if len(current_partition) == n:
            return self, {
                "steps": steps,
                "message": "Already minimal - no equivalent states found",
                "equivalence_classes": [[state.name for state in group] for group in current_partition]
            }
        
        # Create minimized automaton
        minimized_automaton = Automaton.objects.create(
            name=f"{self.name}_minimized",
            alphabet=self.alphabet,
            owner=self.owner
        )
        
        # Create mapping from old states to new states with better names
        state_map = {}
        state_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        
        for i, equiv_class in enumerate(current_partition):
            # Create clean state name
            if i < len(state_names):
                new_state_name = state_names[i]
            else:
                new_state_name = f"S{i}"
            
            # Check if any state in class is start/final
            is_start = any(state.is_start for state in equiv_class)
            is_final = any(state.is_final for state in equiv_class)
            
            new_state = minimized_automaton.states.create(
                name=new_state_name,
                is_start=is_start,
                is_final=is_final
            )
            
            # Map all old states in this class to the new state
            for state in equiv_class:
                state_map[state] = new_state
        
        # Create transitions for minimized automaton
        created_transitions = set()
        
        for old_state in states:
            new_from_state = state_map[old_state]
            
            for symbol in alphabet:
                # Find transition that matches this symbol
                old_transition = None
                for trans in self.transitions.filter(from_state=old_state):
                    if trans.matches_symbol(symbol):
                        old_transition = trans
                        break
                
                if old_transition:
                    new_to_state = state_map[old_transition.to_state]
                    
                    # Avoid duplicate transitions
                    transition_key = (new_from_state.id, new_to_state.id, symbol)
                    if transition_key not in created_transitions:
                        minimized_automaton.transitions.create(
                            from_state=new_from_state,
                            to_state=new_to_state,
                            symbol=symbol
                        )
                        created_transitions.add(transition_key)
        
        # Update JSON representation
        minimized_automaton.update_json_representation()
        
        # Create detailed result
        detailed_steps = {
            "steps": steps,
            "message": f"Successfully minimized from {n} states to {len(current_partition)} states",
            "equivalence_classes": [
                {
                    "new_state": state_names[i] if i < len(state_names) else f"S{i}",
                    "original_states": [state.name for state in equiv_class],
                    "is_start": any(state.is_start for state in equiv_class),
                    "is_final": any(state.is_final for state in equiv_class)
                }
                for i, equiv_class in enumerate(current_partition)
            ],
            "transition_table": self._create_transition_table(minimized_automaton),
            "original_state_count": n,
            "minimized_state_count": len(current_partition),
            "reduction_percentage": round(((n - len(current_partition)) / n) * 100, 1)
        }
        
        return minimized_automaton, detailed_steps

    def _create_transition_table(self, automaton):
        """Helper method to create a transition table for display."""
        alphabet = automaton.get_alphabet_as_set()
        states = list(automaton.states.all())
        
        table = []
        for state in states:
            row = {"state": state.name, "is_start": state.is_start, "is_final": state.is_final}
            for symbol in sorted(alphabet):
                trans = automaton.transitions.filter(from_state=state, symbol=symbol).first()
                row[symbol] = trans.to_state.name if trans else "∅"
            table.append(row)
        
        return {
            "headers": ["State"] + sorted(alphabet),
            "rows": table
        }

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
        Returns all epsilon transitions in the automaton.
        """
        epsilon_transitions = []
        for trans in self.transitions.all():
            if trans.matches_symbol('ε') or not trans.symbol:
                epsilon_transitions.append(trans)
        return epsilon_transitions

    def get_start_states(self):
        """
        Returns all start states in the automaton.
        """
        return self.states.filter(is_start=True)

    def get_final_states(self):
        """
        Returns all final states in the automaton.
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

    def __str__(self):
        return self.name


class State(models.Model):
    """Represents a single state in an automaton."""
    automaton = models.ForeignKey('Automaton', related_name='states', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_start = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    class Meta:
        unique_together = [['automaton', 'name']]
        indexes = [
            models.Index(fields=['automaton', 'is_start']),
            models.Index(fields=['automaton', 'is_final']),
        ]

    def __str__(self):
        return f"{self.name} ({'start, ' if self.is_start else ''}{'final' if self.is_final else ''})"


class Transition(models.Model):
    """Represents a transition between two states on a given symbol."""
    automaton = models.ForeignKey('Automaton', related_name='transitions', on_delete=models.CASCADE)
    from_state = models.ForeignKey('State', related_name='from_transitions', on_delete=models.CASCADE)
    to_state = models.ForeignKey('State', related_name='to_transitions', on_delete=models.CASCADE)
    symbol = models.CharField(max_length=50, blank=True)  # Increased length for multiple symbols

    class Meta:
        indexes = [
            models.Index(fields=['automaton', 'from_state']),
            models.Index(fields=['automaton', 'symbol']),
        ]

    def get_symbols_as_set(self):
        """Returns the symbols in this transition as a set, supporting ranges like a-z, 0-9."""
        import re
        import string
        
        if not self.symbol:
            return {'ε'}  # Epsilon transition
        if self.symbol == 'ε':
            return {'ε'}
        
        symbols = set()
        parts = [s.strip() for s in self.symbol.split(',') if s.strip()]
        
        for part in parts:
            # Check for range patterns like a-z, 0-9, A-Z
            range_match = re.match(r'^([a-zA-Z0-9])-([a-zA-Z0-9])$', part)
            if range_match:
                start_char, end_char = range_match.groups()
                
                # Handle lowercase letters
                if start_char.islower() and end_char.islower():
                    start_ord = ord(start_char)
                    end_ord = ord(end_char)
                    if start_ord <= end_ord:
                        symbols.update(chr(i) for i in range(start_ord, end_ord + 1))
                
                # Handle uppercase letters
                elif start_char.isupper() and end_char.isupper():
                    start_ord = ord(start_char)
                    end_ord = ord(end_char)
                    if start_ord <= end_ord:
                        symbols.update(chr(i) for i in range(start_ord, end_ord + 1))
                
                # Handle digits
                elif start_char.isdigit() and end_char.isdigit():
                    start_ord = ord(start_char)
                    end_ord = ord(end_char)
                    if start_ord <= end_ord:
                        symbols.update(chr(i) for i in range(start_ord, end_ord + 1))
                else:
                    # Invalid range, treat as literal
                    symbols.add(part)
            else:
                # Regular symbol
                symbols.add(part)
        
        return symbols

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


class UserHistory(models.Model):
    """Track user interactions with automata for history and analytics."""
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('view', 'Viewed'),
        ('edit', 'Edited'),
        ('simulate', 'Simulated'),
        ('minimize', 'Minimized'),
        ('convert', 'Converted'),
        ('delete', 'Deleted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='automata_history')
    automaton_id = models.PositiveIntegerField()  # Store ID even if automaton is deleted
    automaton_name = models.CharField(max_length=255)
    automaton_type = models.CharField(max_length=10, choices=[('DFA', 'DFA'), ('NFA', 'NFA')])
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(null=True, blank=True)  # Store action-specific data
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['user', 'action']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.automaton_name} at {self.timestamp}"

    @classmethod
    def log_action(cls, user, automaton, action, details=None):
        """Helper method to log user actions."""
        if not user or not automaton:
            return
        
        automaton_type = automaton.get_type()
        
        return cls.objects.create(
            user=user,
            automaton_id=automaton.id,
            automaton_name=automaton.name,
            automaton_type=automaton_type,
            action=action,
            details=details or {}
        )
