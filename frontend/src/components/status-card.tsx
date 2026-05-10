interface StatusCardProps {
  title: string;
  value: string;
  tone?: "neutral" | "success";
}

export function StatusCard({
  title,
  value,
  tone = "neutral"
}: StatusCardProps) {
  /* 健康检查页使用的小卡片，根据 tone 展示正常或普通状态。 */
  const toneClass =
    tone === "success"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] opacity-70">
        {title}
      </p>
      <p className="mt-3 text-lg font-semibold">{value}</p>
    </div>
  );
}
