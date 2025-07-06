# 🔥 Firebase Push Notifications Setup

**Configure Firebase Cloud Messaging for Vehicle Scout mobile app**

## 📋 **Prerequisites**

1. **Firebase Project:** Create at https://console.firebase.google.com
2. **Android App:** Register your app in Firebase console
3. **Service Account:** Download service account key for backend

---

## 🔧 **Step 1: Firebase Console Setup**

### **Create Firebase Project**
1. Go to https://console.firebase.google.com
2. Click "Create a project"
3. Name: `vehicle-scout-notifications`
4. Enable Google Analytics (optional)

### **Add Android App**
1. Click "Add app" → Android
2. **Package name:** `com.vehiclescout.app` (or your package name)
3. **App nickname:** `Vehicle Scout`
4. Download `google-services.json`

### **Enable Cloud Messaging**
1. Go to Project Settings → Cloud Messaging
2. Note your **Server Key** and **Sender ID**
3. Enable Cloud Messaging API

---

## 📱 **Step 2: Mobile App Configuration**

### **Add Firebase to Ionic/Capacitor App**

1. **Install Firebase SDK**
   ```bash
   cd frontend
   npm install firebase @capacitor/push-notifications
   ```

2. **Add google-services.json**
   ```bash
   # Copy downloaded file to android app
   cp google-services.json android/app/
   ```

3. **Configure Capacitor**
   ```typescript
   // capacitor.config.ts
   import { CapacitorConfig } from '@capacitor/cli';

   const config: CapacitorConfig = {
     appId: 'com.vehiclescout.app',
     appName: 'Vehicle Scout',
     webDir: 'dist',
     bundledWebRuntime: false,
     plugins: {
       PushNotifications: {
         presentationOptions: ["badge", "sound", "alert"]
       }
     }
   };

   export default config;
   ```

4. **Initialize Firebase**
   ```typescript
   // src/services/firebase.ts
   import { initializeApp } from 'firebase/app';
   import { getMessaging, getToken, onMessage } from 'firebase/messaging';

   const firebaseConfig = {
     apiKey: "your-api-key",
     authDomain: "vehicle-scout-notifications.firebaseapp.com",
     projectId: "vehicle-scout-notifications",
     storageBucket: "vehicle-scout-notifications.appspot.com",
     messagingSenderId: "your-sender-id",
     appId: "your-app-id"
   };

   const app = initializeApp(firebaseConfig);
   const messaging = getMessaging(app);

   export { messaging, getToken, onMessage };
   ```

5. **Request Permission & Get Token**
   ```typescript
   // src/services/notifications.ts
   import { PushNotifications } from '@capacitor/push-notifications';
   import { messaging, getToken } from './firebase';

   export class NotificationService {
     async requestPermission(): Promise<string | null> {
       try {
         // Request permission
         const permission = await PushNotifications.requestPermissions();
         
         if (permission.receive === 'granted') {
           // Get FCM token
           const token = await getToken(messaging, {
             vapidKey: 'your-vapid-key' // Get from Firebase console
           });
           
           console.log('FCM Token:', token);
           return token;
         }
         
         return null;
       } catch (error) {
         console.error('Permission request failed:', error);
         return null;
       }
     }

     async registerDevice(token: string) {
       try {
         const response = await fetch('/api/v1/push/register-device', {
           method: 'POST',
           headers: {
             'Content-Type': 'application/json',
             'Authorization': `Bearer ${localStorage.getItem('token')}`
           },
           body: JSON.stringify({
             device_token: token,
             platform: 'android'
           })
         });

         const result = await response.json();
         console.log('Device registered:', result);
         return result.success;
       } catch (error) {
         console.error('Device registration failed:', error);
         return false;
       }
     }
   }
   ```

6. **Handle Incoming Notifications**
   ```typescript
   // src/services/notifications.ts (continued)
   export class NotificationService {
     setupNotificationHandlers() {
       // Handle notifications when app is in foreground
       PushNotifications.addListener('pushNotificationReceived', (notification) => {
         console.log('Notification received:', notification);
         
         // Show in-app notification or update UI
         this.showInAppNotification(notification);
       });

       // Handle notification tap
       PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
         console.log('Notification action:', action);
         
         const data = action.notification.data;
         if (data.type === 'vehicle_match') {
           // Navigate to vehicle details
           this.navigateToVehicle(data.vehicle_id);
         }
       });
     }

     private showInAppNotification(notification: any) {
       // Show toast or modal with notification content
       // Implementation depends on your UI framework
     }

     private navigateToVehicle(vehicleId: string) {
       // Navigate to vehicle details page
       // Implementation depends on your routing setup
     }
   }
   ```

---

## 🔧 **Step 3: Backend Configuration**

### **Service Account Setup**
1. **Download Service Account Key**
   - Go to Firebase Console → Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save as `firebase-service-account.json`

2. **Configure Railway Environment**
   ```bash
   # Set environment variables in Railway
   railway variables set FIREBASE_PROJECT_ID=vehicle-scout-notifications
   railway variables set FIREBASE_CREDENTIALS_PATH=/app/firebase-service-account.json
   ```

3. **Upload Service Account Key**
   ```bash
   # For Railway deployment, add the key file to your repository
   # (Make sure it's in .gitignore for security)
   cp firebase-service-account.json backend/
   ```

### **Test Backend Integration**
```bash
# Test Firebase service
curl -X GET "https://your-app.railway.app/api/v1/push/firebase-config"

# Test notification sending
curl -X POST "https://your-app.railway.app/api/v1/push/test-notification" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"device_token": "YOUR_FCM_TOKEN"}'
```

---

## 🧪 **Step 4: Testing Push Notifications**

### **Test Flow**
1. **Register Device**
   - Launch mobile app
   - Grant notification permission
   - Verify device token is sent to backend

2. **Send Test Notification**
   - Use backend API to send test notification
   - Verify notification appears on device

3. **Test Vehicle Match Notifications**
   - Create alert in mobile app
   - Trigger scraping that finds matching vehicle
   - Verify push notification is sent

### **Testing Commands**
```bash
# Test Firebase status
curl https://your-app.railway.app/api/v1/push/health

# Send test notification
curl -X POST https://your-app.railway.app/api/v1/push/test-notification \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"device_token": "YOUR_FCM_TOKEN", "message": "Test from cloud!"}'
```

---

## 🔒 **Step 5: Security Configuration**

### **Firebase Security Rules**
```javascript
// Firestore Security Rules (if using Firestore)
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### **API Key Restrictions**
1. Go to Google Cloud Console
2. Navigate to APIs & Services → Credentials
3. Restrict API key to specific apps/domains

### **Environment Variables**
```bash
# Production environment variables
FIREBASE_PROJECT_ID=vehicle-scout-notifications
FIREBASE_CREDENTIALS_PATH=/app/firebase-service-account.json
ENVIRONMENT=production
```

---

## 📊 **Step 6: Monitoring & Analytics**

### **Firebase Analytics**
- Monitor notification delivery rates
- Track user engagement with notifications
- Analyze notification performance

### **Backend Monitoring**
```bash
# Check notification status
curl https://your-app.railway.app/api/v1/push/status

# Monitor Railway logs
railway logs --filter="notification"
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Notifications Not Received**
1. Check device token is valid
2. Verify Firebase project configuration
3. Check app is not in battery optimization
4. Verify notification permissions granted

#### **Backend Errors**
1. Check Firebase service account key
2. Verify environment variables set
3. Check Railway logs for errors
4. Test Firebase connectivity

#### **Token Registration Fails**
1. Verify API endpoint is correct
2. Check authentication token
3. Verify device token format
4. Check network connectivity

### **Debug Commands**
```bash
# Check Firebase service status
curl https://your-app.railway.app/api/v1/push/firebase-config

# Test notification service
curl https://your-app.railway.app/api/v1/push/health

# Check Railway logs
railway logs --tail
```

---

## ✅ **Success Criteria**

- [ ] ✅ Firebase project created and configured
- [ ] ✅ Mobile app receives FCM tokens
- [ ] ✅ Device tokens registered with backend
- [ ] ✅ Test notifications work
- [ ] ✅ Vehicle match notifications sent automatically
- [ ] ✅ Notifications work when app is closed
- [ ] ✅ Backend deployed with Firebase integration

---

**🎉 RESULT: Complete push notification system working 24/7 in the cloud!**
