import type { UiEvent } from '../contracts/events';

type EventHandler = (event: UiEvent) => void;

export class RealtimeClient {
  private socket: WebSocket | null = null;
  private sequence = 0;
  private heartbeat: number | undefined;
  private reconnectTimer: number | undefined;
  private reconnectAttempt = 0;
  private connecting = false;
  private readonly seen = new Set<string>();
  private readonly listeners = new Set<EventHandler>();

  constructor(private readonly onStatus: (status: 'connected' | 'connecting' | 'offline') => void) {}

  subscribe(listener: EventHandler) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  async connect() {
    if (this.connecting || (this.socket && this.socket.readyState <= WebSocket.OPEN)) return;
    this.connecting = true;
    this.onStatus('connecting');
    try {
      const ticket = await this.requestTicket();
      const protocol = globalThis.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = new URL(`${protocol}//${globalThis.location.host}/api/v1/ws`);
      if (ticket) url.searchParams.set('ticket', ticket);
      this.socket = new WebSocket(url.toString());
      this.socket.onopen = () => {
        this.connecting = false;
        this.reconnectAttempt = 0;
        this.onStatus('connected');
        this.socket?.send(JSON.stringify({ type: 'resume', cursor: this.sequence }));
        this.heartbeat = window.setInterval(() => this.socket?.send(JSON.stringify({ type: 'ping' })), 20000);
      };
      this.socket.onmessage = (message) => this.receive(message.data);
      this.socket.onclose = () => {
        this.connecting = false;
        this.scheduleReconnect();
      };
      this.socket.onerror = () => {
        this.connecting = false;
        this.onStatus('offline');
      };
    } catch {
      this.connecting = false;
      this.scheduleReconnect();
    }
  }

  disconnect() {
    if (this.heartbeat) window.clearInterval(this.heartbeat);
    if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer);
    this.socket?.close();
    this.socket = null;
    this.connecting = false;
  }

  send(payload: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify(payload));
  }

  private async requestTicket(): Promise<string | undefined> {
    try {
      const response = await fetch('/api/v1/auth/ws-ticket', { method: 'POST', credentials: 'include', headers: { Accept: 'application/json' } });
      if (!response.ok) return undefined;
      const body = await response.json() as { ticket?: string; data?: { ticket?: string } };
      return body.ticket ?? body.data?.ticket;
    } catch {
      return undefined;
    }
  }

  private receive(raw: string) {
    try {
      const parsed = JSON.parse(raw) as UiEvent & { event_id?: string; sequence?: number };
      const eventId = parsed.event_id ?? `${parsed.type}:${parsed.sequence ?? 0}`;
      if (this.seen.has(eventId)) return;
      this.seen.add(eventId);
      if (typeof parsed.sequence === 'number') this.sequence = Math.max(this.sequence, parsed.sequence);
      this.listeners.forEach((listener) => listener(parsed));
    } catch {
      // Invalid events are ignored; the next authoritative snapshot repairs state.
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.onStatus('offline');
    const delay = Math.min(30000, 800 * 2 ** this.reconnectAttempt++);
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = undefined;
      void this.connect();
    }, delay);
  }
}


