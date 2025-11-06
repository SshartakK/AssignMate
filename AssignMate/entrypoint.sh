#!/bin/bash

while ! python manage.py check --database default; do
  sleep 2
done

python manage.py migrate

python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF

python manage.py runserver 0.0.0.0:${ASSIGNMATE_EXTERNAL_PORT}