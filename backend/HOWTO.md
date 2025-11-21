## From the host's command line, connect to database running in a container

This assumes that Docker exposes port 5432 to outside, and database is named "homelog".
```
psql -h localhost -p 5432 -U dev -d homelog
```

### Import data from an SQL File into psql session

Suppose the file is `users.sql`.
```
psql> \i users.sql
```
or with full path
```
psql> \i /home/jim/app/homelog/blah/data/users.sql
```
