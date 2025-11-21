## Homelog Front-End Web Application using Vue.js

A web client for the Homelog application.
The code is based on the official Vue template for Vue 3 apps with Vite.

To run:

1. In the parent directory, run database, back-end, and front-end using:
   ```
   docker compose up -d
   ```
   Verify: use `ps` to view running docker containers. There should be 3.
   ```
   docker compose ps
   ```

For development, 
you can start front-end separately while running backend and database via Docker-compose:

1. Start backend and database
   ```
   docker compose up -d db backend
   ```
   or, run database in a container and run backend natively on your machine:
   ```
   cd {homelog-base-dir}
   docker compose up -d db
   cd backend
   # Activate the virtual env (see backend README.md for how to create it)
   . env/bin/activate
   # Script to start the server
   # This should display a message that server is listening on port 8000
   # and no error messages.
   ./runserver.sh
   ```

2. Then start dev server for front-end
   ```
   cd frontend
   npm run dev
   ```
   Expected output:
   ```
   VITE v7.x.x  ready in 300 ms

   ➜  Local:   http://localhost:5173/
   ➜  Network: use --host to expose
   ➜  Vue DevTools: Open http://localhost:5173/__devtools__/ as separate window
   ➜  press h to show help
   ```

3. Navigate to <http://localhost:5173>.


## Paths Provided by Front-end

| Path        | Use            |
|:------------|:---------------|
| /           | Show Login page or home page if logged in. |
| /home       | Show available data sources. |
| /home/source | Show a particular data source. |

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

See [frontend/CONFIGURE.md](./frontend/CONFIGURE.md)


### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
