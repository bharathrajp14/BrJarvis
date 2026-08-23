export interface AuthSnapshot {
  authRequired: boolean;
  authenticated: boolean;
  label: string;
  scope: string;
}

function normalizeAuth(body: Record<string, unknown>): AuthSnapshot {
  const data = (body.data ?? body) as Record<string, unknown>;
  const identity = (data.user ?? data.session_user ?? data.identity ?? {}) as Record<string, unknown>;
  return {
    authRequired: Boolean(data.auth_required ?? data.authRequired),
    authenticated: Boolean(data.authenticated ?? data.logged_in ?? data.status === 'authenticated'),
    label: String(identity.name ?? identity.email ?? data.username ?? data.user_id ?? 'Operator'),
    scope: String(data.scope ?? data.role ?? 'Local session'),
  };
}

export async function loadAuthSnapshot(): Promise<AuthSnapshot> {
  try {
    const response = await fetch('/api/v1/auth/status', { credentials: 'include', headers: { Accept: 'application/json' } });
    if (!response.ok) return { authRequired: true, authenticated: false, label: 'Local session', scope: 'Unauthenticated' };
    return normalizeAuth(await response.json() as Record<string, unknown>);
  } catch {
    return { authRequired: false, authenticated: false, label: 'Local session', scope: 'Offline' };
  }
}

export async function loginWithApiKey(apiKey: string): Promise<AuthSnapshot> {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    credentials: 'include',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey.trim() }),
  });
  const body = await response.json().catch(() => ({})) as { detail?: string; error?: { message?: string } };
  if (!response.ok) throw new Error(body.detail ?? body.error?.message ?? 'Authentication failed. Check the server API key.');
  return loadAuthSnapshot();
}
