import type { UiEvent } from '../contracts/events';

const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '').replace(/\/$/, '');
type EventHandler = (event: UiEvent) => void;

export class RealtimeClient {
  private socket: WebSocket | null = null;
  private heartbeat: number | undefined;
  private reconnectTimer: number | undefined;
  private reconnectAttempt = 0;
  private connecting = false;
  private stopped = true;
  private readonly seen = new Set<string>();
  private readonly seenOrder: string[] = [];
  private readonly listeners = new Set<EventHandler>();

  constructor(private readonly onStatus: (status: 'connected' | 'connecting' | 'offline') => void) {}

  subscribe(listener: EventHandler) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  async connect() {
    this.stopped = false;
    if (this.connecting || (this.socket && this.socket.readyState <= WebSocket.OPEN)) return;
    this.connecting = true;
    this.onStatus('connecting');
    try {
      const ticket = await this.requestTicket();
      if (this.stopped) return;
      const origin = API_BASE ? new URL(API_BASE, globalThis.location.href) : new URL(globalThis.location.href);
      origin.protocol = origin.protocol === 'https:' ? 'wss:' : 'ws:';
      origin.pathname = '/api/v1/ws';
      origin.search = '';
      if (ticket) origin.searchParams.set('ticket', ticket);
      const socket = new WebSocket(origin.toString());
      this.socket = socket;
      socket.onopen = () => {
        if (this.stopped || socket !== this.socket) return;
        this.connecting = false;
        this.reconnectAttempt = 0;
        this.clearHeartbeat();
        this.onStatus('connected');
        this.heartbeat = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }));
        }, 20000);
      };
      socket.onmessage = (message) => this.receive(message.data);
      socket.onclose = () => {
        if (socket !== this.socket) return;
        this.socket = null;
        this.connecting = false;
        this.clearHeartbeat();
        if (!this.stopped) this.scheduleReconnect();
      };
      socket.onerror = () => {
        if (socket !== this.socket || this.stopped) return;
        this.onStatus('offline');
      };
    } catch {
      this.connecting = false;
      if (!this.stopped) this.scheduleReconnect();
    }
  }

  disconnect() {
    this.stopped = true;
    this.clearHeartbeat();
    if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = undefined;
    const socket = this.socket;
    this.socket = null;
    socket?.close();
    this.connecting = false;
  }

  send(payload: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify(payload));
  }

  private async requestTicket(): Promise<string | undefined> {
    const response = await fetch(`${API_BASE}/api/v1/auth/ws-ticket`, { method: 'POST', credentials: 'include', headers: { Accept: 'application/json' } });
    if (!response.ok) return undefined;
    const body = await response.json() as { ticket?: string; data?: { ticket?: string } };
    return body.ticket ?? body.data?.ticket;
  }

  private receive(raw: string) {
    try {
      const parsed = JSON.parse(raw) as UiEvent & { event_id?: string };
      const eventId = parsed.event_id;
      if (eventId) {
        if (this.seen.has(eventId)) return;
        this.seen.add(eventId);
        this.seenOrder.push(eventId);
        if (this.seenOrder.length > 500) {
          const oldest = this.seenOrder.shift();
          if (oldest) this.seen.delete(oldest);
        }
      }
      this.listeners.forEach((listener) => listener(parsed));
    } catch {
      // The next authoritative REST snapshot repairs malformed or unknown events.
    }
  }

  private clearHeartbeat() {
    if (this.heartbeat) window.clearInterval(this.heartbeat);
    this.heartbeat = undefined;
  }

  private scheduleReconnect() {
    if (this.stopped || this.reconnectTimer) return;
    this.onStatus('offline');
    const delay = Math.min(30000, 800 * 2 ** this.reconnectAttempt++);
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = undefined;
      void this.connect();
    }, delay);
  }
}
