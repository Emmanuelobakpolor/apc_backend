#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create admin user if it doesn't exist
python manage.py shell -c "
from accounts.models import User
if not User.objects.filter(email='admin@apc.com').exists():
    u = User.objects.create_user(email='admin@apc.com', password='admin123', first_name='Admin', last_name='User')
    u.role = 'admin'
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('Admin user created.')
else:
    print('Admin user already exists.')
"
