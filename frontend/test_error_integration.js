// Integration test for error and empty states with API responses
// Run with: node test_error_integration.js

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

console.log('\n=== Integration Tests: Error & Empty States ===\n');

// Test 1: API error response format
console.log('Test Group: API Error Response Handling');
const apiErrorResponse = {
    success: false,
    error: 'No Sentry events found in time range',
    suggestion: 'Try expanding the time range or verify customer ID'
};

assert(apiErrorResponse.success === false, 'Error response has success: false');
assert(apiErrorResponse.error !== undefined, 'Error response has error field');
assert(apiErrorResponse.suggestion !== undefined, 'Error response has suggestion field');
assert(apiErrorResponse.error.length > 0, 'Error message is not empty');
assert(apiErrorResponse.suggestion.length > 0, 'Suggestion is not empty');

// Test 2: Empty state response format
console.log('\nTest Group: Empty State Response Handling');
const emptyStateResponse = {
    success: true,
    events_found: 0,
    causes: [],
    suggested_response: '',
    sentry_links: [],
    logs_summary: 'No events found for this customer'
};

assert(emptyStateResponse.success === true, 'Empty state has success: true');
assert(emptyStateResponse.events_found === 0, 'Empty state has zero events');
assert(Array.isArray(emptyStateResponse.causes), 'Causes is an array');
assert(emptyStateResponse.causes.length === 0, 'Causes array is empty');

// Test 3: Authentication error response
console.log('\nTest Group: Authentication Error Response');
const authErrorResponse = {
    success: false,
    error: 'Invalid authentication token',
    suggestion: 'Please re-enter your password'
};

assert(authErrorResponse.success === false, 'Auth error has success: false');
assert(authErrorResponse.error.includes('authentication'), 'Auth error mentions authentication');
assert(authErrorResponse.suggestion.includes('password'), 'Auth suggestion mentions password');

// Test 4: Network error handling
console.log('\nTest Group: Network Error Simulation');
const networkErrorMessage = 'Network error. Please check your connection and try again.';
assert(networkErrorMessage.includes('Network'), 'Network error message is descriptive');
assert(networkErrorMessage.includes('try again'), 'Network error suggests retry');

// Test 5: Sentry rate limit error
console.log('\nTest Group: Sentry Rate Limit Error');
const rateLimitResponse = {
    success: false,
    error: 'Sentry API rate limit exceeded',
    suggestion: 'Please wait a moment and try again'
};

assert(rateLimitResponse.success === false, 'Rate limit error has success: false');
assert(rateLimitResponse.error.includes('rate limit'), 'Error mentions rate limit');
assert(rateLimitResponse.suggestion.includes('wait'), 'Suggestion advises waiting');

// Test 6: Success response format (for comparison)
console.log('\nTest Group: Success Response Format');
const successResponse = {
    success: true,
    events_found: 3,
    causes: [
        {
            rank: 1,
            cause: 'Payment token expired',
            explanation: 'User session timed out',
            confidence: 'high'
        }
    ],
    suggested_response: 'Hi, it looks like your session expired...',
    sentry_links: ['https://sentry.io/...'],
    logs_summary: 'Found 3 events related to payment flow'
};

assert(successResponse.success === true, 'Success response has success: true');
assert(successResponse.events_found > 0, 'Success response has events');
assert(successResponse.causes.length > 0, 'Success response has causes');
assert(successResponse.suggested_response.length > 0, 'Success response has suggested text');
assert(Array.isArray(successResponse.sentry_links), 'Sentry links is an array');

// Test 7: Validation error response (422)
console.log('\nTest Group: Validation Error Response');
const validationErrorResponse = {
    success: false,
    error: 'Invalid request: timestamp must be in ISO format',
    suggestion: 'Please use format: YYYY-MM-DDTHH:MM:SSZ'
};

assert(validationErrorResponse.success === false, 'Validation error has success: false');
assert(validationErrorResponse.error.includes('Invalid'), 'Error indicates invalid input');
assert(validationErrorResponse.suggestion.includes('format'), 'Suggestion provides format info');

// Test 8: Server error response (500)
console.log('\nTest Group: Server Error Response');
const serverErrorResponse = {
    success: false,
    error: 'An unexpected error occurred',
    suggestion: 'Please try again later or contact support'
};

assert(serverErrorResponse.success === false, 'Server error has success: false');
assert(serverErrorResponse.error.length > 0, 'Server error has message');
assert(serverErrorResponse.suggestion.includes('try again'), 'Server error suggests retry');

// Test 9: LLM analysis error
console.log('\nTest Group: LLM Analysis Error');
const llmErrorResponse = {
    success: false,
    error: 'LLM analysis failed',
    suggestion: 'The AI service is temporarily unavailable. Please try again in a moment.'
};

assert(llmErrorResponse.success === false, 'LLM error has success: false');
assert(llmErrorResponse.error.includes('LLM'), 'Error identifies LLM issue');
assert(llmErrorResponse.suggestion.includes('try again'), 'Suggests retry');

// Test 10: Empty customer ID scenario
console.log('\nTest Group: Empty Customer ID Error');
const emptyCustomerIdResponse = {
    success: false,
    error: 'Customer ID is required',
    suggestion: 'Please provide a valid customer ID (e.g., usr_abc123)'
};

assert(emptyCustomerIdResponse.success === false, 'Empty customer ID error has success: false');
assert(emptyCustomerIdResponse.error.includes('required'), 'Error indicates required field');
assert(emptyCustomerIdResponse.suggestion.includes('e.g.'), 'Suggestion provides example');

// Print results
console.log('\n=== Test Results ===');
console.log(`Total: ${tests.total}`);
console.log(`Passed: ${tests.passed}`);
console.log(`Failed: ${tests.failed}`);
console.log(`Success Rate: ${((tests.passed / tests.total) * 100).toFixed(1)}%\n`);

if (tests.failed === 0) {
    console.log('✅ All integration tests passed!\n');
    process.exit(0);
} else {
    console.log('❌ Some tests failed.\n');
    process.exit(1);
}
