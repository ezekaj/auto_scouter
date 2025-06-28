const express = require('express');
const cors = require('cors');
const http = require('http');
const path = require('path');
const AlertSystem = require('./src/services/alertSystem');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 8000;

// Initialize the alert system
const alertSystem = new AlertSystem();

// Middleware
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002', 'http://localhost:3003'],
  credentials: true
}));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Health check endpoint
app.get('/api/v1/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    system: alertSystem.getSystemStats()
  });
});

// Vehicle endpoints
app.get('/api/v1/cars', (req, res) => {
  try {
    const criteria = {
      make: req.query.make,
      model: req.query.model,
      priceMin: req.query.priceMin ? parseInt(req.query.priceMin) : undefined,
      priceMax: req.query.priceMax ? parseInt(req.query.priceMax) : undefined,
      yearMin: req.query.yearMin ? parseInt(req.query.yearMin) : undefined,
      yearMax: req.query.yearMax ? parseInt(req.query.yearMax) : undefined,
      maxMileage: req.query.maxMileage ? parseInt(req.query.maxMileage) : undefined,
      fuelType: req.query.fuelType,
      transmission: req.query.transmission,
      bodyType: req.query.bodyType,
      sort: req.query.sort || 'newest'
    };

    const limit = parseInt(req.query.limit) || 20;
    const page = parseInt(req.query.page) || 1;
    const offset = (page - 1) * limit;

    const result = alertSystem.searchVehicles(criteria, limit, offset);
    
    res.json(result);
  } catch (error) {
    console.error('Error searching vehicles:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/v1/cars/:id', (req, res) => {
  try {
    const vehicle = alertSystem.getVehicle(req.params.id);
    
    if (!vehicle) {
      return res.status(404).json({ error: 'Vehicle not found' });
    }
    
    res.json(vehicle);
  } catch (error) {
    console.error('Error getting vehicle:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Alert endpoints
app.get('/api/v1/alerts', (req, res) => {
  try {
    const alerts = alertSystem.getAllAlerts();
    res.json(alerts);
  } catch (error) {
    console.error('Error getting alerts:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/v1/alerts', (req, res) => {
  try {
    const alertData = req.body;
    
    // Validate required fields
    if (!alertData.name) {
      return res.status(400).json({ error: 'Alert name is required' });
    }
    
    const alert = alertSystem.createAlert(alertData);
    res.status(201).json(alert);
  } catch (error) {
    console.error('Error creating alert:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/api/v1/alerts/:id', (req, res) => {
  try {
    const alert = alertSystem.getAlert(req.params.id);
    
    if (!alert) {
      return res.status(404).json({ error: 'Alert not found' });
    }
    
    res.json(alert);
  } catch (error) {
    console.error('Error getting alert:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.put('/api/v1/alerts/:id', (req, res) => {
  try {
    const alert = alertSystem.updateAlert(req.params.id, req.body);
    res.json(alert);
  } catch (error) {
    if (error.message === 'Alert not found') {
      return res.status(404).json({ error: 'Alert not found' });
    }
    console.error('Error updating alert:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.delete('/api/v1/alerts/:id', (req, res) => {
  try {
    alertSystem.deleteAlert(req.params.id);
    res.status(204).send();
  } catch (error) {
    if (error.message === 'Alert not found') {
      return res.status(404).json({ error: 'Alert not found' });
    }
    console.error('Error deleting alert:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Check alert matches
app.post('/api/v1/alerts/:id/check', (req, res) => {
  try {
    const alert = alertSystem.getAlert(req.params.id);
    
    if (!alert) {
      return res.status(404).json({ error: 'Alert not found' });
    }
    
    const matches = alertSystem.checkAlertAgainstExistingVehicles(alert);
    res.json({
      alert,
      matches: matches.slice(0, 10), // Return top 10 matches
      totalMatches: matches.length
    });
  } catch (error) {
    console.error('Error checking alert:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Notification endpoints
app.get('/api/v1/notifications', (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 50;
    const offset = parseInt(req.query.offset) || 0;
    const type = req.query.type;
    
    let notifications;
    if (type) {
      notifications = alertSystem.notificationService.getNotificationsByType(type, limit);
    } else {
      notifications = alertSystem.notificationService.getNotifications(limit, offset);
    }
    
    const unreadCount = alertSystem.notificationService.getUnreadCount();
    
    res.json({
      notifications,
      unreadCount,
      total: alertSystem.notificationService.notifications.length
    });
  } catch (error) {
    console.error('Error getting notifications:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.put('/api/v1/notifications/:id/read', (req, res) => {
  try {
    alertSystem.notificationService.markNotificationAsRead(req.params.id);
    res.status(204).send();
  } catch (error) {
    console.error('Error marking notification as read:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.put('/api/v1/notifications/read-all', (req, res) => {
  try {
    alertSystem.notificationService.markAllNotificationsAsRead();
    res.status(204).send();
  } catch (error) {
    console.error('Error marking all notifications as read:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.delete('/api/v1/notifications/:id', (req, res) => {
  try {
    const deleted = alertSystem.notificationService.deleteNotification(req.params.id);
    if (deleted) {
      res.status(204).send();
    } else {
      res.status(404).json({ error: 'Notification not found' });
    }
  } catch (error) {
    console.error('Error deleting notification:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// System stats endpoint
app.get('/api/v1/stats', (req, res) => {
  try {
    const stats = alertSystem.getSystemStats();
    res.json(stats);
  } catch (error) {
    console.error('Error getting stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Manual scrape trigger (for testing)
app.post('/api/v1/scrape', (req, res) => {
  try {
    alertSystem.scraper.performScrape();
    res.json({ message: 'Scrape initiated' });
  } catch (error) {
    console.error('Error initiating scrape:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Start the server
async function startServer() {
  try {
    // Start the alert system
    await alertSystem.start(server);
    
    // Start the HTTP server
    server.listen(PORT, () => {
      console.log(`🚀 Petrit's Vehicle Scout Backend running on port ${PORT}`);
      console.log(`📊 Health check: http://localhost:${PORT}/api/v1/health`);
      console.log(`🔌 WebSocket: ws://localhost:${PORT}/ws`);
      console.log(`📱 API Base: http://localhost:${PORT}/api/v1`);
    });
    
    // Handle graceful shutdown
    process.on('SIGTERM', gracefulShutdown);
    process.on('SIGINT', gracefulShutdown);
    
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

function gracefulShutdown(signal) {
  console.log(`\nReceived ${signal}. Starting graceful shutdown...`);
  
  alertSystem.stop();
  
  server.close(() => {
    console.log('Server closed. Goodbye!');
    process.exit(0);
  });
  
  // Force exit after 10 seconds
  setTimeout(() => {
    console.log('Force exit after timeout');
    process.exit(1);
  }, 10000);
}

// Start the server
startServer();
