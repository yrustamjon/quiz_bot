import { chromium } from "@playwright/test";
import fs from "node:fs";
const identity = JSON.parse(
  fs.readFileSync("/workspace/artifacts/ui-identity.json", "utf8"),
);
const browser = await chromium.launch({
  executablePath: "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.on("pageerror", (err) => console.log("PAGE ERROR", err.message));
await page.goto("http://127.0.0.1:5173/login");
await page.getByLabel("Login yoki email").fill(identity.username);
await page.locator("input[name=password]").fill(identity.password);
await page.getByRole("button", { name: "Hisobga kirish", exact: true }).click();
await page
  .getByRole("heading", { name: "Xush kelibsiz, Interfeys" })
  .waitFor({ timeout: 15000 });
await page.screenshot({
  path: "/workspace/artifacts/dashboard-light.png",
  fullPage: true,
});
await page.getByRole("button", { name: "Qorong‘i mavzu" }).click();
await page.screenshot({
  path: "/workspace/artifacts/dashboard-dark.png",
  fullPage: true,
});
await page.goto("http://127.0.0.1:5173/quizzes");
await page.getByRole("button", { name: "Yangi test", exact: true }).click();
await page.getByLabel("Test nomi").fill("Brauzer tekshiruvi");
await page.getByLabel("Fan", { exact: true }).fill("Matematika");
await page.getByRole("button", { name: "Qoralamani yaratish" }).click();
await page.getByRole("link", { name: "Brauzer tekshiruvi" }).waitFor();
await page.reload();
await page.getByRole("link", { name: "Brauzer tekshiruvi" }).waitFor();
await page.screenshot({
  path: "/workspace/artifacts/quizzes-dark.png",
  fullPage: true,
});
for (const path of ["/", "/quizzes", "/questions", "/students", "/profile"]) {
  await page.goto("http://127.0.0.1:5173" + path);
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
await page.goto("http://127.0.0.1:5173/");
await page.getByRole("heading", { name: "Xush kelibsiz, Interfeys" }).waitFor();
await page.screenshot({
  path: "/workspace/artifacts/dashboard-mobile-dark.png",
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
