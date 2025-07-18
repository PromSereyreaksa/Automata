from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Automaton, State, Transition


class Command(BaseCommand):
    help = 'Creates NFA to DFA conversion examples from Rohini College PDF'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to assign as owner of the examples',
        )

    def handle(self, *args, **options):
        username = options['user']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, password='password')
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))

        # Create Example 1 from PDF
        self.create_example_1(user)
        
        # Create Example 2 from PDF
        self.create_example_2(user)
        
        self.stdout.write(self.style.SUCCESS('Successfully created Rohini College NFA examples'))

    def create_example_1(self, user):
        """
        Create Example 1 from PDF:
        NFA with states q0, q1, q2
        Alphabet: {0, 1}
        Transitions:
        q0 --0--> q0
        q0 --1--> q1
        q1 --0--> {q1, q2}
        q1 --1--> q1
        q2 --0--> q2
        q2 --1--> {q1, q2}
        Start state: q0
        Final state: q2
        """
        # Delete existing example if it exists
        Automaton.objects.filter(name="Rohini Example 1 - NFA").delete()
        
        nfa = Automaton.objects.create(
            name="Rohini Example 1 - NFA",
            alphabet="0,1",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create states
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_start=False, is_final=False)
        q2 = nfa.states.create(name="q2", is_start=False, is_final=True)
        
        # Create transitions
        nfa.transitions.create(from_state=q0, to_state=q0, symbol="0")
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="1")
        nfa.transitions.create(from_state=q1, to_state=q1, symbol="0")
        nfa.transitions.create(from_state=q1, to_state=q2, symbol="0")
        nfa.transitions.create(from_state=q1, to_state=q1, symbol="1")
        nfa.transitions.create(from_state=q2, to_state=q2, symbol="0")
        nfa.transitions.create(from_state=q2, to_state=q1, symbol="1")
        nfa.transitions.create(from_state=q2, to_state=q2, symbol="1")
        
        self.stdout.write(self.style.SUCCESS(f'Created Example 1: {nfa.name}'))

    def create_example_2(self, user):
        """
        Create Example 2 from PDF:
        NFA with states q0, q1
        Alphabet: {0, 1}
        Transitions:
        q0 --0--> {q0, q1}
        q0 --1--> q1
        q1 --0--> ∅
        q1 --1--> {q0, q1}
        Start state: q0
        Final state: q1
        """
        # Delete existing example if it exists
        Automaton.objects.filter(name="Rohini Example 2 - NFA").delete()
        
        nfa = Automaton.objects.create(
            name="Rohini Example 2 - NFA",
            alphabet="0,1",
            owner=user,
            is_example=True,
            has_epsilon=False
        )
        
        # Create states
        q0 = nfa.states.create(name="q0", is_start=True, is_final=False)
        q1 = nfa.states.create(name="q1", is_start=False, is_final=True)
        
        # Create transitions
        nfa.transitions.create(from_state=q0, to_state=q0, symbol="0")
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="0")
        nfa.transitions.create(from_state=q0, to_state=q1, symbol="1")
        nfa.transitions.create(from_state=q1, to_state=q0, symbol="1")
        nfa.transitions.create(from_state=q1, to_state=q1, symbol="1")
        
        self.stdout.write(self.style.SUCCESS(f'Created Example 2: {nfa.name}'))