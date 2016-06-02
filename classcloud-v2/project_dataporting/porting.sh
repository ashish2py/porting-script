#!/bin/sh
echo 'dropping database'
psql -U postgres -c "drop database new_ell_db3"

echo 'creating database'
psql -U postgres -c "create database new_ell_db3"

#find all the migrations
echo 'looking from dumped database'
# psql -U postgres new_ell_db3 < /Users/ashishtiwari/Documents/zaya-workspace/database/classcloud/new_ell_db_23-05-2016_updated.sql

#find all the migrations
echo 'fetching all the migration files'
find */migrations/*0*.py

#drop all the migrations
echo 'droping all the migration files'
rm -rf  `find */migrations/*0*.py`

echo '\n\n\n #### dropping done.'
#drop all the migrations
echo '\n\nrunning migration'
python manage.py makemigrations --settings=classcloud.settings.local
python manage.py migrate --settings=classcloud.settings.local

echo '\n\n\n #### migrations done.'
python manage.py createsuperuser --settings=classcloud.settings.local
python manage.py runserver --settings=classcloud.settings.local
