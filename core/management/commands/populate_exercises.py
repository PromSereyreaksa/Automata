from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Automaton, State, Transition

class Command(BaseCommand):
    help = 'Populate the database with example DFA and NFA exercises'

    def handle(self, *args, **options):
        # Create a system user for examples if it doesn't exist
        system_user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@example.com',
                'first_name': 'System',
                'last_name': 'Examples'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created system user for examples'))

        # Clear existing examples
        Automaton.objects.filter(owner=system_user).delete()

        # Create DFA Examples
        self.create_dfa_examples(system_user)
        
        # Create NFA Examples
        self.create_nfa_examples(system_user)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated exercise examples'))

    def create_dfa_examples(self, user):
        """Create example DFAs"""
        
        # Example 1: DFA that accepts strings with even number of 'a's
        dfa1 = Automaton.objects.create(
            name="Even number of 'a's",
            alphabet="a,b",
            owner=user
        )
        
        # States
        q0 = State.objects.create(automaton=dfa1, name="q0", is_start=True, is_final=True)
        q1 = State.objects.create(automaton=dfa1, name="q1", is_start=False, is_final=False)
        
        # Transitions
        Transition.objects.create(automaton=dfa1, from_state=q0, to_state=q1, symbol="a")
        Transition.objects.create(automaton=dfa1, from_state=q0, to_state=q0, symbol="b")
        Transition.objects.create(automaton=dfa1, from_state=q1, to_state=q0, symbol="a")
        Transition.objects.create(automaton=dfa1, from_state=q1, to_state=q1, symbol="b")
        
        dfa1.update_json_representation()

        # Example 2: DFA that accepts strings ending with "ab"
        dfa2 = DFA.objects.create(
            name="Strings ending with 'ab'",
            alphabet="a,b",
            owner=user
        )
        
        # States
        q0 = DFAState.objects.create(automaton=dfa2, name="q0", is_start=True, is_final=False)
        q1 = DFAState.objects.create(automaton=dfa2, name="q1", is_start=False, is_final=False)
        q2 = DFAState.objects.create(automaton=dfa2, name="q2", is_start=False, is_final=True)
        
        # Transitions
        DFATransition.objects.create(automaton=dfa2, from_state=q0, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa2, from_state=q0, to_state=q0, symbol="b")
        DFATransition.objects.create(automaton=dfa2, from_state=q1, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa2, from_state=q1, to_state=q2, symbol="b")
        DFATransition.objects.create(automaton=dfa2, from_state=q2, to_state=q1, symbol="a")
        DFATransition.objects.create(automaton=dfa2, from_state=q2, to_state=q0, symbol="b")
        
        dfa2.update_json_representation()

        # Example 3: DFA that accepts strings with length divisible by 3
        dfa3 = DFA.objects.create(
            name="Length divisible by 3",
            alphabet="0,1",
            owner=user
        )
        
        # States
        q0 = DFAState.objects.create(automaton=dfa3, name="q0", is_start=True, is_final=True)
        q1 = DFAState.objects.create(automaton=dfa3, name="q1", is_start=False, is_final=False)
        q2 = DFAState.objects.create(automaton=dfa3, name="q2", is_start=False, is_final=False)
        
        # Transitions
        DFATransition.objects.create(automaton=dfa3, from_state=q0, to_state=q1, symbol="0,1")
        DFATransition.objects.create(automaton=dfa3, from_state=q1, to_state=q2, symbol="0,1")
        DFATransition.objects.create(automaton=dfa3, from_state=q2, to_state=q0, symbol="0,1")
        
        dfa3.update_json_representation()

        # Example 4: DFA that accepts binary strings divisible by 3
        dfa4 = DFA.objects.create(
            name="Binary numbers divisible by 3",
            alphabet="0,1",
            owner=user
        )
        
        # States (remainder 0, 1, 2)
        r0 = DFAState.objects.create(automaton=dfa4, name="r0", is_start=True, is_final=True)
        r1 = DFAState.objects.create(automaton=dfa4, name="r1", is_start=False, is_final=False)
        r2 = DFAState.objects.create(automaton=dfa4, name="r2", is_start=False, is_final=False)
        
        # Transitions (based on remainder when divided by 3)
        DFATransition.objects.create(automaton=dfa4, from_state=r0, to_state=r0, symbol="0")
        DFATransition.objects.create(automaton=dfa4, from_state=r0, to_state=r1, symbol="1")
        DFATransition.objects.create(automaton=dfa4, from_state=r1, to_state=r2, symbol="0")
        DFATransition.objects.create(automaton=dfa4, from_state=r1, to_state=r0, symbol="1")
        DFATransition.objects.create(automaton=dfa4, from_state=r2, to_state=r1, symbol="0")
        DFATransition.objects.create(automaton=dfa4, from_state=r2, to_state=r2, symbol="1")
        
        dfa4.update_json_representation()

        # Example 5: DFA with multiple symbol transitions
        dfa5 = DFA.objects.create(
            name="Vowel-Consonant Pattern",
            alphabet="a,e,i,o,u,b,c,d,f,g",
            owner=user
        )
        
        # States
        start = DFAState.objects.create(automaton=dfa5, name="start", is_start=True, is_final=False)
        vowel = DFAState.objects.create(automaton=dfa5, name="vowel", is_start=False, is_final=False)
        consonant = DFAState.objects.create(automaton=dfa5, name="consonant", is_start=False, is_final=True)
        
        # Transitions
        DFATransition.objects.create(automaton=dfa5, from_state=start, to_state=vowel, symbol="a,e,i,o,u")
        DFATransition.objects.create(automaton=dfa5, from_state=start, to_state=consonant, symbol="b,c,d,f,g")
        DFATransition.objects.create(automaton=dfa5, from_state=vowel, to_state=consonant, symbol="b,c,d,f,g")
        DFATransition.objects.create(automaton=dfa5, from_state=vowel, to_state=vowel, symbol="a,e,i,o,u")
        DFATransition.objects.create(automaton=dfa5, from_state=consonant, to_state=vowel, symbol="a,e,i,o,u")
        DFATransition.objects.create(automaton=dfa5, from_state=consonant, to_state=consonant, symbol="b,c,d,f,g")
        
        dfa5.update_json_representation()

        self.stdout.write(self.style.SUCCESS('Created 5 DFA examples'))

    def create_nfa_examples(self, user):
        """Create example NFAs"""
        
        # Example 1: NFA that accepts strings containing "ab"
        nfa1 = NFA.objects.create(
            name="Contains substring 'ab'",
            alphabet="a,b",
            owner=user
        )
        
        # States
        q0 = NFAState.objects.create(automaton=nfa1, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa1, name="q1", is_start=False, is_final=False)
        q2 = NFAState.objects.create(automaton=nfa1, name="q2", is_start=False, is_final=True)
        
        # Transitions
        NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q0, symbol="a,b")
        NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q1, symbol="a")
        NFATransition.objects.create(automaton=nfa1, from_state=q1, to_state=q2, symbol="b")
        NFATransition.objects.create(automaton=nfa1, from_state=q2, to_state=q2, symbol="a,b")
        
        nfa1.update_json_representation()

        # Example 2: NFA that accepts strings ending with "a" or "bb"
        nfa2 = NFA.objects.create(
            name="Ends with 'a' or 'bb'",
            alphabet="a,b",
            owner=user
        )
        
        # States
        q0 = NFAState.objects.create(automaton=nfa2, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa2, name="q1", is_start=False, is_final=True)  # ends with 'a'
        q2 = NFAState.objects.create(automaton=nfa2, name="q2", is_start=False, is_final=False)  # first 'b'
        q3 = NFAState.objects.create(automaton=nfa2, name="q3", is_start=False, is_final=True)   # ends with 'bb'
        
        # Transitions
        NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q0, symbol="a,b")
        NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q1, symbol="a")  # path to end with 'a'
        NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q2, symbol="b")  # path to end with 'bb'
        NFATransition.objects.create(automaton=nfa2, from_state=q2, to_state=q3, symbol="b")
        
        nfa2.update_json_representation()

        # Example 3: NFA with epsilon transitions
        nfa3 = NFA.objects.create(
            name="Epsilon transitions example",
            alphabet="a,b",
            owner=user
        )
        
        # States
        s0 = NFAState.objects.create(automaton=nfa3, name="s0", is_start=True, is_final=False)
        s1 = NFAState.objects.create(automaton=nfa3, name="s1", is_start=False, is_final=False)
        s2 = NFAState.objects.create(automaton=nfa3, name="s2", is_start=False, is_final=False)
        s3 = NFAState.objects.create(automaton=nfa3, name="s3", is_start=False, is_final=True)
        
        # Transitions with epsilon
        NFATransition.objects.create(automaton=nfa3, from_state=s0, to_state=s1, symbol="ε")  # epsilon transition
        NFATransition.objects.create(automaton=nfa3, from_state=s0, to_state=s2, symbol="a")
        NFATransition.objects.create(automaton=nfa3, from_state=s1, to_state=s3, symbol="b")
        NFATransition.objects.create(automaton=nfa3, from_state=s2, to_state=s3, symbol="ε")  # epsilon transition
        NFATransition.objects.create(automaton=nfa3, from_state=s3, to_state=s3, symbol="a,b")
        
        nfa3.update_json_representation()

        # Example 4: NFA that accepts (a|b)*abb
        nfa4 = NFA.objects.create(
            name="Strings ending with 'abb'",
            alphabet="a,b",
            owner=user
        )
        
        # States
        q0 = NFAState.objects.create(automaton=nfa4, name="q0", is_start=True, is_final=False)
        q1 = NFAState.objects.create(automaton=nfa4, name="q1", is_start=False, is_final=False)
        q2 = NFAState.objects.create(automaton=nfa4, name="q2", is_start=False, is_final=False)
        q3 = NFAState.objects.create(automaton=nfa4, name="q3", is_start=False, is_final=True)
        
        # Transitions
        NFATransition.objects.create(automaton=nfa4, from_state=q0, to_state=q0, symbol="a,b")
        NFATransition.objects.create(automaton=nfa4, from_state=q0, to_state=q1, symbol="a")
        NFATransition.objects.create(automaton=nfa4, from_state=q1, to_state=q2, symbol="b")
        NFATransition.objects.create(automaton=nfa4, from_state=q2, to_state=q3, symbol="b")
        
        nfa4.update_json_representation()

        # Example 5: NFA with multiple start states and epsilon transitions
        nfa5 = NFA.objects.create(
            name="Multiple start states with epsilon",
            alphabet="0,1",
            owner=user
        )
        
        # States
        start1 = NFAState.objects.create(automaton=nfa5, name="start1", is_start=True, is_final=False)
        start2 = NFAState.objects.create(automaton=nfa5, name="start2", is_start=True, is_final=False)
        middle = NFAState.objects.create(automaton=nfa5, name="middle", is_start=False, is_final=False)
        accept = NFAState.objects.create(automaton=nfa5, name="accept", is_start=False, is_final=True)
        
        # Transitions with epsilon
        NFATransition.objects.create(automaton=nfa5, from_state=start1, to_state=middle, symbol="ε")
        NFATransition.objects.create(automaton=nfa5, from_state=start2, to_state=middle, symbol="0")
        NFATransition.objects.create(automaton=nfa5, from_state=middle, to_state=accept, symbol="1")
        NFATransition.objects.create(automaton=nfa5, from_state=middle, to_state=middle, symbol="0,1")
        NFATransition.objects.create(automaton=nfa5, from_state=accept, to_state=accept, symbol="0,1")
        
        nfa5.update_json_representation()

        # Example 6: NFA for union of languages (a* | b*)
        nfa6 = NFA.objects.create(
            name="Union: a* or b*",
            alphabet="a,b",
            owner=user
        )
        
        # States
        start = NFAState.objects.create(automaton=nfa6, name="start", is_start=True, is_final=True)
        a_loop = NFAState.objects.create(automaton=nfa6, name="a_loop", is_start=False, is_final=True)
        b_loop = NFAState.objects.create(automaton=nfa6, name="b_loop", is_start=False, is_final=True)
        
        # Transitions
        NFATransition.objects.create(automaton=nfa6, from_state=start, to_state=a_loop, symbol="ε")
        NFATransition.objects.create(automaton=nfa6, from_state=start, to_state=b_loop, symbol="ε")
        NFATransition.objects.create(automaton=nfa6, from_state=a_loop, to_state=a_loop, symbol="a")
        NFATransition.objects.create(automaton=nfa6, from_state=b_loop, to_state=b_loop, symbol="b")
        
        nfa6.update_json_representation()

        # Example 7: NFA for concatenation a*b*
        nfa7 = NFA.objects.create(
            name="Concatenation: a*b*",
            alphabet="a,b",
            owner=user
        )
        
        # States
        s0 = NFAState.objects.create(automaton=nfa7, name="s0", is_start=True, is_final=True)
        s1 = NFAState.objects.create(automaton=nfa7, name="s1", is_start=False, is_final=True)
        
        # Transitions
        NFATransition.objects.create(automaton=nfa7, from_state=s0, to_state=s0, symbol="a")
        NFATransition.objects.create(automaton=nfa7, from_state=s0, to_state=s1, symbol="ε")
        NFATransition.objects.create(automaton=nfa7, from_state=s1, to_state=s1, symbol="b")
        
        nfa7.update_json_representation()

        # Example 8: Complex NFA with multiple epsilon transitions
        nfa8 = NFA.objects.create(
            name="Complex epsilon transitions",
            alphabet="x,y",
            owner=user
        )
        
        # States
        init = NFAState.objects.create(automaton=nfa8, name="init", is_start=True, is_final=False)
        path1 = NFAState.objects.create(automaton=nfa8, name="path1", is_start=False, is_final=False)
        path2 = NFAState.objects.create(automaton=nfa8, name="path2", is_start=False, is_final=False)
        merge = NFAState.objects.create(automaton=nfa8, name="merge", is_start=False, is_final=False)
        final = NFAState.objects.create(automaton=nfa8, name="final", is_start=False, is_final=True)
        
        # Transitions
        NFATransition.objects.create(automaton=nfa8, from_state=init, to_state=path1, symbol="ε")
        NFATransition.objects.create(automaton=nfa8, from_state=init, to_state=path2, symbol="ε")
        NFATransition.objects.create(automaton=nfa8, from_state=path1, to_state=merge, symbol="x")
        NFATransition.objects.create(automaton=nfa8, from_state=path2, to_state=merge, symbol="y")
        NFATransition.objects.create(automaton=nfa8, from_state=merge, to_state=final, symbol="ε")
        NFATransition.objects.create(automaton=nfa8, from_state=final, to_state=final, symbol="x,y")
        
        nfa8.update_json_representation()

        self.stdout.write(self.style.SUCCESS('Created 8 NFA examples'))

        self.stdout.write(self.style.SUCCESS('All examples created successfully!'))
        self.stdout.write(self.style.SUCCESS('DFA examples: 5 | NFA examples: 8'))
        self.stdout.write(self.style.SUCCESS('Features included: epsilon transitions, multiple inputs, multiple start states'))