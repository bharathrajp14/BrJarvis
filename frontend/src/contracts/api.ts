import type { ExecutionMode, Task, ViewId } from './domain';

export interface ApiMeta {
  requestId?: string;
  nextCursor?: string | null;
}

export interface ApiEnvelope<T> {
  data: T;
  meta?: ApiMeta;
  error?: null;
}

export interface ApiErrorShape {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  requestId?: string;
}

export interface CommandRequest {
  goal: string;
  mode: ExecutionMode;
  projectId?: string;
  privacy: 'balanced' | 'local_only';
  idempotencyKey: string;
}

export interface CommandResponse {
  task: Task;
  acknowledgement: string;
  pathReason: string;
}

export interface NavigationItem {
  id: ViewId;
  label: string;
  eyebrow: string;
  description: string;
}
