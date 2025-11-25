/**
 * Custom Cypress Commands
 * Reusable commands for billing calculator E2E tests
 */

/// <reference types="cypress" />

// ============================================================================
// Type Definitions
// ============================================================================

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Fill billing basic info
       * @param uuid - UUID for billing
       * @param billingGroupId - Billing group ID
       * @example cy.fillBasicInfo('test-001', 'bg-kr-test')
       */
      fillBasicInfo(uuid: string, billingGroupId: string): Chainable<void>

      /**
       * Add a usage entry
       * @param volume - Counter volume
       * @example cy.addUsage(100)
       */
      addUsage(volume: number): Chainable<void>

      /**
       * Add a credit entry
       * @param amount - Credit amount
       * @example cy.addCredit(5000)
       */
      addCredit(amount: number): Chainable<void>

      /**
       * Add an adjustment entry
       * @param type - DISCOUNT or SURCHARGE
       * @param value - Adjustment value
       * @example cy.addAdjustment('DISCOUNT', 10)
       */
      addAdjustment(type: 'DISCOUNT' | 'SURCHARGE', value: number): Chainable<void>

      /**
       * Calculate billing
       * @example cy.calculateBilling()
       */
      calculateBilling(): Chainable<void>

      /**
       * Process payment
       * @example cy.processPayment()
       */
      processPayment(): Chainable<void>
    }
  }
}

// ============================================================================
// Custom Commands Implementation
// ============================================================================

Cypress.Commands.add('fillBasicInfo', (uuid: string, billingGroupId: string) => {
  cy.get('input[id="uuid"]').clear().type(uuid)
  cy.get('input[id="billingGroupId"]').clear().type(billingGroupId)
})

Cypress.Commands.add('addUsage', (volume: number) => {
  // Get initial count using jQuery (works even when 0 elements exist)
  cy.get('body').then(($body) => {
    const initialCount = $body.find('input[id^="usage-volume-"]').length

    // Click Add Usage button
    cy.contains('button', 'Add Usage').click()

    // Wait for new input to be added to DOM
    cy.get('input[id^="usage-volume-"]').should('have.length', initialCount + 1)

    // Target the newly added input by index
    cy.get('input[id^="usage-volume-"]').eq(initialCount).clear().type(volume.toString())
  })
})

Cypress.Commands.add('addCredit', (amount: number) => {
  // Get initial count using jQuery (works even when 0 elements exist)
  cy.get('body').then(($body) => {
    const initialCount = $body.find('input[id^="credit-amount-"]').length

    // Click Add Credit button
    cy.contains('button', 'Add Credit').click()

    // Wait for new input to be added to DOM
    cy.get('input[id^="credit-amount-"]').should('have.length', initialCount + 1)

    // Target the newly added input by index
    cy.get('input[id^="credit-amount-"]').eq(initialCount).clear().type(amount.toString())
  })
})

Cypress.Commands.add('addAdjustment', (type: 'DISCOUNT' | 'SURCHARGE', value: number) => {
  // Get initial count using jQuery (works even when 0 elements exist)
  cy.get('body').then(($body) => {
    const initialCount = $body.find('select[id^="adj-type-"]').length

    // Click Add Adjustment button
    cy.contains('button', 'Add Adjustment').click()

    // Wait for new inputs to be added to DOM
    cy.get('select[id^="adj-type-"]').should('have.length', initialCount + 1)
    cy.get('input[id^="adj-value-"]').should('have.length', initialCount + 1)

    // Target the newly added inputs by index
    cy.get('select[id^="adj-type-"]').eq(initialCount).select(type)
    cy.get('input[id^="adj-value-"]').eq(initialCount).clear().type(value.toString())
  })
})

Cypress.Commands.add('calculateBilling', () => {
  cy.contains('button', 'Calculate Billing').click()

  // Wait for billing statement to appear (verifies API call succeeded)
  // This is the most reliable way to verify the calculation completed
  cy.contains('Billing Statement', { timeout: 30000 }).should('be.visible')
})

Cypress.Commands.add('processPayment', () => {
  cy.contains('button', 'Process Payment').click()

  // Wait for payment result to appear
  // The UI displays either "Payment Successful" or "Payment Failed"
  cy.contains('Payment Successful', { timeout: 15000 }).should('be.visible')
})
