import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
}

interface VehicleSearchParams {
  make?: string;
  model?: string;
  min_price?: number;
  max_price?: number;
  min_year?: number;
  max_year?: number;
  max_mileage?: number;
  city?: string;
  fuel_type?: string;
  transmission?: string;
  body_type?: string;
  limit?: number;
  offset?: number;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  )

  const url = new URL(req.url)
  const path = url.pathname
  const method = req.method

  try {
    // GET /health - Health check endpoint
    if (path === '/health' || path === '/') {
      return new Response(
        JSON.stringify({ 
          status: 'healthy', 
          timestamp: new Date().toISOString(),
          service: 'Auto Scouter Vehicle API',
          version: '1.0.0'
        }), 
        { 
          headers: { 
            ...corsHeaders, 
            'Content-Type': 'application/json' 
          } 
        }
      )
    }

    // GET /vehicles - Search vehicles
    if (path === '/vehicles' && method === 'GET') {
      const params = url.searchParams
      const searchParams: VehicleSearchParams = {
        make: params.get('make') || undefined,
        model: params.get('model') || undefined,
        min_price: params.get('min_price') ? parseInt(params.get('min_price')!) : undefined,
        max_price: params.get('max_price') ? parseInt(params.get('max_price')!) : undefined,
        min_year: params.get('min_year') ? parseInt(params.get('min_year')!) : undefined,
        max_year: params.get('max_year') ? parseInt(params.get('max_year')!) : undefined,
        max_mileage: params.get('max_mileage') ? parseInt(params.get('max_mileage')!) : undefined,
        city: params.get('city') || undefined,
        fuel_type: params.get('fuel_type') || undefined,
        transmission: params.get('transmission') || undefined,
        body_type: params.get('body_type') || undefined,
        limit: params.get('limit') ? parseInt(params.get('limit')!) : 50,
        offset: params.get('offset') ? parseInt(params.get('offset')!) : 0,
      }

      // Use the search function we created
      const { data, error } = await supabase.rpc('search_vehicles', {
        p_make: searchParams.make,
        p_model: searchParams.model,
        p_min_price: searchParams.min_price,
        p_max_price: searchParams.max_price,
        p_min_year: searchParams.min_year,
        p_max_year: searchParams.max_year,
        p_max_mileage: searchParams.max_mileage,
        p_city: searchParams.city,
        p_fuel_type: searchParams.fuel_type,
        p_transmission: searchParams.transmission,
        p_body_type: searchParams.body_type,
        p_limit: searchParams.limit,
        p_offset: searchParams.offset,
      })

      if (error) {
        console.error('Search error:', error)
        return new Response(
          JSON.stringify({ error: error.message }), 
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify({ 
          data: data || [], 
          count: data?.length || 0,
          params: searchParams 
        }), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // GET /vehicles/:id - Get specific vehicle
    if (path.startsWith('/vehicles/') && method === 'GET') {
      const vehicleId = path.split('/')[2]
      
      const { data, error } = await supabase
        .from('vehicle_listings')
        .select(`
          *,
          vehicle_images (
            id, image_url, image_type, display_order, is_primary
          ),
          price_history (
            id, old_price, new_price, change_date, change_percentage
          )
        `)
        .eq('id', vehicleId)
        .eq('is_active', true)
        .single()

      if (error) {
        return new Response(
          JSON.stringify({ error: error.message }), 
          { 
            status: error.code === 'PGRST116' ? 404 : 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify(data), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // POST /favorites - Add to favorites
    if (path === '/favorites' && method === 'POST') {
      const { vehicle_id, notes } = await req.json()
      
      if (!vehicle_id) {
        return new Response(
          JSON.stringify({ error: 'vehicle_id is required' }), 
          { 
            status: 400, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      const { data, error } = await supabase
        .from('favorites')
        .insert({ vehicle_id, notes })
        .select()

      if (error) {
        return new Response(
          JSON.stringify({ error: error.message }), 
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify(data[0]), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // GET /favorites - Get favorites
    if (path === '/favorites' && method === 'GET') {
      const { data, error } = await supabase
        .from('favorites')
        .select(`
          *,
          vehicle_listings (
            id, make, model, year, price, mileage, city, primary_image_url, url
          )
        `)
        .order('added_at', { ascending: false })

      if (error) {
        return new Response(
          JSON.stringify({ error: error.message }), 
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify(data), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // DELETE /favorites/:id - Remove from favorites
    if (path.startsWith('/favorites/') && method === 'DELETE') {
      const favoriteId = path.split('/')[2]
      
      const { error } = await supabase
        .from('favorites')
        .delete()
        .eq('id', favoriteId)

      if (error) {
        return new Response(
          JSON.stringify({ error: error.message }), 
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify({ success: true }), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // GET /alerts - Get alerts
    if (path === '/alerts' && method === 'GET') {
      const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) {
        return new Response(
          JSON.stringify({ error: error.message }), 
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify(data), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // POST /alerts - Create alert
    if (path === '/alerts' && method === 'POST') {
      const alertData = await req.json()
      
      const { data, error } = await supabase
        .from('alerts')
        .insert(alertData)
        .select()

      if (error) {
        return new Response(
          JSON.stringify({ error: error.message }), 
          { 
            status: 500, 
            headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
          }
        )
      }

      return new Response(
        JSON.stringify(data[0]), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // GET /stats - Get statistics
    if (path === '/stats' && method === 'GET') {
      const [vehiclesResult, alertsResult, favoritesResult] = await Promise.all([
        supabase.from('vehicle_listings').select('id', { count: 'exact', head: true }),
        supabase.from('alerts').select('id', { count: 'exact', head: true }),
        supabase.from('favorites').select('id', { count: 'exact', head: true })
      ])

      return new Response(
        JSON.stringify({
          total_vehicles: vehiclesResult.count || 0,
          total_alerts: alertsResult.count || 0,
          total_favorites: favoritesResult.count || 0,
          last_updated: new Date().toISOString()
        }), 
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // 404 - Not Found
    return new Response(
      JSON.stringify({ error: 'Not Found', path, method }), 
      { 
        status: 404, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (error) {
    console.error('API Error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal Server Error', 
        message: error.message 
      }), 
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})
