import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  RefreshCw, 
  Globe,
  Database,
  Activity,
  Car
} from 'lucide-react';
import { api } from '@/lib/api';

interface TestResult {
  name: string;
  status: 'success' | 'error' | 'warning';
  message: string;
  data?: any;
  duration?: number;
}

const ApiTest: React.FC = () => {
  const [tests, setTests] = useState<TestResult[]>([]);
  const [running, setRunning] = useState(false);

  const runTest = async (name: string, testFn: () => Promise<any>): Promise<TestResult> => {
    const startTime = Date.now();
    try {
      const data = await testFn();
      const duration = Date.now() - startTime;
      return {
        name,
        status: 'success',
        message: 'Success',
        data,
        duration
      };
    } catch (error: any) {
      const duration = Date.now() - startTime;
      return {
        name,
        status: 'error',
        message: error.message || 'Unknown error',
        duration
      };
    }
  };

  const runAllTests = async () => {
    setRunning(true);
    setTests([]);

    const testSuite = [
      {
        name: 'API Connection',
        test: () => api.get('/')
      },
      {
        name: 'Health Check',
        test: () => api.get('/health')
      },
      {
        name: 'System Status',
        test: () => api.get('/system/status')
      },
      {
        name: 'Vehicle Endpoint',
        test: () => api.get('/automotive/vehicles?limit=1')
      },
      {
        name: 'Makes Endpoint',
        test: () => api.get('/automotive/makes')
      },
      {
        name: 'Scraper Status',
        test: () => api.get('/automotive/scraper/status')
      }
    ];

    const results: TestResult[] = [];
    
    for (const { name, test } of testSuite) {
      const result = await runTest(name, test);
      results.push(result);
      setTests([...results]); // Update UI after each test
    }

    setRunning(false);
  };

  useEffect(() => {
    runAllTests();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800">Success</Badge>;
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-800">Error</Badge>;
      default:
        return <Badge className="bg-blue-100 text-blue-800">Running</Badge>;
    }
  };

  const successCount = tests.filter(t => t.status === 'success').length;
  const errorCount = tests.filter(t => t.status === 'error').length;
  const totalTests = tests.length;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">API Connection Test</h1>
        <p className="text-gray-600">Testing connection to Vehicle Scout Backend</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTests}</div>
            <p className="text-xs text-muted-foreground">API endpoints tested</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{successCount}</div>
            <p className="text-xs text-muted-foreground">Working endpoints</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{errorCount}</div>
            <p className="text-xs text-muted-foreground">Failed endpoints</p>
          </CardContent>
        </Card>
      </div>

      {/* Test Results */}
      <Card>
        <CardHeader className="flex justify-between items-center">
          <CardTitle>Test Results</CardTitle>
          <Button onClick={runAllTests} disabled={running} size="sm">
            <RefreshCw className={`w-4 h-4 mr-2 ${running ? 'animate-spin' : ''}`} />
            Run Tests
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tests.map((test, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(test.status)}
                  <div>
                    <h3 className="font-medium">{test.name}</h3>
                    <p className="text-sm text-gray-500">{test.message}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {test.duration && (
                    <span className="text-xs text-gray-400">{test.duration}ms</span>
                  )}
                  {getStatusBadge(test.status)}
                </div>
              </div>
            ))}
            
            {running && tests.length < 6 && (
              <div className="flex items-center justify-center p-8">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mr-3" />
                <span>Running tests...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Globe className="w-5 h-5 mr-2" />
            API Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Base URL:</span>
              <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                {api.defaults.baseURL}
              </code>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Timeout:</span>
              <span>{api.defaults.timeout}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Environment:</span>
              <span>{import.meta.env.MODE}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p>• If all tests pass, the backend is running and accessible</p>
            <p>• If tests fail, check that the backend is deployed and running</p>
            <p>• For Railway deployment, use the deployment script in the backend folder</p>
            <p>• Check the console for detailed error messages</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApiTest;
