import { ACTION_COL_WIDTH } from '~/constants/report-table'

/** Auto-fit column sizing: grow with content, optional minimum floor. */
export function colWidthStyle(minWidth?: number) {
  const style: Record<string, string> = {
    width: 'max-content',
  }
  if (minWidth && minWidth > 0) {
    style.minWidth = `${minWidth}px`
  }
  return style
}

export function actionColStyle(isHeader = false) {
  return {
    ...colWidthStyle(ACTION_COL_WIDTH),
    right: '0px',
    zIndex: String(isHeader ? 35 : 25),
  }
}

export function stickyColStyle(
  left: number,
  minWidth: number | undefined,
  isHeader: boolean,
  index: number,
) {
  return {
    ...colWidthStyle(minWidth),
    left: `${left}px`,
    zIndex: String(isHeader ? 42 - index : 22 - index),
  }
}

export function stickyLeftStyle(left: number, minWidth: number, isHeader = false, index = 0) {
  return stickyColStyle(left, minWidth, isHeader, index)
}

export function buildStickyOffsets(widths: number[]) {
  const offsets: number[] = []
  let acc = 0
  for (const width of widths) {
    offsets.push(acc)
    acc += width
  }
  return offsets
}
