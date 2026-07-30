export const formatDate = (datePayload: string | Date | number): string => {
  if (!datePayload) return 'N/A'
  
  const d = new Date(datePayload)
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  })
}
