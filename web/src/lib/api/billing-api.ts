import type { 
  BillingCalculationRequest, 
  BillingCalculationResponse,
  PaymentRequest,
  PaymentResponse 
} from '@/types/billing';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export class BillingAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async calculateBilling(
    request: BillingCalculationRequest
  ): Promise<BillingCalculationResponse> {
    const response = await fetch(`${this.baseUrl}/api/billing/admin/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'uuid': request.uuid,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to calculate billing: ${response.statusText}`);
    }

    return response.json();
  }

  async getPaymentStatements(
    uuid: string,
    month: string
  ): Promise<BillingCalculationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/billing/payments/${month}/statements`,
      {
        method: 'GET',
        headers: {
          'uuid': uuid,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get statements: ${response.statusText}`);
    }

    return response.json();
  }

  async processPayment(
    uuid: string,
    month: string,
    request: PaymentRequest
  ): Promise<PaymentResponse> {
    const response = await fetch(`${this.baseUrl}/api/billing/payments/${month}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'uuid': uuid,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to process payment: ${response.statusText}`);
    }

    return response.json();
  }
}

export const billingAPI = new BillingAPIClient();
