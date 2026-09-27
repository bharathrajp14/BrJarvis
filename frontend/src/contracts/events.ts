import type { Task, TimelineEvent } from './domain';

export type UiEvent =
  | { type: 'task.updated'; task: Task; event_id?: string }
  | { type: 'timeline.appended'; event: TimelineEvent; event_id?: string }
  | { type: 'approval.created'; event_id?: string }
  | { type: 'connection.ready'; event_id?: string }
  | { type: 'connection.error'; message: string; event_id?: string }
  | { type: string; event_id?: string; task_id?: string; payload?: Record<string, unknown>; [key: string]: unknown };
