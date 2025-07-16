from django import forms
from .models import Automaton, State, Transition

# Common Tailwind CSS classes for form inputs to ensure consistent styling
text_input_classes = "w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
select_classes = "w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"

class AutomatonCreateForm(forms.ModelForm):
    """
    A form for creating a new Finite Automaton.
    It handles the name and alphabet, which are the initial properties.
    States and transitions will be managed dynamically on the automaton's detail page.
    """
    class Meta:
        model = Automaton
        fields = ['name', 'alphabet']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': text_input_classes,
                'placeholder': 'e.g., Even Number of A\'s'
            }),
            'alphabet': forms.TextInput(attrs={
                'class': text_input_classes,
                'placeholder': 'e.g., a,b'
            }),
        }
        help_texts = {
            'alphabet': 'Enter symbols separated by commas.',
        }

# Legacy forms for backward compatibility
class DFACreateForm(AutomatonCreateForm):
    pass

class NFACreateForm(AutomatonCreateForm):
    class Meta(AutomatonCreateForm.Meta):
        help_texts = {
            'alphabet': 'Enter symbols separated by commas. Epsilon transitions (ε) are automatically available.',
        }

class StateForm(forms.ModelForm):
    """Form for creating states."""
    class Meta:
        model = State
        fields = ['name', 'is_start', 'is_final']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': text_input_classes,
                'placeholder': 'e.g., q0'
            }),
        }

# Legacy forms for backward compatibility
class DFAStateForm(StateForm):
    pass

class NFAStateForm(StateForm):
    pass

class TransitionForm(forms.ModelForm):
    """Form for creating transitions with symbol selection."""
    class Meta:
        model = Transition
        fields = ['from_state', 'to_state', 'symbol']
        widgets = {
            'from_state': forms.Select(attrs={'class': select_classes}),
            'to_state': forms.Select(attrs={'class': select_classes}),
            'symbol': forms.Select(attrs={'class': select_classes}),
        }

    def __init__(self, *args, **kwargs):
        automaton = kwargs.pop('automaton', None)
        super().__init__(*args, **kwargs)
        
        if automaton:
            # Set state choices
            self.fields['from_state'].queryset = automaton.states.all()
            self.fields['to_state'].queryset = automaton.states.all()
            
            # Set symbol choices from alphabet
            alphabet = automaton.get_alphabet_as_set()
            symbol_choices = [(symbol, symbol) for symbol in sorted(alphabet)]
            
            # For NFA, add epsilon option
            if automaton.get_type() == 'NFA':
                symbol_choices.insert(0, ('ε', 'ε (epsilon)'))
            
            self.fields['symbol'].widget = forms.Select(
                choices=symbol_choices,
                attrs={'class': select_classes}
            )

# Legacy forms for backward compatibility
class DFATransitionForm(TransitionForm):
    pass

class NFATransitionForm(TransitionForm):
    pass

class MultipleSymbolForm(forms.Form):
    """Form for selecting multiple symbols for NFA transitions."""
    symbols = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        help_text='Select multiple symbols for this transition'
    )

    def __init__(self, *args, **kwargs):
        automaton = kwargs.pop('automaton', None)
        super().__init__(*args, **kwargs)
        
        if automaton:
            alphabet = automaton.get_alphabet_as_set()
            choices = [(symbol, symbol) for symbol in sorted(alphabet)]
            self.fields['symbols'].choices = choices
