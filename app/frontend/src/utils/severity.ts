export function severityClass(name: string): string {
  const lower = name.toLowerCase()
  if (lower.startsWith('high')) return 'sev-high'
  if (lower.startsWith('med')) return 'sev-med'
  return 'sev-low'
}
