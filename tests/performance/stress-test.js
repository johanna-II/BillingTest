/**
 * k6 Stress Test - Find system limits
 *
 * This test gradually increases load to find the breaking point
 *
 * Usage:
 *   k6 run tests/performance/stress-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '3m', target: 100 },  // Ramp up to 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '3m', target: 300 },  // Ramp up to 300 users - stress level
    { duration: '2m', target: 400 },  // Ramp up to 400 users - breaking point
    { duration: '5m', target: 0 },    // Ramp down gradually
  ],
  thresholds: {
    http_req_duration: ['p(99)<5000'], // 99% under 5s (relaxed threshold)
    errors: ['rate<0.1'],               // Error rate < 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

// Counter for generating unique IDs
let requestCounter = 0;

export default function stressTest() {
  const uuid = `STRESS_TEST_${Date.now()}_${__VU}`;
  const headers = {
    'Accept': 'application/json;charset=UTF-8',
    'Content-Type': 'application/json',
    'uuid': uuid,
  };

  // Generate test data using predictable values (no random needed for tests)
  const baseVolume = Date.now() % 1000;
  const meteringData = {
    meterList: Array.from({ length: 10 }, (_, i) => {
      requestCounter++;
      return {
        counterName: `test.counter.${i}`,
        counterType: 'DELTA',
        counterUnit: 'n',
        counterVolume: baseVolume + i * 100, // Predictable variation
        resourceId: `resource-${__VU}-${requestCounter}`, // Unique, predictable ID
        projectId: 'stress-test',
        serviceName: 'compute',
      };
    }),
  };

  const res = http.post(
    `${BASE_URL}/billing/meters`,
    JSON.stringify(meteringData),
    { headers }
  );

  const success = check(res, {
    'stress: status is 200': (r) => r.status === 200,
    'stress: response time acceptable': (r) => r.timings.duration < 5000,
  });

  errorRate.add(!success);

  sleep(0.5); // Minimal sleep to maintain pressure
}

export function setup() {
  console.log('⚠️  Starting STRESS test - this will push the system to limits');
  console.log(`📊 Target: ${BASE_URL}`);
  console.log(`👥 Max VUs: 400`);
  console.log(`⏱️  Duration: ~17 minutes`);
}

export function teardown(data) {
  console.log('✅ Stress test completed');
  console.log('📈 Check the results to find system limits');
}
