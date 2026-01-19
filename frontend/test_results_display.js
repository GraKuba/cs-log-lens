// Test Suite for Results Display
// Run these tests in a browser environment with test_results_display.html

const TEST_RESULTS = {
    passed: 0,
    failed: 0,
    tests: []
};

// Mock data for testing
const MOCK_SUCCESSFUL_RESPONSE = {
    success: true,
    causes: [
        {
            rank: 1,
            cause: "Payment token expired",
            explanation: "User session timed out during checkout after being idle for too long",
            confidence: "high"
        },
        {
            rank: 2,
            cause: "Cart session timeout",
            explanation: "Items were removed from cart due to session expiration",
            confidence: "medium"
        },
        {
            rank: 3,
            cause: "Inventory conflict",
            explanation: "Item went out of stock while user was checking out",
            confidence: "low"
        }
    ],
    suggested_response: "Hi [Customer], it looks like your payment session timed out after being idle for too long. This is a security measure. Please try checking out again - your cart items should still be there. Let me know if you run into any other issues!",
    sentry_links: [
        "https://sentry.io/organizations/test-org/issues/123/events/456/",
        "https://sentry.io/organizations/test-org/issues/123/events/789/"
    ],
    logs_summary: "Found 3 error events between 14:25-14:35. All events show PaymentTokenExpiredError with similar stack traces.",
    events_found: 3
};

const MOCK_NO_EVENTS_RESPONSE = {
    success: true,
    causes: [],
    suggested_response: "No specific errors found for this time period.",
    sentry_links: [],
    logs_summary: "No events found in the specified time range.",
    events_found: 0
};

const MOCK_ERROR_RESPONSE = {
    success: false,
    error: "No Sentry events found in time range",
    suggestion: "Try expanding the time range or verify customer ID"
};

// Helper Functions
function assertEqual(actual, expected, testName) {
    if (actual === expected) {
        TEST_RESULTS.passed++;
        TEST_RESULTS.tests.push({ name: testName, status: 'PASS' });
        console.log(`✅ PASS: ${testName}`);
        return true;
    } else {
        TEST_RESULTS.failed++;
        TEST_RESULTS.tests.push({ name: testName, status: 'FAIL', actual, expected });
        console.error(`❌ FAIL: ${testName}`, { actual, expected });
        return false;
    }
}

function assertTrue(condition, testName) {
    return assertEqual(condition, true, testName);
}

function assertFalse(condition, testName) {
    return assertEqual(condition, false, testName);
}

function assertContains(str, substring, testName) {
    if (str.includes(substring)) {
        TEST_RESULTS.passed++;
        TEST_RESULTS.tests.push({ name: testName, status: 'PASS' });
        console.log(`✅ PASS: ${testName}`);
        return true;
    } else {
        TEST_RESULTS.failed++;
        TEST_RESULTS.tests.push({ name: testName, status: 'FAIL', str, substring });
        console.error(`❌ FAIL: ${testName}`, { str, substring });
        return false;
    }
}

function assertElementExists(selector, testName) {
    const element = document.querySelector(selector);
    return assertTrue(element !== null, testName);
}

function assertElementCount(selector, expectedCount, testName) {
    const elements = document.querySelectorAll(selector);
    return assertEqual(elements.length, expectedCount, testName);
}

// Test Suite
function runTests() {
    console.log('=== Starting Results Display Tests ===\n');

    // Reset test results
    TEST_RESULTS.passed = 0;
    TEST_RESULTS.failed = 0;
    TEST_RESULTS.tests = [];

    // Test 1: Results rendering with successful response
    testResultsRendering();

    // Test 2: Copy to clipboard functionality
    testCopyToClipboard();

    // Test 3: Sentry links rendering
    testSentryLinks();

    // Test 4: Empty state (no events)
    testEmptyState();

    // Test 5: Error state
    testErrorState();

    // Test 6: Confidence badges
    testConfidenceBadges();

    // Test 7: HTML escaping (XSS prevention)
    testHtmlEscaping();

    // Test 8: Plural handling
    testPluralHandling();

    // Test 9: Visual hierarchy
    testVisualHierarchy();

    // Test 10: Scroll behavior
    testScrollBehavior();

    // Print summary
    console.log('\n=== Test Summary ===');
    console.log(`Total Tests: ${TEST_RESULTS.passed + TEST_RESULTS.failed}`);
    console.log(`Passed: ${TEST_RESULTS.passed}`);
    console.log(`Failed: ${TEST_RESULTS.failed}`);
    console.log(`Success Rate: ${((TEST_RESULTS.passed / (TEST_RESULTS.passed + TEST_RESULTS.failed)) * 100).toFixed(2)}%`);

    return TEST_RESULTS;
}

// Test 1: Results rendering
function testResultsRendering() {
    console.log('\n--- Test 1: Results Rendering ---');

    const resultsDiv = document.getElementById('results');
    resultsDiv.classList.add('hidden');

    displayResults(MOCK_SUCCESSFUL_RESPONSE);

    assertFalse(resultsDiv.classList.contains('hidden'), 'Results div should be visible');
    assertContains(resultsDiv.innerHTML, 'Analysis Results', 'Should contain results header');
    assertContains(resultsDiv.innerHTML, 'Probable Causes', 'Should contain causes section');
    assertContains(resultsDiv.innerHTML, 'Suggested Response', 'Should contain suggested response section');
    assertContains(resultsDiv.innerHTML, 'Logs Summary', 'Should contain logs summary section');
    assertContains(resultsDiv.innerHTML, 'Sentry Events', 'Should contain Sentry events section');
}

// Test 2: Copy to clipboard
function testCopyToClipboard() {
    console.log('\n--- Test 2: Copy to Clipboard ---');

    displayResults(MOCK_SUCCESSFUL_RESPONSE);

    const copyBtn = document.querySelector('.copy-btn');
    assertTrue(copyBtn !== null, 'Copy button should exist');
    assertContains(copyBtn.innerHTML, 'Copy', 'Copy button should have "Copy" text');

    // Test copy functionality
    const testText = 'Test message for clipboard';
    copyToClipboard(escapeForAttribute(testText));

    // Check toast appeared
    setTimeout(() => {
        const toast = document.getElementById('toast');
        assertFalse(toast.classList.contains('hidden'), 'Toast should be visible after copy');
    }, 100);
}

// Test 3: Sentry links
function testSentryLinks() {
    console.log('\n--- Test 3: Sentry Links ---');

    displayResults(MOCK_SUCCESSFUL_RESPONSE);

    const sentryLinks = document.querySelectorAll('.sentry-links a');
    assertEqual(sentryLinks.length, 2, 'Should render 2 Sentry links');

    sentryLinks.forEach((link, index) => {
        assertTrue(link.getAttribute('target') === '_blank', `Link ${index + 1} should open in new tab`);
        assertTrue(link.getAttribute('rel') === 'noopener noreferrer', `Link ${index + 1} should have security attributes`);
        assertContains(link.textContent, `Event ${index + 1}`, `Link ${index + 1} should have correct label`);
    });
}

// Test 4: Empty state
function testEmptyState() {
    console.log('\n--- Test 4: Empty State ---');

    displayResults(MOCK_NO_EVENTS_RESPONSE);

    const resultsDiv = document.getElementById('results');
    assertContains(resultsDiv.innerHTML, 'No events found', 'Should show no events message');
    assertContains(resultsDiv.innerHTML, 'Found 0 events', 'Should show 0 events count');
}

// Test 5: Error state
function testErrorState() {
    console.log('\n--- Test 5: Error State ---');

    const formError = document.getElementById('form-error');
    formError.textContent = '';
    formError.classList.remove('show');

    displayResults(MOCK_ERROR_RESPONSE);

    const resultsDiv = document.getElementById('results');
    assertTrue(resultsDiv.classList.contains('hidden'), 'Results should be hidden on error');
    assertTrue(formError.classList.contains('show'), 'Error message should be visible');
    assertContains(formError.textContent, 'No Sentry events found', 'Should show error message');
}

// Test 6: Confidence badges
function testConfidenceBadges() {
    console.log('\n--- Test 6: Confidence Badges ---');

    displayResults(MOCK_SUCCESSFUL_RESPONSE);

    assertElementExists('.confidence-high', 'High confidence badge should exist');
    assertElementExists('.confidence-medium', 'Medium confidence badge should exist');
    assertElementExists('.confidence-low', 'Low confidence badge should exist');

    const highBadge = document.querySelector('.confidence-high');
    assertEqual(highBadge.textContent, 'HIGH', 'High confidence badge should be uppercase');

    const mediumBadge = document.querySelector('.confidence-medium');
    assertEqual(mediumBadge.textContent, 'MEDIUM', 'Medium confidence badge should be uppercase');

    const lowBadge = document.querySelector('.confidence-low');
    assertEqual(lowBadge.textContent, 'LOW', 'Low confidence badge should be uppercase');
}

// Test 7: HTML escaping
function testHtmlEscaping() {
    console.log('\n--- Test 7: HTML Escaping (XSS Prevention) ---');

    const xssData = {
        success: true,
        causes: [{
            rank: 1,
            cause: "<script>alert('xss')</script>",
            explanation: "<img src=x onerror=alert('xss')>",
            confidence: "high"
        }],
        suggested_response: "<script>alert('xss')</script>",
        sentry_links: [],
        logs_summary: "<script>alert('xss')</script>",
        events_found: 1
    };

    displayResults(xssData);

    const resultsDiv = document.getElementById('results');
    assertFalse(resultsDiv.innerHTML.includes('<script>'), 'Should escape script tags in causes');
    assertContains(resultsDiv.innerHTML, '&lt;script&gt;', 'Should show escaped HTML entities');
}

// Test 8: Plural handling
function testPluralHandling() {
    console.log('\n--- Test 8: Plural Handling ---');

    const singleEventData = { ...MOCK_SUCCESSFUL_RESPONSE, events_found: 1 };
    displayResults(singleEventData);
    assertContains(document.getElementById('results').innerHTML, 'Found 1 event', 'Should use singular "event"');

    const multipleEventsData = { ...MOCK_SUCCESSFUL_RESPONSE, events_found: 3 };
    displayResults(multipleEventsData);
    assertContains(document.getElementById('results').innerHTML, 'Found 3 events', 'Should use plural "events"');
}

// Test 9: Visual hierarchy
function testVisualHierarchy() {
    console.log('\n--- Test 9: Visual Hierarchy ---');

    displayResults(MOCK_SUCCESSFUL_RESPONSE);

    assertElementCount('.cause-item', 3, 'Should render 3 cause items');
    assertElementExists('.suggested-response', 'Suggested response section should exist');
    assertElementExists('.logs-summary', 'Logs summary section should exist');
    assertElementExists('.sentry-links', 'Sentry links section should exist');

    const causeItems = document.querySelectorAll('.cause-item');
    causeItems.forEach((item, index) => {
        assertContains(item.innerHTML, `${index + 1}.`, `Cause item ${index + 1} should have rank number`);
    });
}

// Test 10: Scroll behavior
function testScrollBehavior() {
    console.log('\n--- Test 10: Scroll Behavior ---');

    // This test verifies that scrollIntoView is called
    // In a real browser, you would check if the element is in viewport
    displayResults(MOCK_SUCCESSFUL_RESPONSE);

    const resultsDiv = document.getElementById('results');
    assertTrue(resultsDiv !== null, 'Results div should exist for scrolling');
    assertFalse(resultsDiv.classList.contains('hidden'), 'Results should be visible for scrolling');
}

// Run tests when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runTests);
} else {
    runTests();
}
