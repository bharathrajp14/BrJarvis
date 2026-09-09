import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import {
  Activity, ArrowUpRight, Bell, Bot, BriefcaseBusiness, Building2, Check, ChevronRight, CircleAlert, CircleCheck,
  Clock3, Command, Database, FileCode2, FileText, FolderTree, Gauge, Layers3, ListTodo, LoaderCircle, LockKeyhole,
  LogOut, Menu, Moon, Network, Plus, RefreshCw, Search, Send, Settings2, ShieldCheck, Sparkles, UserRound, Wifi, X, Zap,
} from 'lucide-react';
import type { NavigationItem } from '../contracts/api';
import type { AppSnapshot, Artifact, ExecutionMode, MemoryEntry, Task, ViewId } from '../contracts/domain';
import { apiClient } from '../platform/api-client';
import { loadAuthSnapshot, loginWithApiKey, logoutSession, type AuthSnapshot } from '../platform/auth-client';
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
  const [lightMode, setLightMode] = useState(false);
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

  const refreshSnapshot = useCallback(async () => {
    try {
      const data = await apiClient.snapshot();
      dispatch({ type: 'hydrate', snapshot: data });
      return true;
    } catch {
      dispatch({ type: 'connection', status: 'offline' });
      return false;
    }
  }, []);

  useEffect(() => {
    if (!auth || (auth.authRequired && !auth.authenticated)) return;
    void refreshSnapshot();
    void realtime.connect();
    const unsubscribe = realtime.subscribe((event) => {
      if (event.type === 'task.updated' && 'task' in event && event.task) {
        dispatch({ type: 'task-upsert', task: event.task as Task });
        return;
      }
      const eventType = String(event.type).toLowerCase();
      if (eventType.startsWith('task.') || eventType.startsWith('message.') || eventType === 'serverready' || eventType === 'connection.ready') {
        refreshSnapshot();
      }
    });
    const keydown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setSearchOpen((open) => !open); }
      if (event.key === 'Escape') { setSearchOpen(false); setMobileOpen(false); }
    };
    window.addEventListener('keydown', keydown);
    return () => { unsubscribe(); realtime.disconnect(); window.removeEventListener('keydown', keydown); };
  }, [auth, realtime, refreshSnapshot]);

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

  const submitLogout = async () => {
    try {
      await logoutSession();
    } catch {
      // Local session state is still cleared so the operator is signed out of this browser.
    }
    realtime.disconnect();
    setAuth((current) => ({
      authRequired: current?.authRequired ?? true,
      authenticated: false,
      label: 'Operator',
      scope: 'Signed out',
    }));
    setOperator({ label: 'Operator', scope: 'Signed out' });
    setToast('Session ended.');
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
    <div className={`app-frame ${lightMode ? 'theme-light' : ''}`}>
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
          <div className="user-card"><div className="avatar"><UserRound size={16} /></div><div className="user-meta"><strong>{operator.label}</strong><span>{operator.scope}</span></div><button className="icon-button" onClick={() => setToast('Settings are managed through the local server configuration.')} aria-label="Settings" title="Open local settings"><Settings2 size={16} /></button><button className="icon-button" onClick={() => void submitLogout()} aria-label="Sign out" title="Sign out"><LogOut size={16} /></button></div>
        </div>
      </aside>
      {mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}
      <main className="main-shell">
        <header className="topbar">
          <div className="topbar-left"><button className="icon-button menu-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={19} /></button><div className="breadcrumb"><span>BRJARVIS</span><ChevronRight size={14} /><strong>{activeNav.label}</strong></div></div>
          <div className="topbar-actions"><button className="command-shortcut" onClick={() => setSearchOpen(true)}><Search size={15} /><span>Search anything</span><kbd>⌘ K</kbd></button><div className="connection-pill"><div className={`status-dot ${snapshot.connection === 'connected' ? 'status-green' : 'status-amber'}`} />{snapshot.connection === 'connected' ? 'Live' : 'Reconnecting'}</div><button className="icon-button notification-button" onClick={() => selectView('operations')} aria-label="Open notifications" title={`${snapshot.timeline.length} live notifications`}><Bell size={17} />{snapshot.timeline.length > 0 && <span className="notification-count">{snapshot.timeline.length > 9 ? '9+' : snapshot.timeline.length}</span>}</button><button className="icon-button" onClick={() => setLightMode((value) => !value)} aria-label={lightMode ? 'Use dark theme' : 'Use light theme'} title={lightMode ? 'Use dark theme' : 'Use light theme'}><Moon size={17} /></button></div>
        </header>
        <div className="content-scroll"><div className="content-wrap"><PageHeader view={snapshot.activeView} activeNav={activeNav} onCommand={() => selectView('command')} />
          {snapshot.activeView === 'command' && <CommandCenter snapshot={snapshot} command={command} setCommand={setCommand} mode={mode} setMode={setMode} privacy={privacy} setPrivacy={setPrivacy} busy={commandBusy} onSubmit={submitCommand} onView={selectView} onToast={setToast} onRefresh={refreshSnapshot} />}
          {snapshot.activeView === 'tasks' && <TasksView snapshot={snapshot} onSelectTask={(id) => dispatch({ type: 'active-task', taskId: id })} onView={selectView} />}
          {snapshot.activeView === 'approvals' && <ApprovalsView snapshot={snapshot} onToast={setToast} />}
          {snapshot.activeView === 'workspace' && <WorkspaceView snapshot={snapshot} onToast={setToast} />}
          {snapshot.activeView === 'artifacts' && <ArtifactsView snapshot={snapshot} onToast={setToast} />}
          {snapshot.activeView === 'memory' && <MemoryView memories={snapshot.memories} onToast={setToast} />}
          {snapshot.activeView === 'career' && <CareerView profile={snapshot.career} onToast={setToast} />}
          {snapshot.activeView === 'business' && <BusinessView snapshot={snapshot} onView={selectView} />}
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

function CommandCenter({ snapshot, command, setCommand, mode, setMode, privacy, setPrivacy, busy, onSubmit, onView, onToast, onRefresh }: { snapshot: AppSnapshot; command: string; setCommand: (value: string) => void; mode: ExecutionMode; setMode: (mode: ExecutionMode) => void; privacy: 'balanced' | 'local_only'; setPrivacy: (value: 'balanced' | 'local_only') => void; busy: boolean; onSubmit: () => void; onView: (view: ViewId) => void; onToast: (message: string) => void; onRefresh: () => Promise<boolean> }) {
  const activeTask = snapshot.tasks.find((task) => task.id === snapshot.activeTaskId) ?? snapshot.tasks[0];
  const fileInput = useRef<HTMLInputElement>(null);
  const [attachment, setAttachment] = useState<string | null>(null);
  const attachContext = async (file: File) => { try { await apiClient.importFile(file); setAttachment(file.name); onToast(`${file.name} imported into live memory.`); } catch (error) { onToast(error instanceof Error ? error.message : 'Context import failed.'); } };
  return <>
    <section className="hero-grid"><div className="hero-copy"><div className="hero-kicker"><span className="pulse-ring"><Sparkles size={15} /></span> {snapshot.connection === 'connected' ? 'LIVE RUNTIME' : 'RUNTIME UNAVAILABLE'}</div><h2>Make the next<br /><em>move deliberate.</em></h2><p>Give BRJARVIS a goal. It will understand the request, choose a capable path, execute with permission, and verify what actually happened.</p><div className="hero-links"><button onClick={() => onView('tasks')}><Activity size={15} />View active execution</button><button onClick={() => onView('workspace')}><FolderTree size={15} />Explore workspace</button></div></div><div className="hero-metrics"><Metric label="Active tasks" value={String(snapshot.tasks.filter((task) => ['running', 'planning', 'waiting', 'retrying'].includes(task.status)).length)} detail="Live task state" tone="accent" /><Metric label="Artifacts loaded" value={String(snapshot.artifacts.length)} detail="Live server response" /><Metric label="Events loaded" value={String(snapshot.timeline.length)} detail="Live event history" tone="success" /></div></section>
    <section className="command-card panel"><div className="panel-topline"><div><span className="eyebrow">COMMAND INPUT</span><h3>What should BRJARVIS do?</h3></div><div className="scope-chip"><LockKeyhole size={13} />Local session</div></div><div className="command-input-wrap"><textarea value={command} onChange={(event) => setCommand(event.target.value)} onKeyDown={(event) => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') onSubmit(); }} placeholder="Ask for an outcome, not a sequence of clicks…" aria-label="Command" /><div className="input-tools"><input ref={fileInput} type="file" hidden accept=".pdf,.docx,.txt,.md,.csv,.vcf" onChange={(event) => { const file = event.target.files?.[0]; if (file) void attachContext(file); event.currentTarget.value = ''; }} /><button className="input-tool" onClick={() => fileInput.current?.click()}><Plus size={15} />{attachment ? attachment : 'Attach context'}</button><span className="input-hint">⌘ ↵ to execute</span></div></div><div className="command-controls"><div className="mode-switch" role="group" aria-label="Execution mode">{(['fast', 'smart', 'deep'] as ExecutionMode[]).map((item) => <button key={item} className={mode === item ? 'mode-active' : ''} onClick={() => setMode(item)}><span className={`mode-dot mode-${item}`} />{item}<small>{item === 'fast' ? 'local' : item === 'smart' ? 'balanced' : 'thorough'}</small></button>)}</div><button className={`privacy-toggle ${privacy === 'local_only' ? 'privacy-local' : ''}`} onClick={() => setPrivacy(privacy === 'balanced' ? 'local_only' : 'balanced')}><LockKeyhole size={14} />{privacy === 'local_only' ? 'Local only' : 'Balanced'}<ChevronRight size={14} /></button><button className="primary-button execute-button" onClick={onSubmit} disabled={busy || !command.trim()}>{busy ? <LoaderCircle size={16} className="spin" /> : <Send size={16} />}{busy ? 'Starting…' : 'Start execution'}</button></div></section>
    <div className="section-heading"><div><span className="eyebrow">LIVE CONTEXT</span><h3>Work in motion</h3></div><button className="text-button" onClick={() => onView('tasks')}>Open task board <ArrowUpRight size={14} /></button></div>
    <section className="dashboard-grid"><TaskFocusCard task={activeTask} onClick={() => onView('tasks')} /><TimelineCard snapshot={snapshot} onRefresh={onRefresh} /></section>
  </>;
}

function Metric({ label, value, detail, tone }: { label: string; value: string; detail: string; tone?: 'accent' | 'success' }) { return <div className="metric"><span className="eyebrow">{label}</span><strong className={tone ? `metric-${tone}` : ''}>{value}</strong><small>{detail}</small></div>; }

function TaskFocusCard({ task, onClick }: { task?: Task; onClick: () => void }) { if (!task) return <article className="panel focus-card"><div className="panel-topline"><div><span className="eyebrow">CURRENT EXECUTION</span><h3>No active task</h3></div><StatusBadge status="queued" /></div><p className="muted-copy">Live task state has not reported an active execution.</p><button className="card-link" onClick={onClick}>Open task board <ArrowUpRight size={14} /></button></article>; return <article className="panel focus-card"><div className="panel-topline"><div><span className="eyebrow">CURRENT EXECUTION</span><h3>{task.title}</h3></div><StatusBadge status={task.status} /></div><p className="muted-copy">{task.summary}</p><div className="progress-row"><span>Overall progress</span><strong>{task.progress}%</strong></div><div className="progress-track"><span style={{ width: `${task.progress}%` }} /></div><div className="step-list">{task.steps.map((step) => <div className="step-row" key={step.id}><span className={`step-icon step-${step.status}`}>{step.status === 'complete' ? <Check size={13} /> : step.status === 'active' ? <LoaderCircle size={13} className="spin" /> : step.status === 'blocked' ? <CircleAlert size={13} /> : <span />}</span><div><strong>{step.label}</strong><small>{step.detail ?? (step.status === 'complete' ? 'Verified' : step.status)}</small></div><span className="step-trailing">{step.status === 'active' ? 'Now' : ''}</span></div>)}</div><button className="card-link" onClick={onClick}>Open full timeline <ArrowUpRight size={14} /></button></article>; }

function TimelineCard({ snapshot, onRefresh }: { snapshot: AppSnapshot; onRefresh: () => Promise<boolean> }) { const [refreshing, setRefreshing] = useState(false); const refresh = async () => { if (refreshing) return; setRefreshing(true); const ok = await onRefresh(); setRefreshing(false); if (!ok) return; }; return <article className="panel timeline-card"><div className="panel-topline"><div><span className="eyebrow">EVENT STREAM</span><h3>Recent signals</h3></div><button className="icon-button" onClick={() => void refresh()} aria-label="Refresh events" disabled={refreshing} title="Refresh live events">{refreshing ? <LoaderCircle size={15} className="spin" /> : <RefreshCw size={15} />}</button></div><div className="event-list">{snapshot.timeline.map((event) => <div className="event-row" key={event.id}><span className={`event-line event-${event.tone}`} /><div className="event-content"><div><strong>{event.label}</strong><time>{event.time}</time></div><p>{event.detail}</p></div></div>)}</div><div className="event-footer"><span><span className={`status-dot ${snapshot.connection === 'connected' ? 'status-green' : 'status-amber'}`} />{snapshot.connection === 'connected' ? 'Stream connected' : 'Stream unavailable'}</span><span>Live cursor unavailable</span></div></article>; }

function TasksView({ snapshot, onSelectTask, onView }: { snapshot: AppSnapshot; onSelectTask: (id: string) => void; onView: (view: ViewId) => void }) { const [filter, setFilter] = useState<'all' | Task['status']>('all'); const tasks = filter === 'all' ? snapshot.tasks : snapshot.tasks.filter((task) => task.status === filter); return <><div className="toolbar-row"><div className="filter-tabs">{(['all', 'running', 'waiting', 'completed', 'failed'] as const).map((item) => <button key={item} className={filter === item ? 'filter-active' : ''} onClick={() => setFilter(item)}>{item === 'all' ? 'All tasks' : item}</button>)}</div><button className="secondary-button" onClick={() => onView('command')}><Plus size={15} />New task</button></div><section className="task-board">{tasks.length ? tasks.map((task) => <article className={`task-row panel ${task.id === snapshot.activeTaskId ? 'task-row-active' : ''}`} key={task.id} onClick={() => onSelectTask(task.id)}><div className="task-state-column"><StatusBadge status={task.status} /><span className="task-updated">{task.updatedAt}</span></div><div className="task-main"><h3>{task.title}</h3><p>{task.summary}</p><div className="task-meta"><span><Zap size={13} />{task.mode} path</span><span><Bot size={13} />{task.provider}</span><span><Clock3 size={13} />{task.duration}</span></div></div><div className="task-progress"><strong>{task.progress}%</strong><div className="progress-track"><span style={{ width: `${task.progress}%` }} /></div><small>{task.steps.filter((step) => step.status === 'complete').length}/{task.steps.length} steps</small></div><ChevronRight className="task-arrow" size={18} /></article>) : <div className="empty-state">No live tasks match this filter.</div>}</section></>; }

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
  return <section className="approval-grid">{snapshot.approvals.length ? snapshot.approvals.map((approval) => <article className="panel approval-card" key={approval.id}><div className="approval-header"><div className={`risk-icon risk-${approval.risk}`}><ShieldCheck size={18} /></div><div><span className="eyebrow">{approval.id} · EXPIRES IN {approval.expiresIn}</span><h3>{approval.action}</h3></div><span className={`risk-label risk-text-${approval.risk}`}>{approval.risk} risk</span></div><div className="approval-target"><span className="eyebrow">TARGET</span><strong>{approval.target}</strong><span>{approval.scope}</span></div><p>{approval.reason}</p><div className="approval-actions"><button className="secondary-button" disabled={busyId === approval.id} onClick={() => resolve(approval.id, approval.taskId, false)}><X size={15} />Reject</button><button className="primary-button" disabled={busyId === approval.id} onClick={() => resolve(approval.id, approval.taskId, true)}>{busyId === approval.id ? <LoaderCircle size={15} className="spin" /> : <Check size={15} />}Approve action</button></div></article>) : <div className="empty-state">No pending approvals were returned by the live task state.</div>}</section>;
}

function WorkspaceView({ snapshot, onToast }: { snapshot: AppSnapshot; onToast: (message: string) => void }) {
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ filename: string; mime_type: string; size: number; is_text: boolean; content?: string; truncated?: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  const entries = snapshot.workspace.filter((entry) => `${entry.name} ${entry.path} ${entry.detail ?? ''}`.toLowerCase().includes(query.toLowerCase()));
  const selected = snapshot.workspace.find((entry) => entry.id === selectedId);
  const selectEntry = async (entry: AppSnapshot['workspace'][number]) => {
    setSelectedId(entry.id);
    setPreview(null);
    if (entry.kind === 'folder' || !entry.projectId || !entry.fileId) return;
    setLoading(true);
    try {
      setPreview(await apiClient.previewProjectFile(entry.projectId, entry.fileId));
    } catch (error) {
      onToast(error instanceof Error ? error.message : 'Workspace file preview failed.');
    } finally {
      setLoading(false);
    }
  };
  return <div className="workspace-grid"><section className="panel workspace-tree"><div className="panel-topline"><div><span className="eyebrow">ACTIVE PROJECT</span><h3>Workspace</h3></div><span className="status-badge badge-completed"><span className="status-dot" />Live index</span></div><div className="workspace-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search indexed workspace" aria-label="Search indexed workspace" /></div><div className="index-status"><div className="status-dot status-green" /><span>Project and file metadata</span><strong>{snapshot.workspace.length} entries loaded</strong></div><div className="workspace-list">{entries.length ? entries.map((entry) => <button className={`workspace-entry ${selectedId === entry.id ? 'workspace-entry-selected' : ''}`} key={entry.id} onClick={() => void selectEntry(entry)}><span className="file-icon">{entry.kind === 'folder' ? <FolderTree size={16} /> : entry.name.endsWith('.toml') ? <Settings2 size={16} /> : <FileCode2 size={16} />}</span><span><strong>{entry.name}</strong><small>{entry.path}</small></span><span className="workspace-detail">{entry.detail ?? 'Live metadata unavailable'}</span></button>) : <div className="empty-state">No live workspace entries match this query.</div>}</div></section><section className="panel code-preview"><div className="code-toolbar"><div className="file-tab"><FileCode2 size={15} />Live file preview</div></div>{loading ? <div className="empty-state"><LoaderCircle size={18} className="spin" /> Loading persisted file…</div> : preview ? <><div className="preview-meta"><strong>{preview.filename}</strong><span>{preview.mime_type} · {preview.size} bytes{preview.truncated ? ' · preview truncated' : ''}</span></div>{preview.is_text && preview.content !== undefined ? <pre>{preview.content}</pre> : <p className="muted-copy">This binary file is available in the protected project workspace but has no text preview.</p>}</> : <p className="muted-copy">{selected ? selected.kind === 'folder' ? 'Select a file inside this project to preview persisted content.' : 'No preview was returned for this file.' : 'Select a file from the workspace index to preview its persisted content.'}</p>}</section></div>;
}

function ArtifactsView({ snapshot, onToast }: { snapshot: AppSnapshot; onToast: (message: string) => void }) { const [preview, setPreview] = useState<{ filename: string; content?: string; download_url?: string } | null>(null); const openPreview = async (artifact: Artifact) => { try { const result = await apiClient.previewArtifact(artifact.id); setPreview(result); } catch (error) { onToast(error instanceof Error ? error.message : 'Artifact preview failed.'); } }; return <>{snapshot.artifacts.length ? <section className="artifact-grid">{snapshot.artifacts.map((artifact) => <article className="panel artifact-card" key={artifact.id}><div className="artifact-icon"><FileText size={20} /></div><div className="artifact-body"><div className="artifact-title"><h3>{artifact.name}</h3><span className={`artifact-status artifact-${artifact.status}`}>{artifact.status.replace('_', ' ')}</span></div><p>{artifact.type} · {artifact.size} · {artifact.updatedAt}</p><div className="artifact-footer"><span>Task {artifact.taskId}</span><button className="text-button" onClick={() => openPreview(artifact)}>Preview <ArrowUpRight size={13} /></button></div></div></article>)}</section> : <div className="empty-state">No live artifacts have been returned.</div>}{preview && <section className="panel artifact-preview"><div className="panel-topline"><div><span className="eyebrow">ARTIFACT PREVIEW</span><h3>{preview.filename}</h3></div><button className="icon-button" onClick={() => setPreview(null)} aria-label="Close preview"><X size={15} /></button></div>{preview.content !== undefined ? <pre>{preview.content}</pre> : preview.download_url ? <a href={preview.download_url} target="_blank" rel="noreferrer">Download artifact</a> : <p className="muted-copy">No preview content returned.</p>}</section>}</>; }

function IntegrationsView({ snapshot }: { snapshot: AppSnapshot }) { return <><section className="capability-grid">{snapshot.capabilities.length ? snapshot.capabilities.map((capability) => <article className="panel capability-card" key={capability.id}><div className={`capability-icon capability-${capability.state}`}><Network size={17} /></div><div><div className="capability-title"><h3>{capability.label}</h3><span className={`capability-state state-${capability.state}`}>{capability.state.replace('_', ' ')}</span></div><p>{capability.detail}</p></div><span className="capability-latency">{capability.latency}</span></article>) : <div className="empty-state">No live capability records have been returned.</div>}</section><section className="panel provider-panel"><div className="panel-topline"><div><span className="eyebrow">CONNECTOR HUB</span><h3>Available integrations</h3></div><span className="eyebrow">{snapshot.connectors.length} discovered</span></div><div className="provider-list">{snapshot.connectors.length ? snapshot.connectors.map((connector) => <div className="provider-row" key={connector.id}><div className="provider-avatar"><Network size={16} /></div><div className="provider-name"><strong>{connector.name}</strong><span>{connector.description || 'No connector description returned.'}</span></div><span className={`status-badge badge-${connector.configured ? 'completed' : 'waiting'}`}><span className="status-dot" />{connector.status}</span><span className="provider-latency">{connector.tools.length} tools</span></div>) : <div className="empty-state">No live connectors have been returned.</div>}</div></section></>; }

function OperationsView({ snapshot }: { snapshot: AppSnapshot }) { return <><section className="ops-metrics"><Metric label="Loaded tasks" value={String(snapshot.tasks.length)} detail="Live server response" tone="accent" /><Metric label="Loaded events" value={String(snapshot.timeline.length)} detail="Live event history" tone="success" /><Metric label="Capabilities" value={String(snapshot.capabilities.length)} detail="Live health response" /><Metric label="Connection" value={snapshot.connection} detail="WebSocket client state" /></section><section className="ops-grid"><article className="panel"><div className="panel-topline"><div><span className="eyebrow">RUNTIME SIGNALS</span><h3>System timeline</h3></div></div><div className="event-list">{snapshot.timeline.length ? snapshot.timeline.map((event) => <div className="event-row" key={event.id}><span className={`event-line event-${event.tone}`} /><div className="event-content"><div><strong>{event.label}</strong><time>{event.time}</time></div><p>{event.detail}</p></div></div>) : <div className="empty-state">No live event history has been returned.</div>}</div></article><article className="panel ops-checks"><div className="panel-topline"><div><span className="eyebrow">READINESS</span><h3>Control gates</h3></div><CircleAlert className="healthy-icon" size={19} /></div>{snapshot.capabilities.length ? snapshot.capabilities.map((capability) => <div className="readiness-row" key={capability.id}><span className={`status-dot ${capability.state === 'healthy' ? 'status-green' : 'status-amber'}`} /><span>{capability.label}</span><strong>{capability.state}</strong></div>) : <div className="empty-state">No live readiness records have been returned.</div>}</article></section></>; }

function MemoryView({ memories, onToast }: { memories: MemoryEntry[]; onToast: (message: string) => void }) {
  const [query, setQuery] = useState('');
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [busy, setBusy] = useState(false);
  const filtered = memories.filter((memory) => `${memory.name} ${memory.scope} ${memory.content}`.toLowerCase().includes(query.toLowerCase()));
  const refresh = async () => { try { dispatch({ type: 'hydrate', snapshot: await apiClient.snapshot() }); } catch (error) { onToast(error instanceof Error ? error.message : 'Memory refresh failed.'); } };
  const save = async (event: React.FormEvent) => { event.preventDefault(); if (!name.trim() || !content.trim() || busy) return; setBusy(true); try { await apiClient.saveMemory(name.trim(), content.trim()); await refresh(); setName(''); setContent(''); onToast('Memory saved to the persistent store.'); } catch (error) { onToast(error instanceof Error ? error.message : 'Memory could not be saved.'); } finally { setBusy(false); } };
  const remove = async (memory: MemoryEntry) => { if (!window.confirm(`Delete memory “${memory.name}”?`)) return; setBusy(true); try { await apiClient.deleteMemory(memory.name, memory.scope); await refresh(); onToast('Memory deleted from the persistent store.'); } catch (error) { onToast(error instanceof Error ? error.message : 'Memory could not be deleted.'); } finally { setBusy(false); } };
  return <section className="simple-view memory-view"><div className="simple-icon"><Database size={20} /></div><div className="eyebrow">SCOPED KNOWLEDGE</div><h2>Memory</h2><p>Live memory records from the persistent memory store.</p><form className="memory-compose panel" onSubmit={save}><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Memory name" aria-label="Memory name" /><textarea value={content} onChange={(event) => setContent(event.target.value)} placeholder="What should BRJARVIS remember?" aria-label="Memory content" /><button className="primary-button" disabled={busy || !name.trim() || !content.trim()}>{busy ? <LoaderCircle size={15} className="spin" /> : <Plus size={15} />}Save memory</button></form><div className="workspace-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search live memory" aria-label="Search live memory" /></div><div className="simple-cards">{filtered.length ? filtered.map((memory) => <div className="panel simple-card" key={memory.id}><span>{memory.scope}</span><strong>{memory.name}<small>{memory.content}</small></strong><time>{memory.updatedAt}</time><button className="icon-button" onClick={() => void remove(memory)} disabled={busy} aria-label={`Delete ${memory.name}`} title="Delete memory"><X size={15} /></button></div>) : <div className="empty-state">No live memory records match this query.</div>}</div></section>;
}

function CareerView({ profile, onToast }: { profile: AppSnapshot['career']; onToast: (message: string) => void }) { const [busy, setBusy] = useState(false); const [resume, setResume] = useState<Record<string, unknown> | null>(null); const generateResume = async () => { setBusy(true); try { const result = await apiClient.createCareerResume(); setResume(result); onToast(String(result.status ?? '').toUpperCase() === 'SUCCESS_VERIFIED' ? 'Resume generated and verified by Career OS.' : 'Resume generation completed; review the returned Career OS status.'); } catch (error) { onToast(error instanceof Error ? error.message : 'Resume generation failed.'); } finally { setBusy(false); } }; if (!profile) return <section className="simple-view"><div className="simple-icon"><BriefcaseBusiness size={20} /></div><div className="eyebrow">FOCUSED WORKSPACE</div><h2>Career profile unavailable</h2><p>The Career OS API did not return a profile for this session.</p></section>; return <section className="simple-view"><div className="simple-icon"><BriefcaseBusiness size={20} /></div><div className="eyebrow">FOCUSED WORKSPACE</div><h2>{profile.name || 'Career profile'}</h2><p>{profile.headline || 'No headline returned'}{profile.location ? ` · ${profile.location}` : ''}</p><div className="simple-cards"><div className="panel simple-card"><span>Skills</span><strong>{profile.skills.length ? profile.skills.join(', ') : 'No skills returned'}</strong></div>{profile.completeness !== undefined && <div className="panel simple-card"><span>Completeness</span><strong>{profile.completeness}%</strong></div>}<div className="panel simple-card"><span>Resume</span><strong>{resume ? `Version ${String(resume.version_id ?? 'created')}` : 'Generate a current ATS-ready resume'}</strong><button type="button" className="primary-button" onClick={() => void generateResume()} disabled={busy}>{busy ? <LoaderCircle size={15} className="spin" /> : <FileText size={15} />} {busy ? 'Generating…' : 'Generate resume'}</button></div></div></section>; }

function BootScreen() {
  return <div className="auth-screen"><div className="auth-card boot-card"><div className="brand-mark"><Sparkles size={18} /></div><div className="eyebrow accent-eyebrow">BRJARVIS / STARTING</div><h1>Preparing your control plane</h1><p>Loading secure session, capabilities, and the latest task state.</p><LoaderCircle size={20} className="spin boot-spinner" /></div></div>;
}

function LoginScreen({ busy, error, onSubmit }: { busy: boolean; error: string | null; onSubmit: (apiKey: string) => void }) {
  const [apiKey, setApiKey] = useState('');
  return <div className="auth-screen"><div className="auth-card"><div className="auth-brand"><div className="brand-mark"><Sparkles size={18} /></div><div><div className="brand-name">BRJARVIS</div><div className="brand-subtitle">CONTROL PLANE</div></div></div><div className="eyebrow accent-eyebrow">SECURE SESSION</div><h1>Sign in to continue</h1><p>Use the local server API key to create a short-lived browser session. The key is sent over the current connection and is not stored in browser storage.</p><form onSubmit={(event) => { event.preventDefault(); if (apiKey.trim()) onSubmit(apiKey); }}><label className="auth-label" htmlFor="server-api-key">Server API key</label><input id="server-api-key" className="auth-input" type="password" autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="Paste the configured server key" autoFocus /><button className="primary-button auth-submit" disabled={busy || !apiKey.trim()}>{busy ? <LoaderCircle size={16} className="spin" /> : <LockKeyhole size={16} />}{busy ? 'Creating session…' : 'Create secure session'}</button></form>{error && <div className="auth-error" role="alert"><CircleAlert size={15} />{error}</div>}<div className="auth-note"><ShieldCheck size={14} /><span>Session cookie is HttpOnly and expires according to server policy.</span></div></div></div>;
}

function BusinessView({ snapshot, onView }: { snapshot: AppSnapshot; onView: (view: ViewId) => void }) {
  const projects = snapshot.workspace.filter((entry) => entry.kind === 'folder');
  const activeTasks = snapshot.tasks.filter((task) => ['queued', 'planning', 'running', 'waiting', 'retrying'].includes(task.status));
  return <section className="business-view"><div className="business-intro"><div><div className="simple-icon"><Building2 size={20} /></div><div className="eyebrow">BUSINESS OPERATIONS</div><h2>Operate from live workspace state.</h2><p>This view aggregates the authoritative projects, contacts, and execution state already stored by BRJARVIS. External CRM or invoicing data appears only after a connector is configured.</p></div><button className="secondary-button" onClick={() => onView('integrations')}><Network size={15} />Configure providers</button></div><div className="ops-metrics"><Metric label="Projects" value={String(projects.length)} detail="Live workspace index" tone="accent" /><Metric label="Contacts" value={String(snapshot.contacts.length)} detail="Encrypted contact store" /><Metric label="Active work" value={String(activeTasks.length)} detail="Durable task state" tone="success" /><Metric label="Artifacts" value={String(snapshot.artifacts.length)} detail="Verified output index" /></div><div className="business-grid"><section className="panel business-panel"><div className="panel-topline"><div><span className="eyebrow">RELATIONSHIPS</span><h3>Contacts</h3></div><button className="text-button" onClick={() => onView('memory')}>Manage records <ArrowUpRight size={13} /></button></div>{snapshot.contacts.length ? snapshot.contacts.slice(0, 8).map((contact) => <div className="business-row" key={contact.id}><UserRound size={15} /><strong>{contact.name}</strong><span>{contact.organization || contact.email || contact.phone || 'No organization details'}</span></div>) : <div className="empty-state">No contacts are stored yet. Add contacts through the API or legacy workspace importer.</div>}</section><section className="panel business-panel"><div className="panel-topline"><div><span className="eyebrow">DELIVERY</span><h3>Current projects</h3></div><button className="text-button" onClick={() => onView('workspace')}>Open workspace <ArrowUpRight size={13} /></button></div>{projects.length ? projects.slice(0, 8).map((project) => <div className="business-row" key={project.id}><FolderTree size={15} /><strong>{project.name}</strong><span>{project.detail || project.path}</span></div>) : <div className="empty-state">No projects are stored yet. Create one through the project API.</div>}</section></div></section>;
}

function CommandPalette({ onClose, onNavigate }: { onClose: () => void; onNavigate: (view: ViewId) => void }) { const [query, setQuery] = useState(''); const items = navigation.filter((item) => `${item.label} ${item.description}`.toLowerCase().includes(query.toLowerCase())); return <div className="palette-backdrop" onClick={onClose}><div className="command-palette" onClick={(event) => event.stopPropagation()}><div className="palette-input"><Search size={18} /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Jump to a surface or action…" /></div><div className="palette-list">{items.map((item) => { const Icon = navIcons[item.id]; return <button key={item.id} onClick={() => onNavigate(item.id)}><span className="palette-icon"><Icon size={16} /></span><span><strong>{item.label}</strong><small>{item.description}</small></span><kbd>↵</kbd></button>; })}</div><div className="palette-footer"><span><kbd>↑↓</kbd> Navigate</span><span><kbd>↵</kbd> Open</span><span><kbd>esc</kbd> Close</span></div></div></div>; }
