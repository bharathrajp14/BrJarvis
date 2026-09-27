import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react';
import type { FormEvent } from 'react';
import {
  Activity, ArrowLeft, ArrowRight, Bell, Bot, BriefcaseBusiness, Building2, Check, ChevronRight,
  CircleAlert, CircleCheck, CircleDot, Clock3, Command, Database, Download, ExternalLink, FileCheck2,
  FileCode2, FilePlus2, FileText, FolderOpen, FolderPlus, FolderTree, Gauge, Globe2, HeartHandshake,
  KeyRound, Layers3, LayoutDashboard, ListFilter, ListTodo, LoaderCircle, LockKeyhole, Menu,
  Moon, Network, PanelLeftClose, Plus, RefreshCw, Rocket, Search, Send, Settings2, ShieldCheck,
  Sparkles, Star, Sun, TerminalSquare, Trash2, Upload, UserPlus, UserRound, UsersRound, Wifi,
  WifiOff, X, Zap,
} from 'lucide-react';
import type { NavigationItem } from '../contracts/api';
import type {
  AppSnapshot, Artifact, CareerJob, ConnectionState, ContactSummary, ExecutionMode, MemoryEntry,
  PanelHealth, SearchResult, Task, TaskStatus, TimelineEvent, ViewId, WorkspaceEntry,
} from '../contracts/domain';
import { apiClient } from '../platform/api-client';
import { loadAuthSnapshot, loginWithApiKey, type AuthSnapshot } from '../platform/auth-client';
import { RealtimeClient } from '../platform/websocket-client';
import { dispatch, getSnapshot, subscribe } from '../state/app-store';
import '../styles/tokens.css';
import '../styles/globals.css';

const navigation: NavigationItem[] = [
  { id: 'command', label: 'Command', eyebrow: '01', description: 'Launch verified work from one focused prompt.' },
  { id: 'tasks', label: 'Tasks', eyebrow: '02', description: 'Inspect durable execution, checkpoints, and outcomes.' },
  { id: 'approvals', label: 'Approvals', eyebrow: '03', description: 'Review protected actions before they run.' },
  { id: 'workspace', label: 'Workspace', eyebrow: '04', description: 'Manage projects, files, and source context.' },
  { id: 'artifacts', label: 'Artifacts', eyebrow: '05', description: 'Preview, verify, and download generated output.' },
  { id: 'memory', label: 'Memory', eyebrow: '06', description: 'Curate persistent knowledge used by BRJARVIS.' },
  { id: 'career', label: 'Career OS', eyebrow: '07', description: 'Turn your profile into targeted career action.' },
  { id: 'business', label: 'Relationships', eyebrow: '08', description: 'Operate contacts and project delivery records.' },
  { id: 'integrations', label: 'Integrations', eyebrow: '09', description: 'Connect providers and validate capabilities.' },
  { id: 'operations', label: 'Operations', eyebrow: '10', description: 'Monitor runtime health, events, and readiness.' },
];

const navIcons: Record<ViewId, typeof Command> = {
  command: Command,
  tasks: ListTodo,
  approvals: ShieldCheck,
  workspace: FolderTree,
  artifacts: Layers3,
  memory: Database,
  career: BriefcaseBusiness,
  business: UsersRound,
  integrations: Network,
  operations: Gauge,
};

const sections: Array<{ label: string; views: ViewId[] }> = [
  { label: 'EXECUTE', views: ['command', 'tasks', 'approvals'] },
  { label: 'ORGANIZE', views: ['workspace', 'artifacts', 'memory'] },
  { label: 'OPERATE', views: ['career', 'business', 'integrations', 'operations'] },
];

interface ToastState { message: string; tone: 'success' | 'error' | 'info' }

type Refresh = () => Promise<boolean>;
type Toast = (message: string, tone?: ToastState['tone']) => void;

function useAppSnapshot() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function shortDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date);
}

function viewFromHash(): ViewId | null {
  const value = globalThis.location?.hash.replace(/^#\/?/, '') as ViewId;
  return navigation.some((item) => item.id === value) ? value : null;
}

export function App() {
  const snapshot = useAppSnapshot();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [compactNav, setCompactNav] = useState(false);
  const [lightMode, setLightMode] = useState(() => globalThis.localStorage?.getItem('brjarvis-theme') === 'light');
  const [command, setCommand] = useState('');
  const [mode, setMode] = useState<ExecutionMode>('smart');
  const [privacy, setPrivacy] = useState<'balanced' | 'local_only'>('balanced');
  const [searchOpen, setSearchOpen] = useState(false);
  const [commandBusy, setCommandBusy] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const [operator, setOperator] = useState({ label: 'Operator', scope: 'Local session' });
  const [auth, setAuth] = useState<AuthSnapshot | null>(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const refreshSequence = useRef(0);
  const [realtime] = useState(() => new RealtimeClient((status) => dispatch({ type: 'connection', status })));

  const notify: Toast = useCallback((message, tone = 'success') => setToast({ message, tone }), []);

  useEffect(() => {
    const initialView = viewFromHash();
    if (initialView) dispatch({ type: 'view', view: initialView });
    const onHistory = () => {
      const next = viewFromHash();
      if (next) dispatch({ type: 'view', view: next });
    };
    globalThis.addEventListener('hashchange', onHistory);
    void loadAuthSnapshot().then((currentAuth) => {
      setAuth(currentAuth);
      setOperator({ label: currentAuth.label, scope: currentAuth.scope });
    });
    return () => globalThis.removeEventListener('hashchange', onHistory);
  }, []);

  useEffect(() => {
    globalThis.localStorage?.setItem('brjarvis-theme', lightMode ? 'light' : 'dark');
  }, [lightMode]);

  const refreshSnapshot = useCallback(async () => {
    const sequence = ++refreshSequence.current;
    try {
      const data = await apiClient.snapshot();
      if (sequence !== refreshSequence.current) return false;
      dispatch({ type: 'hydrate', snapshot: data });
      return data.backend !== 'offline';
    } catch {
      return false;
    }
  }, []);

  useEffect(() => {
    if (!auth || (auth.authRequired && !auth.authenticated)) return;
    void refreshSnapshot();
    void realtime.connect();
    const unsubscribe = realtime.subscribe((event) => {
      if (event.type === 'timeline.appended' && 'event' in event && event.event) {
        dispatch({ type: 'timeline-append', event: event.event as TimelineEvent });
        return;
      }
      const eventType = String(event.type).toLowerCase();
      if (eventType.startsWith('task.') || eventType.startsWith('message.') || eventType.startsWith('approval.') || eventType === 'serverready' || eventType === 'connection.ready') {
        void refreshSnapshot();
      }
    });
    const keydown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
      if (event.key === 'Escape') {
        setSearchOpen(false);
        setMobileOpen(false);
      }
    };
    globalThis.addEventListener('keydown', keydown);
    return () => {
      unsubscribe();
      realtime.disconnect();
      globalThis.removeEventListener('keydown', keydown);
    };
  }, [auth, realtime, refreshSnapshot]);

  useEffect(() => {
    if (!toast) return;
    const timeout = globalThis.setTimeout(() => setToast(null), 4200);
    return () => globalThis.clearTimeout(timeout);
  }, [toast]);

  const selectView = useCallback((view: ViewId) => {
    dispatch({ type: 'view', view });
    setMobileOpen(false);
    if (globalThis.location.hash !== `#/${view}`) globalThis.location.hash = `/${view}`;
  }, []);

  const submitLogin = async (apiKey: string) => {
    setAuthBusy(true);
    setAuthError(null);
    try {
      const currentAuth = await loginWithApiKey(apiKey);
      setAuth(currentAuth);
      setOperator({ label: currentAuth.label, scope: currentAuth.scope });
    } catch (error) {
      setAuthError(errorMessage(error, 'Authentication failed.'));
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
      const idempotencyKey = globalThis.crypto?.randomUUID?.() ?? `ui-${Date.now()}`;
      const result = await apiClient.createTask({ goal, mode, privacy, idempotencyKey });
      dispatch({ type: 'task-upsert', task: result.task });
      setCommand('');
      notify(result.acknowledgement);
      selectView('tasks');
    } catch (error) {
      notify(errorMessage(error, 'The command could not be submitted.'), 'error');
    } finally {
      setCommandBusy(false);
    }
  };

  const activeNav = navigation.find((item) => item.id === snapshot.activeView) ?? navigation[0];
  const connectionLabel = snapshot.connection === 'connected' ? 'Realtime' : snapshot.connection === 'connecting' ? 'Connecting' : 'Offline';

  return (
    <div className={`app ${lightMode ? 'theme-light' : ''} ${compactNav ? 'nav-compact' : ''}`}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside id="primary-navigation" className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`} aria-label="Application navigation">
        <div className="brand">
          <div className="brand-glyph" aria-hidden="true"><Sparkles size={19} /></div>
          <div className="brand-copy"><strong>BRJARVIS</strong><span>CONTROL PLANE</span></div>
          <button className="icon-button mobile-only" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={19} /></button>
        </div>
        <div className={`runtime-card runtime-${snapshot.backend}`}>
          <div className="runtime-orb"><CircleDot size={16} /></div>
          <div><span>LOCAL RUNTIME</span><strong>{snapshot.backend === 'online' ? 'Operational' : snapshot.backend === 'degraded' ? 'Degraded' : 'Unavailable'}</strong></div>
        </div>
        <nav className="nav-list">
          {sections.map((section) => (
            <div className="nav-section" key={section.label}>
              <span className="nav-label">{section.label}</span>
              {section.views.map((view) => {
                const item = navigation.find((candidate) => candidate.id === view)!;
                const Icon = navIcons[view];
                const badge = view === 'approvals' ? snapshot.approvals.length : view === 'operations' ? snapshot.unreadNotifications : 0;
                return (
                  <button key={view} className={`nav-item ${snapshot.activeView === view ? 'active' : ''}`} onClick={() => selectView(view)} aria-current={snapshot.activeView === view ? 'page' : undefined} title={compactNav ? item.label : undefined}>
                    <Icon size={18} /><span>{item.label}</span>{badge > 0 && <b>{badge > 99 ? '99+' : badge}</b>}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="operator"><div className="operator-avatar"><UserRound size={17} /></div><div><strong>{operator.label}</strong><span>{operator.scope}</span></div></div>
          <button className="collapse-button desktop-only" onClick={() => setCompactNav((value) => !value)} aria-label={compactNav ? 'Expand navigation' : 'Collapse navigation'}><PanelLeftClose size={17} /><span>Collapse</span></button>
        </div>
      </aside>
      {mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}

      <div className="shell">
        <header className="topbar">
          <div className="topbar-start">
            <button className="icon-button mobile-only" onClick={() => setMobileOpen(true)} aria-label="Open navigation" aria-controls="primary-navigation" aria-expanded={mobileOpen}><Menu size={20} /></button>
            <div className="breadcrumb"><span>BRJARVIS</span><ChevronRight size={13} /><strong>{activeNav.label}</strong></div>
          </div>
          <div className="topbar-end">
            <button className="search-trigger" onClick={() => setSearchOpen(true)}><Search size={16} /><span>Search control plane</span><kbd>Ctrl K</kbd></button>
            <div className={`live-pill live-${snapshot.connection}`} title="WebSocket connection state">{snapshot.connection === 'connected' ? <Wifi size={14} /> : <WifiOff size={14} />}<span>{connectionLabel}</span></div>
            <button className="icon-button notification-button" onClick={() => selectView('operations')} aria-label={`Open events, ${snapshot.unreadNotifications} unread`}>
              <Bell size={18} />{snapshot.unreadNotifications > 0 && <span>{snapshot.unreadNotifications > 9 ? '9+' : snapshot.unreadNotifications}</span>}
            </button>
            <button className="icon-button" onClick={() => setLightMode((value) => !value)} aria-label={lightMode ? 'Use dark theme' : 'Use light theme'}>{lightMode ? <Sun size={18} /> : <Moon size={18} />}</button>
          </div>
        </header>

        <main id="main-content" className="main" tabIndex={-1}>
          <PageHeader item={activeNav} view={snapshot.activeView} onCommand={() => selectView('command')} onRefresh={refreshSnapshot} />
          {snapshot.activeView === 'command' && <CommandCenter snapshot={snapshot} command={command} setCommand={setCommand} mode={mode} setMode={setMode} privacy={privacy} setPrivacy={setPrivacy} busy={commandBusy} onSubmit={submitCommand} onView={selectView} onToast={notify} />}
          {snapshot.activeView === 'tasks' && <TasksView snapshot={snapshot} onView={selectView} />}
          {snapshot.activeView === 'approvals' && <ApprovalsView snapshot={snapshot} onToast={notify} onRefresh={refreshSnapshot} />}
          {snapshot.activeView === 'workspace' && <WorkspaceView snapshot={snapshot} onToast={notify} onRefresh={refreshSnapshot} />}
          {snapshot.activeView === 'artifacts' && <ArtifactsView snapshot={snapshot} onToast={notify} onRefresh={refreshSnapshot} />}
          {snapshot.activeView === 'memory' && <MemoryView snapshot={snapshot} onToast={notify} onRefresh={refreshSnapshot} />}
          {snapshot.activeView === 'career' && <CareerView snapshot={snapshot} onToast={notify} />}
          {snapshot.activeView === 'business' && <BusinessView snapshot={snapshot} onToast={notify} onRefresh={refreshSnapshot} onView={selectView} />}
          {snapshot.activeView === 'integrations' && <IntegrationsView snapshot={snapshot} onToast={notify} onRefresh={refreshSnapshot} />}
          {snapshot.activeView === 'operations' && <OperationsView snapshot={snapshot} onToast={notify} onRefresh={refreshSnapshot} />}
        </main>
      </div>

      {searchOpen && <CommandPalette onClose={() => setSearchOpen(false)} onNavigate={(view) => { selectView(view); setSearchOpen(false); }} />}
      {toast && <div className={`toast toast-${toast.tone}`} role={toast.tone === 'error' ? 'alert' : 'status'}>{toast.tone === 'error' ? <CircleAlert size={18} /> : toast.tone === 'success' ? <CircleCheck size={18} /> : <CircleDot size={18} />}<span>{toast.message}</span><button className="icon-button" onClick={() => setToast(null)} aria-label="Dismiss message"><X size={16} /></button></div>}
    </div>
  );
}

function PageHeader({ item, view, onCommand, onRefresh }: { item: NavigationItem; view: ViewId; onCommand: () => void; onRefresh: Refresh }) {
  const [busy, setBusy] = useState(false);
  const refresh = async () => { setBusy(true); await onRefresh(); setBusy(false); };
  return <header className="page-header"><div><div className="page-kicker"><span>{item.eyebrow}</span> CONTROL SURFACE</div><h1>{item.label}</h1><p>{item.description}</p></div><div className="page-actions"><button className="icon-button" onClick={() => void refresh()} disabled={busy} aria-label="Refresh live data">{busy ? <LoaderCircle className="spin" size={17} /> : <RefreshCw size={17} />}</button>{view !== 'command' && <button className="button secondary" onClick={onCommand}><Command size={16} />New command</button>}</div></header>;
}

function PanelState({ health, empty, children, onRetry }: { health?: PanelHealth; empty: string; children: React.ReactNode; onRetry?: Refresh }) {
  if (health?.state === 'error') return <div className="state-card error-state"><CircleAlert size={20} /><div><strong>Could not load this surface</strong><p>{health.message ?? 'The server did not return live data.'}</p></div>{onRetry && <button className="button tertiary" onClick={() => void onRetry()}>Retry</button>}</div>;
  if (health?.state === 'empty') return <div className="state-card"><Sparkles size={20} /><div><strong>Nothing here yet</strong><p>{empty}</p></div></div>;
  return <>{children}</>;
}

function Metric({ label, value, detail, tone = 'default', icon: Icon }: { label: string; value: string; detail: string; tone?: 'default' | 'accent' | 'success' | 'warning'; icon?: typeof Activity }) {
  return <div className={`metric tone-${tone}`}>{Icon && <div className="metric-icon"><Icon size={16} /></div>}<span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function CommandCenter({ snapshot, command, setCommand, mode, setMode, privacy, setPrivacy, busy, onSubmit, onView, onToast }: { snapshot: AppSnapshot; command: string; setCommand: (value: string) => void; mode: ExecutionMode; setMode: (mode: ExecutionMode) => void; privacy: 'balanced' | 'local_only'; setPrivacy: (value: 'balanced' | 'local_only') => void; busy: boolean; onSubmit: () => void; onView: (view: ViewId) => void; onToast: Toast }) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const activeTasks = snapshot.tasks.filter((task) => ['queued', 'planning', 'running', 'waiting', 'retrying'].includes(task.status));
  const activeTask = snapshot.tasks.find((task) => task.id === snapshot.activeTaskId) ?? activeTasks[0];
  const importKnowledge = async (file: File) => {
    setImporting(true);
    try {
      await apiClient.importFile(file);
      onToast(`${file.name} was imported into persistent knowledge.`);
    } catch (error) {
      onToast(errorMessage(error, 'File import failed.'), 'error');
    } finally { setImporting(false); }
  };
  return <>
    <section className="command-hero panel">
      <div className="hero-copy"><div className="hero-status"><span className={`pulse ${snapshot.backend}`} />{snapshot.backend === 'online' ? 'RUNTIME READY' : 'RUNTIME ATTENTION REQUIRED'}</div><h2>Move from intent<br />to <em>verified outcome.</em></h2><p>Describe the result you need. BRJARVIS plans the path, requests permission when risk changes, and records what actually happened.</p><div className="hero-links"><button onClick={() => onView('tasks')}><Activity size={16} />Inspect active work</button><button onClick={() => onView('workspace')}><FolderOpen size={16} />Open workspace</button></div></div>
      <div className="hero-metrics"><Metric label="Active work" value={String(activeTasks.length)} detail="Durable tasks" tone="accent" icon={Rocket} /><Metric label="Pending gates" value={String(snapshot.approvals.length)} detail="Need your review" tone={snapshot.approvals.length ? 'warning' : 'default'} icon={ShieldCheck} /><Metric label="Verified output" value={String(snapshot.artifacts.filter((item) => item.status === 'verified').length)} detail="Artifacts" tone="success" icon={FileCheck2} /></div>
    </section>
    <section className="composer panel">
      <div className="composer-heading"><div><span className="eyebrow">NEW EXECUTION</span><h3>What outcome should we create?</h3></div><span className="secure-chip"><LockKeyhole size={14} />Policy governed</span></div>
      <textarea value={command} onChange={(event) => setCommand(event.target.value)} onKeyDown={(event) => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') onSubmit(); }} placeholder="Example: Audit this repository, fix the failing checkout flow, run focused tests, and summarize the evidence…" aria-label="Command goal" />
      <div className="composer-footer">
        <div className="composer-tools"><input ref={fileInput} type="file" hidden onChange={(event) => { const file = event.target.files?.[0]; if (file) void importKnowledge(file); event.currentTarget.value = ''; }} /><button className="tool-button" onClick={() => fileInput.current?.click()} disabled={importing}>{importing ? <LoaderCircle className="spin" size={15} /> : <Upload size={15} />}Import to knowledge</button><span>Ctrl + Enter to start</span></div>
        <div className="execution-controls"><div className="segmented" role="group" aria-label="Execution mode">{(['fast', 'smart', 'deep'] as ExecutionMode[]).map((value) => <button key={value} className={mode === value ? 'selected' : ''} aria-pressed={mode === value} onClick={() => setMode(value)}>{value}</button>)}</div><button className={`privacy-button ${privacy === 'local_only' ? 'selected' : ''}`} aria-pressed={privacy === 'local_only'} onClick={() => setPrivacy(privacy === 'balanced' ? 'local_only' : 'balanced')}><LockKeyhole size={14} />{privacy === 'local_only' ? 'Local only' : 'Balanced'}</button><button className="button primary execute" disabled={busy || !command.trim() || snapshot.backend === 'offline'} onClick={onSubmit}>{busy ? <LoaderCircle className="spin" size={17} /> : <Send size={17} />}{busy ? 'Starting' : 'Start task'}</button></div>
      </div>
    </section>
    <section className="section-block"><div className="section-title"><div><span className="eyebrow">LIVE EXECUTION</span><h2>Current focus</h2></div><button className="text-button" onClick={() => onView('tasks')}>View all tasks <ArrowRight size={15} /></button></div><div className="dashboard-grid"><TaskFocus task={activeTask} onOpen={() => onView('tasks')} /><EventPreview events={snapshot.timeline.slice(0, 5)} onOpen={() => onView('operations')} /></div></section>
  </>;
}

function TaskFocus({ task, onOpen }: { task?: Task; onOpen: () => void }) {
  if (!task) return <article className="panel focus-panel"><div className="panel-heading"><div><span className="eyebrow">CURRENT FOCUS</span><h3>No active task</h3></div><StatusBadge status="queued" /></div><div className="state-card compact"><Rocket size={20} /><div><strong>Ready for a new outcome</strong><p>Start a command to create durable execution state.</p></div></div></article>;
  return <article className="panel focus-panel"><div className="panel-heading"><div><span className="eyebrow">CURRENT FOCUS</span><h3>{task.title}</h3></div><StatusBadge status={task.status} /></div><p className="muted">{task.summary}</p><div className="progress-copy"><span>{task.phase || 'Overall progress'}</span><strong>{Math.round(task.progress)}%</strong></div><Progress value={task.progress} /><div className="mini-steps">{task.steps.slice(0, 4).map((step) => <div key={step.id}><span className={`step-dot ${step.status}`}>{step.status === 'complete' ? <Check size={11} /> : step.status === 'active' ? <LoaderCircle className="spin" size={11} /> : null}</span><div><strong>{step.label}</strong><small>{step.detail || step.status}</small></div></div>)}</div><button className="text-button" onClick={onOpen}>Inspect task details <ArrowRight size={15} /></button></article>;
}

function EventPreview({ events, onOpen }: { events: TimelineEvent[]; onOpen: () => void }) {
  return <article className="panel event-panel"><div className="panel-heading"><div><span className="eyebrow">SYSTEM SIGNALS</span><h3>Recent events</h3></div><Bell size={18} /></div>{events.length ? <div className="timeline">{events.map((event) => <div className={`timeline-item ${event.tone}`} key={event.id}><span /><div><div><strong>{event.label}</strong><time>{shortDate(event.time)}</time></div><p>{event.detail}</p></div></div>)}</div> : <div className="state-card compact"><Bell size={19} /><div><strong>No recent events</strong><p>Runtime notifications will appear here.</p></div></div>}<button className="text-button" onClick={onOpen}>Open operations <ArrowRight size={15} /></button></article>;
}

function TasksView({ snapshot, onView }: { snapshot: AppSnapshot; onView: (view: ViewId) => void }) {
  const [filter, setFilter] = useState<'all' | TaskStatus>('all');
  const [query, setQuery] = useState('');
  const tasks = snapshot.tasks.filter((task) => (filter === 'all' || task.status === filter) && `${task.title} ${task.summary} ${task.provider}`.toLowerCase().includes(query.toLowerCase()));
  const activeTask = snapshot.tasks.find((task) => task.id === snapshot.activeTaskId) ?? tasks[0];
  return <div className="task-layout">
    <section className="task-list-panel panel"><div className="surface-toolbar"><div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search tasks" aria-label="Search tasks" /></div><button className="button secondary" onClick={() => onView('command')}><Plus size={16} />New task</button></div><div className="filter-row" role="group" aria-label="Filter tasks">{(['all', 'running', 'waiting', 'completed', 'failed'] as const).map((value) => <button key={value} className={filter === value ? 'selected' : ''} aria-pressed={filter === value} onClick={() => setFilter(value)}>{value === 'all' ? 'All' : value}</button>)}</div><PanelState health={snapshot.panelHealth.tasks} empty="New commands will appear here with live progress and evidence."><div className="task-list">{tasks.map((task) => <button key={task.id} className={`task-list-item ${task.id === activeTask?.id ? 'selected' : ''}`} onClick={() => dispatch({ type: 'active-task', taskId: task.id })} aria-pressed={task.id === activeTask?.id}><span className={`task-indicator ${task.status}`} /><div><div><strong>{task.title}</strong><StatusBadge status={task.status} /></div><p>{task.summary}</p><small>{shortDate(task.updatedAt)} · {Math.round(task.progress)}%</small></div><ChevronRight size={17} /></button>)}</div></PanelState></section>
    <TaskDetail task={activeTask} />
  </div>;
}

function TaskDetail({ task }: { task?: Task }) {
  if (!task) return <section className="panel detail-panel"><div className="state-card"><ListTodo size={22} /><div><strong>Select a task</strong><p>Execution steps, provider details, and evidence will appear here.</p></div></div></section>;
  return <section className="panel detail-panel"><div className="panel-heading"><div><span className="eyebrow">TASK DETAIL</span><h2>{task.title}</h2></div><StatusBadge status={task.status} /></div><p className="detail-summary">{task.summary}</p><div className="detail-stats"><Metric label="Progress" value={`${Math.round(task.progress)}%`} detail={task.phase || 'Current state'} tone="accent" /><Metric label="Provider" value={task.provider} detail={`${task.mode} execution`} /><Metric label="Artifacts" value={String(task.artifactCount)} detail="Linked output" tone="success" /></div><Progress value={task.progress} /><div className="detail-section"><span className="eyebrow">EXECUTION PATH</span><div className="step-list">{task.steps.map((step, index) => <div className="step-item" key={step.id}><span className={`step-number ${step.status}`}>{step.status === 'complete' ? <Check size={13} /> : index + 1}</span><div><strong>{step.label}</strong><p>{step.detail || (step.status === 'active' ? 'In progress' : step.status === 'complete' ? 'Completed' : step.status === 'blocked' ? 'Blocked' : 'Queued')}</p></div><span className={`step-label ${step.status}`}>{step.status}</span></div>)}</div></div><div className="detail-note"><ShieldCheck size={17} /><span>Task state is authoritative. Pause, retry, and cancellation controls are shown only when the runtime exposes those operations.</span></div></section>;
}

function ApprovalsView({ snapshot, onToast, onRefresh }: { snapshot: AppSnapshot; onToast: Toast; onRefresh: Refresh }) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const resolve = async (approvalId: string, taskId: string, approved: boolean) => {
    setBusyId(approvalId);
    try {
      await apiClient.resolveApproval(taskId, approvalId, approved);
      await onRefresh();
      onToast(approved ? 'Action approved. The task may continue.' : 'Action rejected. The runtime recorded your decision.', approved ? 'success' : 'info');
    } catch (error) { onToast(errorMessage(error, 'Approval could not be resolved.'), 'error'); }
    finally { setBusyId(null); }
  };
  return <PanelState health={snapshot.panelHealth.tasks?.state === 'error' ? snapshot.panelHealth.tasks : snapshot.approvals.length ? { state: 'ready' } : { state: 'empty' }} empty="Protected actions will wait here until you explicitly approve or reject them." onRetry={onRefresh}><section className="approval-grid">{snapshot.approvals.map((approval) => <article className="panel approval-card" key={approval.id}><div className="approval-top"><div className={`risk-glyph risk-${approval.risk}`}><ShieldCheck size={19} /></div><div><span className="eyebrow">{approval.risk.toUpperCase()} RISK · {approval.expiresIn}</span><h2>{approval.action}</h2></div></div><div className="approval-scope"><span>Target</span><strong>{approval.target}</strong><small>{approval.scope}</small></div><p>{approval.reason}</p><div className="approval-actions"><button className="button danger-ghost" disabled={busyId === approval.id} onClick={() => void resolve(approval.id, approval.taskId, false)}><X size={16} />Reject</button><button className="button primary" disabled={busyId === approval.id} onClick={() => void resolve(approval.id, approval.taskId, true)}>{busyId === approval.id ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />}Approve once</button></div></article>)}</section></PanelState>;
}

function WorkspaceView({ snapshot, onToast, onRefresh }: { snapshot: AppSnapshot; onToast: Toast; onRefresh: Refresh }) {
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ filename: string; mime_type: string; size: number; is_text: boolean; content?: string; truncated?: boolean } | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [mutating, setMutating] = useState(false);
  const uploadInput = useRef<HTMLInputElement>(null);
  const requestId = useRef(0);
  const projects = snapshot.workspace.filter((entry) => entry.kind === 'folder');
  const entries = snapshot.workspace.filter((entry) => `${entry.name} ${entry.path} ${entry.detail ?? ''}`.toLowerCase().includes(query.toLowerCase()));
  const selected = snapshot.workspace.find((entry) => entry.id === selectedId);
  const selectedProjectId = selected?.projectId ?? (selected?.kind === 'folder' ? selected.id : undefined);
  const selectEntry = async (entry: WorkspaceEntry) => {
    setSelectedId(entry.id); setPreview(null);
    const currentRequest = ++requestId.current;
    if (entry.kind === 'folder' || !entry.projectId || !entry.fileId) return;
    setPreviewing(true);
    try {
      const result = await apiClient.previewProjectFile(entry.projectId, entry.fileId);
      if (currentRequest === requestId.current) setPreview(result);
    } catch (error) { if (currentRequest === requestId.current) onToast(errorMessage(error, 'File preview failed.'), 'error'); }
    finally { if (currentRequest === requestId.current) setPreviewing(false); }
  };
  const createProject = async (event: FormEvent) => {
    event.preventDefault(); if (!projectName.trim()) return; setMutating(true);
    try { await apiClient.createProject(projectName.trim(), projectDescription.trim()); await onRefresh(); setProjectName(''); setProjectDescription(''); setCreating(false); onToast('Project created.'); }
    catch (error) { onToast(errorMessage(error, 'Project could not be created.'), 'error'); }
    finally { setMutating(false); }
  };
  const upload = async (file: File) => {
    if (!selectedProjectId) return; setMutating(true);
    try { await apiClient.uploadProjectFile(selectedProjectId, file); await onRefresh(); onToast(`${file.name} uploaded to the project.`); }
    catch (error) { onToast(errorMessage(error, 'File upload failed.'), 'error'); }
    finally { setMutating(false); }
  };
  const removeProject = async () => {
    if (!selectedProjectId || selected?.kind !== 'folder' || !globalThis.confirm(`Delete project “${selected.name}”?`)) return; setMutating(true);
    try { await apiClient.deleteProject(selectedProjectId); setSelectedId(null); setPreview(null); await onRefresh(); onToast('Project deleted.', 'info'); }
    catch (error) { onToast(errorMessage(error, 'Project could not be deleted.'), 'error'); }
    finally { setMutating(false); }
  };
  return <div className="workspace-layout"><section className="panel explorer"><div className="surface-toolbar"><div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter projects and files" aria-label="Filter workspace" /></div><button className="button secondary" onClick={() => setCreating((value) => !value)}><FolderPlus size={16} />New project</button></div>{creating && <form className="inline-form" onSubmit={createProject}><input autoFocus value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="Project name" aria-label="Project name" /><input value={projectDescription} onChange={(event) => setProjectDescription(event.target.value)} placeholder="Short description" aria-label="Project description" /><button className="button primary" disabled={mutating || !projectName.trim()}>{mutating ? <LoaderCircle className="spin" size={15} /> : <Plus size={15} />}Create</button></form>}<div className="explorer-meta"><span><FolderTree size={15} />{projects.length} projects · {snapshot.workspace.length - projects.length} files</span><span>25 MB upload limit</span></div><PanelState health={snapshot.panelHealth.projects} empty="Create a project to organize files, conversations, and artifacts." onRetry={onRefresh}><div className="file-tree">{entries.map((entry) => <button key={entry.id} className={`${entry.kind} ${selectedId === entry.id ? 'selected' : ''}`} onClick={() => void selectEntry(entry)}><span className="file-glyph">{entry.kind === 'folder' ? <FolderOpen size={17} /> : <FileCode2 size={17} />}</span><span><strong>{entry.name}</strong><small>{entry.detail || entry.path}</small></span><ChevronRight size={15} /></button>)}</div></PanelState></section><section className="panel preview-panel"><div className="panel-heading"><div><span className="eyebrow">WORKSPACE PREVIEW</span><h2>{selected?.name ?? 'Select an item'}</h2></div>{selectedProjectId && <div className="row-actions"><input ref={uploadInput} type="file" hidden onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); event.currentTarget.value = ''; }} /><button className="icon-button" onClick={() => uploadInput.current?.click()} disabled={mutating} aria-label="Upload file to selected project"><Upload size={17} /></button>{selected?.kind === 'folder' && <button className="icon-button danger" onClick={() => void removeProject()} disabled={mutating} aria-label="Delete selected project"><Trash2 size={17} /></button>}</div>}</div>{previewing ? <div className="preview-empty"><LoaderCircle className="spin" size={22} /><span>Loading protected preview…</span></div> : preview ? <><div className="preview-meta"><span>{preview.mime_type}</span><span>{preview.size} bytes{preview.truncated ? ' · truncated' : ''}</span></div>{preview.is_text ? <pre className="code-block">{preview.content}</pre> : <div className="preview-empty"><FileText size={24} /><strong>Binary file</strong><span>A protected text preview is not available.</span></div>}</> : <div className="preview-empty">{selected?.kind === 'folder' ? <><FolderOpen size={28} /><strong>{selected.name}</strong><span>Upload a file or select an existing file to preview it.</span></> : <><FileCode2 size={28} /><strong>No file selected</strong><span>Choose a persisted file from the project tree.</span></>}</div>}</section></div>;
}

function ArtifactsView({ snapshot, onToast, onRefresh }: { snapshot: AppSnapshot; onToast: Toast; onRefresh: Refresh }) {
  const [preview, setPreview] = useState<{ filename: string; content?: string; download_url?: string } | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const requestId = useRef(0);
  const openPreview = async (artifact: Artifact) => {
    const current = ++requestId.current; setBusyId(artifact.id);
    try { const result = await apiClient.previewArtifact(artifact.id); if (current === requestId.current) setPreview(result); }
    catch (error) { onToast(errorMessage(error, 'Artifact preview failed.'), 'error'); }
    finally { if (current === requestId.current) setBusyId(null); }
  };
  const verify = async (artifact: Artifact) => {
    setBusyId(artifact.id);
    try { await apiClient.verifyArtifact(artifact.id); await onRefresh(); onToast(`${artifact.name} marked verified.`); }
    catch (error) { onToast(errorMessage(error, 'Artifact verification failed.'), 'error'); }
    finally { setBusyId(null); }
  };
  return <><PanelState health={snapshot.panelHealth.artifacts} empty="Verified task output will appear here with provenance and download controls." onRetry={onRefresh}><section className="artifact-grid">{snapshot.artifacts.map((artifact) => <article className="panel artifact-card" key={artifact.id}><div className="artifact-glyph"><FileText size={21} /></div><div className="artifact-main"><div><span className={`artifact-state ${artifact.status}`}>{artifact.status.replace('_', ' ')}</span><h2>{artifact.name}</h2><p>{artifact.type} · {artifact.size}</p></div><div className="artifact-meta"><span>Task {artifact.taskId}</span><span>{shortDate(artifact.updatedAt)}</span></div><div className="artifact-actions"><button className="button tertiary" onClick={() => void openPreview(artifact)} disabled={busyId === artifact.id}>{busyId === artifact.id ? <LoaderCircle className="spin" size={15} /> : <FileCode2 size={15} />}Preview</button>{artifact.status !== 'verified' && <button className="button secondary" onClick={() => void verify(artifact)} disabled={busyId === artifact.id}><FileCheck2 size={15} />Verify</button>}<a className="button icon-link" href={artifact.downloadUrl} target="_blank" rel="noreferrer" aria-label={`Download ${artifact.name}`}><Download size={16} /></a></div></div></article>)}</section></PanelState>{preview && <section className="panel artifact-preview"><div className="panel-heading"><div><span className="eyebrow">SECURE PREVIEW</span><h2>{preview.filename}</h2></div><button className="icon-button" onClick={() => setPreview(null)} aria-label="Close preview"><X size={17} /></button></div>{preview.content !== undefined ? <pre className="code-block">{preview.content}</pre> : preview.download_url ? <a className="button secondary" href={preview.download_url} target="_blank" rel="noreferrer"><Download size={16} />Download binary artifact</a> : <div className="preview-empty">No preview content was returned.</div>}</section>}</>;
}

function MemoryView({ snapshot, onToast, onRefresh }: { snapshot: AppSnapshot; onToast: Toast; onRefresh: Refresh }) {
  const [query, setQuery] = useState('');
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [scope, setScope] = useState('user');
  const [busy, setBusy] = useState(false);
  const filtered = snapshot.memories.filter((memory) => `${memory.name} ${memory.scope} ${memory.content}`.toLowerCase().includes(query.toLowerCase()));
  const save = async (event: FormEvent) => {
    event.preventDefault(); if (!name.trim() || !content.trim()) return; setBusy(true);
    try { await apiClient.saveMemory(name.trim(), content.trim(), scope); await onRefresh(); setName(''); setContent(''); onToast('Memory saved to persistent storage.'); }
    catch (error) { onToast(errorMessage(error, 'Memory could not be saved.'), 'error'); }
    finally { setBusy(false); }
  };
  const remove = async (memory: MemoryEntry) => {
    if (!globalThis.confirm(`Delete memory “${memory.name}”?`)) return; setBusy(true);
    try { await apiClient.deleteMemory(memory.name, memory.scope); await onRefresh(); onToast('Memory deleted.', 'info'); }
    catch (error) { onToast(errorMessage(error, 'Memory could not be deleted.'), 'error'); }
    finally { setBusy(false); }
  };
  return <div className="memory-layout"><form className="panel memory-composer" onSubmit={save}><div className="panel-heading"><div><span className="eyebrow">NEW MEMORY</span><h2>Save durable context</h2></div><Database size={19} /></div><label>Name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Example: deployment preference" /></label><label>Content<textarea value={content} onChange={(event) => setContent(event.target.value)} placeholder="What should BRJARVIS remember?" /></label><div className="form-footer"><select value={scope} onChange={(event) => setScope(event.target.value)} aria-label="Memory scope"><option value="user">User scope</option><option value="project">Project scope</option></select><button className="button primary" disabled={busy || !name.trim() || !content.trim()}>{busy ? <LoaderCircle className="spin" size={16} /> : <Plus size={16} />}Save memory</button></div></form><section className="panel memory-library"><div className="surface-toolbar"><div><span className="eyebrow">KNOWLEDGE LIBRARY</span><h2>{snapshot.memoryCount} memories</h2></div><div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search memory" aria-label="Search memory" /></div></div><PanelState health={snapshot.panelHealth.memories} empty="Save preferences, reusable facts, and project context here." onRetry={onRefresh}><div className="memory-list">{filtered.map((memory) => <article key={memory.id}><div className="memory-icon"><Database size={16} /></div><div><span>{memory.scope}</span><h3>{memory.name}</h3><p>{memory.content}</p><small>{shortDate(memory.updatedAt)}</small></div><button className="icon-button danger" onClick={() => void remove(memory)} disabled={busy} aria-label={`Delete ${memory.name}`}><Trash2 size={16} /></button></article>)}</div></PanelState></section></div>;
}

function CareerView({ snapshot, onToast }: { snapshot: AppSnapshot; onToast: Toast }) {
  const [role, setRole] = useState('');
  const [location, setLocation] = useState('');
  const [jobs, setJobs] = useState<CareerJob[]>([]);
  const [searched, setSearched] = useState(false);
  const [busy, setBusy] = useState<'jobs' | 'resume' | null>(null);
  const [resume, setResume] = useState<Record<string, unknown> | null>(null);
  const searchJobs = async (event: FormEvent) => {
    event.preventDefault(); if (!role.trim()) return; setBusy('jobs');
    try { setJobs(await apiClient.searchCareerJobs(role.trim(), location.trim())); setSearched(true); }
    catch (error) { onToast(errorMessage(error, 'Job search failed.'), 'error'); }
    finally { setBusy(null); }
  };
  const createResume = async () => {
    setBusy('resume');
    try { const result = await apiClient.createCareerResume(role.trim() || undefined); setResume(result); onToast('Career OS completed the resume request.'); }
    catch (error) { onToast(errorMessage(error, 'Resume generation failed.'), 'error'); }
    finally { setBusy(null); }
  };
  const profile = snapshot.career;
  return <div className="career-layout"><section className="panel career-profile"><div className="career-cover"><div className="career-avatar"><UserRound size={25} /></div><div><span className="eyebrow">CAREER IDENTITY</span><h2>{profile?.name || 'Profile not configured'}</h2><p>{profile?.headline || 'Complete your Career OS profile through onboarding.'}{profile?.location ? ` · ${profile.location}` : ''}</p></div></div>{profile ? <><div className="completion"><div><span>Profile completeness</span><strong>{profile.completeness ?? 0}%</strong></div><Progress value={profile.completeness ?? 0} /></div><div className="skill-cloud">{profile.skills.length ? profile.skills.slice(0, 20).map((skill) => <span key={skill}>{skill}</span>) : <p className="muted">No skills have been returned.</p>}</div></> : <PanelState health={snapshot.panelHealth.career} empty="Create a profile to unlock resume and job matching workflows."><></></PanelState>}<button className="button primary full" onClick={() => void createResume()} disabled={busy === 'resume'}>{busy === 'resume' ? <LoaderCircle className="spin" size={16} /> : <FileText size={16} />}{resume ? `Resume ${String(resume.version_id ?? 'created')}` : 'Generate ATS resume'}</button></section><section className="panel job-search"><div className="panel-heading"><div><span className="eyebrow">OPPORTUNITY SEARCH</span><h2>Find aligned roles</h2></div><Globe2 size={19} /></div><form className="job-form" onSubmit={searchJobs}><label>Target role<input value={role} onChange={(event) => setRole(event.target.value)} placeholder="Senior software engineer" /></label><label>Location<input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Remote or city" /></label><button className="button primary" disabled={busy === 'jobs' || !role.trim()}>{busy === 'jobs' ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}Search jobs</button></form><div className="job-list">{jobs.map((job) => <article key={job.id}><div className="job-glyph"><BriefcaseBusiness size={17} /></div><div><h3>{job.title}</h3><p>{job.company} · {job.location}</p>{job.summary && <small>{job.summary}</small>}</div>{job.url && <a className="icon-button" href={job.url} target="_blank" rel="noreferrer" aria-label={`Open ${job.title}`}><ExternalLink size={16} /></a>}</article>)}{searched && !jobs.length && <div className="state-card compact"><Search size={19} /><div><strong>No matching jobs returned</strong><p>Try a broader role or location.</p></div></div>}</div></section></div>;
}

function BusinessView({ snapshot, onToast, onRefresh, onView }: { snapshot: AppSnapshot; onToast: Toast; onRefresh: Refresh; onView: (view: ViewId) => void }) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const projects = snapshot.workspace.filter((entry) => entry.kind === 'folder');
  const activeTasks = snapshot.tasks.filter((task) => ['queued', 'planning', 'running', 'waiting', 'retrying'].includes(task.status));
  const add = async (event: FormEvent) => {
    event.preventDefault(); if (!name.trim()) return; setBusyId('new');
    try { await apiClient.createContact({ name: name.trim(), email: email.trim(), phone_number: phone.trim() }); await onRefresh(); setName(''); setEmail(''); setPhone(''); setAdding(false); onToast('Contact created.'); }
    catch (error) { onToast(errorMessage(error, 'Contact could not be created.'), 'error'); }
    finally { setBusyId(null); }
  };
  const toggleImportant = async (contact: ContactSummary) => {
    setBusyId(contact.id);
    try { await apiClient.updateContact(contact.id, { is_important: !contact.important }); await onRefresh(); onToast(contact.important ? 'Contact unstarred.' : 'Contact marked important.', 'info'); }
    catch (error) { onToast(errorMessage(error, 'Contact could not be updated.'), 'error'); }
    finally { setBusyId(null); }
  };
  const remove = async (contact: ContactSummary) => {
    if (!globalThis.confirm(`Delete contact “${contact.name}”?`)) return; setBusyId(contact.id);
    try { await apiClient.deleteContact(contact.id); await onRefresh(); onToast('Contact deleted.', 'info'); }
    catch (error) { onToast(errorMessage(error, 'Contact could not be deleted.'), 'error'); }
    finally { setBusyId(null); }
  };
  return <><section className="business-metrics"><Metric label="Relationships" value={String(snapshot.contacts.length)} detail="Stored contacts" tone="accent" icon={HeartHandshake} /><Metric label="Projects" value={String(projects.length)} detail="Delivery spaces" icon={FolderTree} /><Metric label="Active work" value={String(activeTasks.length)} detail="Durable tasks" tone="success" icon={Activity} /><Metric label="Artifacts" value={String(snapshot.artifacts.length)} detail="Tracked output" icon={Layers3} /></section><div className="business-layout"><section className="panel contacts-panel"><div className="panel-heading"><div><span className="eyebrow">RELATIONSHIPS</span><h2>Contacts</h2></div><button className="button secondary" onClick={() => setAdding((value) => !value)}><UserPlus size={16} />Add contact</button></div>{adding && <form className="inline-form contact-form" onSubmit={add}><input autoFocus value={name} onChange={(event) => setName(event.target.value)} placeholder="Full name" aria-label="Contact name" /><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" aria-label="Contact email" /><input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Phone" aria-label="Contact phone" /><button className="button primary" disabled={busyId === 'new' || !name.trim()}><Plus size={15} />Create</button></form>}<PanelState health={snapshot.panelHealth.contacts} empty="Add a relationship to build your local contact graph." onRetry={onRefresh}><div className="contact-list">{snapshot.contacts.map((contact) => <article key={contact.id}><div className="contact-avatar">{contact.name.charAt(0).toUpperCase()}</div><div><div><h3>{contact.name}</h3>{contact.important && <Star size={13} fill="currentColor" />}</div><p>{contact.organization || contact.title || 'Independent contact'}</p><small>{contact.email || contact.phone || 'No contact channel'}</small></div><div className="row-actions"><button className="icon-button" onClick={() => void toggleImportant(contact)} disabled={busyId === contact.id} aria-label={contact.important ? `Unstar ${contact.name}` : `Star ${contact.name}`}><Star size={16} fill={contact.important ? 'currentColor' : 'none'} /></button><button className="icon-button danger" onClick={() => void remove(contact)} disabled={busyId === contact.id} aria-label={`Delete ${contact.name}`}><Trash2 size={16} /></button></div></article>)}</div></PanelState></section><section className="panel delivery-panel"><div className="panel-heading"><div><span className="eyebrow">DELIVERY</span><h2>Project pulse</h2></div><button className="text-button" onClick={() => onView('workspace')}>Open workspace <ArrowRight size={15} /></button></div>{projects.length ? <div className="project-pulse">{projects.slice(0, 8).map((project) => { const fileCount = snapshot.workspace.filter((entry) => entry.kind === 'file' && entry.projectId === project.projectId).length; return <button key={project.id} onClick={() => onView('workspace')}><div className="project-glyph"><FolderOpen size={17} /></div><div><strong>{project.name}</strong><span>{project.detail}</span></div><small>{fileCount} files</small><ChevronRight size={15} /></button>; })}</div> : <div className="state-card compact"><FolderPlus size={20} /><div><strong>No delivery projects</strong><p>Create a workspace project to organize work.</p></div></div>}</section></div></>;
}

function IntegrationsView({ snapshot, onToast, onRefresh }: { snapshot: AppSnapshot; onToast: Toast; onRefresh: Refresh }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const selected = snapshot.connectors.find((item) => item.id === selectedId);
  const test = async (id: string) => {
    setBusy(id);
    try { const result = await apiClient.testConnector(id); onToast(`Connector test: ${String(result.status ?? 'complete')}.`, 'info'); }
    catch (error) { onToast(errorMessage(error, 'Connector test failed.'), 'error'); }
    finally { setBusy(null); }
  };
  const configure = async (event: FormEvent) => {
    event.preventDefault(); if (!selected || !apiKey.trim()) return; setBusy(selected.id);
    try { await apiClient.configureConnector(selected.id, apiKey.trim()); setApiKey(''); await onRefresh(); onToast(`${selected.name} credential saved to the secure vault.`); }
    catch (error) { onToast(errorMessage(error, 'Connector configuration failed.'), 'error'); }
    finally { setBusy(null); }
  };
  return <><section className="capability-strip">{snapshot.capabilities.map((capability) => <article className="panel" key={capability.id}><div className={`capability-glyph ${capability.state}`}><Network size={17} /></div><div><span>{capability.label}</span><strong>{capability.detail}</strong></div><small>{capability.latency}</small></article>)}</section><div className="integration-layout"><section className="panel connector-list"><div className="panel-heading"><div><span className="eyebrow">CONNECTOR REGISTRY</span><h2>{snapshot.connectors.length} integrations</h2></div><Settings2 size={18} /></div><PanelState health={snapshot.panelHealth.connectors} empty="No integrations were discovered by the runtime." onRetry={onRefresh}><div>{snapshot.connectors.map((connector) => <button key={connector.id} className={selectedId === connector.id ? 'selected' : ''} onClick={() => setSelectedId(connector.id)}><div className="connector-glyph"><Network size={17} /></div><div><div><strong>{connector.name}</strong><span className={`connector-status ${connector.configured ? 'connected' : ''}`}>{connector.configured ? 'Configured' : 'Setup needed'}</span></div><p>{connector.description || 'No connector description returned.'}</p><small>{connector.category} · {connector.tools.length} tools</small></div><ChevronRight size={16} /></button>)}</div></PanelState></section><section className="panel connector-detail">{selected ? <><div className="connector-hero"><div className="connector-glyph large"><Network size={22} /></div><div><span className="eyebrow">{selected.category}</span><h2>{selected.name}</h2><p>{selected.description}</p></div></div><div className="connector-facts"><div><span>Status</span><strong>{selected.status}</strong></div><div><span>Tools</span><strong>{selected.tools.length}</strong></div><div><span>Authentication</span><strong>{selected.requiresAuth ? 'Required' : 'Not required'}</strong></div></div>{selected.tools.length > 0 && <div className="tool-cloud">{selected.tools.slice(0, 12).map((tool) => <span key={tool}>{tool}</span>)}</div>}<div className="credential-note"><KeyRound size={18} /><div><strong>Vault-backed credentials</strong><p>Secrets are sent directly to the local server credential vault and are never displayed again.</p></div></div>{selected.requiresAuth && <form className="credential-form" onSubmit={configure}><label htmlFor="connector-key">{selected.authHint || `${selected.name} API key`}</label><div><input id="connector-key" type="password" autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="Paste credential" /><button className="button primary" disabled={busy === selected.id || !apiKey.trim()}><LockKeyhole size={16} />Save securely</button></div></form>}<button className="button secondary full" onClick={() => void test(selected.id)} disabled={busy === selected.id}>{busy === selected.id ? <LoaderCircle className="spin" size={16} /> : <Activity size={16} />}Test connection</button></> : <div className="preview-empty"><Network size={28} /><strong>Select an integration</strong><span>Review capabilities, configure credentials, or run a connection test.</span></div>}</section></div></>;
}

function OperationsView({ snapshot, onToast, onRefresh }: { snapshot: AppSnapshot; onToast: Toast; onRefresh: Refresh }) {
  const [busy, setBusy] = useState(false);
  const markAll = async () => {
    setBusy(true);
    try { await apiClient.markAllNotificationsRead(); dispatch({ type: 'notifications-read' }); onToast('All events marked read.', 'info'); }
    catch (error) { onToast(errorMessage(error, 'Notifications could not be updated.'), 'error'); }
    finally { setBusy(false); }
  };
  const markOne = async (event: TimelineEvent) => {
    if (event.read) return;
    try { await apiClient.markNotificationRead(event.id); await onRefresh(); }
    catch (error) { onToast(errorMessage(error, 'Notification could not be updated.'), 'error'); }
  };
  return <><section className="ops-overview"><Metric label="Backend" value={snapshot.backend} detail="REST control plane" tone={snapshot.backend === 'online' ? 'success' : 'warning'} icon={TerminalSquare} /><Metric label="Realtime" value={snapshot.connection} detail="WebSocket channel" tone={snapshot.connection === 'connected' ? 'success' : 'warning'} icon={Wifi} /><Metric label="Unread" value={String(snapshot.unreadNotifications)} detail="Runtime events" tone="accent" icon={Bell} /><Metric label="Capabilities" value={`${snapshot.capabilities.filter((item) => item.state === 'healthy').length}/${snapshot.capabilities.length}`} detail="Healthy checks" icon={ShieldCheck} /></section><div className="operations-layout"><section className="panel operations-events"><div className="panel-heading"><div><span className="eyebrow">EVENT INBOX</span><h2>Runtime notifications</h2></div><button className="button tertiary" disabled={busy || snapshot.unreadNotifications === 0} onClick={() => void markAll()}><Check size={15} />Mark all read</button></div><PanelState health={snapshot.panelHealth.notifications} empty="Runtime notifications and policy events will appear here." onRetry={onRefresh}><div className="notification-list">{snapshot.timeline.map((event) => <button key={event.id} className={event.read ? 'read' : ''} onClick={() => void markOne(event)}><span className={`notification-tone ${event.tone}`} /><div><div><strong>{event.label}</strong><time>{shortDate(event.time)}</time></div><p>{event.detail}</p><small>{event.category}</small></div>{!event.read && <span className="unread-dot" />}</button>)}</div></PanelState></section><section className="panel readiness-panel"><div className="panel-heading"><div><span className="eyebrow">READINESS</span><h2>Control gates</h2></div><ShieldCheck size={19} /></div><div className="readiness-list">{snapshot.capabilities.map((capability) => <div key={capability.id}><span className={`readiness-dot ${capability.state}`} /><div><strong>{capability.label}</strong><p>{capability.detail}</p></div><small>{capability.state.replace('_', ' ')}</small></div>)}</div><div className="security-callout"><LockKeyhole size={18} /><div><strong>Fail-closed security</strong><p>Protected routes require a valid local session. Destructive actions remain approval-gated.</p></div></div></section></div></>;
}

function StatusBadge({ status }: { status: TaskStatus }) {
  const labels: Record<TaskStatus, string> = { queued: 'Queued', planning: 'Planning', running: 'Running', waiting: 'Approval', retrying: 'Recovering', completed: 'Completed', failed: 'Failed', cancelled: 'Cancelled' };
  return <span className={`status-badge ${status}`}><i />{labels[status]}</span>;
}

function Progress({ value }: { value: number }) {
  const safe = Math.max(0, Math.min(100, value));
  return <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(safe)}><span style={{ width: `${safe}%` }} /></div>;
}

function CommandPalette({ onClose, onNavigate }: { onClose: () => void; onNavigate: (view: ViewId) => void }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const localItems = useMemo(() => navigation.filter((item) => `${item.label} ${item.description}`.toLowerCase().includes(query.toLowerCase())), [query]);
  const totalItems = localItems.length + results.length;
  useEffect(() => {
    inputRef.current?.focus();
    const controller = new AbortController();
    if (query.trim().length < 2) { setResults([]); setLoading(false); return () => controller.abort(); }
    const timeout = globalThis.setTimeout(async () => {
      setLoading(true);
      try { setResults(await apiClient.search(query.trim(), controller.signal)); }
      catch { if (!controller.signal.aborted) setResults([]); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    }, 250);
    return () => { controller.abort(); globalThis.clearTimeout(timeout); };
  }, [query]);
  useEffect(() => setSelected(0), [query]);
  const navigateResult = (result: SearchResult) => {
    const type = result.entityType.toLowerCase();
    if (type.includes('project') || type.includes('file')) onNavigate('workspace');
    else if (type.includes('artifact')) onNavigate('artifacts');
    else if (type.includes('contact')) onNavigate('business');
    else if (type.includes('memory') || type.includes('note')) onNavigate('memory');
    else onNavigate('tasks');
  };
  const activate = () => {
    if (selected < localItems.length) onNavigate(localItems[selected].id);
    else if (results[selected - localItems.length]) navigateResult(results[selected - localItems.length]);
  };
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setSelected((value) => totalItems ? (value + 1) % totalItems : 0);
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setSelected((value) => totalItems ? (value - 1 + totalItems) % totalItems : 0);
    }
    if (event.key === 'Enter') {
      event.preventDefault();
      activate();
    }
    if (event.key === 'Tab') {
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>('input,button');
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  };
  return <div className="dialog-backdrop" onMouseDown={onClose}>
    <div ref={dialogRef} className="command-palette" role="dialog" aria-modal="true" aria-label="Search control plane" onMouseDown={(event) => event.stopPropagation()} onKeyDown={handleKeyDown}>
      <div className="palette-search"><Search size={19} /><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search surfaces, projects, contacts, and artifacts…" aria-label="Search" />{loading && <LoaderCircle className="spin" size={17} />}<button className="icon-button" onClick={onClose} aria-label="Close search"><X size={17} /></button></div>
      <div className="palette-results"><span className="palette-label">SURFACES</span>{localItems.map((item, index) => { const Icon = navIcons[item.id]; return <button key={item.id} className={selected === index ? 'selected' : ''} onMouseEnter={() => setSelected(index)} onClick={() => onNavigate(item.id)}><span className="palette-glyph"><Icon size={17} /></span><span><strong>{item.label}</strong><small>{item.description}</small></span><ArrowRight size={15} /></button>; })}{results.length > 0 && <><span className="palette-label">LIVE RESULTS</span>{results.map((result, index) => { const itemIndex = localItems.length + index; return <button key={`${result.entityType}-${result.entityId}`} className={selected === itemIndex ? 'selected' : ''} onMouseEnter={() => setSelected(itemIndex)} onClick={() => navigateResult(result)}><span className="palette-glyph"><Search size={17} /></span><span><strong>{result.title}</strong><small>{result.entityType} · {result.snippet}</small></span><ArrowRight size={15} /></button>; })}</>}</div>
      <div className="palette-footer"><span><kbd>↑↓</kbd> Navigate</span><span><kbd>Enter</kbd> Open</span><span><kbd>Esc</kbd> Close</span></div>
    </div>
  </div>;
}

function BootScreen() {
  return <div className="auth-screen"><div className="boot-orbit"><span /><span /><span /><div className="brand-glyph"><Sparkles size={23} /></div></div><span className="eyebrow">BRJARVIS / SECURE STARTUP</span><h1>Preparing the control plane</h1><p>Restoring the browser session and reading authoritative runtime state.</p></div>;
}

function LoginScreen({ busy, error, onSubmit }: { busy: boolean; error: string | null; onSubmit: (apiKey: string) => void }) {
  const [apiKey, setApiKey] = useState('');
  return <div className="login-layout"><section className="login-story"><div className="brand login-brand"><div className="brand-glyph"><Sparkles size={19} /></div><div className="brand-copy"><strong>BRJARVIS</strong><span>CONTROL PLANE</span></div></div><div><span className="eyebrow">PRIVATE · LOCAL-FIRST · POLICY-GOVERNED</span><h1>Your intelligent operations workspace.</h1><p>Plan complex work, authorize risk, inspect evidence, and operate your local AI runtime from one secure surface.</p></div><div className="login-features"><span><ShieldCheck size={17} />Fail-closed access</span><span><Database size={17} />Local persistence</span><span><Activity size={17} />Live execution state</span></div></section><section className="login-panel"><form className="login-card" onSubmit={(event) => { event.preventDefault(); if (apiKey.trim()) onSubmit(apiKey); }}><div className="login-icon"><KeyRound size={22} /></div><span className="eyebrow">SECURE SESSION</span><h2>Sign in to continue</h2><p>Enter the API key configured on this BRJARVIS server. It creates an HttpOnly browser session and is not saved in browser storage.</p><label htmlFor="server-key">Server API key</label><div className="password-field"><LockKeyhole size={17} /><input id="server-key" type="password" autoComplete="off" autoFocus value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="Paste your local server key" /></div><button className="button primary full" disabled={busy || !apiKey.trim()}>{busy ? <LoaderCircle className="spin" size={17} /> : <ArrowRight size={17} />}{busy ? 'Creating session' : 'Open control plane'}</button>{error && <div className="form-error" role="alert"><CircleAlert size={16} /><span>{error}</span></div>}<div className="login-note"><ShieldCheck size={15} /><span>Session cookie: HttpOnly · SameSite strict · server managed</span></div></form></section></div>;
}
