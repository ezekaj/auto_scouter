# Authentication System Documentation

## Overview

Vehicle Scout implements a comprehensive JWT-based authentication system that secures all user-specific features and API endpoints. This document provides detailed information about the authentication flow, implementation, and usage.

## Architecture

### Frontend Authentication Components

#### 1. Authentication Service (`frontend/src/services/authService.ts`)
- Handles all authentication-related API calls
- Manages JWT token storage in localStorage
- Provides login, register, logout, and user data retrieval functions

#### 2. Authentication Context (`frontend/src/contexts/AuthContext.tsx`)
- React context for global authentication state management
- Provides authentication state and functions to all components
- Handles automatic token validation and user session management

#### 3. Authentication Forms
- **LoginForm** (`frontend/src/components/auth/LoginForm.tsx`): User login interface
- **RegisterForm** (`frontend/src/components/auth/RegisterForm.tsx`): User registration interface
- Both include form validation, error handling, and loading states

#### 4. Protected Routes (`frontend/src/components/auth/ProtectedRoute.tsx`)
- Wrapper component that requires authentication for access
- Automatically redirects unauthenticated users to login page
- Preserves intended destination for post-login redirect

### Backend Authentication System

#### 1. JWT Token Management
- **Library**: `python-jose[cryptography]` for JWT handling
- **Algorithm**: HS256 for token signing
- **Expiration**: 24 hours (configurable via environment variables)
- **Secret Key**: Configurable via `JWT_SECRET_KEY` environment variable

#### 2. Authentication Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication (returns JWT token)
- `GET /auth/me` - Get current user information (protected)

#### 3. Protected Endpoint Middleware
- All user-specific endpoints require valid JWT tokens
- Automatic token validation and user context injection
- Standardized error responses for authentication failures

## Authentication Flow

### 1. User Registration
```
User → Registration Form → POST /auth/register → User Created → Auto-login
```

### 2. User Login
```
User → Login Form → POST /auth/login → JWT Token → localStorage → API Headers
```

### 3. Protected API Calls
```
Frontend → API Request + Bearer Token → Backend Validation → Response
```

### 4. Token Expiration Handling
```
Expired Token → 401 Response → Auto-logout → Redirect to Login
```

## Implementation Details

### Frontend Token Management

#### Token Storage
```typescript
// Store token after successful login
localStorage.setItem('auth_token', token);

// Retrieve token for API calls
const token = localStorage.getItem('auth_token');
```

#### API Interceptor
```typescript
// Automatic token injection in API requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

#### Error Handling
```typescript
// Automatic logout on 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth data and redirect to login
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Backend Token Validation

#### JWT Token Creation
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

#### Token Validation Dependency
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user
```

## Protected Endpoints

### Alert Management
- `GET /api/v1/alerts/` - Retrieve user alerts
- `POST /api/v1/alerts/` - Create new alert
- `PUT /api/v1/alerts/{id}` - Update existing alert
- `DELETE /api/v1/alerts/{id}` - Delete alert
- `POST /api/v1/alerts/{id}/test` - Test alert criteria
- `POST /api/v1/alerts/{id}/toggle` - Toggle alert active status

### Notification Management
- `GET /api/v1/notifications/` - Retrieve user notifications
- `POST /api/v1/notifications/{id}/read` - Mark notification as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

### User Management
- `GET /auth/me` - Get current user profile
- `PUT /auth/me` - Update user profile

## Security Considerations

### Token Security
- JWT tokens are signed with a secret key
- Tokens include expiration timestamps
- No sensitive data is stored in tokens (only user identifier)

### Frontend Security
- Tokens stored in localStorage (consider httpOnly cookies for enhanced security)
- Automatic token cleanup on logout
- Protected routes prevent unauthorized access

### Backend Security
- All user-specific endpoints require authentication
- User context is validated on every request
- Standardized error responses prevent information leakage

## Error Handling

### Common Authentication Errors

#### 401 Unauthorized
- **Cause**: Missing, invalid, or expired JWT token
- **Frontend Response**: Automatic logout and redirect to login
- **User Action**: Re-authenticate

#### 403 Forbidden
- **Cause**: Valid token but insufficient permissions
- **Frontend Response**: Error message display
- **User Action**: Contact administrator

#### 422 Validation Error
- **Cause**: Invalid login credentials or registration data
- **Frontend Response**: Form validation errors
- **User Action**: Correct input and retry

## Testing Authentication

### Manual Testing
1. Register a new user account
2. Login with valid credentials
3. Access protected features (alerts, notifications)
4. Verify token expiration handling
5. Test logout functionality

### API Testing with curl
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Login user
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# Access protected endpoint
curl -X GET http://localhost:8000/api/v1/alerts/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### Common Issues

#### "Not authenticated" errors
- **Solution**: Ensure JWT token is included in Authorization header
- **Check**: Token format should be `Bearer <token>`

#### Token expiration
- **Solution**: Re-login to obtain new token
- **Prevention**: Implement token refresh mechanism

#### CORS issues with authentication
- **Solution**: Ensure backend CORS settings allow Authorization headers
- **Check**: Frontend and backend are running on expected ports

#### localStorage not persisting
- **Solution**: Check browser settings for localStorage support
- **Alternative**: Consider using sessionStorage or cookies

## Future Enhancements

### Planned Authentication Features
- [ ] Token refresh mechanism
- [ ] OAuth integration (Google, GitHub, etc.)
- [ ] Two-factor authentication (2FA)
- [ ] Role-based access control (RBAC)
- [ ] Session management and concurrent login limits
- [ ] Password reset functionality
- [ ] Account verification via email

### Security Improvements
- [ ] HttpOnly cookies for token storage
- [ ] CSRF protection
- [ ] Rate limiting for authentication endpoints
- [ ] Account lockout after failed attempts
- [ ] Audit logging for authentication events
