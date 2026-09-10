"""
encryption_utils.py
纯算法级的加解密工具，不包含任何业务逻辑。
支持 AES 加解密 (使用 AES-GCM 模式，提供高安全性的认证加密)。
"""
import base64
from Crypto.Cipher import AES

def encrypt_aes(plaintext: str, key: str) -> str:
    """
    使用 AES-GCM 算法加密字符串。
    
    :param plaintext: 待加密的明文
    :param key: 加密密钥，长度必须为 16, 24 或 32 字节的字符串
    :return: Base64 编码的密文字符串 (包含 nonce, tag 和 ciphertext)
    """
    key_bytes = key.encode('utf-8')
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("AES key 必须是 16, 24 或 32 字节长度")
        
    cipher = AES.new(key_bytes, AES.MODE_GCM)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    
    # 组合 nonce (16 bytes), tag (16 bytes) 和 密文，并进行 Base64 编码
    encrypted_data = nonce + tag + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt_aes(encrypted_b64: str, key: str) -> str:
    """
    使用 AES-GCM 算法解密字符串。
    
    :param encrypted_b64: encrypt_aes 函数生成的 Base64 编码密文
    :param key: 解密密钥，必须与加密时使用的密钥一致
    :return: 解密后的明文
    """
    key_bytes = key.encode('utf-8')
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("AES key 必须是 16, 24 或 32 字节长度")
        
    try:
        encrypted_data = base64.b64decode(encrypted_b64)
        
        if len(encrypted_data) < 32:
            raise ValueError("密文数据长度不足")
            
        # 提取 nonce, tag 和密文 (默认 nonce 和 tag 各 16 字节)
        nonce = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        
        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
        plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext_bytes.decode('utf-8')
    except ValueError as e:
        raise ValueError(f"解密失败: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"解密过程中发生异常: {str(e)}") from e
