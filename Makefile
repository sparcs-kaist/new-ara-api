UV_RUN := uv run --locked

init:
	mysql -u root -e 'CREATE DATABASE new_ara CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;'
	$(UV_RUN) python manage.py migrate

superuser:
	$(UV_RUN) python manage.py createsuperuser

flush:
	mysql -u root -e 'DROP DATABASE new_ara;'

flush_test:
	mysql -u root -e 'DROP DATABASE test_new_ara;'

reset: flush init

run:
	$(UV_RUN) python manage.py runserver 0.0.0.0:9000

shell:
	$(UV_RUN) python manage.py shell -i ipython

migrate:
	$(UV_RUN) python manage.py makemigrations --merge
	$(UV_RUN) python manage.py makemigrations
	$(UV_RUN) python manage.py migrate

test:
	$(UV_RUN) --group test pytest tests/

test_coverage:
	$(UV_RUN) --group test pytest --cov-report html --cov=. --cov-config=.coveragerc tests/

test_coverage_missing:
	$(UV_RUN) --group test pytest --cov-report term-missing --cov=. tests/

env:  # use for local & might not be ~/.bashrc
	git clone git@github.com:hyperupcall/autoenv.git ~/.autoenv
	echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
	source ~/.bashrc

celery_worker_run:
	$(UV_RUN) celery -A ara worker -l info

clear_celery:
	pkill -9 -f celery || true
	redis-cli flushall

celery_beat_run:
	$(UV_RUN) celery -A ara beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

kill_celery_processes:
	ps auxww | grep 'celery' | awk '{print $$2}' | xargs kill -9

i18n_generate:
	mkdir -p ara/locale
	$(UV_RUN) python manage.py makemessages -l en -i env
	$(UV_RUN) python manage.py makemessages -l ko -i env

i18n_compile:
	$(UV_RUN) python manage.py compilemessages -l en -l ko

elasticsearch_index:
	$(UV_RUN) python manage.py search_index --rebuild

show_sql:
	$(UV_RUN) python manage.py shell_plus --print-sql

schema:
	$(UV_RUN) python manage.py spectacular --color --file schema.yml

local_env:
	docker compose -f docker-compose.local.yml up -d

local_env_down:
	docker compose -f docker-compose.local.yml down

# Run the same isolated integration environment as CI.
test_docker:
	docker compose -p newara-test -f docker-compose.test.yml build api
	docker compose -p newara-test -f docker-compose.test.yml run --rm api test

test_docker_down:
	docker compose -p newara-test -f docker-compose.test.yml down

sync:
	uv sync --locked

lock_check:
	uv lock --check
