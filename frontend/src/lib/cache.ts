// In-memory cache with TTL. For serverless (Vercel), set Cache-Control headers.
// For local long-running server, this avoids hitting Turso on every request.

const store = new Map<string, { data: any; expires: number }>();

export function getCached(key: string): any | null {
  const entry = store.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expires) {
    store.delete(key);
    return null;
  }
  return entry.data;
}

export function setCache(key: string, data: any, ttlSeconds: number = 300) {
  store.set(key, { data, expires: Date.now() + ttlSeconds * 1000 });
}

export function invalidateCache(prefix?: string) {
  if (prefix) {
    for (const key of store.keys()) {
      if (key.startsWith(prefix)) store.delete(key);
    }
  } else {
    store.clear();
  }
}

// Aggressive CDN cache headers for Vercel edge
export const CACHE_5MIN = {
  "Cache-Control": "public, max-age=300, s-maxage=300, stale-while-revalidate=600",
};

export const CACHE_1MIN = {
  "Cache-Control": "public, max-age=60, s-maxage=60, stale-while-revalidate=120",
};
