# Cecil UI

React frontend for Cecil Data Sanitizer & Cost Optimizer.

## Tech Stack

- **React 18** with TypeScript (strict mode)
- **Vite** for fast development and optimized builds
- **Tailwind CSS 4** for styling with custom design tokens
- **React Router** for navigation
- **Axios** for API communication
- **Vitest** and React Testing Library for testing
- **lucide-react** for icons

## Design Tokens

Cecil uses a professional, CFO-centric design system:

| Token | Tailwind Class | Usage |
|-------|---------------|-------|
| Primary | `slate-900` | Headings, primary text, nav |
| Accent | `indigo-600` | Buttons, links, active states |
| Success | `emerald-500` | Savings indicators, success |
| Danger | `red-500` | Errors, destructive actions |
| Background | `white`/`slate-50` | Page and card backgrounds |
| Border | `slate-200` | Card borders, dividers |
| Muted | `slate-500` | Secondary labels, captions |

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run linter
npm run lint

# Run tests
npm test

# Build for production
npm run build
```

## Project Structure

```
src/
  components/       # Reusable UI components
    common/         # Shared components (Shell, etc.)
    mapping/        # Mapping-specific components
    audit/          # Audit-specific components
  pages/            # Top-level page components
  hooks/            # Custom React hooks
  lib/              # Utilities and API client
  types/            # TypeScript type definitions
  test/             # Test setup and utilities
```

## API Communication

The UI communicates with a local FastAPI backend via the `ApiClient` class in `src/lib/apiClient.ts`. The backend binds to `127.0.0.1` only for security.

Configure the API port via environment variables:

```bash
cp .env.example .env
# Edit VITE_API_PORT if needed (default: 8000)
```

## Code Style

- TypeScript strict mode (no `.js`/`.jsx` files)
- Named exports only (no default exports)
- Functional components with hooks
- Import order: React → third-party → internal (`@/...`) → relative
- Use Tailwind utilities directly (no custom CSS)
- lucide-react for all icons

## Testing

Tests are located alongside source files with `.test.tsx` or `.test.ts` extensions.

```bash
# Run tests
npm test

# Run tests with UI
npm run test -- --ui

# Run tests with coverage
npm run test -- --coverage
```

## Build Output

Production builds are output to `../src/cecil/ui_dist/` for bundling with the PyInstaller binary.
