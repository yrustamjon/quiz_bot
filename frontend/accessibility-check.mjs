const artifactDir = process.env.QUIZ_ARTIFACT_DIR || "/workspace/artifacts";
const baseURL = process.env.QUIZ_BASE_URL || "http://127.0.0.1:5173";
import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
const identity = JSON.parse(
  fs.readFileSync(`${artifactDir}/ui-admin.json`, "utf8"),
);
const reports = [];
await page.goto(`${baseURL}/login`);
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
  "/groups",
  "/settings",
  "/quizzes",
  "/questions",
  "/students",
  "/results",
  "/rankings",
  "/reports",
  "/profile",
]) {
  await page.goto(`${baseURL}` + route);
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
const records = JSON.parse(
  fs.readFileSync(`${artifactDir}/fixture-records.json`, "utf8"),
);
async function auditState(state) {
  for (const theme of ["light", "dark"]) {
    await page.evaluate(
      (t) => document.documentElement.classList.toggle("dark", t === "dark"),
      theme,
    );
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    reports.push({ route: state, theme, violations: result.violations });
  }
}
await page.goto(`${baseURL}/students/${records.student}`);
await page
  .getByRole("heading", { name: "Sinov O‘quvchi", exact: true })
  .waitFor();
await auditState("student-detail");
await page.goto(`${baseURL}/quizzes/${records.draft}`);
await page
  .getByRole("heading", { name: "Wizard brauzer sinovi", exact: true })
  .waitFor();
for (const [step, label] of [
  [1, "Asosiy sozlamalar"],
  [2, "Savollar"],
  [3, "Nashr qilish"],
]) {
  await page
    .getByRole("button", { name: `${step}. ${label}`, exact: true })
    .click();
  await auditState("wizard-" + step);
}
await page.getByRole("button", { name: "2. Savollar", exact: true }).click();
await page.getByRole("button", { name: "Excel importi", exact: true }).click();
await page
  .getByRole("dialog", { name: "Excel orqali savol importi" })
  .waitFor();
await auditState("import-dialog");
await page.keyboard.press("Escape");
for (const [route, button, dialog] of [
  ["questions", "Yangi savol", "Yangi savol"],
  ["groups", "Guruh yaratish", "Yangi guruh"],
  ["teachers", "O‘qituvchi yaratish", "O‘qituvchi yaratish"],
]) {
  await page.goto(`${baseURL}/${route}`);
  await page.getByRole("button", { name: button, exact: true }).click();
  await page.getByRole("dialog", { name: dialog, exact: true }).waitFor();
  await auditState(route + "-dialog");
  await page.keyboard.press("Escape");
}
await page.goto(`${baseURL}/change-password`);
await page.locator("h1").waitFor();
await auditState("password-change");
fs.writeFileSync(
  `${artifactDir}/accessibility.json`,
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
