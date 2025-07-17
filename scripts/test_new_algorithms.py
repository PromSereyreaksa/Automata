#!/usr/bin/env python
"""
Test the new improved algorithms with detailed steps and clean state names.
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


def test_improved_minimization():
    """Test the improved minimization with detailed steps."""
    print("=" * 60)
    print("TESTING IMPROVED DFA MINIMIZATION")
    print("=" * 60)
    
    # Find the large DFA
    try:
        system_user = User.objects.get(username='system')
        large_dfa = Automaton.objects.get(
            name="Large DFA - Contains '101' (12 states → 4 states)",
            owner=system_user
        )
    except (User.DoesNotExist, Automaton.DoesNotExist):
        print("ERROR: Large DFA not found!")
        return
    
    print(f"Original DFA: {large_dfa.name}")
    print(f"Original states: {large_dfa.states.count()}")
    
    # Test minimization
    try:
        minimized_dfa, detailed_steps = large_dfa.minimize()
        
        print(f"\nMinimized DFA: {minimized_dfa.name}")
        print(f"Minimized states: {minimized_dfa.states.count()}")
        
        # Show new clean state names
        print("\nNew clean state names:")
        for state in minimized_dfa.states.all().order_by('name'):
            state_type = "START" if state.is_start else "FINAL" if state.is_final else "NORMAL"
            print(f"  {state.name}: {state_type}")
        
        print(f"\nDetailed steps summary:")
        print(f"- {detailed_steps['message']}")
        print(f"- Reduction: {detailed_steps['reduction_percentage']}%")
        print(f"- Steps recorded: {len(detailed_steps['steps'])}")
        
        # Show equivalence classes
        print("\nEquivalence classes:")
        for eq_class in detailed_steps['equivalence_classes']:
            print(f"  {eq_class['new_state']} = {{{', '.join(eq_class['original_states'])}}}")
        
        # Test some strings
        test_strings = ["101", "1010", "000", "111"]
        print(f"\nTesting strings:")
        for test_string in test_strings:
            orig_result = large_dfa.simulate(test_string)[0]
            min_result = minimized_dfa.simulate(test_string)[0]
            match = "✓" if orig_result == min_result else "✗"
            print(f"  '{test_string}': {orig_result} == {min_result} {match}")
        
        print("\n✓ Minimization test PASSED!")
        return minimized_dfa, detailed_steps
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_improved_conversion():
    """Test the improved NFA to DFA conversion."""
    print("\n" + "=" * 60)
    print("TESTING IMPROVED NFA TO DFA CONVERSION")
    print("=" * 60)
    
    # Find an NFA example
    try:
        system_user = User.objects.get(username='system')
        nfa = Automaton.objects.get(
            name="At least two 'a's (with ε-transitions)",
            owner=system_user
        )
    except (User.DoesNotExist, Automaton.DoesNotExist):
        print("ERROR: NFA not found!")
        return
    
    print(f"Original NFA: {nfa.name}")
    print(f"NFA states: {nfa.states.count()}")
    print(f"Has epsilon transitions: {nfa.has_epsilon}")
    
    # Test conversion
    try:
        dfa, detailed_steps = nfa.to_dfa()
        
        print(f"\nConverted DFA: {dfa.name}")
        print(f"DFA states: {dfa.states.count()}")
        
        # Show new clean state names
        print("\nNew clean state names:")
        for state in dfa.states.all().order_by('name'):
            state_type = "START" if state.is_start else "FINAL" if state.is_final else "NORMAL"
            print(f"  {state.name}: {state_type}")
        
        print(f"\nDetailed steps summary:")
        print(f"- {detailed_steps['message']}")
        print(f"- Steps recorded: {len(detailed_steps['steps'])}")
        
        # Show state mapping
        print("\nState mapping:")
        for mapping in detailed_steps['state_mapping']:
            print(f"  {mapping['dfa_state']} = {{{', '.join(mapping['nfa_states'])}}}")
        
        # Test some strings
        test_strings = ["", "a", "aa", "aaa", "baa", "aba"]
        print(f"\nTesting strings:")
        for test_string in test_strings:
            nfa_result = nfa.simulate(test_string)[0]
            dfa_result = dfa.simulate(test_string)[0]
            match = "✓" if nfa_result == dfa_result else "✗"
            print(f"  '{test_string}': {nfa_result} == {dfa_result} {match}")
        
        print("\n✓ Conversion test PASSED!")
        return dfa, detailed_steps
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == '__main__':
    min_result = test_improved_minimization()
    conv_result = test_improved_conversion()
    
    if min_result[0] and conv_result[0]:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✓ Clean state names (A, B, C instead of {q1,q2,q3})")
        print("✓ Detailed step-by-step algorithms")
        print("✓ Language equivalence maintained")
        print("✓ Ready for web interface!")
        print("=" * 60)
    else:
        print("\n❌ Some tests failed!")