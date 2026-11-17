// Bound each adversarial match in a separate process so a vulnerable matcher
// cannot hang the validation runner. No advisory is suppressed by this check.
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const entry = require.resolve("picomatch");
const program =
  "const match=require(process.argv[1])(process.argv[2]);process.stdout.write(JSON.stringify(match(process.argv[3])));";
const cases = [
  ["single wildcard repeat", "+(*)b", "a".repeat(36) + "c", false],
  ["single wildcard/literal repeat", "+(*a)b", "a".repeat(36) + "c", false],
  ["zero-or-more wildcard repeat", "*(*)b", "a".repeat(36) + "c", false],
  ["ordinary project files", "**/*.{ts,tsx}", "src/pages/Auth.tsx", true],
  ["ordinary exclusion", "**/*.{ts,tsx}", "src/style.css", false],
];
let failures = 0;
for (const [name, pattern, input, expected] of cases) {
  const result = spawnSync(
    process.execPath,
    ["-e", program, entry, pattern, input],
    {
      timeout: 1500,
      encoding: "utf8",
      maxBuffer: 8192,
      killSignal: "SIGKILL",
    },
  );
  const passed =
    !result.error &&
    result.status === 0 &&
    result.stdout === JSON.stringify(expected);
  console.log(
    passed ? "PASS" : "FAIL",
    name,
    result.error?.code === "ETIMEDOUT" ? "bounded timeout exceeded" : "",
  );
  if (!passed) failures++;
}
if (failures) {
  console.error(
    "Glob security gate failed. Keep the dependency advisory open; do not suppress the audit.",
  );
  process.exitCode = 1;
}
