import type { AppSnapshot } from '../contracts/domain';

/** Truthful state used while the control plane is loading or unavailable. */
export const emptySnapshot: AppSnapshot = {
  activeView: 'command',
  activeTaskId: '',
  connection: 'connecting',
  backend: 'offline',
  capabilities: [],
  tasks: [],
  approvals: [],
  artifacts: [],
  workspace: [],
  memories: [],
  memoryCount: 0,
  career: null,
  contacts: [],
  connectors: [],
  timeline: [],
  unreadNotifications: 0,
  panelHealth: {},
};
