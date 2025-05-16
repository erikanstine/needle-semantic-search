const CACHE_KEY = 'needleQueryCache';

export function getCachedResult(queryKey) {
    try {
        const cache = JSON.parse(localStorage.getItem(CACHE_KEY)) || {};
        const entry = cache[queryKey];

        if (!entry) return null;

        const age = Date.now() - entry.timestamp;
        const ttl = 5 * 60 * 1000; // 5 minutes

        if (age > ttl) {
            delete cache[queryKey];
            localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
            return null;
        }

        return entry;
    } catch {
        return null;
    }
}

export function setCachedResult(queryKey, result) {
    try {
        const cache = JSON.parse(localStorage.getItem(CACHE_KEY)) || {};
        cache[queryKey] = {
            ...result,
            timestamp: Date.now(),
        };
        localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
    } catch {
        // fail silently
    }
}