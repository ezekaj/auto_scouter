# Vehicle Scout Mobile App Guide

This guide provides comprehensive instructions for building, testing, and distributing the Vehicle Scout mobile app using Capacitor.

## 📱 Overview

The Vehicle Scout mobile app is built using Capacitor, which allows the React web application to run as a native mobile app on Android and iOS devices. The app includes all web features plus native mobile optimizations.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Java 17 JDK (for Android)
- Android SDK (for Android)
- macOS with Xcode (for iOS)

### Build Android APK (Debug)
```bash
# From the frontend directory
npm install
npm run build
npx cap sync android
cd android
./gradlew assembleDebug
```

The APK will be located at: `android/app/build/outputs/apk/debug/app-debug.apk`

## 🔧 Android Development Setup

### 1. Install Java 17 JDK
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openjdk-17-jdk

# macOS
brew install openjdk@17

# Verify installation
java -version
```

### 2. Set JAVA_HOME
```bash
# Linux
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# macOS
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
```

### 3. Install Android SDK
```bash
# Create Android SDK directory
mkdir -p ~/android-sdk/cmdline-tools
cd ~/android-sdk/cmdline-tools

# Download command line tools
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-11076708_latest.zip
mv cmdline-tools latest

# Set environment variables
export ANDROID_HOME=~/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export ANDROID_HOME=~/android-sdk' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools' >> ~/.bashrc
```

### 4. Install SDK Components
```bash
# Accept all licenses
sdkmanager --licenses

# Install required components
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

# Verify installation
sdkmanager --list_installed
```

### 5. Configure local.properties
```bash
# In the android directory, create local.properties
cd frontend/android
echo "sdk.dir=$ANDROID_HOME" > local.properties
```

## 📦 Building APKs

### Debug APK (for testing)
```bash
cd frontend
npm run build
npx cap sync android
cd android
./gradlew assembleDebug
```

### Release APK (for production)

1. **Generate Keystore** (one-time setup):
```bash
keytool -genkey -v -keystore vehicle-scout.keystore -alias vehicle-scout -keyalg RSA -keysize 2048 -validity 10000
```

2. **Configure Signing** in `android/app/build.gradle`:
```gradle
android {
    signingConfigs {
        release {
            storeFile file('../vehicle-scout.keystore')
            storePassword 'your-store-password'
            keyAlias 'vehicle-scout'
            keyPassword 'your-key-password'
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

3. **Build Release APK**:
```bash
cd android
./gradlew assembleRelease
```

## 🍎 iOS Development

### Prerequisites
- macOS with Xcode installed
- Apple Developer Account (for distribution)

### Setup
```bash
# Add iOS platform (if not already added)
npx cap add ios

# Sync web assets
npx cap sync ios

# Open in Xcode
npx cap open ios
```

### Building in Xcode
1. Open the project in Xcode
2. Select your development team
3. Configure bundle identifier
4. Build and run on simulator or device

## 🛠️ Development Workflow

### Available Scripts
```bash
# Build web assets and sync to native platforms
npm run cap:build

# Sync web assets only
npm run cap:sync

# Build Android APK
npm run android:build

# Build and run on connected Android device
npm run android:run

# Open Android project in Android Studio
npx cap open android

# Open iOS project in Xcode
npx cap open ios
```

### Live Reload Development
```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Run with live reload
npx cap run android --livereload --external
```

## 📱 Testing

### Android Testing
```bash
# Install APK on connected device
adb install android/app/build/outputs/apk/debug/app-debug.apk

# View device logs
adb logcat

# List connected devices
adb devices
```

### iOS Testing
- Use Xcode simulator
- Deploy to physical device via Xcode
- Use TestFlight for beta testing

## 🚀 Distribution

### Android Distribution Options

1. **Direct APK Distribution**
   - Share the APK file directly
   - Users need to enable "Install from unknown sources"

2. **Google Play Store**
   - Create Google Play Console account
   - Upload signed APK or AAB
   - Follow Play Store guidelines

3. **Enterprise Distribution**
   - Use Mobile Device Management (MDM)
   - Internal app distribution

### iOS Distribution Options

1. **TestFlight** (Beta Testing)
   - Upload to App Store Connect
   - Invite beta testers

2. **App Store**
   - Submit for App Store review
   - Follow App Store guidelines

3. **Enterprise Distribution**
   - Requires Apple Developer Enterprise Program
   - Internal distribution only

## 🔧 Troubleshooting

### Common Android Issues

**Gradle Build Fails**
```bash
# Clean and rebuild
cd android
./gradlew clean
./gradlew assembleDebug
```

**SDK License Issues**
```bash
# Re-accept licenses
sdkmanager --licenses
```

**Java Version Issues**
```bash
# Check Java version
java -version
javac -version

# Ensure JAVA_HOME is set correctly
echo $JAVA_HOME
```

### Common iOS Issues

**Code Signing Issues**
- Ensure Apple Developer account is configured
- Check bundle identifier is unique
- Verify provisioning profiles

**Xcode Build Fails**
- Clean build folder (Product → Clean Build Folder)
- Update Xcode to latest version
- Check iOS deployment target

## 📋 Checklist

### Before Building
- [ ] Web app builds successfully (`npm run build`)
- [ ] All environment variables configured
- [ ] Java 17 JDK installed and JAVA_HOME set
- [ ] Android SDK installed and ANDROID_HOME set
- [ ] local.properties file created

### Before Release
- [ ] App tested on physical devices
- [ ] Release keystore generated and secured
- [ ] App signed with release keystore
- [ ] App icons and splash screens configured
- [ ] App permissions reviewed
- [ ] Privacy policy and terms of service ready

### Distribution
- [ ] APK/IPA tested on multiple devices
- [ ] Store listings prepared (if applicable)
- [ ] Screenshots and app descriptions ready
- [ ] Beta testing completed
- [ ] Release notes prepared

## 📞 Support

For mobile app development issues:
1. Check this guide for common solutions
2. Review Capacitor documentation: https://capacitorjs.com/docs
3. Check Android/iOS platform-specific documentation
4. Review build logs for specific error messages

## 🔗 Useful Links

- [Capacitor Documentation](https://capacitorjs.com/docs)
- [Android Developer Guide](https://developer.android.com/guide)
- [iOS Developer Guide](https://developer.apple.com/documentation/)
- [Google Play Console](https://play.google.com/console)
- [App Store Connect](https://appstoreconnect.apple.com/)
