const { EventEmitter } = require('events');
const WebSocket = require('ws');

class NotificationService extends EventEmitter {
  constructor() {
    super();
    this.notifications = [];
    this.wsClients = new Set();
    this.wsServer = null;
  }

  initializeWebSocket(server) {
    this.wsServer = new WebSocket.Server({ server, path: '/ws' });
    
    this.wsServer.on('connection', (ws, req) => {
      console.log('New WebSocket connection established');
      this.wsClients.add(ws);
      
      // Send existing notifications to new client
      ws.send(JSON.stringify({
        type: 'initial_notifications',
        data: this.getRecentNotifications(50)
      }));
      
      ws.on('close', () => {
        console.log('WebSocket connection closed');
        this.wsClients.delete(ws);
      });
      
      ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        this.wsClients.delete(ws);
      });
      
      // Handle incoming messages
      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          this.handleWebSocketMessage(ws, data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      });
    });
    
    console.log('WebSocket server initialized on /ws');
  }

  handleWebSocketMessage(ws, data) {
    switch (data.type) {
      case 'mark_read':
        this.markNotificationAsRead(data.notificationId);
        break;
      case 'mark_all_read':
        this.markAllNotificationsAsRead();
        break;
      case 'ping':
        ws.send(JSON.stringify({ type: 'pong' }));
        break;
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }

  broadcastToClients(message) {
    const messageStr = JSON.stringify(message);
    this.wsClients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        try {
          client.send(messageStr);
        } catch (error) {
          console.error('Error sending WebSocket message:', error);
          this.wsClients.delete(client);
        }
      }
    });
  }

  createVehicleMatchNotification(match, alert) {
    const notification = {
      id: this.generateNotificationId(),
      type: 'vehicle_match',
      title: `New Vehicle Match: ${match.vehicle.make} ${match.vehicle.model}`,
      message: `Found a ${match.matchPercentage}% match for your "${alert.name}" alert`,
      data: {
        vehicle: match.vehicle,
        matchPercentage: match.matchPercentage,
        matchDetails: match.matchDetails,
        alert: {
          id: alert.id,
          name: alert.name
        }
      },
      isRead: false,
      createdAt: new Date().toISOString(),
      priority: this.calculatePriority(match.matchPercentage),
      actions: [
        {
          type: 'view_vehicle',
          label: 'View Vehicle',
          url: match.vehicle.url
        },
        {
          type: 'view_alert',
          label: 'View Alert',
          url: `/alerts/${alert.id}`
        }
      ]
    };

    this.addNotification(notification);
    return notification;
  }

  createPriceDropNotification(vehicle, oldPrice, newPrice, alert) {
    const priceDrop = oldPrice - newPrice;
    const percentageDrop = Math.round((priceDrop / oldPrice) * 100);

    const notification = {
      id: this.generateNotificationId(),
      type: 'price_drop',
      title: `Price Drop Alert: ${vehicle.make} ${vehicle.model}`,
      message: `Price dropped by €${priceDrop} (${percentageDrop}%) - Now €${newPrice}`,
      data: {
        vehicle,
        oldPrice,
        newPrice,
        priceDrop,
        percentageDrop,
        alert: {
          id: alert.id,
          name: alert.name
        }
      },
      isRead: false,
      createdAt: new Date().toISOString(),
      priority: percentageDrop >= 10 ? 'high' : 'medium',
      actions: [
        {
          type: 'view_vehicle',
          label: 'View Vehicle',
          url: vehicle.url
        }
      ]
    };

    this.addNotification(notification);
    return notification;
  }

  createNewVehiclesNotification(vehicleCount, topMatches) {
    const notification = {
      id: this.generateNotificationId(),
      type: 'new_vehicles',
      title: `${vehicleCount} New Vehicles Available`,
      message: `Found ${vehicleCount} new vehicles, including ${topMatches.length} potential matches`,
      data: {
        vehicleCount,
        topMatches: topMatches.slice(0, 3), // Show top 3 matches
        hasMoreMatches: topMatches.length > 3
      },
      isRead: false,
      createdAt: new Date().toISOString(),
      priority: topMatches.length > 0 ? 'high' : 'low',
      actions: [
        {
          type: 'view_search',
          label: 'View New Vehicles',
          url: '/search?sort=newest'
        }
      ]
    };

    this.addNotification(notification);
    return notification;
  }

  createSystemNotification(title, message, type = 'info') {
    const notification = {
      id: this.generateNotificationId(),
      type: 'system',
      title,
      message,
      data: { systemType: type },
      isRead: false,
      createdAt: new Date().toISOString(),
      priority: type === 'error' ? 'high' : 'low',
      actions: []
    };

    this.addNotification(notification);
    return notification;
  }

  addNotification(notification) {
    this.notifications.unshift(notification);
    
    // Keep only last 1000 notifications
    if (this.notifications.length > 1000) {
      this.notifications = this.notifications.slice(0, 1000);
    }

    // Broadcast to WebSocket clients
    this.broadcastToClients({
      type: 'new_notification',
      data: notification
    });

    // Send browser notification if supported
    this.sendBrowserNotification(notification);

    // Emit event for other services
    this.emit('notification_created', notification);

    console.log(`Created notification: ${notification.title}`);
  }

  sendBrowserNotification(notification) {
    // This will be handled by the frontend
    this.broadcastToClients({
      type: 'browser_notification',
      data: {
        title: notification.title,
        message: notification.message,
        icon: '/icons/car-notification.png',
        tag: notification.type,
        data: notification.data
      }
    });
  }

  markNotificationAsRead(notificationId) {
    const notification = this.notifications.find(n => n.id === notificationId);
    if (notification && !notification.isRead) {
      notification.isRead = true;
      notification.readAt = new Date().toISOString();
      
      this.broadcastToClients({
        type: 'notification_read',
        data: { notificationId }
      });
      
      this.emit('notification_read', notification);
    }
  }

  markAllNotificationsAsRead() {
    const unreadCount = this.notifications.filter(n => !n.isRead).length;
    
    this.notifications.forEach(notification => {
      if (!notification.isRead) {
        notification.isRead = true;
        notification.readAt = new Date().toISOString();
      }
    });
    
    this.broadcastToClients({
      type: 'all_notifications_read',
      data: { count: unreadCount }
    });
    
    this.emit('all_notifications_read', unreadCount);
  }

  getNotifications(limit = 50, offset = 0) {
    return this.notifications.slice(offset, offset + limit);
  }

  getRecentNotifications(limit = 20) {
    return this.notifications.slice(0, limit);
  }

  getUnreadNotifications() {
    return this.notifications.filter(n => !n.isRead);
  }

  getUnreadCount() {
    return this.notifications.filter(n => !n.isRead).length;
  }

  getNotificationsByType(type, limit = 50) {
    return this.notifications
      .filter(n => n.type === type)
      .slice(0, limit);
  }

  deleteNotification(notificationId) {
    const index = this.notifications.findIndex(n => n.id === notificationId);
    if (index !== -1) {
      const notification = this.notifications.splice(index, 1)[0];
      
      this.broadcastToClients({
        type: 'notification_deleted',
        data: { notificationId }
      });
      
      this.emit('notification_deleted', notification);
      return true;
    }
    return false;
  }

  clearOldNotifications(daysOld = 30) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);
    
    const initialCount = this.notifications.length;
    this.notifications = this.notifications.filter(n => 
      new Date(n.createdAt) > cutoffDate
    );
    
    const deletedCount = initialCount - this.notifications.length;
    
    if (deletedCount > 0) {
      console.log(`Cleared ${deletedCount} old notifications`);
      this.broadcastToClients({
        type: 'notifications_cleared',
        data: { deletedCount }
      });
    }
    
    return deletedCount;
  }

  generateNotificationId() {
    return `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  calculatePriority(matchPercentage) {
    if (matchPercentage >= 90) return 'high';
    if (matchPercentage >= 80) return 'medium';
    return 'low';
  }

  getStats() {
    const total = this.notifications.length;
    const unread = this.getUnreadCount();
    const byType = {};
    const byPriority = {};

    this.notifications.forEach(n => {
      byType[n.type] = (byType[n.type] || 0) + 1;
      byPriority[n.priority] = (byPriority[n.priority] || 0) + 1;
    });

    return {
      total,
      unread,
      read: total - unread,
      byType,
      byPriority,
      connectedClients: this.wsClients.size
    };
  }
}

module.exports = NotificationService;
