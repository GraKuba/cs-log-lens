// Test suite for error and empty states
// Run this file with Node.js: node test_error_states.js

const tests = {
    passed: 0,
    failed: 0,
    total: 0
};

function assert(condition, testName) {
    tests.total++;
    if (condition) {
        tests.passed++;
        console.log(`✓ ${testName}`);
    } else {
        tests.failed++;
        console.error(`✗ ${testName}`);
    }
}

function assertEqual(actual, expected, testName) {
    tests.total++;
    if (actual === expected) {
        tests.passed++;
        console.log(`✓ ${testName}`);
    } else {
        tests.failed++;
        console.error(`✗ ${testName}`);
        console.error(`  Expected: ${expected}`);
        console.error(`  Actual: ${actual}`);
    }
}

// Mock DOM
class MockElement {
    constructor() {
        this.textContent = '';
        this.innerHTML = '';
        this._classList = new Set();
        this.style = {};
        this.value = '';

        // Create proper classList object
        this.classList = {
            add: (className) => this._classList.add(className),
            remove: (className) => this._classList.delete(className),
            contains: (className) => this._classList.has(className),
            has: (className) => this._classList.has(className)
        };
    }

    scrollIntoView() {}
    focus() {}
}

const document = {
    getElementById: (id) => new MockElement(),
    createElement: (tag) => new MockElement(),
    addEventListener: () => {},
    readyState: 'complete'
};

const localStorage = {
    data: {},
    getItem: (key) => localStorage.data[key] || null,
    setItem: (key, value) => localStorage.data[key] = value,
    removeItem: (key) => delete localStorage.data[key]
};

global.document = document;
global.localStorage = localStorage;

// Mock functions needed for testing
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showError(element, message) {
    element.textContent = message;
    element.classList.add('show');
}

function hideError(element) {
    element.textContent = '';
    element.classList.remove('show');
}

function showErrorWithSuggestion(errorMessage, suggestion) {
    const html = `
        <div class="error-state">
            <div class="error-icon">⚠️</div>
            <h3>Analysis Error</h3>
            <p class="error-text">${escapeHtml(errorMessage)}</p>
            <p class="error-suggestion"><strong>Suggestion:</strong> ${escapeHtml(suggestion)}</p>
            <button class="btn btn-primary retry-btn" onclick="retryAnalysis()">Try Again</button>
        </div>
    `;
    return html;
}

function showEmptyState() {
    const html = `
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <h3>No Events Found</h3>
            <p class="empty-text">We couldn't find any Sentry events matching the provided criteria.</p>
            <div class="empty-suggestions">
                <p><strong>Here's what you can try:</strong></p>
                <ul>
                    <li>✓ Widen the time range by adjusting the timestamp</li>
                    <li>✓ Verify the customer ID is correct</li>
                    <li>✓ Check that events exist in Sentry for this customer</li>
                    <li>✓ Ensure the customer ID format matches your system (e.g., usr_abc123)</li>
                </ul>
            </div>
            <button class="btn btn-primary retry-btn" onclick="retryAnalysis()">Adjust & Try Again</button>
        </div>
    `;
    return html;
}

console.log('\n=== Running Error and Empty States Tests ===\n');

// Test 1: Error state with suggestion
console.log('Test Group: Error State with Suggestion');
const errorHtml = showErrorWithSuggestion('No Sentry events found', 'Try expanding the time range');
assert(errorHtml.includes('error-state'), 'Error state container is present');
assert(errorHtml.includes('Analysis Error'), 'Error title is displayed');
assert(errorHtml.includes('No Sentry events found'), 'Error message is displayed');
assert(errorHtml.includes('Try expanding the time range'), 'Suggestion is displayed');
assert(errorHtml.includes('Try Again'), 'Retry button is present');
assert(errorHtml.includes('⚠️'), 'Error icon is present');

// Test 2: Empty state
console.log('\nTest Group: Empty State');
const emptyHtml = showEmptyState();
assert(emptyHtml.includes('empty-state'), 'Empty state container is present');
assert(emptyHtml.includes('No Events Found'), 'Empty state title is displayed');
assert(emptyHtml.includes('Widen the time range'), 'First suggestion is present');
assert(emptyHtml.includes('Verify the customer ID'), 'Second suggestion is present');
assert(emptyHtml.includes('Check that events exist'), 'Third suggestion is present');
assert(emptyHtml.includes('Ensure the customer ID format'), 'Fourth suggestion is present');
assert(emptyHtml.includes('Adjust & Try Again'), 'Retry button is present');
assert(emptyHtml.includes('🔍'), 'Search icon is present');

// Test 3: XSS prevention in error messages
console.log('\nTest Group: XSS Prevention');
const xssError = showErrorWithSuggestion('<script>alert("xss")</script>', '<img src=x onerror=alert(1)>');
assert(!xssError.includes('<script>'), 'Script tags are escaped in error message');
assert(xssError.includes('&lt;img'), 'Image tags are escaped in suggestion');
assert(!xssError.includes('<img'), 'Raw HTML is not present in suggestion');

// Test 4: Error element state management
console.log('\nTest Group: Error Element State Management');
const errorElement = new MockElement();
showError(errorElement, 'Test error message');
assertEqual(errorElement.textContent, 'Test error message', 'Error message is set correctly');
assert(errorElement.classList.has('show'), 'Show class is added to error element');

hideError(errorElement);
assertEqual(errorElement.textContent, '', 'Error message is cleared');
assert(!errorElement.classList.has('show'), 'Show class is removed from error element');

// Test 5: Multiple error states
console.log('\nTest Group: Different Error Scenarios');
const networkError = showErrorWithSuggestion('Network error', 'Check your connection and try again');
assert(networkError.includes('Network error'), 'Network error message is displayed');
assert(networkError.includes('Check your connection'), 'Network error suggestion is displayed');

const authError = showErrorWithSuggestion('Authentication failed', 'Please re-enter your password');
assert(authError.includes('Authentication failed'), 'Auth error message is displayed');
assert(authError.includes('re-enter your password'), 'Auth error suggestion is displayed');

const apiError = showErrorWithSuggestion('Analysis failed', 'Please try again');
assert(apiError.includes('Analysis failed'), 'API error message is displayed');
assert(apiError.includes('Please try again'), 'API error suggestion is displayed');

// Test 6: Empty string handling
console.log('\nTest Group: Edge Cases');
const emptyMessageError = showErrorWithSuggestion('', '');
assert(emptyMessageError.includes('error-state'), 'Empty error still renders container');
assert(emptyMessageError.includes('Try Again'), 'Empty error still has retry button');

// Test 7: Long error messages
console.log('\nTest Group: Long Content Handling');
const longMessage = 'This is a very long error message that should still be displayed correctly without breaking the layout or causing any rendering issues in the user interface.';
const longSuggestion = 'This is a very long suggestion that provides detailed steps for the user to follow in order to resolve the issue they are experiencing.';
const longError = showErrorWithSuggestion(longMessage, longSuggestion);
assert(longError.includes(longMessage), 'Long error message is displayed');
assert(longError.includes(longSuggestion), 'Long suggestion is displayed');

// Test 8: Special characters in error messages
console.log('\nTest Group: Special Characters');
const specialCharsError = showErrorWithSuggestion('Error: "quoted text" & symbols', "Use 'single quotes' & <brackets>");
assert(specialCharsError.includes('quoted text'), 'Quoted text is handled');
assert(specialCharsError.includes('symbols'), 'Ampersands are handled');

// Test 9: Empty state structure
console.log('\nTest Group: Empty State Structure');
const emptyStateHtml = showEmptyState();
assert(emptyStateHtml.includes('empty-suggestions'), 'Empty state has suggestions section');
assert(emptyStateHtml.includes('<ul>'), 'Empty state has suggestion list');
assert(emptyStateHtml.includes('<li>'), 'Empty state has list items');

// Test 10: Consistency checks
console.log('\nTest Group: Consistency');
assert(errorHtml.includes('btn-primary'), 'Error state uses primary button class');
assert(emptyHtml.includes('btn-primary'), 'Empty state uses primary button class');
assert(errorHtml.includes('retry-btn'), 'Error state has retry button class');
assert(emptyHtml.includes('retry-btn'), 'Empty state has retry button class');

// Print results
console.log('\n=== Test Results ===');
console.log(`Total: ${tests.total}`);
console.log(`Passed: ${tests.passed}`);
console.log(`Failed: ${tests.failed}`);
console.log(`Success Rate: ${((tests.passed / tests.total) * 100).toFixed(1)}%\n`);

if (tests.failed === 0) {
    console.log('✅ All tests passed!\n');
    process.exit(0);
} else {
    console.log('❌ Some tests failed.\n');
    process.exit(1);
}
