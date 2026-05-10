import type { ReactNode } from "react";
import { cx } from "./cx";

interface CardProps {
  children: ReactNode;
  className?: string;
}

interface CardSectionProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  /* 通用卡片外壳：统一圆角、边框、背景和阴影。 */
  return (
    <div
      className={cx(
        "rounded-xl border border-slate-200/80 bg-[rgba(255,255,255,0.96)] shadow-[0_20px_60px_rgba(15,23,42,0.08)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: CardSectionProps) {
  /* 卡片头部区域：通常放标题、说明和操作按钮。 */
  return <div className={cx("border-b border-slate-200/70 p-5 sm:p-6", className)}>{children}</div>;
}

export function CardBody({ children, className }: CardSectionProps) {
  /* 卡片内容区域：承载表单、列表、详情等主体内容。 */
  return <div className={cx("p-5 sm:p-6", className)}>{children}</div>;
}
