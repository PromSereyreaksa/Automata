import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automata.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import DFA, NFA, DFAState, NFAState, DFATransition, NFATransition

def populate_examples():
    """Populate the database with example DFA and NFA exercises"""
    
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
        print('Created system user for examples')

    # Clear existing examples
    DFA.objects.filter(owner=system_user).delete()
    NFA.objects.filter(owner=system_user).delete()

    # Create DFA Examples
    create_dfa_examples(system_user)
    
    # Create NFA Examples
    create_nfa_examples(system_user)
    
    print('Successfully populated exercise examples')

def create_dfa_examples(user):
    """Create example DFAs"""
    
    # Example 1: DFA that accepts strings with even number of 'a's
    dfa1 = DFA.objects.create(
        name="Even number of 'a's",
        alphabet="a,b",
        owner=user
    )
    
    # States
    q0 = DFAState.objects.create(automaton=dfa1, name="q0", is_start=True, is_final=True)
    q1 = DFAState.objects.create(automaton=dfa1, name="q1", is_start=False, is_final=False)
    
    # Transitions
    DFATransition.objects.create(automaton=dfa1, from_state=q0, to_state=q1, symbol="a")
    DFATransition.objects.create(automaton=dfa1, from_state=q0, to_state=q0, symbol="b")
    DFATransition.objects.create(automaton=dfa1, from_state=q1, to_state=q0, symbol="a")
    DFATransition.objects.create(automaton=dfa1, from_state=q1, to_state=q1, symbol="b")
    
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
    DFATransition.objects.create(automaton=dfa3, from_state=q0, to_state=q1, symbol="0")
    DFATransition.objects.create(automaton=dfa3, from_state=q0, to_state=q1, symbol="1")
    DFATransition.objects.create(automaton=dfa3, from_state=q1, to_state=q2, symbol="0")
    DFATransition.objects.create(automaton=dfa3, from_state=q1, to_state=q2, symbol="1")
    DFATransition.objects.create(automaton=dfa3, from_state=q2, to_state=q0, symbol="0")
    DFATransition.objects.create(automaton=dfa3, from_state=q2, to_state=q0, symbol="1")
    
    dfa3.update_json_representation()

    print('Created 3 DFA examples')

def create_nfa_examples(user):
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
    NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q0, symbol="a")
    NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q0, symbol="b")
    NFATransition.objects.create(automaton=nfa1, from_state=q0, to_state=q1, symbol="a")
    NFATransition.objects.create(automaton=nfa1, from_state=q1, to_state=q2, symbol="b")
    NFATransition.objects.create(automaton=nfa1, from_state=q2, to_state=q2, symbol="a")
    NFATransition.objects.create(automaton=nfa1, from_state=q2, to_state=q2, symbol="b")
    
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
    NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q0, symbol="a")
    NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q0, symbol="b")
    NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q1, symbol="a")  # path to end with 'a'
    NFATransition.objects.create(automaton=nfa2, from_state=q0, to_state=q2, symbol="b")  # path to end with 'bb'
    NFATransition.objects.create(automaton=nfa2, from_state=q2, to_state=q3, symbol="b")
    
    nfa2.update_json_representation()

    print('Created 2 NFA examples')

if __name__ == '__main__':
    populate_examples()
