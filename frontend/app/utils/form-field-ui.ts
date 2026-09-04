/** Shared Nuxt UI props for ERPNext-style document form controls.
 * soft = light fill, no border idle; grey ring only when focused/active.
 */
export const FORM_CONTROL = {
  color: 'neutral' as const,
  variant: 'soft' as const,
  size: 'md' as const,
}

export const FORM_NUMBER_BUTTONS = {
  color: 'neutral' as const,
  variant: 'ghost' as const,
  size: 'sm' as const,
}

/** Compact table/matrix cells still use the same fill, just smaller. */
export const FORM_CONTROL_COMPACT = {
  color: 'neutral' as const,
  variant: 'soft' as const,
  size: 'sm' as const,
}

/** Idle: elevated fill, no ring. Active: grey inset ring only. */
export const FORM_SOFT_IDLE
  = 'text-highlighted bg-elevated/70 hover:bg-elevated ring-0 disabled:bg-elevated/50'

export const FORM_SOFT_FOCUS
  = 'focus:bg-elevated focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default focus-visible:outline-none'

export const FORM_SOFT_FOCUS_WITHIN
  = 'has-focus:bg-elevated has-focus:ring-1 has-focus:ring-inset has-focus:ring-default'

export const FORM_SOFT_CLASS = `${FORM_SOFT_IDLE} ${FORM_SOFT_FOCUS}`
export const FORM_SOFT_DATE_CLASS = `${FORM_SOFT_IDLE} ${FORM_SOFT_FOCUS_WITHIN}`
