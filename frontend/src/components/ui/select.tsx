import type { ReactNode, SelectHTMLAttributes } from "react";
import { cx } from "./cx";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  children: ReactNode;
}

export function Select({ label, error, className, children, ...props }: SelectProps) {
  /* 通用下拉框：用于科类、是否 985/211 等固定选项。 */
  return (
    <label className="block">
      {label ? <span className="text-sm font-medium text-slate-700">{label}</span> : null}
      <select
        className={cx(
          "w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-100",
          label && "mt-2",
          error && "border-rose-300 focus:border-rose-400 focus:ring-rose-100",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}
    </label>
  );
}
