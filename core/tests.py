from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db import IntegrityError
import json

from .models import Automaton, State, Transition


class AutomatonModelTest(TestCase):
    """Test cases for the base Automaton functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_get_alphabet_as_set(self):
        """Test alphabet parsing."""
        dfa = DFA.objects.create(
            name="Test DFA",
            alphabet="a,b,c",
            owner=self.user
        )
        expected = {'a', 'b', 'c'}
        self.assertEqual(dfa.get_alphabet_as_set(), expected)
        
        # Test with spaces
        dfa2 = DFA.objects.create(
            name="Test DFA 2",
            alphabet="a, b , c",
            owner=self.user
        )
        self.assertEqual(dfa2.get_alphabet_as_set(), expected)
        
        # Test empty alphabet
        dfa3 = DFA.objects.create(
            name="Test DFA 3",
            alphabet="",
            owner=self.user
        )
        self.assertEqual(dfa3.get_alphabet_as_set(), set())


class TransitionModelTest(TestCase):
    """Test cases for Transition model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.dfa = DFA.objects.create(
            name="Test DFA",
            alphabet="a,b",
            owner=self.user
        )
        self.state1 = self.dfa.states.create(name="q0", is_start=True)
        self.state2 = self.dfa.states.create(name="q1", is_final=True)
        
    def test_get_symbols_as_set_single_symbol(self):
        """Test single symbol parsing."""
        transition = self.dfa.transitions.create(
            from_state=self.state1,
            to_state=self.state2,
            symbol="a"
        )
        self.assertEqual(transition.get_symbols_as_set(), {'a'})
        
    def test_get_symbols_as_set_multiple_symbols(self):
        """Test multiple symbols parsing."""
        transition = self.dfa.transitions.create(
            from_state=self.state1,
            to_state=self.state2,
            symbol="a,b"
        )
        self.assertEqual(transition.get_symbols_as_set(), {'a', 'b'})
        
    def test_get_symbols_as_set_epsilon(self):
        """Test epsilon symbol parsing."""
        transition = self.dfa.transitions.create(
            from_state=self.state1,
            to_state=self.state2,
            symbol="ε"
        )
        self.assertEqual(transition.get_symbols_as_set(), {'ε'})
        
        # Test empty string as epsilon
        transition2 = self.dfa.transitions.create(
            from_state=self.state1,
            to_state=self.state2,
            symbol=""
        )
        self.assertEqual(transition2.get_symbols_as_set(), {'ε'})
        
    def test_matches_symbol(self):
        """Test symbol matching."""
        transition = self.dfa.transitions.create(
            from_state=self.state1,
            to_state=self.state2,
            symbol="a,b"
        )
        self.assertTrue(transition.matches_symbol('a'))
        self.assertTrue(transition.matches_symbol('b'))
        self.assertFalse(transition.matches_symbol('c'))
        
    def test_transition_validation(self):
        """Test transition validation."""
        # Valid transition
        transition = DFATransition(
            automaton=self.dfa,
            from_state=self.state1,
            to_state=self.state2,
            symbol="a"
        )
        transition.clean()  # Should not raise
        
        # Invalid transition - symbol not in alphabet
        invalid_transition = DFATransition(
            automaton=self.dfa,
            from_state=self.state1,
            to_state=self.state2,
            symbol="c"
        )
        with self.assertRaises(ValidationError):
            invalid_transition.clean()


class DFAModelTest(TestCase):
    """Test cases for DFA model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def create_simple_dfa(self):
        """Create a simple DFA that accepts strings with even number of 'a's."""
        dfa = DFA.objects.create(
            name="Even A's",
            alphabet="a,b",
            owner=self.user
        )
        
        # States
        q0 = dfa.states.create(name="q0", is_start=True, is_final=True)  # even a's
        q1 = dfa.states.create(name="q1", is_final=False)  # odd a's
        
        # Transitions
        dfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa.transitions.create(from_state=q0, to_state=q0, symbol="b")
        dfa.transitions.create(from_state=q1, to_state=q0, symbol="a")
        dfa.transitions.create(from_state=q1, to_state=q1, symbol="b")
        
        return dfa
        
    def test_dfa_creation(self):
        """Test DFA creation."""
        dfa = self.create_simple_dfa()
        self.assertEqual(dfa.name, "Even A's")
        self.assertEqual(dfa.states.count(), 2)
        self.assertEqual(dfa.transitions.count(), 4)
        
    def test_dfa_is_valid(self):
        """Test DFA validation."""
        dfa = self.create_simple_dfa()
        is_valid, message = dfa.is_valid()
        self.assertTrue(is_valid)
        self.assertEqual(message, "DFA is valid.")
        
    def test_dfa_invalid_no_start_state(self):
        """Test DFA validation with no start state."""
        dfa = DFA.objects.create(
            name="Invalid DFA",
            alphabet="a,b",
            owner=self.user
        )
        q0 = dfa.states.create(name="q0", is_start=False, is_final=True)
        
        is_valid, message = dfa.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "A DFA must have exactly one start state.")
        
    def test_dfa_invalid_missing_transitions(self):
        """Test DFA validation with missing transitions."""
        dfa = DFA.objects.create(
            name="Invalid DFA",
            alphabet="a,b",
            owner=self.user
        )
        q0 = dfa.states.create(name="q0", is_start=True, is_final=True)
        # Missing transitions for 'a' and 'b'
        
        is_valid, message = dfa.is_valid()
        self.assertFalse(is_valid)
        self.assertIn("must have exactly one transition", message)
        
    def test_dfa_simulate_accept(self):
        """Test DFA simulation - accepting strings."""
        dfa = self.create_simple_dfa()
        
        # Test accepting strings (even number of a's)
        test_cases = ["", "aa", "b", "bb", "aabb", "aba", "baab"]  # Added "aba" and "baab" which have even a's
        for test_string in test_cases:
            accepted, message, path = dfa.simulate(test_string)
            self.assertTrue(accepted, f"String '{test_string}' should be accepted")
            self.assertEqual(message, "Simulation completed.")
            
    def test_dfa_simulate_reject(self):
        """Test DFA simulation - rejecting strings."""
        dfa = self.create_simple_dfa()
        
        # Test rejecting strings (odd number of a's)
        test_cases = ["a", "aaa", "bab"]  # Fixed: "aba" has 2 a's (even), "bab" has 1 a (odd)
        for test_string in test_cases:
            accepted, message, path = dfa.simulate(test_string)
            self.assertFalse(accepted, f"String '{test_string}' should be rejected")
            self.assertEqual(message, "Simulation completed.")
            
    def test_dfa_simulate_invalid_symbol(self):
        """Test DFA simulation with invalid symbol."""
        dfa = self.create_simple_dfa()
        
        accepted, message, path = dfa.simulate("ac")
        self.assertFalse(accepted)
        self.assertIn("not in the alphabet", message)
        
    def test_dfa_simulate_no_start_state(self):
        """Test DFA simulation with no start state."""
        dfa = DFA.objects.create(
            name="No Start DFA",
            alphabet="a,b",
            owner=self.user
        )
        q0 = dfa.states.create(name="q0", is_start=False, is_final=True)
        
        accepted, message, path = dfa.simulate("a")
        self.assertFalse(accepted)
        self.assertEqual(message, "No start state defined.")


class NFAModelTest(TestCase):
    """Test cases for NFA model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def create_simple_nfa(self):
        """Create a simple NFA that accepts strings ending with 'ab'."""
        nfa = NFA.objects.create(
            name="Ends with ab",
            alphabet="a,b",
            owner=self.user
        )
        
        # States
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_final=False)
        q2 = nfa.states.create(name="q2", is_final=True)
        
        # Transitions
        nfa.transitions.create(from_state=q0, to_state=q0, symbol="a,b")  # Multiple symbols
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        nfa.transitions.create(from_state=q1, to_state=q2, symbol="b")
        
        return nfa
        
    def create_epsilon_nfa(self):
        """Create an NFA with epsilon transitions."""
        nfa = NFA.objects.create(
            name="Epsilon NFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # States
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_final=False)
        q2 = nfa.states.create(name="q2", is_final=True)
        
        # Transitions
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="ε")  # Epsilon
        nfa.transitions.create(from_state=q1, to_state=q2, symbol="a")
        nfa.transitions.create(from_state=q0, to_state=q2, symbol="b")
        
        return nfa
        
    def test_nfa_creation(self):
        """Test NFA creation."""
        nfa = self.create_simple_nfa()
        self.assertEqual(nfa.name, "Ends with ab")
        self.assertEqual(nfa.states.count(), 3)
        self.assertEqual(nfa.transitions.count(), 3)
        
    def test_nfa_is_valid(self):
        """Test NFA validation."""
        nfa = self.create_simple_nfa()
        is_valid, message = nfa.is_valid()
        self.assertTrue(is_valid)
        self.assertEqual(message, "NFA is valid.")
        
    def test_nfa_is_dfa_check(self):
        """Test NFA to DFA check."""
        nfa = self.create_simple_nfa()
        is_dfa, message = nfa.is_dfa()
        self.assertFalse(is_dfa)  # Has multiple transitions for same symbol
        
        # Test with epsilon transitions
        epsilon_nfa = self.create_epsilon_nfa()
        is_dfa, message = epsilon_nfa.is_dfa()
        self.assertFalse(is_dfa)
        self.assertEqual(message, "NFA has epsilon transitions.")
        
    def test_nfa_simulate_accept(self):
        """Test NFA simulation - accepting strings."""
        nfa = self.create_simple_nfa()
        
        # Test accepting strings (ending with 'ab')
        test_cases = ["ab", "aab", "bab", "aaab", "abab"]
        for test_string in test_cases:
            accepted, message, path = nfa.simulate(test_string)
            self.assertTrue(accepted, f"String '{test_string}' should be accepted")
            self.assertEqual(message, "String accepted.")
            
    def test_nfa_simulate_reject(self):
        """Test NFA simulation - rejecting strings."""
        nfa = self.create_simple_nfa()
        
        # Test rejecting strings (not ending with 'ab')
        test_cases = ["", "a", "b", "aa", "ba", "aba"]
        for test_string in test_cases:
            accepted, message, path = nfa.simulate(test_string)
            self.assertFalse(accepted, f"String '{test_string}' should be rejected")
            self.assertEqual(message, "String rejected.")
            
    def test_nfa_epsilon_closure(self):
        """Test NFA with epsilon transitions."""
        nfa = self.create_epsilon_nfa()
        
        # Test strings that should be accepted
        accepted, message, path = nfa.simulate("a")
        self.assertTrue(accepted)  # q0 -ε-> q1 -a-> q2 (final)
        
        accepted, message, path = nfa.simulate("b")
        self.assertTrue(accepted)  # q0 -b-> q2 (final)
        
    def test_nfa_multiple_start_states(self):
        """Test NFA with multiple start states."""
        nfa = NFA.objects.create(
            name="Multiple Start NFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # Multiple start states
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_start=True, is_final=True)
        q2 = nfa.states.create(name="q2", is_final=True)
        
        # Transitions
        nfa.transitions.create(from_state=q0, to_state=q2, symbol="a")
        
        accepted, message, path = nfa.simulate("")
        self.assertTrue(accepted)  # q1 is start and final
        
    def test_nfa_helper_methods(self):
        """Test NFA helper methods."""
        nfa = self.create_epsilon_nfa()
        
        # Test get_start_states
        start_states = nfa.get_start_states()
        self.assertEqual(start_states.count(), 1)
        self.assertEqual(start_states.first().name, "q0")
        
        # Test get_final_states
        final_states = nfa.get_final_states()
        self.assertEqual(final_states.count(), 1)
        self.assertEqual(final_states.first().name, "q2")
        
        # Test get_epsilon_transitions
        epsilon_transitions = nfa.get_epsilon_transitions()
        self.assertEqual(len(epsilon_transitions), 1)
        
    def test_nfa_add_transition_helper(self):
        """Test NFA add_transition helper method."""
        nfa = self.create_simple_nfa()
        q0 = nfa.states.get(name="q0")
        q1 = nfa.states.get(name="q1")
        
        # Add transition with multiple symbols
        transition = nfa.add_transition(q0, q1, ['a', 'b'])
        self.assertEqual(transition.symbol, 'a,b')
        
        # Add transition with string
        transition2 = nfa.add_transition(q0, q1, 'c')
        self.assertEqual(transition2.symbol, 'c')


class DFAMinimizationTest(TestCase):
    """Test cases for DFA minimization."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def create_minimizable_dfa(self):
        """Create a DFA that can be minimized."""
        dfa = DFA.objects.create(
            name="Minimizable DFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # States (q1 and q2 are equivalent)
        q0 = dfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = dfa.states.create(name="q1", is_final=True)
        q2 = dfa.states.create(name="q2", is_final=True)
        
        # Transitions
        dfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        dfa.transitions.create(from_state=q0, to_state=q2, symbol="b")
        dfa.transitions.create(from_state=q1, to_state=q1, symbol="a")
        dfa.transitions.create(from_state=q1, to_state=q1, symbol="b")
        dfa.transitions.create(from_state=q2, to_state=q2, symbol="a")
        dfa.transitions.create(from_state=q2, to_state=q2, symbol="b")
        
        return dfa
        
    def test_dfa_minimization(self):
        """Test DFA minimization."""
        dfa = self.create_minimizable_dfa()
        original_state_count = dfa.states.count()
        
        minimized_dfa = dfa.minimize()
        
        # Check that minimization created a new DFA
        self.assertNotEqual(dfa.id, minimized_dfa.id)
        self.assertEqual(minimized_dfa.name, f"{dfa.name}_minimized")
        
        # Check that the minimized DFA has fewer states
        self.assertLess(minimized_dfa.states.count(), original_state_count)
        
        # Check that the minimized DFA is valid
        is_valid, message = minimized_dfa.is_valid()
        self.assertTrue(is_valid)


class NFAToDFATest(TestCase):
    """Test cases for NFA to DFA conversion."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def create_convertible_nfa(self):
        """Create an NFA that can be converted to DFA."""
        nfa = NFA.objects.create(
            name="Convertible NFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # States
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_final=True)
        
        # Transitions
        nfa.transitions.create(from_state=q0, to_state=q0, symbol="a")
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="b")
        nfa.transitions.create(from_state=q1, to_state=q1, symbol="a,b")
        
        return nfa
        
    def test_nfa_to_dfa_conversion(self):
        """Test NFA to DFA conversion."""
        nfa = self.create_convertible_nfa()
        
        dfa = nfa.to_dfa()
        
        # Check that conversion created a new DFA
        self.assertIsInstance(dfa, DFA)
        self.assertEqual(dfa.name, f"{nfa.name}_DFA")
        self.assertEqual(dfa.alphabet, nfa.alphabet)
        
        # Check that the DFA is valid
        is_valid, message = dfa.is_valid()
        self.assertTrue(is_valid)
        
        # Test that both automata accept the same strings
        test_strings = ["", "a", "b", "ab", "ba", "abb", "aab"]
        for test_string in test_strings:
            nfa_result, _, _ = nfa.simulate(test_string)
            dfa_result, _, _ = dfa.simulate(test_string)
            self.assertEqual(nfa_result, dfa_result, 
                           f"String '{test_string}' should have same result in both automata")


class AutomatonViewTest(TestCase):
    """Test cases for automaton views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
    def test_dashboard_view(self):
        """Test dashboard view."""
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        
    def test_create_dfa_view(self):
        """Test DFA creation view."""
        response = self.client.get(reverse('core:create_dfa'))
        self.assertEqual(response.status_code, 200)
        
        # Test POST request
        response = self.client.post(reverse('core:create_dfa'), {
            'name': 'Test DFA',
            'alphabet': 'a,b'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check that DFA was created
        dfa = DFA.objects.get(name='Test DFA')
        self.assertEqual(dfa.owner, self.user)
        
    def test_create_nfa_view(self):
        """Test NFA creation view."""
        response = self.client.get(reverse('core:create_nfa'))
        self.assertEqual(response.status_code, 200)
        
        # Test POST request
        response = self.client.post(reverse('core:create_nfa'), {
            'name': 'Test NFA',
            'alphabet': 'a,b'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check that NFA was created
        nfa = NFA.objects.get(name='Test NFA')
        self.assertEqual(nfa.owner, self.user)


class AutomatonAJAXTest(TestCase):
    """Test cases for AJAX endpoints."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.dfa = DFA.objects.create(
            name="Test DFA",
            alphabet="a,b",
            owner=self.user
        )
        
    def test_add_state_ajax(self):
        """Test adding state via AJAX."""
        url = reverse('core:add_state', kwargs={'pk': self.dfa.pk})
        data = json.dumps({'name': 'q0'})
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'ok')
        
        # Check that state was created
        state = self.dfa.states.get(name='q0')
        self.assertTrue(state.is_start)  # First state should be start state
        
    def test_get_alphabet_symbols_ajax(self):
        """Test getting alphabet symbols via AJAX."""
        url = reverse('core:get_alphabet_symbols', kwargs={'pk': self.dfa.pk})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertIn('symbols', response_data)
        
        expected_symbols = [
            {'value': 'a', 'label': 'a'},
            {'value': 'b', 'label': 'b'}
        ]
        self.assertEqual(response_data['symbols'], expected_symbols)
        
    def test_simulate_string_ajax(self):
        """Test string simulation via AJAX."""
        # Create a simple DFA first
        q0 = self.dfa.states.create(name="q0", is_start=True, is_final=True)
        q1 = self.dfa.states.create(name="q1", is_final=False)
        
        self.dfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        self.dfa.transitions.create(from_state=q0, to_state=q0, symbol="b")
        self.dfa.transitions.create(from_state=q1, to_state=q0, symbol="a")
        self.dfa.transitions.create(from_state=q1, to_state=q1, symbol="b")
        
        url = reverse('core:simulate_string', kwargs={'pk': self.dfa.pk})
        data = json.dumps({'string': 'aa'})
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertIn('accepted', response_data)
        self.assertIn('message', response_data)
        self.assertIn('path', response_data)


if __name__ == '__main__':
    import unittest
    unittest.main()
