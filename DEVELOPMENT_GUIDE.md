# Finite Automata Visualizer - Development Guide

## Overview

This comprehensive guide documents the development process and architecture of the Finite Automata Visualizer, a Django web application for creating, visualizing, and working with deterministic and nondeterministic finite automata.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Initial Setup](#initial-setup)
3. [Core Architecture](#core-architecture)
4. [Feature Implementation](#feature-implementation)
5. [Database Design](#database-design)
6. [API Endpoints](#api-endpoints)
7. [Frontend Integration](#frontend-integration)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

## Project Structure

```
automata/
├── automata/                 # Main Django project
│   ├── __init__.py
│   ├── asgi.py
│   ├── main.py
│   ├── settings.py          # Database config, apps, middleware
│   ├── urls.py              # Root URL configuration
│   ├── views.py
│   └── wsgi.py
├── core/                    # Main application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py             # DFA/NFA creation forms
│   ├── models.py            # Core data models
│   ├── urls.py              # App URL patterns
│   ├── views.py             # View logic and API endpoints
│   ├── migrations/          # Database migrations
│   ├── templates/           # HTML templates
│   │   └── automaton/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── automaton_detail.html
│   │       ├── create_dfa.html
│   │       ├── create_nfa.html
│   │       └── ...
│   ├── management/          # Custom Django commands
│   │   └── commands/
│   │       ├── populate_exercises.py
│   │       └── populate_diverse_examples.py
│   └── templatetags/        # Custom template filters
├── theme/                   # Tailwind CSS theme
│   ├── static_src/          # Source CSS and build tools
│   │   ├── src/
│   │   ├── package.json
│   │   ├── postcss.config.js
│   │   └── node_modules/
│   └── static/              # Compiled CSS output
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
├── README.md               # Project documentation
├── CLAUDE.md               # Claude Code guidance
└── DEVELOPMENT_GUIDE.md    # This file
```

## Initial Setup

### 1. Environment Setup

```bash
# Clone the project
git clone [repository-url]
cd automata

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd theme/static_src
npm install
cd ../..
```

### 2. Database Configuration

The project uses PostgreSQL with Supabase. Configuration is in `automata/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres.yqygrtsyixslpyyzdvaa',
        'PASSWORD': '12345',
        'HOST': 'aws-0-ap-southeast-1.pooler.supabase.com',
        'PORT': '6543',
    }
}
```

### 3. Database Migrations

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Populate example data
python manage.py populate_exercises
```

**Note**: If you encounter `is_example` field errors during creation, ensure the field exists in both the model and database. The field was added to track system example automata vs user-created ones.

### 4. Frontend Build

```bash
# Development mode (watches for changes)
cd theme/static_src
npm run dev

# Production build
npm run build
```

### 5. Running the Server

```bash
python manage.py runserver
```

## Core Architecture

### Model Hierarchy

The application uses an abstract base class pattern for code reuse:

```python
# Abstract Models
class Automaton(models.Model):
    # Common fields: name, alphabet, owner, json_representation
    class Meta:
        abstract = True

class State(models.Model):
    # Common state fields: name, is_start, is_final
    class Meta:
        abstract = True

class Transition(models.Model):
    # Common transition fields: from_state, to_state, symbol
    class Meta:
        abstract = True

# Concrete Models
class DFA(Automaton):
    # DFA-specific methods: is_valid(), simulate(), minimize()

class NFA(Automaton):
    # NFA-specific methods: is_valid(), simulate(), is_dfa(), to_dfa()

class DFAState(State):
    automaton = models.ForeignKey('DFA', ...)

class NFAState(State):
    automaton = models.ForeignKey('NFA', ...)

class DFATransition(Transition):
    from_state = models.ForeignKey(DFAState, ...)
    to_state = models.ForeignKey(DFAState, ...)

class NFATransition(Transition):
    from_state = models.ForeignKey(NFAState, ...)
    to_state = models.ForeignKey(NFAState, ...)
```

### User History Tracking

```python
class UserHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    automaton_id = models.PositiveIntegerField()
    automaton_name = models.CharField(max_length=255)
    automaton_type = models.CharField(max_length=10)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(null=True, blank=True)
    
    @classmethod
    def log_action(cls, user, automaton, action, details=None):
        # Helper method to log user actions
```

## Feature Implementation

### 1. Generic FA Type Checker

The `check_fa_type()` method works on any automaton type:

```python
def check_fa_type(self):
    """
    Returns tuple: (fa_type, is_valid, message)
    where fa_type is 'DFA', 'NFA', or 'INVALID'
    """
    # Check for epsilon transitions
    if has_epsilon_transitions:
        return 'NFA', True, "Automaton has epsilon transitions"
    
    # Check for multiple start states
    if multiple_start_states:
        return 'NFA', True, "Automaton has multiple start states"
    
    # Check for nondeterministic transitions
    if nondeterministic_transitions:
        return 'NFA', True, f"Multiple transitions for symbol '{symbol}'"
    
    # Check completeness
    if complete_dfa:
        return 'DFA', True, "Complete deterministic finite automaton"
    else:
        return 'DFA', True, "Incomplete DFA (missing transitions)"
```

### 2. Enhanced NFA Transition Support

Range and multi-symbol transition parsing:

```python
def get_symbols_as_set(self):
    """Supports ranges like a-z, 0-9 and multi-symbols like a,b,c"""
    symbols = set()
    for part in self.symbol.split(','):
        # Handle ranges like a-z, 0-9, A-Z
        if re.match(r'^([a-zA-Z0-9])-([a-zA-Z0-9])$', part):
            start_char, end_char = match.groups()
            symbols.update(chr(i) for i in range(ord(start_char), ord(end_char) + 1))
        else:
            symbols.add(part)
    return symbols
```

### 3. User Activity Logging

Automatic logging in views:

```python
# Creation logging
def form_valid(self, form):
    response = super().form_valid(form)
    UserHistory.log_action(
        user=self.request.user,
        automaton=self.object,
        action='create',
        details={'automaton_type': 'DFA'}
    )
    return response

# Simulation logging
def simulate_string(request, pk):
    # ... simulation logic ...
    UserHistory.log_action(
        user=request.user,
        automaton=automaton,
        action='simulate',
        details={
            'input_string': input_string,
            'accepted': accepted,
            'result_message': message
        }
    )
```

## Database Design

### Entity Relationship Diagram

```
User
├── UserHistory (many-to-one)
├── DFA (many-to-one, nullable)
└── NFA (many-to-one, nullable)

DFA
├── DFAState (one-to-many)
└── DFATransition (one-to-many)

NFA
├── NFAState (one-to-many)
└── NFATransition (one-to-many)

DFATransition
├── from_state (many-to-one DFAState)
└── to_state (many-to-one DFAState)

NFATransition
├── from_state (many-to-one NFAState)
└── to_state (many-to-one NFAState)
```

### Key Indexes

```python
class UserHistory:
    class Meta:
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['user', 'action']),
        ]
```

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/automata/api/automaton/<id>/json/` | GET | Get automaton graph data |
| `/automata/api/automaton/<id>/simulate/` | GET | Simulate string input |
| `/automata/api/automaton/<id>/check-fa-type/` | GET | Generic FA type checker |
| `/automata/api/dfa/<id>/minimize/` | POST | Minimize DFA |
| `/automata/api/nfa/<id>/to-dfa/` | POST | Convert NFA to DFA |
| `/automata/api/automaton/<id>/add-state/` | POST | Add new state |
| `/automata/api/automaton/<id>/add-transition/` | POST | Add new transition |

### API Response Format

```json
// Generic FA Checker Response
{
    "fa_type": "DFA|NFA|INVALID",
    "is_valid": true,
    "message": "Detailed explanation",
    "current_type": "DFA"
}

// Simulation Response
{
    "accepted": true,
    "message": "String accepted",
    "path": ["q0", "q1", "q2"]
}

// Minimization Response
{
    "status": "success",
    "message": "DFA successfully minimized",
    "minimized_dfa_id": 123,
    "minimized_dfa_name": "MyDFA_minimized"
}
```

## Frontend Integration

### Dashboard Features

The dashboard shows:
- User statistics (created automata, simulations)
- Recent activity feed with action details
- Quick creation buttons
- System examples access

### Cytoscape.js Integration

Graph visualization uses Cytoscape.js with:
- Node styling based on state type (start/final)
- Edge labels for transition symbols
- Interactive editing capabilities
- JSON representation storage

### Real-time Updates

AJAX endpoints provide real-time updates without page refresh:
- State management (add/edit/delete)
- Transition management
- String simulation with path highlighting
- FA type checking

## Testing Strategy

### Model Tests

```python
class AutomatonModelTest(TestCase):
    def test_get_symbols_as_set_range(self):
        # Test range expansion: a-z, 0-9
        
    def test_check_fa_type_detection(self):
        # Test generic FA type checker
        
    def test_user_history_logging(self):
        # Test activity logging
```

### View Tests

```python
class AutomatonViewTest(TestCase):
    def test_user_specific_access(self):
        # Test user isolation
        
    def test_api_endpoints(self):
        # Test AJAX API responses
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test files
python manage.py test core.tests
python manage.py test core.test_advanced
python manage.py test core.test_api

# Run with verbosity
python manage.py test -v 2
```

## Deployment

### Production Checklist

1. **Security Settings**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   SECRET_KEY = os.environ.get('SECRET_KEY')
   ```

2. **Database Migration**
   ```bash
   python manage.py collectstatic
   python manage.py migrate
   python manage.py populate_exercises
   ```

3. **CSS Build**
   ```bash
   cd theme/static_src
   npm run build
   ```

### Environment Variables

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
DB_NAME=production_db
DB_USER=production_user
DB_PASSWORD=production_password
DB_HOST=production_host
DB_PORT=5432
```

## Troubleshooting

### Common Issues

1. **CSS Not Loading**
   - Run `npm run build` in `theme/static_src/`
   - Check `STATIC_URL` and `STATIC_ROOT` settings

2. **Migration Errors**
   - Check database connection
   - Run `python manage.py showmigrations`
   - Reset migrations if needed: `python manage.py migrate core zero`

3. **Permission Errors**
   - Verify user authentication in views
   - Check `get_automaton_instance()` helper function

4. **JavaScript Errors**
   - Check browser console for AJAX errors
   - Verify CSRF token inclusion in requests

5. **DFA/NFA Creation Issues**
   - Ensure `is_example` field exists in model and database
   - Check that `owner` field is properly set in views
   - Verify form validation in templates
   - Run `python manage.py makemigrations` and `python manage.py migrate`

6. **UserHistory Not Logging**
   - Check that UserHistory.log_action() is called in views
   - Verify user authentication before logging
   - Check database permissions for UserHistory table

7. **Input Field Text Not Visible**
   - Form fields now use white background with dark text
   - CSS classes: `bg-white border border-gray-300 text-gray-900`
   - Ensure Tailwind CSS is properly compiled

8. **Creation Flow Issues**
   - Creation now uses two-step process: Preview → Confirm → Create
   - Check for `action` parameter in POST requests
   - Verify confirmation templates exist

### Development Tips

1. **Adding New Features**
   - Follow the abstract model pattern
   - Add corresponding tests
   - Update UserHistory logging
   - Add API endpoints if needed

2. **Database Changes**
   - Always create migrations: `python manage.py makemigrations`
   - Test migrations on sample data
   - Update model documentation

3. **Frontend Changes**
   - Use Tailwind CSS classes
   - Test responsive design
   - Maintain accessibility standards

### Creation Issues Fix

If you encounter issues with DFA/NFA creation, follow these steps:

1. **Check Model Fields**
   ```python
   # Ensure Automaton model has is_example field
   class Automaton(models.Model):
       # ... other fields ...
       is_example = models.BooleanField(default=False)
   ```

2. **Update Views**
   ```python
   def form_valid(self, form):
       form.instance.owner = self.request.user
       form.instance.is_example = False  # Mark as user-created
       return super().form_valid(form)
   ```

3. **Create Migration**
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   ```

4. **Test Creation**
   ```python
   from core.models import DFA
   dfa = DFA.objects.create(name='Test', alphabet='a,b', owner=user)
   ```

## Future Enhancements

### Potential Features

1. **Export/Import**
   - JSON/XML export of automata
   - JFLAP file format support

2. **Collaboration**
   - Share automata between users
   - Real-time collaborative editing

3. **Advanced Algorithms**
   - Regular expression to automaton conversion
   - Automaton equivalence checking

4. **Enhanced Visualization**
   - Animation of string processing
   - Multiple layout algorithms

### Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

This guide provides a comprehensive overview for developers working on the Finite Automata Visualizer. For specific implementation details, refer to the inline code comments and existing test cases.