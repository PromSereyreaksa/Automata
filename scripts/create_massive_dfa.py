#!/usr/bin/env python
"""
Creates a massive DFA with 20 states that can be minimized dramatically.
This DFA recognizes strings that have an even number of 'a's AND end with 'b'.
"""

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


def create_massive_dfa():
    """Create a massive DFA with 20 states that minimizes to 4 states."""
    
    # Create a system user for examples if it doesn't exist
    system_user, created = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@example.com',
            'first_name': 'System',
            'last_name': 'Examples'
        }
    )
    
    # Create the massive DFA
    # Language: strings with even number of 'a's AND ending with 'b'
    massive_dfa = Automaton.objects.create(
        name="MASSIVE DFA - Even 'a's AND ends with 'b' (20 states → 4 states)",
        alphabet="a,b",
        owner=system_user
    )
    
    # The minimal DFA would have 4 states:
    # State 1: Even 'a's, doesn't end with 'b' (start state)
    # State 2: Odd 'a's, doesn't end with 'b' 
    # State 3: Even 'a's, ends with 'b' (final state)
    # State 4: Odd 'a's, ends with 'b'
    
    # But we'll create 20 states with lots of redundancy
    states = []
    
    # Group 1: Even 'a's, doesn't end with 'b' (equivalent to minimal state 1)
    states.extend([
        State.objects.create(automaton=massive_dfa, name="q0", is_start=True, is_final=False),  # Start
        State.objects.create(automaton=massive_dfa, name="q1", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q2", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q3", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q4", is_start=False, is_final=False),
    ])
    
    # Group 2: Odd 'a's, doesn't end with 'b' (equivalent to minimal state 2)
    states.extend([
        State.objects.create(automaton=massive_dfa, name="q5", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q6", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q7", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q8", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q9", is_start=False, is_final=False),
    ])
    
    # Group 3: Even 'a's, ends with 'b' (equivalent to minimal state 3 - FINAL)
    states.extend([
        State.objects.create(automaton=massive_dfa, name="q10", is_start=False, is_final=True),
        State.objects.create(automaton=massive_dfa, name="q11", is_start=False, is_final=True),
        State.objects.create(automaton=massive_dfa, name="q12", is_start=False, is_final=True),
        State.objects.create(automaton=massive_dfa, name="q13", is_start=False, is_final=True),
        State.objects.create(automaton=massive_dfa, name="q14", is_start=False, is_final=True),
    ])
    
    # Group 4: Odd 'a's, ends with 'b' (equivalent to minimal state 4)
    states.extend([
        State.objects.create(automaton=massive_dfa, name="q15", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q16", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q17", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q18", is_start=False, is_final=False),
        State.objects.create(automaton=massive_dfa, name="q19", is_start=False, is_final=False),
    ])
    
    # Create transitions
    # The pattern is:
    # - 'a' transitions flip between even/odd parity groups
    # - 'b' transitions go to "ends with b" states
    
    # Transitions from Group 1 (even 'a's, doesn't end with 'b')
    for i in range(5):
        from_state = states[i]
        to_state_a = states[5 + (i + 1) % 5]  # Go to odd group (cycling within group)
        to_state_b = states[10 + (i + 2) % 5]  # Go to even+b group
        
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_a, symbol="a")
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_b, symbol="b")
    
    # Transitions from Group 2 (odd 'a's, doesn't end with 'b')
    for i in range(5):
        from_state = states[5 + i]
        to_state_a = states[(i + 3) % 5]  # Go to even group (cycling within group)
        to_state_b = states[15 + (i + 1) % 5]  # Go to odd+b group
        
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_a, symbol="a")
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_b, symbol="b")
    
    # Transitions from Group 3 (even 'a's, ends with 'b') - FINAL STATES
    for i in range(5):
        from_state = states[10 + i]
        to_state_a = states[15 + (i + 2) % 5]  # Go to odd+b group
        to_state_b = states[10 + (i + 3) % 5]  # Stay in even+b group
        
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_a, symbol="a")
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_b, symbol="b")
    
    # Transitions from Group 4 (odd 'a's, ends with 'b')
    for i in range(5):
        from_state = states[15 + i]
        to_state_a = states[10 + (i + 1) % 5]  # Go to even+b group
        to_state_b = states[15 + (i + 4) % 5]  # Stay in odd+b group
        
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_a, symbol="a")
        Transition.objects.create(automaton=massive_dfa, from_state=from_state, to_state=to_state_b, symbol="b")
    
    massive_dfa.update_json_representation()
    
    print(f"Created MASSIVE DFA with {massive_dfa.states.count()} states")
    print(f"Final states: {massive_dfa.states.filter(is_final=True).count()}")
    print(f"Transitions: {massive_dfa.transitions.count()}")
    
    return massive_dfa


def test_massive_dfa():
    """Test the massive DFA."""
    massive_dfa = create_massive_dfa()
    
    # Test some strings
    test_strings = [
        "",           # Even 'a's (0), doesn't end with 'b' → REJECT
        "b",          # Even 'a's (0), ends with 'b' → ACCEPT
        "a",          # Odd 'a's (1), doesn't end with 'b' → REJECT  
        "ab",         # Odd 'a's (1), ends with 'b' → REJECT
        "aa",         # Even 'a's (2), doesn't end with 'b' → REJECT
        "aab",        # Even 'a's (2), ends with 'b' → ACCEPT
        "aba",        # Odd 'a's (1), doesn't end with 'b' → REJECT
        "abab",       # Even 'a's (2), ends with 'b' → ACCEPT
        "aaaa",       # Even 'a's (4), doesn't end with 'b' → REJECT
        "aaaab",      # Even 'a's (4), ends with 'b' → ACCEPT
        "baaab",      # Odd 'a's (3), ends with 'b' → REJECT
        "babaab",     # Even 'a's (4), ends with 'b' → ACCEPT
    ]
    
    print("\nTesting strings on massive DFA:")
    for test_string in test_strings:
        result, message, path = massive_dfa.simulate(test_string)
        status = "ACCEPT" if result else "REJECT"
        a_count = test_string.count('a')
        ends_with_b = test_string.endswith('b')
        expected = (a_count % 2 == 0) and ends_with_b
        expected_status = "ACCEPT" if expected else "REJECT"
        correct = "✓" if (result == expected) else "✗"
        print(f"  '{test_string}' → {status} (expected: {expected_status}) {correct}")
    
    # Test minimization
    print(f"\nMinimizing massive DFA...")
    minimized = massive_dfa.minimize()
    
    reduction = massive_dfa.states.count() - minimized.states.count()
    percentage = (reduction / massive_dfa.states.count()) * 100
    
    print(f"Original states:     {massive_dfa.states.count()}")
    print(f"Minimized states:    {minimized.states.count()}")
    print(f"States reduced:      {reduction}")
    print(f"Reduction:           {percentage:.1f}%")
    
    return massive_dfa, minimized


if __name__ == '__main__':
    test_massive_dfa()