import http from 'k6/http';
import { check, sleep } from 'k6';

// 测试配置
export const options = {
  // 阶梯式负载
  stages: [
    { duration: '30s', target: 10 },   // 30秒内增加到10个虚拟用户
    { duration: '1m', target: 10 },    // 保持10个用户持续1分钟
    { duration: '30s', target: 20 },   // 30秒内增加到20个用户
    { duration: '1m', target: 20 },    // 保持20个用户持续1分钟
    { duration: '30s', target: 0 },    // 30秒内降到0
  ],
  // 阈值
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% 请求响应时间小于500ms
    http_req_failed: ['rate<0.01'],    // 错误率小于1%
  },
};

// 测试逻辑
export default function () {
  // 替换为实际接口地址
  const res = http.get('https://test.example.com/api/health');
  
  check(res, {
    '状态码为200': (r) => r.status === 200,
    '响应时间小于500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
