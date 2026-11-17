export const statusLabel: Record<string, string> = {
  draft: "Qoralama",
  published: "Faol",
  closed: "Yopilgan",
  archived: "Arxivlangan",
  in_progress: "Jarayonda",
  completed: "Yakunlangan",
  timed_out: "Vaqt tugagan",
  pending: "Navbatda",
  ready: "Tayyor",
  failed: "Xatolik",
};
export function tashkentDateInput(value: string) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Tashkent",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(value));
  const part = (name: string) => parts.find((x) => x.type === name)?.value;
  return `${part("year")}-${part("month")}-${part("day")}T${part("hour")}:${part("minute")}`;
}
export function formatPercent(value: string | number | null | undefined) {
  if (value == null) return "—";
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0 || number > 100) return "—";
  if (Math.abs(number) < 0.000001) return "0.00";
  const [whole, fraction = ""] = (
    String(value).toLowerCase().includes("e")
      ? number.toFixed(8)
      : String(value)
  ).split(".");
  const digits = fraction.padEnd(3, "0");
  let hundredths = BigInt(whole) * 100n + BigInt(digits.slice(0, 2));
  if (digits[2] >= "5") hundredths += 1n;
  return `${hundredths / 100n}.${String(hundredths % 100n).padStart(2, "0")}`;
}
