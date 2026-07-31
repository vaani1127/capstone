# HealthSaathi PWA - Progressive Web App

Modern web-based Hospital Management System built with React + TypeScript, replacing the Flutter mobile app.

## Features

✅ **Progressive Web App (PWA)**
- Installable on mobile devices ("Add to Home Screen")
- Works offline with service workers
- Instant updates (no app store needed)
- Single codebase for all devices

✅ **Real-time Updates**
- WebSocket support for live queue updates
- Instant notifications via Server-Sent Events

✅ **Role-Based Access**
- Doctor dashboard (queue management, consultations)
- Nurse dashboard (vitals, walk-in registration)
- Admin dashboard (user management, anomaly alerts)
- Patient portal (appointments, medical history)

✅ **Full Backend Integration**
- Connects to existing FastAPI backend
- All 54 API endpoints supported
- JWT authentication with token refresh
- Rate limiting and error handling

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **PWA**: vite-plugin-pwa
- **Styling**: CSS (no frameworks, keeps it lightweight)

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- FastAPI backend running (http://localhost:8000)

### Installation

```bash
# Navigate to web directory
cd project/web

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Update .env if backend is not at default location
# VITE_API_URL=http://your-backend:8000/api/v1
# VITE_WS_URL=ws://your-backend:8000
```

### Development

```bash
# Start dev server (hot reload)
npm run dev

# Open http://localhost:3000 in your browser
```

### Production Build

```bash
# Build for production
npm run build

# Preview build locally
npm run preview

# Deploy to your server
# The 'dist' folder contains all static files
```

## Project Structure

```
web/
├── public/
│   ├── manifest.json          # PWA manifest
│   ├── apple-touch-icon.png   # iOS home screen icon
│   └── icon-*.png             # Android icons
├── src/
│   ├── components/
│   │   └── ProtectedRoute.tsx # Role-based route protection
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DoctorDashboard.tsx
│   │   ├── NurseDashboard.tsx
│   │   ├── AdminDashboard.tsx
│   │   └── PatientDashboard.tsx
│   ├── services/
│   │   ├── api.ts            # API client with interceptors
│   │   └── websocket.ts      # WebSocket manager
│   ├── store/
│   │   └── auth.ts           # Zustand auth store
│   ├── styles/
│   │   ├── auth.css
│   │   └── dashboard.css
│   ├── App.tsx               # Main app with routing
│   ├── main.tsx              # React entry point
│   └── App.css
├── index.html                # HTML entry point
├── vite.config.ts            # Vite + PWA config
├── tsconfig.json             # TypeScript config
├── package.json
└── .env.example
```

## Features in Detail

### Authentication
- Email/password login
- JWT token storage
- Automatic token refresh
- Role-based access control
- Secure logout (clears all data)

### API Integration
- Axios client with interceptors
- Automatic token injection
- 401 error handling (auto-logout)
- 429 rate limit handling with user-friendly messages
- Request/response error handling

### WebSocket Real-Time Updates
- Auto-reconnect with exponential backoff
- Event-based message handling
- Graceful disconnection on logout
- Zero-dependency implementation

### PWA Capabilities
- Install prompt on supported browsers
- Service worker caching strategy
- Offline support (with service workers)
- Network-first caching for API calls

## Development Guidelines

### Adding New Pages
1. Create new file in `src/pages/` 
2. Wrap with `<ProtectedRoute roles={['Role']}>`
3. Add route in `App.tsx`

### Adding New API Calls
```typescript
// Use the apiClient
import { apiClient } from '@/services/api';

const data = await apiClient.get<T>('/endpoint');
const result = await apiClient.post('/endpoint', { ...data });
```

### Using WebSocket
```typescript
import { wsService } from '@/services/websocket';

// Subscribe to events
wsService.on('queue_update', (message) => {
  console.log('Queue updated:', message.data);
});

// Send data via API (if needed)
```

## Environment Variables

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

## Deployment

### Static Hosting (Vercel, Netlify, etc.)
```bash
npm run build
# Deploy the 'dist' folder
```

### Docker
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Backend Proxy
Ensure CORS is enabled on the FastAPI backend:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Common Issues & Solutions

### WebSocket Connection Failed
- Check backend is running with WebSocket support
- Verify `VITE_WS_URL` is correct
- Check firewall/CORS settings

### API Requests Getting 401
- Token might have expired
- App will auto-refresh, but logout if repeated
- Check `VITE_API_URL` is correct

### PWA Not Installing
- Must be served over HTTPS (except localhost)
- Check manifest.json is valid
- Clear browser cache and retry

## Testing

### Manual Testing Checklist
- [ ] Login with test credentials
- [ ] Verify correct role redirects to correct dashboard
- [ ] Check queue loads and updates
- [ ] Verify logout clears all data
- [ ] Test on mobile device (install PWA)
- [ ] Check offline behavior
- [ ] Verify rate limit messages
- [ ] Test WebSocket reconnection

### Browser DevTools
- Application tab: Check service worker, manifest, storage
- Network tab: Monitor API calls and WebSocket
- Console: Check for errors
- Performance: Analyze load time

## Maintenance

### Security
- Keep dependencies updated: `npm audit fix`
- Review auth token handling
- Validate all user inputs
- Use HTTPS in production

### Performance
- Monitor bundle size
- Use React DevTools Profiler
- Optimize images
- Cache service worker updates

### Monitoring
- Log all errors
- Monitor WebSocket disconnections
- Track API response times
- Check deployment health

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Push notifications (Web Push API)
- [ ] Sync queue data offline
- [ ] Export reports to PDF
- [ ] Multi-language support
- [ ] Accessibility (WCAG 2.1)
- [ ] Unit tests (Jest + React Testing Library)
- [ ] E2E tests (Cypress)

## License

Part of HealthSaathi capstone project

## Support

For issues or questions, refer to the backend documentation or contact the development team.
