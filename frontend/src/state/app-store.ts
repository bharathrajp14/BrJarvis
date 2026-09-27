import { emptySnapshot } from '../platform/empty-state';
import type { AppSnapshot, Task, TimelineEvent, ViewId } from '../contracts/domain';

export type AppAction =
  | { type: 'hydrate'; snapshot: AppSnapshot }
  | { type: 'view'; view: ViewId }
  | { type: 'active-task'; taskId: string }
  | { type: 'connection'; status: AppSnapshot['connection'] }
  | { type: 'task-upsert'; task: Task }
  | { type: 'timeline-append'; event: TimelineEvent }
  | { type: 'notifications-read' };

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
    case 'hydrate': {
      const selectedTaskStillExists = action.snapshot.tasks.some((task) => task.id === snapshot.activeTaskId);
      snapshot = {
        ...action.snapshot,
        activeView: snapshot.activeView,
        activeTaskId: selectedTaskStillExists ? snapshot.activeTaskId : (action.snapshot.activeTaskId || action.snapshot.tasks[0]?.id || ''),
        connection: snapshot.connection,
      };
      break;
    }
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
      const exists = snapshot.tasks.some((task) => task.id === action.task.id);
      snapshot = {
        ...snapshot,
        tasks: exists ? snapshot.tasks.map((task) => task.id === action.task.id ? action.task : task) : [action.task, ...snapshot.tasks],
        activeTaskId: action.task.id,
      };
      break;
    }
    case 'timeline-append':
      snapshot = {
        ...snapshot,
        timeline: [action.event, ...snapshot.timeline.filter((event) => event.id !== action.event.id)].slice(0, 50),
        unreadNotifications: snapshot.unreadNotifications + (action.event.read ? 0 : 1),
      };
      break;
    case 'notifications-read':
      snapshot = { ...snapshot, unreadNotifications: 0, timeline: snapshot.timeline.map((event) => ({ ...event, read: true })) };
      break;
  }
  notify();
}
