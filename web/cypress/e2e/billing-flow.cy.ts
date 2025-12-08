/**
 * E2E Test: Complete Billing Flow
 * Tests the entire billing calculation and payment process
 */

describe('Billing Calculator - Complete Flow', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should display the home page correctly', () => {
    cy.contains('h2', 'Billing Parameters').should('be.visible')
    cy.contains('button', 'Calculate Billing').should('be.visible')
  })

  it('should calculate billing with basic usage', () => {
    // Fill basic info
    cy.fillBasicInfo('test-uuid-e2e-001', 'bg-kr-e2e')

    // Add usage
    cy.addUsage(100)

    // Calculate
    cy.calculateBilling()

    // Verify statement is displayed
    cy.contains('Billing Statement').should('be.visible')
    cy.contains('Subtotal').should('be.visible')
  })

  it('should handle usage with adjustments', () => {
    cy.fillBasicInfo('test-uuid-e2e-002', 'bg-kr-e2e')

    // Add usage
    cy.addUsage(200)

    // Add discount
    cy.addAdjustment('DISCOUNT', 10)

    // Calculate
    cy.calculateBilling()

    // Verify statement is displayed
    cy.contains('Billing Statement').should('be.visible')
    // Adjustments are shown in line items or totals section
    cy.contains('Subtotal').should('be.visible')
    cy.contains('Total').should('be.visible')
  })

  it('should calculate and show statement successfully', () => {
    cy.fillBasicInfo('test-uuid-e2e-003', 'bg-kr-e2e')

    // Add usage
    cy.addUsage(150)

    // Calculate
    cy.calculateBilling()

    // Verify statement is displayed with expected sections
    cy.contains('Billing Statement').should('be.visible')
    cy.contains('Subtotal').should('be.visible')
    cy.contains('Total').should('be.visible')
  })

  it('should save calculation in history', () => {
    cy.fillBasicInfo('test-uuid-e2e-004', 'bg-kr-e2e')
    cy.addUsage(75)
    cy.calculateBilling()

    // Verify calculation completed
    cy.contains('Billing Statement').should('be.visible')

    // History is automatically saved
    // Verify by checking localStorage (Zustand persist)
    cy.window().its('localStorage.billing-history-storage').should('exist')
  })

  it('should validate required fields', () => {
    // Try to calculate without UUID
    cy.get('input[id="uuid"]').clear()
    cy.get('input[id="billingGroupId"]').clear().type('bg-test')
    cy.contains('button', 'Calculate Billing').click()

    // Should show validation error
    cy.contains('UUID and Billing Group ID are required').should('be.visible')
  })

  it('should handle multiple usage entries', () => {
    cy.fillBasicInfo('test-uuid-e2e-005', 'bg-kr-e2e')

    // Add multiple usage entries
    cy.addUsage(100)
    cy.addUsage(200)
    cy.addUsage(50)

    // Calculate
    cy.calculateBilling()

    // Verify statement
    cy.contains('Billing Statement').should('be.visible')
  })

  it('should handle credits', () => {
    cy.fillBasicInfo('test-uuid-e2e-006', 'bg-kr-e2e')

    cy.addUsage(200)
    cy.addCredit(10000)

    cy.calculateBilling()

    // Verify statement shows credits section
    cy.contains('Billing Statement').should('be.visible')
    // Credits are shown in the breakdown section
    cy.contains('Credits', { matchCase: false }).should('exist')
  })

  it('should navigate to documentation', () => {
    // Navigate using header link
    cy.get('a[href="/docs"]').first().click()
    cy.url().should('include', '/docs')
    cy.contains('h1', 'Documentation').should('be.visible')
  })

  it('should navigate to API reference', () => {
    // Navigate using header link
    cy.get('a[href="/api-reference"]').first().click()
    cy.url().should('include', '/api-reference')
    cy.contains('API').should('be.visible')
  })
})
