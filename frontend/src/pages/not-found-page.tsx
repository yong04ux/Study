import { Link } from "react-router-dom";

export function NotFoundPage() {
  /* 404 兜底页：当路由表没有匹配页面时，引导用户回到首页。 */
  return (
    <section className="panel mx-auto max-w-2xl text-center">
      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
        404
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
        页面不存在
      </h1>
      <p className="mt-4 text-sm leading-7 text-slate-600">
        你访问的页面还没有配置对应内容，可以先返回首页继续浏览当前已经搭好的功能模块。
      </p>
      <Link
        to="/"
        className="mt-6 inline-flex rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
      >
        返回首页
      </Link>
    </section>
  );
}
