import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automata.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Automaton, State, Transition

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
    Automaton.objects.filter(owner=system_user).delete()

    # Create DFA Examples
    create_dfa_examples(system_user)
    
    # Create NFA Examples
    create_nfa_examples(system_user)
    
    print('Successfully populated exercise examples')

def create_dfa_examples(user):
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
    dfa2 = Automaton.objects.create(
        name="Strings ending with 'ab'",
        alphabet="a,b",
        owner=user
    )
    
    # States
    q0 = State.objects.create(automaton=dfa2, name="q0", is_start=True, is_final=False)
    q1 = State.objects.create(automaton=dfa2, name="q1", is_start=False, is_final=False)
    q2 = State.objects.create(automaton=dfa2, name="q2", is_start=False, is_final=True)
    
    # Transitions
    Transition.objects.create(automaton=dfa2, from_state=q0, to_state=q1, symbol="a")
    Transition.objects.create(automaton=dfa2, from_state=q0, to_state=q0, symbol="b")
    Transition.objects.create(automaton=dfa2, from_state=q1, to_state=q1, symbol="a")
    Transition.objects.create(automaton=dfa2, from_state=q1, to_state=q2, symbol="b")
    Transition.objects.create(automaton=dfa2, from_state=q2, to_state=q1, symbol="a")
    Transition.objects.create(automaton=dfa2, from_state=q2, to_state=q0, symbol="b")
    
    dfa2.update_json_representation()

    # Example 3: DFA that accepts strings with length divisible by 3
    dfa3 = Automaton.objects.create(
        name="Length divisible by 3",
        alphabet="0,1",
        owner=user
    )
    
    # States
    q0 = State.objects.create(automaton=dfa3, name="q0", is_start=True, is_final=True)
    q1 = State.objects.create(automaton=dfa3, name="q1", is_start=False, is_final=False)
    q2 = State.objects.create(automaton=dfa3, name="q2", is_start=False, is_final=False)
    
    # Transitions
    Transition.objects.create(automaton=dfa3, from_state=q0, to_state=q1, symbol="0")
    Transition.objects.create(automaton=dfa3, from_state=q0, to_state=q1, symbol="1")
    Transition.objects.create(automaton=dfa3, from_state=q1, to_state=q2, symbol="0")
    Transition.objects.create(automaton=dfa3, from_state=q1, to_state=q2, symbol="1")
    Transition.objects.create(automaton=dfa3, from_state=q2, to_state=q0, symbol="0")
    Transition.objects.create(automaton=dfa3, from_state=q2, to_state=q0, symbol="1")
    
    dfa3.update_json_representation()

    # Example 4: Large DFA with many equivalent states for minimization testing
    # This DFA accepts strings that contain "101" as a substring
    # It has 12 states but can be minimized to 4 states
    dfa4 = Automaton.objects.create(
        name="Large DFA - Contains '101' (12 states → 4 states)",
        alphabet="0,1",
        owner=user
    )
    
    # Create 12 states (many will be equivalent)
    q0 = State.objects.create(automaton=dfa4, name="q0", is_start=True, is_final=False)   # Start state
    q1 = State.objects.create(automaton=dfa4, name="q1", is_start=False, is_final=False)  # Read '1'
    q2 = State.objects.create(automaton=dfa4, name="q2", is_start=False, is_final=False)  # Read '10'
    q3 = State.objects.create(automaton=dfa4, name="q3", is_start=False, is_final=True)   # Read '101' - ACCEPT
    
    # Redundant states that are equivalent to q0
    q4 = State.objects.create(automaton=dfa4, name="q4", is_start=False, is_final=False)  # Equivalent to q0
    q5 = State.objects.create(automaton=dfa4, name="q5", is_start=False, is_final=False)  # Equivalent to q0
    
    # Redundant states that are equivalent to q1
    q6 = State.objects.create(automaton=dfa4, name="q6", is_start=False, is_final=False)  # Equivalent to q1
    q7 = State.objects.create(automaton=dfa4, name="q7", is_start=False, is_final=False)  # Equivalent to q1
    
    # Redundant states that are equivalent to q2
    q8 = State.objects.create(automaton=dfa4, name="q8", is_start=False, is_final=False)  # Equivalent to q2
    q9 = State.objects.create(automaton=dfa4, name="q9", is_start=False, is_final=False)  # Equivalent to q2
    
    # Redundant states that are equivalent to q3 (accepting states)
    q10 = State.objects.create(automaton=dfa4, name="q10", is_start=False, is_final=True)  # Equivalent to q3
    q11 = State.objects.create(automaton=dfa4, name="q11", is_start=False, is_final=True)  # Equivalent to q3
    
    # Transitions from q0 (start state)
    Transition.objects.create(automaton=dfa4, from_state=q0, to_state=q4, symbol="0")   # Stay in q0-equivalent
    Transition.objects.create(automaton=dfa4, from_state=q0, to_state=q1, symbol="1")   # Go to q1
    
    # Transitions from q1 (read '1')
    Transition.objects.create(automaton=dfa4, from_state=q1, to_state=q2, symbol="0")   # Go to q2 (read '10')
    Transition.objects.create(automaton=dfa4, from_state=q1, to_state=q6, symbol="1")   # Stay in q1-equivalent
    
    # Transitions from q2 (read '10')
    Transition.objects.create(automaton=dfa4, from_state=q2, to_state=q5, symbol="0")   # Back to q0-equivalent
    Transition.objects.create(automaton=dfa4, from_state=q2, to_state=q3, symbol="1")   # Accept! (read '101')
    
    # Transitions from q3 (accepting state)
    Transition.objects.create(automaton=dfa4, from_state=q3, to_state=q10, symbol="0")  # Stay accepting
    Transition.objects.create(automaton=dfa4, from_state=q3, to_state=q11, symbol="1")  # Stay accepting
    
    # Transitions from q4 (equivalent to q0)
    Transition.objects.create(automaton=dfa4, from_state=q4, to_state=q0, symbol="0")   # Back to q0
    Transition.objects.create(automaton=dfa4, from_state=q4, to_state=q7, symbol="1")   # Go to q1-equivalent
    
    # Transitions from q5 (equivalent to q0)
    Transition.objects.create(automaton=dfa4, from_state=q5, to_state=q4, symbol="0")   # Stay in q0-equivalent
    Transition.objects.create(automaton=dfa4, from_state=q5, to_state=q1, symbol="1")   # Go to q1
    
    # Transitions from q6 (equivalent to q1)
    Transition.objects.create(automaton=dfa4, from_state=q6, to_state=q8, symbol="0")   # Go to q2-equivalent
    Transition.objects.create(automaton=dfa4, from_state=q6, to_state=q1, symbol="1")   # Stay in q1-equivalent
    
    # Transitions from q7 (equivalent to q1)
    Transition.objects.create(automaton=dfa4, from_state=q7, to_state=q9, symbol="0")   # Go to q2-equivalent
    Transition.objects.create(automaton=dfa4, from_state=q7, to_state=q6, symbol="1")   # Stay in q1-equivalent
    
    # Transitions from q8 (equivalent to q2)
    Transition.objects.create(automaton=dfa4, from_state=q8, to_state=q0, symbol="0")   # Back to q0
    Transition.objects.create(automaton=dfa4, from_state=q8, to_state=q10, symbol="1")  # Go to accepting
    
    # Transitions from q9 (equivalent to q2)
    Transition.objects.create(automaton=dfa4, from_state=q9, to_state=q5, symbol="0")   # Back to q0-equivalent
    Transition.objects.create(automaton=dfa4, from_state=q9, to_state=q11, symbol="1")  # Go to accepting
    
    # Transitions from q10 (equivalent to q3, accepting)
    Transition.objects.create(automaton=dfa4, from_state=q10, to_state=q3, symbol="0")  # Stay accepting
    Transition.objects.create(automaton=dfa4, from_state=q10, to_state=q11, symbol="1") # Stay accepting
    
    # Transitions from q11 (equivalent to q3, accepting)
    Transition.objects.create(automaton=dfa4, from_state=q11, to_state=q10, symbol="0") # Stay accepting
    Transition.objects.create(automaton=dfa4, from_state=q11, to_state=q3, symbol="1")  # Stay accepting
    
    dfa4.update_json_representation()

    print('Created 4 DFA examples (including 1 large DFA with 12 states)')

def create_nfa_examples(user):
    """Create example NFAs"""
    
    # Example 1: NFA that accepts strings containing "ab"
    nfa1 = Automaton.objects.create(
        name="Contains substring 'ab'",
        alphabet="a,b",
        owner=user,
        has_epsilon=False
    )
    
    # States
    q0 = State.objects.create(automaton=nfa1, name="q0", is_start=True, is_final=False)
    q1 = State.objects.create(automaton=nfa1, name="q1", is_start=False, is_final=False)
    q2 = State.objects.create(automaton=nfa1, name="q2", is_start=False, is_final=True)
    
    # Transitions
    Transition.objects.create(automaton=nfa1, from_state=q0, to_state=q0, symbol="a")
    Transition.objects.create(automaton=nfa1, from_state=q0, to_state=q0, symbol="b")
    Transition.objects.create(automaton=nfa1, from_state=q0, to_state=q1, symbol="a")
    Transition.objects.create(automaton=nfa1, from_state=q1, to_state=q2, symbol="b")
    Transition.objects.create(automaton=nfa1, from_state=q2, to_state=q2, symbol="a")
    Transition.objects.create(automaton=nfa1, from_state=q2, to_state=q2, symbol="b")
    
    nfa1.update_json_representation()

    # Example 2: NFA that accepts strings ending with "a" or "bb"
    nfa2 = Automaton.objects.create(
        name="Ends with 'a' or 'bb'",
        alphabet="a,b",
        owner=user,
        has_epsilon=False
    )
    
    # States
    q0 = State.objects.create(automaton=nfa2, name="q0", is_start=True, is_final=False)
    q1 = State.objects.create(automaton=nfa2, name="q1", is_start=False, is_final=True)  # ends with 'a'
    q2 = State.objects.create(automaton=nfa2, name="q2", is_start=False, is_final=False)  # first 'b'
    q3 = State.objects.create(automaton=nfa2, name="q3", is_start=False, is_final=True)   # ends with 'bb'
    
    # Transitions
    Transition.objects.create(automaton=nfa2, from_state=q0, to_state=q0, symbol="a")
    Transition.objects.create(automaton=nfa2, from_state=q0, to_state=q0, symbol="b")
    Transition.objects.create(automaton=nfa2, from_state=q0, to_state=q1, symbol="a")  # path to end with 'a'
    Transition.objects.create(automaton=nfa2, from_state=q0, to_state=q2, symbol="b")  # path to end with 'bb'
    Transition.objects.create(automaton=nfa2, from_state=q2, to_state=q3, symbol="b")
    
    nfa2.update_json_representation()

    # Example 3: NFA with epsilon transitions that accepts strings with at least two 'a's
    nfa3 = Automaton.objects.create(
        name="At least two 'a's (with ε-transitions)",
        alphabet="a,b",
        owner=user,
        has_epsilon=True
    )
    
    # States
    q0 = State.objects.create(automaton=nfa3, name="q0", is_start=True, is_final=False)
    q1 = State.objects.create(automaton=nfa3, name="q1", is_start=False, is_final=False)
    q2 = State.objects.create(automaton=nfa3, name="q2", is_start=False, is_final=True)
    
    # Transitions
    Transition.objects.create(automaton=nfa3, from_state=q0, to_state=q0, symbol="b")
    Transition.objects.create(automaton=nfa3, from_state=q0, to_state=q1, symbol="a")
    Transition.objects.create(automaton=nfa3, from_state=q1, to_state=q1, symbol="b")
    Transition.objects.create(automaton=nfa3, from_state=q1, to_state=q2, symbol="a")
    Transition.objects.create(automaton=nfa3, from_state=q2, to_state=q2, symbol="a")
    Transition.objects.create(automaton=nfa3, from_state=q2, to_state=q2, symbol="b")
    # Add epsilon transition
    Transition.objects.create(automaton=nfa3, from_state=q1, to_state=q2, symbol="ε")
    
    nfa3.update_json_representation()

    print('Created 3 NFA examples')

if __name__ == '__main__':
    populate_examples()
