import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  )

  try {
    console.log('🕐 Scheduled scraping job started at:', new Date().toISOString())

    // Check if scraping is already running
    const { data: runningSessions, error: sessionError } = await supabase
      .from('scraping_sessions')
      .select('id, status, started_at')
      .eq('status', 'running')
      .gte('started_at', new Date(Date.now() - 30 * 60 * 1000).toISOString()) // Last 30 minutes

    if (sessionError) {
      console.error('Error checking running sessions:', sessionError)
    }

    if (runningSessions && runningSessions.length > 0) {
      console.log('⏳ Scraping already in progress, skipping this run')
      return new Response(
        JSON.stringify({ 
          success: true, 
          message: 'Scraping already in progress',
          running_sessions: runningSessions.length
        }),
        { 
          headers: { 
            ...corsHeaders, 
            'Content-Type': 'application/json' 
          } 
        }
      )
    }

    // Call the vehicle-scraper function
    const scraperUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/vehicle-scraper`
    
    console.log('🚀 Triggering vehicle scraper...')
    
    const scraperResponse = await fetch(scraperUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        source: 'scheduled_cron',
        max_vehicles: 100,
        force_scrape: false
      })
    })

    if (!scraperResponse.ok) {
      throw new Error(`Scraper failed with status: ${scraperResponse.status}`)
    }

    const scraperResult = await scraperResponse.json()
    
    console.log('✅ Scheduled scraping completed:', scraperResult)

    // Log the scheduled run
    const { error: logError } = await supabase
      .from('scraping_logs')
      .insert({
        session_id: scraperResult.session_id || 'scheduled_unknown',
        log_level: 'INFO',
        message: 'Scheduled scraping completed successfully',
        data: {
          trigger: 'cron_job',
          result: scraperResult,
          timestamp: new Date().toISOString()
        }
      })

    if (logError) {
      console.error('Error logging scheduled run:', logError)
    }

    // Check for new vehicles and trigger alerts if needed
    await checkAndTriggerAlerts(supabase, scraperResult)

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Scheduled scraping completed successfully',
        scraper_result: scraperResult,
        timestamp: new Date().toISOString()
      }),
      { 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    )

  } catch (error) {
    console.error('❌ Scheduled scraping failed:', error)
    
    // Log the error
    try {
      await supabase
        .from('scraping_logs')
        .insert({
          session_id: 'scheduled_error',
          log_level: 'ERROR',
          message: 'Scheduled scraping failed',
          data: {
            error: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
          }
        })
    } catch (logError) {
      console.error('Error logging scheduled error:', logError)
    }

    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message,
        timestamp: new Date().toISOString()
      }), 
      { 
        status: 500, 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    )
  }
})

async function checkAndTriggerAlerts(supabase: any, scraperResult: any) {
  try {
    console.log('🔔 Checking for alert matches...')

    // Get all active alerts
    const { data: alerts, error: alertsError } = await supabase
      .from('alerts')
      .select('*')
      .eq('is_active', true)

    if (alertsError) {
      console.error('Error fetching alerts:', alertsError)
      return
    }

    if (!alerts || alerts.length === 0) {
      console.log('No active alerts found')
      return
    }

    console.log(`Found ${alerts.length} active alerts to check`)

    // Get recently added vehicles (from the last scraping session)
    const { data: recentVehicles, error: vehiclesError } = await supabase
      .from('vehicle_listings')
      .select('*')
      .eq('is_active', true)
      .gte('created_at', new Date(Date.now() - 60 * 60 * 1000).toISOString()) // Last hour

    if (vehiclesError) {
      console.error('Error fetching recent vehicles:', vehiclesError)
      return
    }

    if (!recentVehicles || recentVehicles.length === 0) {
      console.log('No recent vehicles found')
      return
    }

    console.log(`Checking ${recentVehicles.length} recent vehicles against alerts`)

    // Check each alert against recent vehicles
    for (const alert of alerts) {
      const matchingVehicles = recentVehicles.filter(vehicle => 
        matchesAlert(vehicle, alert)
      )

      if (matchingVehicles.length > 0) {
        console.log(`Alert "${alert.name}" matched ${matchingVehicles.length} vehicles`)

        // Create notifications for matches
        for (const vehicle of matchingVehicles) {
          await createAlertNotification(supabase, alert, vehicle)
        }
      }
    }

  } catch (error) {
    console.error('Error checking alerts:', error)
  }
}

function matchesAlert(vehicle: any, alert: any): boolean {
  // Check make
  if (alert.make && vehicle.make?.toLowerCase() !== alert.make.toLowerCase()) {
    return false
  }

  // Check model
  if (alert.model && !vehicle.model?.toLowerCase().includes(alert.model.toLowerCase())) {
    return false
  }

  // Check year range
  if (alert.min_year && vehicle.year && vehicle.year < alert.min_year) {
    return false
  }
  if (alert.max_year && vehicle.year && vehicle.year > alert.max_year) {
    return false
  }

  // Check price range
  if (alert.min_price && vehicle.price && vehicle.price < alert.min_price) {
    return false
  }
  if (alert.max_price && vehicle.price && vehicle.price > alert.max_price) {
    return false
  }

  // Check mileage
  if (alert.max_mileage && vehicle.mileage && vehicle.mileage > alert.max_mileage) {
    return false
  }

  // Check fuel type
  if (alert.fuel_type && vehicle.fuel_type?.toLowerCase() !== alert.fuel_type.toLowerCase()) {
    return false
  }

  // Check transmission
  if (alert.transmission && vehicle.transmission?.toLowerCase() !== alert.transmission.toLowerCase()) {
    return false
  }

  // Check body type
  if (alert.body_type && vehicle.body_type?.toLowerCase() !== alert.body_type.toLowerCase()) {
    return false
  }

  // Check city
  if (alert.city && vehicle.city?.toLowerCase() !== alert.city.toLowerCase()) {
    return false
  }

  return true
}

async function createAlertNotification(supabase: any, alert: any, vehicle: any) {
  try {
    const notification = {
      type: 'alert_triggered',
      title: `Alert Match: ${alert.name}`,
      message: `Found matching vehicle: ${vehicle.make} ${vehicle.model} (${vehicle.year}) - €${vehicle.price}`,
      data: {
        alert_id: alert.id,
        vehicle_id: vehicle.id,
        alert_name: alert.name,
        vehicle: {
          make: vehicle.make,
          model: vehicle.model,
          year: vehicle.year,
          price: vehicle.price,
          mileage: vehicle.mileage,
          city: vehicle.city,
          url: vehicle.url
        }
      },
      is_read: false
    }

    const { error } = await supabase
      .from('notifications')
      .insert(notification)

    if (error) {
      console.error('Error creating notification:', error)
    } else {
      console.log(`✅ Created notification for alert "${alert.name}"`)
    }

  } catch (error) {
    console.error('Error creating alert notification:', error)
  }
}
