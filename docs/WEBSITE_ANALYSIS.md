# GruppoAutoUno.it Website Analysis Report

## Website Overview
- **Target URL**: https://gruppoautouno.it/usato
- **Type**: Automotive dealership website (WordPress-based)
- **Location**: Naples, Italy (Napoli)
- **Primary Business**: Used car sales with multiple brands

## Robots.txt Analysis
- **Status**: ✅ Scraping Allowed
- **Key Findings**:
  - General scraping allowed: `User-agent: * Allow: /`
  - No specific restrictions on `/usato` section
  - Standard WordPress restrictions (wp-admin, xmlrpc.php)
  - Sitemap available: `https://www.gruppoautouno.it/usato-sitemap.xml`

## Website Structure

### Main Listing Page (`/usato`)
- **Total Vehicles**: 185 vehicles (as of analysis)
- **Pagination**: "Mostra altri risultati" button (Load More pattern)
- **Filters Available**:
  - Brand (Volkswagen, Peugeot, Opel, Citroën, etc.)
  - Vehicle Type
  - Fuel Type (Alimentazione)
  - Transmission (Cambio)
  - Category
  - Year (Anno)
  - Price (Prezzo)

### Individual Listing Structure
**URL Pattern**: `/usato/{brand-model-id}/`
**Example**: `/usato/citroen-c3-4/`

## Data Fields Available

### Vehicle Identification
- **Make**: Citroen, Volkswagen, Peugeot, etc.
- **Model**: C3, T-Roc, 2008, etc.
- **Full Title**: "C3 1.2 puretech Shine s&s 110cv eat6"
- **Listing ID**: Found in URL and image paths (e.g., 4782228)

### Pricing Information
- **Listed Price**: €16.390 format
- **Currency**: Euro (€)
- **Price Display**: Clear pricing on both listing and detail pages

### Technical Specifications
- **Registration Date**: "02/2024" (Immatricolazione)
- **Mileage**: "23.398" km
- **Fuel Type**: Benzina (Gasoline), Diesel
- **Transmission**: Automatico, Manuale
- **Engine Power**: "81 kW"
- **Displacement**: "1.199" cc
- **Doors**: "5 Porte"
- **Seats**: "5 Posti"
- **Cylinders**: "3 Cilindri"
- **Gears**: "6 Marce"

### Vehicle Features
- **Equipment List**: ABS, Vetri elettrici, Chiusura centralizzata, etc.
- **Safety Features**: ESP, Assistenza alla frenata, etc.
- **Comfort Features**: Cruise control, Computer di bordo, etc.

### Media Assets
- **Image URLs**: High-resolution images in `/wp-content/uploads/usato/{id}/` directory
- **Image Format**: JPG files with descriptive names
- **Multiple Views**: Exterior, interior, detail shots

### Location & Contact
- **Dealer**: Autouno Group
- **Location**: Naples (Napoli), Avellino
- **Phone**: 0817593700
- **WhatsApp**: Available

## Technical Implementation

### Frontend Technology
- **CMS**: WordPress
- **JavaScript**: Lazy loading for images
- **CSS Framework**: Custom styling
- **Image Optimization**: SVG placeholders with lazy loading

### Data Loading Patterns
- **Initial Load**: First set of vehicles
- **Pagination**: "Load More" button for additional results
- **Filtering**: AJAX-based filtering system
- **Search**: Model search functionality

### Anti-Scraping Measures
- **Rate Limiting**: Not immediately apparent
- **CAPTCHA**: None detected
- **IP Blocking**: Not observed
- **JavaScript Dependency**: Minimal for basic data extraction

## Scraping Strategy Recommendations

### Approach
1. **Static Scraping**: BeautifulSoup + Requests sufficient for basic data
2. **Dynamic Scraping**: Selenium/Playwright for pagination and filtering
3. **Hybrid Approach**: Static for individual pages, dynamic for navigation

### Rate Limiting
- **Recommended Delay**: 2-3 seconds between requests
- **Concurrent Requests**: Max 1-2 simultaneous
- **User-Agent Rotation**: Recommended
- **Session Management**: Use session cookies

### Data Extraction Points
1. **Listing Page**: Vehicle cards with basic info
2. **Detail Pages**: Complete vehicle specifications
3. **Image Gallery**: High-resolution photos
4. **Contact Information**: Dealer details

### Pagination Handling
- **Method**: Click "Mostra altri risultati" button
- **Detection**: Monitor for new vehicle cards
- **Termination**: When no more results load

## Compliance Considerations

### Legal Compliance
- **Robots.txt**: ✅ Compliant
- **Rate Limiting**: Implement conservative delays
- **Data Usage**: Public listing information only
- **Attribution**: Consider dealer attribution

### Ethical Guidelines
- **Respect Server Resources**: Implement delays
- **Data Accuracy**: Verify extracted information
- **Update Frequency**: Reasonable scraping intervals
- **Error Handling**: Graceful failure management

## Data Quality Assessment

### Completeness
- **High**: Price, basic specs, images
- **Medium**: Detailed features, equipment
- **Variable**: VIN numbers (not always visible)

### Consistency
- **Format**: Standardized across listings
- **Language**: Italian
- **Currency**: Euro
- **Units**: Metric system

### Reliability
- **Source**: Official dealer website
- **Updates**: Regular inventory updates
- **Accuracy**: Professional listing standards

## Recommended Scraping Schedule
- **Frequency**: Every 8-12 hours
- **Peak Avoidance**: Avoid business hours (9 AM - 6 PM CET)
- **Weekend Consideration**: Lower activity periods
- **Monitoring**: Track inventory changes
