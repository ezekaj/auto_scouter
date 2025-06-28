const VehicleScraper = require('./vehicleScraper');
const VehicleMatchingService = require('./vehicleMatchingService');
const NotificationService = require('./notificationService');
const { EventEmitter } = require('events');

class AlertSystem extends EventEmitter {
  constructor() {
    super();
    this.scraper = new VehicleScraper();
    this.matcher = new VehicleMatchingService();
    this.notificationService = new NotificationService();
    
    this.alerts = new Map(); // Store active alerts
    this.vehicles = new Map(); // Store known vehicles
    this.vehicleHistory = new Map(); // Track price changes
    
    this.isRunning = false;
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    // Handle new vehicles from scraper
    this.scraper.on('newVehicles', (newVehicles) => {
      this.handleNewVehicles(newVehicles);
    });

    // Handle all vehicles update
    this.scraper.on('allVehicles', (allVehicles) => {
      this.updateVehicleDatabase(allVehicles);
    });

    // Handle scraper errors
    this.scraper.on('error', (error) => {
      console.error('Scraper error:', error);
      this.notificationService.createSystemNotification(
        'Scraping Error',
        'There was an issue checking for new vehicles. Will retry automatically.',
        'error'
      );
    });
  }

  async start(server) {
    if (this.isRunning) {
      console.log('Alert system is already running');
      return;
    }

    console.log('Starting Petrit\'s Vehicle Alert System...');
    
    // Initialize WebSocket server
    this.notificationService.initializeWebSocket(server);
    
    // Start vehicle monitoring
    await this.scraper.startMonitoring();
    
    // Set up periodic cleanup
    this.setupPeriodicCleanup();
    
    this.isRunning = true;
    
    // Send startup notification
    this.notificationService.createSystemNotification(
      'Alert System Started',
      'Petrit\'s Vehicle Scout is now monitoring for new vehicles and matches.',
      'info'
    );
    
    console.log('Alert system started successfully');
    this.emit('started');
  }

  stop() {
    if (!this.isRunning) {
      console.log('Alert system is not running');
      return;
    }

    console.log('Stopping alert system...');
    
    this.scraper.stopMonitoring();
    
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    
    this.isRunning = false;
    
    console.log('Alert system stopped');
    this.emit('stopped');
  }

  // Alert Management
  createAlert(alertData) {
    const alert = {
      id: this.generateAlertId(),
      name: alertData.name,
      criteria: {
        make: alertData.make,
        model: alertData.model,
        yearMin: alertData.yearMin,
        yearMax: alertData.yearMax,
        priceMin: alertData.priceMin,
        priceMax: alertData.priceMax,
        maxMileage: alertData.maxMileage,
        location: alertData.location,
        radiusKm: alertData.radiusKm,
        fuelType: alertData.fuelType,
        transmission: alertData.transmission,
        bodyType: alertData.bodyType
      },
      isActive: true,
      createdAt: new Date().toISOString(),
      lastChecked: null,
      matchCount: 0,
      lastMatch: null
    };

    this.alerts.set(alert.id, alert);
    
    // Check existing vehicles against new alert
    this.checkAlertAgainstExistingVehicles(alert);
    
    console.log(`Created alert: ${alert.name}`);
    this.emit('alert_created', alert);
    
    return alert;
  }

  updateAlert(alertId, updateData) {
    const alert = this.alerts.get(alertId);
    if (!alert) {
      throw new Error('Alert not found');
    }

    // Update alert properties
    Object.assign(alert, updateData);
    alert.updatedAt = new Date().toISOString();
    
    // Re-check against existing vehicles if criteria changed
    if (updateData.criteria) {
      this.checkAlertAgainstExistingVehicles(alert);
    }
    
    console.log(`Updated alert: ${alert.name}`);
    this.emit('alert_updated', alert);
    
    return alert;
  }

  deleteAlert(alertId) {
    const alert = this.alerts.get(alertId);
    if (!alert) {
      throw new Error('Alert not found');
    }

    this.alerts.delete(alertId);
    
    console.log(`Deleted alert: ${alert.name}`);
    this.emit('alert_deleted', alert);
    
    return true;
  }

  getAlert(alertId) {
    return this.alerts.get(alertId);
  }

  getAllAlerts() {
    return Array.from(this.alerts.values());
  }

  getActiveAlerts() {
    return Array.from(this.alerts.values()).filter(alert => alert.isActive);
  }

  // Vehicle Processing
  handleNewVehicles(newVehicles) {
    console.log(`Processing ${newVehicles.length} new vehicles...`);
    
    const allMatches = [];
    const activeAlerts = this.getActiveAlerts();
    
    newVehicles.forEach(vehicle => {
      // Store vehicle
      this.vehicles.set(vehicle.id, vehicle);
      
      // Check against all active alerts
      activeAlerts.forEach(alert => {
        const match = this.matcher.calculateMatch(vehicle, alert.criteria);
        
        if (match.isMatch) {
          allMatches.push({ match, alert, vehicle });
          
          // Update alert stats
          alert.matchCount++;
          alert.lastMatch = new Date().toISOString();
          alert.lastChecked = new Date().toISOString();
          
          // Create notification
          this.notificationService.createVehicleMatchNotification(match, alert);
          
          console.log(`Match found: ${vehicle.make} ${vehicle.model} (${match.matchPercentage}%) for alert "${alert.name}"`);
        }
      });
    });

    // Create summary notification if there are new vehicles
    if (newVehicles.length > 0) {
      const topMatches = allMatches
        .sort((a, b) => b.match.matchPercentage - a.match.matchPercentage)
        .slice(0, 5);
      
      this.notificationService.createNewVehiclesNotification(
        newVehicles.length,
        topMatches.map(m => m.match)
      );
    }

    this.emit('new_vehicles_processed', {
      vehicleCount: newVehicles.length,
      matchCount: allMatches.length,
      matches: allMatches
    });
  }

  updateVehicleDatabase(allVehicles) {
    console.log(`Updating vehicle database with ${allVehicles.length} vehicles...`);
    
    // Check for price changes
    allVehicles.forEach(vehicle => {
      const existingVehicle = this.vehicles.get(vehicle.id);
      
      if (existingVehicle && existingVehicle.price && vehicle.price) {
        if (existingVehicle.price > vehicle.price) {
          // Price dropped
          this.handlePriceDrop(vehicle, existingVehicle.price, vehicle.price);
        }
      }
      
      // Update vehicle in database
      this.vehicles.set(vehicle.id, vehicle);
    });

    // Update last checked time for all alerts
    this.getActiveAlerts().forEach(alert => {
      alert.lastChecked = new Date().toISOString();
    });

    this.emit('vehicle_database_updated', {
      vehicleCount: allVehicles.length,
      totalVehicles: this.vehicles.size
    });
  }

  handlePriceDrop(vehicle, oldPrice, newPrice) {
    console.log(`Price drop detected: ${vehicle.make} ${vehicle.model} from €${oldPrice} to €${newPrice}`);
    
    // Check if any alerts would be interested in this price drop
    const activeAlerts = this.getActiveAlerts();
    
    activeAlerts.forEach(alert => {
      const match = this.matcher.calculateMatch(vehicle, alert.criteria);
      
      if (match.matchPercentage >= 50) { // Lower threshold for price drops
        this.notificationService.createPriceDropNotification(
          vehicle,
          oldPrice,
          newPrice,
          alert
        );
      }
    });
  }

  checkAlertAgainstExistingVehicles(alert) {
    console.log(`Checking alert "${alert.name}" against ${this.vehicles.size} existing vehicles...`);
    
    const vehicles = Array.from(this.vehicles.values());
    const matches = this.matcher.findMatches(vehicles, alert.criteria);
    
    if (matches.length > 0) {
      console.log(`Found ${matches.length} existing matches for alert "${alert.name}"`);
      
      // Create notifications for top matches
      matches.slice(0, 5).forEach(match => {
        this.notificationService.createVehicleMatchNotification(match, alert);
      });
      
      // Update alert stats
      alert.matchCount = matches.length;
      alert.lastMatch = new Date().toISOString();
    }
    
    alert.lastChecked = new Date().toISOString();
    
    return matches;
  }

  // Utility Methods
  setupPeriodicCleanup() {
    // Clean up old notifications every hour
    this.cleanupInterval = setInterval(() => {
      this.notificationService.clearOldNotifications(7); // Keep 7 days
    }, 60 * 60 * 1000); // 1 hour
  }

  generateAlertId() {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  getSystemStats() {
    return {
      isRunning: this.isRunning,
      alerts: {
        total: this.alerts.size,
        active: this.getActiveAlerts().length
      },
      vehicles: {
        total: this.vehicles.size,
        lastUpdate: this.scraper.lastScrapeTime
      },
      notifications: this.notificationService.getStats(),
      uptime: process.uptime()
    };
  }

  // API Methods for frontend
  searchVehicles(criteria, limit = 20, offset = 0) {
    const vehicles = Array.from(this.vehicles.values());
    
    let filteredVehicles = vehicles;
    
    // Apply filters
    if (criteria.make) {
      filteredVehicles = filteredVehicles.filter(v => 
        v.make && v.make.toLowerCase().includes(criteria.make.toLowerCase())
      );
    }
    
    if (criteria.model) {
      filteredVehicles = filteredVehicles.filter(v => 
        v.model && v.model.toLowerCase().includes(criteria.model.toLowerCase())
      );
    }
    
    if (criteria.priceMin) {
      filteredVehicles = filteredVehicles.filter(v => v.price >= criteria.priceMin);
    }
    
    if (criteria.priceMax) {
      filteredVehicles = filteredVehicles.filter(v => v.price <= criteria.priceMax);
    }
    
    if (criteria.yearMin) {
      filteredVehicles = filteredVehicles.filter(v => v.year >= criteria.yearMin);
    }
    
    if (criteria.yearMax) {
      filteredVehicles = filteredVehicles.filter(v => v.year <= criteria.yearMax);
    }
    
    if (criteria.maxMileage) {
      filteredVehicles = filteredVehicles.filter(v => v.mileage <= criteria.maxMileage);
    }
    
    if (criteria.fuelType && criteria.fuelType !== 'any') {
      filteredVehicles = filteredVehicles.filter(v => 
        v.fuelType && v.fuelType.toLowerCase() === criteria.fuelType.toLowerCase()
      );
    }
    
    if (criteria.transmission && criteria.transmission !== 'any') {
      filteredVehicles = filteredVehicles.filter(v => 
        v.transmission && v.transmission.toLowerCase() === criteria.transmission.toLowerCase()
      );
    }
    
    // Sort by date (newest first) or price
    if (criteria.sort === 'price_asc') {
      filteredVehicles.sort((a, b) => (a.price || 0) - (b.price || 0));
    } else if (criteria.sort === 'price_desc') {
      filteredVehicles.sort((a, b) => (b.price || 0) - (a.price || 0));
    } else if (criteria.sort === 'year_desc') {
      filteredVehicles.sort((a, b) => (b.year || 0) - (a.year || 0));
    } else if (criteria.sort === 'mileage_asc') {
      filteredVehicles.sort((a, b) => (a.mileage || 0) - (b.mileage || 0));
    } else {
      // Default: newest first
      filteredVehicles.sort((a, b) => new Date(b.scrapedAt) - new Date(a.scrapedAt));
    }
    
    const total = filteredVehicles.length;
    const results = filteredVehicles.slice(offset, offset + limit);
    
    return {
      vehicles: results,
      total,
      page: Math.floor(offset / limit) + 1,
      limit,
      hasMore: offset + limit < total
    };
  }

  getVehicle(vehicleId) {
    return this.vehicles.get(vehicleId);
  }
}

module.exports = AlertSystem;
