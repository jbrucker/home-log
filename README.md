## Home Log

Application to make and view records of residual data such as power and water usage.


## Design and Implementation

All project docs are in the [Project Wiki](../../wiki).


### Explanation of docker-compose lines

In the `docker-compose.yml` file, the lines:
```yaml
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
```

* `- db_data:/var/lib/postgresql/data`

`db_data` is a named volume managed by Docker, not a host path. `/var/lib/postgresql/data` is the default directory inside the Postgres container where Postgres database files are stored.

Where is the database? On the host's file system, the volume is stored in Docer's internal storage, i.e. `/var/lib/docker/volumes` on Linux. Its not in the project directory.

### Inspecting the Volume

See "Deployment" page in wiki.

## Running Locally

1. Start the "db" service:
   ```bash
   docker compose up -d db
   ```
   or start with dependencies:
   ```bash
   docker compose up -d db init-script
   ```
2. Verify it's running:
   ```bash
   docker ps
   ```
3. Interact with it:
   - `pgsql` command line
   - Database browser such as DBeaver

5. Stop it, using id prefix or container name.
   ```bash
   docker container ls
   docker stop [ a1b2c3d4 | homelog-db-1 ]
   ```
6. View log files (specify container name)
   ```bash
   docker logs homelog-db-1
   ```
7. docker-compose projects, stop & remove container:
   * Stop container and remove it: `docker compose down`
   * Also remove volumes: `docker compose down --volumes`

## Using the Database Container

The environment variables used in both Python code and docker-compose are in file `.env`.

- Start the container
  ```
  docker-compose up -d db
  ```
- Other compose commands to know:
  | Command                | Meaning                     |
  |:-----------------------|:----------------------------|
  | docker-compose ps      | List processes              |
  | docker-compose stop db | Stop the service            |
  | docker-compose down    | Remove the container (and lose data) |
  
- Connect to database via command line (will prompt for password):
  ```
  psql -h localhost -p 5432 -U postgres_user -d homelog
  ```
  Or specify password as env var:
  ```
  PGPASSWORD=mypassword psql -h localhost -p 5432 -U username -d homelog
  ```
- Alternative: run `psql` inside the container:
  ```
  docker-compose exec db psql -U username -d homelog
  ```
- List tables:
  ```
  psql>  \dt
  ```

## Debug Container Problems

1. View logs
   ```
   docker-compose logs backend
   ```
2. Inspect interactively (you should create a user in your Dockerfile or docker-compose)
   ```
   docker compuse run --rm backend sh  (or bash)
   ```
   and verify that the app code in in `/app` and `/app/app`.

## Postgres Version on Supabase

Since I plan to use Supabase for the deployed database, their version of Postgres determines what Postgres features the app can use.

On [Supabase](https://supabase.com) I used the SQL Editor to query the database version.  Response was (15 Jun 2025):
```
PostgreSQL 17.4 on aarch64-unknown-linux-gnu, compiled by gcc (GCC) 13.2.0, 64-bit
```
