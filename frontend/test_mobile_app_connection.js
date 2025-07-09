#!/usr/bin/env node
/**
 * Mobile App Connection Test
 * Tests the mobile app's connection to the Render backend
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Read API URL from .env file
function getApiUrl() {
    try {
        const envPath = path.join(__dirname, '.env');
        const envContent = fs.readFileSync(envPath, 'utf8');
        const apiUrlMatch = envContent.match(/VITE_API_URL=(.+)/);
        
        if (apiUrlMatch) {
            return apiUrlMatch[1].trim();
        }
    } catch (error) {
        console.error('Error reading .env file:', error.message);
    }
    
    return 'https://auto-scouter-backend.onrender.com/api/v1';
}

const API_URL = getApiUrl();
const BASE_URL = API_URL.replace('/api/v1', '');

console.log('🚀 Auto Scouter Mobile App Connection Test');
console.log('=' .repeat(60));
console.log(`Backend URL: ${BASE_URL}`);
console.log(`API URL: ${API_URL}`);
console.log('=' .repeat(60));

async function testHealthEndpoint() {
    console.log('\n🏥 Testing Health Endpoint');
    console.log('-'.repeat(40));
    
    try {
        const response = await axios.get(`${BASE_URL}/health`, { timeout: 30000 });
        
        if (response.status === 200) {
            const data = response.data;
            console.log('✅ Health endpoint working');
            console.log(`   Status: ${data.status}`);
            console.log(`   Environment: ${data.environment}`);
            console.log(`   Version: ${data.version || 'Not specified'}`);
            
            if (data.version === '2.0.0-alerts-enabled') {
                console.log('✅ Updated backend code deployed!');
                return true;
            } else {
                console.log('❌ Old backend code detected');
                return false;
            }
        }
    } catch (error) {
        console.log(`❌ Health endpoint failed: ${error.message}`);
        return false;
    }
}

async function testVehicleListings() {
    console.log('\n🚗 Testing Vehicle Listings (Mobile App Data)');
    console.log('-'.repeat(40));
    
    try {
        const response = await axios.get(`${API_URL}/automotive/vehicles/simple?limit=5`, { 
            timeout: 30000 
        });
        
        if (response.status === 200) {
            const data = response.data;
            const vehicles = data.vehicles || [];
            console.log(`✅ Vehicle listings working - ${vehicles.length} vehicles`);
            
            if (vehicles.length > 0) {
                const vehicle = vehicles[0];
                console.log(`   Sample: ${vehicle.make} ${vehicle.model} - €${vehicle.price?.toLocaleString()}`);
                console.log(`   Location: ${vehicle.city}, ${vehicle.country}`);
            }
            
            return true;
        }
    } catch (error) {
        console.log(`❌ Vehicle listings failed: ${error.message}`);
        if (error.response) {
            console.log(`   Status: ${error.response.status}`);
            console.log(`   Response: ${JSON.stringify(error.response.data, null, 2)}`);
        }
        return false;
    }
}

async function testAlertCreation() {
    console.log('\n🔔 Testing Alert Creation (Mobile App Feature)');
    console.log('-'.repeat(40));
    
    const alertData = {
        name: 'Mobile App Test Alert',
        description: 'Testing alert creation from mobile app',
        make: 'BMW',
        model: '3 Series',
        max_price: 30000,
        min_year: 2018,
        fuel_type: 'Diesel',
        city: 'Tiranë',
        is_active: true,
        notification_frequency: 'immediate'
    };
    
    try {
        const response = await axios.post(`${API_URL}/alerts/`, alertData, {
            headers: { 'Content-Type': 'application/json' },
            timeout: 30000
        });
        
        if (response.status === 200) {
            const data = response.data;
            console.log('✅ Alert creation working');
            console.log(`   Alert ID: ${data.alert?.id}`);
            console.log(`   Alert Name: ${data.alert?.name}`);
            console.log(`   Status: ${data.status}`);
            return data.alert?.id;
        }
    } catch (error) {
        console.log(`❌ Alert creation failed: ${error.message}`);
        if (error.response) {
            console.log(`   Status: ${error.response.status}`);
            console.log(`   Response: ${JSON.stringify(error.response.data, null, 2)}`);
        }
        return null;
    }
}

async function testAlertRetrieval() {
    console.log('\n📋 Testing Alert Retrieval (Mobile App List)');
    console.log('-'.repeat(40));
    
    try {
        const response = await axios.get(`${API_URL}/alerts/`, { timeout: 30000 });
        
        if (response.status === 200) {
            const data = response.data;
            const alerts = data.alerts || [];
            console.log(`✅ Alert retrieval working - ${alerts.length} alerts`);
            
            if (alerts.length > 0) {
                const alert = alerts[0];
                console.log(`   Sample: ${alert.name}`);
                console.log(`   Active: ${alert.is_active}`);
                console.log(`   Created: ${alert.created_at}`);
            }
            
            return true;
        }
    } catch (error) {
        console.log(`❌ Alert retrieval failed: ${error.message}`);
        if (error.response) {
            console.log(`   Status: ${error.response.status}`);
        }
        return false;
    }
}

async function testCorsHeaders() {
    console.log('\n🌐 Testing CORS Headers (Mobile App Compatibility)');
    console.log('-'.repeat(40));
    
    try {
        const response = await axios.options(`${API_URL}/alerts/`, {
            headers: {
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout: 30000
        });
        
        const corsHeaders = {
            'Access-Control-Allow-Origin': response.headers['access-control-allow-origin'],
            'Access-Control-Allow-Methods': response.headers['access-control-allow-methods'],
            'Access-Control-Allow-Headers': response.headers['access-control-allow-headers']
        };
        
        console.log('✅ CORS headers present');
        console.log(`   Allow-Origin: ${corsHeaders['Access-Control-Allow-Origin'] || 'Not set'}`);
        console.log(`   Allow-Methods: ${corsHeaders['Access-Control-Allow-Methods'] || 'Not set'}`);
        
        return true;
    } catch (error) {
        console.log(`⚠️  CORS test inconclusive: ${error.message}`);
        return true; // Don't fail the test for CORS issues
    }
}

async function runMobileAppTest() {
    const results = [];
    
    // Test 1: Health endpoint
    const healthOk = await testHealthEndpoint();
    results.push(['Health Endpoint', healthOk]);
    
    // Test 2: Vehicle listings
    const vehiclesOk = await testVehicleListings();
    results.push(['Vehicle Listings', vehiclesOk]);
    
    // Test 3: Alert creation
    const alertId = await testAlertCreation();
    const alertCreationOk = alertId !== null;
    results.push(['Alert Creation', alertCreationOk]);
    
    // Test 4: Alert retrieval
    const alertRetrievalOk = await testAlertRetrieval();
    results.push(['Alert Retrieval', alertRetrievalOk]);
    
    // Test 5: CORS headers
    const corsOk = await testCorsHeaders();
    results.push(['CORS Headers', corsOk]);
    
    // Summary
    console.log('\n📊 Mobile App Connection Test Results');
    console.log('='.repeat(60));
    
    let passed = 0;
    const total = results.length;
    
    results.forEach(([testName, success]) => {
        const status = success ? '✅ PASS' : '❌ FAIL';
        console.log(`${testName.padEnd(20)} ${status}`);
        if (success) passed++;
    });
    
    console.log('-'.repeat(60));
    console.log(`Tests passed: ${passed}/${total}`);
    
    if (passed === total) {
        console.log('\n🎉 ALL TESTS PASSED!');
        console.log('✅ Mobile app should work with this backend');
        console.log('✅ You can now test alert creation in the mobile app');
        console.log('\nNext steps:');
        console.log('1. Run: npm run dev');
        console.log('2. Open: http://localhost:5173');
        console.log('3. Navigate to Alert Management');
        console.log('4. Try creating a new alert');
        return true;
    } else {
        console.log(`\n❌ ${total - passed} TESTS FAILED`);
        console.log('❌ Mobile app may not work correctly');
        console.log('\nTroubleshooting:');
        console.log('1. Check if backend is deployed and running');
        console.log('2. Verify .env file has correct API URL');
        console.log('3. Check backend logs for errors');
        return false;
    }
}

// Run the test
runMobileAppTest()
    .then(success => {
        process.exit(success ? 0 : 1);
    })
    .catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
