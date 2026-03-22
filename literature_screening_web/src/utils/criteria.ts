export interface ParsedCriteriaDraft {
  topic: string
  inclusion: string[]
  exclusion: string[]
  matched: boolean
  warnings: string[]
}

type SectionType = 'inclusion' | 'exclusion' | null

function normalizeLine(input: string) {
  return input.replace(/\u3000/g, ' ').replace(/\s+/g, ' ').trim()
}

function stripMarkdownDecoration(input: string) {
  return input
    .replace(/^\s*#+\s*/, '')
    .replace(/^\s*[-*+]\s+/, '')
    .replace(/^\s*\d+[.)、]\s+/, '')
    .replace(/\*\*/g, '')
    .replace(/__/g, '')
    .replace(/`/g, '')
    .trim()
}

function isBulletLine(line: string) {
  return /^[-*+]\s+/.test(line) || /^\d+[.)、]\s+/.test(line)
}

function stripBullet(line: string) {
  return stripMarkdownDecoration(line)
}

function normalizeLabel(line: string) {
  return stripMarkdownDecoration(line)
    .replace(/[()（）]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function detectSection(line: string): SectionType {
  const normalized = normalizeLabel(line).toLowerCase()
  if (/(^| )纳入标准( |$)|(^| )inclusion criteria( |$)|(^| )inclusion( |$)/i.test(normalized)) {
    return 'inclusion'
  }
  if (/(^| )排除标准( |$)|(^| )exclusion criteria( |$)|(^| )exclusion( |$)/i.test(normalized)) {
    return 'exclusion'
  }
  return null
}

function splitInlineCriteria(value: string) {
  return value
    .split(/[；;]+/)
    .map((item) => stripMarkdownDecoration(item))
    .filter(Boolean)
}

function parseInlineSection(line: string): { section: SectionType; items: string[] } | null {
  const cleaned = stripMarkdownDecoration(line)
  const normalized = normalizeLabel(cleaned)

  const inclusionMatch = normalized.match(/^(纳入标准|inclusion criteria|inclusion)\s*[:：]\s*(.+)$/i)
  if (inclusionMatch) {
    return { section: 'inclusion', items: splitInlineCriteria(inclusionMatch[2]) }
  }

  const exclusionMatch = normalized.match(/^(排除标准|exclusion criteria|exclusion)\s*[:：]\s*(.+)$/i)
  if (exclusionMatch) {
    return { section: 'exclusion', items: splitInlineCriteria(exclusionMatch[2]) }
  }

  return null
}

function looksLikeSectionHeader(line: string) {
  const normalized = normalizeLabel(line)
  return /^(纳入标准|排除标准|inclusion criteria|exclusion criteria|inclusion|exclusion)\s*[:：]?$/i.test(normalized)
}

function isMeaningfulTopicLine(line: string) {
  const normalized = normalizeLabel(line)
  if (!normalized) return false
  if (/^(role|task|step \d+|input data)$/i.test(normalized)) return false
  if (/^(你是一位|我将提供|请根据|请按以下|重要指令)/.test(normalized)) return false
  if (detectSection(normalized)) return false
  return true
}

export function parseCriteriaMarkdown(markdown: string): ParsedCriteriaDraft {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n').map(normalizeLine)
  let topic = ''
  let section: SectionType = null
  const inclusion: string[] = []
  const exclusion: string[] = []
  const warnings: string[] = []

  for (const rawLine of lines) {
    if (!rawLine) continue

    const line = rawLine.trim()
    const inlineSection = parseInlineSection(line)
    if (inlineSection) {
      section = inlineSection.section
      if (section === 'inclusion') inclusion.push(...inlineSection.items)
      if (section === 'exclusion') exclusion.push(...inlineSection.items)
      continue
    }

    const sectionType = detectSection(line)
    if (sectionType && looksLikeSectionHeader(line)) {
      section = sectionType
      continue
    }

    if (line.startsWith('#')) {
      const heading = stripMarkdownDecoration(line)
      const headingSection = detectSection(heading)
      if (headingSection) {
        section = headingSection
        continue
      }
      if (!topic && isMeaningfulTopicLine(heading)) {
        topic = heading
      }
      continue
    }

    if (!topic && !isBulletLine(line) && isMeaningfulTopicLine(line)) {
      topic = stripMarkdownDecoration(line)
      continue
    }

    if (sectionType) {
      section = sectionType
      continue
    }

    if (isBulletLine(line)) {
      const value = stripBullet(line)
      if (!value) continue
      if (section === 'inclusion') {
        inclusion.push(value)
      } else if (section === 'exclusion') {
        exclusion.push(value)
      }
    }
  }

  if (!topic) {
    warnings.push('未识别到主题，建议在 Markdown 中单独写一个一级标题或明确的主题行。')
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
