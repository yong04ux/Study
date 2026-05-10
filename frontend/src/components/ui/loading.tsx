import { cx } from "./cx";

interface LoadingProps {
  label?: string;
  className?: string;
}

export function Loading({ label = "Loading...", className }: LoadingProps) {
  /* 行内加载提示：适合按钮附近或局部区域展示。 */
  return (
    <div className={cx("flex items-center gap-3 text-sm text-slate-600", className)}>
      <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-sky-500" />
      <span>{label}</span>
    </div>
  );
}

export function LoadingBlock({ className }: { className?: string }) {
  /* 骨架块：用于列表、详情等内容加载前的占位。 */
  return <div className={cx("h-24 animate-pulse rounded-lg bg-slate-100", className)} />;
}
