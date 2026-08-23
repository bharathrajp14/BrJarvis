import type { Task, TimelineEvent } from './domain';

export type UiEvent =
  | { type: 'task.updated'; sequence?: number; task: Task }
  | { type: 'timeline.appended'; sequence?: number; event: TimelineEvent }
  | { type: 'approval.created'; sequence?: number }
  | { type: 'connection.ready'; sequence?: number }
  | { type: 'connection.error'; sequence?: number; message: string }
  | { type: string; sequence?: number; event_id?: string; task_id?: string; payload?: Record<string, unknown>; [key: string]: unknown };
