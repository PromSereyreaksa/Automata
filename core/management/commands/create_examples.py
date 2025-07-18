from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Automaton, State, Transition

class Command(BaseCommand):
    help = 'Create example DFA and NFA automata'

    def handle(self, *args, **options):
        # Get or create system user
        system_user, created = User.objects.get_or_create(username='system')
        
        # Clear existing examples
        Automaton.objects.filter(owner=system_user).delete()
        
        # Create DFA examples
        self.create_dfa_examples(system_user)
        
        # Create NFA examples
        self.create_nfa_examples(system_user)
        
        # Create Rohini College PDF examples
        self.create_rohini_examples(system_user)
        
        # Create DFA minimization examples
        self.create_minimization_examples(system_user)
        
        self.stdout.write(self.style.SUCCESS('Successfully created example automata'))

    def create_dfa_examples(self, system_user):
        """Create DFA examples"""
        
        # DFA 1: Simple binary strings ending in 01
        dfa1 = Automaton.objects.create(
            name="DFA: Binary strings ending in 01",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States
        q0 = State.objects.create(automaton=dfa1, name="q0", is_start=True)
        q1 = State.objects.create(automaton=dfa1, name="q1")
        q2 = State.objects.create(automaton=dfa1, name="q2", is_final=True)
        
        # Transitions
        Transition.objects.create(automaton=dfa1, from_state=q0, to_state=q0, symbol="1")
        Transition.objects.create(automaton=dfa1, from_state=q0, to_state=q1, symbol="0")
        Transition.objects.create(automaton=dfa1, from_state=q1, to_state=q1, symbol="0")
        Transition.objects.create(automaton=dfa1, from_state=q1, to_state=q2, symbol="1")
        Transition.objects.create(automaton=dfa1, from_state=q2, to_state=q0, symbol="1")
        Transition.objects.create(automaton=dfa1, from_state=q2, to_state=q1, symbol="0")
        
        dfa1.update_json_representation()
        
        # DFA 2: Even number of 1s
        dfa2 = Automaton.objects.create(
            name="DFA: Even number of 1s",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States
        even = State.objects.create(automaton=dfa2, name="even", is_start=True, is_final=True)
        odd = State.objects.create(automaton=dfa2, name="odd")
        
        # Transitions
        Transition.objects.create(automaton=dfa2, from_state=even, to_state=even, symbol="0")
        Transition.objects.create(automaton=dfa2, from_state=even, to_state=odd, symbol="1")
        Transition.objects.create(automaton=dfa2, from_state=odd, to_state=odd, symbol="0")
        Transition.objects.create(automaton=dfa2, from_state=odd, to_state=even, symbol="1")
        
        dfa2.update_json_representation()
        
        # DFA 3: Divisible by 3 (binary)
        dfa3 = Automaton.objects.create(
            name="DFA: Binary numbers divisible by 3",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States (remainders 0, 1, 2)
        r0 = State.objects.create(automaton=dfa3, name="r0", is_start=True, is_final=True)
        r1 = State.objects.create(automaton=dfa3, name="r1")
        r2 = State.objects.create(automaton=dfa3, name="r2")
        
        # Transitions (mod 3 arithmetic)
        Transition.objects.create(automaton=dfa3, from_state=r0, to_state=r0, symbol="0")
        Transition.objects.create(automaton=dfa3, from_state=r0, to_state=r1, symbol="1")
        Transition.objects.create(automaton=dfa3, from_state=r1, to_state=r2, symbol="0")
        Transition.objects.create(automaton=dfa3, from_state=r1, to_state=r0, symbol="1")
        Transition.objects.create(automaton=dfa3, from_state=r2, to_state=r1, symbol="0")
        Transition.objects.create(automaton=dfa3, from_state=r2, to_state=r2, symbol="1")
        
        dfa3.update_json_representation()

    def create_nfa_examples(self, system_user):
        """Create NFA examples"""
        
        # NFA 1: Contains substring "ab"
        nfa1 = Automaton.objects.create(
            name="NFA: Contains substring 'ab'",
            alphabet="a,b",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States
        q0 = State.objects.create(automaton=nfa1, name="q0", is_start=True)
        q1 = State.objects.create(automaton=nfa1, name="q1")
        q2 = State.objects.create(automaton=nfa1, name="q2", is_final=True)
        
        # Transitions
        Transition.objects.create(automaton=nfa1, from_state=q0, to_state=q0, symbol="a,b")
        Transition.objects.create(automaton=nfa1, from_state=q0, to_state=q1, symbol="a")
        Transition.objects.create(automaton=nfa1, from_state=q1, to_state=q2, symbol="b")
        Transition.objects.create(automaton=nfa1, from_state=q2, to_state=q2, symbol="a,b")
        
        nfa1.update_json_representation()
        
        # NFA 2: With epsilon transitions
        nfa2 = Automaton.objects.create(
            name="NFA: With epsilon transitions",
            alphabet="a,b",
            owner=system_user,
            is_example=True,
            has_epsilon=True
        )
        
        # States
        s0 = State.objects.create(automaton=nfa2, name="s0", is_start=True)
        s1 = State.objects.create(automaton=nfa2, name="s1")
        s2 = State.objects.create(automaton=nfa2, name="s2")
        s3 = State.objects.create(automaton=nfa2, name="s3", is_final=True)
        
        # Transitions with epsilon
        Transition.objects.create(automaton=nfa2, from_state=s0, to_state=s1, symbol="ε")
        Transition.objects.create(automaton=nfa2, from_state=s0, to_state=s2, symbol="a")
        Transition.objects.create(automaton=nfa2, from_state=s1, to_state=s3, symbol="b")
        Transition.objects.create(automaton=nfa2, from_state=s2, to_state=s3, symbol="ε")
        
        nfa2.update_json_representation()
        
        # NFA 3: Multiple start states simulation
        nfa3 = Automaton.objects.create(
            name="NFA: Ends with 'aa' or 'bb'",
            alphabet="a,b",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States
        q0 = State.objects.create(automaton=nfa3, name="q0", is_start=True)
        q1 = State.objects.create(automaton=nfa3, name="q1")
        q2 = State.objects.create(automaton=nfa3, name="q2", is_final=True)
        q3 = State.objects.create(automaton=nfa3, name="q3")
        q4 = State.objects.create(automaton=nfa3, name="q4", is_final=True)
        
        # Transitions
        Transition.objects.create(automaton=nfa3, from_state=q0, to_state=q0, symbol="a,b")
        Transition.objects.create(automaton=nfa3, from_state=q0, to_state=q1, symbol="a")
        Transition.objects.create(automaton=nfa3, from_state=q0, to_state=q3, symbol="b")
        Transition.objects.create(automaton=nfa3, from_state=q1, to_state=q2, symbol="a")
        Transition.objects.create(automaton=nfa3, from_state=q3, to_state=q4, symbol="b")
        
        nfa3.update_json_representation()
        
        # NFA 4: Complex with epsilon transitions
        nfa4 = Automaton.objects.create(
            name="NFA: Complex with epsilon transitions",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=True
        )
        
        # States
        p0 = State.objects.create(automaton=nfa4, name="p0", is_start=True)
        p1 = State.objects.create(automaton=nfa4, name="p1")
        p2 = State.objects.create(automaton=nfa4, name="p2")
        p3 = State.objects.create(automaton=nfa4, name="p3")
        p4 = State.objects.create(automaton=nfa4, name="p4", is_final=True)
        
        # Transitions with multiple epsilon transitions
        Transition.objects.create(automaton=nfa4, from_state=p0, to_state=p1, symbol="ε")
        Transition.objects.create(automaton=nfa4, from_state=p0, to_state=p2, symbol="0")
        Transition.objects.create(automaton=nfa4, from_state=p1, to_state=p3, symbol="1")
        Transition.objects.create(automaton=nfa4, from_state=p2, to_state=p3, symbol="ε")
        Transition.objects.create(automaton=nfa4, from_state=p3, to_state=p4, symbol="ε")
        Transition.objects.create(automaton=nfa4, from_state=p3, to_state=p1, symbol="0")
        
        nfa4.update_json_representation()
        
        # NFA 5: Non-deterministic choices
        nfa5 = Automaton.objects.create(
            name="NFA: Non-deterministic choices",
            alphabet="x,y",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States
        n0 = State.objects.create(automaton=nfa5, name="n0", is_start=True)
        n1 = State.objects.create(automaton=nfa5, name="n1")
        n2 = State.objects.create(automaton=nfa5, name="n2")
        n3 = State.objects.create(automaton=nfa5, name="n3", is_final=True)
        
        # Multiple transitions for same symbol
        Transition.objects.create(automaton=nfa5, from_state=n0, to_state=n1, symbol="x")
        Transition.objects.create(automaton=nfa5, from_state=n0, to_state=n2, symbol="x")
        Transition.objects.create(automaton=nfa5, from_state=n1, to_state=n3, symbol="y")
        Transition.objects.create(automaton=nfa5, from_state=n2, to_state=n3, symbol="y")
        
        nfa5.update_json_representation()

    def create_rohini_examples(self, system_user):
        """Create Rohini College PDF NFA examples"""
        
        # Rohini Example 1: NFA with 3 states
        rohini1 = Automaton.objects.create(
            name="Rohini Example 1 - NFA to DFA",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States
        q0 = State.objects.create(automaton=rohini1, name="q0", is_start=True)
        q1 = State.objects.create(automaton=rohini1, name="q1")
        q2 = State.objects.create(automaton=rohini1, name="q2", is_final=True)
        
        # Transitions
        Transition.objects.create(automaton=rohini1, from_state=q0, to_state=q0, symbol="0")
        Transition.objects.create(automaton=rohini1, from_state=q0, to_state=q1, symbol="1")
        Transition.objects.create(automaton=rohini1, from_state=q1, to_state=q1, symbol="0")
        Transition.objects.create(automaton=rohini1, from_state=q1, to_state=q2, symbol="0")
        Transition.objects.create(automaton=rohini1, from_state=q1, to_state=q1, symbol="1")
        Transition.objects.create(automaton=rohini1, from_state=q2, to_state=q2, symbol="0")
        Transition.objects.create(automaton=rohini1, from_state=q2, to_state=q1, symbol="1")
        Transition.objects.create(automaton=rohini1, from_state=q2, to_state=q2, symbol="1")
        
        rohini1.update_json_representation()
        
        # Rohini Example 2: NFA with 2 states
        rohini2 = Automaton.objects.create(
            name="Rohini Example 2 - NFA to DFA",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # States
        r0 = State.objects.create(automaton=rohini2, name="q0", is_start=True)
        r1 = State.objects.create(automaton=rohini2, name="q1", is_final=True)
        
        # Transitions
        Transition.objects.create(automaton=rohini2, from_state=r0, to_state=r0, symbol="0")
        Transition.objects.create(automaton=rohini2, from_state=r0, to_state=r1, symbol="0")
        Transition.objects.create(automaton=rohini2, from_state=r0, to_state=r1, symbol="1")
        Transition.objects.create(automaton=rohini2, from_state=r1, to_state=r0, symbol="1")
        Transition.objects.create(automaton=rohini2, from_state=r1, to_state=r1, symbol="1")
        
        rohini2.update_json_representation()

    def create_minimization_examples(self, system_user):
        """Create DFA examples suitable for Myhill-Nerode minimization"""
        
        # 6-State DFA for Minimization
        min_dfa1 = Automaton.objects.create(
            name="6-State DFA for Minimization",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create states
        a = State.objects.create(automaton=min_dfa1, name="a", is_start=True)
        b = State.objects.create(automaton=min_dfa1, name="b")
        c = State.objects.create(automaton=min_dfa1, name="c")
        d = State.objects.create(automaton=min_dfa1, name="d")
        e = State.objects.create(automaton=min_dfa1, name="e")
        f = State.objects.create(automaton=min_dfa1, name="f", is_final=True)
        
        # Create transitions
        Transition.objects.create(automaton=min_dfa1, from_state=a, to_state=c, symbol="0")
        Transition.objects.create(automaton=min_dfa1, from_state=a, to_state=a, symbol="1")
        Transition.objects.create(automaton=min_dfa1, from_state=b, to_state=d, symbol="0")
        Transition.objects.create(automaton=min_dfa1, from_state=b, to_state=b, symbol="1")
        Transition.objects.create(automaton=min_dfa1, from_state=c, to_state=c, symbol="0")
        Transition.objects.create(automaton=min_dfa1, from_state=c, to_state=f, symbol="1")
        Transition.objects.create(automaton=min_dfa1, from_state=d, to_state=d, symbol="0")
        Transition.objects.create(automaton=min_dfa1, from_state=d, to_state=f, symbol="1")
        Transition.objects.create(automaton=min_dfa1, from_state=e, to_state=e, symbol="0")
        Transition.objects.create(automaton=min_dfa1, from_state=e, to_state=f, symbol="1")
        Transition.objects.create(automaton=min_dfa1, from_state=f, to_state=c, symbol="0")
        Transition.objects.create(automaton=min_dfa1, from_state=f, to_state=a, symbol="1")
        
        min_dfa1.update_json_representation()
        
        # 4-State DFA for Minimization
        min_dfa2 = Automaton.objects.create(
            name="4-State DFA for Minimization",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create states
        q0 = State.objects.create(automaton=min_dfa2, name="q0", is_start=True, is_final=True)
        q1 = State.objects.create(automaton=min_dfa2, name="q1")
        q2 = State.objects.create(automaton=min_dfa2, name="q2", is_final=True)
        q3 = State.objects.create(automaton=min_dfa2, name="q3")
        
        # Create transitions
        Transition.objects.create(automaton=min_dfa2, from_state=q0, to_state=q0, symbol="0")
        Transition.objects.create(automaton=min_dfa2, from_state=q0, to_state=q1, symbol="1")
        Transition.objects.create(automaton=min_dfa2, from_state=q1, to_state=q1, symbol="0")
        Transition.objects.create(automaton=min_dfa2, from_state=q1, to_state=q2, symbol="1")
        Transition.objects.create(automaton=min_dfa2, from_state=q2, to_state=q2, symbol="0")
        Transition.objects.create(automaton=min_dfa2, from_state=q2, to_state=q3, symbol="1")
        Transition.objects.create(automaton=min_dfa2, from_state=q3, to_state=q3, symbol="0")
        Transition.objects.create(automaton=min_dfa2, from_state=q3, to_state=q0, symbol="1")
        
        min_dfa2.update_json_representation()
        
        # DFA with Unreachable States
        min_dfa3 = Automaton.objects.create(
            name="DFA with Unreachable States",
            alphabet="0,1",
            owner=system_user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create states
        r0 = State.objects.create(automaton=min_dfa3, name="q0", is_start=True)
        r1 = State.objects.create(automaton=min_dfa3, name="q1", is_final=True)
        r2 = State.objects.create(automaton=min_dfa3, name="q2")  # unreachable
        r3 = State.objects.create(automaton=min_dfa3, name="q3", is_final=True)  # unreachable
        
        # Create transitions
        Transition.objects.create(automaton=min_dfa3, from_state=r0, to_state=r0, symbol="0")
        Transition.objects.create(automaton=min_dfa3, from_state=r0, to_state=r1, symbol="1")
        Transition.objects.create(automaton=min_dfa3, from_state=r1, to_state=r0, symbol="0")
        Transition.objects.create(automaton=min_dfa3, from_state=r1, to_state=r1, symbol="1")
        Transition.objects.create(automaton=min_dfa3, from_state=r2, to_state=r2, symbol="0")
        Transition.objects.create(automaton=min_dfa3, from_state=r2, to_state=r3, symbol="1")
        Transition.objects.create(automaton=min_dfa3, from_state=r3, to_state=r2, symbol="0")
        Transition.objects.create(automaton=min_dfa3, from_state=r3, to_state=r3, symbol="1")
        
        min_dfa3.update_json_representation()