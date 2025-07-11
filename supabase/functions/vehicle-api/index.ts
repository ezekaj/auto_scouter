import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
}

serve(async (req) => {
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

  console.log('API Request:', method, path)

  try {
    // Health check - matches any path with health or root
    if (path.endsWith('/health') || path === '/' || path === '') {
      return new Response(
        JSON.stringify({ 
          status: 'healthy', 
          timestamp: new Date().toISOString(),
          service: 'Auto Scouter Vehicle API',
          version: '1.0.0',
          path: path
        }), 
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Vehicle search - matches any path with vehicles
    if (path.endsWith('/vehicles') && method === 'GET') {
      const params = url.searchParams
      const searchParams = {
        make: params.get('make') || undefined,
        model: params.get('model') || undefined,
        min_price: params.get('min_price') ? parseInt(params.get('min_price')) : undefined,
        max_price: params.get('max_price') ? parseInt(params.get('max_price')) : undefined,
        limit: params.get('limit') ? parseInt(params.get('limit')) : 50,
        offset: params.get('offset') ? parseInt(params.get('offset')) : 0,
      }

      console.log('Search params:', searchParams)

      const { data, error } = await supabase.rpc('search_vehicles', {
        p_make: searchParams.make,
        p_model: searchParams.model,
        p_min_price: searchParams.min_price,
        p_max_price: searchParams.max_price,
        p_limit: searchParams.limit,
        p_offset: searchParams.offset,
      })

      if (error) {
        console.error('Search error:', error)
        return new Response(
          JSON.stringify({ error: error.message }), 
          { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      return new Response(
        JSON.stringify({ 
          data: data || [], 
          count: data?.length || 0,
          params: searchParams
        }), 
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Add to favorites
    if (path.endsWith('/favorites') && method === 'POST') {
      const { vehicle_id, notes } = await req.json()
      
      if (!vehicle_id) {
        return new Response(
          JSON.stringify({ error: 'vehicle_id is required' }), 
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      const { data, error } = await supabase
        .from('favorites')
        .insert({ vehicle_id, notes })
        .select()

      if (error) {
        return new Response(
          JSON.stringify({ error: error.message }), 
          { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      return new Response(
        JSON.stringify(data[0]), 
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Get favorites
    if (path.endsWith('/favorites') && method === 'GET') {
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
          { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      return new Response(
        JSON.stringify(data), 
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Statistics
    if (path.endsWith('/stats') && method === 'GET') {
      const [vehiclesResult, favoritesResult] = await Promise.all([
        supabase.from('vehicle_listings').select('id', { count: 'exact', head: true }),
        supabase.from('favorites').select('id', { count: 'exact', head: true })
      ])

      return new Response(
        JSON.stringify({
          total_vehicles: vehiclesResult.count || 0,
          total_favorites: favoritesResult.count || 0,
          last_updated: new Date().toISOString()
        }), 
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Default response
    return new Response(
      JSON.stringify({ 
        error: 'Not Found', 
        path: path, 
        method: method,
        available_endpoints: ['/health', '/vehicles', '/favorites', '/stats']
      }), 
      { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('API Error:', error)
    return new Response(
      JSON.stringify({ 
        error: 'Internal Server Error', 
        message: error.message,
        path: path
      }), 
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
