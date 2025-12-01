## Verify that a container name can be resolved to an IP address inside a container

What is the IP address for "backend"?
```
compose exec -it <container_name> nslookup backend
```

## View Container Managed Networks and Addresses

```bash
docker network ls
# Get all hosts on a given network
docker network inspect homelog_app-net
```

## View and Manage Docker volumes

```bash
docker volume ls
docker volume inspect appname_db_data
```

Named volumes are created implicitly when:
- defined using `compose -v mydata:/path`
- defined in "volumes" in docker-compose.yml

Explicitly create:
```bash
docker volume create mydata
```
If your app is managed using docker-compose, be sure to use compose's naming rule
that prefixes the volume name with `projectname_`.

## Live Resource Usage Stats for a Running Project

```
compose stats
```

## Connect to database running in a container from host's CLI

This assumes that Docker exposes port 5432 to outside, and database is named "homelog".
```bash
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

### Reset the Grafana Admin Password

Grafana on native host, perform as the grafana user:
```bash
sudo grafana grafana-cli admin reset-admin-password <newpassword>
```

Grafana running in a Docker container named "grafana":
```bash
docker exec -it grafana grafana-cli admin reset-admin-password <newpassword>
```

Use an environment variable.  This works only on **first startup** of the container.
Once an admin password has been set, this has no effect.
```yml
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=fatchance
```
```bash
docker compose up -d
```

Set hashed password directly in grafana's database:
```python
python3 - <<EOF
import bcrypt
print(bcrypt.hashpw(b"newpassword123", bcrypt.gensalt()).decode())
EOF
```

Set password in local grafana database, assuming SQLite3 database:
```bash
sqlite3 /var/lib/grafana/grafana.db \
"UPDATE user SET password='bcrypt_hashed_password' WHERE login='admin';"
```
