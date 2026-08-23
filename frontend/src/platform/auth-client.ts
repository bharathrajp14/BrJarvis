export interface AuthSnapshot {
  authenticated: boolean;
  label: string;
  scope: string;
}

export async function loadAuthSnapshot(): Promise<AuthSnapshot> {
  try {
    const response = await fetch('/api/v1/auth/status', { credentials: 'include', headers: { Accept: 'application/json' } });
    if (!response.ok) return { authenticated: false, label: 'Local session', scope: 'Unauthenticated' };
    const body = await response.json() as Record<string, unknown>;
    const data = (body.data ?? body) as Record<string, unknown>;
    const identity = (data.user ?? data.session_user ?? data.identity ?? {}) as Record<string, unknown>;
    return {
      authenticated: Boolean(data.authenticated ?? data.logged_in ?? data.status === 'authenticated'),
      label: String(identity.name ?? identity.email ?? data.username ?? data.user_id ?? 'Operator'),
      scope: String(data.scope ?? data.role ?? 'Local session'),
    };
  } catch {
    return { authenticated: false, label: 'Local session', scope: 'Offline' };
  }
}
