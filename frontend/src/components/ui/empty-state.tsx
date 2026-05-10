import type { ReactNode } from "react";
import { cx } from "./cx";

interface EmptyStateProps {
  title?: string;
  description: ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  className,
}: EmptyStateProps) {
  /* 空状态组件：用于初始状态、暂无结果和某个分组无数据。 */
  return (
    <div
      className={cx(
        "rounded-xl border border-dashed border-slate-300 bg-slate-50/80 px-5 py-10 text-sm text-slate-500",
        className,
      )}
    >
      {title ? <p className="font-semibold text-slate-700">{title}</p> : null}
      <p className={cx(title && "mt-2", "leading-7")}>{description}</p>
    </div>
  );
}
