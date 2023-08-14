
release: python3 manage.py makemigrations
release: python3 manage.py migrate
# web: daphne irmpaye.asgi:application --port $PORT --bind 0.0.0.0
web: gunicorn irmpaye.wsgi --preload --log-file - --log-level debug
worker: python manage.py runworker
