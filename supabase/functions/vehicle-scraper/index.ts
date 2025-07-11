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
    console.log('🚀 Starting vehicle scraping process...')
    
    // Create a scraping session
    const sessionId = `scrape_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    const { data: session, error: sessionError } = await supabase
      .from('scraping_sessions')
      .insert({
        session_id: sessionId,
        source_website: 'demo_scraper',
        scraper_version: '1.0.0',
        status: 'running'
      })
      .select()
      .single()

    if (sessionError) {
      throw new Error(`Failed to create scraping session: ${sessionError.message}`)
    }

    // Demo vehicles data
    const demoVehicles = [
      {
        make: 'BMW',
        model: 'X3',
        year: 2020,
        price: 35000,
        mileage: 45000,
        fuel_type: 'diesel',
        transmission: 'automatic',
        body_type: 'suv',
        city: 'Rome',
        url: `https://demo-source.com/bmw-x3-${Date.now()}`,
        source_website: 'demo_source',
        primary_image_url: 'https://example.com/bmw-x3.jpg',
        description: 'Excellent condition BMW X3'
      },
      {
        make: 'Audi',
        model: 'A4',
        year: 2019,
        price: 28000,
        mileage: 52000,
        fuel_type: 'petrol',
        transmission: 'manual',
        body_type: 'sedan',
        city: 'Milan',
        url: `https://demo-source.com/audi-a4-${Date.now()}`,
        source_website: 'demo_source',
        primary_image_url: 'https://example.com/audi-a4.jpg',
        description: 'Well maintained Audi A4'
      }
    ]
    
    let newVehicles = 0
    let errors = 0

    // Process each vehicle
    for (const vehicle of demoVehicles) {
      try {
        const { data: newVehicle, error: insertError } = await supabase
          .from('vehicle_listings')
          .insert({
            ...vehicle,
            scraped_at: new Date().toISOString(),
            created_at: new Date().toISOString()
          })
          .select()
          .single()

        if (!insertError) {
          newVehicles++
        } else {
          errors++
        }
      } catch (vehicleError) {
        errors++
      }
    }

    // Update scraping session
    await supabase
      .from('scraping_sessions')
      .update({
        total_vehicles_found: demoVehicles.length,
        total_vehicles_new: newVehicles,
        total_errors: errors,
        completed_at: new Date().toISOString(),
        status: 'completed'
      })
      .eq('id', session.id)

    const result = {
      success: true,
      session_id: sessionId,
      summary: {
        total_found: demoVehicles.length,
        new_vehicles: newVehicles,
        errors: errors
      },
      timestamp: new Date().toISOString()
    }

    return new Response(
      JSON.stringify(result),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message,
        timestamp: new Date().toISOString()
      }), 
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
