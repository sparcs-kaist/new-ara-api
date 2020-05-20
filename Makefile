init:
	python manage.py migrate

superuser:
	python manage.py createsuperuser

flush:
	mysql -u root -e 'DROP DATABASE new_ara; CREATE DATABASE new_ara CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;'

reset: flush init

run:
	python manage.py runserver 0.0.0.0:9000

shell:
	python manage.py shell -i bpython

migrate:
	python manage.py makemigrations --merge
	python manage.py makemigrations
	python manage.py migrate

test:
	pytest tests/

test_coverage:
	pytest --cov=. tests/

test_coverage_missing:
	pytest --cov-report term-missing --cov=. tests/
