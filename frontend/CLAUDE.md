# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Dev Commands

- **Install**: `pnpm install`
- **Dev server**: `pnpm dev` — runs at http://127.0.0.1:5173, proxies `/api` to FastAPI at `VITE_API_TARGET` (default `http://127.0.0.1:8000`)
- **Build**: `pnpm build` — runs `tsc` then `vite build`
- **Lint**: `pnpm lint` (oxlint), `pnpm lint:fix` (auto-fix)
- **Format**: `pnpm format` (oxfmt), `pnpm format:check` (check only)
- **Test**: `pnpm test` (vitest single run), `pnpm test:watch` (watch mode)
- **Run single test**: `pnpm vitest run src/test/request.test.ts`

## Architecture

### Tech Stack

React 18 + TypeScript (strict) + Vite 8 + Ant Design 6 + TanStack React Query 5 + Zustand 5 + React Router 6.

### Directory Convention: `app / domain / shared / pages`

```
src/
├── app/           Application shell: layout, router, providers, theme, global styles
├── domain/        Business domains (one subdir per domain)
├── shared/        Cross-domain infrastructure: API client, query client, stores, types, config
├── pages/         Route-level page components (thin, compose domain components)
└── test/          Test files and setup
```

- **`app/`** owns the application skeleton. Layouts, routing, providers (React Query + Ant Design ConfigProvider + theme), and global CSS live here. Not for business logic.
- **`domain/`** holds business features. Each domain subdirectory is self-contained with a fixed internal structure (see below).
- **`shared/`** is pure infrastructure consumed by domains and app — no business knowledge.
- **`pages/`** are thin route targets that compose domain components and shared UI. Pages never contain business logic or data fetching directly.

### Domain Internal Structure

Every domain follows the same file convention:

| File | Responsibility |
|---|---|
| `types.ts` | TypeScript interfaces for the domain |
| `api.ts` | Request descriptor strings (`"GET /path"`) exported as a const object |
| `service.ts` | Async functions that call `request()` from shared API layer, transform responses |
| `queries.ts` | React Query hooks, query key factory, query/mutation option factories |
| `components.tsx` | UI components that consume React Query hooks and render domain data |

Import chain is one-directional: `components → queries → service → api → shared`.

### Request Layer

All HTTP calls go through `shared/api/client.ts`'s `request<T>()` function. It uses a **declarative descriptor pattern** — callers pass `{ request: "GET /path", pathParams?, query?, body? }` and the function handles URL construction, headers, and error parsing.

- API base path is `/api/v1` (configured in `shared/config/env.ts`).
- Backend responses follow `ResultEnvelope<T>`: `{ code: number, message: string, data: T }`.
- Errors are parsed into `AppRequestError` / `AppBusinessError` / `AppResponseFormatError` class hierarchy.

### State Management

- **Server state**: TanStack React Query. Domains define query key factories and `queryOptions()` in their `queries.ts`.
- **Client UI state**: Zustand store at `shared/stores/app.ts`. Only persists theme and navigation preferences to localStorage.

### Theming

Theme registry in `app/theme/registry.ts` maps `"light"` | `"dark"` to Ant Design `ThemeConfig` plus CSS custom properties. `AppProviders` syncs `document.documentElement` attributes and CSS variables on theme change.

### Path Alias

`@/` maps to `src/` (configured in `tsconfig.app.json` and `vite.config.ts`).

## Conventions

- **Strict TypeScript**: `noUnusedLocals`, `noUnusedParameters`, `noUncheckedIndexedAccess` are all enabled. All code must pass `tsc` without errors.
- **No `console.log`** in production code.
- **Immutable patterns**: use spread/object spread, never mutate state objects directly.
- **Chinese locale**: user-facing text and comments are in Chinese. The `<html lang="zh-CN">` is set.
- **Ant Design 6**: use Ant Design components as the primary UI library. Access Antd's `App` wrapper context (message, notification, modal) via `App.useApp()` hook, not static methods.
- **New domains**: create a subdirectory under `domain/` with the five-file structure (`types.ts`, `api.ts`, `service.ts`, `queries.ts`, `components.tsx`). Add corresponding page components under `pages/` and register routes in `app/router/AppRouter.tsx`.
