import React, { useState } from 'react'
import { Settings, Save, Bell, Mail, Smartphone, Volume2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface NotificationPreferences {
  email: {
    enabled: boolean
    newMatches: boolean
    priceDrops: boolean
    weeklyDigest: boolean
    systemUpdates: boolean
  }
  push: {
    enabled: boolean
    newMatches: boolean
    priceDrops: boolean
    systemUpdates: boolean
  }
  inApp: {
    enabled: boolean
    sound: boolean
    desktop: boolean
  }
  frequency: {
    immediate: boolean
    daily: boolean
    weekly: boolean
  }
  quietHours: {
    enabled: boolean
    startTime: string
    endTime: string
  }
}

interface NotificationPreferencesProps {
  isOpen: boolean
  onClose: () => void
}

export const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({
  isOpen,
  onClose,
}) => {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email: {
      enabled: true,
      newMatches: true,
      priceDrops: true,
      weeklyDigest: true,
      systemUpdates: false,
    },
    push: {
      enabled: true,
      newMatches: true,
      priceDrops: true,
      systemUpdates: false,
    },
    inApp: {
      enabled: true,
      sound: true,
      desktop: true,
    },
    frequency: {
      immediate: true,
      daily: false,
      weekly: false,
    },
    quietHours: {
      enabled: false,
      startTime: '22:00',
      endTime: '08:00',
    },
  })

  const updatePreference = (category: keyof NotificationPreferences, key: string, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }))
  }

  const handleSave = () => {
    // Implementation for saving preferences
    console.log('Saving preferences:', preferences)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Settings className="mr-2 h-5 w-5" />
            Notification Preferences
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="channels" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="channels">Channels</TabsTrigger>
            <TabsTrigger value="types">Types</TabsTrigger>
            <TabsTrigger value="schedule">Schedule</TabsTrigger>
          </TabsList>

          <TabsContent value="channels" className="space-y-4 mt-6">
            {/* Email Notifications */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Mail className="mr-2 h-5 w-5" />
                  Email Notifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Enable Email Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Receive notifications via email
                    </p>
                  </div>
                  <Switch
                    checked={preferences.email.enabled}
                    onCheckedChange={(checked) => updatePreference('email', 'enabled', checked)}
                  />
                </div>

                {preferences.email.enabled && (
                  <div className="space-y-3 pl-4 border-l-2 border-muted">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">New vehicle matches</span>
                      <Switch
                        checked={preferences.email.newMatches}
                        onCheckedChange={(checked) => updatePreference('email', 'newMatches', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Price drop alerts</span>
                      <Switch
                        checked={preferences.email.priceDrops}
                        onCheckedChange={(checked) => updatePreference('email', 'priceDrops', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Weekly digest</span>
                      <Switch
                        checked={preferences.email.weeklyDigest}
                        onCheckedChange={(checked) => updatePreference('email', 'weeklyDigest', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">System updates</span>
                      <Switch
                        checked={preferences.email.systemUpdates}
                        onCheckedChange={(checked) => updatePreference('email', 'systemUpdates', checked)}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Push Notifications */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Smartphone className="mr-2 h-5 w-5" />
                  Push Notifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Enable Push Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Receive notifications on your device
                    </p>
                  </div>
                  <Switch
                    checked={preferences.push.enabled}
                    onCheckedChange={(checked) => updatePreference('push', 'enabled', checked)}
                  />
                </div>

                {preferences.push.enabled && (
                  <div className="space-y-3 pl-4 border-l-2 border-muted">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">New vehicle matches</span>
                      <Switch
                        checked={preferences.push.newMatches}
                        onCheckedChange={(checked) => updatePreference('push', 'newMatches', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Price drop alerts</span>
                      <Switch
                        checked={preferences.push.priceDrops}
                        onCheckedChange={(checked) => updatePreference('push', 'priceDrops', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">System updates</span>
                      <Switch
                        checked={preferences.push.systemUpdates}
                        onCheckedChange={(checked) => updatePreference('push', 'systemUpdates', checked)}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* In-App Notifications */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Bell className="mr-2 h-5 w-5" />
                  In-App Notifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Enable In-App Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Show notifications within the application
                    </p>
                  </div>
                  <Switch
                    checked={preferences.inApp.enabled}
                    onCheckedChange={(checked) => updatePreference('inApp', 'enabled', checked)}
                  />
                </div>

                {preferences.inApp.enabled && (
                  <div className="space-y-3 pl-4 border-l-2 border-muted">
                    <div className="flex items-center justify-between">
                      <span className="text-sm flex items-center">
                        <Volume2 className="mr-2 h-4 w-4" />
                        Sound notifications
                      </span>
                      <Switch
                        checked={preferences.inApp.sound}
                        onCheckedChange={(checked) => updatePreference('inApp', 'sound', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Desktop notifications</span>
                      <Switch
                        checked={preferences.inApp.desktop}
                        onCheckedChange={(checked) => updatePreference('inApp', 'desktop', checked)}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="types" className="space-y-4 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Notification Types</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">New Vehicle Matches</h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      Get notified when new vehicles match your alerts
                    </p>
                    <div className="flex space-x-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="radio"
                          name="newMatches"
                          checked={preferences.frequency.immediate}
                          onChange={() => {
                            updatePreference('frequency', 'immediate', true)
                            updatePreference('frequency', 'daily', false)
                            updatePreference('frequency', 'weekly', false)
                          }}
                        />
                        <span className="text-sm">Immediate</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="radio"
                          name="newMatches"
                          checked={preferences.frequency.daily}
                          onChange={() => {
                            updatePreference('frequency', 'immediate', false)
                            updatePreference('frequency', 'daily', true)
                            updatePreference('frequency', 'weekly', false)
                          }}
                        />
                        <span className="text-sm">Daily digest</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="radio"
                          name="newMatches"
                          checked={preferences.frequency.weekly}
                          onChange={() => {
                            updatePreference('frequency', 'immediate', false)
                            updatePreference('frequency', 'daily', false)
                            updatePreference('frequency', 'weekly', true)
                          }}
                        />
                        <span className="text-sm">Weekly digest</span>
                      </label>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="schedule" className="space-y-4 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quiet Hours</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Enable Quiet Hours</p>
                    <p className="text-sm text-muted-foreground">
                      Pause notifications during specified hours
                    </p>
                  </div>
                  <Switch
                    checked={preferences.quietHours.enabled}
                    onCheckedChange={(checked) => updatePreference('quietHours', 'enabled', checked)}
                  />
                </div>

                {preferences.quietHours.enabled && (
                  <div className="grid grid-cols-2 gap-4 pl-4 border-l-2 border-muted">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Start Time</label>
                      <input
                        type="time"
                        value={preferences.quietHours.startTime}
                        onChange={(e) => updatePreference('quietHours', 'startTime', e.target.value)}
                        className="w-full border rounded px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">End Time</label>
                      <input
                        type="time"
                        value={preferences.quietHours.endTime}
                        onChange={(e) => updatePreference('quietHours', 'endTime', e.target.value)}
                        className="w-full border rounded px-3 py-2"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Actions */}
        <div className="flex justify-end space-x-2 mt-6">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} className="auto-scouter-gradient">
            <Save className="mr-2 h-4 w-4" />
            Save Preferences
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
