/**
 * Cypress E2E Support File
 * Global configuration and custom commands
 */

// Import Cypress commands
import './commands'

// Global before hook
before(() => {
  cy.log('🚀 Starting E2E Test Suite')
})

// Global after hook
after(() => {
  cy.log('✅ E2E Test Suite Complete')
})

// Handle uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // Prevent Cypress from failing the test on certain errors
  // Add specific error messages you want to ignore
  if (err.message.includes('ResizeObserver')) {
    return false
  }

  // Let other errors fail the test
  return true
})
