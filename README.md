## Home Log

Application to make and view records of residual data such as power and water usage.


## Design and Implementation

All project docs are in the [Project Wiki](../../wiki).


## Why Use Docker?

- Consistency - development matches the production environment
- Isolation - avoid polluting the host system with dependencies & avoid errors in the application due to changes in software installed on host system
- Reproducibility & Portability - team members or others can create the exact same environment
- Quick Reset - can destroy and rebuild everything quickly
W

Downsides of using Docker:

- Some overhead, 2 - 5% performance penalty
- Extra complexity, such as exposing ports

### Explanation of docker-compose lines

In the `docker-compose.yml` file, the lines:
```yaml
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
```

* `- db_data:/var/lib/postgresql/data`

`db_data` is a named volume managed by Docker, not a host path. `/var/lib/postgresql/data` is a directory inside the Postgres container where Postgres database files are stored.

Where is the database? On the host's file system, the volume is stored in Docer's internal storage, i.e. `/var/lib/docker/volumes` on Linux. Its not in the project directory.

### Inspecting the Volume

On Linux use:
```shell
docker volume ls
docker volume inspect homelog_db_data
```

* `- ./db/init.sql:/docker-entrypoint-initdb.d/init.sql`

is a **bind mount** that instruct Docker to copy a file (db/init.sql) from the host filesystem into the PostgreSQL container.  

`/docker-entrypoint-initdb.d/init.sql` is a special location.
When you start a Postgres contain, **if** the data volume is **empty** the container will

1. create the specified database (`homelog`)
2. Look in `/docker-entrypoint-initdb.d/` for *any* .sql, .sql.gz, or .sh files.
3. Execute all the files in alphabetical order.

Hence, the script runs only if the database volume is empty.   
Useful for development, but for a production environment it is better to manage the schema and data using **migrations**, e.g. Alembic with SQLAlchemy.

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

## Supabase

What version of Postgres is Supabase using?

On [Supabase](https://supabase.com) I used the SQL Editor to query the database version.  Response was (15 Jun 2025):
```
PostgreSQL 17.4 on aarch64-unknown-linux-gnu, compiled by gcc (GCC) 13.2.0, 64-bit
```
