import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { authService, LoginRequest, RegisterRequest, AuthState } from '@/services/authService'

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  })

  useEffect(() => {
    const initializeAuth = async () => {
      const token = authService.getToken()
      const user = authService.getUser()

      if (token && user) {
        setAuthState({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
        })

        // Try to refresh user data
        try {
          const refreshedUser = await authService.getCurrentUser()
          setAuthState(prev => ({
            ...prev,
            user: refreshedUser,
          }))
        } catch (error) {
          console.error('Failed to refresh user data:', error)
          // Token might be expired, logout
          authService.logout()
          setAuthState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      } else {
        setAuthState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        })
      }
    }

    initializeAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }))
      const loginData = await authService.login(credentials)
      
      setAuthState({
        user: loginData.user,
        token: loginData.token.access_token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }))
      throw error
    }
  }

  const register = async (userData: RegisterRequest) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }))
      const loginData = await authService.register(userData)
      
      setAuthState({
        user: loginData.user,
        token: loginData.token.access_token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }))
      throw error
    }
  }

  const logout = () => {
    authService.logout()
    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })
  }

  const refreshUser = async () => {
    try {
      const user = await authService.getCurrentUser()
      setAuthState(prev => ({ ...prev, user }))
    } catch (error) {
      console.error('Failed to refresh user:', error)
      logout()
    }
  }

  const value: AuthContextType = {
    ...authState,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
