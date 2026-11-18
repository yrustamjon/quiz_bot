import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
// Chromium's ICU can fall back to numeric "M11" for Uzbek short months.
const months = [
  "yan",
  "fev",
  "mar",
  "apr",
  "may",
  "iyn",
  "iyl",
  "avg",
  "sen",
  "okt",
  "noy",
  "dek",
];
const dateLabel = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return year && months[month - 1] && day
    ? `${day} ${months[month - 1]}`
    : value;
};
export default function ActivityChart({
  data,
}: {
  data: { date: string; attempts: number }[];
}) {
  return (
    <div className="chart" role="img" aria-label="Kunlik urinishlar grafigi">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 12, right: 8, bottom: 0, left: -22 }}
        >
          <CartesianGrid
            stroke="var(--border)"
            vertical={false}
            strokeDasharray="3 5"
          />
          <XAxis
            dataKey="date"
            tickFormatter={dateLabel}
            axisLine={false}
            tickLine={false}
            stroke="var(--muted)"
            fontSize={11}
            minTickGap={24}
          />
          <YAxis
            allowDecimals={false}
            axisLine={false}
            tickLine={false}
            stroke="var(--muted)"
            fontSize={11}
          />
          <Tooltip
            labelFormatter={(value) => dateLabel(String(value))}
            cursor={{ fill: "var(--soft)" }}
            contentStyle={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              color: "var(--text)",
              boxShadow: "var(--shadow)",
            }}
          />
          <Bar
            dataKey="attempts"
            name="Urinishlar"
            fill="var(--primary)"
            radius={[5, 5, 0, 0]}
            maxBarSize={36}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
