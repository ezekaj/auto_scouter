import React, { useState } from 'react'
import { TestTube, CheckCircle, XCircle, Loader2, Car, AlertTriangle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

interface AlertTestDialogProps {
  isOpen: boolean
  onClose: () => void
  alert: any
  onTest: (alertId: number) => Promise<any>
}

interface TestResult {
  success: boolean
  matchCount: number
  matches: any[]
  error?: string
  executionTime: number
}

export const AlertTestDialog: React.FC<AlertTestDialogProps> = ({
  isOpen,
  onClose,
  alert,
  onTest,
}) => {
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)

  const runTest = async () => {
    setTesting(true)
    setTestResult(null)

    try {
      const startTime = Date.now()
      const result = await onTest(alert.id)
      const executionTime = Date.now() - startTime

      setTestResult({
        success: true,
        matchCount: result.matches?.length || 0,
        matches: result.matches || [],
        executionTime,
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        matchCount: 0,
        matches: [],
        error: error.message || 'Test failed',
        executionTime: 0,
      })
    } finally {
      setTesting(false)
    }
  }

  const formatCriteria = (alert: any): string[] => {
    const criteria: string[] = []
    
    if (alert.make) criteria.push(`Make: ${alert.make}`)
    if (alert.model) criteria.push(`Model: ${alert.model}`)
    if (alert.min_price || alert.max_price) {
      const priceRange = `Price: €${alert.min_price || 0} - €${alert.max_price || '∞'}`
      criteria.push(priceRange)
    }
    if (alert.min_year || alert.max_year) {
      const yearRange = `Year: ${alert.min_year || '∞'} - ${alert.max_year || new Date().getFullYear()}`
      criteria.push(yearRange)
    }
    if (alert.max_mileage) criteria.push(`Max Mileage: ${alert.max_mileage.toLocaleString()} km`)
    if (alert.fuel_type) criteria.push(`Fuel: ${alert.fuel_type}`)
    if (alert.transmission) criteria.push(`Transmission: ${alert.transmission}`)
    if (alert.city) criteria.push(`Location: ${alert.city}`)
    
    return criteria
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <TestTube className="mr-2 h-5 w-5" />
            Test Alert: {alert?.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Alert Criteria */}
          <Card>
            <CardContent className="pt-6">
              <h3 className="font-medium mb-3">Alert Criteria</h3>
              <div className="space-y-2">
                {formatCriteria(alert).map((criterion, index) => (
                  <div key={index} className="flex items-center text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full mr-2" />
                    {criterion}
                  </div>
                ))}
              </div>
              {alert?.description && (
                <div className="mt-3 p-3 bg-muted/50 rounded text-sm">
                  <strong>Description:</strong> {alert.description}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Test Button */}
          <div className="flex justify-center">
            <Button
              onClick={runTest}
              disabled={testing}
              className="auto-scouter-gradient"
              size="lg"
            >
              {testing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing Alert...
                </>
              ) : (
                <>
                  <TestTube className="mr-2 h-4 w-4" />
                  Run Test
                </>
              )}
            </Button>
          </div>

          {/* Test Results */}
          {testResult && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium flex items-center">
                    {testResult.success ? (
                      <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="mr-2 h-5 w-5 text-red-500" />
                    )}
                    Test Results
                  </h3>
                  <Badge variant={testResult.success ? 'success' : 'destructive'}>
                    {testResult.success ? 'Success' : 'Failed'}
                  </Badge>
                </div>

                {testResult.success ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-green-50 rounded">
                        <div className="text-2xl font-bold text-green-600">
                          {testResult.matchCount}
                        </div>
                        <div className="text-sm text-green-700">Matches Found</div>
                      </div>
                      <div className="text-center p-3 bg-blue-50 rounded">
                        <div className="text-2xl font-bold text-blue-600">
                          {testResult.executionTime}ms
                        </div>
                        <div className="text-sm text-blue-700">Execution Time</div>
                      </div>
                    </div>

                    {testResult.matches.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Sample Matches</h4>
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {testResult.matches.slice(0, 5).map((match, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between p-2 border rounded text-sm"
                            >
                              <div className="flex items-center space-x-2">
                                <Car className="h-4 w-4 text-muted-foreground" />
                                <span>
                                  {match.make} {match.model} ({match.year})
                                </span>
                              </div>
                              <div className="font-medium">
                                €{match.price?.toLocaleString()}
                              </div>
                            </div>
                          ))}
                          {testResult.matches.length > 5 && (
                            <div className="text-center text-sm text-muted-foreground">
                              ... and {testResult.matches.length - 5} more matches
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {testResult.matchCount === 0 && (
                      <div className="text-center py-4 text-muted-foreground">
                        <AlertTriangle className="mx-auto h-8 w-8 mb-2" />
                        <p>No vehicles match your criteria</p>
                        <p className="text-sm">Try adjusting your filters to get more results</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <XCircle className="mx-auto h-8 w-8 text-red-500 mb-2" />
                    <p className="text-red-600 font-medium">Test Failed</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {testResult.error}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            {testResult?.success && testResult.matchCount > 0 && (
              <Button variant="outline">
                View All Matches
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
