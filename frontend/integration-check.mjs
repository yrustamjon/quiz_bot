const artifactDir = process.env.QUIZ_ARTIFACT_DIR || "/workspace/artifacts";
const baseURL = process.env.QUIZ_BASE_URL || "http://127.0.0.1:5173";
import { chromium } from "@playwright/test";
import fs from "node:fs";
const a = JSON.parse(fs.readFileSync(`${artifactDir}/ui-admin.json`, "utf8"));
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  headless: true,
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
async function login(username, password) {
  await page.goto(`${baseURL}/login`);
  await page.getByLabel("Login yoki email").fill(username);
  await page.locator("input[name=password]").fill(password);
  await page
    .getByRole("button", { name: "Hisobga kirish", exact: true })
    .click();
}
await login(a.username, a.password);
await page.getByRole("heading", { name: "Xush kelibsiz, Admin" }).waitFor();
await page.goto(`${baseURL}/teachers`);
await page
  .getByRole("button", { name: "O‘qituvchi yaratish", exact: true })
  .click();
const username = "ui_new_" + Date.now();
await page.getByLabel("Ism va familiya").fill("Yangi Ustoz");
await page.getByLabel("Login", { exact: true }).fill(username);
await page
  .getByLabel("Email", { exact: true })
  .fill(username + "@example.test");
await page.getByLabel("Fan", { exact: true }).fill("Matematika");
await page.getByRole("button", { name: "Yaratish", exact: true }).click();
await page.getByRole("dialog", { name: "Vaqtinchalik parol" }).waitFor();
const temp = await page.locator("output").innerText();
await page
  .getByRole("dialog")
  .getByRole("button", { name: "Yopish", exact: true })
  .first()
  .click();
await page.screenshot({
  path: `${artifactDir}/teachers-light.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "Hisobdan chiqish" }).click();
await page
  .getByRole("heading", { name: "Xush kelibsiz", exact: true })
  .waitFor();
await login(username, temp);
await page
  .getByRole("heading", { name: "Parolni almashtirish", exact: true })
  .waitFor();
await page.locator("input[name=password]").fill(temp);
await page
  .locator("input[name=new_password]")
  .fill("Secure-replacement-UI-739@");
await page
  .locator("input[name=confirm_password]")
  .fill("Secure-replacement-UI-739@");
await page
  .getByRole("button", { name: "Parolni saqlash", exact: true })
  .click();
await page.getByRole("heading", { name: "Xush kelibsiz, Yangi" }).waitFor();
await page.goto(`${baseURL}/quizzes`);
await page.getByRole("button", { name: "Yangi test", exact: true }).click();
await page.getByLabel("Test nomi").fill("Excel integratsiyasi");
await page.getByLabel("Fan", { exact: true }).fill("Matematika");
await page.getByLabel("Savollar soni").fill("1");
await page
  .getByRole("button", { name: "Qoralamani yaratish", exact: true })
  .click();
await page.getByRole("heading", { name: "Excel integratsiyasi",exact:true }).waitFor();
await page.getByRole("button", { name: "2. Savollar" }).click();
await page.getByRole("button", { name: "Excel importi", exact: true }).click();
await page
  .getByLabel("Import fayli")
  .setInputFiles(`${artifactDir}/template.xlsx`);
await page.getByRole("heading", { name: "1 ta savol" }).waitFor();
await page.screenshot({
  path: `${artifactDir}/import-preview-light.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "Importni tasdiqlash" }).click();
await page.getByText("1 ta savol import qilindi.").waitFor();
await page.keyboard.press("Escape");
await page.getByRole("button", { name: "3. Nashr qilish" }).click();
await page.getByRole("button", { name: "Nashr qilish", exact: true }).click();
await page.getByRole("button", { name: "Testni yopish" }).waitFor();
await page.screenshot({
  path: `${artifactDir}/quiz-published-light.png`,
  fullPage: true,
});
for (const route of [
  "results",
  "rankings",
  "reports",
  "profile",
  "questions",
  "students",
]) {
  await page.goto(`${baseURL}/` + route);
  await page.locator("h1").waitFor();
  for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    if (
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
      )
    )
      throw new Error("overflow " + route + " " + width);
  }
  await page.screenshot({
    path: `${artifactDir}/` + route + "-light.png",
    fullPage: true,
  });
}
await page.goto(`${baseURL}/reports`);
const download = page.waitForEvent("download");
await page.getByRole("button", { name: "Excel eksporti" }).click();
await (await download).saveAs(`${artifactDir}/export.xlsx`);
console.log(
  "PASS: Super Admin teacher creation, temporary login, forced password change, draft, real XLSX preview/confirm, publish, report download, all current routes 7 widths. Browser errors:",
  errors.length,
);
if (errors.length) throw new Error(errors.join(";"));
await browser.close();
