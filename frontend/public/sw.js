// Advanced Options Trading Calculator - Service Worker
// Version 2.0.0 - PWA Phase 4 Implementation

const CACHE_NAME = 'options-calculator-v2.0.0';
const DATA_CACHE_NAME = 'options-calculator-data-v2.0.0';
const OFFLINE_CACHE_NAME = 'options-calculator-offline-v2.0.0';

// Cache strategies
const CACHE_STRATEGIES = {
  CACHE_FIRST: 'cache-first',
  NETWORK_FIRST: 'network-first',
  STALE_WHILE_REVALIDATE: 'stale-while-revalidate',
  NETWORK_ONLY: 'network-only',
  CACHE_ONLY: 'cache-only'
};

// URLs to cache on install
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/js/bundle.js',
  '/static/css/main.css',
  // App shell resources
  '/charts',
  '/charts/comparison',
  '/reports',
  '/settings',
  // Icons and assets
  '/icon-192x192.png',
  '/icon-512x512.png',
  '/apple-touch-icon.png',
  '/favicon-32x32.png',
  '/favicon-16x16.png'
];

// API endpoints that should be cached
const API_CACHE_PATTERNS = [
  /^https:\/\/api\..*\/options\/.*/,
  /^https:\/\/.*\.yahoo\.com\/v8\/finance\/chart\/.*/,
  /^https:\/\/api\.polygon\.io\/v2\/.*/,
  /^https:\/\/finnhub\.io\/api\/v1\/.*/
];

// Demo data for offline functionality
const OFFLINE_DEMO_DATA = {
  symbols: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX'],
  
  sampleAnalysis: {
    symbol: 'AAPL',
    currentPrice: 175.50,
    analysis: {
      calendar_trade: {
        strike: 175.00,
        net_debit: 2.50,
        max_profit: 7.50,
        days_to_expiration: 30,
        probability_of_profit: 0.65
      },
      greeks: {
        delta: 0.15,
        gamma: 0.025,
        theta: -0.08,
        vega: 0.12
      },
      pnl_scenarios: [
        { price: 160, pnl: -2.5, days: 30 },
        { price: 170, pnl: 4.2, days: 30 },
        { price: 175, pnl: 7.5, days: 30 },
        { price: 180, pnl: 4.1, days: 30 },
        { price: 190, pnl: -2.5, days: 30 }
      ]
    },
    timestamp: new Date().toISOString()
  }
};

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static resources
      caches.open(CACHE_NAME).then((cache) => {
        console.log('[ServiceWorker] Caching static resources');
        return cache.addAll(STATIC_CACHE_URLS.filter(url => url));
      }),
      
      // Cache offline demo data
      caches.open(OFFLINE_CACHE_NAME).then((cache) => {
        console.log('[ServiceWorker] Caching offline demo data');
        const demoResponse = new Response(JSON.stringify(OFFLINE_DEMO_DATA), {
          headers: { 'Content-Type': 'application/json' }
        });
        return cache.put('/api/demo/analysis', demoResponse);
      })
    ]).then(() => {
      console.log('[ServiceWorker] Installation complete');
      // Skip waiting to activate immediately
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== DATA_CACHE_NAME && 
              cacheName !== OFFLINE_CACHE_NAME) {
            console.log('[ServiceWorker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[ServiceWorker] Activation complete');
      // Take control of all pages immediately
      return self.clients.claim();
    })
  );
});

// Fetch event - handle network requests with different strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle different types of requests with appropriate strategies
  if (request.method !== 'GET') {
    return; // Only handle GET requests
  }
  
  // API requests - Network First with offline fallback
  if (isAPIRequest(url)) {
    event.respondWith(handleAPIRequest(request));
  }
  // Static resources - Cache First
  else if (isStaticResource(url)) {
    event.respondWith(handleStaticResource(request));
  }
  // Navigation requests - Stale While Revalidate
  else if (isNavigationRequest(request)) {
    event.respondWith(handleNavigationRequest(request));
  }
  // Everything else - Network First
  else {
    event.respondWith(handleNetworkFirst(request));
  }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);
  
  if (event.tag === 'background-sync-analysis') {
    event.waitUntil(syncPendingAnalysis());
  }
});

// Push notification handling
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received:', event);
  
  const options = {
    body: event.data ? event.data.text() : 'New trading opportunity available!',
    icon: '/icon-192x192.png',
    badge: '/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: event.data ? JSON.parse(event.data.text()) : {},
    actions: [
      {
        action: 'open',
        title: 'Open App',
        icon: '/icon-192x192.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icon-192x192.png'
      }
    ],
    requireInteraction: true,
    tag: 'options-alert'
  };
  
  event.waitUntil(
    self.registration.showNotification('Options Trading Alert', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    // Open the app
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          // Focus existing window if available
          for (const client of clientList) {
            if (client.url.includes('/') && 'focus' in client) {
              return client.focus();
            }
          }
          // Open new window if no existing window
          if (clients.openWindow) {
            return clients.openWindow('/');
          }
        })
    );
  }
});

// Helper functions

function isAPIRequest(url) {
  return url.pathname.startsWith('/api/') || 
         API_CACHE_PATTERNS.some(pattern => pattern.test(url.href));
}

function isStaticResource(url) {
  return url.pathname.includes('.') && 
         (url.pathname.endsWith('.js') || 
          url.pathname.endsWith('.css') || 
          url.pathname.endsWith('.png') || 
          url.pathname.endsWith('.jpg') || 
          url.pathname.endsWith('.svg') || 
          url.pathname.endsWith('.ico'));
}

function isNavigationRequest(request) {
  return request.mode === 'navigate' || 
         (request.method === 'GET' && request.headers.get('accept').includes('text/html'));
}

async function handleAPIRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful API responses
      const cache = await caches.open(DATA_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
  } catch (error) {
    console.log('[ServiceWorker] API network failed, trying cache:', error);
    
    // Try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline demo data if available
    if (request.url.includes('/api/analysis')) {
      const offlineCache = await caches.open(OFFLINE_CACHE_NAME);
      const demoResponse = await offlineCache.match('/api/demo/analysis');
      if (demoResponse) {
        return demoResponse;
      }
    }
    
    // Return offline response
    return new Response(JSON.stringify({
      error: 'Offline mode - limited functionality available',
      offline: true,
      timestamp: new Date().toISOString()
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 503
    });
  }
}

async function handleStaticResource(request) {
  // Cache first strategy
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('[ServiceWorker] Static resource failed:', error);
    return new Response('Resource unavailable offline', { status: 404 });
  }
}

async function handleNavigationRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache the page
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
  } catch (error) {
    console.log('[ServiceWorker] Navigation network failed, trying cache:', error);
    
    // Try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return app shell
    const appShell = await caches.match('/');
    if (appShell) {
      return appShell;
    }
    
    // Return offline page
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Offline - Options Calculator</title>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 2rem; text-align: center; }
            .offline-container { max-width: 400px; margin: 0 auto; }
            .offline-icon { font-size: 4rem; margin-bottom: 1rem; }
            .offline-title { color: #374151; margin-bottom: 1rem; }
            .offline-message { color: #6b7280; margin-bottom: 2rem; }
            .retry-button { background: #2563eb; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 0.5rem; cursor: pointer; }
          </style>
        </head>
        <body>
          <div class="offline-container">
            <div class="offline-icon">📱</div>
            <h1 class="offline-title">You're Offline</h1>
            <p class="offline-message">Check your connection and try again. Some features are available offline.</p>
            <button class="retry-button" onclick="window.location.reload()">Try Again</button>
          </div>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' },
      status: 200
    });
  }
}

async function handleNetworkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    return new Response('Resource unavailable', { status: 404 });
  }
}

async function syncPendingAnalysis() {
  // Handle background sync for pending analysis requests
  try {
    const pending = await getFromIndexedDB('pending-analysis');
    if (pending && pending.length > 0) {
      for (const analysis of pending) {
        await fetch('/api/analysis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(analysis)
        });
      }
      await clearFromIndexedDB('pending-analysis');
    }
  } catch (error) {
    console.error('[ServiceWorker] Background sync failed:', error);
  }
}

// IndexedDB helpers for background sync
async function getFromIndexedDB(key) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('options-calculator-sync', 1);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['sync-data'], 'readonly');
      const store = transaction.objectStore('sync-data');
      const getRequest = store.get(key);
      getRequest.onsuccess = () => resolve(getRequest.result?.data);
      getRequest.onerror = () => reject(getRequest.error);
    };
    request.onerror = () => reject(request.error);
  });
}

async function clearFromIndexedDB(key) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('options-calculator-sync', 1);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['sync-data'], 'readwrite');
      const store = transaction.objectStore('sync-data');
      const deleteRequest = store.delete(key);
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
    request.onerror = () => reject(request.error);
  });
}