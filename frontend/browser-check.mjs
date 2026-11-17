const artifactDir = process.env.QUIZ_ARTIFACT_DIR || "/workspace/artifacts";
const baseURL = process.env.QUIZ_BASE_URL || "http://127.0.0.1:5173";
import { chromium } from "@playwright/test";
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  headless: true,
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.goto(`${baseURL}/login`);
await page
  .getByRole("heading", { name: "Xush kelibsiz", exact: true })
  .waitFor();
await page.screenshot({
  path: `${artifactDir}/login-light.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "Qorong‘i mavzu" }).click();
await page.screenshot({
  path: `${artifactDir}/login-dark.png`,
  fullPage: true,
});
for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
  await page.setViewportSize({ width, height: 900 });
  if (
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
  )
    throw new Error("Overflow " + width);
}
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({
  path: `${artifactDir}/login-mobile-dark.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "Hisobga kirish" }).click();
await page.getByText("Loginni kiriting.", { exact: true }).waitFor();
console.log(
  "Login real browser: light/dark, 7 viewport widths, required validation PASS",
);
await browser.close();
