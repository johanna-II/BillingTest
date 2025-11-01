/**
 * k6 Smoke Test - Quick validation
 *
 * Run this before full load tests to verify basic functionality
 *
 * Usage:
 *   k6 run tests/performance/smoke-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,           // 1 virtual user
  duration: '30s',  // Run for 30 seconds
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% under 1 second
    http_req_failed: ['rate<0.01'],     // Less than 1% errors
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

export default function () {
  const uuid = `SMOKE_TEST_${Date.now()}`;
  const headers = {
    'Accept': 'application/json;charset=UTF-8',
    'Content-Type': 'application/json',
    'uuid': uuid,
  };

  // Test 1: Send metering data
  const meteringData = {
    meterList: [
      {
        counterName: 'cpu.usage.test',
        counterType: 'DELTA',
        counterUnit: 'n',
        counterVolume: 100,
        resourceId: 'test-resource',
        projectId: 'test-project',
        serviceName: 'compute',
      },
    ],
  };

  const meteringRes = http.post(
    `${BASE_URL}/billing/meters`,
    JSON.stringify(meteringData),
    { headers }
  );

  check(meteringRes, {
    'smoke: metering endpoint works': (r) => r.status === 200,
  });

  sleep(1);

  // Test 2: Get payment status
  const month = new Date().toISOString().slice(0, 7);
  const statusRes = http.get(
    `${BASE_URL}/billing/payments/${month}/statements`,
    { headers }
  );

  check(statusRes, {
    'smoke: payment status endpoint works': (r) => r.status === 200,
  });

  sleep(1);
}

export function setup() {
  console.log('🔍 Running smoke test...');
  console.log(`📊 Target: ${BASE_URL}`);
}

export function teardown(data) {
  console.log('✅ Smoke test completed');
}
