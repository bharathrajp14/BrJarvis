import type { ApiEnvelope, ApiErrorShape, CommandRequest, CommandResponse } from '../contracts/api';
import type { AppSnapshot, Artifact, Capability, Task, TaskStatus } from '../contracts/domain';
import { initialSnapshot } from './mock-data';

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId?: string;

  constructor(error: ApiErrorShape, status = 0) {
    super(error.message);
    this.name = 'ApiError';
    this.code = error.code;
    this.status = status;
    this.requestId = error.requestId;
  }
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';
const explicitDemoMode = (import.meta.env.VITE_DEMO_MODE as string | undefined) === 'true';

function key() {
  return globalThis.crypto?.randomUUID?.() ?? `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function taskStatus(value: unknown): TaskStatus {
  const normalized = String(value ?? '').toLowerCase();
  if (normalized.includes('complete') || normalized === 'success') return 'completed';
  if (normalized.includes('fail') || normalized.includes('error')) return 'failed';
  if (normalized.includes('wait') || normalized.includes('approval')) return 'waiting';
  if (normalized.includes('cancel')) return 'cancelled';
  if (normalized.includes('plan')) return 'planning';
  if (normalized.includes('run') || normalized.includes('active')) return 'running';
  return 'queued';
}

function normalizeTask(raw: Record<string, unknown>, index: number): Task {
  const id = String(raw.id ?? raw.task_id ?? raw.taskId ?? `task-${index + 1}`);
  const goal = String(raw.goal ?? raw.title ?? raw.name ?? 'Untitled task');
  const progress = Number(raw.progress ?? raw.percent ?? (taskStatus(raw.status) === 'completed' ? 100 : 0));
  const status = taskStatus(raw.status ?? raw.state);
  return {
    id,
    title: goal,
    status,
    mode: raw.mode === 'fast' || raw.mode === 'deep' ? raw.mode : 'smart',
    progress: Math.max(0, Math.min(100, progress)),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? 'Recently'),
    duration: String(raw.duration ?? '—'),
    provider: String(raw.provider ?? raw.backend ?? 'BRJARVIS runtime'),
    summary: String(raw.summary ?? raw.description ?? raw.result ?? 'Task state received from the BRJARVIS runtime.'),
    artifactCount: Number(raw.artifact_count ?? raw.artifactCount ?? 0),
    requiresApproval: Boolean(raw.requires_approval ?? raw.requiresApproval),
    steps: Array.isArray(raw.steps)
      ? raw.steps.map((step, stepIndex) => {
        const record = (step ?? {}) as Record<string, unknown>;
        const stepStatus = String(record.status ?? 'queued').toLowerCase();
        return {
          id: String(record.id ?? `step-${stepIndex + 1}`),
          label: String(record.label ?? record.name ?? `Execution step ${stepIndex + 1}`),
          status: stepStatus.includes('complete') ? 'complete' : stepStatus.includes('run') ? 'active' : stepStatus.includes('block') ? 'blocked' : 'queued',
          detail: record.detail ? String(record.detail) : undefined,
        };
      })
      : [{ id: `${id}-state`, label: 'Runtime state', status: status === 'completed' ? 'complete' : status === 'running' ? 'active' : 'queued', detail: String(raw.status ?? 'queued') }],
  };
}

export class ApiClient {
  constructor(private readonly baseUrl = API_BASE) {}

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set('Accept', 'application/json');
    if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    headers.set('X-Request-ID', key());
    const response = await fetch(`${this.baseUrl}${path}`, { ...init, headers, credentials: 'include' });
    const body = (await response.json().catch(() => ({}))) as ApiEnvelope<T> & { error?: ApiErrorShape };
    if (!response.ok || body.error) {
      throw new ApiError(body.error ?? { code: 'HTTP_ERROR', message: `Request failed with ${response.status}` }, response.status);
    }
    return body.data ?? (body as unknown as T);
  }

  async snapshot(signal?: AbortSignal): Promise<AppSnapshot> {
    if (explicitDemoMode) return structuredClone(initialSnapshot);
    try {
      const [taskResult, artifactResult, healthResult, connectorResult] = await Promise.allSettled([
        this.request<{ tasks?: Record<string, unknown>[]; total?: number }>('/api/agent/tasks?limit=50', { signal }),
        this.request<{ artifacts?: Record<string, unknown>[]; total?: number }>('/api/artifacts', { signal }),
        this.request<Record<string, unknown>>('/health', { signal }),
        this.request<Record<string, unknown>>('/api/v1/connectors', { signal }),
      ]);
      const tasks = taskResult.status === 'fulfilled' && Array.isArray(taskResult.value.tasks)
        ? taskResult.value.tasks.map(normalizeTask)
        : initialSnapshot.tasks;
      const artifacts: Artifact[] = artifactResult.status === 'fulfilled' && Array.isArray(artifactResult.value.artifacts)
        ? artifactResult.value.artifacts.map((raw, index) => ({
          id: String(raw.id ?? raw.artifact_id ?? `artifact-${index + 1}`),
          name: String(raw.name ?? raw.filename ?? 'Untitled artifact'),
          type: String(raw.type ?? raw.mime_type ?? 'Artifact'),
          taskId: String(raw.task_id ?? raw.taskId ?? '—'),
          status: raw.verified ? 'verified' : 'processing',
          size: String(raw.size ?? '—'),
          updatedAt: String(raw.updated_at ?? 'Recently'),
        }))
        : initialSnapshot.artifacts;
      const health = healthResult.status === 'fulfilled' ? healthResult.value : {};
      const connectorPayload = connectorResult.status === 'fulfilled' ? connectorResult.value : {};
      const connectorCount = Array.isArray(connectorPayload.connectors) ? connectorPayload.connectors.length : 0;
      const capabilities: Capability[] = [
        { id: 'runtime', label: 'Core runtime', state: health.status === 'online' ? 'healthy' : 'degraded', detail: health.status === 'online' ? 'Task orchestration online' : 'Runtime health needs attention', latency: 'Live' },
        { id: 'workspace', label: 'Workspace index', state: 'healthy', detail: 'Workspace intelligence available', latency: 'Live' },
        { id: 'provider', label: 'Reasoning gateway', state: 'healthy', detail: 'Provider status available through runtime', latency: String(health.backend ?? '—') },
        { id: 'connectors', label: 'Connectors', state: connectorCount > 0 ? 'healthy' : 'degraded', detail: `${connectorCount} connector${connectorCount === 1 ? '' : 's'} discovered`, latency: 'Live' },
      ];
      return { ...structuredClone(initialSnapshot), tasks, artifacts, capabilities, activeTaskId: tasks[0]?.id ?? initialSnapshot.activeTaskId, connection: 'connected' };
    } catch {
      const fallback = structuredClone(initialSnapshot);
      fallback.connection = 'offline';
      fallback.capabilities = fallback.capabilities.map((capability) => ({ ...capability, state: capability.id === 'runtime' ? 'offline' : 'degraded', detail: 'Live backend unavailable; showing local recovery state' }));
      return fallback;
    }
  }

  async resolveApproval(taskId: string, approvalId: string, approved: boolean, signal?: AbortSignal): Promise<void> {
    if (explicitDemoMode) return;
    await this.request(`/api/agent/tasks/${encodeURIComponent(taskId)}/approve`, {
      method: 'POST',
      body: JSON.stringify({ request_id: approvalId, approved }),
      signal,
      headers: { 'Idempotency-Key': key() },
    });
  }

  async createTask(command: CommandRequest, signal?: AbortSignal): Promise<CommandResponse> {
    if (explicitDemoMode) {
      const task: Task = {
        id: `task-${Math.floor(Math.random() * 9000) + 1000}`,
        title: command.goal,
        status: 'planning',
        mode: command.mode,
        progress: 8,
        updatedAt: 'Just now',
        duration: '00:00',
        provider: command.mode === 'fast' ? 'Deterministic local' : command.mode === 'smart' ? 'Proxy brain' : 'Deep reasoning gateway',
        summary: 'BRJARVIS acknowledged the command and is preparing an execution plan.',
        artifactCount: 0,
        steps: [
          { id: 'plan', label: 'Understand request', status: 'active', detail: 'Classifying intent and constraints' },
          { id: 'context', label: 'Select relevant context', status: 'queued' },
          { id: 'execute', label: 'Execute and verify', status: 'queued' },
        ],
      };
      return { task, acknowledgement: 'Command accepted. BRJARVIS is preparing a verified execution path.', pathReason: `${command.mode} path selected for the requested latency and complexity budget.` };
    }
    const response = await this.request<Record<string, unknown>>('/api/agent/tasks', {
      method: 'POST',
      body: JSON.stringify({ goal: command.goal, active_devices: [] }),
      signal,
      headers: { 'Idempotency-Key': command.idempotencyKey },
    });
    const taskId = String(response.task_id ?? response.id ?? `task-${key()}`);
    const task = normalizeTask({ task_id: taskId, goal: command.goal, status: 'planning', mode: command.mode, progress: 5, provider: 'BRJARVIS runtime' }, 0);
    return { task, acknowledgement: 'Command accepted by the BRJARVIS runtime. The task is now being planned.', pathReason: `${command.mode} mode requested; backend execution policy remains authoritative.` };
  }
}

export const apiClient = new ApiClient();
