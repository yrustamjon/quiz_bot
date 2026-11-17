// Actual Django API and browser network conditions; no API route mocks.
import { chromium } from "@playwright/test";
import fs from "node:fs";
import AxeBuilder from "@axe-core/playwright";
const artifacts = process.env.QUIZ_ARTIFACT_DIR || "/workspace/artifacts";
const baseURL = process.env.QUIZ_BASE_URL || "http://127.0.0.1:5173";
const identity = JSON.parse(
  fs.readFileSync(`${artifacts}/ui-identity.json`, "utf8"),
);
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
page.setDefaultTimeout(15000);
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const audits = [];
async function auditState(state) {
  for (const theme of ["light", "dark"]) {
    await page.evaluate(
      (t) => document.documentElement.classList.toggle("dark", t === "dark"),
      theme,
    );
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    audits.push({ state, theme, violations: result.violations });
    if (result.violations.length)
      throw new Error(
        state +
          " accessibility: " +
          result.violations.map((v) => v.id).join(","),
      );
  }
  await page.evaluate(() => document.documentElement.classList.remove("dark"));
}
async function mutation(path, method, data) {
  return page.evaluate(
    async ({ path, method, data }) => {
      const { csrfToken } = await (await fetch("/api/auth/csrf/")).json();
      const response = await fetch("/api/" + path, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: data === undefined ? undefined : JSON.stringify(data),
      });
      if (!response.ok)
        throw new Error("Real API mutation failed: " + response.status);
      return response.status === 204 ? null : response.json();
    },
    { path, method, data },
  );
}
try {
  await page.goto(baseURL + "/login");
  await page.getByLabel("Login yoki email").fill(identity.username);
  await page.locator("input[name=password]").fill(identity.password);
  await page
    .getByRole("button", { name: "Hisobga kirish", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Xush kelibsiz, Interfeys" })
    .waitFor();
  const payload = 'XSS sinovi <img src=x onerror="window.__quizXss=1">';
  const question = await mutation("questions/", "POST", {
    text: payload,
    options: ["a", "b", "c", "d"],
    correct_option: 0,
    points: "1",
  });
  const quiz = await mutation("quizzes/", "POST", {
    title: payload,
    subject: "Xavfsizlik sinovi",
    question_count: 1,
    duration_minutes: 10,
  });
  await page.goto(baseURL + "/questions");
  await page.getByRole("cell", { name: payload, exact: true }).waitFor();
  if (
    (await page.locator('img[src="x"]').count()) ||
    (await page.evaluate(() => window.__quizXss))
  )
    throw new Error("Stored question HTML executed");
  await page.goto(baseURL + "/quizzes");
  await page.getByRole("link", { name: payload, exact: true }).waitFor();
  if (
    (await page.locator('img[src="x"]').count()) ||
    (await page.evaluate(() => window.__quizXss))
  )
    throw new Error("Stored quiz HTML executed");
  await page.goto(baseURL + "/questions");
  await page.getByRole("cell", { name: payload, exact: true }).waitFor();
  // Offline-aware queries pause; make that state explicit instead of a silent spinner.
  await context.setOffline(true);
  await page
    .getByLabel("Qidirish", { exact: true })
    .fill("offline-empty-check");
  await page
    .getByRole("alert")
    .filter({ hasText: "Internet aloqasi uzildi." })
    .waitFor();
  await page.screenshot({
    path: `${artifacts}/questions-offline-light.png`,
    fullPage: true,
  });
  await auditState("offline");
  await page.setViewportSize({ width: 390, height: 844 });
  if (
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
  )
    throw new Error("Offline mobile overflow");
  await page.screenshot({
    path: `${artifacts}/questions-offline-mobile.png`,
    fullPage: true,
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await context.setOffline(false);
  await page.locator(".empty").waitFor();
  await page
    .getByRole("alert")
    .filter({ hasText: "Internet aloqasi uzildi." })
    .waitFor({ state: "detached" });
  console.log("PASS: real offline notice and reconnect recovery");
  const network = await context.newCDPSession(page);
  await network.send("Network.enable");
  // Drop transport while navigator stays online: this exercises real fetch failure/retry.
  await network.send("Network.setBlockedURLs", { urls: ["*api/questions/*"] });
  await page
    .getByLabel("Qidirish", { exact: true })
    .fill("transport-empty-check");
  await page
    .getByRole("alert")
    .filter({ hasText: "Internet bilan bog‘lanishda muammo yuz berdi." })
    .waitFor();
  await page.screenshot({
    path: `${artifacts}/questions-error-light.png`,
    fullPage: true,
  });
  await auditState("request-error");
  await network.send("Network.setBlockedURLs", { urls: [] });
  await page
    .getByRole("button", { name: "Qayta urinish", exact: true })
    .click();
  await page.locator(".empty").waitFor();
  await page.screenshot({
    path: `${artifacts}/questions-empty-light.png`,
    fullPage: true,
  });
  await auditState("empty");
  // Delay real responses without changing their status, body or ownership.
  console.log(
    "PASS: real request blocking, localized error, retry and empty state",
  );
  await network.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 12000,
    downloadThroughput: -1,
    uploadThroughput: -1,
  });
  await page.getByLabel("Qidirish", { exact: true }).fill("XSS sinovi");
  await page
    .getByRole("status", { name: "Yuklanmoqda", exact: true })
    .waitFor();
  await page.screenshot({
    path: `${artifacts}/questions-loading-light.png`,
    fullPage: true,
  });
  await auditState("loading");
  await page.getByRole("cell", { name: payload, exact: true }).waitFor();
  await network.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 0,
    downloadThroughput: -1,
    uploadThroughput: -1,
  });
  await network.detach();
  await mutation(`questions/${question.id}/`, "DELETE");
  await mutation(`quizzes/${quiz.id}/`, "DELETE");
  fs.writeFileSync(
    `${artifacts}/security-accessibility.json`,
    JSON.stringify(audits, null, 2),
  );
  if (errors.length) throw new Error(errors.join("; "));
  console.log(
    "PASS: stored question/quiz XSS rendered as text, actual offline error/retry recovery, empty and delayed-response loading states. No API mocks.",
  );
} catch (error) {
  await page
    .screenshot({
      path: `${artifacts}/security-failure.png`,
      fullPage: true,
      timeout: 3000,
    })
    .catch(() => {});
  throw error;
} finally {
  await context.setOffline(false);
  await browser.close();
}
