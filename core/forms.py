from django import forms
from .models import DFA, NFA, DFAState, DFATransition, NFAState, NFATransition

# Common Tailwind CSS classes for form inputs to ensure consistent styling
text_input_classes = "w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
select_classes = "w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"

class DFACreateForm(forms.ModelForm):
    """
    A form for creating a new Deterministic Finite Automaton (DFA).
    It handles the name and alphabet, which are the initial properties.
    States and transitions will be managed dynamically on the automaton's detail page.
    """
    class Meta:
        model = DFA
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

class NFACreateForm(forms.ModelForm):
    """
    A form for creating a new Nondeterministic Finite Automaton (NFA).
    Similar to the DFA form, it handles the initial setup.
    """
    class Meta:
        model = NFA
        fields = ['name', 'alphabet']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': text_input_classes,
                'placeholder': 'e.g., Ends with "ab"'
            }),
            'alphabet': forms.TextInput(attrs={
                'class': text_input_classes,
                'placeholder': 'e.g., a,b'
            }),
        }
        help_texts = {
            'alphabet': 'Enter symbols separated by commas. Epsilon transitions (ε) are automatically available.',
        }

class DFAStateForm(forms.ModelForm):
    """Form for creating DFA states."""
    class Meta:
        model = DFAState
        fields = ['name', 'is_start', 'is_final']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': text_input_classes,
                'placeholder': 'e.g., q0'
            }),
        }

class NFAStateForm(forms.ModelForm):
    """Form for creating NFA states."""
    class Meta:
        model = NFAState
        fields = ['name', 'is_start', 'is_final']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': text_input_classes,
                'placeholder': 'e.g., q0'
            }),
        }

class DFATransitionForm(forms.ModelForm):
    """Form for creating DFA transitions with symbol selection."""
    class Meta:
        model = DFATransition
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
            self.fields['symbol'].widget = forms.Select(
                choices=symbol_choices,
                attrs={'class': select_classes}
            )

class NFATransitionForm(forms.ModelForm):
    """Form for creating NFA transitions with symbol selection."""
    class Meta:
        model = NFATransition
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
            
            # Set symbol choices from alphabet + epsilon
            alphabet = automaton.get_alphabet_as_set()
            symbol_choices = [('ε', 'ε (epsilon)')]  # Epsilon always available for NFA
            symbol_choices.extend([(symbol, symbol) for symbol in sorted(alphabet)])
            
            # Allow multiple symbol selection for NFA (a,b format)
            symbol_choices.append(('multiple', 'Multiple symbols (a,b)'))
            
            self.fields['symbol'].widget = forms.Select(
                choices=symbol_choices,
                attrs={'class': select_classes}
            )

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
