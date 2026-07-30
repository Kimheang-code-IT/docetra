/** Slice rows for client-side pagination (mock mode). API mode returns rows as-is. */
export function slicePage<T>(
  rows: readonly T[],
  pageIndex: number,
  pageSize: number,
  clientPaginate: boolean,
): T[] {
  if (!clientPaginate) return [...rows]
  const start = pageIndex * pageSize
  return rows.slice(start, start + pageSize)
}
