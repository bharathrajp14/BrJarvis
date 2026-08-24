import { emptySnapshot } from '../platform/empty-state';
import type { AppSnapshot, Task, ViewId } from '../contracts/domain';

export type AppAction =
  | { type: 'hydrate'; snapshot: AppSnapshot }
  | { type: 'view'; view: ViewId }
  | { type: 'active-task'; taskId: string }
  | { type: 'connection'; status: AppSnapshot['connection'] }
  | { type: 'task-upsert'; task: Task }
  | { type: 'task-progress'; taskId: string; progress: number; detail?: string }
  | { type: 'approval-resolved'; approvalId: string; taskId: string; approved: boolean };

let snapshot: AppSnapshot = structuredClone(emptySnapshot);
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((listener) => listener());
}

export function getSnapshot() {
  return snapshot;
}

export function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function dispatch(action: AppAction) {
  switch (action.type) {
    case 'hydrate':
      snapshot = structuredClone(action.snapshot);
      break;
    case 'view':
      snapshot = { ...snapshot, activeView: action.view };
      break;
    case 'active-task':
      snapshot = { ...snapshot, activeTaskId: action.taskId };
      break;
    case 'connection':
      snapshot = { ...snapshot, connection: action.status };
      break;
    case 'task-upsert': {
      const existing = snapshot.tasks.some((task) => task.id === action.task.id);
      snapshot = { ...snapshot, tasks: existing ? snapshot.tasks.map((task) => task.id === action.task.id ? action.task : task) : [action.task, ...snapshot.tasks], activeTaskId: action.task.id };
      break;
    }
    case 'task-progress':
      snapshot = { ...snapshot, tasks: snapshot.tasks.map((task) => task.id === action.taskId ? { ...task, progress: action.progress, updatedAt: 'Just now', summary: action.detail ?? task.summary } : task) };
      break;
    case 'approval-resolved':
      snapshot = {
        ...snapshot,
        approvals: snapshot.approvals.filter((approval) => approval.id !== action.approvalId),
        tasks: snapshot.tasks.map((task) => task.id === action.taskId && action.approved ? { ...task, status: 'running', requiresApproval: false, updatedAt: 'Just now' } : task),
      };
      break;
  }
  notify();
}
