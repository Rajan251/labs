import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '2m', target: 50 },  // Ramp up to 50 users
        { duration: '3m', target: 50 },  // Stay at 50 users
        { duration: '1m', target: 100 }, // Spike to 100 users (testing autoscaling)
        { duration: '3m', target: 50 },  // Scale down
        { duration: '2m', target: 0 },   // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(99)<200'], // P99 < 200ms expectation
        http_req_failed: ['rate<0.01'],   // Error rate < 1%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
    // 1. Health Checks
    const healthRes = http.get(`${BASE_URL}/health/live`);
    check(healthRes, { 'status was 200': (r) => r.status == 200 });

    // 2. Job Creation (Write)
    const payload = JSON.stringify({
        name: 'test-job',
        priority: 'high',
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const jobRes = http.post(`${BASE_URL}/jobs`, payload, params);
    check(jobRes, { 'job queued': (r) => r.status == 200 });

    sleep(1);
}
