# -*- coding: utf-8 -*- 
import json 
import base64 
from Crypto.Cipher import AES, PKCS1_OAEP 
from Crypto.PublicKey import RSA 
from Crypto.Hash import SHA256 
from Crypto.Random import get_random_bytes 

def encrypt_payload_for_takedown(payload_dict: dict, public_key_pem: str) -> dict: 
    """ 
    针对开发者中心下架接口的混合加密算法 
    1. 生成 32 字节 (256-bit) AES 随机密钥 
    2. 生成 12 字节 GCM Nonce (IV) 
    3. AES-256-GCM 加密 payload_dict (附加 16 字节 Tag) 
    4. RSA-OAEP (SHA256) 加密 AES 密钥 
    """ 
    # 1. 准备随机密钥和 IV 
    aes_key = get_random_bytes(32) 
    iv = get_random_bytes(12)  # GCM 推荐 12 字节 nonce 

    # 2. AES-256-GCM 加密明文数据 
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=iv) 
    plaintext = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8') 
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext) 
    
    # 标准 GCM 密文结构：ciphertext + tag 
    encrypted_data = ciphertext + tag 

    # 3. RSA-OAEP-SHA256 加密 AES 密钥 
    rsa_key = RSA.import_key(public_key_pem) 
    # 注意：此处明确指定 hashAlgo 为 SHA256 以符合后端 "RSA-OAEP-SHA256" 的要求 
    cipher_rsa = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA256.new()) 
    encrypted_aes_key = cipher_rsa.encrypt(aes_key) 

    # 4. 返回标准 Base64 结构 
    return { 
        "key": base64.b64encode(encrypted_aes_key).decode('utf-8'), 
        "iv": base64.b64encode(iv).decode('utf-8'), 
        "data": base64.b64encode(encrypted_data).decode('utf-8') 
    } 
