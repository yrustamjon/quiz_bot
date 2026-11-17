import { chromium } from "@playwright/test";
import fs from "node:fs";
const artifactDir = process.env.QUIZ_ARTIFACT_DIR || "/workspace/artifacts";
const baseURL = process.env.QUIZ_BASE_URL || "http://127.0.0.1:5173";
const identity = JSON.parse(
  fs.readFileSync(`${artifactDir}/ui-admin.json`, "utf8"),
);
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
await page.goto(baseURL + "/login");
await page.getByLabel("Login yoki email").fill(identity.username);
await page.locator("input[name=password]").fill(identity.password);
await page.getByRole("button", { name: "Hisobga kirish", exact: true }).click();
await page.getByRole("heading", { name: "Xush kelibsiz, Admin" }).waitFor();
await page.getByRole("button", { name: "Hisob menyusi" }).click();
await page.getByRole("menuitem", { name: "Parolni almashtirish" }).waitFor();
await page.keyboard.press("Escape");
await page.goto(baseURL + "/quizzes");
await page
  .getByRole("button", { name: "Yopiq brauzer sinovi: amallar", exact: true })
  .click();
await page.getByRole("menuitem", { name: "Kirish kodi", exact: true }).click();
const codeDialog = page.getByRole("dialog", { name: "Testga kirish kodi" });
await codeDialog.waitFor();
const previousCode = await codeDialog.locator("output").textContent();
await codeDialog.getByRole("button", { name: "Yangi kod yaratish" }).click();
await page.waitForFunction(
  (old) => document.querySelector("[role=dialog] output")?.textContent !== old,
  previousCode,
);
await page.keyboard.press("Escape");
await page
  .getByRole("button", { name: "Yopiq brauzer sinovi: amallar", exact: true })
  .click();
await page
  .getByRole("menuitem", { name: "Nusxa yaratish", exact: true })
  .click();
await page
  .getByRole("link", { name: "Yopiq brauzer sinovi (nusxa)", exact: true })
  .waitFor();
await page
  .getByRole("button", {
    name: "Yopiq brauzer sinovi (nusxa): amallar",
    exact: true,
  })
  .click();
await page.getByRole("menuitem", { name: "O‘chirish", exact: true }).click();
await page.getByRole("button", { name: "Bekor qilish", exact: true }).click();
await page
  .getByRole("link", { name: "Yopiq brauzer sinovi (nusxa)", exact: true })
  .waitFor();
await page
  .getByRole("button", {
    name: "Yopiq brauzer sinovi (nusxa): amallar",
    exact: true,
  })
  .click();
await page.getByRole("menuitem", { name: "O‘chirish", exact: true }).click();
await page.getByRole("button", { name: "Tasdiqlash", exact: true }).click();
await page
  .getByRole("link", { name: "Yopiq brauzer sinovi (nusxa)", exact: true })
  .waitFor({ state: "detached" });
await page.goto(baseURL + "/teachers");
const teacherRow = page.getByRole("row").filter({ hasText: "browser-teacher" });
await teacherRow
  .getByRole("button", { name: "Tahrirlash", exact: true })
  .click();
await page.getByRole("dialog", { name: "O‘qituvchini tahrirlash" }).waitFor();
await page
  .getByLabel("Email", { exact: true })
  .fill("browser-teacher@example.test");
await page.getByLabel("Fan", { exact: true }).fill("Matematika");
await page.getByRole("button", { name: "Saqlash", exact: true }).click();
await teacherRow
  .getByText("browser-teacher@example.test", { exact: true })
  .waitFor();
for (const action of ["Nofaol qilish", "Faollashtirish"]) {
  await teacherRow.getByRole("button", { name: action, exact: true }).click();
  await page
    .getByRole("dialog", { name: "Amalni tasdiqlash" })
    .getByRole("button", { name: "Tasdiqlash", exact: true })
    .click();
  await teacherRow
    .getByRole("button", {
      name: action === "Nofaol qilish" ? "Faollashtirish" : "Nofaol qilish",
      exact: true,
    })
    .waitFor();
}
await teacherRow
  .getByRole("button", { name: "Parolni yangilash", exact: true })
  .click();
await page.getByRole("button", { name: "Tasdiqlash", exact: true }).click();
const passwordDialog = page.getByRole("dialog", { name: "Vaqtinchalik parol" });
await passwordDialog.waitFor();
if ((await passwordDialog.locator("output").textContent()).length < 12)
  throw new Error("Missing temporary credential");
await passwordDialog
  .getByRole("button", { name: "Yopish", exact: true })
  .last()
  .click();
await page.goto(baseURL + "/groups");
await page.getByRole("button", { name: "Guruh yaratish" }).click();
await page.getByLabel("Guruh nomi").fill("Matematika guruhi");
await page.getByLabel("Sinov O‘quvchi", { exact: true }).check();
await page.getByRole("button", { name: "Saqlash", exact: true }).click();
await page.getByRole("heading", { name: "Matematika guruhi" }).waitFor();
await page.getByText("1 o‘quvchi", { exact: true }).waitFor();
await page.screenshot({
  path: `${artifactDir}/groups-light.png`,
  fullPage: true,
});
await page.getByRole("button", { name: "O‘chirish", exact: true }).click();
await page.getByRole("dialog", { name: "Amalni tasdiqlash" }).waitFor();
await page.getByRole("button", { name: "Bekor qilish", exact: true }).click();
await page
  .getByRole("heading", { name: "Matematika guruhi", exact: true })
  .waitFor();
await page.getByRole("button", { name: "O‘chirish", exact: true }).click();
await page.getByRole("button", { name: "Tasdiqlash", exact: true }).click();
await page
  .getByRole("heading", { name: "Matematika guruhi", exact: true })
  .waitFor({ state: "detached" });
await page.goto(baseURL + "/profile");
await page
  .getByLabel("Email", { exact: true })
  .fill("browser-admin@example.test");
await page.getByRole("button", { name: "Saqlash", exact: true }).click();
await page.getByText("Profil saqlandi.").waitFor();
await page.reload();
await page.getByLabel("Email", { exact: true }).waitFor();
if (
  (await page.getByLabel("Email", { exact: true }).inputValue()) !==
  "browser-admin@example.test"
)
  throw new Error("Profile did not persist");
await page.goto(baseURL + "/questions");
await page.getByRole("button", { name: "Yangi savol" }).click();
await page.getByLabel("Savol matni").fill("Qo‘lda yaratilgan savol");
for (const [label, value] of [
  ["A variant", "Birinchi"],
  ["B variant", "Ikkinchi"],
  ["C variant", "Uchinchi"],
  ["D variant", "To‘rtinchi"],
])
  await page.getByLabel(label, { exact: true }).fill(value);
await page.getByRole("radio", { name: "B", exact: true }).check();
await page.getByRole("button", { name: "Saqlash", exact: true }).click();
await page.getByText("Qo‘lda yaratilgan savol", { exact: true }).waitFor();
const manualRow = page
  .getByRole("row")
  .filter({ hasText: "Qo‘lda yaratilgan savol" });
await manualRow
  .getByRole("button", { name: "Tahrirlash", exact: true })
  .click();
await page
  .getByLabel("Rasm (PNG/JPEG/WebP, 5 MB gacha)", { exact: true })
  .setInputFiles(`${artifactDir}/question.png`);
await page.getByRole("img", { name: "Yuklanadigan rasm" }).waitFor();
await page.getByRole("button", { name: "Saqlash", exact: true }).click();
await page
  .getByRole("dialog", { name: "Savolni tahrirlash" })
  .waitFor({ state: "detached" });
await manualRow
  .getByRole("button", { name: "Tahrirlash", exact: true })
  .click();
await page.getByRole("img", { name: "Yuklanadigan rasm" }).waitFor();
await page
  .getByRole("button", { name: "Rasmni olib tashlash", exact: true })
  .click();
await page.getByRole("button", { name: "Saqlash", exact: true }).click();
await page
  .getByRole("dialog", { name: "Savolni tahrirlash" })
  .waitFor({ state: "detached" });
await manualRow
  .getByRole("button", { name: "Tahrirlash", exact: true })
  .click();
if (await page.getByRole("img", { name: "Yuklanadigan rasm" }).count())
  throw new Error("Image removal did not persist");
await page.getByRole("button", { name: "Bekor qilish", exact: true }).click();
await manualRow.getByRole("button", { name: "Nusxalash", exact: true }).click();
await page.waitForFunction(
  () =>
    [...document.querySelectorAll("tbody tr")].filter((row) =>
      row.textContent.includes("Qo‘lda yaratilgan savol"),
    ).length === 2,
);
await manualRow
  .first()
  .getByRole("button", { name: "O‘chirish", exact: true })
  .click();
await page.getByRole("button", { name: "Tasdiqlash", exact: true }).click();
await page.waitForFunction(
  () =>
    [...document.querySelectorAll("tbody tr")].filter((row) =>
      row.textContent.includes("Qo‘lda yaratilgan savol"),
    ).length === 1,
);
await page.goto(`${baseURL}/quizzes`);
await page.getByRole("link",{name:"Wizard brauzer sinovi",exact:true}).click();
await page.getByRole("heading",{name:"Wizard brauzer sinovi",exact:true}).waitFor();
await page.getByRole("button", { name: "2. Savollar", exact: true }).click();
await page
  .locator(".section-heading")
  .filter({ hasText: "Bankdan tanlanadigan savol" })
  .getByRole("button", { name: "Tanlash", exact: true })
  .click();
await page
  .getByRole("button", { name: "2-savolni yuqoriga", exact: true })
  .click();
await page
  .locator(".notice")
  .filter({ hasText: "1. Bankdan tanlanadigan savol" })
  .waitFor();
await page
  .locator(".notice")
  .filter({ hasText: "Bankdan tanlanadigan savol" })
  .getByRole("button", { name: "Ajratish", exact: true })
  .click();
await page
  .locator(".notice")
  .filter({ hasText: "Bankdan tanlanadigan savol" })
  .waitFor({ state: "detached" });
await page
  .getByRole("button", { name: "1. Asosiy sozlamalar", exact: true })
  .click();
await page.getByLabel("Test nomi", { exact: true }).fill("Saqlanmagan nom");
await page.getByRole("link", { name: "Savollar", exact: true }).click();
await page.getByRole("dialog", { name: "Amalni tasdiqlash" }).waitFor();
await page.getByRole("button", { name: "Bekor qilish", exact: true }).click();
if (
  (await page.getByLabel("Test nomi", { exact: true }).inputValue()) !==
  "Saqlanmagan nom"
)
  throw new Error("Unsaved title was lost");
await page.evaluate(() => history.back());
await page.getByRole("dialog", { name: "Amalni tasdiqlash" }).waitFor();
await page.getByRole("button", { name: "Tasdiqlash", exact: true }).click();
await page.getByRole("heading", { name: "Testlar", exact: true }).waitFor();
await page.goto(baseURL + "/students");
const studentRow = page.getByRole("row").filter({ hasText: "Sinov O‘quvchi" });
for (const action of ["Nofaol qilish", "Faollashtirish"]) {
  await studentRow.getByRole("button", { name: action, exact: true }).click();
  await page.getByRole("button", { name: "Tasdiqlash", exact: true }).click();
  await studentRow
    .getByRole("button", {
      name: action === "Nofaol qilish" ? "Faollashtirish" : "Nofaol qilish",
      exact: true,
    })
    .waitFor();
}
await page.getByRole("link", { name: "Sinov O‘quvchi" }).click();
await page
  .getByRole("heading", { name: "Sinov O‘quvchi", exact: true })
  .waitFor();
await page.screenshot({
  path: `${artifactDir}/student-detail-light.png`,
  fullPage: true,
});
await page.goto(baseURL + "/results");
await page.getByRole("button", { name: "Sinov O‘quvchi" }).click();
await page.getByRole("dialog", { name: "Natija tafsilotlari" }).waitFor();
await page.getByText("To‘g‘ri javob: 4", { exact: true }).waitFor();
await page.screenshot({
  path: `${artifactDir}/result-detail-light.png`,
  fullPage: true,
});
await page.keyboard.press("Escape");
await page.goto(baseURL + "/reports");
for (const kind of ["results", "students", "leaderboard", "teachers"]) {
  await page.getByLabel("Hisobot turi").selectOption(kind);
  await page.waitForTimeout(300);
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Excel eksporti" }).click();
  await (await download).saveAs(`${artifactDir}/report-${kind}.xlsx`);
}
// Enqueue through the real authenticated API and verify the actual worker output.
const background = await page.evaluate(async () => {
  const { csrfToken } = await (await fetch("/api/auth/csrf/")).json();
  const response = await fetch("/api/reports/export/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
    body: JSON.stringify({ background: true, report_type: "results" }),
  });
  if (response.status !== 202)
    throw new Error("Background export was not queued");
  return response.json();
});
await page.reload();
await page
  .getByRole("status")
  .filter({ hasText: "Tayyor" })
  .waitFor({ timeout: 30000 });
const backgroundDownload = page.waitForEvent("download");
await page
  .locator(`a[href="/api/reports/exports/${background.id}/download/"]`)
  .click();
await (
  await backgroundDownload
).saveAs(`${artifactDir}/report-background.xlsx`);
for (const theme of ["light", "dark"])
  for (const route of [
    "groups",
    "settings",
    "reports",
    "rankings",
    "questions",
  ]) {
    await page.goto(baseURL + "/" + route);
    await page.locator("h1").waitFor();
    await page.evaluate(
      (t) => document.documentElement.classList.toggle("dark", t === "dark"),
      theme,
    );
    for (const width of [360, 390, 768, 1024, 1280, 1440, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      if (
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        )
      )
        throw new Error("Overflow " + route + " " + width);
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.screenshot({
      path: `${artifactDir}/${route}-${theme}-expanded.png`,
      fullPage: true,
    });
  }
console.log(
  "PASS: account menu keyboard, group membership, persisted profile update, manual question, real student/result details, four XLSX report kinds, expanded responsive light/dark pages.",
);
await browser.close();
