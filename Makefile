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

env:  # use for local & might not be ~/.bashrc
	git clone git://github.com/inishchith/autoenv.git ~/.autoenv
	echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
	source ~/.bashrc
