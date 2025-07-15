## Project Overview

This is a Django web application for creating, visualizing, and working with finite automata (DFA and NFA). It provides an interactive interface for creating automatons, testing string acceptance, and performing operations like DFA minimization and NFA-to-DFA conversion.

## Development Commands

### Backend (Django)
- **Start development server**: `python manage.py runserver`
- **Run database migrations**: `python manage.py migrate`
- **Create migrations**: `python manage.py makemigrations`
- **Run tests**: `python manage.py test`
- **Populate example automata**: `python manage.py populate_exercises`
- **Access Django shell**: `python manage.py shell`

### Frontend (CSS/JavaScript)
- **Build CSS for production**: `cd theme/static_src && npm run build`
- **Watch CSS in development**: `cd theme/static_src && npm run dev`
- **Install frontend dependencies**: `cd theme/static_src && npm install`

### Database Setup
The project uses PostgreSQL (Supabase). Database credentials are in `automata/settings.py`. Make sure to run migrations before starting development.

## Architecture

### Core Models (`core/models.py`)
- **Automaton**: Abstract base class for DFA and NFA with generic FA type checking
- **DFA**: Deterministic Finite Automaton with validation and minimization
- **NFA**: Nondeterministic Finite Automaton with epsilon transitions and DFA conversion
- **State/Transition**: Abstract models with concrete DFAState/NFAState and DFATransition/NFATransition
- **UserHistory**: Tracks all user interactions (create, view, simulate, minimize, convert)

### Key Features
- **Interactive visualization**: Uses Cytoscape.js for graph rendering with zoom constraints
- **String simulation**: Test input strings against automata with visual path highlighting
- **DFA minimization**: Table-filling algorithm implementation
- **NFA to DFA conversion**: Subset construction algorithm
- **Real-time editing**: Dynamic state/transition management with auto-saving
- **Optimized user tracking**: Selective activity history and analytics dashboard
- **Generic FA checker**: Automatically detects DFA/NFA/Invalid automata types
- **Enhanced state management**: Range transitions, multi-symbol inputs, and batch operations
- **User-specific storage**: All automata saved to individual user accounts with auto-save

### Frontend Structure
- **Tailwind CSS**: Styling framework configured in `theme/` app
- **Templates**: Located in `core/templates/automaton/`
- **JavaScript**: Real-time graph visualization and interactive editing with auto-save
- **Dark theme**: UI designed with dark color scheme and proper contrast
- **Responsive design**: Modern authentication pages with full-screen layouts

### URL Structure
- `/` - Root page (redirects to dashboard if logged in, login if not)
- `/accounts/login/` - Modern login page with dark theme
- `/accounts/register/` - User registration page
- `/accounts/logout/` - Proper logout functionality
- `/automata/` - Dashboard with user statistics and optimized activity history
- `/automata/create/dfa/` - Create new DFA (direct creation)
- `/automata/create/nfa/` - Create new NFA (direct creation)
- `/automata/dfa/<id>/` - DFA detail view with real-time editing
- `/automata/nfa/<id>/` - NFA detail view with real-time editing
- `/automata/api/automaton/<id>/check-fa-type/` - Generic FA type checker
- `/automata/api/...` - AJAX endpoints for real-time operations with auto-save

### Testing
- Test files: `core/tests.py`, `core/test_advanced.py`, `core/test_api.py`
- Coverage includes model validation, simulation, and conversion algorithms
- Run with `python manage.py test core`

### Management Commands
- `populate_exercises.py`: Creates example DFAs and NFAs for demonstration
- Creates system user and sample automata for educational purposes

## Development Notes

- Models use abstract base classes with concrete implementations for DFA/NFA
- JSON representation field stores graph data for visualization
- Epsilon transitions supported in NFAs (symbol='ε' or empty string)
- Enhanced transition support: ranges (a-z, 0-9, A-Z) and multi-symbol inputs (a,b,c)
- State and transition validation ensures automata correctness
- Owner field supports both user-owned and system example automata
- UserHistory model tracks all user actions with detailed context
- Generic FA checker works on any automaton type, detecting DFA/NFA/Invalid states

## New Features Added

### Optimized User Activity Tracking
- **Selective logging**: Only tracks meaningful actions (create, edit) - no longer logs views or simulations
- Dashboard analytics with statistics and recent activity feed
- Detailed action logging for state/transition changes with context
- Improved performance with reduced database overhead

### Enhanced State and Transition Management  
- Range transitions: `a-z`, `0-9`, `A-Z` supported in transition symbols
- Multi-symbol transitions: `a,b,c` format for multiple symbols on single transition
- Batch state creation: Enter multiple state names separated by commas (e.g., "q0,q1,q2,q3")
- Proper validation and expansion of range expressions
- **Real-time updates**: No page refresh when adding/editing states and transitions
- **Auto-saving**: All changes persist immediately

### Generic FA Type Detection
- `check_fa_type()` method works on any automaton instance
- Automatically detects if automaton is DFA, NFA, or Invalid
- Identifies specific issues: epsilon transitions, multiple start states, nondeterminism
- Visual indicators in UI showing detected type vs. declared type

### Improved Creation Flow
- Direct creation process: Create → Edit immediately (no preview step)
- Better input field visibility with white background and dark text
- Automatons created directly and redirect to editing interface
- No confirmation step - save happens during editing instead of before
- Clear create/cancel buttons with descriptive actions
- **Auto-saving**: All changes save automatically without user intervention

### DFA Implementation Fixes
- Fixed DFA minimization algorithm to use `matches_symbol()` method instead of direct symbol comparison
- Improved transition lookup in both simulation and minimization to handle complex symbol patterns
- Fixed NFA to DFA conversion to properly handle start state validation
- Enhanced error handling in transition validation and creation

### Enhanced User Experience (UX)
- **No more page refreshes**: Real-time updates maintain zoom level and graph position
- **Auto-saving**: All changes save automatically during editing
- **Loading indicators**: Visual feedback with spinners during operations
- **Smart notifications**: Success (green), warning (yellow), and error (red) messages
- **Smooth animations**: Subtle fade-in effects for new elements
- **Zoom constraints**: Users can zoom in but can't zoom out past original size or pan the visualization
- **Responsive feedback**: Buttons show loading states during operations

### Modern Authentication System
- **Beautiful login/register pages**: Full-screen centered design with dark theme
- **White text styling**: Proper contrast on dark backgrounds  
- **Proper logout functionality**: Fixed logout URLs and POST-based logout
- **Root page protection**: `/` redirects to dashboard if logged in, login if not
- **Session management**: Proper redirects after login/logout

### API Endpoints
- `/api/automaton/<id>/check-fa-type/` - Generic FA type checker
- Optimized logging in all existing endpoints (reduced unnecessary logging)
- `/api/automaton/<id>/add-state/` - Supports multiple state names separated by commas
- Real-time auto-saving on all edit endpoints