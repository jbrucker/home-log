## Docker Related Notes

## Forcing Use of Local Cache in Docker builds

docker-compose repeatedly downloads the same images from docker.io during builds.

To use locally stored images instead, do this.

1. Explicitly Pull the Images First
   ```bash
   # silently ignore pull failures
   docker-compose pull --ignore-pull-failures
   ```
2. Explicitly Pull Node base image for frontend:
   ```
   docker pull node:20.19.0
   ```
   Confirm the image is installed locally:
   ```
   docker images | grep node
   ```
2. Disable Pulling `docker-compose.yml` by adding `pull_policy: never`
   ```yaml
   services:
     frontend:
       image: nginx:alpine
       build:
         context: ./frontend
         pull: false
   ```
   and add `pull: false` to other services.

3. Alternatively, specify cache-only in the build command:
   ```bash
   docker-compose build --pull=false --no-cache=false
   ```
   
4. Alternatively, pin to exact local image ID:
   - In `Dockerfile`
     ```
     ARG BASE_IMAGE=nginx:alpine
     FROM ${BASE_IMAGE} AS production
     ```
   - Build command:
     ```bash
     docker-compose build --build-arg BASE_IMAGE="$(docker image inspect nginx:alpine -f '{{.Id}}')"
     ```

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

