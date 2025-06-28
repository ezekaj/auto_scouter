const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 8000;

app.use(cors());
app.use(express.json());

app.get('/api/v1/health', (req, res) => {
  console.log('Health check requested');
  res.json({ status: 'ok', message: 'Test server is running!' });
});

app.get('/api/v1/cars', (req, res) => {
  console.log('Cars endpoint requested');
  res.json({
    vehicles: [
      {
        id: 'test-1',
        title: 'Test Vehicle',
        make: 'Toyota',
        model: 'Camry',
        year: 2022,
        price: 25000,
        mileage: 15000,
        fuelType: 'Gasoline',
        transmission: 'Automatic',
        location: 'Napoli, Italy',
        url: 'https://www.gruppoautouno.it/usato/test-vehicle',
        scrapedAt: new Date().toISOString(),
        source: 'gruppoautouno.it'
      }
    ],
    total: 1,
    page: 1,
    limit: 20,
    hasMore: false
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Test server running on http://localhost:${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/api/v1/health`);
  console.log(`🚗 Cars endpoint: http://localhost:${PORT}/api/v1/cars`);
});
