import type { PlayerProfile } from './player';
import type { DrawingBatch, CanvasOperation } from './drawing';
export type RoomMode = 'individual' | 'team';
export interface RoomSettings { mode: RoomMode; seats: number; teamCount: number; seatsPerTeam: number; rounds: number }
export interface RoomPlayer { id: string; profile: PlayerProfile; connected: boolean; teamId?: string; joinedAt: number; solved?: boolean; score?: number }
export interface RoomTeam { id: string; name: string; capacity?: number }
export interface ChatMessage { id: string; playerId: string; text: string; at: number; kind?: 'chat' | 'correct' | 'system' }
export interface RoomGame { generation: number; canvasId: string; drawerId: string; hint: string; time: string; scores: Record<string, number>; round?: number; aiStatus?: 'waiting' | 'guessing' | 'correct' | 'wrong'; result?: { word: string; aiAnswers: string[]; aiCorrect: boolean; deltas: Record<string, number>; nextDrawerId?: string; finalAnswer?: string; countdown?: number; components?: Record<string, { guesserBase?: number; aiAdjustment?: number; drawerRecognition?: number; drawerBonus?: number }> } }
export interface RoomSnapshot { code: string; revision: number; settings: RoomSettings; players: RoomPlayer[]; teams: RoomTeam[]; hostId: string; phase: 'lobby' | 'drawing' | 'result' | 'closed'; chat: ChatMessage[]; startBlockers?: string[]; hostDisconnectedUntil?: number; game?: RoomGame }
export interface PrivateRoomState { role?: 'drawer' | 'guesser' | 'spectator'; target?: string }
export interface RoomSession { snapshot: RoomSnapshot; playerId: string; resumeToken: string; privateState?: PrivateRoomState; demo: boolean }
export type RoomEvent = { type: 'snapshot'; snapshot: RoomSnapshot; privateState?: PrivateRoomState } | { type: 'connection'; status: 'connecting' | 'connected' | 'disconnected' | 'restoring'; message?: string } | { type: 'drawing'; canvasId: string; generation: number; sequence: number; reset: boolean; caughtUp: boolean; operations: CanvasOperation[] } | { type: 'ack'; batchId: string; accepted: boolean; message?: string } | { type: 'gameplay'; name: string; payload?: unknown };
export interface RoomClient { create(profile: PlayerProfile): Promise<RoomSession>; join(code: string, profile: PlayerProfile): Promise<RoomSession>; resume(code: string, resumeToken: string): Promise<RoomSession>; updateSettings(settings: RoomSettings): Promise<void>; movePlayer(playerId: string, teamId: string): Promise<void>; selectTeam(teamId: string): Promise<void>; start(): Promise<void>; leave(): Promise<void>; sendChat(text: string): Promise<void>; submitGuess(text: string): Promise<void>; submitDrawing(batch: DrawingBatch): Promise<void>; resync(): Promise<void>; getSession(): RoomSession | null; subscribe(listener: (event: RoomEvent) => void): () => void; dispose(): void }
export class RoomClientError extends Error { constructor(public code: string, message: string, public retryable = false) { super(message); this.name = 'RoomClientError'; } }
export const DEFAULT_ROOM_SETTINGS: RoomSettings = { mode: 'individual', seats: 6, teamCount: 2, seatsPerTeam: 6, rounds: 6 };


