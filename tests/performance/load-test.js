/**
 * k6 Load Testing Script for Billing API
 *
 * Run locally:
 *   k6 run tests/performance/load-test.js
 *
 * Run with options:
 *   k6 run --vus 100 --duration 30s tests/performance/load-test.js
 *
 * Generate HTML report:
 *   k6 run --out json=results.json tests/performance/load-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const meteringDuration = new Trend('metering_duration');
const paymentDuration = new Trend('payment_duration');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 100 }, // Peak: 100 users
    { duration: '1m', target: 100 },  // Stay at peak
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests should be below 2s
    http_req_failed: ['rate<0.01'],     // Error rate should be less than 1%
    errors: ['rate<0.05'],              // Custom error rate < 5%
  },
};

// Base URL - override with environment variable
const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

// Generate unique test ID
const testRunId = `K6_TEST_${Date.now()}_${__VU}`;

// Test data generators
function generateUUID() {
  return `TEST_${testRunId}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateMeteringData(count = 5) {
  const meters = [];
  for (let i = 0; i < count; i++) {
    meters.push({
      counterName: `cpu.usage.${i}`,
      counterType: 'DELTA',
      counterUnit: 'n',
      counterVolume: Math.floor(Math.random() * 1000) + 100,
      resourceId: `resource-${Math.random().toString(36).substr(2, 8)}`,
      projectId: 'test-project',
      serviceName: 'compute',
    });
  }
  return { meterList: meters };
}

function getCurrentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

// Main test scenario
export default function () {
  const uuid = generateUUID();
  const month = getCurrentMonth();
  const headers = {
    'Accept': 'application/json;charset=UTF-8',
    'Content-Type': 'application/json',
    'uuid': uuid,
  };

  // Test Group 1: Metering Data Submission
  group('Metering Data Submission', function () {
    const meteringData = generateMeteringData(5);
    const startTime = new Date();

    const meteringRes = http.post(
      `${BASE_URL}/billing/meters`,
      JSON.stringify(meteringData),
      { headers }
    );

    const duration = new Date() - startTime;
    meteringDuration.add(duration);

    const meteringCheck = check(meteringRes, {
      'metering: status is 200': (r) => r.status === 200,
      'metering: response time < 1s': (r) => r.timings.duration < 1000,
      'metering: valid response': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body !== null;
        } catch (e) {
          return false;
        }
      },
    });

    errorRate.add(!meteringCheck);
  });

  sleep(1);

  // Test Group 2: Payment Status Check
  group('Payment Status Retrieval', function () {
    const statusRes = http.get(
      `${BASE_URL}/billing/payments/${month}/statements`,
      { headers }
    );

    const statusCheck = check(statusRes, {
      'payment status: status is 200': (r) => r.status === 200,
      'payment status: response time < 500ms': (r) => r.timings.duration < 500,
      'payment status: has statements': (r) => {
        try {
          const body = JSON.parse(r.body);
          return Array.isArray(body.statements);
        } catch (e) {
          return false;
        }
      },
    });

    errorRate.add(!statusCheck);
  });

  sleep(1);

  // Test Group 3: Bulk Metering (High Volume)
  group('Bulk Metering Submission', function () {
    const bulkData = generateMeteringData(50); // 50 meters at once
    const startTime = new Date();

    const bulkRes = http.post(
      `${BASE_URL}/billing/meters`,
      JSON.stringify(bulkData),
      { headers }
    );

    const duration = new Date() - startTime;
    meteringDuration.add(duration);

    const bulkCheck = check(bulkRes, {
      'bulk metering: status is 200': (r) => r.status === 200,
      'bulk metering: response time < 2s': (r) => r.timings.duration < 2000,
      'bulk metering: SLA met': (r) => r.timings.duration < 2000,
    });

    errorRate.add(!bulkCheck);
  });

  sleep(2);

  // Test Group 4: Batch Job Submission
  group('Batch Job Processing', function () {
    const batchData = {
      month: month,
      jobCode: 'API_CALCULATE_USAGE_AND_PRICE',
    };

    const batchRes = http.post(
      `${BASE_URL}/batch/jobs`,
      JSON.stringify(batchData),
      { headers: { 'Content-Type': 'application/json' } }
    );

    const batchCheck = check(batchRes, {
      'batch job: status is 2xx': (r) => r.status >= 200 && r.status < 300,
      'batch job: response time < 1s': (r) => r.timings.duration < 1000,
    });

    errorRate.add(!batchCheck);
  });

  sleep(Math.random() * 3 + 1); // Random sleep 1-4 seconds
}

// Spike test - sudden load
export function spike() {
  const uuid = generateUUID();
  const headers = {
    'Accept': 'application/json;charset=UTF-8',
    'Content-Type': 'application/json',
    'uuid': uuid,
  };

  // Send rapid requests
  for (let i = 0; i < 10; i++) {
    const meteringData = generateMeteringData(10);
    http.post(
      `${BASE_URL}/billing/meters`,
      JSON.stringify(meteringData),
      { headers }
    );
  }
}

// Setup function - runs once before tests
export function setup() {
  console.log('🚀 Starting k6 load test');
  console.log(`📊 Target URL: ${BASE_URL}`);
  console.log(`⏱️  Test duration: ~3.5 minutes`);
  console.log(`👥 Max VUs: 100`);

  // Verify server is up
  const res = http.get(BASE_URL);
  if (res.status !== 200 && res.status !== 404) {
    throw new Error(`Server not responding: ${BASE_URL}`);
  }

  return { startTime: new Date().toISOString() };
}

// Teardown function - runs once after all tests
export function teardown(data) {
  console.log('✅ Load test completed');
  console.log(`🕐 Started at: ${data.startTime}`);
  console.log(`🕐 Finished at: ${new Date().toISOString()}`);
}
