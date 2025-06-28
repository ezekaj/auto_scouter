const axios = require('axios');
const cheerio = require('cheerio');
const { EventEmitter } = require('events');

class VehicleScraper extends EventEmitter {
  constructor() {
    super();
    this.baseUrl = 'https://www.gruppoautouno.it';
    this.usedCarsUrl = 'https://www.gruppoautouno.it/usato/';
    this.scrapingInterval = 5 * 60 * 1000; // 5 minutes
    this.isRunning = false;
    this.knownVehicles = new Set();
  }

  async scrapeVehicleList(page = 1) {
    try {
      const url = page === 1 ? this.usedCarsUrl : `${this.usedCarsUrl}page/${page}/`;
      console.log(`Scraping page ${page}: ${url}`);
      
      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
          'Accept-Encoding': 'gzip, deflate, br',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1',
        },
        timeout: 30000
      });

      const $ = cheerio.load(response.data);
      const vehicles = [];

      // Parse vehicle listings
      $('.usato-item, .vehicle-card, [class*="vehicle"], [class*="car"]').each((index, element) => {
        try {
          const vehicle = this.parseVehicleElement($, element);
          if (vehicle && vehicle.id) {
            vehicles.push(vehicle);
          }
        } catch (error) {
          console.error('Error parsing vehicle element:', error);
        }
      });

      // Alternative parsing if main selector doesn't work
      if (vehicles.length === 0) {
        $('a[href*="/usato/"]').each((index, element) => {
          try {
            const vehicle = this.parseVehicleLink($, element);
            if (vehicle && vehicle.id) {
              vehicles.push(vehicle);
            }
          } catch (error) {
            console.error('Error parsing vehicle link:', error);
          }
        });
      }

      console.log(`Found ${vehicles.length} vehicles on page ${page}`);
      return vehicles;
    } catch (error) {
      console.error(`Error scraping page ${page}:`, error.message);
      return [];
    }
  }

  parseVehicleElement($, element) {
    const $el = $(element);
    const link = $el.find('a').first().attr('href') || $el.attr('href');
    
    if (!link || !link.includes('/usato/')) {
      return null;
    }

    const fullUrl = link.startsWith('http') ? link : `${this.baseUrl}${link}`;
    const id = this.extractVehicleId(link);
    
    const title = $el.find('h3, h2, .title, [class*="title"]').text().trim() ||
                  $el.find('img').attr('alt') || '';
    
    const priceText = $el.find('[class*="price"], .price, [data-price]').text().trim();
    const price = this.extractPrice(priceText);
    
    const year = this.extractYear($el.text());
    const mileage = this.extractMileage($el.text());
    
    // Extract make and model from title
    const { make, model } = this.extractMakeModel(title);
    
    // Extract additional details
    const transmission = this.extractTransmission($el.text());
    const fuelType = this.extractFuelType($el.text());
    
    const imageUrl = $el.find('img').first().attr('src') || 
                     $el.find('img').first().attr('data-src') || '';

    return {
      id,
      title: title || `${make} ${model}`.trim(),
      make,
      model,
      year,
      price,
      mileage,
      transmission,
      fuelType,
      url: fullUrl,
      imageUrl: imageUrl.startsWith('http') ? imageUrl : `${this.baseUrl}${imageUrl}`,
      location: 'Napoli, Italy', // Gruppo Auto Uno location
      bodyType: this.extractBodyType(title),
      scrapedAt: new Date().toISOString(),
      source: 'gruppoautouno.it'
    };
  }

  parseVehicleLink($, element) {
    const $el = $(element);
    const link = $el.attr('href');
    
    if (!link || !link.includes('/usato/')) {
      return null;
    }

    const fullUrl = link.startsWith('http') ? link : `${this.baseUrl}${link}`;
    const id = this.extractVehicleId(link);
    
    // Get text content from the link and surrounding elements
    const linkText = $el.text().trim();
    const parentText = $el.parent().text().trim();
    const combinedText = `${linkText} ${parentText}`;
    
    const { make, model } = this.extractMakeModel(linkText);
    const price = this.extractPrice(combinedText);
    const year = this.extractYear(combinedText);
    const mileage = this.extractMileage(combinedText);
    const transmission = this.extractTransmission(combinedText);
    const fuelType = this.extractFuelType(combinedText);

    return {
      id,
      title: linkText || `${make} ${model}`.trim(),
      make,
      model,
      year,
      price,
      mileage,
      transmission,
      fuelType,
      url: fullUrl,
      imageUrl: '',
      location: 'Napoli, Italy',
      bodyType: this.extractBodyType(linkText),
      scrapedAt: new Date().toISOString(),
      source: 'gruppoautouno.it'
    };
  }

  extractVehicleId(url) {
    // Extract ID from URL like /usato/citroen-c3-4/ or /usato/volkswagen-t-roc-14/
    const match = url.match(/\/usato\/([^\/]+)\/?$/);
    return match ? match[1] : url.split('/').pop() || Math.random().toString(36).substr(2, 9);
  }

  extractMakeModel(text) {
    const cleanText = text.toLowerCase().trim();
    
    // Common Italian car makes
    const makes = [
      'volkswagen', 'peugeot', 'citroen', 'opel', 'fiat', 'bmw', 'audi', 'mercedes', 'mercedes-benz',
      'ford', 'renault', 'toyota', 'honda', 'nissan', 'hyundai', 'kia', 'mazda', 'subaru',
      'jeep', 'alfa romeo', 'lancia', 'maserati', 'ferrari', 'lamborghini', 'mini', 'skoda',
      'seat', 'cupra', 'mg', 'ssangyong', 'dacia', 'suzuki', 'mitsubishi', 'lexus', 'infiniti'
    ];
    
    let make = '';
    let model = '';
    
    for (const brand of makes) {
      if (cleanText.includes(brand)) {
        make = brand.charAt(0).toUpperCase() + brand.slice(1);
        // Extract model after the make
        const afterMake = cleanText.split(brand)[1];
        if (afterMake) {
          model = afterMake.trim().split(' ')[0];
          if (model) {
            model = model.charAt(0).toUpperCase() + model.slice(1);
          }
        }
        break;
      }
    }
    
    return { make, model };
  }

  extractPrice(text) {
    const priceMatch = text.match(/€\s*([0-9.,]+)/);
    if (priceMatch) {
      return parseInt(priceMatch[1].replace(/[.,]/g, ''));
    }
    return null;
  }

  extractYear(text) {
    const yearMatch = text.match(/\b(19|20)\d{2}\b/);
    return yearMatch ? parseInt(yearMatch[0]) : null;
  }

  extractMileage(text) {
    const kmMatch = text.match(/(\d+[.,]?\d*)\s*km/i);
    if (kmMatch) {
      return parseInt(kmMatch[1].replace(/[.,]/g, ''));
    }
    return null;
  }

  extractTransmission(text) {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('automatico') || lowerText.includes('auto') || lowerText.includes('dsg') || lowerText.includes('eat')) {
      return 'Automatic';
    } else if (lowerText.includes('manuale')) {
      return 'Manual';
    }
    return 'Unknown';
  }

  extractFuelType(text) {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('diesel')) return 'Diesel';
    if (lowerText.includes('benzina') || lowerText.includes('petrol')) return 'Gasoline';
    if (lowerText.includes('elettric') || lowerText.includes('electric')) return 'Electric';
    if (lowerText.includes('ibrido') || lowerText.includes('hybrid')) return 'Hybrid';
    if (lowerText.includes('gpl')) return 'LPG';
    if (lowerText.includes('metano') || lowerText.includes('cng')) return 'CNG';
    return 'Unknown';
  }

  extractBodyType(text) {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('suv')) return 'SUV';
    if (lowerText.includes('station') || lowerText.includes('wagon')) return 'Station Wagon';
    if (lowerText.includes('coupe')) return 'Coupe';
    if (lowerText.includes('cabrio') || lowerText.includes('convertible')) return 'Convertible';
    if (lowerText.includes('van') || lowerText.includes('commerciale')) return 'Van';
    return 'Sedan';
  }

  async scrapeAllPages() {
    const allVehicles = [];
    let page = 1;
    let hasMorePages = true;

    while (hasMorePages && page <= 10) { // Limit to 10 pages to avoid infinite loops
      const vehicles = await this.scrapeVehicleList(page);
      
      if (vehicles.length === 0) {
        hasMorePages = false;
      } else {
        allVehicles.push(...vehicles);
        page++;
        
        // Add delay between requests to be respectful
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    return allVehicles;
  }

  async startMonitoring() {
    if (this.isRunning) {
      console.log('Vehicle monitoring is already running');
      return;
    }

    this.isRunning = true;
    console.log('Starting vehicle monitoring...');

    // Initial scrape
    await this.performScrape();

    // Set up periodic scraping
    this.intervalId = setInterval(async () => {
      await this.performScrape();
    }, this.scrapingInterval);

    console.log(`Vehicle monitoring started. Checking every ${this.scrapingInterval / 1000 / 60} minutes.`);
  }

  async performScrape() {
    try {
      console.log('Performing vehicle scrape...');
      const vehicles = await this.scrapeAllPages();
      
      const newVehicles = vehicles.filter(vehicle => !this.knownVehicles.has(vehicle.id));
      
      if (newVehicles.length > 0) {
        console.log(`Found ${newVehicles.length} new vehicles`);
        
        // Add new vehicles to known set
        newVehicles.forEach(vehicle => this.knownVehicles.add(vehicle.id));
        
        // Emit event for new vehicles
        this.emit('newVehicles', newVehicles);
      } else {
        console.log('No new vehicles found');
      }
      
      // Emit event for all vehicles (for initial load or full refresh)
      this.emit('allVehicles', vehicles);
      
    } catch (error) {
      console.error('Error during vehicle scrape:', error);
      this.emit('error', error);
    }
  }

  stopMonitoring() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isRunning = false;
    console.log('Vehicle monitoring stopped');
  }
}

module.exports = VehicleScraper;
