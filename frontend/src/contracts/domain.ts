export type ViewId =
  | 'command'
  | 'tasks'
  | 'approvals'
  | 'workspace'
  | 'artifacts'
  | 'memory'
  | 'career'
  | 'business'
  | 'integrations'
  | 'operations';

export type TaskStatus =
  | 'queued'
  | 'planning'
  | 'running'
  | 'waiting'
  | 'retrying'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type ExecutionMode = 'fast' | 'smart' | 'deep';
export type CapabilityState = 'healthy' | 'degraded' | 'offline' | 'requires_approval' | 'unavailable';

export interface Capability {
  id: string;
  label: string;
  state: CapabilityState;
  detail: string;
  latency?: string;
}

export interface TaskStep {
  id: string;
  label: string;
  status: 'complete' | 'active' | 'queued' | 'blocked';
  detail?: string;
}

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  mode: ExecutionMode;
  progress: number;
  updatedAt: string;
  duration: string;
  provider: string;
  summary: string;
  steps: TaskStep[];
  artifactCount: number;
  requiresApproval?: boolean;
}

export interface Approval {
  id: string;
  taskId: string;
  action: string;
  target: string;
  risk: 'low' | 'medium' | 'high';
  scope: string;
  reason: string;
  expiresIn: string;
}

export interface Artifact {
  id: string;
  name: string;
  type: string;
  taskId: string;
  status: 'verified' | 'processing' | 'needs_review' | 'failed';
  size: string;
  updatedAt: string;
}

export interface WorkspaceEntry {
  id: string;
  name: string;
  kind: 'folder' | 'file';
  path: string;
  detail?: string;
}

export interface TimelineEvent {
  id: string;
  time: string;
  label: string;
  detail: string;
  tone: 'neutral' | 'accent' | 'success' | 'warning';
}

export interface MemoryEntry {
  id: string;
  name: string;
  scope: string;
  content: string;
  updatedAt: string;
}

export interface CareerProfile {
  name: string;
  headline: string;
  location: string;
  skills: string[];
  completeness?: number;
}

export interface ConnectorSummary {
  id: string;
  name: string;
  description: string;
  status: string;
  configured: boolean;
  requiresAuth: boolean;
  tools: string[];
}

export interface AppSnapshot {
  activeView: ViewId;
  activeTaskId: string;
  connection: 'connected' | 'connecting' | 'offline';
  capabilities: Capability[];
  tasks: Task[];
  approvals: Approval[];
  artifacts: Artifact[];
  workspace: WorkspaceEntry[];
  memories: MemoryEntry[];
  memoryCount: number;
  career: CareerProfile | null;
  connectors: ConnectorSummary[];
  timeline: TimelineEvent[];
}
