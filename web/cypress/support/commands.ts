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
  // Click Add Usage button
  cy.contains('button', 'Add Usage').click()

  // Fill in the volume for the newly added usage entry
  cy.get('input[id^="usage-volume-"]').last().clear().type(volume.toString())
})

Cypress.Commands.add('addCredit', (amount: number) => {
  cy.contains('button', 'Add Credit').click()
  cy.get('input[id^="credit-amount-"]').last().clear().type(amount.toString())
})

Cypress.Commands.add('addAdjustment', (type: 'DISCOUNT' | 'SURCHARGE', value: number) => {
  cy.contains('button', 'Add Adjustment').click()

  // Select type
  cy.get('select[id^="adj-type-"]').last().select(type)

  // Fill value
  cy.get('input[id^="adj-value-"]').last().clear().type(value.toString())
})

Cypress.Commands.add('calculateBilling', () => {
  // Set up API intercept before clicking with precise endpoint match
  cy.intercept('POST', '**/api/billing/admin/calculate').as('calculateRequest')

  cy.contains('button', 'Calculate Billing').click()

  // Wait for API call with generous timeout
  cy.wait('@calculateRequest', { timeout: 30000 }).then((interception) => {
    // Log for debugging
    cy.log('API Response Status:', interception.response?.statusCode)

    // Verify successful response
    expect(interception.response?.statusCode).to.equal(200)
  })

  // Wait for UI to show statement
  cy.contains('Billing Statement', { timeout: 10000 }).should('be.visible')
})

Cypress.Commands.add('processPayment', () => {
  // Intercept payment API call with precise endpoint match
  cy.intercept('POST', '**/api/billing/payments/*').as('paymentAPI')

  cy.contains('button', 'Process Payment').click()

  // Wait for API response
  cy.wait('@paymentAPI', { timeout: 15000 })

  // Wait for success message or payment result
  cy.contains(/Payment.*success|Payment Result/i, { timeout: 10000 }).should('be.visible')
})
