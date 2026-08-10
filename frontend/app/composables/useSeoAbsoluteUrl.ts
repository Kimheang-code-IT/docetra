/**
 * Resolve a path or URL to an absolute URL for Open Graph / Twitter crawlers.
 * Relative paths (e.g. `/logo.png`) are ignored by Telegram, WhatsApp, Facebook, etc.
 */
export function useSeoAbsoluteUrl() {
  const config = useRuntimeConfig()

  function absoluteUrl(pathOrUrl: string | undefined | null): string {
    const raw = String(pathOrUrl || '').trim()
    if (!raw) return ''
    if (/^https?:\/\//i.test(raw)) return raw

    const configured = String(config.public.siteUrl || '').replace(/\/$/, '')
    const origin = configured || (() => {
      try {
        return useRequestURL().origin
      }
      catch {
        return ''
      }
    })()

    if (!origin) return raw

    const path = raw.startsWith('/') ? raw : `/${raw}`
    return `${origin}${path}`
  }

  function absolutePageUrl(path?: string): string {
    const configured = String(config.public.siteUrl || '').replace(/\/$/, '')
    try {
      const request = useRequestURL()
      if (path) {
        const origin = configured || request.origin
        return `${origin}${path.startsWith('/') ? path : `/${path}`}`
      }
      if (configured) {
        return `${configured}${request.pathname}${request.search}`
      }
      return request.href
    }
    catch {
      return configured || ''
    }
  }

  return {
    absoluteUrl,
    absolutePageUrl,
  }
}
