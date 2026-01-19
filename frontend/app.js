// LogLens Frontend Application
// This file handles authentication, form submission, and results display

// Configuration
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-railway-app.railway.app'; // Will be updated during deployment

// State Management
const state = {
    authToken: null,
    isAuthenticated: false,
    isLoading: false
};

// DOM Elements
const elements = {
    authScreen: null,
    analysisScreen: null,
    authForm: null,
    authError: null,
    analysisForm: null,
    formError: null,
    results: null,
    loading: null,
    analyzeBtn: null
};

// Initialize the application
function init() {
    // Cache DOM elements
    elements.authScreen = document.getElementById('auth-screen');
    elements.analysisScreen = document.getElementById('analysis-screen');
    elements.authForm = document.getElementById('auth-form');
    elements.authError = document.getElementById('auth-error');
    elements.analysisForm = document.getElementById('analysis-form');
    elements.formError = document.getElementById('form-error');
    elements.results = document.getElementById('results');
    elements.loading = document.getElementById('loading');
    elements.analyzeBtn = document.getElementById('analyze-btn');

    // Check for stored auth token
    const storedToken = localStorage.getItem('loglens_auth_token');
    if (storedToken) {
        state.authToken = storedToken;
        state.isAuthenticated = true;
        showAnalysisScreen();
    } else {
        showAuthScreen();
    }

    // Setup event listeners
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    elements.authForm.addEventListener('submit', handleAuth);
    elements.analysisForm.addEventListener('submit', handleAnalysis);
}

// Show authentication screen
function showAuthScreen() {
    elements.authScreen.classList.remove('hidden');
    elements.analysisScreen.classList.add('hidden');
}

// Show analysis screen
function showAnalysisScreen() {
    elements.authScreen.classList.add('hidden');
    elements.analysisScreen.classList.remove('hidden');
}

// Handle authentication
async function handleAuth(event) {
    event.preventDefault();

    const password = document.getElementById('password').value;

    // Store the password as auth token
    state.authToken = password;
    localStorage.setItem('loglens_auth_token', password);

    // Clear any previous errors
    hideError(elements.authError);

    // Show analysis screen
    state.isAuthenticated = true;
    showAnalysisScreen();
}

// Handle analysis form submission
async function handleAnalysis(event) {
    event.preventDefault();

    if (state.isLoading) return;

    // Get form data
    const description = document.getElementById('description').value;
    const timestamp = document.getElementById('timestamp').value;
    const customerId = document.getElementById('customer_id').value;

    // Convert timestamp to ISO format
    const isoTimestamp = new Date(timestamp).toISOString();

    // Prepare request payload
    const payload = {
        description,
        timestamp: isoTimestamp,
        customer_id: customerId
    };

    // Show loading state
    setLoadingState(true);
    hideError(elements.formError);
    elements.results.classList.add('hidden');

    try {
        // Make API request
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Token': state.authToken
            },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            // Authentication failed - clear token and go back to auth screen
            handleAuthFailure();
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            // Handle error response
            showError(elements.formError, data.error || 'Analysis failed. Please try again.');
            return;
        }

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('Analysis error:', error);
        showError(elements.formError, 'Network error. Please check your connection and try again.');
    } finally {
        setLoadingState(false);
    }
}

// Handle authentication failure
function handleAuthFailure() {
    // Clear stored token
    localStorage.removeItem('loglens_auth_token');
    state.authToken = null;
    state.isAuthenticated = false;

    // Show auth screen with error
    showAuthScreen();
    showError(elements.authError, 'Invalid password. Please try again.');

    // Reset loading state
    setLoadingState(false);
}

// Set loading state
function setLoadingState(isLoading) {
    state.isLoading = isLoading;

    if (isLoading) {
        elements.loading.classList.remove('hidden');
        elements.analyzeBtn.disabled = true;
        elements.analyzeBtn.textContent = 'Analyzing...';
    } else {
        elements.loading.classList.add('hidden');
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.textContent = 'Analyze Logs';
    }
}

// Display analysis results
function displayResults(data) {
    if (!data.success) {
        // Handle error response with suggestion
        const errorMessage = data.error || 'Analysis failed';
        const suggestion = data.suggestion || 'Please try again.';
        showErrorWithSuggestion(errorMessage, suggestion);
        return;
    }

    // Check for empty state (no events found)
    if (data.events_found === 0) {
        showEmptyState();
        return;
    }

    // Build results HTML
    let html = '<h3><span class="material-symbols-outlined results-icon">analytics</span> Analysis Results</h3>';

    // Display probable causes
    if (data.causes && data.causes.length > 0) {
        html += '<div class="causes-section results-section">';
        html += '<h4>Probable Causes</h4>';
        data.causes.forEach(cause => {
            const confidenceClass = `confidence-${cause.confidence.toLowerCase()}`;
            html += `
                <div class="cause-item">
                    <div>
                        <strong>${cause.rank}. ${escapeHtml(cause.cause)}</strong>
                        <span class="confidence-badge ${confidenceClass}">${cause.confidence.toUpperCase()}</span>
                    </div>
                    <p>${escapeHtml(cause.explanation)}</p>
                </div>
            `;
        });
        html += '</div>';
    }

    // Display suggested response with copy button
    if (data.suggested_response) {
        html += `
            <div class="suggested-response results-section">
                <h4>
                    <span>Suggested Response</span>
                    <button class="copy-btn" onclick="copyToClipboard('${escapeForAttribute(data.suggested_response)}')">
                        📋 Copy
                    </button>
                </h4>
                <div class="suggested-response-text">${escapeHtml(data.suggested_response)}</div>
            </div>
        `;
    }

    // Display logs summary
    if (data.logs_summary) {
        html += `
            <div class="logs-summary results-section">
                <h4>Logs Summary</h4>
                <p>${escapeHtml(data.logs_summary)}</p>
                ${data.events_found !== undefined ? `<p class="events-count">Found ${data.events_found} event${data.events_found !== 1 ? 's' : ''}</p>` : ''}
            </div>
        `;
    }

    // Display Sentry links
    if (data.sentry_links && data.sentry_links.length > 0) {
        html += '<div class="sentry-links results-section">';
        html += '<h4>Sentry Events</h4>';
        html += '<ul>';
        data.sentry_links.forEach((link, index) => {
            html += `<li><a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">Event ${index + 1}</a></li>`;
        });
        html += '</ul></div>';
    }

    elements.results.innerHTML = html;
    elements.results.classList.remove('hidden');

    // Scroll to results
    elements.results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Copy to clipboard function
function copyToClipboard(text) {
    // Decode HTML entities and unescape attribute-escaped text
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    const decodedText = textarea.value;

    navigator.clipboard.writeText(decodedText).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = decodedText;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('Copied to clipboard!');
        } catch (err) {
            showToast('Failed to copy');
        }
        document.body.removeChild(textArea);
    });
}

// Show toast notification
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Escape text for use in HTML attributes
function escapeForAttribute(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/'/g, '&#39;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '&#10;')
        .replace(/\r/g, '');
}

// Show error message
function showError(element, message) {
    element.textContent = message;
    element.classList.add('show');
}

// Hide error message
function hideError(element) {
    element.textContent = '';
    element.classList.remove('show');
}

// Show error message with actionable suggestion
function showErrorWithSuggestion(errorMessage, suggestion) {
    const html = `
        <div class="error-state">
            <span class="material-symbols-outlined error-icon">error</span>
            <h3>Analysis Error</h3>
            <p class="error-text">${escapeHtml(errorMessage)}</p>
            <p class="error-suggestion"><strong>Suggestion:</strong> ${escapeHtml(suggestion)}</p>
            <button class="btn btn-primary retry-btn" onclick="retryAnalysis()">
                <span class="material-symbols-outlined btn-icon">refresh</span>
                Try Again
            </button>
        </div>
    `;

    elements.results.innerHTML = html;
    elements.results.classList.remove('hidden');
    elements.results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Show empty state when no events found
function showEmptyState() {
    const html = `
        <div class="empty-state">
            <span class="material-symbols-outlined empty-icon">search_off</span>
            <h3>No Events Found</h3>
            <p class="empty-text">We couldn't find any Sentry events matching the provided criteria.</p>
            <div class="empty-suggestions">
                <p><strong>Here's what you can try:</strong></p>
                <ul>
                    <li>Widen the time range by adjusting the timestamp</li>
                    <li>Verify the customer ID is correct</li>
                    <li>Check that events exist in Sentry for this customer</li>
                    <li>Ensure the customer ID format matches your system (e.g., usr_abc123)</li>
                </ul>
            </div>
            <button class="btn btn-primary retry-btn" onclick="retryAnalysis()">
                <span class="material-symbols-outlined btn-icon">refresh</span>
                Adjust & Try Again
            </button>
        </div>
    `;

    elements.results.innerHTML = html;
    elements.results.classList.remove('hidden');
    elements.results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Retry analysis - clears results and focuses on form
function retryAnalysis() {
    elements.results.classList.add('hidden');
    hideError(elements.formError);
    document.getElementById('description').focus();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
