/**
 * Formatting utilities for the Auto Scouter application
 */

/**
 * Format price with currency symbol and proper number formatting
 */
export function formatPrice(price: number | string, currency: string = '€'): string {
  const numPrice = typeof price === 'string' ? parseFloat(price) : price;
  
  if (isNaN(numPrice)) {
    return 'N/A';
  }
  
  // Format with thousands separator
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numPrice);
  
  return `${formatted} ${currency}`;
}

/**
 * Format distance/mileage
 */
export function formatMileage(mileage: number | string, unit: string = 'km'): string {
  const numMileage = typeof mileage === 'string' ? parseFloat(mileage) : mileage;
  
  if (isNaN(numMileage)) {
    return 'N/A';
  }
  
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numMileage);
  
  return `${formatted} ${unit}`;
}

/**
 * Format year
 */
export function formatYear(year: number | string): string {
  const numYear = typeof year === 'string' ? parseInt(year) : year;
  
  if (isNaN(numYear) || numYear < 1900 || numYear > new Date().getFullYear() + 1) {
    return 'N/A';
  }
  
  return numYear.toString();
}

/**
 * Format engine size
 */
export function formatEngineSize(size: number | string): string {
  const numSize = typeof size === 'string' ? parseFloat(size) : size;
  
  if (isNaN(numSize)) {
    return 'N/A';
  }
  
  // Convert to liters if it's in cc
  if (numSize > 100) {
    return `${(numSize / 1000).toFixed(1)}L`;
  }
  
  return `${numSize.toFixed(1)}L`;
}

/**
 * Format power (HP/kW)
 */
export function formatPower(power: number | string, unit: string = 'HP'): string {
  const numPower = typeof power === 'string' ? parseFloat(power) : power;
  
  if (isNaN(numPower)) {
    return 'N/A';
  }
  
  return `${Math.round(numPower)} ${unit}`;
}

/**
 * Format fuel consumption
 */
export function formatFuelConsumption(consumption: number | string): string {
  const numConsumption = typeof consumption === 'string' ? parseFloat(consumption) : consumption;
  
  if (isNaN(numConsumption)) {
    return 'N/A';
  }
  
  return `${numConsumption.toFixed(1)} L/100km`;
}

/**
 * Format percentage
 */
export function formatPercentage(value: number | string, decimals: number = 1): string {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numValue)) {
    return 'N/A';
  }
  
  return `${numValue.toFixed(decimals)}%`;
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format duration in milliseconds to human readable format
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Capitalize first letter of each word
 */
export function capitalizeWords(text: string): string {
  return text.replace(/\w\S*/g, (txt) => 
    txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
  );
}

/**
 * Format phone number
 */
export function formatPhoneNumber(phone: string): string {
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Format based on length
  if (cleaned.length === 10) {
    return cleaned.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
  } else if (cleaned.length === 11) {
    return cleaned.replace(/(\d{1})(\d{3})(\d{3})(\d{4})/, '$1 ($2) $3-$4');
  }
  
  return phone; // Return original if can't format
}
