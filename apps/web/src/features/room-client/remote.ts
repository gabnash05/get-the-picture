import { io, type Socket } from 'socket.io-client';
import type { RoomClient, RoomEvent, RoomSession, RoomSettings } from '@/contracts/room';
import { RoomClientError } from '@/contracts/room';
import type { PlayerProfile } from '@/contracts/player';
import type { DrawingBatch } from '@/contracts/drawing';
export interface RemoteOptions { apiUrl?: string; socketUrl?: string; fetch?: typeof fetch; socketFactory?: (url: string, options: { autoConnect: false; auth: { token: string; code: string } }) => Socket }
export class RemoteRoomClient implements RoomClient {
  private session: RoomSession | null = null;
  private socket: Socket | null = null;
  private sequence = -1;
  private pending = new Map<string, string>();
  private stream = '';
  private unbind: (() => void) | null = null;
  private listeners = new Set<(event: RoomEvent) => void>();
  private fetcher: typeof fetch;
  constructor(private options: RemoteOptions = {}) { this.fetcher = options.fetch ?? fetch; }
  private emit(event: RoomEvent) { this.listeners.forEach(fn => fn(event)); }
  private async bootstrap(path: string, init?: RequestInit) { let response: Response; try { response = await this.fetcher(`${this.options.apiUrl ?? ''}${path}`, init); } catch { throw new RoomClientError('connection', 'Could not connect to the room service.', true); } if (!response.ok) { let payload: { code?: string; message?: string } = {}; try { payload = await response.json(); } catch {} throw new RoomClientError(payload.code ?? 'connection', payload.message ?? 'Room request failed.', response.status >= 500); } const session = await response.json() as RoomSession; if (!session || typeof session.playerId !== 'string' || typeof session.resumeToken !== 'string' || !session.snapshot || typeof session.snapshot.code !== 'string' || !Number.isInteger(session.snapshot.revision)) throw new RoomClientError('malformed', 'Room service returned an invalid session.'); this.session = session; this.connect(session); return session; }
  private connect(session: RoomSession) {
    this.unbind?.();
    this.socket?.disconnect();
    const socket = this.options.socketFactory?.(this.options.socketUrl ?? '', { autoConnect: false, auth: { token: session.resumeToken, code: session.snapshot.code } }) ?? io(this.options.socketUrl ?? undefined, { autoConnect: false, auth: { token: session.resumeToken, code: session.snapshot.code } });
    this.socket = socket;
    const onConnect = () => { this.emit({ type: 'connection', status: 'restoring' }); void this.command('room:resync').catch(error => this.emit({ type: 'connection', status: 'disconnected', message: error.message })); };
    const onDisconnect = () => this.emit({ type: 'connection', status: 'disconnected' });
    const onError = (error: Error) => this.emit({ type: 'connection', status: 'disconnected', message: error.message });
    const onEvent = (event: RoomEvent) => {
      if (!event || typeof event !== 'object' || typeof event.type !== 'string') return;
      if (event.type === 'snapshot') {
        if (!event.snapshot || !Number.isInteger(event.snapshot.revision) || (this.session && event.snapshot.revision <= this.session.snapshot.revision)) return;
        if (this.session) { this.session.snapshot = event.snapshot; this.session.privateState = event.privateState; }
      }
      if (event.type === 'drawing') {
        const game = this.session?.snapshot.game;
        if (!game || event.canvasId !== game.canvasId || event.generation !== game.generation || !Number.isInteger(event.sequence) || !Array.isArray(event.operations)) return;
        const stream = `${event.canvasId}:${event.generation}`;
        if (stream !== this.stream) { this.stream = stream; this.sequence = -1; }
        if (event.sequence < this.sequence || (!event.reset && event.sequence === this.sequence)) return;
        if (!event.reset && this.sequence >= 0 && event.sequence > this.sequence + event.operations.length) { void this.resync(); return; }
        this.sequence = event.sequence;
      }
      this.emit(event);
      if (event.type === 'drawing' && event.caughtUp) this.emit({ type: 'connection', status: 'connected' });
      if (event.type === 'snapshot' && !event.snapshot.game) this.emit({ type: 'connection', status: 'connected' });
    };
    socket.on('connect', onConnect); socket.on('disconnect', onDisconnect); socket.on('connect_error', onError); socket.on('room:event', onEvent);
    this.unbind = () => { socket.off('connect', onConnect); socket.off('disconnect', onDisconnect); socket.off('connect_error', onError); socket.off('room:event', onEvent); };
    socket.connect();
  }
  private command(name: string, payload?: unknown): Promise<void> { if (!this.socket?.connected) return Promise.reject(new RoomClientError('connection', 'Connection lost. Retry after restoring.', true)); const key = JSON.stringify([name, payload]); const requestId = this.pending.get(key) ?? globalThis.crypto.randomUUID(); this.pending.set(key, requestId); return new Promise((resolve, reject) => { this.socket!.timeout(10000).emit(name, { requestId, expectedRevision: this.session?.snapshot.revision, generation: this.session?.snapshot.game?.generation, payload }, (error: Error | null, result?: { ok: boolean; code?: string; message?: string }) => { if (error) reject(new RoomClientError('connection', 'Request timed out.', true)); else if (!result?.ok) reject(new RoomClientError(result?.code ?? 'rejected', result?.message ?? 'Request rejected.')); else { this.pending.delete(key); resolve(); } }); }); }
  create(profile: PlayerProfile) { return this.bootstrap('/api/rooms', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ profile }) }); }
  join(code: string, profile: PlayerProfile) { return this.bootstrap(`/api/rooms/${encodeURIComponent(code.trim().toUpperCase())}/join`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ profile }) }); }
  resume(code: string, token: string) { this.emit({ type: 'connection', status: 'restoring' }); return this.bootstrap(`/api/rooms/${encodeURIComponent(code)}/resume`, { headers: { authorization: `Bearer ${token}` } }); }
  updateSettings(settings: RoomSettings) { return this.command('room:settings', settings); }
  movePlayer(playerId: string, teamId: string) { return this.command('room:move', { playerId, teamId }); }
  selectTeam(teamId: string) { return this.command('room:select-team', { teamId }); }
  start() { return this.command('room:start'); }
  async leave() { await this.command('room:leave'); this.dispose(); this.session = null; }
  sendChat(text: string) { return this.command('room:chat', { text }); }
  submitGuess(text: string) { return this.command('room:guess', { text }); }
  submitDrawing(batch: DrawingBatch) { return this.command('room:drawing', batch); }
  async resync() {
    const socket = this.socket;
    if (!socket) throw new RoomClientError('connection', 'No room session to restore.', true);
    if (!socket.connected) {
      this.emit({ type: 'connection', status: 'restoring' });
      await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(() => { socket.off('connect', connected); socket.off('connect_error', failed); reject(new RoomClientError('connection', 'Reconnect timed out.', true)); }, 10000);
        const connected = () => { clearTimeout(timer); socket.off('connect_error', failed); resolve(); };
        const failed = () => { clearTimeout(timer); socket.off('connect', connected); reject(new RoomClientError('connection', 'Reconnect failed.', true)); };
        socket.once('connect', connected); socket.once('connect_error', failed); socket.connect();
      });
      return;
    }
    await this.command('room:resync');
  }
  getSession() { return this.session; }
  subscribe(fn: (event: RoomEvent) => void) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  dispose() { this.unbind?.(); this.unbind = null; this.socket?.disconnect(); this.socket = null; this.listeners.clear(); }
}



