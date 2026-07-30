export function getColumnLabel(
  columns: readonly { key: string, label: string }[],
  key: string,
): string {
  return columns.find((column) => column.key === key)?.label ?? key
}
