#!/usr/bin/env node

/**
 * Render Deployment Status Checker
 * Monitors your Render deployment and helps diagnose issues
 */

const https = require('https');
const http = require('http');

// Test different possible URLs
const TEST_URLS = [
    'https://auto-scouter-backend.onrender.com',
    'https://auto-scouter-backend-production.onrender.com',
    'https://auto-scouter-backend-main.onrender.com'
];

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

function makeRequest(url, timeout = 15000) {
    return new Promise((resolve, reject) => {
        const protocol = url.startsWith('https:') ? https : http;
        
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
                        data: jsonData,
                        raw: data
                    });
                } catch (e) {
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: null,
                        raw: data
                    });
                }
            });
        });
        
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout - service may not be deployed'));
        });
        
        req.on('error', (err) => {
            reject(err);
        });
    });
}

async function checkUrl(baseUrl) {
    log(`\n🔍 Testing: ${baseUrl}`, 'blue');
    log('=' .repeat(50), 'blue');
    
    try {
        // Test health endpoint
        const healthResponse = await makeRequest(`${baseUrl}/health`);
        
        if (healthResponse.status === 200) {
            log('✅ Service is LIVE and responding!', 'green');
            log(`   Status: ${healthResponse.data?.status || 'Unknown'}`, 'cyan');
            log(`   Environment: ${healthResponse.data?.environment || 'Unknown'}`, 'cyan');
            log(`   Database: ${healthResponse.data?.database || 'Unknown'}`, 'cyan');
            log(`   Version: ${healthResponse.data?.version || 'Unknown'}`, 'cyan');
            
            // Test API endpoint
            try {
                const apiResponse = await makeRequest(`${baseUrl}/api/v1/automotive/vehicles/simple`);
                if (apiResponse.status === 200) {
                    log('✅ API endpoints working', 'green');
                    log(`   Found ${Array.isArray(apiResponse.data) ? apiResponse.data.length : 'unknown'} vehicles`, 'cyan');
                } else {
                    log(`⚠️  API endpoint returned status: ${apiResponse.status}`, 'yellow');
                }
            } catch (apiError) {
                log(`⚠️  API endpoint test failed: ${apiError.message}`, 'yellow');
            }
            
            return { url: baseUrl, status: 'live', response: healthResponse };
        } else {
            log(`❌ Service returned status: ${healthResponse.status}`, 'red');
            log(`   Response: ${healthResponse.raw}`, 'yellow');
            return { url: baseUrl, status: 'error', response: healthResponse };
        }
    } catch (error) {
        if (error.message.includes('timeout')) {
            log('❌ Service not responding (timeout)', 'red');
            log('   This usually means the service is not deployed yet', 'yellow');
        } else if (error.code === 'ENOTFOUND') {
            log('❌ URL does not exist', 'red');
        } else {
            log(`❌ Connection failed: ${error.message}`, 'red');
        }
        return { url: baseUrl, status: 'failed', error: error.message };
    }
}

async function checkAllUrls() {
    log('🚀 Render Deployment Status Checker', 'magenta');
    log('=' .repeat(60), 'magenta');
    
    const results = [];
    
    for (const url of TEST_URLS) {
        const result = await checkUrl(url);
        results.push(result);
        
        if (result.status === 'live') {
            log(`\n🎉 FOUND WORKING DEPLOYMENT!`, 'green');
            log(`✅ Your backend is live at: ${url}`, 'green');
            
            // Update APK configuration instructions
            log(`\n📱 To update your APK configuration:`, 'blue');
            log(`   1. Edit frontend/.env.production`, 'cyan');
            log(`   2. Update VITE_API_BASE_URL to: ${url}/api/v1`, 'cyan');
            log(`   3. Update VITE_WS_BASE_URL to: ${url.replace('https:', 'wss:')}/ws`, 'cyan');
            log(`   4. Rebuild APK: cd frontend && ./build_cloud_apk.sh`, 'cyan');
            
            return result;
        }
    }
    
    log(`\n❌ No working deployments found`, 'red');
    log(`\n🔧 Troubleshooting Steps:`, 'yellow');
    log(`   1. Check if you've deployed to Render yet:`, 'cyan');
    log(`      - Go to render.com dashboard`, 'cyan');
    log(`      - Look for 'auto-scouter-backend' service`, 'cyan');
    log(`   2. If not deployed, deploy now:`, 'cyan');
    log(`      - New → Blueprint`, 'cyan');
    log(`      - Repository: ezekaj/auto_scouter`, 'cyan');
    log(`      - Blueprint path: render.yaml`, 'cyan');
    log(`   3. If deployed but failing:`, 'cyan');
    log(`      - Check Render deployment logs`, 'cyan');
    log(`      - Verify build completed successfully`, 'cyan');
    log(`      - Check database connection`, 'cyan');
    
    return null;
}

async function continuousMonitor() {
    log(`\n🔄 Starting continuous monitoring...`, 'blue');
    log(`Press Ctrl+C to stop`, 'yellow');
    
    let attempt = 1;
    
    const monitor = setInterval(async () => {
        log(`\n--- Attempt ${attempt} ---`, 'magenta');
        
        const result = await checkUrl(TEST_URLS[0]);
        
        if (result.status === 'live') {
            log(`\n🎉 DEPLOYMENT IS NOW LIVE!`, 'green');
            clearInterval(monitor);
            return;
        }
        
        attempt++;
        
        if (attempt > 20) {
            log(`\n⏰ Stopping after 20 attempts. Check Render dashboard manually.`, 'yellow');
            clearInterval(monitor);
        }
    }, 30000); // Check every 30 seconds
}

// Main execution
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.includes('--monitor') || args.includes('-m')) {
        continuousMonitor().catch(console.error);
    } else {
        checkAllUrls().catch(console.error);
    }
}

module.exports = { checkAllUrls, checkUrl };
