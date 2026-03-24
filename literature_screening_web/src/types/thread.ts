import type { TaskKind, TaskStatus } from '@/types/api'

export interface ThreadMetric {
  label: string
  value: string | number
}

export interface ThreadAction {
  id: string
  label: string
  kind: 'route' | 'download'
  to?: string
  href?: string
  emphasis?: 'primary' | 'secondary' | 'ghost'
  disabled?: boolean
}

export interface ThreadMessage {
  id: string
  taskId: string
  kind: TaskKind
  status: TaskStatus
  title: string
  eyebrow: string
  body: string
  sourceLabel: string
  note?: string
  createdAt: string
  updatedAt: string
  phaseLabel?: string | null
  progressCurrent?: number | null
  progressTotal?: number | null
  progressMessage?: string | null
  metrics: ThreadMetric[]
  actions: ThreadAction[]
}
