# Coding Standards & Patterns

**Objective:** Provide consistent guidelines so every contributor writes code that is predictable, secure, and easy to review. Judges can audit this document to confirm spec-driven development.

---

## 1. TypeScript / Next.js Frontend

### 1.1 File & Folder Organization
```
src/
├── app/
│   ├── page.tsx                   # Landing page
│   ├── marketplace/page.tsx       # Agent marketplace
│   ├── security/page.tsx          # SecurityGuard AI
│   ├── api/                       # Server actions / Lambda handlers
│   │   ├── agents/route.ts
│   │   ├── agents/[id]/route.ts
│   │   ├── requests/route.ts
│   │   └── requests/[id]/approve/route.ts
│   ├── dashboard/
│   │   ├── user/page.tsx
│   │   └── creator/page.tsx
│   └── layout.tsx
├── components/
│   ├── marketplace/
│   ├── security/
│   └── ui/
├── lib/                          # Utilities (RPC helpers, constants)
├── hooks/                        # React hooks
├── services/                     # Client-side service wrappers
├── styles/
└── types/
```

### 1.2 Naming Conventions
- React components: `PascalCase.tsx`
- Hooks: `useSomething.ts`
- Utility functions: `camelCase.ts`
- Constants: `UPPER_SNAKE_CASE`
- Test files: `ComponentName.test.tsx`
- CSS Modules (if any): `component-name.module.css`

### 1.3 Styling & UI
- Primary styling via TailwindCSS utility classes.
- Shared UI elements sourced from `shadcn/ui` with minimal overrides.
- No inline styles unless dynamic and unavoidable.
- Support dark mode using `class="dark"` toggles (stretch goal).

### 1.4 State & Data Fetching
- Global state: Zustand stores (`src/hooks/use-*.ts`).
- Remote data: React Query (`useQuery`, `useMutation`).
- Form handling: React Hook Form + Zod validation schemas.
- Error boundaries for critical tree segments (`<ErrorBoundary />`).

### 1.5 Type Safety
- `tsconfig.json` uses `"strict": true`.
- Never use `any`; prefer generics or explicit interfaces.
- Define API response/request types in `src/types/api.ts` and import where consumed.
- Re-export reused types via `src/types/index.ts`.

### 1.6 Testing
- Component tests: React Testing Library.
- Hooks: `@testing-library/react-hooks` or custom harness.
- Snapshot tests only for large, mostly-static components.

---

## 2. Next.js API Routes (Serverless Lambda)

### 2.1 Structure
```
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const limit = clamp(parseInt(searchParams.get('limit') ?? '20', 10), 1, 50)
  try {
    const agents = await agentService.list({ limit })
    return NextResponse.json({ agents })
  } catch (error) {
    log.error('listAgentsFailed', { error })
    return NextResponse.json({ error: 'Failed to fetch agents' }, { status: 500 })
  }
}
```

### 2.2 Guidelines
- Always validate inputs with Zod or custom validators before hitting the database.
- Use a shared `pg` pool (`src/lib/db.ts`) that reads credentials from environment variables (populated by Secrets Manager in production).
- Wrap each handler in `try/catch`; never leak stack traces to clients.
- Log structured errors (JSON) so CloudWatch Insights can search them.
- Return consistent error payloads `{ error: string; code?: string }`.

### 2.3 Database Access
- Parameterized queries only (`pool.query('SELECT * FROM agents WHERE id = $1', [id])`).
- Create separate repository modules (e.g., `src/services/agent-repo.ts`).
- Paginate results server-side; default limit 20, max 50.
- Add indexes for every frequent WHERE clause (documented in migrations).

### 2.4 Testing
- Unit test service layer with mocked `pg` client.
- Integration test full API route using Next.js test runner + Supertest (or Playwright for e2e).

---

## 3. Rust / Anchor Smart Contracts

### 3.1 Project Layout
```
programs/
├── agent-registry/src/lib.rs
├── marketplace-escrow/src/lib.rs
├── reputation-system/src/lib.rs
└── royalty-splitter/src/lib.rs
```

### 3.2 Patterns
- Use `#[account]` and `#[derive(Accounts)]` for strict account validation.
- Group instructions using modules per feature (e.g., `pub mod register_agent`).
- All state structs implement `space()` helper for PDA sizing.
- Emit events for every instruction that mutates state.
- Use `require!` and `require_keys_eq!` macros for checks.
- Add descriptive error codes via `#[error_code]`.

### 3.3 Testing
- Anchor integration tests live under each program's `tests/` folder.
- Use `solana-program-test` for unit tests when possible.
- Mock cross-program invocations (CPIs) to royalty splitter in tests.
- Run `anchor test --skip-local-validator` before each deploy.

### 3.4 Security
- Validate signer authority on approve/reject flows.
- Ensure escrow lamports cannot be withdrawn twice (track status enum).
- Cap maximum SOL per request (configurable).
- Pause features via admin PDA in case of incident (optional stretch).

---

## 4. Python / FastAPI (SecurityGuard AI)

### 4.1 Structure
- Follow existing layout in `security-ai/` (`core/`, `models/`, `services/`, `tests/`).
- Strict linting via `ruff` and formatting via `black`.
- Configuration handled through `pydantic.BaseSettings`.
- Async endpoints using `async def`; leverage `httpx.AsyncClient`.

### 4.2 Testing & Quality
- Maintain 90%+ coverage (already near 95%).
- Mock external APIs (Helius, Anthropic) in tests.
- Run `pytest` + `mypy` in CI before merge.

---

## 5. Git & Commit Hygiene
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
- Reference Kiro task IDs or requirement IDs in commit body when possible.
- Keep PRs under 400 lines to simplify code review (splitting when needed).

---

## 6. Tooling & Automation
- Prettier + ESLint for TypeScript (run via `npm run lint`).
- Husky pre-commit hooks to run `lint` and `test` on staged files (optional but recommended).
- Configure GitHub Actions workflow for CI (install deps, run tests, build Next.js).

---

## 7. How to Keep This Updated
- Update when architectural decisions change (e.g., switching to Server Actions).
- Mention AWS Q Developer contributions here when new patterns originate from Q (link to evidence file).
- Review weekly during hackathon standups to ensure alignment.

Consistent adherence to these standards demonstrates production readiness and maximizes our Technical Implementation score.