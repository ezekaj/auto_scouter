# Development Guide

## Getting Started

### Prerequisites
- Node.js (v16+)
- Python (v3.8+)
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ezekaj/auto_scouter.git
   cd auto_scouter
   ```

2. **Install dependencies**
   ```bash
   # Install root dependencies (optional, for development scripts)
   npm install
   
   # Install frontend dependencies
   cd frontend
   npm install
   cd ..
   
   # Install backend dependencies
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

3. **Setup database**
   ```bash
   cd backend
   python create_db.py
   cd ..
   ```

## Development Workflow

### Running the Application

**Option 1: Manual (Recommended for development)**
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Option 2: Using development scripts**
```bash
# PowerShell (Windows)
.\start-dev.ps1

# Or using npm (if concurrently is installed)
npm run dev
```

### Project Structure

```
auto_scouter/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Utility functions
│   │   ├── types/          # TypeScript type definitions
│   │   └── assets/         # Static assets
│   ├── public/             # Public assets
│   └── package.json
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API route handlers
│   │   ├── schemas/        # Pydantic schemas
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   └── create_db.py
└── docs/                   # Documentation
```

## Code Style Guidelines

### Frontend (React/TypeScript)
- Use functional components with hooks
- Follow React best practices
- Use TypeScript for type safety
- Use CSS modules or styled-components for styling
- Follow naming conventions:
  - Components: PascalCase
  - Files: kebab-case
  - Variables: camelCase

### Backend (Python/FastAPI)
- Follow PEP 8 style guide
- Use type hints
- Follow FastAPI best practices
- Use Pydantic for data validation
- Follow naming conventions:
  - Files: snake_case
  - Classes: PascalCase
  - Functions/variables: snake_case

## Database Management

### Creating Tables
```bash
cd backend
python create_db.py
```

### Database Migrations (Future)
When Alembic is fully configured:
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Testing

### Frontend Testing
```bash
cd frontend
npm test
```

### Backend Testing
```bash
cd backend
pytest
```

## Building for Production

### Frontend Build
```bash
cd frontend
npm run build
```

### Backend Deployment
The backend can be deployed using:
- Docker
- Heroku
- AWS Lambda
- Traditional server with Gunicorn

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=sqlite:///./auto_scouter.db
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=["http://localhost:3000"]
```

### Frontend (.env.local)
```env
VITE_API_URL=http://localhost:8000
```

## Common Issues

### Backend won't start
- Check Python version (3.8+)
- Ensure all dependencies are installed
- Check if port 8000 is available

### Frontend won't start
- Check Node.js version (16+)
- Clear node_modules and reinstall
- Check if port 3000 is available

### Database issues
- Delete the SQLite file and recreate
- Check file permissions
- Ensure create_db.py runs without errors

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

### Commit Message Format
- `Add: new feature`
- `Edit: existing functionality`
- `Fix: bug fix`
- `Remove: deleted code`
