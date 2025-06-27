# Auto Scouter

An automated scouting system for robotics competitions, built with React (frontend) and FastAPI (backend).

## 🚀 Features

- **Scout Management**: Create and manage scout profiles
- **Team Tracking**: Maintain comprehensive team databases
- **Match Recording**: Record and analyze match performance data
- **Real-time Data**: Live updates and synchronization
- **Modern UI**: Responsive React interface with Vite for fast development
- **RESTful API**: FastAPI backend with automatic documentation

## 🏗️ Project Structure

```
auto_scouter/
├── frontend/          # React + Vite frontend
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── core/      # Configuration
│   │   ├── models/    # Database models
│   │   ├── routers/   # API endpoints
│   │   └── schemas/   # Pydantic schemas
│   ├── requirements.txt
│   └── create_db.py
├── docs/              # Documentation
└── README.md
```

## 🛠️ Technology Stack

### Frontend
- **React 18** - Modern UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **CSS3** - Styling

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Development database (PostgreSQL ready)
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server

## 📋 Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**
- **pip**

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ezekaj/auto_scouter.git
cd auto_scouter
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create database tables
python create_db.py

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: http://localhost:3000

## 🔧 Development

### Running Both Services

For development, you'll need to run both the frontend and backend simultaneously:

1. **Terminal 1** (Backend):
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Terminal 2** (Frontend):
   ```bash
   cd frontend
   npm run dev
   ```

### API Documentation

When the backend is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=sqlite:///./auto_scouter.db
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## 📊 Database Schema

### Core Models

- **Scout**: Scout profiles and authentication
- **Team**: Team information and details
- **Match**: Match data and results
- **ScoutReport**: Individual scouting reports linking scouts, teams, and matches

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add: amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Format

- `Add: new feature or functionality`
- `Edit: modifications to existing code`
- `Fix: bug fixes`
- `Remove: deleted code or features`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [API documentation](http://localhost:8000/docs) when backend is running
2. Review the console logs for error messages
3. Create an issue on GitHub

## 🔮 Future Enhancements

- [ ] User authentication and authorization
- [ ] Real-time match updates via WebSocket
- [ ] Advanced analytics and reporting
- [ ] Mobile app support
- [ ] PostgreSQL production database
- [ ] Docker containerization
- [ ] CI/CD pipeline
