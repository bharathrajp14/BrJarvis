import type { AppSnapshot } from '../contracts/domain';

export const initialSnapshot: AppSnapshot = {
  activeView: 'command',
  activeTaskId: 'task-1042',
  connection: 'connected',
  capabilities: [
    { id: 'runtime', label: 'Core runtime', state: 'healthy', detail: 'Task orchestration online', latency: '42 ms' },
    { id: 'workspace', label: 'Workspace index', state: 'healthy', detail: '2,184 files indexed', latency: '18 ms' },
    { id: 'provider', label: 'Reasoning gateway', state: 'degraded', detail: 'Fallback available · cloud latency elevated', latency: '1.8 s' },
    { id: 'voice', label: 'Voice bridge', state: 'requires_approval', detail: 'Microphone permission required', latency: '—' },
  ],
  tasks: [
    {
      id: 'task-1042', title: 'Prepare architecture risk brief', status: 'running', mode: 'deep', progress: 68,
      updatedAt: 'Just now', duration: '02:14', provider: 'Manus · deep reasoning',
      summary: 'Synthesizing repository structure, task state, and provider fallback risks.', artifactCount: 2,
      steps: [
        { id: 's1', label: 'Inspect repository map', status: 'complete', detail: '2,563 files classified' },
        { id: 's2', label: 'Trace execution spine', status: 'complete', detail: 'Agent → tools → events mapped' },
        { id: 's3', label: 'Rank production risks', status: 'active', detail: 'Security and reliability review' },
        { id: 's4', label: 'Generate decision brief', status: 'queued' },
      ],
    },
    {
      id: 'task-1038', title: 'Refresh workspace intelligence index', status: 'completed', mode: 'smart', progress: 100,
      updatedAt: '18 min ago', duration: '00:42', provider: 'Local indexer', summary: 'Updated AST, import, and Git metadata for the active project.', artifactCount: 1,
      steps: [
        { id: 's1', label: 'Hash changed files', status: 'complete' },
        { id: 's2', label: 'Update dependency graph', status: 'complete' },
        { id: 's3', label: 'Refresh semantic summaries', status: 'complete' },
      ],
    },
    {
      id: 'task-1034', title: 'Draft candidate follow-up email', status: 'waiting', mode: 'smart', progress: 54,
      updatedAt: '1 hr ago', duration: '00:31', provider: 'Proxy brain', summary: 'Waiting for permission to use the configured email connector.', artifactCount: 0, requiresApproval: true,
      steps: [
        { id: 's1', label: 'Read candidate context', status: 'complete' },
        { id: 's2', label: 'Draft message', status: 'complete' },
        { id: 's3', label: 'Send via connector', status: 'blocked', detail: 'Approval required' },
      ],
    },
    {
      id: 'task-1027', title: 'Summarize local runtime status', status: 'completed', mode: 'fast', progress: 100,
      updatedAt: 'Yesterday', duration: '00:04', provider: 'Deterministic local', summary: 'Returned cached system health and queue status.', artifactCount: 0,
      steps: [
        { id: 's1', label: 'Read cached health', status: 'complete' },
        { id: 's2', label: 'Format response', status: 'complete' },
      ],
    },
  ],
  approvals: [
    { id: 'approval-18', taskId: 'task-1034', action: 'Send email via connector', target: 'Career outreach · candidate follow-up', risk: 'high', scope: 'External communication', reason: 'This will send a message outside BRJARVIS using the configured connector.', expiresIn: '12 min' },
    { id: 'approval-17', taskId: 'task-1042', action: 'Read workspace project files', target: 'BRJARVIS repository', risk: 'medium', scope: 'Workspace read access', reason: 'The task needs project context to verify architecture findings.', expiresIn: '28 min' },
  ],
  artifacts: [
    { id: 'artifact-44', name: 'architecture-risk-brief.md', type: 'Markdown report', taskId: 'task-1042', status: 'processing', size: '—', updatedAt: 'Just now' },
    { id: 'artifact-43', name: 'workspace-dependency-map.json', type: 'Graph data', taskId: 'task-1038', status: 'verified', size: '184 KB', updatedAt: '18 min ago' },
    { id: 'artifact-42', name: 'career-follow-up-draft.txt', type: 'Text draft', taskId: 'task-1034', status: 'needs_review', size: '4 KB', updatedAt: '1 hr ago' },
  ],
  workspace: [
    { id: 'w1', name: 'src', kind: 'folder', path: '/src', detail: '1,204 files' },
    { id: 'w2', name: 'runtime', kind: 'folder', path: '/runtime', detail: 'State and reports' },
    { id: 'w3', name: 'pyproject.toml', kind: 'file', path: '/pyproject.toml', detail: 'Package configuration' },
    { id: 'w4', name: 'upgrade_plan.md', kind: 'file', path: '/upgrade_plan.md', detail: 'Architecture roadmap' },
    { id: 'w5', name: 'websocket.py', kind: 'file', path: '/src/brjarvis/web/api/routes/websocket.py', detail: '528 lines' },
  ],
  timeline: [
    { id: 'e1', time: '10:42:18', label: 'Task resumed', detail: 'Reconnected from sequence 1884', tone: 'accent' },
    { id: 'e2', time: '10:42:11', label: 'Context filtered', detail: '12 relevant modules retained from workspace index', tone: 'neutral' },
    { id: 'e3', time: '10:41:58', label: 'Deep path selected', detail: 'Complexity and verification requirement exceeded smart-path threshold', tone: 'accent' },
    { id: 'e4', time: '10:41:55', label: 'Command accepted', detail: 'Idempotency key confirmed · task-1042', tone: 'success' },
  ],
};
