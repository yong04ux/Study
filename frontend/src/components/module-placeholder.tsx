import type { ReactNode } from "react";

interface ModulePlaceholderProps {
  eyebrow: string;
  title: string;
  description: string;
  highlights: string[];
  aside?: ReactNode;
}

export function ModulePlaceholder({
  eyebrow,
  title,
  description,
  highlights,
  aside
}: ModulePlaceholderProps) {
  /* 通用占位模块：早期开发时用于快速搭页面骨架和说明区。 */
  return (
    <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
      <div className="panel">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-brand-600">
          {eyebrow}
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          {title}
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
          {description}
        </p>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {highlights.map((item) => (
            <div
              key={item}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-700"
            >
              {item}
            </div>
          ))}
        </div>
      </div>

      <aside className="panel">
        {aside ?? (
          <>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
              页面说明
            </p>
            <p className="mt-4 text-sm leading-7 text-slate-600">
              这个页面已经接入路由，可直接继续补表单、列表、图表和 API 调用逻辑。
            </p>
          </>
        )}
      </aside>
    </section>
  );
}
