import type { RoomSession } from '@/contracts/room';
import { persistLocalRoomSession, deleteLocalRoomSession } from './local';
import { DEFAULT_ROOM_SETTINGS } from '@/contracts/room';
import { DEFAULT_AVATAR } from '@/contracts/player';
export type ReviewScenario = 'lobby' | 'drawer' | 'guesser' | 'result-correct' | 'result-missed' | 'restoring' | 'team-minimum' | 'host-recovery' | 'host-transfer' | 'invite-full' | 'invite-not-found' | 'invite-in-progress' | 'drawer-away' | 'ai-guessing' | 'ai-wrong' | 'ai-correct';
/** Isolated deterministic browser-only fixtures for the review route. */
export async function seedReviewScenario(name: ReviewScenario): Promise<RoomSession> {
  const playerId = 'review-you';
  const isResult = name.startsWith('result-');
  const drawer = name !== 'guesser' && !isResult;
  const session: RoomSession = {
    playerId, resumeToken: 'review-token', demo: true,
    privateState: { role: drawer ? 'drawer' : 'guesser', ...(drawer ? { target: 'cat' } : {}) },
    snapshot: {
      code: 'REVIEW', revision: 1, settings: { ...DEFAULT_ROOM_SETTINGS }, hostId: playerId,
      phase: name === 'lobby' ? 'lobby' : isResult ? 'result' : 'drawing', chat: [], teams: [],
      players: [
        { id: playerId, profile: { name: 'You', avatar: DEFAULT_AVATAR }, connected: true, joinedAt: 1, score: 0, ...(name === 'result-correct' ? { solved: true } : {}) },
        { id: 'review-friend', profile: { name: 'Friend', avatar: { ...DEFAULT_AVATAR, color: 'pink' } }, connected: true, joinedAt: 2, score: 0 },
      ],
      ...(name === 'lobby' ? {} : { game: { generation: 1, canvasId: 'review-canvas', drawerId: drawer ? playerId : 'review-friend', hint: '_ _ _', time: '--:--', round: 1, aiStatus: 'waiting' as const, scores: {}, ...(isResult ? { result: { word: 'cat', aiAnswers: name === 'result-correct' ? ['dog', 'cat'] : ['bird', 'dog'], aiCorrect: name === 'result-correct', deltas: { [playerId]: name === 'result-correct' ? 100 : 0 }, finalAnswer: name === 'result-correct' ? 'cat' : 'dog', components: { [playerId]: { guesserBase: name === 'result-correct' ? 100 : 0, aiAdjustment: 0 } } } } : {}) } }),
    },
  };
  if (name === 'drawer-away') { session.privateState = { role: 'guesser' }; session.snapshot.game!.drawerId = 'review-friend'; session.snapshot.players[1].connected = false; }
  if (name === 'ai-guessing' || name === 'ai-wrong' || name === 'ai-correct') session.snapshot.game!.aiStatus = name.slice(3) as 'guessing' | 'wrong' | 'correct';
  if (name === 'team-minimum') {
    session.snapshot.settings = { ...session.snapshot.settings, mode: 'team' };
    session.snapshot.teams = [{ id: 'team-1', name: 'Team 1' }, { id: 'team-2', name: 'Team 2' }];
    session.snapshot.players.forEach(player => { player.teamId = 'team-1'; });
    session.snapshot.phase = 'lobby';
    session.snapshot.startBlockers = ['Team 2 needs two connected players.'];
  }
  if (name === 'host-recovery') { session.snapshot.hostId = 'review-friend'; session.snapshot.players[1].connected = false; session.snapshot.hostDisconnectedUntil = Date.now() + 30000; session.snapshot.phase = 'lobby'; }
  if (name === 'host-transfer') { session.snapshot.hostId = playerId; session.snapshot.phase = 'lobby'; }
  if (name === 'invite-full') { session.snapshot.settings.seats = 2; session.snapshot.phase = 'lobby'; }
  if (name === 'invite-in-progress') session.snapshot.phase = 'drawing';
  if (name === 'invite-not-found') await deleteLocalRoomSession(session.snapshot.code);
  else await persistLocalRoomSession(session);
  return session;
}
