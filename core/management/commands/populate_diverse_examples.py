from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import DFA, NFA, DFAState, DFATransition, NFAState, NFATransition


class Command(BaseCommand):
    help = 'Populate diverse DFA and NFA examples with epsilon transitions and multiple inputs'

    def handle(self, *args, **options):
        # Clear existing examples
        DFA.objects.all().delete()
        NFA.objects.all().delete()
        
        # Create a default user if none exists
        user, created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
        
        # Create diverse DFA examples
        self.create_dfa_examples(user)
        
        # Create diverse NFA examples
        self.create_nfa_examples(user)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated diverse examples'))
    
    def create_dfa_examples(self, user):
        """Create diverse DFA examples."""
        
        # DFA 1: Even number of a's
        dfa1 = DFA.objects.create(
            name="Even number of a's",
            alphabet="a,b",
            owner=user
        )
        
        q0 = DFAState.objects.create(automaton=dfa1, name="q0", is_start=True, is_final=True)
        q1 = DFAState.objects.create(automaton=dfa1, name="q1", is_start=False, is_final=False)
        
        DFATransition.objects.create(automaton=dfa1, from_state=q0, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa1, from_state=q0, to_state=q0, symbol="b")
        DFATransition.objects.create(automaton=dfa1, from_state=q1, to_state=q0, symbol="a")
        DFATransition.objects.create(automaton=dfa1, from_state=q1, to_state=q1, symbol="b")
        
        dfa1.update_json_representation()
        
        # DFA 2: Strings ending with "ab"
        dfa2 = DFA.objects.create(
            name="Strings ending with 'ab'",
            alphabet="a,b",
            owner=user
        )
        
        q0 = DFAState.objects.create(automaton=dfa2, name="q0", is_start=True, is_final=False)
        q1 = DFAState.objects.create(automaton=dfa2, name="q1", is_start=False, is_final=False)
        q2 = DFAState.objects.create(automaton=dfa2, name="q2", is_start=False, is_final=True)
        
        DFATransition.objects.create(automaton=dfa2, from_state=q0, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa2, from_state=q0, to_state=q0, symbol="b")
        DFATransition.objects.create(automaton=dfa2, from_state=q1, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa2, from_state=q1, to_state=q2, symbol="b")
        DFATransition.objects.create(automaton=dfa2, from_state=q2, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa2, from_state=q2, to_state=q0, symbol="b")
        
        dfa2.update_json_representation()
        
        # DFA 3: Binary numbers divisible by 3
        dfa3 = DFA.objects.create(
            name="Binary numbers divisible by 3",
            alphabet="0,1",
            owner=user
        )
        
        q0 = DFAState.objects.create(automaton=dfa3, name="q0", is_start=True, is_final=True)  # remainder 0
        q1 = DFAState.objects.create(automaton=dfa3, name="q1", is_start=False, is_final=False)  # remainder 1
        q2 = DFAState.objects.create(automaton=dfa3, name="q2", is_start=False, is_final=False)  # remainder 2
        
        DFATransition.objects.create(automaton=dfa3, from_state=q0, to_state=q0, symbol="0")
        DFATransition.objects.create(automaton=dfa3, from_state=q0, to_state=q1, symbol="1")
        DFATransition.objects.create(automaton=dfa3, from_state=q1, to_state=q2, symbol="0")
        DFATransition.objects.create(automaton=dfa3, from_state=q1, to_state=q0, symbol="1")
        DFATransition.objects.create(automaton=dfa3, from_state=q2, to_state=q1, symbol="0")
        DFATransition.objects.create(automaton=dfa3, from_state=q2, to_state=q2, symbol="1")
        
        dfa3.update_json_representation()
        
        # DFA 4: Strings with exactly one 'a'
        dfa4 = DFA.objects.create(
            name="Strings with exactly one 'a'",
            alphabet="a,b",
            owner=user
        )
        
        q0 = DFAState.objects.create(automaton=dfa4, name="q0", is_start=True, is_final=False)
        q1 = DFAState.objects.create(automaton=dfa4, name="q1", is_start=False, is_final=True)
        q2 = DFAState.objects.create(automaton=dfa4, name="q2", is_start=False, is_final=False)  # sink state
        
        DFATransition.objects.create(automaton=dfa4, from_state=q0, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa4, from_state=q0, to_state=q0, symbol="b")
        DFATransition.objects.create(automaton=dfa4, from_state=q1, to_state=q2, symbol="a")
        DFATransition.objects.create(automaton=dfa4, from_state=q1, to_state=q1, symbol="b")
        DFATransition.objects.create(automaton=dfa4, from_state=q2, to_state=q2, symbol="a")
        DFATransition.objects.create(automaton=dfa4, from_state=q2, to_state=q2, symbol="b")
        
        dfa4.update_json_representation()
    
    def create_nfa_examples(self, user):
        """Create diverse NFA examples with epsilon transitions."""
        
        # NFA 1: Strings containing "ab" or "ba"
        nfa1 = NFA.objects.create(
            name="Strings containing 'ab' or 'ba'",
            alphabet="a,b",
            owner=user
        )
        
        q0 = NFAState.objects.create(automaton=nfa1, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa1, name="q1", is_start=False, is_final=False)
        q2 = NFAState.objects.create(automaton=nfa1, name="q2", is_start=False, is_final=False)
        q3 = NFAState.objects.create(automaton=nfa1, name="q3", is_start=False, is_final=True)
        q4 = NFAState.objects.create(automaton=nfa1, name="q4", is_start=False, is_final=True)
        
        # Multiple transitions from q0
        NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q0, symbol="a,b")
        NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q1, symbol="a")
        NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q2, symbol="b")
        
        # Path for "ab"
        NFATransition.objects.create(automaton=nfa1, from_state=q1, to_state=q3, symbol="b")
        
        # Path for "ba"
        NFATransition.objects.create(automaton=nfa1, from_state=q2, to_state=q4, symbol="a")
        
        # Final states can consume any input
        NFATransition.objects.create(automaton=nfa1, from_state=q3, to_state=q3, symbol="a,b")
        NFATransition.objects.create(automaton=nfa1, from_state=q4, to_state=q4, symbol="a,b")
        
        nfa1.update_json_representation()
        
        # NFA 2: Strings ending with "aa" or "bb" (with epsilon transitions)
        nfa2 = NFA.objects.create(
            name="Strings ending with 'aa' or 'bb' (with ε)",
            alphabet="a,b",
            owner=user
        )
        
        q0 = NFAState.objects.create(automaton=nfa2, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa2, name="q1", is_start=False, is_final=False)
        q2 = NFAState.objects.create(automaton=nfa2, name="q2", is_start=False, is_final=False)
        q3 = NFAState.objects.create(automaton=nfa2, name="q3", is_start=False, is_final=False)
        q4 = NFAState.objects.create(automaton=nfa2, name="q4", is_start=False, is_final=False)
        qf = NFAState.objects.create(automaton=nfa2, name="qf", is_start=False, is_final=True)
        
        # General transitions
        NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q0, symbol="a,b")
        
        # Epsilon transitions to start checking for "aa"
        NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q1, symbol="ε")
        NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q3, symbol="ε")
        
        # Path for "aa"
        NFATransition.objects.create(automaton=nfa2, from_state=q1, to_state=q2, symbol="a")
        NFATransition.objects.create(automaton=nfa2, from_state=q2, to_state=qf, symbol="a")
        
        # Path for "bb"
        NFATransition.objects.create(automaton=nfa2, from_state=q3, to_state=q4, symbol="b")
        NFATransition.objects.create(automaton=nfa2, from_state=q4, to_state=qf, symbol="b")
        
        nfa2.update_json_representation()
        
        # NFA 3: Regular expression (a|b)*abb
        nfa3 = NFA.objects.create(
            name="Regular expression (a|b)*abb",
            alphabet="a,b",
            owner=user
        )
        
        q0 = NFAState.objects.create(automaton=nfa3, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa3, name="q1", is_start=False, is_final=False)
        q2 = NFAState.objects.create(automaton=nfa3, name="q2", is_start=False, is_final=False)
        q3 = NFAState.objects.create(automaton=nfa3, name="q3", is_start=False, is_final=True)
        
        # (a|b)*
        NFATransition.objects.create(automaton=nfa3, from_state=q0, to_state=q0, symbol="a,b")
        
        # abb
        NFATransition.objects.create(automaton=nfa3, from_state=q0, to_state=q1, symbol="a")
        NFATransition.objects.create(automaton=nfa3, from_state=q1, to_state=q2, symbol="b")
        NFATransition.objects.create(automaton=nfa3, from_state=q2, to_state=q3, symbol="b")
        
        nfa3.update_json_representation()
        
        # NFA 4: Complex epsilon transitions example
        nfa4 = NFA.objects.create(
            name="Complex epsilon transitions example",
            alphabet="0,1",
            owner=user
        )
        
        q0 = NFAState.objects.create(automaton=nfa4, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa4, name="q1", is_start=False, is_final=False)
        q2 = NFAState.objects.create(automaton=nfa4, name="q2", is_start=False, is_final=False)
        q3 = NFAState.objects.create(automaton=nfa4, name="q3", is_start=False, is_final=False)
        q4 = NFAState.objects.create(automaton=nfa4, name="q4", is_start=False, is_final=True)
        
        # Epsilon transitions creating multiple paths
        NFATransition.objects.create(automaton=nfa4, from_state=q0, to_state=q1, symbol="ε")
        NFATransition.objects.create(automaton=nfa4, from_state=q0, to_state=q2, symbol="ε")
        
        # Path 1: 0*
        NFATransition.objects.create(automaton=nfa4, from_state=q1, to_state=q1, symbol="0")
        NFATransition.objects.create(automaton=nfa4, from_state=q1, to_state=q4, symbol="ε")
        
        # Path 2: 1*
        NFATransition.objects.create(automaton=nfa4, from_state=q2, to_state=q2, symbol="1")
        NFATransition.objects.create(automaton=nfa4, from_state=q2, to_state=q3, symbol="ε")
        
        # Final epsilon transition
        NFATransition.objects.create(automaton=nfa4, from_state=q3, to_state=q4, symbol="ε")
        
        nfa4.update_json_representation()
        
        # NFA 5: Multiple start states example
        nfa5 = NFA.objects.create(
            name="Multiple start states example",
            alphabet="x,y",
            owner=user
        )
        
        q0 = NFAState.objects.create(automaton=nfa5, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa5, name="q1", is_start=True, is_final=False)  # Another start state
        q2 = NFAState.objects.create(automaton=nfa5, name="q2", is_start=False, is_final=True)
        q3 = NFAState.objects.create(automaton=nfa5, name="q3", is_start=False, is_final=True)
        
        # From first start state
        NFATransition.objects.create(automaton=nfa5, from_state=q0, to_state=q2, symbol="x")
        NFATransition.objects.create(automaton=nfa5, from_state=q0, to_state=q0, symbol="y")
        
        # From second start state  
        NFATransition.objects.create(automaton=nfa5, from_state=q1, to_state=q3, symbol="y")
        NFATransition.objects.create(automaton=nfa5, from_state=q1, to_state=q1, symbol="x")
        
        # Final states can loop
        NFATransition.objects.create(automaton=nfa5, from_state=q2, to_state=q2, symbol="x,y")
        NFATransition.objects.create(automaton=nfa5, from_state=q3, to_state=q3, symbol="x,y")
        
        nfa5.update_json_representation()
