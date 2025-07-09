#!/usr/bin/env python
"""
Setup script to initialize the database with migrations and sample data
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automata.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    """Run database setup"""
    print("🚀 Setting up Finite Automaton Manager...")
    
    # Make migrations
    print("📝 Creating migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # Apply migrations
    print("🔄 Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser (optional)
    print("👤 Creating admin user...")
    try:
        execute_from_command_line(['manage.py', 'createsuperuser', '--noinput', '--username=admin1234', '--email=admin@example.com'])
    except:
        print("Admin user already exists or creation failed")
    
    # Populate exercises
    print("📚 Populating sample exercises...")
    execute_from_command_line(['manage.py', 'populate_exercises'])
    
    print("✅ Setup complete!")
    print("\n🎯 Next steps:")
    print("1. Run: python manage.py runserver")
    print("2. Visit: http://127.0.0.1:8000/automata/")
    print("3. Login with admin/admin123 or register a new account")

if __name__ == '__main__':
    main()
