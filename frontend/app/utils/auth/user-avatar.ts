function initialsFromName(name?: string) {
  const trimmed = (name || 'User').trim()
  const first = Array.from(trimmed)[0] || 'U'
  return /[\p{L}\p{N}]/u.test(first) ? first.toUpperCase() : 'U'
}

export function defaultUserAvatarUrl(name?: string) {
  const letter = initialsFromName(name)
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" fill="#64748b"/><text x="32" y="42" text-anchor="middle" font-size="28" font-family="system-ui,sans-serif" fill="#fff">${letter}</text></svg>`
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

export function resolveUserAvatar(user?: { name?: string, avatar?: string } | null) {
  return user?.avatar || defaultUserAvatarUrl(user?.name)
}
