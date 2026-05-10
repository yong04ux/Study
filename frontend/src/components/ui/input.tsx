import type { InputHTMLAttributes } from "react";
import { cx } from "./cx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className, ...props }: InputProps) {
  /* 通用输入框：label、error 和原生 input 属性统一封装，页面只关心字段值。 */
  return (
    <label className="block">
      {label ? <span className="text-sm font-medium text-slate-700">{label}</span> : null}
      <input
        className={cx(
          "w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-sky-500 focus:ring-4 focus:ring-sky-100",
          label && "mt-2",
          error && "border-rose-300 focus:border-rose-400 focus:ring-rose-100",
          className,
        )}
        {...props}
      />
      {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}
    </label>
  );
}
