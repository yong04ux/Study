import type { TextareaHTMLAttributes } from "react";
import { cx } from "./cx";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function Textarea({ label, error, className, ...props }: TextareaProps) {
  /* 通用多行输入框：常用于问题输入、地区偏好和专业偏好。 */
  return (
    <label className="block">
      {label ? <span className="text-sm font-medium text-slate-700">{label}</span> : null}
      <textarea
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
