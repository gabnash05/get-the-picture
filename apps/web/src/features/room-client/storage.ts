import type { RoomSession } from '@/contracts/room';
const database = () => new Promise<IDBDatabase>((resolve, reject) => {
  const request = indexedDB.open('more-than-meets-room-demo', 1);
  request.onupgradeneeded = () => request.result.createObjectStore('rooms');
  request.onsuccess = () => resolve(request.result);
  request.onerror = () => reject(request.error);
});
async function transaction<T>(mode: IDBTransactionMode, operation: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await database();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('rooms', mode);
    const request = operation(tx.objectStore('rooms'));
    tx.oncomplete = () => { db.close(); resolve(request.result); };
    tx.onerror = () => { db.close(); reject(tx.error); };
    tx.onabort = () => { db.close(); reject(tx.error); };
  });
}
export async function persistLocalRoomSession(session: RoomSession): Promise<void> { await transaction('readwrite', store => store.put(session, session.snapshot.code)); await transaction('readwrite', store => store.put({ playerId: session.playerId, resumeToken: session.resumeToken, privateState: session.privateState }, `session:${session.resumeToken}`)); }
export async function loadLocalRoomSession(code: string): Promise<RoomSession | null> { return (await transaction('readonly', store => store.get(code))) ?? null; }
export async function deleteLocalRoomSession(code: string): Promise<void> { await transaction('readwrite', store => store.delete(code)); }

export async function loadLocalCredential(token: string): Promise<Pick<RoomSession, 'playerId' | 'resumeToken' | 'privateState'> | null> { return (await transaction('readonly', store => store.get(`session:${token}`))) ?? null; }
