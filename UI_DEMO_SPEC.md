# Prime Anonymizer - UI Demo Specification

## Project Overview

Build a modern, interactive web UI to demonstrate the Prime Anonymizer API's capabilities. The UI will provide visual before/after comparison of JSON anonymization, making PII detection and replacement immediately clear to users.

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **JSON Editor**: Monaco Editor (VSCode-style)
- **State Management**: React hooks (useState, useEffect)
- **HTTP Client**: fetch API

### Backend Integration
- Connects to existing FastAPI backend at `/anonymize` endpoint
- CORS enabled on FastAPI for local development
- Production: Next.js and FastAPI in same Docker network

## Core Features

### 1. Split-Pane JSON Editor
**Left Pane - Input**
- Monaco Editor with JSON syntax highlighting
- Validation indicator (green checkmark / red error)
- Line numbers
- Auto-formatting button
- Clear button

**Right Pane - Output**
- Monaco Editor (read-only)
- Highlighted differences from input
- Color-coded entity replacements
- Copy to clipboard button

### 2. Control Panel
**Location**: Top bar or sidebar

**Controls**:
- **Anonymize Button** (primary CTA - large, prominent)
- **Strategy Selector**: Dropdown with "Replace" (default) / "Hash"
- **Entity Type Filter**: Multi-select checkboxes
  - Select All / Deselect All
  - Individual toggles: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD, IBAN, US_SSN, LOCATION, DATE_TIME, IP_ADDRESS, URL
- **Example Templates Dropdown**: Pre-loaded sample JSON

### 3. Statistics Panel
**Location**: Bottom panel or right sidebar

**Display**:
- **Processing Time**: Response time in ms
- **PII Entities Found**: Badge-style counts by type
  - Color-coded badges (e.g., blue for PERSON, purple for EMAIL_ADDRESS)
  - Format: "PERSON: 3 | EMAIL: 2 | PHONE: 1"
- **Payload Size**: Request/response size in bytes/KB
- **Status Indicator**: Success (green) / Error (red) with message

### 4. Example Templates
Pre-loaded JSON examples for quick demonstration:

**Template 1: Customer Data**
```json
{
  "customer_id": "CUST-12345",
  "name": "Alice Johnson",
  "email": "alice.johnson@email.com",
  "phone": "+1-555-123-4567",
  "address": {
    "street": "123 Main Street",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "active": true
}
```

**Template 2: Employee Record**
```json
{
  "employee": {
    "id": 10234,
    "full_name": "Robert Smith",
    "ssn": "123-45-6789",
    "email": "robert.smith@company.com",
    "phone": "+1-555-987-6543",
    "hire_date": "2023-03-15",
    "salary": 85000,
    "department": "Engineering"
  },
  "emergency_contact": {
    "name": "Sarah Smith",
    "relationship": "Spouse",
    "phone": "+1-555-111-2222"
  }
}
```

**Template 3: Financial Transaction**
```json
{
  "transaction_id": "TXN-789012",
  "timestamp": "2024-10-08T14:23:45Z",
  "amount": 1250.00,
  "currency": "USD",
  "customer": {
    "name": "Emily Davis",
    "email": "emily.davis@example.com",
    "card_number": "4532-1234-5678-9010",
    "billing_address": "456 Oak Avenue, New York, NY 10001"
  },
  "merchant": "TechStore Inc",
  "status": "completed"
}
```

**Template 4: Medical Record**
```json
{
  "patient": {
    "mrn": "MRN-445566",
    "name": "Dr. Michael Chen",
    "date_of_birth": "1985-07-22",
    "ssn": "987-65-4321",
    "phone": "+1-555-444-3333",
    "email": "m.chen@health.net"
  },
  "visit": {
    "date": "2024-10-01",
    "facility": "City Hospital",
    "doctor": "Dr. Jessica Williams",
    "diagnosis": "Annual checkup",
    "notes": "Patient Michael Chen reported no issues. Dr. Jessica Williams approved all tests."
  }
}
```

**Template 5: Complex Nested Structure**
```json
{
  "company": "Acme Corporation",
  "contacts": [
    {
      "name": "John Doe",
      "role": "CEO",
      "email": "john.doe@acme.com",
      "phone": "+1-555-999-8888"
    },
    {
      "name": "Jane Smith",
      "role": "CTO",
      "email": "jane.smith@acme.com",
      "phone": "+1-555-777-6666"
    }
  ],
  "meeting_notes": [
    "John Doe and Jane Smith discussed Q4 strategy.",
    "Contact John Doe at john.doe@acme.com for follow-up."
  ],
  "metadata": {
    "created_by": "Alice Johnson",
    "created_at": "2024-10-08T09:00:00Z",
    "ip_address": "192.168.1.100",
    "session_id": 98765
  }
}
```

## UI/UX Design

### Layout Options

**Option A: Horizontal Split (Recommended)**
```
┌─────────────────────────────────────────────────────────┐
│  Prime Anonymizer                    [Example ▼] [Anonymize] │
├──────────────────┬──────────────────────────────────────┤
│                  │                                      │
│   INPUT JSON     │      OUTPUT JSON                     │
│                  │                                      │
│   Monaco         │      Monaco (read-only)              │
│   Editor         │      Editor                          │
│                  │                                      │
│   [Format]       │      [Copy]                          │
│   [Clear]        │                                      │
│                  │                                      │
├──────────────────┴──────────────────────────────────────┤
│  Controls: Strategy: [Replace ▼] Entities: [☑ All] [...] │
├──────────────────────────────────────────────────────────┤
│  Stats: ⏱️ 145ms | 📊 PERSON: 3 | EMAIL: 2 | PHONE: 1     │
└──────────────────────────────────────────────────────────┘
```

**Option B: Vertical Split**
```
┌─────────────────────────────────────────────────────────┐
│  Prime Anonymizer                                       │
│  [Example ▼] Strategy: [Replace ▼] Entities: [☑ All]    │
│  [Anonymize Button - Large]                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   INPUT JSON                                            │
│   Monaco Editor                                         │
│   [Format] [Clear]                                      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   OUTPUT JSON                                           │
│   Monaco Editor (read-only)                             │
│   [Copy]                                                │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Stats: ⏱️ 145ms | 📊 PERSON: 3 | EMAIL: 2 | PHONE: 1    │
└─────────────────────────────────────────────────────────┘
```

### Color Scheme

**Dark Theme (Primary)**
- Background: `#0a0a0a` (near black)
- Panel backgrounds: `#1a1a1a`
- Borders: `#2a2a2a`
- Text: `#e0e0e0`
- Accent: `#3b82f6` (blue)
- Success: `#10b981` (green)
- Error: `#ef4444` (red)

**Entity Color Coding**
- PERSON: `#3b82f6` (blue)
- EMAIL_ADDRESS: `#a855f7` (purple)
- PHONE_NUMBER: `#10b981` (green)
- CREDIT_CARD: `#f59e0b` (amber)
- IBAN: `#f59e0b` (amber)
- US_SSN: `#ef4444` (red)
- LOCATION: `#06b6d4` (cyan)
- DATE_TIME: `#8b5cf6` (violet)
- IP_ADDRESS: `#ec4899` (pink)
- URL: `#14b8a6` (teal)

### Visual Highlighting

**Diff Highlighting in Output**
- Changed values: subtle background glow in entity color (10% opacity)
- Hover tooltip: "Original: <original_value>"
- Animation: smooth fade-in when results appear

**Badges**
- Pill-shaped with entity color as background
- White text
- Small size (text-sm)
- Grouped horizontally with spacing

## API Integration

### Endpoint
```
POST /anonymize?strategy={replace|hash}&entities={PERSON,EMAIL,...}
Content-Type: application/json

Body: <any valid JSON>

Response: <anonymized JSON>
```

### Request Flow
1. User clicks "Anonymize"
2. Validate input JSON (client-side)
3. Show loading state (spinner on button)
4. POST to `/anonymize` with query params
5. Handle response:
   - Success: Display in output pane + stats
   - Error: Show error message in stats panel
6. Calculate and display processing time

### Error Handling
- **Invalid JSON**: Show error message below input editor
- **API Error 400**: Display error detail in stats panel
- **API Error 413**: "Payload too large (max 2 MiB)"
- **API Error 500**: "Server error - please try again"
- **Network Error**: "Cannot connect to API"

## Component Structure

```
app/
├── page.tsx                    # Main page (client component)
├── layout.tsx                  # Root layout
├── globals.css                 # Tailwind imports
└── components/
    ├── AnonymizerUI.tsx        # Main container component
    ├── JsonEditor.tsx          # Monaco editor wrapper
    ├── ControlPanel.tsx        # Strategy/entity controls
    ├── StatsPanel.tsx          # Statistics display
    ├── ExampleSelector.tsx     # Template dropdown
    └── ui/                     # shadcn/ui components
        ├── button.tsx
        ├── select.tsx
        ├── checkbox.tsx
        ├── badge.tsx
        └── card.tsx
```

## Implementation Steps

### Phase 1: Project Setup
1. Create Next.js project with TypeScript
   ```bash
   npx create-next-app@latest prime-anonymizer-ui --typescript --tailwind --app
   ```
2. Install dependencies:
   ```bash
   npm install @monaco-editor/react
   npm install lucide-react class-variance-authority clsx tailwind-merge
   ```
3. Initialize shadcn/ui:
   ```bash
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button select checkbox badge card
   ```

### Phase 2: Core Components
1. Create `JsonEditor.tsx` with Monaco integration
2. Create `AnonymizerUI.tsx` with split-pane layout
3. Implement API client function
4. Add loading/error states

### Phase 3: Controls & Templates
1. Build `ControlPanel.tsx` with strategy/entity selectors
2. Create `ExampleSelector.tsx` with pre-loaded templates
3. Implement template injection into input editor

### Phase 4: Statistics & Polish
1. Build `StatsPanel.tsx` with entity badges
2. Add diff highlighting in output editor
3. Implement animations and transitions
4. Add copy-to-clipboard functionality

### Phase 5: Integration & Testing
1. Configure CORS on FastAPI backend
2. Test all example templates
3. Test error scenarios
4. Optimize for performance (memoization, lazy loading)

### Phase 6: Deployment
1. Build Next.js app: `npm run build`
2. Option A: Serve via Node.js
3. Option B: Export static and serve via FastAPI
4. Update Dockerfile to include frontend
5. Update docker-compose.yml with frontend service

## Environment Configuration

### Development
```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production
```env
# .env.production
NEXT_PUBLIC_API_URL=https://prime.rnd.2bv.io
```

## FastAPI CORS Configuration

Add to `app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://prime-ui.rnd.2bv.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Docker Integration

### Option A: Separate Services
```yaml
# docker-compose.yml
services:
  backend:
    build: .
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
```

### Option B: Static Export via FastAPI
```python
# app/main.py
from fastapi.staticfiles import StaticFiles

# Serve Next.js static export
app.mount("/", StaticFiles(directory="frontend/out", html=True), name="ui")
```

## Performance Considerations

1. **Monaco Editor**: Lazy load with dynamic import
2. **JSON Validation**: Debounce validation (300ms)
3. **Large Payloads**: Stream processing for >500KB
4. **Diff Calculation**: Web Worker for large diffs
5. **Caching**: Cache example templates in memory

## Accessibility

- Keyboard navigation for all controls
- ARIA labels on interactive elements
- High contrast mode support
- Screen reader announcements for status changes
- Focus management in modal/dropdown interactions

## Future Enhancements (Optional)

1. **History**: Save last 5 anonymization requests
2. **Export**: Download anonymized JSON as file
3. **Compare Mode**: Toggle side-by-side vs overlay diff
4. **Batch Mode**: Upload multiple JSON files
5. **API Key Auth**: If backend adds authentication
6. **Dark/Light Theme Toggle**: User preference
7. **Audit Log Viewer**: Display recent anonymization stats from database
8. **Mobile Responsive**: Vertical layout for tablets/phones

## Success Criteria

✅ Professional, polished appearance
✅ Intuitive user experience (no instructions needed)
✅ Clear visual demonstration of anonymization
✅ Fast response times (<200ms for typical payloads)
✅ Handles errors gracefully
✅ Works in all modern browsers (Chrome, Firefox, Safari, Edge)
✅ Responsive design (desktop priority, mobile friendly)

## Deliverables

1. Complete Next.js application source code
2. README with setup instructions
3. Docker configuration for deployment
4. Environment configuration templates
5. User guide (optional markdown doc)

---

## Quick Start Commands

```bash
# Create Next.js project
npx create-next-app@latest prime-anonymizer-ui --typescript --tailwind --app

# Install dependencies
cd prime-anonymizer-ui
npm install @monaco-editor/react lucide-react

# Initialize shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button select checkbox badge card

# Run development server
npm run dev

# Build for production
npm run build

# Export static (optional)
npm run build && npm run export
```

---

**This specification provides a complete blueprint for building a professional, impressive demo UI for the Prime Anonymizer API.**
