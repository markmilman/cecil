# Cecil UI Implementation

## Overview

This document describes the implementation of GitHub Issue #5 (TS.5): React Boilerplate & Design System Integration.

## Completed Sub-Issues

### Sub-issue #28: Initialize Vite/React project in /ui

**Implementation:**
- Created Vite+React+TypeScript project structure in `/Users/mark/dev/cecil/ui/`
- Preserved existing `src/` subdirectory structure
- Configured TypeScript in strict mode
- All source files use `.ts` or `.tsx` extensions (no `.js`/`.jsx` files)

**Key Files:**
- `package.json` - Project dependencies and scripts
- `vite.config.ts` - Vite build configuration
- `tsconfig.json` - TypeScript strict mode configuration
- `tsconfig.node.json` - TypeScript configuration for build scripts
- `.eslintrc.cjs` - ESLint configuration for TypeScript and React

### Sub-issue #29: Configure tailwind.config.js with Cecil design tokens

**Implementation:**
- Installed Tailwind CSS 4 (alpha) with @tailwindcss/vite plugin
- Configured custom design tokens matching Cecil's CFO-centric aesthetic
- Created minimal `src/index.css` with Tailwind directives and CSS resets
- No `@apply`, no dark mode variants (as per requirements)

**Design Tokens:**
```javascript
{
  primary: '#0f172a',     // slate-900 - Headings, primary text, nav
  accent: '#4f46e5',      // indigo-600 - Buttons, links, active states
  success: '#10b981',     // emerald-500 - Savings indicators
  danger: '#ef4444',      // red-500 - Errors, destructive actions
  muted: '#64748b',       // slate-500 - Secondary labels, captions
}
```

**Key Files:**
- `tailwind.config.js` - Tailwind configuration with Cecil tokens
- `src/index.css` - CSS resets and Tailwind imports

### Sub-issue #30: Install lucide-react for iconography

**Implementation:**
- Installed `lucide-react` as a dependency
- Used in Shell component (MapIcon, FileSearchIcon)
- Used in page components for visual consistency

**Usage Example:**
```typescript
import { MapIcon, FileSearchIcon } from 'lucide-react';
```

### Sub-issue #31: Build ApiClient.ts wrapper with local FastAPI base URL

**Implementation:**
- Created `src/lib/apiClient.ts` with Axios-based API client
- Configured for local FastAPI server on `127.0.0.1`
- Included typed health check method
- Custom error handling with `ApiClientError` class
- Environment variable support for port configuration

**Key Features:**
- Type-safe API responses
- Centralized error handling
- Response interceptors
- Configurable base URL and timeout
- Health check endpoint (`/api/v1/health`)

**Key Files:**
- `src/lib/apiClient.ts` - API client implementation
- `src/lib/apiClient.test.ts` - Unit tests
- `.env.example` - Environment variable template

### Sub-issue #32: Create Shell layout with navigation placeholders

**Implementation:**
- Created `Shell` component in `src/components/common/Shell.tsx`
- Implemented navigation sidebar with Cecil branding
- Created placeholder page components (MappingPage, AuditPage)
- Set up React Router for navigation
- Applied Cecil design tokens throughout

**Components Created:**
- `src/components/common/Shell.tsx` - Main layout component
- `src/pages/MappingPage.tsx` - Schema mapping page placeholder
- `src/pages/AuditPage.tsx` - Audit view page placeholder
- `src/App.tsx` - Main app with routing
- `src/main.tsx` - Application entry point
- `index.html` - HTML entry point

**Navigation Structure:**
- `/mapping` - Schema mapping interface (default route)
- `/audit` - Audit view interface
- `/` - Redirects to `/mapping`

## Testing

**Test Infrastructure:**
- Vitest configured with jsdom environment
- React Testing Library for component testing
- Test setup file with @testing-library/jest-dom

**Tests Created:**
- `src/components/common/Shell.test.tsx` - Shell component smoke tests
- `src/lib/apiClient.test.ts` - API client unit tests

**Running Tests:**
```bash
cd /Users/mark/dev/cecil/ui
npm test
```

## Code Style Compliance

All code follows the Cecil Style Guide (CLAUDE.md):

✅ TypeScript strict mode
✅ Named exports only (no default exports)
✅ Functional components with hooks
✅ Import order: React → third-party → internal (@/...) → relative
✅ Tailwind utilities directly (no custom CSS except index.css)
✅ lucide-react for all icons
✅ Google-style docstrings on public components

## File Structure

```
ui/
├── public/
│   └── vite.svg                    # Favicon
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Shell.tsx           # Main layout
│   │   │   └── Shell.test.tsx      # Shell tests
│   │   ├── mapping/                # (placeholder for mapping components)
│   │   └── audit/                  # (placeholder for audit components)
│   ├── hooks/                      # (placeholder for custom hooks)
│   ├── lib/
│   │   ├── apiClient.ts            # API client
│   │   └── apiClient.test.ts       # API client tests
│   ├── pages/
│   │   ├── MappingPage.tsx         # Mapping page
│   │   └── AuditPage.tsx           # Audit page
│   ├── test/
│   │   └── setup.ts                # Test setup
│   ├── types/
│   │   └── index.ts                # Shared types
│   ├── App.tsx                     # Main app component
│   ├── main.tsx                    # Entry point
│   ├── index.css                   # Global styles
│   └── vite-env.d.ts               # Vite types
├── .env.example                    # Environment template
├── .eslintrc.cjs                   # ESLint config
├── .gitignore                      # Git ignore rules
├── index.html                      # HTML entry point
├── package.json                    # Dependencies
├── tailwind.config.js              # Tailwind config
├── tsconfig.json                   # TypeScript config
├── tsconfig.node.json              # TypeScript build config
├── vite.config.ts                  # Vite config
├── vitest.config.ts                # Vitest config
├── README.md                       # UI documentation
└── IMPLEMENTATION.md               # This file
```

## Next Steps

Before merging, run the following commands:

```bash
# Install dependencies
cd /Users/mark/dev/cecil/ui
npm install

# Run linter
npm run lint

# Run tests
npm test

# Verify Python code still passes
cd /Users/mark/dev/cecil
ruff check src/ tests/
mypy --strict src/cecil/
```

## Build Output

Production builds output to `../src/cecil/ui_dist/` for bundling with PyInstaller:

```bash
cd /Users/mark/dev/cecil/ui
npm run build
```

## Development Server

Start the development server:

```bash
cd /Users/mark/dev/cecil/ui
npm run dev
```

The UI will be available at `http://localhost:5173`

## Integration with FastAPI

The UI expects the FastAPI server to be running on `http://127.0.0.1:8000` by default. Configure via environment variable if needed:

```bash
echo "VITE_API_PORT=8000" > .env
```

## Notes

- The UI is ready for PyInstaller bundling via the `ui_dist` output directory
- All components use Cecil design tokens for consistent branding
- Navigation is functional with React Router
- API client is ready to communicate with the FastAPI backend
- Test infrastructure is in place for future development
