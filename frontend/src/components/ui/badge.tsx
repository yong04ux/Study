import type { ReactNode } from "react";
import { cx } from "./cx";

interface BadgeProps {
  children: ReactNode;
  tone?: "neutral" | "brand" | "success" | "warning" | "danger";
  className?: string;
}

const toneMap = {
  neutral: "bg-slate-100 text-slate-700",
  brand: "bg-sky-100 text-sky-700",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  danger: "bg-rose-100 text-rose-700",
};

export function Badge({
  children,
  tone = "neutral",
  className,
}: BadgeProps) {
  /* 通用徽标：用于展示状态、院校标签和模块标识。 */
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold tracking-[0.08em]",
        toneMap[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
