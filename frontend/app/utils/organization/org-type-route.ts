/** Map `/organizations/{orgType}` to a static entity config key. */
export function organizationEntityKeyFromParam(param: string): string | null {
  const key = String(param || '').toLowerCase()
  if (key === 'department' || key === 'departments') return 'departments'
  if (key === 'company' || key === 'companies') return 'companies'
  return null
}

/** Redirect singular menu aliases to the canonical static org routes. */
export function organizationCanonicalPath(param: string, rest = ''): string | null {
  const key = String(param || '').toLowerCase()
  const suffix = rest ? (rest.startsWith('/') ? rest : `/${rest}`) : ''
  if (key === 'department') return `/organizations/departments${suffix}`
  if (key === 'company') return `/organizations/companies${suffix}`
  return null
}
