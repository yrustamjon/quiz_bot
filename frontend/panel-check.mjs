const artifactDir = process.env.QUIZ_ARTIFACT_DIR || "/workspace/artifacts";
const baseURL = process.env.QUIZ_BASE_URL || "http://127.0.0.1:5173";
import { chromium } from "@playwright/test";
import fs from "node:fs";
const identity = JSON.parse(
  fs.readFileSync(`${artifactDir}/ui-identity.json`, "utf8"),
);
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  headless: true,
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.on("pageerror", (err) => console.log("PAGE ERROR", err.message));
await page.goto(`${baseURL}/login`);
await page.getByLabel("Login yoki email").fill(identity.username);
await page.locator("input[name=password]").fill(identity.password);
await page.getByRole("button", { name: "Hisobga kirish", exact: true }).click();
await page
  .getByRole("heading", { name: "Xush kelibsiz, Interfeys" })
  .waitFor({ timeout: 15000 });
await page.locator(".stat-grid .stat").first().waitFor();
await page.getByRole("img", { name: "Kunlik urinishlar grafigi" }).waitFor();
await page
  .getByText("Hisobga kirildi.", { exact: true })
  .waitFor({ state: "hidden" });
await page
  .getByRole("button", { name: "Menyuni yig‘ish", exact: true })
  .click();
await page
  .getByRole("button", { name: "Menyuni kengaytirish", exact: true })
  .click();
await page.screenshot({
  path: `${artifactDir}/dashboard-light.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "Qorong‘i mavzu" }).click();
await page.screenshot({
  path: `${artifactDir}/dashboard-dark.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "Excel importi", exact: true }).click();
await page
  .getByRole("dialog", { name: "Excel importi", exact: true })
  .waitFor();
await page.keyboard.press("Escape");
await page.getByRole("link", { name: "Test yaratish", exact: true }).click();
await page.getByRole("dialog").waitFor();
await page.keyboard.press("Escape");
await page.goto(baseURL + "/");
await page
  .getByRole("heading", { name: "Umumiy ko‘rsatkichlar", exact: true })
  .waitFor();
await page.locator(".status-legend a[href='/quizzes?status=draft']").click();
if (
  (await page.getByLabel("Test holati", { exact: true }).inputValue()) !==
  "draft"
)
  throw new Error("Dashboard status link did not apply quiz filter");
await page.goto(baseURL + "/");
await page.getByText("Sana oralig‘i", { exact: true }).click();
const dateRequest = page.waitForResponse(
  (response) =>
    response.url().includes("dashboard/summary/") &&
    response.url().includes("start=2020-01-01") &&
    response.status() === 200,
);
await page.getByLabel("Sanadan", { exact: true }).fill("2020-01-01");
await dateRequest;
await page.getByRole("button", { name: "Davrni tiklash", exact: true }).click();
if (await page.getByLabel("Sanadan", { exact: true }).inputValue())
  throw new Error("Dashboard date range did not reset");
await page.goto(`${baseURL}/quizzes`);
await page.getByRole("button", { name: "Yangi test", exact: true }).click();
await page.getByLabel("Test nomi").fill("Brauzer tekshiruvi");
await page.getByLabel("Fan", { exact: true }).fill("Matematika");
await page.getByRole("button", { name: "Qoralamani yaratish" }).click();
await page
  .getByRole("heading", { name: "Brauzer tekshiruvi", exact: true })
  .waitFor();
await page.goto(`${baseURL}/quizzes`);
await page.getByRole("link", { name: "Brauzer tekshiruvi" }).waitFor();
await page.reload();
await page.getByRole("link", { name: "Brauzer tekshiruvi" }).waitFor();
await page.screenshot({
  path: `${artifactDir}/quizzes-dark.png`,
  fullPage: true,
});
for (const path of ["/", "/quizzes", "/questions", "/students", "/profile"]) {
  await page.goto(`${baseURL}` + path);
  await page.waitForTimeout(400);
  for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    if (
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      )
    )
      throw new Error("Overflow " + path + " " + width);
  }
}
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(`${baseURL}/`);
await page.getByRole("heading", { name: "Xush kelibsiz, Interfeys" }).waitFor();
await page.locator(".stat-grid .stat").first().waitFor();
await page.getByRole("img", { name: "Kunlik urinishlar grafigi" }).waitFor();
await page.screenshot({
  path: `${artifactDir}/dashboard-mobile-dark.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "Menyuni ochish" }).click();
await page.getByRole("dialog").waitFor();
await page.keyboard.press("Escape");
await page.getByRole("button", { name: "Hisobdan chiqish" }).click();
await page
  .getByRole("heading", { name: "Xush kelibsiz", exact: true })
  .waitFor();
console.log(
  "PASS: real login, API-backed draft create and persistence, dashboard, directories, profile, 7 viewports, mobile dialog Escape, logout.",
);
await browser.close();
