# Vehicle Scout Mobile App - Quick Reference

## 🚀 Quick Build Commands

### Android Debug APK
```bash
cd frontend
npm run build
npx cap sync android
cd android
./gradlew assembleDebug
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

### Android Release APK
```bash
cd frontend
npm run build
npx cap sync android
cd android
./gradlew assembleRelease
# APK: android/app/build/outputs/apk/release/app-release.apk
```

### iOS Build
```bash
cd frontend
npm run build
npx cap sync ios
npx cap open ios
# Build in Xcode
```

## 🔧 Environment Setup (One-time)

### Java 17 JDK
```bash
# Ubuntu/Debian
sudo apt install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# macOS
brew install openjdk@17
export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home
```

### Android SDK
```bash
# Download and setup
mkdir -p ~/android-sdk/cmdline-tools
cd ~/android-sdk/cmdline-tools
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-11076708_latest.zip
mv cmdline-tools latest

# Environment
export ANDROID_HOME=~/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

# Install components
sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

# Configure project
cd frontend/android
echo "sdk.dir=$ANDROID_HOME" > local.properties
```

## 📱 NPM Scripts

```bash
npm run cap:sync      # Sync web assets to native platforms
npm run cap:build     # Build web assets and sync
npm run android:build # Build Android APK
npm run android:run   # Build and run on connected device
```

## 🔐 Release Signing (Android)

### Generate Keystore (one-time)
```bash
keytool -genkey -v -keystore vehicle-scout.keystore -alias vehicle-scout -keyalg RSA -keysize 2048 -validity 10000
```

### Configure build.gradle
Add to `android/app/build.gradle`:
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
        }
    }
}
```

## 🧪 Testing Commands

```bash
# Install APK on device
adb install android/app/build/outputs/apk/debug/app-debug.apk

# View logs
adb logcat

# List devices
adb devices

# Live reload development
npm run dev
npx cap run android --livereload --external
```

## 🚨 Troubleshooting

### Build Fails
```bash
cd android
./gradlew clean
./gradlew assembleDebug
```

### License Issues
```bash
sdkmanager --licenses
```

### Java Issues
```bash
java -version
echo $JAVA_HOME
```

## 📂 Important File Locations

- **Debug APK**: `android/app/build/outputs/apk/debug/app-debug.apk`
- **Release APK**: `android/app/build/outputs/apk/release/app-release.apk`
- **Capacitor Config**: `capacitor.config.ts`
- **Android Config**: `android/app/build.gradle`
- **Local Properties**: `android/local.properties`

## 🎯 Current Build Status

✅ **Android Debug APK Successfully Built**
- Location: `frontend/android/app/build/outputs/apk/debug/app-debug.apk`
- Size: ~4MB
- Ready for testing and distribution

## 📋 Next Steps

1. **Test the APK** on Android devices
2. **Generate release keystore** for production builds
3. **Configure signing** for release APKs
4. **Add iOS platform** if needed
5. **Set up distribution** (Play Store, direct APK, etc.)

## 🔗 Full Documentation

- See `MOBILE_APP_GUIDE.md` for complete instructions
- See `README.md` for general project information
- See Capacitor docs: https://capacitorjs.com/docs
