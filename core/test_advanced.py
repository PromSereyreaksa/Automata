"""
Advanced test cases for automata functionality.
These tests cover edge cases, performance, and complex scenarios.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import time

from .models import DFA, NFA, DFAState, NFAState, DFATransition, NFATransition


class EdgeCaseTest(TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_empty_alphabet_dfa(self):
        """Test DFA with empty alphabet."""
        dfa = DFA.objects.create(
            name="Empty Alphabet DFA",
            alphabet="",
            owner=self.user
        )
        
        q0 = dfa.states.create(name="q0", is_start=True, is_final=True)
        
        # Empty string should be accepted (no symbols to process)
        accepted, message, path = dfa.simulate("")
        self.assertTrue(accepted)
        
        # Any non-empty string should be rejected
        accepted, message, path = dfa.simulate("a")
        self.assertFalse(accepted)
        
    def test_single_state_dfa(self):
        """Test DFA with only one state."""
        dfa = DFA.objects.create(
            name="Single State DFA",
            alphabet="a",
            owner=self.user
        )
        
        q0 = dfa.states.create(name="q0", is_start=True, is_final=True)
        dfa.transitions.create(from_state=q0, to_state=q0, symbol="a")
        
        # Should accept any string of a's
        test_cases = ["", "a", "aa", "aaa"]
        for test_string in test_cases:
            accepted, message, path = dfa.simulate(test_string)
            self.assertTrue(accepted, f"String '{test_string}' should be accepted")
            
    def test_unreachable_states(self):
        """Test DFA with unreachable states."""
        dfa = DFA.objects.create(
            name="Unreachable States DFA",
            alphabet="a,b",
            owner=self.user
        )
        
        q0 = dfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = dfa.states.create(name="q1", is_final=True)
        q2 = dfa.states.create(name="q2", is_final=True)  # Unreachable
        
        # Only transitions from q0 to q1
        dfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa.transitions.create(from_state=q0, to_state=q0, symbol="b")
        dfa.transitions.create(from_state=q1, to_state=q1, symbol="a")
        dfa.transitions.create(from_state=q1, to_state=q1, symbol="b")
        
        # No transitions from q2 (unreachable anyway)
        dfa.transitions.create(from_state=q2, to_state=q2, symbol="a")
        dfa.transitions.create(from_state=q2, to_state=q2, symbol="b")
        
        # DFA should still be valid
        is_valid, message = dfa.is_valid()
        self.assertTrue(is_valid)
        
    def test_complex_epsilon_nfa(self):
        """Test NFA with complex epsilon transitions."""
        nfa = NFA.objects.create(
            name="Complex Epsilon NFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # Create a chain of epsilon transitions
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_final=False)
        q2 = nfa.states.create(name="q2", is_final=False)
        q3 = nfa.states.create(name="q3", is_final=True)
        
        # Epsilon chain: q0 -ε-> q1 -ε-> q2 -ε-> q3
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="ε")
        nfa.transitions.create(from_state=q1, to_state=q2, symbol="ε")
        nfa.transitions.create(from_state=q2, to_state=q3, symbol="ε")
        
        # Also add some regular transitions
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        nfa.transitions.create(from_state=q2, to_state=q0, symbol="b")
        
        # Empty string should be accepted (epsilon closure reaches final state)
        accepted, message, path = nfa.simulate("")
        self.assertTrue(accepted)
        
    def test_multiple_symbol_transitions(self):
        """Test transitions with multiple symbols."""
        nfa = NFA.objects.create(
            name="Multiple Symbol NFA",
            alphabet="a,b,c",
            owner=self.user
        )
        
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_final=True)
        
        # Transition that accepts both 'a' and 'b'
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="a,b")
        nfa.transitions.create(from_state=q1, to_state=q1, symbol="a,b,c")
        
        # Test that both symbols work
        accepted, message, path = nfa.simulate("a")
        self.assertTrue(accepted)
        
        accepted, message, path = nfa.simulate("b")
        self.assertTrue(accepted)
        
        accepted, message, path = nfa.simulate("c")
        self.assertFalse(accepted)
        
        accepted, message, path = nfa.simulate("abc")
        self.assertTrue(accepted)


class PerformanceTest(TestCase):
    """Test performance with larger automata."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_large_alphabet(self):
        """Test DFA with large alphabet."""
        # Create alphabet with many symbols
        alphabet_symbols = [chr(i) for i in range(ord('a'), ord('z') + 1)]
        alphabet = ','.join(alphabet_symbols)
        
        dfa = DFA.objects.create(
            name="Large Alphabet DFA",
            alphabet=alphabet,
            owner=self.user
        )
        
        q0 = dfa.states.create(name="q0", is_start=True, is_final=True)
        
        # Add transitions for all symbols
        for symbol in alphabet_symbols:
            dfa.transitions.create(from_state=q0, to_state=q0, symbol=symbol)
            
        # Test validation
        start_time = time.time()
        is_valid, message = dfa.is_valid()
        validation_time = time.time() - start_time
        
        self.assertTrue(is_valid)
        self.assertLess(validation_time, 5.0)  # Should complete within 5 seconds
        
    def test_many_states_dfa(self):
        """Test DFA with many states."""
        dfa = DFA.objects.create(
            name="Many States DFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # Create a chain of 50 states
        states = []
        for i in range(50):
            is_start = (i == 0)
            is_final = (i == 49)
            state = dfa.states.create(
                name=f"q{i}",
                is_start=is_start,
                is_final=is_final
            )
            states.append(state)
            
        # Create transitions: each state goes to next on 'a', stays on 'b'
        for i in range(50):
            current_state = states[i]
            next_state = states[(i + 1) % 50]
            
            dfa.transitions.create(from_state=current_state, to_state=next_state, symbol="a")
            dfa.transitions.create(from_state=current_state, to_state=current_state, symbol="b")
            
        # Test simulation performance
        start_time = time.time()
        accepted, message, path = dfa.simulate("a" * 49)  # Should reach final state
        simulation_time = time.time() - start_time
        
        self.assertTrue(accepted)
        self.assertLess(simulation_time, 2.0)  # Should complete within 2 seconds
        
    def test_nfa_to_dfa_exponential_growth(self):
        """Test NFA to DFA conversion that causes exponential state growth."""
        nfa = NFA.objects.create(
            name="Exponential Growth NFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # Create an NFA that requires exponential states in DFA
        # Pattern: accepts strings where the n-th symbol from the end is 'a'
        n = 4  # Keep small to avoid excessive test time
        
        states = []
        for i in range(n + 1):
            is_start = (i == 0)
            is_final = (i == n)
            state = nfa.states.create(
                name=f"q{i}",
                is_start=is_start,
                is_final=is_final
            )
            states.append(state)
            
        # From start state, can stay or move to q1 on 'a'
        nfa.transitions.create(from_state=states[0], to_state=states[0], symbol="a,b")
        nfa.transitions.create(from_state=states[0], to_state=states[1], symbol="a")
        
        # Linear chain for remaining states
        for i in range(1, n):
            nfa.transitions.create(from_state=states[i], to_state=states[i + 1], symbol="a,b")
            
        # Test conversion
        start_time = time.time()
        dfa = nfa.to_dfa()
        conversion_time = time.time() - start_time
        
        self.assertLess(conversion_time, 10.0)  # Should complete within 10 seconds
        
        # Verify the converted DFA works correctly
        test_cases = [
            ("aaaa", True),   # 4th from end is 'a'
            ("baaa", True),   # 4th from end is 'a'
            ("bbba", False),  # 4th from end is 'b'
            ("aab", False),   # Less than 4 characters
        ]
        
        for test_string, expected in test_cases:
            nfa_result, _, _ = nfa.simulate(test_string)
            dfa_result, _, _ = dfa.simulate(test_string)
            self.assertEqual(nfa_result, dfa_result)
            self.assertEqual(nfa_result, expected)


class ComplexScenarioTest(TestCase):
    """Test complex real-world scenarios."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_email_validation_dfa(self):
        """Test DFA that validates simple email format."""
        dfa = DFA.objects.create(
            name="Email Validator",
            alphabet="a,@,.",
            owner=self.user
        )
        
        # Simplified email: letter+ @ letter+ . letter+
        q0 = dfa.states.create(name="start", is_start=True, is_final=False)
        q1 = dfa.states.create(name="username", is_final=False)
        q2 = dfa.states.create(name="at_symbol", is_final=False)
        q3 = dfa.states.create(name="domain", is_final=False)
        q4 = dfa.states.create(name="dot", is_final=False)
        q5 = dfa.states.create(name="tld", is_final=True)
        
        # Transitions
        dfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa.transitions.create(from_state=q1, to_state=q1, symbol="a")
        dfa.transitions.create(from_state=q1, to_state=q2, symbol="@")
        dfa.transitions.create(from_state=q2, to_state=q3, symbol="a")
        dfa.transitions.create(from_state=q3, to_state=q3, symbol="a")
        dfa.transitions.create(from_state=q3, to_state=q4, symbol=".")
        dfa.transitions.create(from_state=q4, to_state=q5, symbol="a")
        dfa.transitions.create(from_state=q5, to_state=q5, symbol="a")
        
        # Test valid and invalid emails
        valid_emails = ["a@a.a", "aa@aa.aa", "aaa@a.aaa"]
        invalid_emails = ["", "a", "a@", "a@a", "a@a.", "@a.a", "a.a@a"]
        
        for email in valid_emails:
            accepted, _, _ = dfa.simulate(email)
            self.assertTrue(accepted, f"Email '{email}' should be valid")
            
        for email in invalid_emails:
            accepted, _, _ = dfa.simulate(email)
            self.assertFalse(accepted, f"Email '{email}' should be invalid")
            
    def test_balanced_parentheses_pushdown(self):
        """Test NFA that simulates balanced parentheses (simplified)."""
        # Note: This is a simplified version since true balanced parentheses
        # requires a pushdown automaton, but we can test simple cases
        nfa = NFA.objects.create(
            name="Balanced Parentheses",
            alphabet="(,)",
            owner=self.user
        )
        
        # States represent nesting level (simplified to depth 2)
        q0 = nfa.states.create(name="level0", is_start=True, is_final=True)
        q1 = nfa.states.create(name="level1", is_final=False)
        q2 = nfa.states.create(name="level2", is_final=False)
        
        # Transitions
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="(")
        nfa.transitions.create(from_state=q1, to_state=q0, symbol=")")
        nfa.transitions.create(from_state=q1, to_state=q2, symbol="(")
        nfa.transitions.create(from_state=q2, to_state=q1, symbol=")")
        
        # Test cases (limited to depth 2)
        valid_cases = ["", "()", "(())", "()()", "()()"]
        invalid_cases = ["(", ")", "((", "))", "())", "(()"]
        
        for case in valid_cases:
            accepted, _, _ = nfa.simulate(case)
            self.assertTrue(accepted, f"'{case}' should be balanced")
            
        for case in invalid_cases:
            accepted, _, _ = nfa.simulate(case)
            self.assertFalse(accepted, f"'{case}' should be unbalanced")
            
    def test_regular_expression_simulation(self):
        """Test NFA that simulates regular expression (a|b)*abb."""
        nfa = NFA.objects.create(
            name="Regex (a|b)*abb",
            alphabet="a,b",
            owner=self.user
        )
        
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_final=False)
        q2 = nfa.states.create(name="q2", is_final=False)
        q3 = nfa.states.create(name="q3", is_final=True)
        
        # (a|b)* - stay in q0
        nfa.transitions.create(from_state=q0, to_state=q0, symbol="a,b")
        
        # Start matching "abb"
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        nfa.transitions.create(from_state=q1, to_state=q2, symbol="b")
        nfa.transitions.create(from_state=q2, to_state=q3, symbol="b")
        
        # Handle mismatches (go back to appropriate state)
        nfa.transitions.create(from_state=q1, to_state=q1, symbol="a")  # aa... -> a...
        nfa.transitions.create(from_state=q1, to_state=q0, symbol="b")  # ab -> start over
        nfa.transitions.create(from_state=q2, to_state=q1, symbol="a")  # aba -> a
        nfa.transitions.create(from_state=q2, to_state=q0, symbol="b")  # abb -> match, but also can continue
        nfa.transitions.create(from_state=q3, to_state=q0, symbol="a,b")  # After match, continue
        
        # Test cases
        valid_cases = ["abb", "aabb", "babb", "ababb", "abaabb", "abbabb"]
        invalid_cases = ["", "a", "ab", "ba", "aab", "abba"]
        
        for case in valid_cases:
            accepted, _, _ = nfa.simulate(case)
            self.assertTrue(accepted, f"'{case}' should match (a|b)*abb")
            
        for case in invalid_cases:
            accepted, _, _ = nfa.simulate(case)
            self.assertFalse(accepted, f"'{case}' should not match (a|b)*abb")


if __name__ == '__main__':
    import unittest
    unittest.main()
