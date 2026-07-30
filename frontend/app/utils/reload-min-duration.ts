export const RELOAD_MIN_DURATION_MS = 300

export async function ensureMinReloadDuration(
  startedAt: number,
  minMs = RELOAD_MIN_DURATION_MS,
) {
  const remaining = minMs - (Date.now() - startedAt)
  if (remaining > 0) {
    await new Promise((resolve) => setTimeout(resolve, remaining))
  }
}
