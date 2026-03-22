export interface ParsedCriteriaDraft {
  topic: string
  inclusion: string[]
  exclusion: string[]
  matched: boolean
  warnings: string[]
}

function normalizeLine(input: string) {
  return input.replace(/\u3000/g, ' ').trim()
}

function isBulletLine(line: string) {
  return /^[-*•]\s+/.test(line) || /^\d+[.)、]\s+/.test(line)
}

function stripBullet(line: string) {
  return line.replace(/^[-*•]\s+/, '').replace(/^\d+[.)、]\s+/, '').trim()
}

function detectHeadingType(line: string): 'topic' | 'inclusion' | 'exclusion' | null {
  const heading = line.replace(/^#+/, '').trim().toLowerCase()
  if (/(纳入|inclusion)/i.test(heading)) return 'inclusion'
  if (/(排除|exclusion)/i.test(heading)) return 'exclusion'
  if (heading) return 'topic'
  return null
}

export function parseCriteriaMarkdown(markdown: string): ParsedCriteriaDraft {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n').map(normalizeLine)
  let topic = ''
  let section: 'inclusion' | 'exclusion' | null = null
  const inclusion: string[] = []
  const exclusion: string[] = []
  const warnings: string[] = []

  for (const line of lines) {
    if (!line) continue

    if (line.startsWith('#')) {
      const type = detectHeadingType(line)
      if (type === 'inclusion' || type === 'exclusion') {
        section = type
        continue
      }
      if (type === 'topic' && !topic) {
        topic = line.replace(/^#+/, '').trim()
      }
      continue
    }

    if (!topic && !isBulletLine(line) && !/^(纳入标准|排除标准|inclusion|exclusion)/i.test(line)) {
      topic = line
      continue
    }

    const inlineInclusion = line.match(/^(纳入标准|inclusion|inclusion criteria)\s*[:：]\s*(.+)$/i)
    if (inlineInclusion) {
      section = 'inclusion'
      inclusion.push(...inlineInclusion[2].split(/[；;]+/).map(item => item.trim()).filter(Boolean))
      continue
    }

    const inlineExclusion = line.match(/^(排除标准|exclusion|exclusion criteria)\s*[:：]\s*(.+)$/i)
    if (inlineExclusion) {
      section = 'exclusion'
      exclusion.push(...inlineExclusion[2].split(/[；;]+/).map(item => item.trim()).filter(Boolean))
      continue
    }

    if (/^(纳入标准|inclusion|inclusion criteria)$/i.test(line)) {
      section = 'inclusion'
      continue
    }

    if (/^(排除标准|exclusion|exclusion criteria)$/i.test(line)) {
      section = 'exclusion'
      continue
    }

    if (isBulletLine(line)) {
      const value = stripBullet(line)
      if (!value) continue
      if (section === 'inclusion') inclusion.push(value)
      else if (section === 'exclusion') exclusion.push(value)
      continue
    }
  }

  if (!topic) {
    warnings.push('未识别到主题，建议在 Markdown 中单独写一个一级标题或首行主题。')
  }
  if (!inclusion.length) {
    warnings.push('未识别到纳入标准，建议使用“纳入标准”标题或“纳入标准：”写法。')
  }
  if (!exclusion.length) {
    warnings.push('未识别到排除标准，建议使用“排除标准”标题或“排除标准：”写法。')
  }

  return {
    topic,
    inclusion,
    exclusion,
    matched: Boolean(topic || inclusion.length || exclusion.length),
    warnings
  }
}
