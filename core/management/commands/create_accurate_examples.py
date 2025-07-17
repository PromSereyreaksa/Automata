from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Automaton, State, Transition


class Command(BaseCommand):
    help = 'Create accurate DFA and NFA examples for testing all functions'

    def handle(self, *args, **options):
        # Create system user for examples
        system_user, created = User.objects.get_or_create(username='system')
        
        # Clear existing examples
        Automaton.objects.filter(owner=system_user).delete()
        
        # Create examples
        self.create_dfa_examples(system_user)
        self.create_nfa_examples(system_user)
        
        self.stdout.write(self.style.SUCCESS('Successfully created accurate examples'))
    
    def create_dfa_examples(self, user):
        """Create proper DFA examples."""
        
        # DFA 1: Even number of a's (minimizable)
        dfa1 = Automaton.objects.create(
            name="DFA: Even number of a's (can be minimized)",
            alphabet="a,b",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        q0 = dfa1.states.create(name="q0", is_start=True, is_final=True)   # even a's
        q1 = dfa1.states.create(name="q1", is_start=False, is_final=False) # odd a's
        q2 = dfa1.states.create(name="q2", is_start=False, is_final=True)  # equivalent to q0
        q3 = dfa1.states.create(name="q3", is_start=False, is_final=False) # equivalent to q1
        
        # Main logic
        dfa1.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa1.transitions.create(from_state=q0, to_state=q0, symbol="b")
        dfa1.transitions.create(from_state=q1, to_state=q2, symbol="a")  # back to even
        dfa1.transitions.create(from_state=q1, to_state=q1, symbol="b")
        
        # Redundant states with same behavior
        dfa1.transitions.create(from_state=q2, to_state=q3, symbol="a")
        dfa1.transitions.create(from_state=q2, to_state=q2, symbol="b")
        dfa1.transitions.create(from_state=q3, to_state=q0, symbol="a")
        dfa1.transitions.create(from_state=q3, to_state=q3, symbol="b")
        
        dfa1.update_json_representation()
        
        # DFA 2: Binary divisible by 3 (complete and minimal)
        dfa2 = Automaton.objects.create(
            name="DFA: Binary divisible by 3 (complete)",
            alphabet="0,1",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        q0 = dfa2.states.create(name="q0", is_start=True, is_final=True)   # remainder 0
        q1 = dfa2.states.create(name="q1", is_start=False, is_final=False) # remainder 1
        q2 = dfa2.states.create(name="q2", is_start=False, is_final=False) # remainder 2
        
        # Complete transition function
        dfa2.transitions.create(from_state=q0, to_state=q0, symbol="0")
        dfa2.transitions.create(from_state=q0, to_state=q1, symbol="1")
        dfa2.transitions.create(from_state=q1, to_state=q2, symbol="0")
        dfa2.transitions.create(from_state=q1, to_state=q0, symbol="1")
        dfa2.transitions.create(from_state=q2, to_state=q1, symbol="0")
        dfa2.transitions.create(from_state=q2, to_state=q2, symbol="1")
        
        dfa2.update_json_representation()
        
        # DFA 3: Strings ending with 'ab' (multiple final states)
        dfa3 = Automaton.objects.create(
            name="DFA: Strings ending with 'ab' (multiple finals)",
            alphabet="a,b",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        q0 = dfa3.states.create(name="q0", is_start=True, is_final=False)
        q1 = dfa3.states.create(name="q1", is_start=False, is_final=False)
        q2 = dfa3.states.create(name="q2", is_start=False, is_final=True)
        q3 = dfa3.states.create(name="q3", is_start=False, is_final=True)  # additional final
        
        dfa3.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q0, to_state=q0, symbol="b")
        dfa3.transitions.create(from_state=q1, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q1, to_state=q2, symbol="b")
        dfa3.transitions.create(from_state=q2, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q2, to_state=q3, symbol="b")
        dfa3.transitions.create(from_state=q3, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q3, to_state=q0, symbol="b")
        
        dfa3.update_json_representation()
        
        self.stdout.write(self.style.SUCCESS('Created 3 DFA examples'))
    
    def create_nfa_examples(self, user):
        """Create proper NFA examples."""
        
        # NFA 1: Contains 'ab' (nondeterministic)
        nfa1 = Automaton.objects.create(
            name="NFA: Contains 'ab' (nondeterministic)",
            alphabet="a,b",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        q0 = nfa1.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa1.states.create(name="q1", is_start=False, is_final=False)
        q2 = nfa1.states.create(name="q2", is_start=False, is_final=True)
        
        # Nondeterministic: q0 has multiple transitions for 'a'
        nfa1.transitions.create(from_state=q0, to_state=q0, symbol="a")
        nfa1.transitions.create(from_state=q0, to_state=q1, symbol="a")  # nondeterministic
        nfa1.transitions.create(from_state=q0, to_state=q0, symbol="b")
        nfa1.transitions.create(from_state=q1, to_state=q2, symbol="b")
        nfa1.transitions.create(from_state=q2, to_state=q2, symbol="a")
        nfa1.transitions.create(from_state=q2, to_state=q2, symbol="b")
        
        nfa1.update_json_representation()
        
        # NFA 2: With epsilon transitions
        nfa2 = Automaton.objects.create(
            name="NFA: With epsilon transitions",
            alphabet="0,1",
            owner=user,
            is_example=True,
            has_epsilon=True
        )
        
        q0 = nfa2.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa2.states.create(name="q1", is_start=False, is_final=False)
        q2 = nfa2.states.create(name="q2", is_start=False, is_final=True)
        q3 = nfa2.states.create(name="q3", is_start=False, is_final=True)
        
        # Epsilon transitions
        nfa2.transitions.create(from_state=q0, to_state=q1, symbol="ε")
        nfa2.transitions.create(from_state=q0, to_state=q2, symbol="ε")
        
        # Regular transitions
        nfa2.transitions.create(from_state=q1, to_state=q1, symbol="0")
        nfa2.transitions.create(from_state=q1, to_state=q3, symbol="1")
        nfa2.transitions.create(from_state=q2, to_state=q2, symbol="1")
        nfa2.transitions.create(from_state=q2, to_state=q3, symbol="0")
        nfa2.transitions.create(from_state=q3, to_state=q3, symbol="0")
        nfa2.transitions.create(from_state=q3, to_state=q3, symbol="1")
        
        nfa2.update_json_representation()
        
        # NFA 3: Complex with multiple start states behavior
        nfa3 = Automaton.objects.create(
            name="NFA: Regular expression (a|b)*abb",
            alphabet="a,b",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        q0 = nfa3.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa3.states.create(name="q1", is_start=False, is_final=False)
        q2 = nfa3.states.create(name="q2", is_start=False, is_final=False)
        q3 = nfa3.states.create(name="q3", is_start=False, is_final=True)
        
        # (a|b)*
        nfa3.transitions.create(from_state=q0, to_state=q0, symbol="a")
        nfa3.transitions.create(from_state=q0, to_state=q0, symbol="b")
        
        # abb pattern (nondeterministic)
        nfa3.transitions.create(from_state=q0, to_state=q1, symbol="a")
        nfa3.transitions.create(from_state=q1, to_state=q2, symbol="b")
        nfa3.transitions.create(from_state=q2, to_state=q3, symbol="b")
        
        nfa3.update_json_representation()
        
        self.stdout.write(self.style.SUCCESS('Created 3 NFA examples'))