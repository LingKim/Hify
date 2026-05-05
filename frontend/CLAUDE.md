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
- **Browser E2E**: use the Playwright CLI Skill wrapper for real browser flows before falling back to ad-hoc manual checks. Prefer `"$PWCLI" open`, `"$PWCLI" snapshot`, `"$PWCLI" click`, `"$PWCLI" fill`, and `"$PWCLI" screenshot` loops.

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

- **颜色必须走主题系统**：写样式时禁止随意直接写颜色值作为业务界面最终方案，尤其是 `#xxx`、`rgb()`、`hsl()` 这类硬编码颜色。优先使用现有 CSS 变量，如 `--brand`、`--text-body`、`--panel-bg`、`--border-default`、`--color-success`。这些变量由 `app/theme/tokens.ts` 定义，并通过 `app/theme/registry.ts` 注入。
- **新增颜色先加 token，再在样式中引用**：如果现有变量不够用，先在 `frontend/src/app/theme/tokens.ts` 里补充 light/dark 对应 token，再在 `frontend/src/app/styles.css` 或组件样式里通过 `var(--token-name)` 使用；不要在页面或组件里临时发明一组新颜色。
- **允许的例外要克制**：只有非常局部、一次性的视觉细节，且明确不需要主题联动时，才允许写少量原始颜色值；如果一个颜色会重复出现、会参与 hover/active/disabled、或者需要兼容明暗主题，就必须提升为 token。
- **优先复用语义色，不直接拼状态色**：成功、警告、错误、信息态优先使用 `--color-success`、`--color-warning`、`--color-error`、`--color-info` 及其 subtle 版本；边框、背景、hover 态优先通过 `color-mix(...)` 基于现有 token 生成，而不是重新写一套颜色。

### Path Alias

`@/` maps to `src/` (configured in `tsconfig.app.json` and `vite.config.ts`).

## Conventions

- **Strict TypeScript**: `noUnusedLocals`, `noUnusedParameters`, `noUncheckedIndexedAccess` are all enabled. All code must pass `tsc` without errors.
- **No `console.log`** in production code.
- **Immutable patterns**: use spread/object spread, never mutate state objects directly.
- **Chinese locale**: user-facing text and comments are in Chinese. The `<html lang="zh-CN">` is set.
- **Ant Design 6**: use Ant Design components as the primary UI library. Access Antd's `App` wrapper context (message, notification, modal) via `App.useApp()` hook, not static methods.
- **表格操作列默认仅显示 icon**：`ListTable` 或各页面表格中的“操作”列，按钮默认只显示 icon，不显示文字。按钮名称通过 hover 态展示，优先使用 `Tooltip`；如果产品明确要求做成 hover 才展开文字的胶囊按钮，也应保持默认静态态仅见 icon。
- **操作列交互保持统一**：同一列里的查看、编辑、删除、测试等动作，默认使用统一尺寸、统一视觉权重的 icon button；不要在某些页面直接写“编辑 / 删除”文字按钮，除非该操作极少、风险极高，且经过明确说明。
- **Shared UI first**: before creating page-level or domain-level UI, always check whether `shared/ui` already provides a suitable public component such as `FrameView`, `ListTable`, or `FormDialog`. Prefer extending or composing existing shared components over rebuilding similar structures.
- **No ad-hoc wheels**: if current shared components do not fully satisfy the requirement, first evaluate whether the gap should be filled by enhancing the shared component API. Do not create a parallel duplicate component or reimplement the same pattern locally unless there is a clear reason that shared abstraction is inappropriate.
- **Escalate when abstraction is unclear**: when a requirement only partially matches an existing shared component, do not silently invent a new wheel. Compare reuse, extension, and local-only implementation, then choose the smallest reasonable solution based on actual scope.
- **New domains**: create a subdirectory under `domain/` with the five-file structure (`types.ts`, `api.ts`, `service.ts`, `queries.ts`, `components.tsx`). Add corresponding page components under `pages/` and register routes in `app/router/AppRouter.tsx`.
- **Do not expose internal IDs as primary user inputs**: foreign keys, database IDs, enum implementation codes, and binding IDs are system identifiers. User-facing forms must present meaningful choices such as names, types, statuses, descriptions, or grouped labels, and only submit IDs behind the scenes. If the referenced module has no list/search API yet, use a disabled placeholder, empty state, or explicit deferred integration note instead of asking users to type unknown IDs.
- **Reference fields require option-source design**: before implementing a form field that references another business object, define where options come from, how they are labeled, how dependent fields reset, and what happens when the upstream module is incomplete. For cascades such as Provider -> Model, selecting the parent must clear stale child values.
- **Design reflection for Agent configuration**: the Agent form originally exposed Provider ID, Model ID, tool ID, and knowledge base ID inputs because CRUD/E2E validation was prioritized over real user workflow. This is a product-design smell: a form should model the user's decision, not the database schema. Future modules must review every form field from the user's vocabulary before implementation.
- **E2E verification data cleanup**: data created specifically for tests, E2E, or verification may be deleted after the verification completes. Prefer clearly named temporary records such as `E2E-*` or `PW-E2E-*`, then clean them up through the UI or API once assertions are complete.
- **Playwright CLI Skill for E2E**: when validating real frontend flows, prefer the Playwright CLI Skill over unstructured browser/manual checks. Always open the target page, take a fresh snapshot before using element refs, interact through refs from the latest snapshot, re-snapshot after modal/navigation changes, and capture screenshots under `.playwright-cli/` or `output/playwright/` when useful.
