from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Automaton, State, Transition


class Command(BaseCommand):
    help = 'Create larger DFA examples that can be minimized'

    def handle(self, *args, **options):
        # Create system user for examples
        system_user, created = User.objects.get_or_create(username='system')
        
        # Create larger DFA examples
        self.create_larger_dfas(system_user)
        
        self.stdout.write(self.style.SUCCESS('Successfully created larger DFA examples'))
    
    def create_larger_dfas(self, user):
        """Create larger DFA examples that can be minimized."""
        
        # DFA 1: String length modulo 4 (non-minimal)
        dfa1 = Automaton.objects.create(
            name="String length modulo 4 (non-minimal)",
            alphabet="a,b",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create states with redundant states for minimization
        q0 = dfa1.states.create(name="q0", is_start=True, is_final=True)   # length 0 mod 4
        q1 = dfa1.states.create(name="q1", is_start=False, is_final=False)  # length 1 mod 4
        q2 = dfa1.states.create(name="q2", is_start=False, is_final=False)  # length 2 mod 4
        q3 = dfa1.states.create(name="q3", is_start=False, is_final=False)  # length 3 mod 4
        q4 = dfa1.states.create(name="q4", is_start=False, is_final=True)   # equivalent to q0
        q5 = dfa1.states.create(name="q5", is_start=False, is_final=False)  # equivalent to q1
        q6 = dfa1.states.create(name="q6", is_start=False, is_final=False)  # equivalent to q2
        q7 = dfa1.states.create(name="q7", is_start=False, is_final=False)  # equivalent to q3
        
        # Create transitions - first half
        dfa1.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa1.transitions.create(from_state=q0, to_state=q1, symbol="b")
        dfa1.transitions.create(from_state=q1, to_state=q2, symbol="a")
        dfa1.transitions.create(from_state=q1, to_state=q2, symbol="b")
        dfa1.transitions.create(from_state=q2, to_state=q3, symbol="a")
        dfa1.transitions.create(from_state=q2, to_state=q3, symbol="b")
        dfa1.transitions.create(from_state=q3, to_state=q4, symbol="a")
        dfa1.transitions.create(from_state=q3, to_state=q4, symbol="b")
        
        # Create transitions - second half (equivalent behavior)
        dfa1.transitions.create(from_state=q4, to_state=q5, symbol="a")
        dfa1.transitions.create(from_state=q4, to_state=q5, symbol="b")
        dfa1.transitions.create(from_state=q5, to_state=q6, symbol="a")
        dfa1.transitions.create(from_state=q5, to_state=q6, symbol="b")
        dfa1.transitions.create(from_state=q6, to_state=q7, symbol="a")
        dfa1.transitions.create(from_state=q6, to_state=q7, symbol="b")
        dfa1.transitions.create(from_state=q7, to_state=q0, symbol="a")
        dfa1.transitions.create(from_state=q7, to_state=q0, symbol="b")
        
        dfa1.update_json_representation()
        
        # DFA 2: Binary number divisible by 3 (with redundant states)
        dfa2 = Automaton.objects.create(
            name="Binary divisible by 3 (non-minimal)",
            alphabet="0,1",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create states with some redundancy
        q0 = dfa2.states.create(name="q0", is_start=True, is_final=True)   # remainder 0
        q1 = dfa2.states.create(name="q1", is_start=False, is_final=False)  # remainder 1
        q2 = dfa2.states.create(name="q2", is_start=False, is_final=False)  # remainder 2
        q3 = dfa2.states.create(name="q3", is_start=False, is_final=True)   # equivalent to q0
        q4 = dfa2.states.create(name="q4", is_start=False, is_final=False)  # equivalent to q1
        q5 = dfa2.states.create(name="q5", is_start=False, is_final=False)  # equivalent to q2
        
        # Standard transitions
        dfa2.transitions.create(from_state=q0, to_state=q0, symbol="0")
        dfa2.transitions.create(from_state=q0, to_state=q1, symbol="1")
        dfa2.transitions.create(from_state=q1, to_state=q2, symbol="0")
        dfa2.transitions.create(from_state=q1, to_state=q3, symbol="1")
        dfa2.transitions.create(from_state=q2, to_state=q4, symbol="0")
        dfa2.transitions.create(from_state=q2, to_state=q2, symbol="1")
        
        # Redundant equivalent states
        dfa2.transitions.create(from_state=q3, to_state=q3, symbol="0")
        dfa2.transitions.create(from_state=q3, to_state=q4, symbol="1")
        dfa2.transitions.create(from_state=q4, to_state=q5, symbol="0")
        dfa2.transitions.create(from_state=q4, to_state=q0, symbol="1")
        dfa2.transitions.create(from_state=q5, to_state=q1, symbol="0")
        dfa2.transitions.create(from_state=q5, to_state=q5, symbol="1")
        
        dfa2.update_json_representation()
        
        # DFA 3: Complex pattern matching (non-minimal)
        dfa3 = Automaton.objects.create(
            name="Contains 'abc' pattern (non-minimal)",
            alphabet="a,b,c",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create many states for pattern matching with redundancy
        q0 = dfa3.states.create(name="q0", is_start=True, is_final=False)   # initial
        q1 = dfa3.states.create(name="q1", is_start=False, is_final=False)  # saw 'a'
        q2 = dfa3.states.create(name="q2", is_start=False, is_final=False)  # saw 'ab'
        q3 = dfa3.states.create(name="q3", is_start=False, is_final=True)   # saw 'abc'
        q4 = dfa3.states.create(name="q4", is_start=False, is_final=False)  # redundant state
        q5 = dfa3.states.create(name="q5", is_start=False, is_final=False)  # redundant state
        q6 = dfa3.states.create(name="q6", is_start=False, is_final=True)   # equivalent to q3
        q7 = dfa3.states.create(name="q7", is_start=False, is_final=False)  # redundant state
        
        # Main pattern recognition
        dfa3.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q0, to_state=q4, symbol="b")
        dfa3.transitions.create(from_state=q0, to_state=q5, symbol="c")
        dfa3.transitions.create(from_state=q1, to_state=q2, symbol="b")
        dfa3.transitions.create(from_state=q1, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q1, to_state=q7, symbol="c")
        dfa3.transitions.create(from_state=q2, to_state=q3, symbol="c")
        dfa3.transitions.create(from_state=q2, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q2, to_state=q4, symbol="b")
        
        # Final state behavior
        dfa3.transitions.create(from_state=q3, to_state=q3, symbol="a")
        dfa3.transitions.create(from_state=q3, to_state=q6, symbol="b")
        dfa3.transitions.create(from_state=q3, to_state=q3, symbol="c")
        
        # Redundant state transitions
        dfa3.transitions.create(from_state=q4, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q4, to_state=q4, symbol="b")
        dfa3.transitions.create(from_state=q4, to_state=q5, symbol="c")
        dfa3.transitions.create(from_state=q5, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q5, to_state=q4, symbol="b")
        dfa3.transitions.create(from_state=q5, to_state=q5, symbol="c")
        dfa3.transitions.create(from_state=q6, to_state=q6, symbol="a")
        dfa3.transitions.create(from_state=q6, to_state=q6, symbol="b")
        dfa3.transitions.create(from_state=q6, to_state=q6, symbol="c")
        dfa3.transitions.create(from_state=q7, to_state=q1, symbol="a")
        dfa3.transitions.create(from_state=q7, to_state=q4, symbol="b")
        dfa3.transitions.create(from_state=q7, to_state=q5, symbol="c")
        
        dfa3.update_json_representation()
        
        # DFA 4: Even/odd state counter (highly redundant)
        dfa4 = Automaton.objects.create(
            name="Even/odd counter (highly redundant)",
            alphabet="x,y",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create many redundant states
        states = []
        for i in range(10):
            is_final = i % 2 == 0  # Even numbered states are final
            state = dfa4.states.create(
                name=f"q{i}", 
                is_start=(i == 0), 
                is_final=is_final
            )
            states.append(state)
        
        # Create transitions that cycle through states
        for i in range(10):
            next_state = states[(i + 1) % 10]
            dfa4.transitions.create(from_state=states[i], to_state=next_state, symbol="x")
            dfa4.transitions.create(from_state=states[i], to_state=next_state, symbol="y")
        
        dfa4.update_json_representation()
        
        self.stdout.write(self.style.SUCCESS('Created 4 larger DFA examples that can be minimized'))