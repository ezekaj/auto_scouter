import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface VehicleData {
  make: string;
  model: string;
  year?: number;
  price?: number;
  mileage?: number;
  fuel_type?: string;
  transmission?: string;
  body_type?: string;
  city?: string;
  url: string;
  source_website: string;
  primary_image_url?: string;
  description?: string;
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

    console.log(`📝 Created scraping session: ${sessionId}`)

    // Simulate scraping process with demo data
    const demoVehicles: VehicleData[] = await scrapeVehicles()
    
    console.log(`🔍 Found ${demoVehicles.length} vehicles to process`)

    let newVehicles = 0
    let updatedVehicles = 0
    let errors = 0

    // Process each vehicle
    for (const vehicle of demoVehicles) {
      try {
        // Check if vehicle already exists
        const { data: existing } = await supabase
          .from('vehicle_listings')
          .select('id, price')
          .eq('url', vehicle.url)
          .single()

        if (existing) {
          // Update existing vehicle if price changed
          if (existing.price !== vehicle.price) {
            const { error: updateError } = await supabase
              .from('vehicle_listings')
              .update({
                price: vehicle.price,
                last_updated: new Date().toISOString()
              })
              .eq('id', existing.id)

            if (!updateError) {
              // Log price change
              await supabase.from('price_history').insert({
                vehicle_id: existing.id,
                old_price: existing.price,
                new_price: vehicle.price,
                price_change: (vehicle.price || 0) - (existing.price || 0),
                change_percentage: existing.price ? 
                  (((vehicle.price || 0) - existing.price) / existing.price * 100) : 0
              })
              
              updatedVehicles++
            }
          }
        } else {
          // Insert new vehicle
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
            
            // Log scraping activity
            await supabase.from('scraping_logs').insert({
              vehicle_id: newVehicle.id,
              session_id: sessionId,
              source_website: vehicle.source_website,
              action: 'insert',
              status: 'success'
            })
          } else {
            errors++
            console.error(`❌ Error inserting vehicle: ${insertError.message}`)
          }
        }
      } catch (vehicleError) {
        errors++
        console.error(`❌ Error processing vehicle: ${vehicleError}`)
      }
    }

    // Update scraping session
    const { error: updateSessionError } = await supabase
      .from('scraping_sessions')
      .update({
        total_vehicles_found: demoVehicles.length,
        total_vehicles_new: newVehicles,
        total_vehicles_updated: updatedVehicles,
        total_errors: errors,
        completed_at: new Date().toISOString(),
        status: 'completed'
      })
      .eq('id', session.id)

    if (updateSessionError) {
      console.error(`❌ Error updating session: ${updateSessionError.message}`)
    }

    const result = {
      success: true,
      session_id: sessionId,
      summary: {
        total_found: demoVehicles.length,
        new_vehicles: newVehicles,
        updated_vehicles: updatedVehicles,
        errors: errors
      },
      timestamp: new Date().toISOString()
    }

    console.log('✅ Scraping completed:', result)

    return new Response(
      JSON.stringify(result),
      { 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    )

  } catch (error) {
    console.error('❌ Scraping failed:', error)
    
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

async function scrapeVehicles(): Promise<VehicleData[]> {
  // Demo scraping function - replace with actual scraping logic
  // This simulates scraping from multiple sources
  
  const demoVehicles: VehicleData[] = [
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
      description: 'Excellent condition BMW X3 with full service history'
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
      description: 'Well maintained Audi A4 with low mileage'
    },
    {
      make: 'Mercedes-Benz',
      model: 'C-Class',
      year: 2021,
      price: 42000,
      mileage: 25000,
      fuel_type: 'hybrid',
      transmission: 'automatic',
      body_type: 'sedan',
      city: 'Naples',
      url: `https://demo-source.com/mercedes-c-class-${Date.now()}`,
      source_website: 'demo_source',
      primary_image_url: 'https://example.com/mercedes-c.jpg',
      description: 'Nearly new Mercedes C-Class hybrid with warranty'
    },
    {
      make: 'Volkswagen',
      model: 'Golf',
      year: 2018,
      price: 18000,
      mileage: 68000,
      fuel_type: 'petrol',
      transmission: 'manual',
      body_type: 'hatchback',
      city: 'Florence',
      url: `https://demo-source.com/vw-golf-${Date.now()}`,
      source_website: 'demo_source',
      primary_image_url: 'https://example.com/vw-golf.jpg',
      description: 'Reliable Volkswagen Golf, perfect for city driving'
    },
    {
      make: 'Fiat',
      model: '500',
      year: 2020,
      price: 15000,
      mileage: 32000,
      fuel_type: 'petrol',
      transmission: 'manual',
      body_type: 'hatchback',
      city: 'Turin',
      url: `https://demo-source.com/fiat-500-${Date.now()}`,
      source_website: 'demo_source',
      primary_image_url: 'https://example.com/fiat-500.jpg',
      description: 'Compact and efficient Fiat 500, ideal for urban use'
    }
  ]

  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  return demoVehicles
}
