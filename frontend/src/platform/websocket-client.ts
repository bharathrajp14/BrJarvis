import type { UiEvent } from '../contracts/events';

type EventHandler = (event: UiEvent) => void;

const MAX_SEEN_EVENTS = 500;

export class RealtimeClient {
  private socket: WebSocket | null = null;
  private sequence = 0;
  private heartbeat: number | undefined;
  private reconnectTimer: number | undefined;
  private reconnectAttempt = 0;
  private connecting = false;
  private closed = false;
  private readonly seen = new Set<string>();
  private readonly seenOrder: string[] = [];
  private readonly listeners = new Set<EventHandler>();

  constructor(private readonly onStatus: (status: 'connected' | 'connecting' | 'offline') => void) {}

  subscribe(listener: EventHandler) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  async connect() {
    this.closed = false;
    if (this.connecting || (this.socket && this.socket.readyState <= WebSocket.OPEN)) return;
    this.connecting = true;
    this.onStatus('connecting');
    try {
      const ticket = await this.requestTicket();
      if (this.closed) {
        this.connecting = false;
        return;
      }
      const protocol = globalThis.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = new URL(`${protocol}//${globalThis.location.host}/api/v1/ws`);
      if (ticket) url.searchParams.set('ticket', ticket);
      this.socket = new WebSocket(url.toString());
      this.socket.onopen = () => {
        if (this.closed) {
          this.socket?.close();
          return;
        }
        this.connecting = false;
        this.reconnectAttempt = 0;
        this.onStatus('connected');
        this.socket?.send(JSON.stringify({ type: 'resume', cursor: this.sequence }));
        this.heartbeat = window.setInterval(() => this.socket?.send(JSON.stringify({ type: 'ping' })), 20000);
      };
      this.socket.onmessage = (message) => this.receive(message.data);
      this.socket.onclose = () => {
        this.connecting = false;
        this.socket = null;
        if (this.heartbeat) {
          window.clearInterval(this.heartbeat);
          this.heartbeat = undefined;
        }
        this.scheduleReconnect();
      };
      this.socket.onerror = () => {
        this.connecting = false;
        if (!this.closed) this.onStatus('offline');
      };
    } catch {
      this.connecting = false;
      this.scheduleReconnect();
    }
  }

  disconnect() {
    this.closed = true;
    if (this.heartbeat) {
      window.clearInterval(this.heartbeat);
      this.heartbeat = undefined;
    }
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;
      this.socket.close();
      this.socket = null;
    }
    this.connecting = false;
    this.onStatus('offline');
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
      this.seenOrder.push(eventId);
      if (this.seenOrder.length > MAX_SEEN_EVENTS) {
        const expired = this.seenOrder.splice(0, this.seenOrder.length - MAX_SEEN_EVENTS);
        expired.forEach((id) => this.seen.delete(id));
      }
      if (typeof parsed.sequence === 'number') this.sequence = Math.max(this.sequence, parsed.sequence);
      this.listeners.forEach((listener) => listener(parsed));
    } catch {
      // Invalid events are ignored; the next authoritative snapshot repairs state.
    }
  }

  private scheduleReconnect() {
    if (this.closed || this.reconnectTimer) return;
    this.onStatus('offline');
    const delay = Math.min(30000, 800 * 2 ** this.reconnectAttempt++);
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = undefined;
      void this.connect();
    }, delay);
  }
}
