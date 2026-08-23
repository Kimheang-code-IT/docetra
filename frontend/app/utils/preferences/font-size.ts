import type { AppFontSize } from '~/types/docetra/settings'

export const FONT_SIZE_PX: Record<AppFontSize, string> = {
  sm: '14px',
  md: '16px',
  lg: '18px',
  xl: '20px',
}

export const DEFAULT_FONT_SIZE: AppFontSize = 'md'

export function normalizeFontSize(value: string | null | undefined): AppFontSize {
  if (value === 'sm' || value === 'md' || value === 'lg' || value === 'xl') return value
  return DEFAULT_FONT_SIZE
}
