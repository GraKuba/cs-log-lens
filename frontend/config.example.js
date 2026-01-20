// LogLens Frontend Configuration
//
// This file contains configuration that can be easily updated for different environments.
// Copy this to config.js and update with your actual values.

const CONFIG = {
    // Backend API URL
    // For local development, this will use localhost
    // For production, update with your Railway backend URL
    API_URL: window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'https://your-railway-app.railway.app', // UPDATE THIS

    // Other configuration options can be added here as needed
    // For example:
    // TIMEOUT: 30000,
    // MAX_RETRIES: 3,
};

// Export for use in app.js
window.CONFIG = CONFIG;
