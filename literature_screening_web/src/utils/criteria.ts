export interface ParsedCriteriaDraft {
  topic: string
  inclusion: string[]
  exclusion: string[]
}

export function parseCriteriaMarkdown(markdown: string): ParsedCriteriaDraft {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n')
  let topic = ''
  let section: 'inclusion' | 'exclusion' | null = null
  const inclusion: string[] = []
  const exclusion: string[] = []

  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) continue

    if (line.startsWith('#')) {
      const heading = line.replace(/^#+/, '').trim().toLowerCase()
      if (!topic && !heading.includes('inclusion') && !heading.includes('exclusion') && !heading.includes('纳入') && !heading.includes('排除')) {
        topic = line.replace(/^#+/, '').trim()
      }
      if (heading.includes('inclusion') || heading.includes('纳入')) section = 'inclusion'
      else if (heading.includes('exclusion') || heading.includes('排除')) section = 'exclusion'
      continue
    }

    if (!topic) {
      topic = line
      continue
    }

    if (line.startsWith('-') || line.startsWith('*')) {
      const value = line.replace(/^[-*]\s*/, '').trim()
      if (!value) continue
      if (section === 'inclusion') inclusion.push(value)
      if (section === 'exclusion') exclusion.push(value)
    }
  }

  return {
    topic,
    inclusion,
    exclusion
  }
}
