import { useEffect, useState, useSyncExternalStore } from 'react';
import type { ReactNode } from 'react';
import {
  Activity, ArrowUpRight, Bell, Bot, BriefcaseBusiness, Building2, Check, ChevronRight, CircleAlert, CircleCheck,
  Clock3, Command, Database, Download, FileCode2, FileText, FolderTree, Gauge, GitBranch, Globe2,
  Inbox, Layers3, LayoutDashboard, ListTodo, LoaderCircle, LockKeyhole, Menu, MessageSquareText,
  Moon, MoreHorizontal, Network, Pause, Play, Plus, RefreshCw, Search, Send, Settings2, ShieldCheck,
  Sparkles, Square, Target, TerminalSquare, TrendingUp, UserRound, Wifi, WifiOff, X, Zap,
} from 'lucide-react';
import type { NavigationItem } from '../contracts/api';
import type { AppSnapshot, ExecutionMode, Task, ViewId } from '../contracts/domain';
import { apiClient } from '../platform/api-client';
import { loadAuthSnapshot, loginWithApiKey, type AuthSnapshot } from '../platform/auth-client';
import { RealtimeClient } from '../platform/websocket-client';
import { dispatch, getSnapshot, subscribe } from '../state/app-store';
import '../styles/tokens.css';
import '../styles/globals.css';

const navigation: NavigationItem[] = [
  { id: 'command', label: 'Command Center', eyebrow: '01', description: 'Start work and see what BRJARVIS understands.' },
  { id: 'tasks', label: 'Tasks', eyebrow: '02', description: 'Durable work, checkpoints, and recovery.' },
  { id: 'approvals', label: 'Approvals', eyebrow: '03', description: 'Review sensitive actions before execution.' },
  { id: 'workspace', label: 'Workspace', eyebrow: '04', description: 'Projects, files, Git, and indexing.' },
  { id: 'artifacts', label: 'Artifacts', eyebrow: '05', description: 'Verified outputs and provenance.' },
  { id: 'memory', label: 'Memory', eyebrow: '06', description: 'Scoped knowledge and retrieval.' },
  { id: 'career', label: 'Career OS', eyebrow: '07', description: 'Profile, applications, and resumes.' },
  { id: 'business', label: 'Business OS', eyebrow: '08', description: 'Leads, clients, projects, and business operations.' },
  { id: 'integrations', label: 'Integrations', eyebrow: '09', description: 'Providers, connectors, and capabilities.' },
  { id: 'operations', label: 'Operations', eyebrow: '10', description: 'Runtime health, event lag, and audit.' },
];

const navIcons: Record<ViewId, typeof Command> = {
  command: Command,
  tasks: ListTodo,
  approvals: ShieldCheck,
  workspace: FolderTree,
  artifacts: Layers3,
  memory: Database,
  career: BriefcaseBusiness,
  business: Building2,
  integrations: Network,
  operations: Gauge,
};

function useAppSnapshot() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function App() {
  const snapshot = useAppSnapshot();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [command, setCommand] = useState('');
  const [mode, setMode] = useState<ExecutionMode>('smart');
  const [privacy, setPrivacy] = useState<'balanced' | 'local_only'>('balanced');
  const [searchOpen, setSearchOpen] = useState(false);
  const [commandBusy, setCommandBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [operator, setOperator] = useState({ label: 'Operator', scope: 'Local session' });
  const [auth, setAuth] = useState<AuthSnapshot | null>(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [realtime] = useState(() => new RealtimeClient((status) => dispatch({ type: 'connection', status })));

  useEffect(() => {
    loadAuthSnapshot().then((currentAuth) => {
      setAuth(currentAuth);
      setOperator({ label: currentAuth.label, scope: currentAuth.scope });
    });
  }, []);

  useEffect(() => {
    if (!auth || (auth.authRequired && !auth.authenticated)) return;
    apiClient.snapshot().then((data) => dispatch({ type: 'hydrate', snapshot: data }));
    void realtime.connect();
    const unsubscribe = realtime.subscribe((event) => {
      if (event.type === 'task.updated') dispatch({ type: 'task-upsert', task: event.task });
    });
    const keydown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setSearchOpen((open) => !open); }
      if (event.key === 'Escape') { setSearchOpen(false); setMobileOpen(false); }
    };
    window.addEventListener('keydown', keydown);
    return () => { unsubscribe(); realtime.disconnect(); window.removeEventListener('keydown', keydown); };
  }, [auth, realtime]);

  useEffect(() => {
    if (!toast) return;
    const timeout = window.setTimeout(() => setToast(null), 3600);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const activeTask = snapshot.tasks.find((task) => task.id === snapshot.activeTaskId) ?? snapshot.tasks[0];
  const activeNav = navigation.find((item) => item.id === snapshot.activeView) ?? navigation[0];
  const pendingApprovals = snapshot.approvals.length;

  const submitLogin = async (apiKey: string) => {
    setAuthBusy(true);
    setAuthError(null);
    try {
      const currentAuth = await loginWithApiKey(apiKey);
      setAuth(currentAuth);
      setOperator({ label: currentAuth.label, scope: currentAuth.scope });
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Authentication failed.');
    } finally {
      setAuthBusy(false);
    }
  };

  if (!auth) return <BootScreen />;
  if (auth.authRequired && !auth.authenticated) return <LoginScreen busy={authBusy} error={authError} onSubmit={submitLogin} />;

  const submitCommand = async () => {
    const goal = command.trim();
    if (!goal || commandBusy) return;
    setCommandBusy(true);
    try {
      const idempotencyKey = globalThis.crypto?.randomUUID?.() ?? `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const result = await apiClient.createTask({ goal, mode, privacy, idempotencyKey });
      dispatch({ type: 'task-upsert', task: result.task });
      dispatch({ type: 'view', view: 'tasks' });
      setCommand('');
      setToast(result.acknowledgement);
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'The command could not be submitted. Try again.');
    } finally {
      setCommandBusy(false);
    }
  };

  const selectView = (view: ViewId) => {
    dispatch({ type: 'view', view });
    setMobileOpen(false);
  };

  return (
    <div className="app-frame">
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        <div className="brand-block">
          <div className="brand-mark"><Sparkles size={18} strokeWidth={2.4} /></div>
          <div><div className="brand-name">BRJARVIS</div><div className="brand-subtitle">CONTROL PLANE</div></div>
          <button className="icon-button mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <div className="workspace-chip"><div className="status-dot status-green" /><div><span className="eyebrow">ACTIVE WORKSPACE</span><strong>Br-Jarvis</strong></div><ChevronRight size={15} /></div>
        <nav className="primary-nav" aria-label="Primary navigation">
          <span className="nav-group-label">WORKSPACE</span>
          {navigation.slice(0, 5).map((item) => <NavItem key={item.id} item={item} active={snapshot.activeView === item.id} badge={item.id === 'approvals' ? pendingApprovals : undefined} onClick={() => selectView(item.id)} />)}
          <span className="nav-group-label nav-group-secondary">KNOWLEDGE</span>
          {navigation.slice(5, 8).map((item) => <NavItem key={item.id} item={item} active={snapshot.activeView === item.id} onClick={() => selectView(item.id)} />)}
          <span className="nav-group-label nav-group-secondary">SYSTEM</span>
          {navigation.slice(8).map((item) => <NavItem key={item.id} item={item} active={snapshot.activeView === item.id} onClick={() => selectView(item.id)} />)}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-health"><div className={`status-dot ${snapshot.connection === 'connected' ? 'status-green' : 'status-amber'}`} /><div><span className="eyebrow">RUNTIME</span><strong>{snapshot.connection === 'connected' ? 'Connected' : 'Reconnecting'}</strong></div><Wifi size={14} /></div>
          <div className="user-card"><div className="avatar"><UserRound size={16} /></div><div className="user-meta"><strong>{operator.label}</strong><span>{operator.scope}</span></div><button className="icon-button" aria-label="Settings"><Settings2 size={16} /></button></div>
        </div>
      </aside>
      {mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}
      <main className="main-shell">
        <header className="topbar">
          <div className="topbar-left"><button className="icon-button menu-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={19} /></button><div className="breadcrumb"><span>BRJARVIS</span><ChevronRight size={14} /><strong>{activeNav.label}</strong></div></div>
          <div className="topbar-actions"><button className="command-shortcut" onClick={() => setSearchOpen(true)}><Search size={15} /><span>Search anything</span><kbd>⌘ K</kbd></button><div className="connection-pill"><div className={`status-dot ${snapshot.connection === 'connected' ? 'status-green' : 'status-amber'}`} />{snapshot.connection === 'connected' ? 'Live' : 'Reconnecting'}</div><button className="icon-button notification-button" aria-label="Notifications"><Bell size={17} /><span className="notification-dot" /></button><button className="icon-button" aria-label="Toggle theme"><Moon size={17} /></button></div>
        </header>
        <div className="content-scroll"><div className="content-wrap"><PageHeader view={snapshot.activeView} activeNav={activeNav} onCommand={() => selectView('command')} />
          {snapshot.activeView === 'command' && <CommandCenter snapshot={snapshot} command={command} setCommand={setCommand} mode={mode} setMode={setMode} privacy={privacy} setPrivacy={setPrivacy} busy={commandBusy} onSubmit={submitCommand} onView={selectView} />}
          {snapshot.activeView === 'tasks' && <TasksView snapshot={snapshot} onSelectTask={(id) => dispatch({ type: 'active-task', taskId: id })} onToast={setToast} />}
          {snapshot.activeView === 'approvals' && <ApprovalsView snapshot={snapshot} onToast={setToast} />}
          {snapshot.activeView === 'workspace' && <WorkspaceView snapshot={snapshot} />}
          {snapshot.activeView === 'artifacts' && <ArtifactsView snapshot={snapshot} />}
          {snapshot.activeView === 'memory' && <SimpleView icon={<Database size={20} />} title="Memory" eyebrow="SCOPED KNOWLEDGE" description="A permission-aware memory surface is ready for layered retrieval, freshness, and deletion controls." cards={['Recent conversation context', 'Project knowledge', 'User preferences']} />}
          {snapshot.activeView === 'career' && <SimpleView icon={<BriefcaseBusiness size={20} />} title="Career OS" eyebrow="FOCUSED WORKSPACE" description="Keep sensitive career workflows separate from operations while sharing the same typed platform foundation." cards={['Profile health', 'Active applications', 'Resume artifacts']} />}
          {snapshot.activeView === 'business' && <BusinessView onToast={setToast} />}
          {snapshot.activeView === 'integrations' && <IntegrationsView snapshot={snapshot} />}
          {snapshot.activeView === 'operations' && <OperationsView snapshot={snapshot} />}
        </div></div>
      </main>
      {searchOpen && <CommandPalette onClose={() => setSearchOpen(false)} onNavigate={(view) => { selectView(view); setSearchOpen(false); }} />}
      {toast && <div className="toast" role="status"><CircleCheck size={17} /><span>{toast}</span><button className="icon-button" onClick={() => setToast(null)} aria-label="Dismiss"><X size={15} /></button></div>}
    </div>
  );
}

function NavItem({ item, active, badge, onClick }: { item: NavigationItem; active: boolean; badge?: number; onClick: () => void }) {
  const Icon = navIcons[item.id];
  return <button className={`nav-item ${active ? 'nav-item-active' : ''}`} onClick={onClick} aria-current={active ? 'page' : undefined}><Icon size={17} /><span>{item.label}</span>{badge ? <b className="nav-badge">{badge}</b> : <ChevronRight className="nav-chevron" size={13} />}</button>;
}

function PageHeader({ view, activeNav, onCommand }: { view: ViewId; activeNav: NavigationItem; onCommand: () => void }) {
  return <div className="page-header"><div><div className="eyebrow accent-eyebrow">{activeNav.eyebrow} / {view === 'command' ? 'EXECUTION' : 'CONTROL SURFACE'}</div><h1>{activeNav.label}</h1><p>{activeNav.description}</p></div>{view !== 'command' && <button className="secondary-button" onClick={onCommand}><Command size={15} />New command</button>}</div>;
}

function CommandCenter({ snapshot, command, setCommand, mode, setMode, privacy, setPrivacy, busy, onSubmit, onView }: { snapshot: AppSnapshot; command: string; setCommand: (value: string) => void; mode: ExecutionMode; setMode: (mode: ExecutionMode) => void; privacy: 'balanced' | 'local_only'; setPrivacy: (value: 'balanced' | 'local_only') => void; busy: boolean; onSubmit: () => void; onView: (view: ViewId) => void }) {
  const activeTask = snapshot.tasks.find((task) => task.id === snapshot.activeTaskId) ?? snapshot.tasks[0];
  return <>
    <section className="hero-grid"><div className="hero-copy"><div className="hero-kicker"><span className="pulse-ring"><Sparkles size={15} /></span> INTELLIGENCE ONLINE</div><h2>Make the next<br /><em>move deliberate.</em></h2><p>Give BRJARVIS a goal. It will understand the request, choose a capable path, execute with permission, and verify what actually happened.</p><div className="hero-links"><button onClick={() => onView('tasks')}><Activity size={15} />View active execution</button><button onClick={() => onView('workspace')}><FolderTree size={15} />Explore workspace</button></div></div><div className="hero-metrics"><Metric label="Active tasks" value={String(snapshot.tasks.filter((task) => ['running', 'planning', 'waiting', 'retrying'].includes(task.status)).length).padStart(2, '0')} detail="1 needs attention" tone="accent" /><Metric label="Indexed context" value="2.1k" detail="Files ready to retrieve" /><Metric label="Event stream" value="99.8%" detail="Last 24 hours" tone="success" /></div></section>
    <section className="command-card panel"><div className="panel-topline"><div><span className="eyebrow">COMMAND INPUT</span><h3>What should BRJARVIS do?</h3></div><div className="scope-chip"><LockKeyhole size={13} />Local session</div></div><div className="command-input-wrap"><textarea value={command} onChange={(event) => setCommand(event.target.value)} onKeyDown={(event) => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') onSubmit(); }} placeholder="Ask for an outcome, not a sequence of clicks…" aria-label="Command" /><div className="input-tools"><button className="input-tool"><Plus size={15} />Context</button><span className="input-hint">⌘ ↵ to execute</span></div></div><div className="command-controls"><div className="mode-switch" role="group" aria-label="Execution mode">{(['fast', 'smart', 'deep'] as ExecutionMode[]).map((item) => <button key={item} className={mode === item ? 'mode-active' : ''} onClick={() => setMode(item)}><span className={`mode-dot mode-${item}`} />{item}<small>{item === 'fast' ? 'local' : item === 'smart' ? 'balanced' : 'thorough'}</small></button>)}</div><button className={`privacy-toggle ${privacy === 'local_only' ? 'privacy-local' : ''}`} onClick={() => setPrivacy(privacy === 'balanced' ? 'local_only' : 'balanced')}><LockKeyhole size={14} />{privacy === 'local_only' ? 'Local only' : 'Balanced'}<ChevronRight size={14} /></button><button className="primary-button execute-button" onClick={onSubmit} disabled={busy || !command.trim()}>{busy ? <LoaderCircle size={16} className="spin" /> : <Send size={16} />}{busy ? 'Starting…' : 'Start execution'}</button></div></section>
    <div className="section-heading"><div><span className="eyebrow">LIVE CONTEXT</span><h3>Work in motion</h3></div><button className="text-button" onClick={() => onView('tasks')}>Open task board <ArrowUpRight size={14} /></button></div>
    <section className="dashboard-grid"><TaskFocusCard task={activeTask} onClick={() => onView('tasks')} /><TimelineCard snapshot={snapshot} /></section>
  </>;
}

function Metric({ label, value, detail, tone }: { label: string; value: string; detail: string; tone?: 'accent' | 'success' }) { return <div className="metric"><span className="eyebrow">{label}</span><strong className={tone ? `metric-${tone}` : ''}>{value}</strong><small>{detail}</small></div>; }

function TaskFocusCard({ task, onClick }: { task: Task; onClick: () => void }) { return <article className="panel focus-card"><div className="panel-topline"><div><span className="eyebrow">CURRENT EXECUTION</span><h3>{task.title}</h3></div><StatusBadge status={task.status} /></div><p className="muted-copy">{task.summary}</p><div className="progress-row"><span>Overall progress</span><strong>{task.progress}%</strong></div><div className="progress-track"><span style={{ width: `${task.progress}%` }} /></div><div className="step-list">{task.steps.map((step) => <div className="step-row" key={step.id}><span className={`step-icon step-${step.status}`}>{step.status === 'complete' ? <Check size={13} /> : step.status === 'active' ? <LoaderCircle size={13} className="spin" /> : step.status === 'blocked' ? <CircleAlert size={13} /> : <span />}</span><div><strong>{step.label}</strong><small>{step.detail ?? (step.status === 'complete' ? 'Verified' : step.status)}</small></div><span className="step-trailing">{step.status === 'active' ? 'Now' : ''}</span></div>)}</div><button className="card-link" onClick={onClick}>Open full timeline <ArrowUpRight size={14} /></button></article>; }

function TimelineCard({ snapshot }: { snapshot: AppSnapshot }) { return <article className="panel timeline-card"><div className="panel-topline"><div><span className="eyebrow">EVENT STREAM</span><h3>Recent signals</h3></div><button className="icon-button" aria-label="Refresh events"><RefreshCw size={15} /></button></div><div className="event-list">{snapshot.timeline.map((event) => <div className="event-row" key={event.id}><span className={`event-line event-${event.tone}`} /><div className="event-content"><div><strong>{event.label}</strong><time>{event.time}</time></div><p>{event.detail}</p></div></div>)}</div><div className="event-footer"><span><span className="status-dot status-green" />Stream healthy</span><span>cursor 1,884</span></div></article>; }

function TasksView({ snapshot, onSelectTask, onToast }: { snapshot: AppSnapshot; onSelectTask: (id: string) => void; onToast: (message: string) => void }) { const [filter, setFilter] = useState<'all' | Task['status']>('all'); const tasks = filter === 'all' ? snapshot.tasks : snapshot.tasks.filter((task) => task.status === filter); return <><div className="toolbar-row"><div className="filter-tabs">{(['all', 'running', 'waiting', 'completed', 'failed'] as const).map((item) => <button key={item} className={filter === item ? 'filter-active' : ''} onClick={() => setFilter(item)}>{item === 'all' ? 'All tasks' : item}</button>)}</div><button className="secondary-button" onClick={() => onToast('Task command center is ready for a new execution.')}><Plus size={15} />New task</button></div><section className="task-board">{tasks.map((task) => <article className={`task-row panel ${task.id === snapshot.activeTaskId ? 'task-row-active' : ''}`} key={task.id} onClick={() => onSelectTask(task.id)}><div className="task-state-column"><StatusBadge status={task.status} /><span className="task-updated">{task.updatedAt}</span></div><div className="task-main"><h3>{task.title}</h3><p>{task.summary}</p><div className="task-meta"><span><Zap size={13} />{task.mode} path</span><span><Bot size={13} />{task.provider}</span><span><Clock3 size={13} />{task.duration}</span></div></div><div className="task-progress"><strong>{task.progress}%</strong><div className="progress-track"><span style={{ width: `${task.progress}%` }} /></div><small>{task.steps.filter((step) => step.status === 'complete').length}/{task.steps.length} steps</small></div><ChevronRight className="task-arrow" size={18} /></article>)}</section></>; }

function StatusBadge({ status }: { status: Task['status'] }) { const labels: Record<Task['status'], string> = { queued: 'Queued', planning: 'Planning', running: 'Running', waiting: 'Awaiting approval', retrying: 'Retrying', completed: 'Completed', failed: 'Failed', cancelled: 'Cancelled' }; return <span className={`status-badge badge-${status}`}><span className="status-dot" />{labels[status]}</span>; }

function ApprovalsView({ snapshot, onToast }: { snapshot: AppSnapshot; onToast: (message: string) => void }) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const resolve = async (approvalId: string, taskId: string, approved: boolean) => {
    setBusyId(approvalId);
    try {
      await apiClient.resolveApproval(taskId, approvalId, approved);
      dispatch({ type: 'approval-resolved', approvalId, taskId, approved });
      onToast(approved ? 'Approval recorded. The task can continue.' : 'Approval rejected and the task was left paused.');
    } catch (error) {
      onToast(error instanceof Error ? error.message : 'Approval could not be resolved.');
    } finally {
      setBusyId(null);
    }
  };
  return <section className="approval-grid">{snapshot.approvals.map((approval) => <article className="panel approval-card" key={approval.id}><div className="approval-header"><div className={`risk-icon risk-${approval.risk}`}><ShieldCheck size={18} /></div><div><span className="eyebrow">{approval.id} · EXPIRES IN {approval.expiresIn}</span><h3>{approval.action}</h3></div><span className={`risk-label risk-text-${approval.risk}`}>{approval.risk} risk</span></div><div className="approval-target"><span className="eyebrow">TARGET</span><strong>{approval.target}</strong><span>{approval.scope}</span></div><p>{approval.reason}</p><div className="approval-actions"><button className="secondary-button" disabled={busyId === approval.id} onClick={() => resolve(approval.id, approval.taskId, false)}><X size={15} />Reject</button><button className="primary-button" disabled={busyId === approval.id} onClick={() => resolve(approval.id, approval.taskId, true)}>{busyId === approval.id ? <LoaderCircle size={15} className="spin" /> : <Check size={15} />}Approve action</button></div></article>)}</section>;
}

function WorkspaceView({ snapshot }: { snapshot: AppSnapshot }) { return <div className="workspace-grid"><section className="panel workspace-tree"><div className="panel-topline"><div><span className="eyebrow">ACTIVE PROJECT</span><h3>Br-Jarvis</h3></div><button className="secondary-button small-button"><GitBranch size={14} />main</button></div><div className="workspace-search"><Search size={15} /><input placeholder="Search indexed workspace" aria-label="Search indexed workspace" /></div><div className="index-status"><div className="status-dot status-green" /><span>Index healthy</span><strong>2,184 files</strong></div><div className="workspace-list">{snapshot.workspace.map((entry) => <button className="workspace-entry" key={entry.id}><span className="file-icon">{entry.kind === 'folder' ? <FolderTree size={16} /> : entry.name.endsWith('.toml') ? <Settings2 size={16} /> : <FileCode2 size={16} />}</span><span><strong>{entry.name}</strong><small>{entry.path}</small></span><span className="workspace-detail">{entry.detail}</span></button>)}</div></section><section className="panel code-preview"><div className="code-toolbar"><div className="file-tab"><FileCode2 size={15} />websocket.py <span>×</span></div><div><button className="icon-button" aria-label="Download file"><Download size={15} /></button><button className="icon-button" aria-label="More file actions"><MoreHorizontal size={15} /></button></div></div><div className="code-meta"><span>src / brjarvis / web / api / routes</span><span><GitBranch size={13} />main</span></div><pre><code>{`@router.websocket("/api/v1/ws")\nasync def websocket_endpoint(websocket):\n    """Realtime task and event channel."""\n    if not _check_ws_auth(websocket):\n        await websocket.close(code=4001)\n        return\n\n    await websocket.accept()\n    await send_event({\n        "type": "connection.ready",\n        "sequence": 1884,\n    })\n\n    # The new UI treats the server as truth.\n    # Reconnects replay from the last cursor.`}</code></pre><div className="code-footer"><span><CircleCheck size={14} />No issues in current selection</span><span>Line 129 · UTF-8</span></div></section></div>; }

function ArtifactsView({ snapshot }: { snapshot: AppSnapshot }) { return <section className="artifact-grid">{snapshot.artifacts.map((artifact) => <article className="panel artifact-card" key={artifact.id}><div className="artifact-icon"><FileText size={20} /></div><div className="artifact-body"><div className="artifact-title"><h3>{artifact.name}</h3><span className={`artifact-status artifact-${artifact.status}`}>{artifact.status.replace('_', ' ')}</span></div><p>{artifact.type} · {artifact.size} · {artifact.updatedAt}</p><div className="artifact-footer"><span>Task {artifact.taskId}</span><button className="text-button">Preview <ArrowUpRight size={13} /></button></div></div></article>)}</section>; }

function IntegrationsView({ snapshot }: { snapshot: AppSnapshot }) { return <><section className="capability-grid">{snapshot.capabilities.map((capability) => <article className="panel capability-card" key={capability.id}><div className={`capability-icon capability-${capability.state}`}><Network size={17} /></div><div><div className="capability-title"><h3>{capability.label}</h3><span className={`capability-state state-${capability.state}`}>{capability.state.replace('_', ' ')}</span></div><p>{capability.detail}</p></div><span className="capability-latency">{capability.latency}</span></article>)}</section><section className="panel provider-panel"><div className="panel-topline"><div><span className="eyebrow">ROUTING INTELLIGENCE</span><h3>Capability-aware provider pool</h3></div><button className="secondary-button"><Settings2 size={15} />Configure</button></div><div className="provider-list"><ProviderRow name="Manus" tag="Deep reasoning" state="degraded" latency="1.8 s" /><ProviderRow name="Proxy brain" tag="Smart path" state="healthy" latency="620 ms" /><ProviderRow name="Local Ollama" tag="Private / offline" state="healthy" latency="84 ms" /></div></section></>; }

function ProviderRow({ name, tag, state, latency }: { name: string; tag: string; state: string; latency: string }) { return <div className="provider-row"><div className="provider-avatar"><Bot size={16} /></div><div className="provider-name"><strong>{name}</strong><span>{tag}</span></div><span className={`status-badge badge-${state === 'healthy' ? 'completed' : 'waiting'}`}><span className="status-dot" />{state}</span><span className="provider-latency">{latency}</span><button className="icon-button" aria-label={`Configure ${name}`}><Settings2 size={15} /></button></div>; }

function OperationsView({ snapshot }: { snapshot: AppSnapshot }) { return <><section className="ops-metrics"><Metric label="Queue depth" value="03" detail="1 waiting approval" tone="accent" /><Metric label="Event lag" value="42 ms" detail="Healthy delivery" tone="success" /><Metric label="Provider uptime" value="99.8%" detail="Rolling 24 hours" /><Metric label="Memory" value="38%" detail="12.4 GB available" /></section><section className="ops-grid"><article className="panel"><div className="panel-topline"><div><span className="eyebrow">RUNTIME SIGNALS</span><h3>System timeline</h3></div><button className="text-button">View audit <ArrowUpRight size={13} /></button></div><div className="event-list">{snapshot.timeline.concat([{ id: 'e5', time: formatTime(), label: 'Capability check', detail: 'Runtime, workspace, and gateway health sampled', tone: 'success' }]).map((event) => <div className="event-row" key={event.id}><span className={`event-line event-${event.tone}`} /><div className="event-content"><div><strong>{event.label}</strong><time>{event.time}</time></div><p>{event.detail}</p></div></div>)}</div></article><article className="panel ops-checks"><div className="panel-topline"><div><span className="eyebrow">READINESS</span><h3>Control gates</h3></div><CircleCheck className="healthy-icon" size={19} /></div>{['Authorization boundary', 'Task state persistence', 'Realtime replay cursor', 'Workspace index freshness'].map((label) => <div className="readiness-row" key={label}><span className="status-dot status-green" /><span>{label}</span><strong>Healthy</strong></div>)}</article></section></>; }

function SimpleView({ icon, eyebrow, title, description, cards }: { icon: ReactNode; eyebrow: string; title: string; description: string; cards: string[] }) { return <section className="simple-view"><div className="simple-icon">{icon}</div><div className="eyebrow">{eyebrow}</div><h2>{title}</h2><p>{description}</p><div className="simple-cards">{cards.map((card, index) => <div className="panel simple-card" key={card}><span>0{index + 1}</span><strong>{card}</strong><ArrowUpRight size={15} /></div>)}</div></section>; }

function BootScreen() {
  return <div className="auth-screen"><div className="auth-card boot-card"><div className="brand-mark"><Sparkles size={18} /></div><div className="eyebrow accent-eyebrow">BRJARVIS / STARTING</div><h1>Preparing your control plane</h1><p>Loading secure session, capabilities, and the latest task state.</p><LoaderCircle size={20} className="spin boot-spinner" /></div></div>;
}

function LoginScreen({ busy, error, onSubmit }: { busy: boolean; error: string | null; onSubmit: (apiKey: string) => void }) {
  const [apiKey, setApiKey] = useState('');
  return <div className="auth-screen"><div className="auth-card"><div className="auth-brand"><div className="brand-mark"><Sparkles size={18} /></div><div><div className="brand-name">BRJARVIS</div><div className="brand-subtitle">CONTROL PLANE</div></div></div><div className="eyebrow accent-eyebrow">SECURE SESSION</div><h1>Sign in to continue</h1><p>Use the local server API key to create a short-lived browser session. The key is sent over the current connection and is not stored in browser storage.</p><form onSubmit={(event) => { event.preventDefault(); if (apiKey.trim()) onSubmit(apiKey); }}><label className="auth-label" htmlFor="server-api-key">Server API key</label><input id="server-api-key" className="auth-input" type="password" autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="Paste the configured server key" autoFocus /><button className="primary-button auth-submit" disabled={busy || !apiKey.trim()}>{busy ? <LoaderCircle size={16} className="spin" /> : <LockKeyhole size={16} />}{busy ? 'Creating session…' : 'Create secure session'}</button></form>{error && <div className="auth-error" role="alert"><CircleAlert size={15} />{error}</div>}<div className="auth-note"><ShieldCheck size={14} /><span>Session cookie is HttpOnly and expires according to server policy.</span></div></div></div>;
}

function BusinessView({ onToast }: { onToast: (message: string) => void }) {
  const metrics: Array<{ label: string; value: string; detail: string; tone?: 'accent' | 'success' }> = [
    { label: 'Open opportunities', value: '18', detail: '+4 this month', tone: 'accent' },
    { label: 'Active clients', value: '07', detail: '2 need attention', tone: 'success' },
    { label: 'Pipeline value', value: '$84.2k', detail: 'Weighted forecast' },
    { label: 'Next deadline', value: '03d', detail: 'Quarterly review' },
  ];
  const pipeline = [
    { name: 'Discovery', count: '06', value: '$18.4k', width: '72%', tone: 'accent' },
    { name: 'Proposal', count: '04', value: '$31.8k', width: '54%', tone: 'purple' },
    { name: 'Negotiation', count: '03', value: '$22.0k', width: '42%', tone: 'amber' },
    { name: 'Won', count: '05', value: '$12.0k', width: '31%', tone: 'green' },
  ];
  const priorities = [
    { title: 'Follow up with Northstar Labs', meta: 'Sales · Due today', state: 'Priority' },
    { title: 'Prepare client renewal brief', meta: 'Account · Due tomorrow', state: 'Queued' },
    { title: 'Review Q3 operating plan', meta: 'Strategy · Friday', state: 'Draft' },
  ];
  return <>
    <section className="business-intro"><div><div className="hero-kicker"><span className="pulse-ring"><Building2 size={15} /></span> BUSINESS OPERATIONS ONLINE</div><h2>Turn activity into<br /><em>operating leverage.</em></h2><p>One focused surface for opportunities, clients, delivery, cash flow, and the decisions that keep the business moving.</p></div><button className="primary-button" onClick={() => onToast('Business command created. Start from the Command Center to automate the next step.')}><Plus size={16} />New business action</button></section>
    <section className="business-metrics">{metrics.map((metric) => <Metric key={metric.label} {...metric} />)}</section>
    <div className="business-grid"><section className="panel pipeline-panel"><div className="panel-topline"><div><span className="eyebrow">REVENUE PIPELINE</span><h3>Where work is moving</h3></div><button className="text-button" onClick={() => onToast('Pipeline view is ready for CRM connector data.')}>Open pipeline <ArrowUpRight size={13} /></button></div><div className="pipeline-list">{pipeline.map((stage) => <div className="pipeline-row" key={stage.name}><div className="pipeline-label"><strong>{stage.name}</strong><span>{stage.count} opportunities</span></div><div className="pipeline-bar"><span className={`pipeline-fill pipeline-${stage.tone}`} style={{ width: stage.width }} /></div><strong className="pipeline-value">{stage.value}</strong></div>)}</div><div className="pipeline-footer"><span><TrendingUp size={14} />12.8% conversion trend</span><span>Updated 4 min ago</span></div></section><section className="panel priority-panel"><div className="panel-topline"><div><span className="eyebrow">OPERATING PRIORITIES</span><h3>Next decisions</h3></div><Target size={18} className="accent-icon" /></div><div className="priority-list">{priorities.map((priority) => <button className="priority-row" key={priority.title} onClick={() => onToast(`${priority.title} added to the Command Center queue.`)}><span className="priority-icon"><ArrowUpRight size={14} /></span><span><strong>{priority.title}</strong><small>{priority.meta}</small></span><em>{priority.state}</em></button>)}</div></section></div>
    <section className="business-quick"><div className="section-heading"><div><span className="eyebrow">BUSINESS OS MODULES</span><h3>Make the next move deliberate</h3></div></div><div className="quick-grid">{['Leads & opportunities', 'Client delivery', 'Invoices & cash flow', 'Projects & milestones'].map((label, index) => <button className="panel quick-card" key={label} onClick={() => onToast(`${label} will open through the connected Business OS workflow.`)}><span>0{index + 1}</span><strong>{label}</strong><ChevronRight size={15} /></button>)}</div></section>
  </>;
}

function CommandPalette({ onClose, onNavigate }: { onClose: () => void; onNavigate: (view: ViewId) => void }) { const [query, setQuery] = useState(''); const items = navigation.filter((item) => `${item.label} ${item.description}`.toLowerCase().includes(query.toLowerCase())); return <div className="palette-backdrop" onClick={onClose}><div className="command-palette" onClick={(event) => event.stopPropagation()}><div className="palette-input"><Search size={18} /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Jump to a surface or action…" /></div><div className="palette-list">{items.map((item) => { const Icon = navIcons[item.id]; return <button key={item.id} onClick={() => onNavigate(item.id)}><span className="palette-icon"><Icon size={16} /></span><span><strong>{item.label}</strong><small>{item.description}</small></span><kbd>↵</kbd></button>; })}</div><div className="palette-footer"><span><kbd>↑↓</kbd> Navigate</span><span><kbd>↵</kbd> Open</span><span><kbd>esc</kbd> Close</span></div></div></div>; }
