// Local types for validation (no longer using auth types)
export interface PasswordValidation {
  minLength: boolean
  hasUppercase: boolean
  hasLowercase: boolean
  hasNumber: boolean
  hasSpecialChar: boolean
  isValid: boolean
}

export interface ValidationErrors {
  email?: string
  password?: string
  confirmPassword?: string
  firstName?: string
  lastName?: string
  currentPassword?: string
  newPassword?: string
  general?: string
}

export interface RegisterData {
  email: string
  password: string
  confirmPassword: string
  firstName: string
  lastName: string
  acceptTerms: boolean
  subscribeNewsletter: boolean
}

export interface LoginCredentials {
  email: string
  password: string
  rememberMe: boolean
}

// Email validation
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Password validation
export const validatePassword = (password: string): PasswordValidation => {
  const validation: PasswordValidation = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSpecialChar: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
    isValid: false
  }

  validation.isValid = Object.values(validation).slice(0, -1).every(Boolean)
  return validation
}

// Get password strength score (0-4)
export const getPasswordStrength = (password: string): number => {
  const validation = validatePassword(password)
  let score = 0
  
  if (validation.minLength) score++
  if (validation.hasUppercase) score++
  if (validation.hasLowercase) score++
  if (validation.hasNumber) score++
  if (validation.hasSpecialChar) score++
  
  return Math.min(score, 4)
}

// Get password strength label
export const getPasswordStrengthLabel = (score: number): string => {
  switch (score) {
    case 0:
    case 1:
      return 'Very Weak'
    case 2:
      return 'Weak'
    case 3:
      return 'Good'
    case 4:
      return 'Strong'
    default:
      return 'Very Weak'
  }
}

// Get password strength color
export const getPasswordStrengthColor = (score: number): string => {
  switch (score) {
    case 0:
    case 1:
      return 'text-red-500'
    case 2:
      return 'text-orange-500'
    case 3:
      return 'text-yellow-500'
    case 4:
      return 'text-green-500'
    default:
      return 'text-red-500'
  }
}

// Form validation functions
export const validateLoginForm = (credentials: LoginCredentials): ValidationErrors => {
  const errors: ValidationErrors = {}

  // Email validation
  if (!credentials.email) {
    errors.email = 'Email is required'
  } else if (!isValidEmail(credentials.email)) {
    errors.email = 'Please enter a valid email address'
  }

  // Password validation
  if (!credentials.password) {
    errors.password = 'Password is required'
  } else if (credentials.password.length < 6) {
    errors.password = 'Password must be at least 6 characters'
  }

  return errors
}

export const validateRegisterForm = (data: RegisterData): ValidationErrors => {
  const errors: ValidationErrors = {}

  // Email validation
  if (!data.email) {
    errors.email = 'Email is required'
  } else if (!isValidEmail(data.email)) {
    errors.email = 'Please enter a valid email address'
  }

  // Password validation
  if (!data.password) {
    errors.password = 'Password is required'
  } else {
    const passwordValidation = validatePassword(data.password)
    if (!passwordValidation.isValid) {
      const requirements = []
      if (!passwordValidation.minLength) requirements.push('at least 8 characters')
      if (!passwordValidation.hasUppercase) requirements.push('one uppercase letter')
      if (!passwordValidation.hasLowercase) requirements.push('one lowercase letter')
      if (!passwordValidation.hasNumber) requirements.push('one number')
      if (!passwordValidation.hasSpecialChar) requirements.push('one special character')
      
      errors.password = `Password must contain ${requirements.join(', ')}`
    }
  }

  // Confirm password validation
  if (!data.confirmPassword) {
    errors.confirmPassword = 'Please confirm your password'
  } else if (data.password !== data.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
  }

  // First name validation (optional but if provided, should be valid)
  if (data.firstName && data.firstName.trim().length < 2) {
    errors.firstName = 'First name must be at least 2 characters'
  }

  // Last name validation (optional but if provided, should be valid)
  if (data.lastName && data.lastName.trim().length < 2) {
    errors.lastName = 'Last name must be at least 2 characters'
  }

  // Terms acceptance validation
  if (!data.acceptTerms) {
    errors.general = 'You must accept the terms and conditions'
  }

  return errors
}

export const validateForgotPasswordForm = (email: string): ValidationErrors => {
  const errors: ValidationErrors = {}

  if (!email) {
    errors.email = 'Email is required'
  } else if (!isValidEmail(email)) {
    errors.email = 'Please enter a valid email address'
  }

  return errors
}

export const validateResetPasswordForm = (password: string, confirmPassword: string): ValidationErrors => {
  const errors: ValidationErrors = {}

  // Password validation
  if (!password) {
    errors.password = 'Password is required'
  } else {
    const passwordValidation = validatePassword(password)
    if (!passwordValidation.isValid) {
      const requirements = []
      if (!passwordValidation.minLength) requirements.push('at least 8 characters')
      if (!passwordValidation.hasUppercase) requirements.push('one uppercase letter')
      if (!passwordValidation.hasLowercase) requirements.push('one lowercase letter')
      if (!passwordValidation.hasNumber) requirements.push('one number')
      if (!passwordValidation.hasSpecialChar) requirements.push('one special character')
      
      errors.password = `Password must contain ${requirements.join(', ')}`
    }
  }

  // Confirm password validation
  if (!confirmPassword) {
    errors.confirmPassword = 'Please confirm your password'
  } else if (password !== confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
  }

  return errors
}

export const validateChangePasswordForm = (currentPassword: string, newPassword: string, confirmPassword: string): ValidationErrors => {
  const errors: ValidationErrors = {}

  // Current password validation
  if (!currentPassword) {
    errors.currentPassword = 'Current password is required'
  }

  // New password validation
  if (!newPassword) {
    errors.newPassword = 'New password is required'
  } else if (newPassword === currentPassword) {
    errors.newPassword = 'New password must be different from current password'
  } else {
    const passwordValidation = validatePassword(newPassword)
    if (!passwordValidation.isValid) {
      const requirements = []
      if (!passwordValidation.minLength) requirements.push('at least 8 characters')
      if (!passwordValidation.hasUppercase) requirements.push('one uppercase letter')
      if (!passwordValidation.hasLowercase) requirements.push('one lowercase letter')
      if (!passwordValidation.hasNumber) requirements.push('one number')
      if (!passwordValidation.hasSpecialChar) requirements.push('one special character')
      
      errors.newPassword = `Password must contain ${requirements.join(', ')}`
    }
  }

  // Confirm password validation
  if (!confirmPassword) {
    errors.confirmPassword = 'Please confirm your new password'
  } else if (newPassword !== confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
  }

  return errors
}

// Sanitize user input
export const sanitizeInput = (input: string): string => {
  return input.trim().replace(/[<>]/g, '')
}

// Check if form has errors
export const hasValidationErrors = (errors: ValidationErrors): boolean => {
  return Object.keys(errors).length > 0
}
