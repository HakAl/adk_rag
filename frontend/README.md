# VIBE Agent Frontend

React + TypeScript frontend for the VIBE Agent API.

## Setup

```bash
cd frontend
npm install
```

## Running

Make sure the backend API is running on `http://localhost:8000`, then:

```bash
npm start
```

The app will open at `http://localhost:3000`

## Testing

```bash
npm test
```

## Features

- Health check integration with backend API
- TypeScript for type safety
- Error handling
- Loading states
- Comprehensive test coverage

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── App.tsx          # Main component
│   ├── App.css          # Styles
│   ├── App.test.tsx     # Tests
│   ├── index.tsx        # Entry point
│   ├── index.css        # Global styles
│   └── setupTests.ts    # Test configuration
├── package.json
└── tsconfig.json
```