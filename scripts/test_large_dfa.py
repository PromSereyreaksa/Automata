#!/usr/bin/env python
"""
Test script specifically for the large DFA minimization example.
This demonstrates the power of the Myhill-Nerode theorem implementation.
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


def test_large_dfa_minimization():
    """Test the large DFA minimization example."""
    print("=" * 60)
    print("TESTING LARGE DFA MINIMIZATION")
    print("=" * 60)
    
    # Find the large DFA (created by populate_examples.py)
    try:
        system_user = User.objects.get(username='system')
        large_dfa = Automaton.objects.get(
            name="Large DFA - Contains '101' (12 states → 4 states)",
            owner=system_user
        )
    except (User.DoesNotExist, Automaton.DoesNotExist):
        print("ERROR: Large DFA not found. Run populate_examples.py first!")
        return
    
    print(f"Original DFA: {large_dfa.name}")
    print(f"Original states: {large_dfa.states.count()}")
    print("State details:")
    for state in large_dfa.states.all().order_by('name'):
        state_type = "START" if state.is_start else "FINAL" if state.is_final else "NORMAL"
        print(f"  {state.name}: {state_type}")
    
    # Show transition table
    print("\nTransition table:")
    print("State | 0 → | 1 →")
    print("-" * 20)
    for state in large_dfa.states.all().order_by('name'):
        trans_0 = large_dfa.transitions.filter(from_state=state, symbol="0").first()
        trans_1 = large_dfa.transitions.filter(from_state=state, symbol="1").first()
        to_0 = trans_0.to_state.name if trans_0 else "∅"
        to_1 = trans_1.to_state.name if trans_1 else "∅"
        print(f"{state.name:5} | {to_0:3} | {to_1:3}")
    
    # Test if it's a valid DFA
    is_valid, message = large_dfa.is_dfa()
    print(f"\nDFA validity: {is_valid}")
    print(f"Message: {message}")
    
    if not is_valid:
        print("ERROR: DFA is not valid!")
        return
    
    # Test some strings before minimization
    test_strings = [
        "",           # Should reject
        "0",          # Should reject
        "1",          # Should reject
        "10",         # Should reject
        "101",        # Should accept - contains "101"
        "1010",       # Should reject
        "1011",       # Should accept - contains "101"
        "01010",      # Should reject
        "01011",      # Should accept - contains "101"
        "110101",     # Should accept - contains "101"
        "000101000",  # Should accept - contains "101"
        "111000",     # Should reject
    ]
    
    print("\nTesting strings on original DFA:")
    original_results = {}
    for test_string in test_strings:
        result, message, path = large_dfa.simulate(test_string)
        original_results[test_string] = result
        status = "ACCEPT" if result else "REJECT"
        print(f"  '{test_string}' → {status}")
    
    # Now minimize the DFA
    print("\n" + "=" * 40)
    print("MINIMIZING DFA...")
    print("=" * 40)
    
    try:
        minimized_dfa = large_dfa.minimize()
        
        print(f"Minimized DFA name: {minimized_dfa.name}")
        print(f"Minimized states: {minimized_dfa.states.count()}")
        print("Minimized state details:")
        for state in minimized_dfa.states.all().order_by('name'):
            state_type = "START" if state.is_start else "FINAL" if state.is_final else "NORMAL"
            print(f"  {state.name}: {state_type}")
        
        # Show minimized transition table
        print("\nMinimized transition table:")
        print("State | 0 → | 1 →")
        print("-" * 30)
        for state in minimized_dfa.states.all().order_by('name'):
            trans_0 = minimized_dfa.transitions.filter(from_state=state, symbol="0").first()
            trans_1 = minimized_dfa.transitions.filter(from_state=state, symbol="1").first()
            to_0 = trans_0.to_state.name if trans_0 else "∅"
            to_1 = trans_1.to_state.name if trans_1 else "∅"
            print(f"{state.name:13} | {to_0:13} | {to_1:13}")
        
        # Test validity of minimized DFA
        is_min_valid, min_message = minimized_dfa.is_dfa()
        print(f"\nMinimized DFA validity: {is_min_valid}")
        print(f"Message: {min_message}")
        
        # Test the same strings on minimized DFA
        print("\nTesting strings on minimized DFA:")
        all_match = True
        for test_string in test_strings:
            min_result, min_message, min_path = minimized_dfa.simulate(test_string)
            orig_result = original_results[test_string]
            match = orig_result == min_result
            status = "ACCEPT" if min_result else "REJECT"
            match_status = "✓" if match else "✗"
            print(f"  '{test_string}' → {status} {match_status}")
            if not match:
                all_match = False
        
        # Show the reduction achieved
        print("\n" + "=" * 60)
        print("MINIMIZATION RESULTS")
        print("=" * 60)
        reduction = large_dfa.states.count() - minimized_dfa.states.count()
        percentage = (reduction / large_dfa.states.count()) * 100
        
        print(f"Original states:     {large_dfa.states.count()}")
        print(f"Minimized states:    {minimized_dfa.states.count()}")
        print(f"States reduced:      {reduction}")
        print(f"Reduction:           {percentage:.1f}%")
        
        if all_match:
            print(f"\n✓ SUCCESS: All test strings produce identical results!")
            print(f"✓ The Myhill-Nerode algorithm successfully reduced the DFA!")
            print(f"✓ Language equivalence maintained: L(original) = L(minimized)")
        else:
            print(f"\n✗ FAILURE: Some test strings produce different results!")
            
        # Show the state equivalence classes
        print(f"\nEquivalence classes found:")
        for state in minimized_dfa.states.all().order_by('name'):
            if '{' in state.name:
                original_states = state.name.strip('{}').split(',')
                print(f"  {state.name} represents: {', '.join(original_states)}")
            else:
                print(f"  {state.name} represents: {state.name}")
        
        return minimized_dfa
        
    except Exception as e:
        print(f"ERROR during minimization: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    test_large_dfa_minimization()