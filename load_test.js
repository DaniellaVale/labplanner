import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '30s', target: 50 },
    { duration: '30s', target: 100 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  const payload = JSON.stringify({
    design_type: 'fatorial_2k',
    factors: 3,
    center_points: 2,
    fractionality: 1,
    replicates: 1,
    levels: [
      { name: 'A', minimum: 10, maximum: 20 },
      { name: 'B', minimum: 5, maximum: 15 },
      { name: 'C', minimum: 1, maximum: 3 },
    ],
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const res = http.post('http://localhost:8000/doe/generate', payload, params);

  check(res, {
    'status 200': (r) => r.status === 200,
  });
}