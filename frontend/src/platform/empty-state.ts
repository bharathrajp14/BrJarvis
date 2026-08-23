import type { AppSnapshot } from '../contracts/domain';

/**
 * Empty, truthful state used while the server is loading or unavailable.
 * It intentionally contains no sample tasks, metrics, artifacts, or events.
 */
export const emptySnapshot: AppSnapshot = {
  activeView: 'command',
  activeTaskId: '',
  connection: 'connecting',
  capabilities: [],
  tasks: [],
  approvals: [],
  artifacts: [],
  workspace: [],
  memoryCount: 0,
  timeline: [],
};
