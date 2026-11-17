import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
const browser = await chromium.launch({
  executablePath: "/usr/bin/chromium",
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
const identity = JSON.parse(
  fs.readFileSync("/workspace/artifacts/ui-admin.json", "utf8"),
);
const reports = [];
await page.goto("http://127.0.0.1:5173/login");
await page
  .getByRole("heading", { name: "Xush kelibsiz", exact: true })
  .waitFor();
for (const theme of ["light", "dark"]) {
  await page.evaluate(
    (t) => document.documentElement.classList.toggle("dark", t === "dark"),
    theme,
  );
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  reports.push({ route: "login", theme, violations: result.violations });
}
await page.getByLabel("Login yoki email").fill(identity.username);
await page.locator("input[name=password]").fill(identity.password);
await page.getByRole("button", { name: "Hisobga kirish", exact: true }).click();
await page.getByRole("heading", { name: "Xush kelibsiz, Admin" }).waitFor();
for (const route of [
  "/",
  "/teachers",
  "/quizzes",
  "/questions",
  "/students",
  "/results",
  "/rankings",
  "/reports",
  "/profile",
]) {
  await page.goto("http://127.0.0.1:5173" + route);
  await page.locator("h1").waitFor();
  await page.waitForTimeout(300);
  for (const theme of ["light", "dark"]) {
    await page.evaluate(
      (t) => document.documentElement.classList.toggle("dark", t === "dark"),
      theme,
    );
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    reports.push({ route, theme, violations: result.violations });
  }
}
fs.writeFileSync(
  "/workspace/artifacts/accessibility.json",
  JSON.stringify(reports, null, 2),
);
for (const r of reports)
  if (r.violations.length)
    console.log(
      r.route,
      r.theme,
      r.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.map((n) => n.target),
      })),
    );
console.log(
  "Audited",
  reports.length,
  "route/theme combinations; violations:",
  reports.reduce((a, r) => a + r.violations.length, 0),
);
await browser.close();
if (reports.some((r) => r.violations.length)) process.exitCode = 1;
