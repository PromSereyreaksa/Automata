#!/usr/bin/env python
"""
Test script for the improved DFA minimization algorithm using Myhill-Nerode Theorem.
This script creates a test DFA that can be minimized to verify the algorithm works correctly.
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


def create_test_dfa():
    """
    Create a test DFA that can be minimized.
    Based on the example from the Myhill-Nerode theorem description.
    """
    # Create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Create DFA with redundant states
    dfa = Automaton.objects.create(
        name="Test DFA for Minimization",
        alphabet="0,1",
        owner=user
    )
    
    # Create states (some will be equivalent)
    q0 = State.objects.create(automaton=dfa, name="q0", is_start=True, is_final=False)
    q1 = State.objects.create(automaton=dfa, name="q1", is_start=False, is_final=True)
    q2 = State.objects.create(automaton=dfa, name="q2", is_start=False, is_final=True)
    q3 = State.objects.create(automaton=dfa, name="q3", is_start=False, is_final=False)
    q4 = State.objects.create(automaton=dfa, name="q4", is_start=False, is_final=True)
    q5 = State.objects.create(automaton=dfa, name="q5", is_start=False, is_final=False)
    
    # Create transitions
    Transition.objects.create(automaton=dfa, from_state=q0, to_state=q3, symbol="0")
    Transition.objects.create(automaton=dfa, from_state=q0, to_state=q1, symbol="1")
    
    Transition.objects.create(automaton=dfa, from_state=q1, to_state=q2, symbol="0")
    Transition.objects.create(automaton=dfa, from_state=q1, to_state=q5, symbol="1")
    
    Transition.objects.create(automaton=dfa, from_state=q2, to_state=q2, symbol="0")
    Transition.objects.create(automaton=dfa, from_state=q2, to_state=q5, symbol="1")
    
    Transition.objects.create(automaton=dfa, from_state=q3, to_state=q0, symbol="0")
    Transition.objects.create(automaton=dfa, from_state=q3, to_state=q4, symbol="1")
    
    Transition.objects.create(automaton=dfa, from_state=q4, to_state=q2, symbol="0")
    Transition.objects.create(automaton=dfa, from_state=q4, to_state=q5, symbol="1")
    
    Transition.objects.create(automaton=dfa, from_state=q5, to_state=q5, symbol="0")
    Transition.objects.create(automaton=dfa, from_state=q5, to_state=q5, symbol="1")
    
    dfa.update_json_representation()
    return dfa


def test_minimization():
    """Test the DFA minimization algorithm."""
    print("Creating test DFA...")
    original_dfa = create_test_dfa()
    
    print(f"Original DFA has {original_dfa.states.count()} states")
    print("Original states:", [state.name for state in original_dfa.states.all()])
    
    # Test if it's a valid DFA
    is_valid, message = original_dfa.is_dfa()
    print(f"DFA validity: {is_valid}, Message: {message}")
    
    if not is_valid:
        print("ERROR: Test DFA is not valid!")
        return
    
    # Test minimization
    print("\nRunning minimization algorithm...")
    try:
        minimized_dfa = original_dfa.minimize()
        
        print(f"Minimized DFA has {minimized_dfa.states.count()} states")
        print("Minimized states:", [state.name for state in minimized_dfa.states.all()])
        
        # Test if minimized DFA is valid
        is_min_valid, min_message = minimized_dfa.is_dfa()
        print(f"Minimized DFA validity: {is_min_valid}, Message: {min_message}")
        
        # Test some strings on both DFAs to ensure they're equivalent
        test_strings = ["", "0", "1", "01", "10", "011", "101", "0110", "1010"]
        
        print("\nTesting string equivalence:")
        all_match = True
        for test_string in test_strings:
            orig_result = original_dfa.simulate(test_string)[0]
            min_result = minimized_dfa.simulate(test_string)[0]
            match = orig_result == min_result
            print(f"'{test_string}': Original={orig_result}, Minimized={min_result}, Match={match}")
            if not match:
                all_match = False
        
        if all_match:
            print("\n✓ SUCCESS: All test strings produce the same results!")
            print(f"✓ Minimization reduced states from {original_dfa.states.count()} to {minimized_dfa.states.count()}")
        else:
            print("\n✗ FAILURE: Minimized DFA produces different results!")
            
    except Exception as e:
        print(f"ERROR during minimization: {e}")
        import traceback
        traceback.print_exc()


def test_nfa_to_dfa():
    """Test NFA to DFA conversion."""
    print("\n" + "="*50)
    print("Testing NFA to DFA conversion...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Create test NFA
    nfa = Automaton.objects.create(
        name="Test NFA for Conversion",
        alphabet="a,b",
        owner=user,
        has_epsilon=True
    )
    
    # Create states
    q0 = State.objects.create(automaton=nfa, name="q0", is_start=True, is_final=False)
    q1 = State.objects.create(automaton=nfa, name="q1", is_start=False, is_final=False)
    q2 = State.objects.create(automaton=nfa, name="q2", is_start=False, is_final=True)
    
    # Create transitions with nondeterminism
    Transition.objects.create(automaton=nfa, from_state=q0, to_state=q0, symbol="a")
    Transition.objects.create(automaton=nfa, from_state=q0, to_state=q1, symbol="a")  # Nondeterministic
    Transition.objects.create(automaton=nfa, from_state=q1, to_state=q2, symbol="b")
    Transition.objects.create(automaton=nfa, from_state=q1, to_state=q2, symbol="ε")  # Epsilon transition
    
    nfa.update_json_representation()
    
    print(f"Original NFA has {nfa.states.count()} states")
    print("NFA type:", nfa.get_type())
    
    # Convert to DFA
    try:
        dfa = nfa.to_dfa()
        print(f"Converted DFA has {dfa.states.count()} states")
        print("DFA type:", dfa.get_type())
        
        # Test validity
        is_valid, message = dfa.is_dfa()
        print(f"DFA validity: {is_valid}, Message: {message}")
        
        # Test some strings
        test_strings = ["", "a", "b", "aa", "ab", "aab", "aaab"]
        print("\nTesting string equivalence:")
        all_match = True
        for test_string in test_strings:
            nfa_result = nfa.simulate(test_string)[0]
            dfa_result = dfa.simulate(test_string)[0]
            match = nfa_result == dfa_result
            print(f"'{test_string}': NFA={nfa_result}, DFA={dfa_result}, Match={match}")
            if not match:
                all_match = False
        
        if all_match:
            print("\n✓ SUCCESS: NFA to DFA conversion works correctly!")
        else:
            print("\n✗ FAILURE: NFA and DFA produce different results!")
            
    except Exception as e:
        print(f"ERROR during conversion: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_minimization()
    test_nfa_to_dfa()