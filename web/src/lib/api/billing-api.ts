import type { 
  BillingInput,
  BillingStatement,
  PaymentResult
} from '@/types/billing';

// API request/response types
export interface PaymentRequest {
  amount: number;
  paymentGroupId: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export class BillingAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async calculateBilling(
    request: BillingInput
  ): Promise<BillingStatement> {
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
  ): Promise<BillingStatement> {
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
  ): Promise<PaymentResult> {
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

// Export convenience functions with client-side enhancements
export const calculateBilling = async (request: BillingInput): Promise<BillingStatement> => {
  const statement = await billingAPI.calculateBilling(request);
  
  // Add unpaid amount and late fee client-side (doesn't affect backend/tests)
  const unpaidAmount = request.unpaidAmount || 0;
  const lateFee = request.isOverdue && unpaidAmount > 0 ? unpaidAmount * 0.05 : 0;
  
  return {
    ...statement,
    unpaidAmount,
    lateFee,
    totalAmount: statement.totalAmount + unpaidAmount + lateFee,
  };
};

export const getPaymentStatements = (uuid: string, month: string) =>
  billingAPI.getPaymentStatements(uuid, month);

export const processPayment = (uuid: string, month: string, request: PaymentRequest) =>
  billingAPI.processPayment(uuid, month, request);
