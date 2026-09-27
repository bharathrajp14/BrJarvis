import type { ApiEnvelope, ApiErrorShape, CommandRequest, CommandResponse } from '../contracts/api';
import type {
  AppSnapshot,
  Artifact,
  Capability,
  CareerJob,
  CareerProfile,
  ConnectorSummary,
  ContactSummary,
  MemoryEntry,
  PanelHealth,
  SearchResult,
  Task,
  TaskStatus,
} from '../contracts/domain';
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

const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '').replace(/\/$/, '');

function key() {
  return globalThis.crypto?.randomUUID?.() ?? `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? value as Record<string, unknown> : {};
}

function asBoolean(value: unknown): boolean {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (['true', '1', 'yes', 'on', 'verified', 'success'].includes(normalized)) return true;
    if (['false', '0', 'no', 'off', '', 'unverified'].includes(normalized)) return false;
  }
  return Boolean(value);
}

function asText(value: unknown, fallback = ''): string {
  if (value === null || value === undefined) return fallback;
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return value.map((item) => asText(item)).filter(Boolean).join(', ');
  const valueRecord = record(value);
  return String(valueRecord.summary ?? valueRecord.message ?? valueRecord.result ?? valueRecord.content ?? fallback);
}

function bytes(value: unknown): string {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount < 0) return 'Size unavailable';
  if (amount < 1024) return `${amount} B`;
  if (amount < 1024 ** 2) return `${(amount / 1024).toFixed(1)} KB`;
  if (amount < 1024 ** 3) return `${(amount / 1024 ** 2).toFixed(1)} MB`;
  return `${(amount / 1024 ** 3).toFixed(1)} GB`;
}

function taskStatus(value: unknown): TaskStatus {
  const normalized = String(value ?? '').toLowerCase();
  if (normalized.includes('complete') || normalized.includes('verified') || normalized === 'success') return 'completed';
  if (normalized.includes('fail') || normalized.includes('error')) return 'failed';
  if (normalized.includes('retry') || normalized.includes('recover')) return 'retrying';
  if (normalized.includes('wait') || normalized.includes('approval') || normalized.includes('pause')) return 'waiting';
  if (normalized.includes('cancel')) return 'cancelled';
  if (normalized.includes('plan')) return 'planning';
  if (normalized.includes('run') || normalized.includes('active') || normalized.includes('execut')) return 'running';
  return 'queued';
}

function normalizeApproval(raw: Record<string, unknown>, taskId: string) {
  const details = record(raw.details);
  const risk = String(raw.risk_level ?? raw.risk ?? 'medium').toLowerCase();
  return {
    id: String(raw.request_id ?? raw.id ?? `${taskId}-approval`),
    taskId,
    action: String(raw.description ?? raw.action ?? raw.tool_name ?? 'Approval required'),
    target: String(details.target ?? details.resource ?? raw.target ?? 'Protected operation'),
    risk: (risk === 'high' || risk === 'critical' ? 'high' : risk === 'low' ? 'low' : 'medium') as 'low' | 'medium' | 'high',
    scope: String(details.scope ?? raw.permission ?? 'Runtime policy'),
    reason: String(details.reason ?? raw.reason ?? raw.description ?? 'The task is waiting for operator approval.'),
    expiresIn: String(raw.expires_in ?? raw.timeout ?? 'Policy controlled'),
  };
}

export function normalizeTask(raw: Record<string, unknown>, index: number): Task {
  const id = String(raw.task_id ?? raw.id ?? raw.taskId ?? `task-${index + 1}`);
  const goal = String(raw.goal ?? raw.title ?? raw.name ?? 'Untitled task');
  const status = taskStatus(raw.status ?? raw.state ?? raw.current_phase);
  const planned = Array.isArray(raw.planned_steps) ? raw.planned_steps : Array.isArray(raw.steps) ? raw.steps : [];
  const completed = Array.isArray(raw.completed_steps) ? raw.completed_steps : [];
  const completedKeys = new Set(completed.flatMap((item) => {
    const itemRecord = record(item);
    return [itemRecord.id, itemRecord.step_id, itemRecord.name, itemRecord.label, typeof item === 'string' ? item : undefined]
      .filter((value): value is string | number => value !== undefined && value !== null)
      .map(String);
  }));
  const current = raw.current_step;
  const currentRecord = record(current);
  const currentIndex = typeof current === 'number' ? current : Number(currentRecord.index ?? currentRecord.position ?? -1);
  const steps = planned.map((step, stepIndex) => {
    const stepRecord = record(step);
    const stepId = String(stepRecord.id ?? stepRecord.step_id ?? `step-${stepIndex + 1}`);
    const label = String(stepRecord.label ?? stepRecord.name ?? stepRecord.description ?? (typeof step === 'string' ? step : `Execution step ${stepIndex + 1}`));
    const explicitStatus = String(stepRecord.status ?? '').toLowerCase();
    const isComplete = explicitStatus.includes('complete') || completedKeys.has(stepId) || completedKeys.has(label) || stepIndex < completed.length;
    const isActive = explicitStatus.includes('run') || explicitStatus.includes('active') || currentIndex === stepIndex || String(currentRecord.id ?? currentRecord.step_id ?? current ?? '') === stepId;
    const isBlocked = explicitStatus.includes('block') || explicitStatus.includes('fail');
    return {
      id: stepId,
      label,
      status: isComplete ? 'complete' as const : isBlocked ? 'blocked' as const : isActive ? 'active' as const : 'queued' as const,
      detail: asText(stepRecord.detail ?? stepRecord.result ?? stepRecord.description, undefined),
    };
  });
  if (!steps.length) {
    steps.push({
      id: `${id}-state`,
      label: String(raw.current_phase ?? 'Runtime state'),
      status: status === 'completed' ? 'complete' : status === 'running' || status === 'planning' || status === 'retrying' ? 'active' : status === 'failed' ? 'blocked' : 'queued',
      detail: String(raw.status ?? 'queued'),
    });
  }
  const explicitProgress = Number(raw.progress ?? raw.percent);
  const computedProgress = status === 'completed' ? 100 : planned.length ? (completed.length / planned.length) * 100 : 0;
  const artifacts = Array.isArray(raw.artifacts) ? raw.artifacts : [];
  const approval = record(raw.approval_request);
  const finalReport = raw.final_report ?? raw.summary ?? raw.description ?? raw.result;
  return {
    id,
    title: goal,
    status,
    mode: raw.mode === 'fast' || raw.mode === 'deep' ? raw.mode : 'smart',
    progress: Math.max(0, Math.min(100, Number.isFinite(explicitProgress) ? explicitProgress : computedProgress)),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? raw.created_at ?? 'Recently'),
    duration: String(raw.duration ?? raw.elapsed ?? '—'),
    provider: String(raw.provider ?? raw.backend ?? raw.model ?? 'BRJARVIS runtime'),
    summary: asText(finalReport, 'Task state received from the BRJARVIS runtime.'),
    phase: String(raw.current_phase ?? ''),
    artifactCount: Number(raw.artifact_count ?? raw.artifactCount ?? artifacts.length),
    requiresApproval: Object.keys(approval).length > 0 || asBoolean(raw.requires_approval ?? raw.requiresApproval),
    steps,
  };
}

function panelHealth(result: PromiseSettledResult<unknown>, hasItems: boolean, label: string): PanelHealth {
  if (result.status === 'rejected') {
    const message = result.reason instanceof Error ? result.reason.message : `${label} could not be loaded.`;
    return { state: 'error', message };
  }
  return { state: hasItems ? 'ready' : 'empty' };
}

export class ApiClient {
  constructor(private readonly baseUrl = API_BASE) {}

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set('Accept', 'application/json');
    if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    headers.set('X-Request-ID', key());
    const response = await fetch(`${this.baseUrl}${path}`, { ...init, headers, credentials: 'include' });
    const body = await response.json().catch(() => ({})) as ApiEnvelope<T> & { error?: ApiErrorShape; detail?: unknown };
    if (!response.ok || body.error) {
      const detail = Array.isArray(body.detail) ? body.detail.map((item) => asText(record(item).msg ?? item)).join('; ') : asText(body.detail);
      throw new ApiError(body.error ?? { code: `HTTP_${response.status}`, message: detail || `Request failed with ${response.status}` }, response.status);
    }
    return body.data ?? (body as unknown as T);
  }

  async snapshot(signal?: AbortSignal): Promise<AppSnapshot> {
    const results = await Promise.allSettled([
      this.request<{ tasks?: Record<string, unknown>[] }>('/api/agent/tasks?limit=50', { signal }),
      this.request<{ artifacts?: Record<string, unknown>[] }>('/api/artifacts?limit=100', { signal }),
      this.request<Record<string, unknown>>('/health', { signal }),
      this.request<Record<string, unknown>>('/api/status', { signal }),
      this.request<Record<string, unknown>>('/api/v1/connectors', { signal }),
      this.request<{ projects?: Record<string, unknown>[] }>('/api/projects', { signal }),
      this.request<{ memories?: Record<string, unknown>[] }>('/api/memory', { signal }),
      this.request<{ notifications?: Record<string, unknown>[]; unread_count?: number }>('/api/notifications?limit=30', { signal }),
      this.request<{ profile?: Record<string, unknown>; validation?: Record<string, unknown> }>('/api/career/profile', { signal }),
      this.request<{ contacts?: Record<string, unknown>[] }>('/api/contacts', { signal }),
    ]);
    const [taskResult, artifactResult, healthResult, statusResult, connectorResult, projectResult, memoryResult, notificationResult, careerResult, contactResult] = results;
    const rawTasks = taskResult.status === 'fulfilled' && Array.isArray(taskResult.value.tasks) ? taskResult.value.tasks : [];
    const tasks = rawTasks.map(normalizeTask);
    const approvals = rawTasks.flatMap((raw, index) => {
      const taskId = String(raw.task_id ?? raw.id ?? `task-${index + 1}`);
      const currentApproval = record(raw.approval_request);
      if (Object.keys(currentApproval).length) return [normalizeApproval(currentApproval, taskId)];
      const historical = Array.isArray(raw.approvals) ? raw.approvals : [];
      return historical
        .filter((item) => {
          const itemRecord = record(item);
          const state = String(itemRecord.status ?? itemRecord.state ?? 'pending').toLowerCase();
          return !['approved', 'rejected', 'resolved', 'expired'].includes(state);
        })
        .map((item) => normalizeApproval(record(item), taskId));
    });
    const rawArtifacts = artifactResult.status === 'fulfilled' && Array.isArray(artifactResult.value.artifacts) ? artifactResult.value.artifacts : [];
    const artifacts: Artifact[] = rawArtifacts.map((raw, index) => {
      const verification = String(raw.verification_status ?? raw.status ?? '').toLowerCase();
      const artifactStatus: Artifact['status'] = verification.includes('verified') || asBoolean(raw.verified)
        ? 'verified'
        : verification.includes('fail') || verification.includes('reject')
          ? 'failed'
          : verification.includes('review') || verification.includes('pending')
            ? 'needs_review'
            : 'processing';
      const id = String(raw.artifact_id ?? raw.id ?? `artifact-${index + 1}`);
      return {
        id,
        name: String(raw.filename ?? raw.name ?? 'Untitled artifact'),
        type: String(raw.mime_type ?? raw.type ?? 'Artifact'),
        taskId: String(raw.task_id ?? raw.taskId ?? 'Unlinked'),
        status: artifactStatus,
        size: bytes(raw.file_size ?? raw.size),
        updatedAt: String(raw.updated_at ?? raw.created_at ?? 'Recently'),
        downloadUrl: `${this.baseUrl}/api/artifacts/${encodeURIComponent(id)}/download`,
      };
    });
    const health = healthResult.status === 'fulfilled' ? healthResult.value : {};
    const runtimeStatus = statusResult.status === 'fulfilled' ? statusResult.value : {};
    const connectorPayload = connectorResult.status === 'fulfilled' ? connectorResult.value : {};
    const connectorRecords = Array.isArray(connectorPayload.connectors) ? connectorPayload.connectors : [];
    const connectors: ConnectorSummary[] = connectorRecords.map((connector, index) => {
      const item = record(connector);
      return {
        id: String(item.id ?? `connector-${index + 1}`),
        name: String(item.name ?? item.id ?? 'Connector'),
        description: String(item.description ?? item.desc ?? ''),
        status: String(item.status ?? (asBoolean(item.configured) ? 'CONNECTED' : 'NOT CONFIGURED')),
        configured: asBoolean(item.configured),
        requiresAuth: asBoolean(item.requires_auth ?? item.requiresAuth),
        authHint: String(item.auth_hint ?? ''),
        category: String(item.category ?? 'integration'),
        tools: Array.isArray(item.tools) ? item.tools.map(String) : [],
      };
    });
    const projects = projectResult.status === 'fulfilled' && Array.isArray(projectResult.value.projects) ? projectResult.value.projects : [];
    const workspace = projects.flatMap((project, projectIndex) => {
      const item = record(project);
      const projectId = String(item.project_id ?? item.id ?? `project-${projectIndex + 1}`);
      const projectEntry = {
        id: projectId,
        name: String(item.name ?? 'Project'),
        kind: 'folder' as const,
        path: `Project / ${String(item.name ?? projectId)}`,
        detail: String(item.description ?? 'Project workspace'),
        projectId,
      };
      const files = Array.isArray(item.files) ? item.files : [];
      return [projectEntry, ...files.map((file, fileIndex) => {
        const fileItem = record(file);
        const fileId = String(fileItem.file_id ?? fileItem.id ?? `${projectId}-file-${fileIndex + 1}`);
        return {
          id: fileId,
          name: String(fileItem.filename ?? fileItem.name ?? 'File'),
          kind: 'file' as const,
          path: `${projectEntry.path} / ${String(fileItem.filename ?? fileItem.name ?? 'File')}`,
          detail: bytes(fileItem.file_size ?? fileItem.size),
          projectId,
          fileId,
        };
      })];
    });
    const rawMemories = memoryResult.status === 'fulfilled' && Array.isArray(memoryResult.value.memories) ? memoryResult.value.memories : [];
    const memories: MemoryEntry[] = rawMemories.map((memory, index) => {
      const item = record(memory);
      return {
        id: String(item.id ?? item.memory_id ?? item.name ?? `memory-${index + 1}`),
        name: String(item.name ?? item.key ?? `Memory ${index + 1}`),
        scope: String(item.scope ?? 'user'),
        content: String(item.content ?? item.value ?? ''),
        updatedAt: String(item.updated_at ?? item.created ?? item.created_at ?? '—'),
      };
    });
    const notificationPayload = notificationResult.status === 'fulfilled' ? notificationResult.value : {};
    const rawNotifications = Array.isArray(notificationPayload.notifications) ? notificationPayload.notifications : [];
    const timeline = rawNotifications.map((notification, index) => {
      const item = record(notification);
      const severity = String(item.severity ?? 'info').toLowerCase();
      return {
        id: String(item.notification_id ?? item.id ?? `notification-${index + 1}`),
        time: String(item.created_at ?? item.created ?? 'Recently'),
        label: String(item.title ?? 'Notification'),
        detail: String(item.message ?? ''),
        tone: severity === 'error' || severity === 'critical' ? 'warning' as const : severity === 'success' ? 'success' as const : severity === 'warning' ? 'accent' as const : 'neutral' as const,
        read: asBoolean(item.is_read),
        category: String(item.category ?? 'system'),
      };
    });
    const rawProfile = careerResult.status === 'fulfilled' ? careerResult.value.profile : undefined;
    const validation = careerResult.status === 'fulfilled' ? record(careerResult.value.validation) : {};
    const contact = record(rawProfile?.contact);
    const skillSource = rawProfile?.skills;
    const normalizedSkills = Array.isArray(skillSource)
      ? skillSource.flatMap((group) => {
        if (typeof group === 'string') return [group];
        const groupRecord = record(group);
        return Array.isArray(groupRecord.skills) ? groupRecord.skills.map(String) : [asText(groupRecord.name ?? groupRecord.label)].filter(Boolean);
      })
      : Object.values(record(skillSource)).flatMap((value) => Array.isArray(value) ? value.map(String) : value ? [String(value)] : []);
    const completeness = Number(validation.completeness ?? validation.completion_percent ?? rawProfile?.completeness ?? rawProfile?.completion_percent);
    const career: CareerProfile | null = rawProfile ? {
      name: String(rawProfile.name ?? rawProfile.full_name ?? contact.full_name ?? contact.name ?? [contact.first_name, contact.last_name].filter(Boolean).join(' ')),
      headline: String(rawProfile.headline ?? rawProfile.title ?? rawProfile.target_role ?? ''),
      location: String(rawProfile.location ?? contact.location ?? [contact.city, contact.country].filter(Boolean).join(', ')),
      skills: [...new Set(normalizedSkills.filter(Boolean))],
      completeness: Number.isFinite(completeness) ? completeness : undefined,
    } : null;
    const rawContacts = contactResult.status === 'fulfilled' && Array.isArray(contactResult.value.contacts) ? contactResult.value.contacts : [];
    const contacts: ContactSummary[] = rawContacts.map((rawContact, index) => {
      const item = record(rawContact);
      return {
        id: String(item.id ?? item.contact_id ?? `contact-${index + 1}`),
        name: String(item.name ?? item.full_name ?? 'Unnamed contact'),
        organization: String(item.org ?? item.organization ?? item.company ?? ''),
        title: String(item.title ?? ''),
        email: String(item.email ?? ''),
        phone: String(item.phone_number ?? item.phone ?? ''),
        notes: String(item.notes ?? ''),
        important: asBoolean(item.is_important ?? item.important),
      };
    });
    const backendOnline = healthResult.status === 'fulfilled' && String(health.status ?? '').toLowerCase() === 'online';
    const provider = String(runtimeStatus.backend ?? runtimeStatus.provider ?? 'Unavailable');
    const capabilities: Capability[] = [
      { id: 'runtime', label: 'Core runtime', state: backendOnline ? 'healthy' : 'offline', detail: backendOnline ? 'API and task orchestration responding' : 'Runtime health endpoint is unavailable', latency: 'Live' },
      { id: 'provider', label: 'Reasoning gateway', state: provider !== 'Unavailable' && provider !== 'none' ? 'healthy' : 'degraded', detail: provider !== 'Unavailable' ? `Active backend: ${provider}` : 'No active provider was reported', latency: provider },
      { id: 'workspace', label: 'Workspace storage', state: projectResult.status === 'fulfilled' ? 'healthy' : 'unavailable', detail: `${projects.length} project${projects.length === 1 ? '' : 's'} indexed`, latency: 'Live' },
      { id: 'connectors', label: 'Connector registry', state: connectorResult.status === 'fulfilled' ? 'healthy' : 'unavailable', detail: `${connectors.filter((item) => item.configured).length} of ${connectors.length} configured`, latency: 'Live' },
    ];
    const anyProtectedSuccess = [taskResult, statusResult, connectorResult, projectResult].some((result) => result.status === 'fulfilled');
    return {
      ...structuredClone(emptySnapshot),
      backend: backendOnline && anyProtectedSuccess ? 'online' : anyProtectedSuccess ? 'degraded' : 'offline',
      tasks,
      approvals,
      artifacts,
      capabilities,
      workspace,
      memories,
      memoryCount: memories.length,
      career,
      contacts,
      connectors,
      timeline,
      unreadNotifications: Number(notificationPayload.unread_count ?? timeline.filter((item) => !item.read).length),
      panelHealth: {
        tasks: panelHealth(taskResult, tasks.length > 0, 'Tasks'),
        artifacts: panelHealth(artifactResult, artifacts.length > 0, 'Artifacts'),
        health: panelHealth(healthResult, backendOnline, 'Runtime health'),
        connectors: panelHealth(connectorResult, connectors.length > 0, 'Connectors'),
        projects: panelHealth(projectResult, projects.length > 0, 'Projects'),
        memories: panelHealth(memoryResult, memories.length > 0, 'Memory'),
        notifications: panelHealth(notificationResult, timeline.length > 0, 'Notifications'),
        career: panelHealth(careerResult, Boolean(rawProfile), 'Career profile'),
        contacts: panelHealth(contactResult, contacts.length > 0, 'Contacts'),
      },
      activeTaskId: tasks[0]?.id ?? '',
    };
  }

  async createTask(command: CommandRequest, signal?: AbortSignal): Promise<CommandResponse> {
    const response = await this.request<Record<string, unknown>>('/api/agent/tasks', {
      method: 'POST',
      body: JSON.stringify({ goal: command.goal, active_devices: [], mode: command.mode, privacy: command.privacy }),
      signal,
      headers: { 'Idempotency-Key': command.idempotencyKey },
    });
    const taskId = String(response.task_id ?? response.id ?? `task-${key()}`);
    let taskRecord: Record<string, unknown> = { task_id: taskId, goal: command.goal, status: response.status ?? 'queued', mode: command.mode };
    try {
      taskRecord = await this.request<Record<string, unknown>>(`/api/agent/tasks/${encodeURIComponent(taskId)}`, { signal });
    } catch {
      // The create response is authoritative enough to render a truthful queued task.
    }
    return {
      task: normalizeTask(taskRecord, 0),
      acknowledgement: 'Command accepted. BRJARVIS is planning the execution path.',
      pathReason: `${command.mode} mode requested; backend policy remains authoritative.`,
    };
  }

  async resolveApproval(taskId: string, approvalId: string, approved: boolean, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>(`/api/agent/tasks/${encodeURIComponent(taskId)}/approve`, {
      method: 'POST', body: JSON.stringify({ request_id: approvalId, approved }), signal,
    });
  }

  async previewArtifact(artifactId: string, signal?: AbortSignal) {
    return this.request<{ filename: string; is_text: boolean; content?: string; download_url?: string }>(`/api/artifacts/${encodeURIComponent(artifactId)}/preview`, { signal });
  }

  async verifyArtifact(artifactId: string, verified = true, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>(`/api/artifacts/${encodeURIComponent(artifactId)}/verify`, { method: 'POST', body: JSON.stringify({ verified }), signal });
  }

  async previewProjectFile(projectId: string, fileId: string, signal?: AbortSignal) {
    return this.request<{ filename: string; mime_type: string; size: number; is_text: boolean; content?: string; truncated?: boolean }>(`/api/projects/${encodeURIComponent(projectId)}/files/${encodeURIComponent(fileId)}/preview`, { signal });
  }

  async createProject(name: string, description = '', signal?: AbortSignal) {
    return this.request<Record<string, unknown>>('/api/projects', { method: 'POST', body: JSON.stringify({ name, description }), signal });
  }

  async deleteProject(projectId: string, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectId)}`, { method: 'DELETE', signal });
  }

  async uploadProjectFile(projectId: string, file: File, signal?: AbortSignal) {
    const form = new FormData();
    form.append('file', file, file.name);
    return this.request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectId)}/files`, { method: 'POST', body: form, signal });
  }

  async saveMemory(name: string, content: string, scope = 'user', signal?: AbortSignal) {
    return this.request<Record<string, unknown>>('/api/memory', { method: 'POST', body: JSON.stringify({ name, type: 'note', description: 'Created from the control plane', content, scope }), signal });
  }

  async deleteMemory(name: string, scope = 'user', signal?: AbortSignal) {
    return this.request<Record<string, unknown>>(`/api/memory/${encodeURIComponent(name)}?scope=${encodeURIComponent(scope)}`, { method: 'DELETE', signal });
  }

  async importFile(file: File, signal?: AbortSignal) {
    const form = new FormData();
    form.append('file', file, file.name);
    return this.request<Record<string, unknown>>('/api/import/file', { method: 'POST', body: form, signal });
  }

  async createContact(input: { name: string; phone_number?: string; email?: string; aliases?: string[] }, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>('/api/contacts', { method: 'POST', body: JSON.stringify(input), signal });
  }

  async updateContact(contactId: string, input: Record<string, unknown>, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>(`/api/contacts/${encodeURIComponent(contactId)}`, { method: 'PATCH', body: JSON.stringify(input), signal });
  }

  async deleteContact(contactId: string, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>(`/api/contacts/${encodeURIComponent(contactId)}`, { method: 'DELETE', signal });
  }

  async testConnector(connectorId: string, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>('/api/connector/test', { method: 'POST', body: JSON.stringify({ connector_id: connectorId }), signal });
  }

  async configureConnector(connectorId: string, apiKey: string, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>('/api/connector/config', { method: 'POST', body: JSON.stringify({ connector_id: connectorId, api_key: apiKey }), signal });
  }

  async markNotificationRead(notificationId: string, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>(`/api/notifications/${encodeURIComponent(notificationId)}/read`, { method: 'PATCH', signal });
  }

  async markAllNotificationsRead(signal?: AbortSignal) {
    return this.request<Record<string, unknown>>('/api/notifications/read-all', { method: 'POST', signal });
  }

  async search(query: string, signal?: AbortSignal): Promise<SearchResult[]> {
    const response = await this.request<{ results?: Record<string, unknown>[] }>(`/api/search?q=${encodeURIComponent(query)}&limit=30`, { signal });
    return (response.results ?? []).map((item, index) => ({
      entityType: String(item.entity_type ?? 'result'),
      entityId: String(item.entity_id ?? `result-${index + 1}`),
      title: String(item.title ?? 'Search result'),
      snippet: String(item.snippet ?? ''),
    }));
  }

  async searchCareerJobs(query: string, location = '', signal?: AbortSignal): Promise<CareerJob[]> {
    const response = await this.request<Record<string, unknown>>(`/api/career/jobs/search?query=${encodeURIComponent(query)}&location=${encodeURIComponent(location)}&limit=20`, { signal });
    const matches = Array.isArray(response.matches) ? response.matches : Array.isArray(response.jobs) ? response.jobs : [];
    return matches.map((match, index) => {
      const item = record(match);
      return {
        id: String(item.job_id ?? item.id ?? `job-${index + 1}`),
        title: String(item.title ?? item.job_title ?? 'Untitled role'),
        company: String(item.company ?? item.company_name ?? 'Unknown company'),
        location: String(item.location ?? 'Location not listed'),
        url: item.url ? String(item.url) : undefined,
        summary: asText(item.summary ?? item.description, undefined),
      };
    });
  }

  async createCareerResume(targetRole?: string, signal?: AbortSignal) {
    return this.request<Record<string, unknown>>('/api/career/resumes/create', {
      method: 'POST', body: JSON.stringify({ target_role: targetRole || null, template_id: 'ats_classic' }), signal,
    });
  }
}

export const apiClient = new ApiClient();
