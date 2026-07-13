/**
 * Cross-service e2e: the money path — upload → process → report → export.
 *
 * Requires a running stack (frontend + backend + Supabase project) and the
 * env vars listed in tests/e2e/README.md. Skipped automatically when they're absent
 * so `npx playwright test` stays green in environments without credentials.
 */
import { expect, test } from "@playwright/test";

const E2E_EMAIL = process.env.E2E_EMAIL;
const E2E_PASSWORD = process.env.E2E_PASSWORD;
const E2E_AUDIO_FILE = process.env.E2E_AUDIO_FILE; // path to a short mp3 fixture

test.skip(
  !E2E_EMAIL || !E2E_PASSWORD || !E2E_AUDIO_FILE,
  "E2E_EMAIL / E2E_PASSWORD / E2E_AUDIO_FILE not configured",
);

test("upload a recording and receive an intelligence report", async ({ page }) => {
  test.setTimeout(10 * 60 * 1000); // real transcription + LLM pipeline takes minutes

  await page.goto("/login");
  await page.getByLabel("Email").fill(E2E_EMAIL!);
  await page.getByLabel("Password").fill(E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/dashboard/);

  await page.getByRole("button", { name: /upload meeting/i }).first().click();
  await page.locator('input[type="file"]').setInputFiles(E2E_AUDIO_FILE!);
  await page.getByLabel("Title").fill("E2E smoke meeting");
  await page.getByRole("button", { name: /upload & analyze/i }).click();

  // Lands on the meeting page and shows pipeline progress.
  await expect(page).toHaveURL(/meetings\//);
  await expect(page.getByText("Analyzing your meeting")).toBeVisible();

  // Waits (polling UI) until the report renders.
  await expect(page.getByText("Executive summary")).toBeVisible({ timeout: 9 * 60 * 1000 });

  // Report tabs are usable.
  await page.getByRole("tab", { name: "Action items" }).click();
  await page.getByRole("tab", { name: "Chat" }).click();
  await expect(page.getByPlaceholder("Ask about this meeting…")).toBeVisible();
});
