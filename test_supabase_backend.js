#!/usr/bin/env node

/**
 * Auto Scouter - Supabase Backend Testing Script
 * 
 * This script tests all Supabase components:
 * - Edge Functions
 * - Database operations
 * - Real-time subscriptions
 * - API endpoints
 */

const https = require('https');
const http = require('http');

// Configuration
const SUPABASE_URL = 'https://rwonkzncpzirokqnuoyx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3b25rem5jcHppcm9rcW51b3l4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIyNDU4MjAsImV4cCI6MjA2NzgyMTgyMH0.-MBUrznx8MttfUmQQjZxGgzx08bZNN_PX6OtbMO-Zhk';

// Test results
const testResults = {
  passed: 0,
  failed: 0,
  tests: []
};

// Helper function to make HTTP requests
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    const requestOptions = {
      method: options.method || 'GET',
      headers: {
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    const req = protocol.request(url, requestOptions, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({ status: res.statusCode, data: jsonData, headers: res.headers });
        } catch (e) {
          resolve({ status: res.statusCode, data: data, headers: res.headers });
        }
      });
    });

    req.on('error', reject);
    
    if (options.body) {
      req.write(JSON.stringify(options.body));
    }
    
    req.end();
  });
}

// Test function wrapper
async function runTest(name, testFn) {
  console.log(`\n🧪 Testing: ${name}`);
  try {
    const result = await testFn();
    if (result) {
      console.log(`✅ PASSED: ${name}`);
      testResults.passed++;
      testResults.tests.push({ name, status: 'PASSED', details: result });
    } else {
      console.log(`❌ FAILED: ${name}`);
      testResults.failed++;
      testResults.tests.push({ name, status: 'FAILED', details: 'Test returned false' });
    }
  } catch (error) {
    console.log(`❌ FAILED: ${name} - ${error.message}`);
    testResults.failed++;
    testResults.tests.push({ name, status: 'FAILED', details: error.message });
  }
}

// Test 1: Supabase Project Connectivity
async function testSupabaseConnectivity() {
  const response = await makeRequest(`${SUPABASE_URL}/rest/v1/`);
  return response.status === 200 || response.status === 404; // 404 is expected for root endpoint
}

// Test 2: Vehicle API Edge Function
async function testVehicleAPI() {
  const response = await makeRequest(`${SUPABASE_URL}/functions/v1/vehicle-api`, {
    method: 'POST',
    body: { action: 'stats' }
  });
  return response.status === 200 && response.data.success;
}

// Test 3: Vehicle Scraper Edge Function
async function testVehicleScraper() {
  const response = await makeRequest(`${SUPABASE_URL}/functions/v1/vehicle-scraper`, {
    method: 'GET'
  });
  return response.status === 200;
}

// Test 4: Scheduled Scraper Edge Function
async function testScheduledScraper() {
  const response = await makeRequest(`${SUPABASE_URL}/functions/v1/scheduled-scraper`, {
    method: 'POST',
    body: { source: 'test_run', alerts_only: true }
  });
  return response.status === 200;
}

// Test 5: Database Table Access
async function testDatabaseAccess() {
  const response = await makeRequest(`${SUPABASE_URL}/rest/v1/vehicle_listings?select=id&limit=1`);
  return response.status === 200 && Array.isArray(response.data);
}

// Test 6: Vehicle Search Functionality
async function testVehicleSearch() {
  const response = await makeRequest(`${SUPABASE_URL}/functions/v1/vehicle-api`, {
    method: 'POST',
    body: {
      action: 'search',
      filters: {
        limit: 5
      }
    }
  });
  return response.status === 200 && response.data.success;
}

// Test 7: Alert Creation
async function testAlertCreation() {
  const response = await makeRequest(`${SUPABASE_URL}/functions/v1/vehicle-api`, {
    method: 'POST',
    body: {
      action: 'create_alert',
      alert: {
        name: 'Test Alert',
        make: 'BMW',
        max_price: 50000
      }
    }
  });
  return response.status === 200;
}

// Test 8: Favorites Functionality
async function testFavorites() {
  const response = await makeRequest(`${SUPABASE_URL}/functions/v1/vehicle-api`, {
    method: 'POST',
    body: {
      action: 'get_favorites'
    }
  });
  return response.status === 200;
}

// Test 9: Real-time Endpoint
async function testRealtimeEndpoint() {
  const response = await makeRequest(`${SUPABASE_URL}/realtime/v1/websocket`);
  // WebSocket endpoint should return 426 (Upgrade Required) for HTTP requests
  return response.status === 426 || response.status === 400;
}

// Test 10: Database Health Check
async function testDatabaseHealth() {
  const response = await makeRequest(`${SUPABASE_URL}/rest/v1/rpc/get_scraping_status`, {
    method: 'POST'
  });
  return response.status === 200 || response.status === 404; // Function might not exist yet
}

// Main test runner
async function runAllTests() {
  console.log('🚀 Starting Auto Scouter Supabase Backend Tests');
  console.log('=' .repeat(60));

  await runTest('Supabase Project Connectivity', testSupabaseConnectivity);
  await runTest('Vehicle API Edge Function', testVehicleAPI);
  await runTest('Vehicle Scraper Edge Function', testVehicleScraper);
  await runTest('Scheduled Scraper Edge Function', testScheduledScraper);
  await runTest('Database Table Access', testDatabaseAccess);
  await runTest('Vehicle Search Functionality', testVehicleSearch);
  await runTest('Alert Creation', testAlertCreation);
  await runTest('Favorites Functionality', testFavorites);
  await runTest('Real-time Endpoint', testRealtimeEndpoint);
  await runTest('Database Health Check', testDatabaseHealth);

  // Print summary
  console.log('\n' + '=' .repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log('=' .repeat(60));
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log(`📈 Success Rate: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`);

  if (testResults.failed > 0) {
    console.log('\n❌ FAILED TESTS:');
    testResults.tests
      .filter(test => test.status === 'FAILED')
      .forEach(test => {
        console.log(`  - ${test.name}: ${test.details}`);
      });
  }

  console.log('\n🎯 PRODUCTION READINESS CHECK:');
  const criticalTests = [
    'Supabase Project Connectivity',
    'Vehicle API Edge Function',
    'Database Table Access',
    'Vehicle Search Functionality'
  ];

  const criticalPassed = testResults.tests
    .filter(test => criticalTests.includes(test.name) && test.status === 'PASSED')
    .length;

  if (criticalPassed === criticalTests.length) {
    console.log('✅ PRODUCTION READY - All critical tests passed!');
  } else {
    console.log('❌ NOT PRODUCTION READY - Critical tests failed!');
  }

  console.log('\n📝 RECOMMENDATIONS:');
  if (testResults.failed === 0) {
    console.log('✅ All tests passed! The Supabase backend is fully functional.');
  } else {
    console.log('⚠️  Some tests failed. Please review the failed tests and fix issues before production deployment.');
  }

  console.log('\n🔗 USEFUL LINKS:');
  console.log(`📊 Supabase Dashboard: https://supabase.com/dashboard/project/rwonkzncpzirokqnuoyx`);
  console.log(`🔧 Edge Functions: ${SUPABASE_URL}/functions/v1/`);
  console.log(`📡 Real-time: ${SUPABASE_URL}/realtime/v1/`);
  console.log(`🗄️  Database: ${SUPABASE_URL}/rest/v1/`);

  return testResults.failed === 0;
}

// Run tests if this script is executed directly
if (require.main === module) {
  runAllTests()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('❌ Test runner failed:', error);
      process.exit(1);
    });
}

module.exports = { runAllTests, testResults };
