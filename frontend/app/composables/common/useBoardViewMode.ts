export type BoardViewMode = 'cards' | 'table'

/** Persist card/table preference per board across navigations in the session. */
export function useBoardViewMode(stateKey: string, defaultMode: BoardViewMode = 'cards') {
  return useState<BoardViewMode>(stateKey, () => defaultMode)
}
