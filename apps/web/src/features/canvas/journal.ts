import type { CanvasOperation } from "@/contracts/drawing";

export interface DrawingJournal {
  append(operations: CanvasOperation[]): Promise<void>;
  load(): Promise<CanvasOperation[]>;
  clear(): Promise<void>;
}

/** Browser-local ordered journal. Each namespace is independent and op IDs are idempotent. */
export function openDrawingJournal(namespace: string): DrawingJournal {
  const database = () => new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open("more-than-meets-drawing-journal", 1);
    request.onupgradeneeded = () => request.result.createObjectStore("journals");
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  const transact = async <T>(mode: IDBTransactionMode, run: (store: IDBObjectStore, resolve: (value: T) => void, reject: (reason?: unknown) => void) => void) => {
    const db = await database();
    return new Promise<T>((resolve, reject) => {
      const tx = db.transaction("journals", mode);
      let result: T;
      run(tx.objectStore("journals"), value => { result = value; }, reject);
      tx.oncomplete = () => { db.close(); resolve(result); };
      tx.onerror = () => { db.close(); reject(tx.error); };
      tx.onabort = () => { db.close(); reject(tx.error ?? new Error("Journal transaction aborted")); };
    });
  };
  return {
    append(operations) {
      return transact<void>("readwrite", (store, resolve, reject) => {
        const request = store.get(namespace);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const entries: CanvasOperation[] = request.result ?? [];
          const seen = new Set(entries.map(op => op.opId));
          for (const operation of operations) if (!seen.has(operation.opId)) {
            entries.push(structuredClone(operation)); seen.add(operation.opId);
          }
          store.put(entries, namespace);
          resolve();
        };
      });
    },
    load() {
      return transact<CanvasOperation[]>("readonly", (store, resolve, reject) => {
        const request = store.get(namespace);
        request.onsuccess = () => resolve(request.result ?? []);
        request.onerror = () => reject(request.error);
      });
    },
    clear() {
      return transact<void>("readwrite", (store, resolve) => { store.delete(namespace); resolve(); });
    },
  };
}
