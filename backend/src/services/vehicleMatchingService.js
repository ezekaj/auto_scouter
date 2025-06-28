const geolib = require('geolib');

class VehicleMatchingService {
  constructor() {
    // Default location for Gruppo Auto Uno (Napoli)
    this.defaultLocation = {
      latitude: 40.8518,
      longitude: 14.2681,
      name: 'Napoli, Italy'
    };
  }

  /**
   * Calculate match percentage between a vehicle and alert criteria
   * @param {Object} vehicle - Vehicle object
   * @param {Object} alertCriteria - Alert criteria object
   * @returns {Object} - Match result with percentage and details
   */
  calculateMatch(vehicle, alertCriteria) {
    const matchDetails = {
      make: this.matchMake(vehicle.make, alertCriteria.make),
      model: this.matchModel(vehicle.model, alertCriteria.model),
      year: this.matchYear(vehicle.year, alertCriteria.yearMin, alertCriteria.yearMax),
      price: this.matchPrice(vehicle.price, alertCriteria.priceMin, alertCriteria.priceMax),
      mileage: this.matchMileage(vehicle.mileage, alertCriteria.maxMileage),
      location: this.matchLocation(vehicle.location, alertCriteria.location, alertCriteria.radiusKm),
      fuelType: this.matchFuelType(vehicle.fuelType, alertCriteria.fuelType),
      transmission: this.matchTransmission(vehicle.transmission, alertCriteria.transmission),
      bodyType: this.matchBodyType(vehicle.bodyType, alertCriteria.bodyType)
    };

    // Calculate weighted percentage
    const weights = {
      make: 20,      // Most important
      model: 15,     // Very important
      price: 20,     // Most important
      year: 10,      // Important
      mileage: 10,   // Important
      location: 10,  // Important
      fuelType: 5,   // Moderate
      transmission: 5, // Moderate
      bodyType: 5    // Moderate
    };

    let totalScore = 0;
    let totalWeight = 0;

    Object.keys(matchDetails).forEach(criterion => {
      const match = matchDetails[criterion];
      if (match.applicable) {
        totalScore += match.score * weights[criterion];
        totalWeight += weights[criterion];
      }
    });

    const matchPercentage = totalWeight > 0 ? Math.round((totalScore / totalWeight) * 100) : 0;

    return {
      matchPercentage,
      matchDetails,
      isMatch: matchPercentage >= 70, // 70% threshold for notifications
      vehicle,
      alertCriteria
    };
  }

  matchMake(vehicleMake, criterionMake) {
    if (!criterionMake || criterionMake === 'any') {
      return { score: 1, applicable: false, reason: 'No make preference specified' };
    }

    if (!vehicleMake) {
      return { score: 0, applicable: true, reason: 'Vehicle make unknown' };
    }

    const normalizedVehicleMake = vehicleMake.toLowerCase().trim();
    const normalizedCriterionMake = criterionMake.toLowerCase().trim();

    if (normalizedVehicleMake === normalizedCriterionMake) {
      return { score: 1, applicable: true, reason: 'Exact make match' };
    }

    // Check for partial matches (e.g., "Mercedes" vs "Mercedes-Benz")
    if (normalizedVehicleMake.includes(normalizedCriterionMake) || 
        normalizedCriterionMake.includes(normalizedVehicleMake)) {
      return { score: 0.9, applicable: true, reason: 'Partial make match' };
    }

    return { score: 0, applicable: true, reason: 'Make does not match' };
  }

  matchModel(vehicleModel, criterionModel) {
    if (!criterionModel || criterionModel === 'any') {
      return { score: 1, applicable: false, reason: 'No model preference specified' };
    }

    if (!vehicleModel) {
      return { score: 0.5, applicable: true, reason: 'Vehicle model unknown' };
    }

    const normalizedVehicleModel = vehicleModel.toLowerCase().trim();
    const normalizedCriterionModel = criterionModel.toLowerCase().trim();

    if (normalizedVehicleModel === normalizedCriterionModel) {
      return { score: 1, applicable: true, reason: 'Exact model match' };
    }

    // Check for partial matches
    if (normalizedVehicleModel.includes(normalizedCriterionModel) || 
        normalizedCriterionModel.includes(normalizedVehicleModel)) {
      return { score: 0.8, applicable: true, reason: 'Partial model match' };
    }

    return { score: 0, applicable: true, reason: 'Model does not match' };
  }

  matchYear(vehicleYear, minYear, maxYear) {
    if (!minYear && !maxYear) {
      return { score: 1, applicable: false, reason: 'No year preference specified' };
    }

    if (!vehicleYear) {
      return { score: 0.5, applicable: true, reason: 'Vehicle year unknown' };
    }

    const min = minYear || 1900;
    const max = maxYear || new Date().getFullYear() + 1;

    if (vehicleYear >= min && vehicleYear <= max) {
      // Give higher score for newer cars within range
      const rangeSize = max - min;
      const yearPosition = vehicleYear - min;
      const score = rangeSize > 0 ? 0.7 + (yearPosition / rangeSize) * 0.3 : 1;
      return { score, applicable: true, reason: `Year ${vehicleYear} within range ${min}-${max}` };
    }

    // Partial score for close misses
    const distance = Math.min(Math.abs(vehicleYear - min), Math.abs(vehicleYear - max));
    if (distance <= 2) {
      return { score: 0.3, applicable: true, reason: `Year ${vehicleYear} close to range ${min}-${max}` };
    }

    return { score: 0, applicable: true, reason: `Year ${vehicleYear} outside range ${min}-${max}` };
  }

  matchPrice(vehiclePrice, minPrice, maxPrice) {
    if (!minPrice && !maxPrice) {
      return { score: 1, applicable: false, reason: 'No price preference specified' };
    }

    if (!vehiclePrice) {
      return { score: 0.5, applicable: true, reason: 'Vehicle price unknown' };
    }

    const min = minPrice || 0;
    const max = maxPrice || Infinity;

    if (vehiclePrice >= min && vehiclePrice <= max) {
      // Give higher score for prices closer to the lower end of the range
      const rangeSize = max - min;
      if (rangeSize > 0) {
        const pricePosition = vehiclePrice - min;
        const score = 1 - (pricePosition / rangeSize) * 0.3; // Lower prices get higher scores
        return { score: Math.max(0.7, score), applicable: true, reason: `Price €${vehiclePrice} within range €${min}-€${max}` };
      }
      return { score: 1, applicable: true, reason: `Price €${vehiclePrice} matches exactly` };
    }

    // Partial score for close misses (within 10% of range)
    const tolerance = Math.max((max - min) * 0.1, 1000);
    if (vehiclePrice < min && (min - vehiclePrice) <= tolerance) {
      return { score: 0.4, applicable: true, reason: `Price €${vehiclePrice} slightly below range` };
    }
    if (vehiclePrice > max && (vehiclePrice - max) <= tolerance) {
      return { score: 0.2, applicable: true, reason: `Price €${vehiclePrice} slightly above range` };
    }

    return { score: 0, applicable: true, reason: `Price €${vehiclePrice} outside range €${min}-€${max}` };
  }

  matchMileage(vehicleMileage, maxMileage) {
    if (!maxMileage) {
      return { score: 1, applicable: false, reason: 'No mileage preference specified' };
    }

    if (!vehicleMileage) {
      return { score: 0.5, applicable: true, reason: 'Vehicle mileage unknown' };
    }

    if (vehicleMileage <= maxMileage) {
      // Give higher score for lower mileage
      const score = maxMileage > 0 ? 1 - (vehicleMileage / maxMileage) * 0.3 : 1;
      return { score: Math.max(0.7, score), applicable: true, reason: `Mileage ${vehicleMileage}km within limit ${maxMileage}km` };
    }

    // Partial score for close misses (within 20% of limit)
    const tolerance = maxMileage * 0.2;
    if ((vehicleMileage - maxMileage) <= tolerance) {
      return { score: 0.3, applicable: true, reason: `Mileage ${vehicleMileage}km slightly above limit` };
    }

    return { score: 0, applicable: true, reason: `Mileage ${vehicleMileage}km exceeds limit ${maxMileage}km` };
  }

  matchLocation(vehicleLocation, criterionLocation, radiusKm) {
    if (!criterionLocation || !radiusKm) {
      return { score: 1, applicable: false, reason: 'No location preference specified' };
    }

    // For Gruppo Auto Uno, all vehicles are in Napoli area
    // This is a simplified implementation - in a real system you'd geocode locations
    const vehicleCoords = this.defaultLocation;
    const criterionCoords = this.geocodeLocation(criterionLocation);

    if (!criterionCoords) {
      return { score: 0.8, applicable: true, reason: 'Could not determine criterion location' };
    }

    const distance = geolib.getDistance(vehicleCoords, criterionCoords) / 1000; // Convert to km

    if (distance <= radiusKm) {
      const score = radiusKm > 0 ? 1 - (distance / radiusKm) * 0.3 : 1;
      return { score: Math.max(0.7, score), applicable: true, reason: `Distance ${distance}km within radius ${radiusKm}km` };
    }

    // Partial score for close misses
    const tolerance = radiusKm * 0.5;
    if ((distance - radiusKm) <= tolerance) {
      return { score: 0.4, applicable: true, reason: `Distance ${distance}km slightly outside radius` };
    }

    return { score: 0, applicable: true, reason: `Distance ${distance}km exceeds radius ${radiusKm}km` };
  }

  matchFuelType(vehicleFuelType, criterionFuelType) {
    if (!criterionFuelType || criterionFuelType === 'any') {
      return { score: 1, applicable: false, reason: 'No fuel type preference specified' };
    }

    if (!vehicleFuelType) {
      return { score: 0.5, applicable: true, reason: 'Vehicle fuel type unknown' };
    }

    const normalizedVehicleFuel = vehicleFuelType.toLowerCase().trim();
    const normalizedCriterionFuel = criterionFuelType.toLowerCase().trim();

    if (normalizedVehicleFuel === normalizedCriterionFuel) {
      return { score: 1, applicable: true, reason: 'Exact fuel type match' };
    }

    // Check for related fuel types
    const fuelGroups = {
      'gasoline': ['benzina', 'petrol', 'gas'],
      'diesel': ['diesel', 'gasolio'],
      'electric': ['electric', 'elettrico'],
      'hybrid': ['hybrid', 'ibrido']
    };

    for (const [group, variants] of Object.entries(fuelGroups)) {
      if (variants.includes(normalizedVehicleFuel) && variants.includes(normalizedCriterionFuel)) {
        return { score: 1, applicable: true, reason: 'Fuel type group match' };
      }
    }

    return { score: 0, applicable: true, reason: 'Fuel type does not match' };
  }

  matchTransmission(vehicleTransmission, criterionTransmission) {
    if (!criterionTransmission || criterionTransmission === 'any') {
      return { score: 1, applicable: false, reason: 'No transmission preference specified' };
    }

    if (!vehicleTransmission) {
      return { score: 0.7, applicable: true, reason: 'Vehicle transmission unknown' };
    }

    const normalizedVehicleTransmission = vehicleTransmission.toLowerCase().trim();
    const normalizedCriterionTransmission = criterionTransmission.toLowerCase().trim();

    if (normalizedVehicleTransmission === normalizedCriterionTransmission) {
      return { score: 1, applicable: true, reason: 'Exact transmission match' };
    }

    // Check for related transmission types
    const autoTypes = ['automatic', 'automatico', 'auto', 'dsg', 'cvt', 'eat'];
    const manualTypes = ['manual', 'manuale', 'stick'];

    const vehicleIsAuto = autoTypes.some(type => normalizedVehicleTransmission.includes(type));
    const criterionIsAuto = autoTypes.some(type => normalizedCriterionTransmission.includes(type));
    const vehicleIsManual = manualTypes.some(type => normalizedVehicleTransmission.includes(type));
    const criterionIsManual = manualTypes.some(type => normalizedCriterionTransmission.includes(type));

    if ((vehicleIsAuto && criterionIsAuto) || (vehicleIsManual && criterionIsManual)) {
      return { score: 1, applicable: true, reason: 'Transmission type match' };
    }

    return { score: 0, applicable: true, reason: 'Transmission does not match' };
  }

  matchBodyType(vehicleBodyType, criterionBodyType) {
    if (!criterionBodyType || criterionBodyType === 'any') {
      return { score: 1, applicable: false, reason: 'No body type preference specified' };
    }

    if (!vehicleBodyType) {
      return { score: 0.7, applicable: true, reason: 'Vehicle body type unknown' };
    }

    const normalizedVehicleBody = vehicleBodyType.toLowerCase().trim();
    const normalizedCriterionBody = criterionBodyType.toLowerCase().trim();

    if (normalizedVehicleBody === normalizedCriterionBody) {
      return { score: 1, applicable: true, reason: 'Exact body type match' };
    }

    // Check for related body types
    const bodyGroups = {
      'suv': ['suv', 'crossover', 'off-road'],
      'sedan': ['sedan', 'saloon', 'berlina'],
      'hatchback': ['hatchback', 'hatch', '3-door', '5-door'],
      'wagon': ['wagon', 'estate', 'station wagon', 'touring'],
      'coupe': ['coupe', 'coupé', '2-door'],
      'convertible': ['convertible', 'cabrio', 'cabriolet', 'roadster']
    };

    for (const [group, variants] of Object.entries(bodyGroups)) {
      if (variants.includes(normalizedVehicleBody) && variants.includes(normalizedCriterionBody)) {
        return { score: 1, applicable: true, reason: 'Body type group match' };
      }
    }

    return { score: 0, applicable: true, reason: 'Body type does not match' };
  }

  geocodeLocation(location) {
    // Simplified geocoding - in a real system you'd use a geocoding service
    const knownLocations = {
      'napoli': { latitude: 40.8518, longitude: 14.2681 },
      'naples': { latitude: 40.8518, longitude: 14.2681 },
      'roma': { latitude: 41.9028, longitude: 12.4964 },
      'rome': { latitude: 41.9028, longitude: 12.4964 },
      'milano': { latitude: 45.4642, longitude: 9.1900 },
      'milan': { latitude: 45.4642, longitude: 9.1900 },
      'torino': { latitude: 45.0703, longitude: 7.6869 },
      'turin': { latitude: 45.0703, longitude: 7.6869 },
      'firenze': { latitude: 43.7696, longitude: 11.2558 },
      'florence': { latitude: 43.7696, longitude: 11.2558 }
    };

    const normalizedLocation = location.toLowerCase().trim();
    return knownLocations[normalizedLocation] || null;
  }

  /**
   * Check multiple vehicles against an alert and return matches
   * @param {Array} vehicles - Array of vehicle objects
   * @param {Object} alertCriteria - Alert criteria object
   * @returns {Array} - Array of match results for vehicles that meet the threshold
   */
  findMatches(vehicles, alertCriteria) {
    return vehicles
      .map(vehicle => this.calculateMatch(vehicle, alertCriteria))
      .filter(match => match.isMatch)
      .sort((a, b) => b.matchPercentage - a.matchPercentage);
  }
}

module.exports = VehicleMatchingService;
