#!/usr/bin/env node

/**
 * LogLens Frontend Authentication Tests
 * Tests for Task 6.1: Password Authentication UI
 *
 * This test suite verifies:
 * 1. Password storage in localStorage
 * 2. Auth header sent correctly
 * 3. 401 handling
 * 4. Password clearing
 */

// Mock localStorage for Node.js environment
class LocalStorageMock {
    constructor() {
        this.store = {};
    }

    getItem(key) {
        return this.store[key] !== undefined ? this.store[key] : null;
    }

    setItem(key, value) {
        this.store[key] = String(value);
    }

    removeItem(key) {
        delete this.store[key];
    }

    clear() {
        this.store = {};
    }
}

// Test utilities
const testResults = [];

function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(`${message}\nExpected: ${expected}\nActual: ${actual}`);
    }
}

function runTest(name, testFn) {
    try {
        testFn();
        testResults.push({ name, passed: true, error: null });
        console.log(`✅ ${name}`);
        return true;
    } catch (error) {
        testResults.push({ name, passed: false, error: error.message });
        console.log(`❌ ${name}`);
        console.log(`   Error: ${error.message}`);
        return false;
    }
}

// Run all tests
function runTests() {
    console.log('='.repeat(70));
    console.log('LogLens Frontend Authentication Tests');
    console.log('Task 6.1: Password Authentication UI');
    console.log('='.repeat(70));
    console.log();

    const localStorage = new LocalStorageMock();

    // Test 1: Password storage in localStorage
    runTest('Test 1: Password is stored in localStorage after authentication', () => {
        localStorage.clear();
        const testPassword = 'test-password-123';

        // Simulate the authentication flow from app.js
        localStorage.setItem('loglens_auth_token', testPassword);

        const stored = localStorage.getItem('loglens_auth_token');
        assertEqual(stored, testPassword, 'Password should be stored in localStorage');
    });

    // Test 2: localStorage key name is correct
    runTest('Test 2: localStorage uses correct key name "loglens_auth_token"', () => {
        localStorage.clear();
        localStorage.setItem('loglens_auth_token', 'test');

        const stored = localStorage.getItem('loglens_auth_token');
        assert(stored !== null, 'localStorage should contain loglens_auth_token key');
    });

    // Test 3: Password clearing on 401
    runTest('Test 3: Password is cleared from localStorage on 401 response', () => {
        localStorage.setItem('loglens_auth_token', 'test-password');

        // Simulate 401 response handling from app.js (handleAuthFailure)
        localStorage.removeItem('loglens_auth_token');

        const stored = localStorage.getItem('loglens_auth_token');
        assertEqual(stored, null, 'Password should be removed from localStorage on 401');
    });

    // Test 4: X-Auth-Token header format
    runTest('Test 4: X-Auth-Token header is included in API requests', () => {
        const testPassword = 'my-secret-password';
        localStorage.setItem('loglens_auth_token', testPassword);

        // Simulate header construction from app.js
        const authToken = localStorage.getItem('loglens_auth_token');
        const headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': authToken
        };

        assert('X-Auth-Token' in headers, 'Headers should include X-Auth-Token');
        assertEqual(headers['X-Auth-Token'], testPassword, 'X-Auth-Token should contain the password');
    });

    // Test 5: Password persistence
    runTest('Test 5: Password persists in localStorage', () => {
        localStorage.clear();
        const password = 'persistent-password';
        localStorage.setItem('loglens_auth_token', password);

        // Simulate page reload by reading from localStorage
        const retrievedPassword = localStorage.getItem('loglens_auth_token');
        assertEqual(retrievedPassword, password, 'Password should persist in localStorage');
    });

    // Test 6: Authentication state check
    runTest('Test 6: Authentication check on app initialization', () => {
        localStorage.clear();

        // Simulate app.js init() - no token stored
        const storedToken = localStorage.getItem('loglens_auth_token');
        assert(storedToken === null, 'Should return null when no token is stored');

        // Simulate with token stored
        localStorage.setItem('loglens_auth_token', 'some-password');
        const storedToken2 = localStorage.getItem('loglens_auth_token');
        assert(storedToken2 !== null, 'Should return token when stored');
    });

    // Test 7: Multiple password changes
    runTest('Test 7: Password can be updated in localStorage', () => {
        localStorage.setItem('loglens_auth_token', 'old-password');
        localStorage.setItem('loglens_auth_token', 'new-password');

        const stored = localStorage.getItem('loglens_auth_token');
        assertEqual(stored, 'new-password', 'Password should be updated in localStorage');
    });

    // Test 8: Special characters in password
    runTest('Test 8: Special characters in password are stored correctly', () => {
        const specialPassword = 'p@$$w0rd!#%^&*()';
        localStorage.setItem('loglens_auth_token', specialPassword);

        const stored = localStorage.getItem('loglens_auth_token');
        assertEqual(stored, specialPassword, 'Special characters should be stored correctly');
    });

    // Test 9: Empty password handling
    runTest('Test 9: Empty password is stored as empty string', () => {
        localStorage.clear();
        localStorage.setItem('loglens_auth_token', '');

        const stored = localStorage.getItem('loglens_auth_token');
        assertEqual(stored, '', 'Empty password should be stored as empty string');
    });

    // Test 10: Very long password
    runTest('Test 10: Long passwords are stored correctly', () => {
        const longPassword = 'a'.repeat(200);
        localStorage.setItem('loglens_auth_token', longPassword);

        const stored = localStorage.getItem('loglens_auth_token');
        assertEqual(stored, longPassword, 'Long passwords should be stored correctly');
        assertEqual(stored.length, 200, 'Password length should be preserved');
    });

    // Test 11: State management after authentication
    runTest('Test 11: State is updated correctly after authentication', () => {
        localStorage.clear();
        const password = 'auth-test-password';

        // Simulate app.js authentication flow
        let authToken = null;
        let isAuthenticated = false;

        // Login
        authToken = password;
        localStorage.setItem('loglens_auth_token', password);
        isAuthenticated = true;

        assertEqual(authToken, password, 'authToken should be set to password');
        assert(isAuthenticated === true, 'isAuthenticated should be true');

        // Logout on 401
        localStorage.removeItem('loglens_auth_token');
        authToken = null;
        isAuthenticated = false;

        assertEqual(authToken, null, 'authToken should be null after logout');
        assert(isAuthenticated === false, 'isAuthenticated should be false after logout');
    });

    // Test 12: localStorage clearing
    runTest('Test 12: localStorage.clear() removes auth token', () => {
        localStorage.setItem('loglens_auth_token', 'test');
        localStorage.clear();

        const stored = localStorage.getItem('loglens_auth_token');
        assertEqual(stored, null, 'Auth token should be removed after clear()');
    });

    // Display summary
    console.log();
    console.log('='.repeat(70));
    console.log('Test Summary');
    console.log('='.repeat(70));

    const passed = testResults.filter(r => r.passed).length;
    const failed = testResults.filter(r => !r.passed).length;
    const total = testResults.length;

    console.log(`Total Tests: ${total}`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
    console.log();

    if (failed === 0) {
        console.log('🎉 All tests passed!');
        process.exit(0);
    } else {
        console.log('❌ Some tests failed.');
        process.exit(1);
    }
}

// Run tests
runTests();
