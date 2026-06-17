#!/usr/bin/env python3
"""
DeepSeek / 火山引擎 反向代理
拦截 Qoder 发往 api.moonshot.cn (Kimi) 的请求，转发到上游 API（DeepSeek/火山引擎）

用法:
  sudo python3 proxy.py                    # 前台运行（需要 sudo 监听 443 端口）
  sudo python3 proxy.py --daemon           # 后台运行
"""

import json
import logging
import os
import signal
import socket
import ssl
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import requests as http_requests

# ============================================================
# 配置加载
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
PID_FILE = os.path.join(SCRIPT_DIR, "proxy.pid")
LOG_FILE = os.path.join(SCRIPT_DIR, "proxy.log")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 日志设置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("volcano-proxy")


# ============================================================
# 代理请求处理器
# ============================================================

class ProxyHandler(BaseHTTPRequestHandler):
    """处理 Qoder 发往 api.minimax.chat 的 HTTP/HTTPS 请求"""

    config = None

    def log_message(self, format, *args):
        """重写日志输出到 logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

    def do_GET(self):
        """处理 GET 请求（如模型列表查询等）"""
        self._proxy_request("GET")

    def do_POST(self):
        """处理 POST 请求（主要的 chat/completions 请求）"""
        self._proxy_request("POST")

    def do_OPTIONS(self):
        """处理 OPTIONS 预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def _proxy_request(self, method):
        """核心代理逻辑：拦截请求 → 修改 → 转发到上游 API"""

        config = self.config
        upstream_config = config.get("upstream", config.get("volcano_engine", {}))
        upstream_base_url = upstream_config["base_url"]
        upstream_api_key = upstream_config["api_key"]
        model_mapping = config.get("model_mapping", {})
        fallback_model = config.get("default_fallback_model", "deepseek-chat")
        reasoning_effort = config.get("reasoning_effort", "medium")

        # 读取请求体
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        # 解析原始请求路径
        original_path = self.path
        logger.info(f"━━━ 收到请求: {method} {original_path}")

        # ============================================================
        # GET /v1/models → 返回模拟模型列表（让 Qoder 看到自定义模型名）
        if method == "GET" and original_path.rstrip("/") in ("/v1/models", "/models"):
            logger.info("  → 拦截模型列表请求，返回模拟数据")
            mock_models = {
                "object": "list",
                "data": [
                    {"id": m, "object": "model", "created": 1700000000, "owned_by": "volcano-proxy"}
                    for m in model_mapping.keys()
                ]
            }
            mock_body = json.dumps(mock_models).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(mock_body)))
            self.end_headers()
            self.wfile.write(mock_body)
            logger.info(f"  ✓ 返回 {len(model_mapping)} 个模拟模型")
            return

        # 构造上游目标 URL
        # 火山引擎 base_url 已含 /v3，需剥离 /v1 前缀
        # DeepSeek 标准 OpenAI 格式需保留 /v1 前缀
        target_path = original_path
        strip_v1 = upstream_config.get("strip_v1_prefix", True)
        if strip_v1 and target_path.startswith("/v1/"):
            target_path = target_path[3:]  # 去掉 /v1，保留 /chat/completions
        if not target_path.startswith("/"):
            target_path = "/" + target_path

        target_url = upstream_base_url + target_path

        # 修改请求体：替换模型名和推理程度
        modified_body = body
        if body:
            try:
                body_json = json.loads(body)
                original_model = body_json.get("model", "")

                # 模型映射
                mapped_model = model_mapping.get(original_model, fallback_model)
                body_json["model"] = mapped_model

                # 设置推理程度（如果请求中没有指定）
                if "reasoning_effort" not in body_json:
                    body_json["reasoning_effort"] = reasoning_effort

                modified_body = json.dumps(body_json).encode("utf-8")

                logger.info(f"  原始模型: {original_model}")
                logger.info(f"  映射模型: {mapped_model}")
                logger.info(f"  推理程度: {reasoning_effort}")
                logger.info(f"  目标 URL: {target_url}")

            except json.JSONDecodeError:
                logger.warning("  请求体不是有效 JSON，原样转发")

        # 构造转发请求头 — 只保留必要的非认证头
        # 需要过滤掉的认证相关头（各种 Provider 可能用不同格式）
        auth_headers_to_remove = {
            "host", "content-length", "transfer-encoding", "connection",
            "authorization", "api-key", "x-api-key", "x-auth-token",
            "x-minimax-api-key", "token",
        }

        headers = {}
        for key, value in self.headers.items():
            key_lower = key.lower()
            if key_lower in auth_headers_to_remove:
                continue
            headers[key] = value

        # 记录原始认证头（用于调试）
        original_auth = self.headers.get("Authorization", "(none)")
        original_api_key = self.headers.get("api-key", "(none)")
        original_x_api_key = self.headers.get("x-api-key", "(none)")
        logger.info(f"  原始 Authorization: {original_auth[:30]}...")
        logger.info(f"  原始 api-key: {original_api_key}")
        logger.info(f"  原始 x-api-key: {original_x_api_key}")

        # 设置上游 API 所需的 Bearer 认证头
        headers["Authorization"] = f"Bearer {upstream_api_key}"

        # 发送转发请求
        try:
            logger.info(f"  转发到: {target_url}")

            resp = http_requests.request(
                method=method,
                url=target_url,
                headers=headers,
                data=modified_body,
                stream=True,  # 支持 SSE 流式响应
                timeout=300,  # 5 分钟超时
                verify=True,
            )

            # 发送响应头
            self.send_response(resp.status_code)
            for key, value in resp.headers.items():
                key_lower = key.lower()
                if key_lower in ("transfer-encoding", "content-encoding",
                                 "content-length", "connection"):
                    continue
                self.send_header(key, value)

            # 处理流式响应
            is_streaming = resp.headers.get("content-type", "").startswith("text/event-stream")

            if is_streaming:
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                all_chunks = b""
                for chunk in resp.iter_content(chunk_size=None, decode_unicode=False):
                    if chunk:
                        all_chunks += chunk
                        # HTTP chunked encoding
                        chunk_bytes = chunk
                        self.wfile.write(
                            f"{len(chunk_bytes):x}\r\n".encode() + chunk_bytes + b"\r\n"
                        )
                        self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
                # 记录流式响应内容（前500字符）
                try:
                    body_preview = all_chunks.decode("utf-8", errors="replace")[:500]
                    logger.info(f"  流式响应内容(前500字): {body_preview}")
                except Exception:
                    pass
            else:
                content = resp.content

                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                # 记录非流式响应内容（前500字符）
                try:
                    body_preview = content.decode("utf-8", errors="replace")[:500]
                    logger.info(f"  响应内容(前500字): {body_preview}")
                except Exception:
                    pass

            logger.info(f"  ✓ 响应完成 (HTTP {resp.status_code})")

        except http_requests.exceptions.Timeout:
            logger.error("  ✗ 请求超时")
            self._send_error(504, "Upstream request timed out")

        except http_requests.exceptions.ConnectionError as e:
            logger.error(f"  ✗ 连接错误: {e}")
            self._send_error(502, f"Upstream connection error: {str(e)}")

        except Exception as e:
            logger.error(f"  ✗ 代理错误: {e}", exc_info=True)
            self._send_error(500, f"Proxy error: {str(e)}")

    def _send_error(self, code, message):
        """发送错误响应"""
        error_body = json.dumps({
            "error": {
                "message": message,
                "type": "proxy_error",
                "code": code,
            }
        }).encode("utf-8")

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(error_body)))
        self.end_headers()
        self.wfile.write(error_body)


# ============================================================
# 健康检查端点（通过 HTTP 而非 HTTPS）
# ============================================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({
                "status": "running",
                "proxy": "deepseek-upstream-proxy",
                "target": "api.moonshot.cn → api.deepseek.com",
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


# ============================================================
# 服务器启动
# ============================================================

def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def start_health_check(port=8443):
    """在 HTTP 端口启动健康检查"""
    server = HTTPServer(("127.0.0.1", port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"[*] 健康检查端点: http://127.0.0.1:{port}/health")
    return server


def main():
    config = load_config()

    proxy_config = config["proxy"]
    listen_host = proxy_config["listen_host"]
    listen_port = proxy_config["listen_port"]
    cert_file = os.path.join(SCRIPT_DIR, proxy_config["cert_file"])
    key_file = os.path.join(SCRIPT_DIR, proxy_config["key_file"])

    # 检查证书文件
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        logger.error(f"[✗] SSL 证书文件不存在!")
        logger.error(f"    请先运行: python3 gen_cert.py")
        sys.exit(1)

    # 检查 API Key
    upstream_config = config.get("upstream", config.get("volcano_engine", {}))
    api_key = upstream_config["api_key"]
    if "YOUR" in api_key.upper() or "HERE" in api_key.upper():
        logger.error("[✗] 请先在 config.json 的 upstream.api_key 中填写你的 DeepSeek API Key!")
        sys.exit(1)

    # 设置处理器配置
    ProxyHandler.config = config

    # 打印映射信息
    print()
    upstream_base_url = upstream_config["base_url"]
    print("=" * 60)
    print("  🔥 DeepSeek 上游反向代理")
    print("=" * 60)
    print(f"  拦截域名:  {proxy_config['target_domain']}")
    print(f"  监听端口:  {listen_port}")
    print(f"  转发目标:  {upstream_base_url}")
    print(f"  推理程度:  {config.get('reasoning_effort', 'medium')}")
    print()
    print("  模型映射表:")
    print("  " + "-" * 50)
    for qoder_name, volcano_name in config["model_mapping"].items():
        marker = "  ★" if qoder_name == volcano_name else "  →"
        print(f"    {qoder_name:<25}{marker} {volcano_name}")
    print(f"    {'(其他/默认)':<25}  → {config.get('default_fallback_model', 'N/A')}")
    print("  " + "-" * 50)
    print()

    # 创建支持 IPv4+IPv6 双栈的 HTTPS 服务器
    class DualStackHTTPServer(HTTPServer):
        address_family = socket.AF_INET6
        def server_bind(self):
            # macOS 要求在 bind 之前设置 IPV6_V6ONLY
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            super().server_bind()
    server = DualStackHTTPServer(("::" , listen_port), ProxyHandler)

    # 配置 SSL
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_file, key_file)
    server.socket = ssl_context.wrap_socket(server.socket, server_side=True)

    # 启动健康检查
    start_health_check()

    # 写 PID 文件
    write_pid()

    # 优雅退出
    def signal_handler(sig, frame):
        logger.info("[*] 收到退出信号，正在关闭代理...")
        remove_pid()
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"[✓] 代理已启动! 监听 https://{listen_host}:{listen_port}")
    logger.info(f"[✓] 拦截所有发往 {proxy_config['target_domain']} 的请求")
    print()
    logger.info("[*] 按 Ctrl+C 停止代理")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        logger.info("[*] 代理已停止")
        remove_pid()


if __name__ == "__main__":
    main()
