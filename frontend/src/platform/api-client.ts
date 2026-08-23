import type { ApiEnvelope, ApiErrorShape, CommandRequest, CommandResponse } from '../contracts/api';
import type { AppSnapshot, Artifact, Capability, Task, TaskStatus } from '../contracts/domain';
import { emptySnapshot } from './empty-state';

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

function normalizeApproval(raw: Record<string, unknown>, taskId: string) {
  const details = (raw.details ?? {}) as Record<string, unknown>;
  const risk = String(raw.risk_level ?? raw.risk ?? 'medium').toLowerCase();
  return {
    id: String(raw.request_id ?? raw.id ?? `${taskId}-approval`),
    taskId,
    action: String(raw.description ?? raw.action ?? 'Approval required'),
    target: String(details.target ?? details.resource ?? 'Protected operation'),
    risk: (risk === 'high' || risk === 'critical' ? 'high' : risk === 'low' ? 'low' : 'medium') as 'low' | 'medium' | 'high',
    scope: String(details.scope ?? 'Runtime policy'),
    reason: String(details.reason ?? raw.description ?? 'The task is waiting for operator approval.'),
    expiresIn: String(raw.expires_in ?? '—'),
  };
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
    try {
      const [taskResult, artifactResult, healthResult, connectorResult, projectResult, memoryResult, notificationResult] = await Promise.allSettled([
        this.request<{ tasks?: Record<string, unknown>[]; total?: number }>('/api/agent/tasks?limit=50', { signal }),
        this.request<{ artifacts?: Record<string, unknown>[]; total?: number }>('/api/artifacts', { signal }),
        this.request<Record<string, unknown>>('/health', { signal }),
        this.request<Record<string, unknown>>('/api/v1/connectors', { signal }),
        this.request<{ projects?: Record<string, unknown>[] }>('/api/projects', { signal }),
        this.request<{ memories?: Record<string, unknown>[] }>('/api/memory', { signal }),
        this.request<{ notifications?: Record<string, unknown>[] }>('/api/notifications?limit=20', { signal }),
      ]);
      const rawTasks = taskResult.status === 'fulfilled' && Array.isArray(taskResult.value.tasks) ? taskResult.value.tasks : [];
      const tasks = rawTasks.map(normalizeTask);
      const approvals = rawTasks.flatMap((raw, index) => {
        const taskId = String(raw.task_id ?? raw.id ?? `task-${index + 1}`);
        const rawApprovals = Array.isArray(raw.approvals) ? raw.approvals : raw.approval_request ? [raw.approval_request] : [];
        return rawApprovals.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object')).map((item) => normalizeApproval(item, taskId));
      });
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
        : [];
      const health = healthResult.status === 'fulfilled' ? healthResult.value : {};
      const connectorPayload = connectorResult.status === 'fulfilled' ? connectorResult.value : {};
      const projects = projectResult.status === 'fulfilled' && Array.isArray(projectResult.value.projects) ? projectResult.value.projects : [];
      const memories = memoryResult.status === 'fulfilled' && Array.isArray(memoryResult.value.memories) ? memoryResult.value.memories : [];
      const notifications = notificationResult.status === 'fulfilled' && Array.isArray(notificationResult.value.notifications) ? notificationResult.value.notifications : [];
      const connectorCount = Array.isArray(connectorPayload.connectors) ? connectorPayload.connectors.length : 0;
      const workspace = projects.flatMap((project, projectIndex) => {
        const record = project as Record<string, unknown>;
        return [{ id: String(record.project_id ?? record.id ?? `project-${projectIndex + 1}`), name: String(record.name ?? 'Project'), kind: 'folder' as const, path: String(record.path ?? '/workspace'), detail: String(record.description ?? 'Live project') }];
      });
      const timeline = notifications.map((notification, index) => {
        const record = notification as Record<string, unknown>;
        const severity = String(record.severity ?? 'info').toLowerCase();
        return {
          id: String(record.notification_id ?? record.id ?? `notification-${index + 1}`),
          time: String(record.created_at ?? record.created ?? 'Recently'),
          label: String(record.title ?? 'Notification'),
          detail: String(record.message ?? ''),
          tone: severity === 'error' || severity === 'critical' ? 'warning' : severity === 'success' ? 'success' : severity === 'warning' ? 'accent' : 'neutral',
        } as const;
      });
      const capabilities: Capability[] = [
        { id: 'runtime', label: 'Core runtime', state: health.status === 'online' ? 'healthy' : 'degraded', detail: health.status === 'online' ? 'Task orchestration online' : 'Runtime health needs attention', latency: 'Live' },
        { id: 'workspace', label: 'Workspace projects', state: projectResult.status === 'fulfilled' ? 'healthy' : 'unavailable', detail: projectResult.status === 'fulfilled' ? `${projects.length} project${projects.length === 1 ? '' : 's'} returned` : 'Workspace API unavailable', latency: 'Live' },
        { id: 'provider', label: 'Reasoning gateway', state: health.backend ? 'healthy' : 'unavailable', detail: health.backend ? 'Provider status reported by runtime' : 'Provider status unavailable', latency: String(health.backend ?? '—') },
        { id: 'connectors', label: 'Connectors', state: connectorCount > 0 ? 'healthy' : 'degraded', detail: `${connectorCount} connector${connectorCount === 1 ? '' : 's'} discovered`, latency: 'Live' },
      ];
      return {
        ...structuredClone(emptySnapshot),
        tasks,
        approvals,
        artifacts,
        capabilities,
        workspace,
        memoryCount: memories.length,
        timeline,
        activeTaskId: tasks[0]?.id ?? '',
        connection: taskResult.status === 'fulfilled' || healthResult.status === 'fulfilled' ? 'connected' : 'offline',
      };
    } catch {
      const offline = structuredClone(emptySnapshot);
      offline.connection = 'offline';
      offline.capabilities = [{ id: 'runtime', label: 'Core runtime', state: 'offline', detail: 'Live backend unavailable', latency: '—' }];
      return offline;
    }
  }

  async resolveApproval(taskId: string, approvalId: string, approved: boolean, signal?: AbortSignal): Promise<void> {
    await this.request(`/api/agent/tasks/${encodeURIComponent(taskId)}/approve`, {
      method: 'POST',
      body: JSON.stringify({ request_id: approvalId, approved }),
      signal,
      headers: { 'Idempotency-Key': key() },
    });
  }

  async createTask(command: CommandRequest, signal?: AbortSignal): Promise<CommandResponse> {
    const response = await this.request<Record<string, unknown>>('/api/agent/tasks', {
      method: 'POST',
      body: JSON.stringify({ goal: command.goal, active_devices: [] }),
      signal,
      headers: { 'Idempotency-Key': command.idempotencyKey },
    });
    const taskId = String(response.task_id ?? response.id ?? `task-${key()}`);
    let taskRecord: Record<string, unknown> = { task_id: taskId, goal: command.goal };
    try {
      taskRecord = await this.request<Record<string, unknown>>(`/api/agent/tasks/${encodeURIComponent(taskId)}`, { signal });
    } catch {
      // The create response is still authoritative enough to show a queued row;
      // do not invent progress or completion state while the detail read settles.
    }
    const task = normalizeTask(taskRecord, 0);
    return { task, acknowledgement: 'Command accepted by the BRJARVIS runtime. The task is now being planned.', pathReason: `${command.mode} mode requested; backend execution policy remains authoritative.` };
  }
}

export const apiClient = new ApiClient();
