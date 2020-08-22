init:
	mysql -u root -e 'CREATE DATABASE new_ara CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;'
	python manage.py migrate

superuser:
	python manage.py createsuperuser

flush:
	mysql -u root -e 'DROP DATABASE new_ara;'

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

env:  # use for local & might not be ~/.bashrc
	git clone git://github.com/inishchith/autoenv.git ~/.autoenv
	echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
	source ~/.bashrc

celery_worker_run:
	celery -A ara worker -l info

clear_celery:
	pkill -9 -f celery || true
	redis-cli flushall

celery_beat_run:
	celery -A ara beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

kill_celery_processes:
	ps auxww | grep 'celery' | awk '{print $$2}' | xargs kill -9
