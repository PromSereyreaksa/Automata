"""
Test cases for web interface and API endpoints.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
import json

from .models import DFA, NFA


class WebInterfaceTest(TestCase):
    """Test the web interface functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create test automata
        self.dfa = DFA.objects.create(
            name="Test DFA",
            alphabet="a,b",
            owner=self.user
        )
        self.q0 = self.dfa.states.create(name="q0", is_start=True, is_final=True)
        self.q1 = self.dfa.states.create(name="q1", is_final=False)
        self.dfa.transitions.create(from_state=self.q0, to_state=self.q1, symbol="a")
        self.dfa.transitions.create(from_state=self.q0, to_state=self.q0, symbol="b")
        self.dfa.transitions.create(from_state=self.q1, to_state=self.q0, symbol="a")
        self.dfa.transitions.create(from_state=self.q1, to_state=self.q1, symbol="b")
        
    def test_dashboard_shows_automata(self):
        """Test that dashboard shows user's automata."""
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test DFA")
        
    def test_dfa_detail_view(self):
        """Test DFA detail view."""
        response = self.client.get(reverse('core:dfa_detail', kwargs={'pk': self.dfa.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test DFA")
        self.assertContains(response, "q0")
        self.assertContains(response, "q1")
        
    def test_create_dfa_form_validation(self):
        """Test DFA creation form validation."""
        # Valid form
        response = self.client.post(reverse('core:create_dfa'), {
            'name': 'New DFA',
            'alphabet': 'x,y,z'
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Check DFA was created
        new_dfa = DFA.objects.get(name='New DFA')
        self.assertEqual(new_dfa.alphabet, 'x,y,z')
        self.assertEqual(new_dfa.owner, self.user)
        
        # Invalid form (empty name)
        response = self.client.post(reverse('core:create_dfa'), {
            'name': '',
            'alphabet': 'a,b'
        })
        self.assertEqual(response.status_code, 200)  # Stay on form page
        self.assertFormError(response, 'form', 'name', 'This field is required.')
        
    def test_create_nfa_form_validation(self):
        """Test NFA creation form validation."""
        # Valid form
        response = self.client.post(reverse('core:create_nfa'), {
            'name': 'New NFA',
            'alphabet': 'p,q'
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Check NFA was created
        new_nfa = NFA.objects.get(name='New NFA')
        self.assertEqual(new_nfa.alphabet, 'p,q')
        self.assertEqual(new_nfa.owner, self.user)
        
    def test_unauthorized_access(self):
        """Test that unauthorized users can't access automata."""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass'
        )
        other_dfa = DFA.objects.create(
            name="Other DFA",
            alphabet="x,y",
            owner=other_user
        )
        
        # Current user should not be able to access other user's DFA
        response = self.client.get(reverse('core:dfa_detail', kwargs={'pk': other_dfa.pk}))
        self.assertEqual(response.status_code, 404)
        
    def test_system_examples_accessible(self):
        """Test that system examples are accessible to all users."""
        # Create system example (no owner)
        system_dfa = DFA.objects.create(
            name="System Example DFA",
            alphabet="0,1",
            owner=None
        )
        
        # User should be able to access system examples
        response = self.client.get(reverse('core:dfa_detail', kwargs={'pk': system_dfa.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Example DFA")


class APIEndpointTest(TestCase):
    """Test API endpoints for AJAX functionality."""
    
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
        
    def test_get_automaton_json(self):
        """Test getting automaton JSON representation."""
        url = reverse('core:get_automaton_json', kwargs={'pk': self.dfa.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        
    def test_get_alphabet_symbols(self):
        """Test getting alphabet symbols."""
        url = reverse('core:get_alphabet_symbols', kwargs={'pk': self.dfa.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('symbols', data)
        expected_symbols = [
            {'value': 'a', 'label': 'a'},
            {'value': 'b', 'label': 'b'}
        ]
        self.assertEqual(data['symbols'], expected_symbols)
        
    def test_get_alphabet_symbols_nfa(self):
        """Test getting alphabet symbols for NFA (includes epsilon)."""
        nfa = NFA.objects.create(
            name="Test NFA",
            alphabet="x,y",
            owner=self.user
        )
        
        url = reverse('core:get_alphabet_symbols', kwargs={'pk': nfa.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('symbols', data)
        symbols = data['symbols']
        
        # Should include epsilon first, then alphabet symbols
        self.assertEqual(symbols[0], {'value': 'ε', 'label': 'ε (epsilon)'})
        self.assertIn({'value': 'x', 'label': 'x'}, symbols)
        self.assertIn({'value': 'y', 'label': 'y'}, symbols)
        
    def test_add_state_api(self):
        """Test adding state via API."""
        url = reverse('core:add_state', kwargs={'pk': self.dfa.pk})
        data = json.dumps({'name': 'q0'})
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'ok')
        
        # Check state was created
        state = self.dfa.states.get(name='q0')
        self.assertTrue(state.is_start)  # First state should be start
        
    def test_add_state_duplicate_name(self):
        """Test adding state with duplicate name."""
        # Add first state
        self.dfa.states.create(name='q0', is_start=True)
        
        url = reverse('core:add_state', kwargs={'pk': self.dfa.pk})
        data = json.dumps({'name': 'q0'})
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('already exists', response_data['message'])
        
    def test_add_transition_api(self):
        """Test adding transition via API."""
        # Create states first
        q0 = self.dfa.states.create(name='q0', is_start=True)
        q1 = self.dfa.states.create(name='q1', is_final=True)
        
        url = reverse('core:add_transition', kwargs={'pk': self.dfa.pk})
        data = json.dumps({
            'from_state': q0.pk,
            'to_state': q1.pk,
            'symbol': 'a'
        })
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'ok')
        
        # Check transition was created
        transition = self.dfa.transitions.get(from_state=q0, to_state=q1, symbol='a')
        self.assertIsNotNone(transition)
        
    def test_add_transition_invalid_symbol(self):
        """Test adding transition with invalid symbol."""
        q0 = self.dfa.states.create(name='q0', is_start=True)
        q1 = self.dfa.states.create(name='q1', is_final=True)
        
        url = reverse('core:add_transition', kwargs={'pk': self.dfa.pk})
        data = json.dumps({
            'from_state': q0.pk,
            'to_state': q1.pk,
            'symbol': 'x'  # Not in alphabet
        })
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')
        self.assertIn('not in the alphabet', response_data['message'])
        
    def test_simulate_string_api(self):
        """Test string simulation via API."""
        # Create a complete DFA
        q0 = self.dfa.states.create(name='q0', is_start=True, is_final=True)
        q1 = self.dfa.states.create(name='q1', is_final=False)
        
        self.dfa.transitions.create(from_state=q0, to_state=q1, symbol='a')
        self.dfa.transitions.create(from_state=q0, to_state=q0, symbol='b')
        self.dfa.transitions.create(from_state=q1, to_state=q0, symbol='a')
        self.dfa.transitions.create(from_state=q1, to_state=q1, symbol='b')
        
        url = reverse('core:simulate_string', kwargs={'pk': self.dfa.pk})
        data = json.dumps({'string': 'aa'})
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertIn('accepted', response_data)
        self.assertIn('message', response_data)
        self.assertIn('path', response_data)
        
        # Test accepted string (even number of a's)
        self.assertTrue(response_data['accepted'])
        
        # Test rejected string (odd number of a's)
        data = json.dumps({'string': 'a'})
        response = self.client.post(url, data, content_type='application/json')
        response_data = json.loads(response.content)
        self.assertFalse(response_data['accepted'])
        
    def test_update_state_api(self):
        """Test updating state properties via API."""
        q0 = self.dfa.states.create(name='q0', is_start=True, is_final=False)
        
        url = reverse('core:update_state', kwargs={'pk': self.dfa.pk})
        
        # Test toggle final
        data = json.dumps({
            'action': 'toggle_final',
            'state_pk': q0.pk
        })
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check state was updated
        q0.refresh_from_db()
        self.assertTrue(q0.is_final)
        
        # Test set start (should unset other start states)
        q1 = self.dfa.states.create(name='q1', is_start=False)
        data = json.dumps({
            'action': 'set_start',
            'state_pk': q1.pk
        })
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check states were updated
        q0.refresh_from_db()
        q1.refresh_from_db()
        self.assertFalse(q0.is_start)
        self.assertTrue(q1.is_start)
        
    def test_delete_state_api(self):
        """Test deleting state via API."""
        q0 = self.dfa.states.create(name='q0', is_start=True)
        
        url = reverse('core:delete_state', kwargs={'pk': self.dfa.pk})
        data = json.dumps({'state_pk': q0.pk})
        
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check state was deleted
        self.assertFalse(self.dfa.states.filter(pk=q0.pk).exists())
        
    def test_api_requires_authentication(self):
        """Test that API endpoints require authentication."""
        self.client.logout()
        
        # Test various endpoints
        endpoints = [
            reverse('core:get_automaton_json', kwargs={'pk': self.dfa.pk}),
            reverse('core:get_alphabet_symbols', kwargs={'pk': self.dfa.pk}),
            reverse('core:add_state', kwargs={'pk': self.dfa.pk}),
            reverse('core:simulate_string', kwargs={'pk': self.dfa.pk}),
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Should redirect to login or return 403/401
            self.assertIn(response.status_code, [302, 401, 403])


class IntegrationTest(TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
    def test_complete_dfa_creation_workflow(self):
        """Test complete workflow of creating and using a DFA."""
        # 1. Create DFA
        response = self.client.post(reverse('core:create_dfa'), {
            'name': 'Workflow DFA',
            'alphabet': 'x,y'
        })
        self.assertEqual(response.status_code, 302)
        
        dfa = DFA.objects.get(name='Workflow DFA')
        
        # 2. Add states
        add_state_url = reverse('core:add_state', kwargs={'pk': dfa.pk})
        
        response = self.client.post(add_state_url, 
                                  json.dumps({'name': 'q0'}), 
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(add_state_url, 
                                  json.dumps({'name': 'q1'}), 
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # 3. Set state properties
        q0 = dfa.states.get(name='q0')
        q1 = dfa.states.get(name='q1')
        
        update_state_url = reverse('core:update_state', kwargs={'pk': dfa.pk})
        
        # Make q1 final
        response = self.client.post(update_state_url,
                                  json.dumps({'action': 'toggle_final', 'state_pk': q1.pk}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # 4. Add transitions
        add_transition_url = reverse('core:add_transition', kwargs={'pk': dfa.pk})
        
        transitions = [
            {'from_state': q0.pk, 'to_state': q0.pk, 'symbol': 'x'},
            {'from_state': q0.pk, 'to_state': q1.pk, 'symbol': 'y'},
            {'from_state': q1.pk, 'to_state': q1.pk, 'symbol': 'x'},
            {'from_state': q1.pk, 'to_state': q1.pk, 'symbol': 'y'},
        ]
        
        for transition in transitions:
            response = self.client.post(add_transition_url,
                                      json.dumps(transition),
                                      content_type='application/json')
            self.assertEqual(response.status_code, 200)
            
        # 5. Test simulation
        simulate_url = reverse('core:simulate_string', kwargs={'pk': dfa.pk})
        
        test_cases = [
            ('y', True),    # Should accept (ends in final state)
            ('xy', True),   # Should accept
            ('x', False),   # Should reject (not in final state)
            ('', False),    # Should reject (start state not final)
        ]
        
        for test_string, expected in test_cases:
            response = self.client.post(simulate_url,
                                      json.dumps({'string': test_string}),
                                      content_type='application/json')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertEqual(data['accepted'], expected,
                           f"String '{test_string}' simulation failed")
            
        # 6. Verify DFA is valid
        is_valid, message = dfa.is_valid()
        self.assertTrue(is_valid, f"DFA should be valid: {message}")
        
    def test_nfa_to_dfa_conversion_workflow(self):
        """Test complete NFA to DFA conversion workflow."""
        # 1. Create NFA
        nfa = NFA.objects.create(
            name="Test NFA",
            alphabet="a,b",
            owner=self.user
        )
        
        # 2. Build NFA (accepts strings ending with 'ab')
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_final=False)
        q2 = nfa.states.create(name="q2", is_final=True)
        
        nfa.transitions.create(from_state=q0, to_state=q0, symbol="a,b")
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="a")
        nfa.transitions.create(from_state=q1, to_state=q2, symbol="b")
        
        # 3. Test NFA
        test_cases = [
            ("ab", True),
            ("aab", True),
            ("bab", True),
            ("", False),
            ("a", False),
            ("aba", False),
        ]
        
        for test_string, expected in test_cases:
            accepted, _, _ = nfa.simulate(test_string)
            self.assertEqual(accepted, expected,
                           f"NFA test failed for '{test_string}'")
            
        # 4. Convert to DFA
        dfa = nfa.to_dfa()
        
        # 5. Test DFA gives same results
        for test_string, expected in test_cases:
            accepted, _, _ = dfa.simulate(test_string)
            self.assertEqual(accepted, expected,
                           f"DFA test failed for '{test_string}'")
            
        # 6. Verify DFA is valid
        is_valid, message = dfa.is_valid()
        self.assertTrue(is_valid, f"Converted DFA should be valid: {message}")


if __name__ == '__main__':
    import unittest
    unittest.main()
