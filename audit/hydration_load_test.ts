import { performance } from 'node:perf_hooks';
import { ApiClient } from './hydration_api_client.ts';

function payloadFor(url: string, projectCount: number): Record<string, unknown> {
  if (url.includes('/api/agent/tasks')) return { tasks: [] };
  if (url.includes('/api/artifacts')) return { artifacts: [] };
  if (url.includes('/health')) return { status: 'online', backend: 'mock' };
  if (url.includes('/api/v1/connectors')) return { connectors: [] };
  if (url.includes('/api/projects')) return {
    projects: Array.from({ length: projectCount }, (_, index) => ({
      project_id: `project-${index}`,
      name: `Project ${index}`,
      description: 'Load-test project',
      files: Array.from({ length: Math.min(index % 5, 3) }, (_, fileIndex) => ({
        file_id: `file-${index}-${fileIndex}`,
        filename: `file-${fileIndex}.txt`,
        file_path: `/workspace/project-${index}/file-${fileIndex}.txt`,
        file_size: 100,
        status: 'READY',
      })),
    })),
  };
  if (url.includes('/api/memory')) return { memories: [] };
  if (url.includes('/api/notifications')) return { notifications: [] };
  if (url.includes('/api/career/profile')) return { profile: null };
  if (url.includes('/api/contacts')) return { contacts: [] };
  return {};
}

async function oneSnapshot(projectCount: number, delayMs: number, failPath = '') {
  const client = new ApiClient('');
  let requests = 0;
  let active = 0;
  let peak = 0;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input: RequestInfo | URL) => {
    const url = String(input);
    requests += 1;
    active += 1;
    peak = Math.max(peak, active);
    try {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      if (failPath && url.includes(failPath)) throw new Error('simulated panel outage');
      return new Response(JSON.stringify(payloadFor(url, projectCount)), { status: 200, headers: { 'content-type': 'application/json' } });
    } finally {
      active -= 1;
    }
  };
  const started = performance.now();
  const snapshot = await client.snapshot();
  const elapsedMs = performance.now() - started;
  globalThis.fetch = originalFetch;
  return { projectCount, delayMs, requests, peakConcurrency: peak, elapsedMs, connection: snapshot.connection, panelHealth: snapshot.panelHealth };
}

async function main() {
  const results: unknown[] = [];
  for (const projectCount of [0, 10, 100, 500]) {
    for (const delayMs of [0, 5, 20]) {
      const samples = [];
      for (let i = 0; i < 20; i += 1) samples.push(await oneSnapshot(projectCount, delayMs));
      const sorted = samples.map((item) => item.elapsedMs).sort((a, b) => a - b);
      results.push({ projectCount, delayMs, samples: samples.length, requests: samples[0].requests, peakConcurrency: samples[0].peakConcurrency, p50Ms: sorted[Math.floor(sorted.length * 0.50)], p95Ms: sorted[Math.floor(sorted.length * 0.95)], maxMs: sorted.at(-1) });
    }
  }
  results.push({ failureCase: await oneSnapshot(100, 5, '/api/artifacts') });
  const concurrentStarted = performance.now();
  const concurrent = await Promise.all(Array.from({ length: 20 }, () => oneSnapshot(100, 5)));
  results.push({ concurrentSnapshots: concurrent.length, concurrentElapsedMs: performance.now() - concurrentStarted, requestsPerSnapshot: concurrent[0].requests, peakFetchConcurrencyPerSnapshot: concurrent[0].peakConcurrency });
  console.log(JSON.stringify({ hydration: results }, null, 2));
}

main();
