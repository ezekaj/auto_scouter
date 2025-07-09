#!/usr/bin/env node

/**
 * APK Connection Test Script
 * Tests if the newly built APK can connect to the Render backend
 */

const https = require('https');
const http = require('http');

// Configuration - Update with your actual Render URL
const RENDER_BASE_URL = 'https://auto-scouter-backend.onrender.com';
const API_BASE_URL = `${RENDER_BASE_URL}/api/v1`;

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
        const protocol = url.startsWith('https:') ? https : http;
        const timeout = options.timeout || 10000;
        
        const req = protocol.get(url, { timeout }, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: jsonData
                    });
                } catch (e) {
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: data
                    });
                }
            });
        });
        
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });
        
        req.on('error', (err) => {
            reject(err);
        });
    });
}

async function testHealthEndpoint() {
    log('\n🏥 Testing Health Endpoint', 'blue');
    log('=' .repeat(40), 'blue');
    
    try {
        const response = await makeRequest(`${RENDER_BASE_URL}/health`);
        
        if (response.status === 200) {
            log('✅ Health endpoint accessible', 'green');
            log(`   Status: ${response.data.status || 'Unknown'}`, 'cyan');
            log(`   Environment: ${response.data.environment || 'Unknown'}`, 'cyan');
            log(`   Database: ${response.data.database || 'Unknown'}`, 'cyan');
            log(`   Version: ${response.data.version || 'Unknown'}`, 'cyan');
            
            if (response.data.features) {
                log(`   Features: ${response.data.features.join(', ')}`, 'cyan');
            }
            
            return true;
        } else {
            log(`❌ Health endpoint returned status: ${response.status}`, 'red');
            return false;
        }
    } catch (error) {
        log(`❌ Health endpoint failed: ${error.message}`, 'red');
        return false;
    }
}

async function testVehiclesEndpoint() {
    log('\n🚗 Testing Vehicles Endpoint', 'blue');
    log('=' .repeat(40), 'blue');
    
    try {
        const response = await makeRequest(`${API_BASE_URL}/automotive/vehicles/simple`);
        
        if (response.status === 200) {
            log('✅ Vehicles endpoint accessible', 'green');
            
            if (Array.isArray(response.data)) {
                log(`   Found ${response.data.length} vehicles`, 'cyan');
                
                if (response.data.length > 0) {
                    const vehicle = response.data[0];
                    log(`   Sample vehicle: ${vehicle.make} ${vehicle.model} (${vehicle.year})`, 'cyan');
                    log(`   Price: €${vehicle.price}`, 'cyan');
                }
            } else {
                log('   Response format unexpected', 'yellow');
            }
            
            return true;
        } else {
            log(`❌ Vehicles endpoint returned status: ${response.status}`, 'red');
            return false;
        }
    } catch (error) {
        log(`❌ Vehicles endpoint failed: ${error.message}`, 'red');
        return false;
    }
}

async function testAlertsEndpoint() {
    log('\n🔔 Testing Alerts Endpoint', 'blue');
    log('=' .repeat(40), 'blue');
    
    try {
        const response = await makeRequest(`${API_BASE_URL}/alerts/`);
        
        if (response.status === 200) {
            log('✅ Alerts endpoint accessible', 'green');
            
            if (Array.isArray(response.data)) {
                log(`   Found ${response.data.length} alerts`, 'cyan');
            } else {
                log('   Response format unexpected', 'yellow');
            }
            
            return true;
        } else {
            log(`❌ Alerts endpoint returned status: ${response.status}`, 'red');
            return false;
        }
    } catch (error) {
        log(`❌ Alerts endpoint failed: ${error.message}`, 'red');
        return false;
    }
}

async function testCorsHeaders() {
    log('\n🌐 Testing CORS Configuration', 'blue');
    log('=' .repeat(40), 'blue');
    
    try {
        const response = await makeRequest(`${RENDER_BASE_URL}/health`);
        
        const corsHeaders = {
            'access-control-allow-origin': response.headers['access-control-allow-origin'],
            'access-control-allow-methods': response.headers['access-control-allow-methods'],
            'access-control-allow-headers': response.headers['access-control-allow-headers']
        };
        
        if (corsHeaders['access-control-allow-origin']) {
            log('✅ CORS headers present', 'green');
            log(`   Allow-Origin: ${corsHeaders['access-control-allow-origin']}`, 'cyan');
            
            if (corsHeaders['access-control-allow-methods']) {
                log(`   Allow-Methods: ${corsHeaders['access-control-allow-methods']}`, 'cyan');
            }
        } else {
            log('⚠️  CORS headers not found - may cause mobile app issues', 'yellow');
        }
        
        return true;
    } catch (error) {
        log(`❌ CORS test failed: ${error.message}`, 'red');
        return false;
    }
}

async function runAllTests() {
    log('🧪 APK Backend Connection Test', 'magenta');
    log('=' .repeat(50), 'magenta');
    log(`Testing connection to: ${RENDER_BASE_URL}`, 'cyan');
    log(`API Base URL: ${API_BASE_URL}`, 'cyan');
    
    const results = {
        health: await testHealthEndpoint(),
        vehicles: await testVehiclesEndpoint(),
        alerts: await testAlertsEndpoint(),
        cors: await testCorsHeaders()
    };
    
    log('\n📊 Test Results Summary', 'magenta');
    log('=' .repeat(30), 'magenta');
    
    const passed = Object.values(results).filter(Boolean).length;
    const total = Object.keys(results).length;
    
    Object.entries(results).forEach(([test, passed]) => {
        const status = passed ? '✅ PASS' : '❌ FAIL';
        const color = passed ? 'green' : 'red';
        log(`${status} ${test.toUpperCase()}`, color);
    });
    
    log(`\n🎯 Overall: ${passed}/${total} tests passed`, passed === total ? 'green' : 'yellow');
    
    if (passed === total) {
        log('\n🎉 All tests passed! Your APK should connect successfully to the backend.', 'green');
        log('\n📱 Next Steps:', 'blue');
        log('   1. Install VehicleScout-cloud-release.apk on Android device', 'cyan');
        log('   2. Enable "Unknown Sources" in Android settings', 'cyan');
        log('   3. Launch the app and test vehicle browsing', 'cyan');
        log('   4. Test alert creation and management', 'cyan');
    } else {
        log('\n⚠️  Some tests failed. Check your Render deployment:', 'yellow');
        log('   1. Verify your Render app is running', 'cyan');
        log('   2. Check Render deployment logs', 'cyan');
        log('   3. Ensure database is connected', 'cyan');
        log('   4. Update the RENDER_BASE_URL in this script if needed', 'cyan');
    }
    
    return passed === total;
}

// Run the tests
if (require.main === module) {
    runAllTests().catch(console.error);
}

module.exports = { runAllTests };
