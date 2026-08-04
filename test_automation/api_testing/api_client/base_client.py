"""
API 接口测试基类
封装 HTTP 请求方法，支持 Session 管理、Token 认证、响应断言、日志记录
"""
import requests
import json
import time
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.logger import get_logger
from config.settings import settings

logger = get_logger("APIClient")


class BaseClient:
    """API 客户端基类，封装常用 HTTP 请求方法和断言工具"""

    def __init__(self, base_url=None, token=None):
        """
        初始化 API 客户端
        :param base_url: API 基础地址，默认从配置读取
        :param token: 认证 token
        """
        self.base_url = base_url or settings.get("api", {}).get("base_url", "")
        self.timeout = settings.get("api", {}).get("timeout", 30)
        self.session = requests.Session()
        self.token = token

        # 设置默认 headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        if self.token:
            self.set_token(self.token)

    def set_token(self, token):
        """设置认证 Token"""
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _build_url(self, path):
        """
        拼接完整 URL
        :param path: 接口路径，如 /api/users
        :return: 完整 URL
        """
        # 如果 path 已经是完整 URL，则直接返回
        if path.startswith("http://") or path.startswith("https://"):
            return path
        # 去除 base_url 末尾的斜杠和 path 开头的斜杠，避免双斜杠
        base = self.base_url.rstrip("/")
        path = path if path.startswith("/") else f"/{path}"
        return f"{base}{path}"

    def _log_request(self, method, url, **kwargs):
        """
        记录请求日志
        :param method: 请求方法（GET/POST/PUT/DELETE/PATCH）
        :param url: 完整 URL
        :param kwargs: 请求参数
        """
        logger.info(f">>> 发送请求: {method.upper()} {url}")
        if kwargs.get("params"):
            logger.debug(f"    Query Params: {kwargs['params']}")
        if kwargs.get("json"):
            logger.debug(f"    JSON Body: {json.dumps(kwargs['json'], ensure_ascii=False)}")
        if kwargs.get("data"):
            logger.debug(f"    Form Data: {kwargs['data']}")
        if kwargs.get("headers"):
            logger.debug(f"    Headers: {kwargs['headers']}")

    def _log_response(self, response, elapsed):
        """
        记录响应日志
        :param response: 响应对象
        :param elapsed: 请求耗时（秒）
        """
        logger.info(f"<<< 响应状态: {response.status_code} | 耗时: {elapsed:.3f}s")
        # 尝试解析 JSON 响应体，失败时记录原始文本（截断）
        try:
            body = response.json()
            logger.debug(f"    响应体: {json.dumps(body, ensure_ascii=False, indent=2)[:2000]}")
        except (json.JSONDecodeError, ValueError):
            logger.debug(f"    响应体(文本): {response.text[:500]}")

    def _request(self, method, path, **kwargs):
        """
        通用请求方法（内部使用）
        :param method: HTTP 方法
        :param path: 接口路径
        :param kwargs: 传递给 requests 的参数
        :return: Response 对象
        """
        url = self._build_url(path)

        # 设置超时，允许调用方覆盖
        kwargs.setdefault("timeout", self.timeout)

        # 如果传入了自定义 headers，合并到请求中（不影响 session 全局 headers）
        custom_headers = kwargs.pop("headers", None)
        if custom_headers:
            # 合并 session headers 和自定义 headers
            merged_headers = dict(self.session.headers)
            merged_headers.update(custom_headers)
            kwargs["headers"] = merged_headers

        # 记录请求日志
        self._log_request(method, url, **kwargs)

        # 发送请求，捕获异常
        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            elapsed = time.time() - start_time
            self._log_response(response, elapsed)
            return response
        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            logger.error(f"请求超时 ({elapsed:.3f}s): {method.upper()} {url} | 错误: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start_time
            logger.error(f"连接错误 ({elapsed:.3f}s): {method.upper()} {url} | 错误: {e}")
            raise
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"请求异常 ({elapsed:.3f}s): {method.upper()} {url} | 错误: {e}")
            raise

    def get(self, path, params=None, headers=None, **kwargs):
        """
        发送 GET 请求
        :param path: 接口路径
        :param params: URL 查询参数
        :param headers: 自定义请求头（覆盖默认值）
        :return: Response 对象
        """
        return self._request("GET", path, params=params, headers=headers, **kwargs)

    def post(self, path, data=None, json_data=None, headers=None, **kwargs):
        """
        发送 POST 请求
        :param path: 接口路径
        :param data: 表单数据
        :param json_data: JSON 请求体
        :param headers: 自定义请求头
        :return: Response 对象
        """
        return self._request("POST", path, data=data, json=json_data, headers=headers, **kwargs)

    def put(self, path, data=None, json_data=None, headers=None, **kwargs):
        """
        发送 PUT 请求
        :param path: 接口路径
        :param data: 表单数据
        :param json_data: JSON 请求体
        :param headers: 自定义请求头
        :return: Response 对象
        """
        return self._request("PUT", path, data=data, json=json_data, headers=headers, **kwargs)

    def delete(self, path, params=None, headers=None, **kwargs):
        """
        发送 DELETE 请求
        :param path: 接口路径
        :param params: URL 查询参数
        :param headers: 自定义请求头
        :return: Response 对象
        """
        return self._request("DELETE", path, params=params, headers=headers, **kwargs)

    def patch(self, path, data=None, json_data=None, headers=None, **kwargs):
        """
        发送 PATCH 请求
        :param path: 接口路径
        :param data: 表单数据
        :param json_data: JSON 请求体
        :param headers: 自定义请求头
        :return: Response 对象
        """
        return self._request("PATCH", path, data=data, json=json_data, headers=headers, **kwargs)

    def upload_file(self, path, file_path, field_name="file", extra_data=None, headers=None, **kwargs):
        """
        文件上传
        :param path: 接口路径
        :param file_path: 本地文件路径
        :param field_name: 文件字段名，默认 "file"
        :param extra_data: 额外的表单字段
        :param headers: 自定义请求头
        :return: Response 对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"上传文件不存在: {file_path}")

        url = self._build_url(path)
        kwargs.setdefault("timeout", self.timeout)

        # 准备文件和额外数据
        file_name = os.path.basename(file_path)
        files = {field_name: (file_name, open(file_path, "rb"))}
        data = extra_data or {}

        # 上传文件时不使用 JSON content-type，需要移除
        upload_headers = dict(self.session.headers)
        upload_headers.pop("Content-Type", None)  # 让 requests 自动设置 multipart 头
        if headers:
            upload_headers.update(headers)

        logger.info(f">>> 文件上传: POST {url} | 文件: {file_name}")

        start_time = time.time()
        try:
            response = self.session.post(url, files=files, data=data, headers=upload_headers, **kwargs)
            elapsed = time.time() - start_time
            self._log_response(response, elapsed)
            return response
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"文件上传失败 ({elapsed:.3f}s): {url} | 错误: {e}")
            raise
        finally:
            # 确保文件句柄关闭
            files[field_name][1].close()

    # === 断言辅助方法 ===

    @staticmethod
    def assert_status_code(response, expected_code=200):
        """
        断言 HTTP 状态码
        :param response: 响应对象
        :param expected_code: 期望的状态码，默认 200
        """
        assert response.status_code == expected_code, \
            f"状态码不匹配: 期望 {expected_code}, 实际 {response.status_code}"

    @staticmethod
    def assert_json_key(response, key, expected_value=None):
        """
        断言 JSON 响应中包含指定 key
        :param response: 响应对象
        :param key: 期望存在的 key
        :param expected_value: 期望的值（可选，传入则同时校验值）
        """
        json_data = response.json()
        assert key in json_data, f"响应中不包含 key: {key}"
        if expected_value is not None:
            assert json_data[key] == expected_value, \
                f"key '{key}' 的值不匹配: 期望 {expected_value}, 实际 {json_data[key]}"

    @staticmethod
    def assert_response_time(response, max_time=5.0):
        """
        断言响应时间不超过指定阈值
        :param response: 响应对象
        :param max_time: 最大允许时间（秒），默认 5.0s
        """
        assert response.elapsed.total_seconds() <= max_time, \
            f"响应时间超标: {response.elapsed.total_seconds()}s > {max_time}s"

    @staticmethod
    def assert_json_contains(response, expected_dict):
        """
        断言 JSON 响应包含指定键值对（子集匹配）
        :param response: 响应对象
        :param expected_dict: 期望包含的键值对字典
        """
        json_data = response.json()
        for key, value in expected_dict.items():
            assert key in json_data, f"响应中不包含 key: {key}"
            assert json_data[key] == value, \
                f"key '{key}' 的值不匹配: 期望 {value}, 实际 {json_data[key]}"

    @staticmethod
    def assert_json_list_not_empty(response, key=None):
        """
        断言 JSON 响应中列表不为空
        :param response: 响应对象
        :param key: 列表字段名（可选，为 None 时认为响应本身是列表）
        """
        json_data = response.json()
        if key:
            assert key in json_data, f"响应中不包含 key: {key}"
            target_list = json_data[key]
        else:
            target_list = json_data
        assert isinstance(target_list, list), f"目标不是列表类型: {type(target_list)}"
        assert len(target_list) > 0, "列表为空"

    def close(self):
        """关闭 session，释放连接资源"""
        self.session.close()
        logger.debug("Session 已关闭")

    def __enter__(self):
        """支持 with 语句"""
        return self

    def __exit__(self, *args):
        """退出 with 语句时自动关闭 session"""
        self.close()
