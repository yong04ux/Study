export function splitPreferenceInput(value: string): string[] {
  // 偏好输入支持空格、逗号、中文标点和换行分隔，方便用户自然输入。
  const items = value
    .split(/[\s,，、;；]+/)
    .map((item) => item.trim())
    .filter(Boolean);

  // 使用 Set 去重，同时保留用户输入的原始顺序。
  const seen = new Set<string>();
  const uniqueItems: string[] = [];

  for (const item of items) {
    if (!seen.has(item)) {
      seen.add(item);
      uniqueItems.push(item);
    }
  }

  return uniqueItems;
}
