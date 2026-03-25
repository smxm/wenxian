import type { StrategyPlan } from '@/types/api'

export function strategyPlanToCriteriaMarkdown(
  plan: Pick<StrategyPlan, 'screening_topic' | 'inclusion' | 'exclusion'> & { topic?: string }
) {
  const lines = [
    `# 研究主题`,
    '',
    plan.screening_topic || plan.topic,
    '',
    `# 纳入标准`,
    '',
    ...plan.inclusion.map((item) => `- ${item}`),
    '',
    `# 排除标准`,
    '',
    ...plan.exclusion.map((item) => `- ${item}`)
  ]
  return lines.join('\n').trim()
}

export function describeStrategyDatabases(plan: StrategyPlan) {
  return plan.search_blocks.map((block) => block.database).join(', ')
}
