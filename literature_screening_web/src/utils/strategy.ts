import type { StrategyPlan } from '@/types/api'

export function buildCriteriaMarkdown(topic: string, inclusion: string[], exclusion: string[]) {
  const lines = [
    `# 研究主题`,
    '',
    topic,
    '',
    `# 纳入标准`,
    '',
    ...inclusion.filter(Boolean).map((item) => `- ${item}`),
    '',
    `# 排除标准`,
    '',
    ...exclusion.filter(Boolean).map((item) => `- ${item}`)
  ]
  return lines.join('\n').trim()
}

export function strategyPlanToCriteriaMarkdown(
  plan: Pick<StrategyPlan, 'screening_topic' | 'inclusion' | 'exclusion'> & { topic?: string }
) {
  return buildCriteriaMarkdown(plan.screening_topic || plan.topic || '', plan.inclusion, plan.exclusion)
}

export function describeStrategyDatabases(plan: StrategyPlan) {
  return plan.search_blocks.map((block) => block.database).join(', ')
}
