# Auto Scouter API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. This will be added in future versions.

## Endpoints

### Health Check
- **GET** `/` - Welcome message
- **GET** `/health` - Health check endpoint

### Scouts
- **GET** `/api/v1/scouts` - List all scouts
- **POST** `/api/v1/scouts` - Create a new scout
- **GET** `/api/v1/scouts/{scout_id}` - Get scout by ID
- **PUT** `/api/v1/scouts/{scout_id}` - Update scout
- **DELETE** `/api/v1/scouts/{scout_id}` - Delete scout

### Teams
- **GET** `/api/v1/teams` - List all teams
- **POST** `/api/v1/teams` - Create a new team
- **GET** `/api/v1/teams/{team_id}` - Get team by ID
- **GET** `/api/v1/teams/number/{team_number}` - Get team by number
- **PUT** `/api/v1/teams/{team_id}` - Update team
- **DELETE** `/api/v1/teams/{team_id}` - Delete team

### Matches
- **GET** `/api/v1/matches` - List all matches
- **POST** `/api/v1/matches` - Create a new match
- **GET** `/api/v1/matches/{match_id}` - Get match by ID
- **PUT** `/api/v1/matches/{match_id}` - Update match
- **DELETE** `/api/v1/matches/{match_id}` - Delete match

### Scout Reports
- **GET** `/api/v1/matches/{match_id}/reports` - Get reports for a match
- **POST** `/api/v1/matches/{match_id}/reports` - Create a scout report
- **GET** `/api/v1/matches/reports/{report_id}` - Get report by ID
- **PUT** `/api/v1/matches/reports/{report_id}` - Update report
- **DELETE** `/api/v1/matches/reports/{report_id}` - Delete report

## Data Models

### Scout
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Team
```json
{
  "id": 1,
  "team_number": 1234,
  "team_name": "The Robots",
  "school": "Example High School",
  "city": "Example City",
  "state": "EX",
  "country": "USA",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Match
```json
{
  "id": 1,
  "match_number": 1,
  "competition_level": "Qualification",
  "red_alliance": "1234,5678,9012",
  "blue_alliance": "3456,7890,1234",
  "red_score": 150,
  "blue_score": 120,
  "match_date": "2023-01-01T10:00:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Scout Report
```json
{
  "id": 1,
  "scout_id": 1,
  "team_id": 1,
  "match_id": 1,
  "auto_mobility": true,
  "auto_high_goals": 2,
  "auto_low_goals": 1,
  "teleop_high_goals": 8,
  "teleop_low_goals": 3,
  "climb_attempted": true,
  "climb_successful": true,
  "notes": "Great performance in autonomous",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

## Interactive Documentation

When the backend is running, you can access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
