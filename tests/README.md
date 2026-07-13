# Cross-service tests

Unit and integration tests live with their packages (`backend/tests/`, frontend `*.test.ts`) —
see `docs/02-folder-structure.md` for the rationale. This directory holds only what spans
both deployables: Playwright end-to-end flows against a running stack.

## Running the e2e suite

```bash
cd tests/e2e
npm init -y && npm i -D @playwright/test && npx playwright install chromium

E2E_BASE_URL=http://localhost:5173 \
E2E_EMAIL=you@example.com \
E2E_PASSWORD=your-password \
E2E_AUDIO_FILE=/path/to/short-meeting.mp3 \
npx playwright test
```

The spec self-skips when credentials aren't configured, so it never breaks CI that
lacks a live environment.
