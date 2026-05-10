export function cx(...values: Array<string | false | null | undefined>) {
  /* 简单 className 合并工具：过滤掉 false/null/undefined，避免 JSX 中拼接样式混乱。 */
  return values.filter(Boolean).join(" ");
}
