export interface AuthSnapshot {
  authRequired: boolean;
  authenticated: boolean;
  label: string;
  scope: string;
}

const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '').replace(/\/$/, '');

function asBoolean(value: unknown): boolean {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (['true', '1', 'yes', 'on', 'authenticated'].includes(normalized)) return true;
    if (['false', '0', 'no', 'off', ''].includes(normalized)) return false;
  }
  return Boolean(value);
}

function normalizeAuth(body: Record<string, unknown>): AuthSnapshot {
  const data = (body.data ?? body) as Record<string, unknown>;
  const identity = (data.user ?? data.session_user ?? data.identity ?? {}) as Record<string, unknown>;
  return {
    authRequired: asBoolean(data.auth_required ?? data.authRequired),
    authenticated: asBoolean(data.authenticated ?? data.logged_in ?? data.status === 'authenticated'),
    label: String(identity.name ?? identity.email ?? data.username ?? data.user_id ?? 'Operator'),
    scope: String(data.scope ?? data.role ?? 'Local session'),
  };
}

export async function loadAuthSnapshot(): Promise<AuthSnapshot> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/status`, { credentials: 'include', headers: { Accept: 'application/json' } });
    if (!response.ok) return { authRequired: true, authenticated: false, label: 'Local session', scope: 'Unauthenticated' };
    return normalizeAuth(await response.json() as Record<string, unknown>);
  } catch {
    return { authRequired: false, authenticated: false, label: 'Local session', scope: 'Offline' };
  }
}

export async function loginWithApiKey(apiKey: string): Promise<AuthSnapshot> {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey.trim() }),
  });
  const body = await response.json().catch(() => ({})) as { detail?: string; error?: { message?: string } };
  if (!response.ok) throw new Error(body.detail ?? body.error?.message ?? 'Authentication failed. Check the server API key.');
  return loadAuthSnapshot();
}

export async function logoutSession(): Promise<void> {
  await fetch(`${API_BASE}/api/v1/auth/logout`, { method: 'POST', credentials: 'include', headers: { Accept: 'application/json' } });
}
