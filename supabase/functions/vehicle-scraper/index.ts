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
        source_website: 'carmarket.ayvens.com',
        scraper_version: '2.0.0',
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
  // Real Ayvens carmarket.ayvens.com scraping implementation
  console.log('🔍 Starting carmarket.ayvens.com scraping...')

  try {
    // Ayvens authentication credentials (hardcoded for single-user app)
    const AYVENS_USERNAME = "Pndoj"
    const AYVENS_PASSWORD = "Asdfgh,.&78"
    const BASE_URL = "https://carmarket.ayvens.com"

    // Create session for authentication
    const session = new Map<string, string>()

    // Step 1: Authenticate with Ayvens
    console.log('🔐 Authenticating with carmarket.ayvens.com...')
    const authResult = await authenticateAyvens(BASE_URL, AYVENS_USERNAME, AYVENS_PASSWORD, session)

    if (!authResult.success) {
      console.error('❌ Authentication failed:', authResult.error)
      // Return empty array if authentication fails
      return []
    }

    console.log('✅ Authentication successful')

    // Step 2: Scrape vehicle listings
    console.log('🚗 Scraping vehicle listings...')
    const vehicles = await scrapeAyvensListings(BASE_URL, session)

    console.log(`✅ Successfully scraped ${vehicles.length} vehicles from carmarket.ayvens.com`)
    return vehicles

  } catch (error) {
    console.error('❌ Error during Ayvens scraping:', error)
    return []
  }
}

async function authenticateAyvens(baseUrl: string, username: string, password: string, session: Map<string, string>): Promise<{success: boolean, error?: string}> {
  try {
    console.log('🔐 Starting Ayvens authentication process...')

    // Step 1: Get main page to establish session
    console.log('📄 Loading main page...')
    const mainPageResponse = await fetch(`${baseUrl}/`, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
      }
    })

    if (!mainPageResponse.ok) {
      console.error(`❌ Failed to load main page: ${mainPageResponse.status}`)
      return { success: false, error: `Failed to load main page: ${mainPageResponse.status}` }
    }

    // Extract cookies from response
    const cookies = mainPageResponse.headers.get('set-cookie')
    if (cookies) {
      session.set('cookies', cookies)
      console.log('🍪 Session cookies established')
    }

    // Get the HTML to look for login forms
    const html = await mainPageResponse.text()

    // Step 2: Try different authentication approaches
    console.log('🔑 Attempting authentication...')

    // Try form-based login first
    const formLoginResult = await tryFormLogin(baseUrl, username, password, session, html)
    if (formLoginResult.success) {
      return formLoginResult
    }

    // Try API-based login
    const apiLoginResult = await tryApiLogin(baseUrl, username, password, session)
    if (apiLoginResult.success) {
      return apiLoginResult
    }

    // If authentication fails, try to access protected pages anyway
    console.log('⚠️ Authentication uncertain, testing access...')
    const accessTest = await testProtectedAccess(baseUrl, session)
    if (accessTest.success) {
      console.log('✅ Access granted without explicit authentication')
      return { success: true }
    }

    return { success: false, error: 'All authentication methods failed' }

  } catch (error) {
    console.error('❌ Authentication error:', error)
    return { success: false, error: `Authentication error: ${error}` }
  }
}

async function tryFormLogin(baseUrl: string, username: string, password: string, session: Map<string, string>, html: string): Promise<{success: boolean, error?: string}> {
  try {
    // Look for login form in HTML
    const formAction = html.match(/action=["']([^"']*login[^"']*)["']/i)?.[1]
    if (!formAction) {
      return { success: false, error: 'No login form found' }
    }

    const loginUrl = formAction.startsWith('http') ? formAction : `${baseUrl}${formAction}`

    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    formData.append('email', username)

    const response = await fetch(loginUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': baseUrl,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': session.get('cookies') || ''
      },
      body: formData.toString()
    })

    if (response.ok) {
      const newCookies = response.headers.get('set-cookie')
      if (newCookies) {
        session.set('cookies', newCookies)
      }

      // Check if redirected to dashboard or success page
      if (response.url.includes('dashboard') || response.url.includes('lots') || response.url.includes('vehicles')) {
        return { success: true }
      }
    }

    return { success: false, error: 'Form login failed' }
  } catch (error) {
    return { success: false, error: `Form login error: ${error}` }
  }
}

async function tryApiLogin(baseUrl: string, username: string, password: string, session: Map<string, string>): Promise<{success: boolean, error?: string}> {
  const loginEndpoints = [
    `${baseUrl}/api/auth/login`,
    `${baseUrl}/api/login`,
    `${baseUrl}/login`,
    `${baseUrl}/auth/login`,
    `${baseUrl}/account/login`
  ]

  const loginData = {
    username: username,
    password: password,
    email: username
  }

  for (const endpoint of loginEndpoints) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'Referer': baseUrl,
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Cookie': session.get('cookies') || ''
        },
        body: JSON.stringify(loginData)
      })

      if (response.ok) {
        const responseText = await response.text()

        // Check for success indicators
        if (responseText.includes('success') || responseText.includes('dashboard') || responseText.includes('lots')) {
          const newCookies = response.headers.get('set-cookie')
          if (newCookies) {
            session.set('cookies', newCookies)
          }
          return { success: true }
        }
      }
    } catch (error) {
      console.log(`API login attempt failed for ${endpoint}:`, error)
      continue
    }
  }

  return { success: false, error: 'All API login attempts failed' }
}

async function testProtectedAccess(baseUrl: string, session: Map<string, string>): Promise<{success: boolean}> {
  try {
    const testUrls = [
      `${baseUrl}/lots`,
      `${baseUrl}/vehicles`,
      `${baseUrl}/dashboard`
    ]

    for (const url of testUrls) {
      const response = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'Cookie': session.get('cookies') || ''
        }
      })

      if (response.ok && !response.url.includes('login')) {
        return { success: true }
      }
    }

    return { success: false }
  } catch (error) {
    return { success: false }
  }
}

async function scrapeAyvensListings(baseUrl: string, session: Map<string, string>): Promise<VehicleData[]> {
  const vehicles: VehicleData[] = []

  try {
    // Common Ayvens listing page URLs
    const listingUrls = [
      `${baseUrl}/lots`,
      `${baseUrl}/en-fr/lots`,
      `${baseUrl}/vehicles`,
      `${baseUrl}/en-fr/vehicles`,
      `${baseUrl}/auction`,
      `${baseUrl}/en-fr/auction`
    ]

    for (const url of listingUrls) {
      try {
        console.log(`🔍 Checking listings at: ${url}`)

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Cookie': session.get('cookies') || ''
          }
        })

        if (!response.ok) {
          continue
        }

        const html = await response.text()

        // Parse HTML and extract vehicle data
        const pageVehicles = parseAyvensHTML(html, baseUrl)
        vehicles.push(...pageVehicles)

        console.log(`Found ${pageVehicles.length} vehicles on ${url}`)

        // If we found vehicles, we can break or continue to next page
        if (pageVehicles.length > 0) {
          break // For now, just get from first successful page
        }

      } catch (error) {
        console.log(`Error scraping ${url}:`, error)
        continue
      }
    }

  } catch (error) {
    console.error('Error in scrapeAyvensListings:', error)
  }

  return vehicles
}

function parseAyvensHTML(html: string, baseUrl: string): VehicleData[] {
  const vehicles: VehicleData[] = []

  try {
    console.log('🔍 Parsing HTML for vehicle listings...')

    // Enhanced patterns for better vehicle data extraction
    const vehicleBlockPattern = /<(?:div|article|section)[^>]*(?:class|id)="[^"]*(?:vehicle|car|listing|lot|auction)[^"]*"[^>]*>[\s\S]*?<\/(?:div|article|section)>/gi
    const pricePattern = /(?:€|EUR|£|GBP|\$|USD)\s*([0-9,]+(?:\.[0-9]{2})?)/gi
    const yearPattern = /\b(19[89]\d|20[0-2]\d)\b/g
    const mileagePattern = /([0-9,]+)\s*(?:km|miles|mi)\b/gi

    // Enhanced make/model patterns
    const makeModelPattern = /\b(BMW|Mercedes-Benz|Mercedes|Audi|Volkswagen|VW|Ford|Opel|Peugeot|Renault|Fiat|Citroen|Citroën|Skoda|Škoda|Seat|Volvo|Toyota|Honda|Nissan|Mazda|Hyundai|Kia|Porsche|Jaguar|Land Rover|Range Rover|Mini|Alfa Romeo|Lancia|Subaru|Mitsubishi|Lexus|Infiniti|Acura|Cadillac|Chevrolet|Buick|GMC|Jeep|Chrysler|Dodge|Ram|Tesla|Bentley|Rolls-Royce|Maserati|Ferrari|Lamborghini|McLaren|Aston Martin)\s+([A-Za-z0-9\-\s]+)/gi

    // Look for structured vehicle blocks first
    const vehicleBlocks = [...html.matchAll(vehicleBlockPattern)]

    if (vehicleBlocks.length > 0) {
      console.log(`📋 Found ${vehicleBlocks.length} structured vehicle blocks`)

      for (let i = 0; i < Math.min(vehicleBlocks.length, 20); i++) {
        const block = vehicleBlocks[i][0]
        const vehicle = parseVehicleBlock(block, baseUrl, i)
        if (vehicle) {
          vehicles.push(vehicle)
        }
      }
    } else {
      console.log('📄 No structured blocks found, using pattern matching...')

      // Fallback to pattern matching across entire HTML
      const priceMatches = [...html.matchAll(pricePattern)]
      const yearMatches = [...html.matchAll(yearPattern)]
      const mileageMatches = [...html.matchAll(mileagePattern)]
      const makeModelMatches = [...html.matchAll(makeModelPattern)]

      console.log(`🔢 Found patterns: ${priceMatches.length} prices, ${makeModelMatches.length} make/models`)

      const maxVehicles = Math.min(15, Math.max(priceMatches.length, makeModelMatches.length))

      for (let i = 0; i < maxVehicles; i++) {
        try {
          const price = priceMatches[i] ? parseFloat(priceMatches[i][1].replace(/,/g, '')) : null
          const year = yearMatches[i] ? parseInt(yearMatches[i][0]) : null
          const mileage = mileageMatches[i] ? parseInt(mileageMatches[i][1].replace(/,/g, '')) : null
          const makeModel = makeModelMatches[i] ? makeModelMatches[i][0].trim() : null

          let make = 'Unknown'
          let model = 'Unknown'

          if (makeModel) {
            const parts = makeModel.split(/\s+/)
            make = parts[0] || 'Unknown'
            model = parts.slice(1).join(' ').trim() || 'Unknown'

            // Clean up model name
            model = model.replace(/^\d+\.\d+\s*/, '') // Remove engine size prefix
                         .replace(/\s+/g, ' ')
                         .trim()
          }

          // Only create vehicle if we have essential data
          if (make !== 'Unknown' && price && price > 1000) {
            const vehicle: VehicleData = {
              make: make,
              model: model || 'Unknown',
              year: year,
              price: price,
              mileage: mileage,
              fuel_type: extractFuelType(html, i),
              transmission: extractTransmission(html, i),
              body_type: extractBodyType(html, i),
              city: extractCity(html, i),
              url: `${baseUrl}/lot/${Date.now()}_${i}`,
              source_website: 'carmarket.ayvens.com',
              primary_image_url: extractImageUrl(html, i, baseUrl),
              description: `${make} ${model} - ${year || 'Unknown Year'} from carmarket.ayvens.com`
            }

            vehicles.push(vehicle)
          }
        } catch (error) {
          console.log(`Error parsing vehicle ${i}:`, error)
          continue
        }
      }
    }

    console.log(`✅ Successfully parsed ${vehicles.length} vehicles`)

  } catch (error) {
    console.error('❌ Error parsing Ayvens HTML:', error)
  }

  return vehicles
}

function parseVehicleBlock(block: string, baseUrl: string, index: number): VehicleData | null {
  try {
    // Extract data from individual vehicle block
    const priceMatch = block.match(/(?:€|EUR|£|GBP|\$|USD)\s*([0-9,]+(?:\.[0-9]{2})?)/i)
    const yearMatch = block.match(/\b(19[89]\d|20[0-2]\d)\b/)
    const mileageMatch = block.match(/([0-9,]+)\s*(?:km|miles|mi)\b/i)
    const makeModelMatch = block.match(/\b(BMW|Mercedes-Benz|Mercedes|Audi|Volkswagen|VW|Ford|Opel|Peugeot|Renault|Fiat|Citroen|Citroën|Skoda|Škoda|Seat|Volvo|Toyota|Honda|Nissan|Mazda|Hyundai|Kia|Porsche|Jaguar|Land Rover|Range Rover|Mini|Alfa Romeo|Lancia|Subaru|Mitsubishi|Lexus|Infiniti|Acura|Cadillac|Chevrolet|Buick|GMC|Jeep|Chrysler|Dodge|Ram|Tesla|Bentley|Rolls-Royce|Maserati|Ferrari|Lamborghini|McLaren|Aston Martin)\s+([A-Za-z0-9\-\s]+)/i)

    const price = priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : null
    const year = yearMatch ? parseInt(yearMatch[1]) : null
    const mileage = mileageMatch ? parseInt(mileageMatch[1].replace(/,/g, '')) : null

    let make = 'Unknown'
    let model = 'Unknown'

    if (makeModelMatch) {
      make = makeModelMatch[1]
      model = makeModelMatch[2]?.trim() || 'Unknown'
    }

    if (make !== 'Unknown' && price && price > 1000) {
      return {
        make: make,
        model: model,
        year: year,
        price: price,
        mileage: mileage,
        fuel_type: extractFuelType(block, 0),
        transmission: extractTransmission(block, 0),
        body_type: extractBodyType(block, 0),
        city: extractCity(block, 0),
        url: `${baseUrl}/lot/${Date.now()}_${index}`,
        source_website: 'carmarket.ayvens.com',
        primary_image_url: extractImageUrl(block, 0, baseUrl),
        description: `${make} ${model} - ${year || 'Unknown Year'} from carmarket.ayvens.com`
      }
    }

    return null
  } catch (error) {
    console.log(`Error parsing vehicle block ${index}:`, error)
    return null
  }
}

function extractFuelType(html: string, index: number): string | undefined {
  const fuelPatterns = ['diesel', 'petrol', 'gasoline', 'electric', 'hybrid', 'gas']
  for (const fuel of fuelPatterns) {
    if (html.toLowerCase().includes(fuel)) {
      return fuel
    }
  }
  return undefined
}

function extractTransmission(html: string, index: number): string | undefined {
  if (html.toLowerCase().includes('automatic')) return 'automatic'
  if (html.toLowerCase().includes('manual')) return 'manual'
  return undefined
}

function extractBodyType(html: string, index: number): string | undefined {
  const bodyTypes = ['sedan', 'hatchback', 'suv', 'coupe', 'wagon', 'convertible', 'van']
  for (const type of bodyTypes) {
    if (html.toLowerCase().includes(type)) {
      return type
    }
  }
  return undefined
}

function extractCity(html: string, index: number): string | undefined {
  // Common European cities that might appear in Ayvens listings
  const cities = ['Rome', 'Milan', 'Naples', 'Turin', 'Florence', 'Bologna', 'Venice', 'Palermo']
  for (const city of cities) {
    if (html.includes(city)) {
      return city
    }
  }
  return undefined
}

function extractImageUrl(html: string, index: number, baseUrl: string): string | undefined {
  // Look for image URLs in the HTML
  const imgPattern = /<img[^>]+src=["']([^"']+)["'][^>]*>/gi
  const matches = [...html.matchAll(imgPattern)]

  if (matches[index]) {
    const imgSrc = matches[index][1]
    if (imgSrc.startsWith('http')) {
      return imgSrc
    } else if (imgSrc.startsWith('/')) {
      return `${baseUrl}${imgSrc}`
    }
  }

  return undefined
}
