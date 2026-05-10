import type { ReactNode } from "react";
import { cx } from "./cx";

interface ErrorMessageProps {
  children: ReactNode;
  className?: string;
}

export function ErrorMessage({ children, className }: ErrorMessageProps) {
  /* 统一错误提示样式，页面只需要传入错误文案。 */
  return (
    <div
      className={cx(
        "rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700",
        className,
      )}
    >
      {children}
    </div>
  );
}
