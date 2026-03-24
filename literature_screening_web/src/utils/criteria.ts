export interface ParsedCriteriaDraft {
  topic: string
  inclusion: string[]
  exclusion: string[]
  matched: boolean
  warnings: string[]
}

type SectionType = 'inclusion' | 'exclusion' | null

const TOPIC_PATTERNS = [
  /关于\s*[“"'《](.+?)[”"'》]\s*的论文/,
  /研究主题\s*[:：]\s*(.+)/i,
  /论文主题\s*[:：]\s*(.+)/i,
  /主题\s*[:：]\s*(.+)/i
]

const TOPIC_STOP_WORDS = [
  'role',
  'task',
  'step 1',
  'step 2',
  'input data',
  '格式化输出',
  '情况 a',
  '情况 b',
  '核心总结',
  '深度分析',
  '参考价值'
]

function normalizeLine(input: string) {
  return input.replace(/\u3000/g, ' ').replace(/\s+/g, ' ').trim()
}

function stripMarkdownDecoration(input: string) {
  return input
    .replace(/^\s*#+\s*/, '')
    .replace(/^\s*[-*+]\s+/, '')
    .replace(/^\s*\d+[.)、]\s+/, '')
    .replace(/^\s*[（(]?\d+[）)]\s+/, '')
    .replace(/\*\*/g, '')
    .replace(/__/g, '')
    .replace(/`/g, '')
    .trim()
}

function normalizeLabel(input: string) {
  return stripMarkdownDecoration(input)
    .replace(/[()（）]/g, ' ')
    .replace(/[：:]/g, ' : ')
    .replace(/\s+/g, ' ')
    .trim()
}

function isBulletLine(line: string) {
  return /^[-*+]\s+/.test(line) || /^\d+[.)、]\s+/.test(line) || /^[（(]?\d+[）)]\s+/.test(line)
}

function detectSection(line: string): SectionType {
  const normalized = normalizeLabel(line).toLowerCase()
  if (/(^| )(纳入标准|inclusion criteria|inclusion)( |$)/i.test(normalized)) {
    return 'inclusion'
  }
  if (/(^| )(排除标准|exclusion criteria|exclusion)( |$)/i.test(normalized)) {
    return 'exclusion'
  }
  return null
}

function looksLikeSectionHeader(line: string) {
  const normalized = normalizeLabel(line)
  return /^(纳入标准(\s+inclusion criteria)?|排除标准(\s+exclusion criteria)?|inclusion criteria|exclusion criteria|inclusion|exclusion)\s*[:：]?$/i.test(normalized)
}

function splitInlineCriteria(value: string) {
  return value
    .split(/[;；]/)
    .map((item) => stripMarkdownDecoration(item))
    .filter(Boolean)
}

function parseInlineSection(line: string): { section: SectionType; items: string[] } | null {
  const cleaned = normalizeLabel(line)
  const inclusionMatch = cleaned.match(/^(纳入标准(\s+inclusion criteria)?|inclusion criteria|inclusion)\s*[:：]\s*(.*)$/i)
  if (inclusionMatch) {
    return { section: 'inclusion', items: splitInlineCriteria(inclusionMatch[inclusionMatch.length - 1] || '') }
  }

  const exclusionMatch = cleaned.match(/^(排除标准(\s+exclusion criteria)?|exclusion criteria|exclusion)\s*[:：]\s*(.*)$/i)
  if (exclusionMatch) {
    return { section: 'exclusion', items: splitInlineCriteria(exclusionMatch[exclusionMatch.length - 1] || '') }
  }

  return null
}

function isBoundaryLine(line: string) {
  const normalized = normalizeLabel(line).toLowerCase()
  if (!normalized) return false

  return [
    /^step\s*\d+/,
    /^情况\s*[ab]/,
    /^case\s*[ab]/,
    /^input data$/,
    /^格式化输出$/,
    /^输出格式$/,
    /^核心总结$/,
    /^深度分析$/,
    /^参考价值$/,
    /^仅输出一行文字/,
    /^请按以下结构输出/,
    /^根据判读结果/,
    /^重要指令/,
    /^task$/,
    /^role$/
  ].some((pattern) => pattern.test(normalized))
}

function isInstructionLine(line: string) {
  const normalized = normalizeLabel(line)
  if (!normalized) return true

  return [
    /^你是一位/,
    /^我将提供/,
    /^请根据以下标准判断/,
    /^请你逐一阅读/,
    /^根据判读结果/,
    /^绝对禁止/,
    /^只输出纯文本/,
    /^在此处粘贴/,
    /^输出在markdown代码框内/,
    /^不要使用任何形式/
  ].some((pattern) => pattern.test(normalized))
}

function cleanupTopic(value: string) {
  return value
    .replace(/^关于\s*/, '')
    .replace(/[。；;]+$/, '')
    .trim()
}

function extractTopic(markdown: string, lines: string[]) {
  for (const pattern of TOPIC_PATTERNS) {
    const match = markdown.match(pattern)
    if (match?.[1]) return cleanupTopic(match[1])
  }

  for (const rawLine of lines) {
    const line = normalizeLabel(rawLine)
    if (!line) continue
    const lower = line.toLowerCase()
    if (TOPIC_STOP_WORDS.some((word) => lower.includes(word))) continue
    if (/^(你是一位|我正在撰写一篇关于)/.test(line)) {
      for (const pattern of TOPIC_PATTERNS) {
        const match = line.match(pattern)
        if (match?.[1]) return cleanupTopic(match[1])
      }
    }
  }

  return ''
}

function pushUnique(target: string[], value: string) {
  const cleaned = stripMarkdownDecoration(value)
    .replace(/^核心要素（满足其一即可）$/, '')
    .replace(/^排除标准 \(exclusion criteria\)$/i, '')
    .replace(/^纳入标准 \(inclusion criteria\)$/i, '')
    .trim()
  if (!cleaned) return
  if (!target.includes(cleaned)) target.push(cleaned)
}

export function parseCriteriaMarkdown(markdown: string): ParsedCriteriaDraft {
  const normalizedMarkdown = markdown.replace(/\r\n/g, '\n')
  const lines = normalizedMarkdown.split('\n').map(normalizeLine)
  const topic = extractTopic(normalizedMarkdown, lines)
  let section: SectionType = null
  const inclusion: string[] = []
  const exclusion: string[] = []
  const warnings: string[] = []

  for (const rawLine of lines) {
    if (!rawLine) continue

    const line = rawLine.trim()

    if (isBoundaryLine(line)) {
      section = null
      continue
    }

    const inlineSection = parseInlineSection(line)
    if (inlineSection) {
      section = inlineSection.section
      const target = section === 'inclusion' ? inclusion : exclusion
      inlineSection.items.forEach((item) => pushUnique(target, item))
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
      section = headingSection ?? null
      continue
    }

    if (!section) continue
    if (isInstructionLine(line)) continue

    if (isBulletLine(line)) {
      const target = section === 'inclusion' ? inclusion : exclusion
      pushUnique(target, line)
      continue
    }

    const plainLine = stripMarkdownDecoration(line)
    if (/^[（(]?(如|例如)/.test(plainLine)) continue
    if (/^(情况\s*[ab]|case\s*[ab])/i.test(plainLine)) continue

    if (plainLine && !/^#/.test(plainLine)) {
      const target = section === 'inclusion' ? inclusion : exclusion
      pushUnique(target, plainLine)
    }
  }

  if (!topic) {
    warnings.push('未识别到研究主题，建议在 Role 中保留“关于《主题》”或单独写一行“研究主题：...”')
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
