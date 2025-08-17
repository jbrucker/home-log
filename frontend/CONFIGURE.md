Client interface to application using Vue.


## Development

There are 2 slightly different ways to initialize a Vue project.

1. [Initialize with Official Vue Scaffolding](#initialize-with-official-value-scaffolding)
2. [Initialize as a Vite Project](#initialize-as-a-vite-project)

In both cases, I configured the project to use Typescript and Vite.

After some comparison, I chose the official Vue Scaffolding.

### Initialize with Official Vue Scaffolding

- Uses Vue official template with Vue CLI tools
- Creates a Vue-focused project
- Configuration prompts for
  - TypeScript
  - Vite or Webpack as build tool
  - Vue Router
  - Pinia
  - ESLint or Prettier
  - Testing setup
- This choice is recommended by **Deepseek**

1. Create the app - from top-level directory
   ```
   npm create vue@latest frontend
   ```
   when prompted, choose:
   - [x] Add Typescript? **yes**
   - [ ] Add JSX Support? no
   - [x] Add Vue Router for SPA? **yes**
   - [x] Add Pinia for state management? **yes**
   - [ ] Add Vitest for Unit Testing? no (optional)
   - [x] Add Eslint for code quality? **yes** (recommended)
   Skip all example code and start with an empty Vue project?
   - Choose **no** (do not skip)
   - Reasons: 
     - provides working router/pinea demo you can modify
     - Preconfigured `views/` folder for router components
     - Pinea store example
     - Typescript-ready components
   - Files to delete later:
     ```
     src/views/AboutView.vue
     src/components/HelloWord.vue
     src/assets/base.css (optional if you that css)
     ```
   - Files to modify:
     - src/views/HomeView.vue rename to SourcesView.vue and modify
     - src/router/index.ts replace with actual routes
     - src/stores/counter.ts replace with auth.ts
    

2. Install dependencies
   ```
   cd  frontend
   npm install
   ```

3. Add axios and (?) bootstrap for styling
   ```
   npm install axios
   # bootstrap is optional. 
   # Alternatives: Framework7, Tailwind (smaller but more complex)
   npm install bootstrap  
   npm install --save-dev @types/node
   ```

4. Configure Vite in `vite.config.ts`
   - Add aliases (`@`)
   - Define a "server" for backend, using `http://localhost:8000`

5. Setup Typescript support in `tsconfig.json`
   - add path for `@/*`, i.e. `"@/*": ["src/*"] in `"paths"`.
   - File recommended by Deepseek is totally different from the default createed by `@vue/latest`, which uses "includes".   Deepseek:
   ```json
   "compilerOptions": {
       "target": "ESNext",
       "module": "ESNext",
       "baseUrl": ".",
       "paths": {
         "@/*": ["src/*"]
       },
       "types": ["vite/client"],
       "strict": true,
       "skipLibCheck": true
     },
     "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.vue"]
   }
   ```

6. Initialize Vue Router (src/router/index.ts)
   - add routes for / -> HomeView, /login -> LoginView,  /sources -> SourcesView, `/sources/:id/readings` -> ReadingsView

7. Configure Axios in `src/api.ts`.  This is used by Pinia.

8. Configure Pinia for state management in `src/stores/auth.ts`.

9. Add global styles in `src/main.ts` (import Bootstramp, but I skipped this).

---

### Initialize as a Vite Project

- Creates a generic Vite project with templates for multiple frameworks
- Template options:
  - vanilla, vue, vue-ts, react, svelte, others
- Makes vite the default build tool

Benefits & drawbacks: 

- manually install vue router and pinia
- build tool: vite
- minimal and fast
- light weight

> **Note** I use `frontend.vite` as directory for this instance.

1. Create the app - from top-level directory
   ```
   npm create vite@latest frontend -- --template vue-ts
   ```

2. Install dependencies
   ```
   cd  frontend
   npm install
   ```

3. Add Vue Router, Typescript-compatible
   ```
   npm install vue-router@4
   ```

4. Configure Vue Router in `src/router/index.ts` (new file).
   ```typescript
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import HomePage from '@/pages/HomePage.vue';
import LoginPage from '@/pages/LoginPage.vue';
import SourceDetailPage from '@/pages/SourceDetailPage.vue';

const routes: RouteRecordRaw[] = [
  { path: '/', component: HomePage },
  { path: '/login', component: LoginPage },
  { path: '/sources/:id', component: SourceDetailPage, props: true },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
   ```

5. Register the router in `src/main.ts`.
   ```typescript
import { createApp } from 'vue';
import './style.css';
import App from './App.vue';
import router from './router';

const app = createApp(App);
app.use(router);
app.mount('#app');
   ```

6. Create page components
   ```
   mkdir src/pages
   touch src/pages/{HomePage.vue,LoginPage.vue,SourceDetailPage.vue}
   ```
   add minimal content to each page
   ```typescript
   <!-- src/pages/HomePage.vue -->
   <template><div>Home Page</div></template>
   <script lang="ts" setup></script>
```

7. Fix Problems: `path` module and `__dirname` not recognized in `vite.config.ts`:
   ```
   npm install --save-dev @types/node
   ```
   and add to `tsconfig.json`:
   ```
      "compilerOptions": {
         ...,
         "types": ["node"],
   ```

8. Fix **another** problem, `@` is not recognized as prefix in `router/index.ts`:
   ```
   npm install --save-dev @vue/runtime-core
   ```

9. Run: `npm run dev --verbose`

Next Steps:

1. Install support for other components:
   ```
   npm install pinia
   npm install axios
   ```
   and configure aliases in `vite.config.ts`.
2. Add CSS:
   ```
   npm install -D tailwindcss
   ```

