SPARCS NewAra API
==================


Install requirements
--------------------

```sh
$ pip install -r requirements.txt
```


Create/Update database tables
-----------------------------

```sh
$ python manage.py migrate
```


Initiate test environment
-------------------------

```sh
$ python manage.py init_test
```


Initiate real environment
-------------------------

```sh
$ python manage.py init_real
```


Run Celery workers
------------------

```sh
$ celery -A ara worker -l info
```


Run test cases
--------------

```sh
$ python manage.py test
```
