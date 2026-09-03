package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"errors"
	"fmt"
	"os"
)

const (
	RsaPublicType = "RSA PUBLIC KEY"
)

// RSAEncode 公钥加密接口
func RSAEncode(src []byte, public []byte) (dst []byte, errResult error) {
	block, _ := pem.Decode(public)
	if block == nil {
		return nil, errors.New("failed to decode PEM block")
	}

	if block.Type != RsaPublicType {
		return nil, errors.New("public key type error")
	}

	// 解析公钥
	publicKey, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("failed to parse public key: %v", err)
	}

	rsaPublicKey, ok := publicKey.(*rsa.PublicKey)
	if !ok {
		return nil, errors.New("not an RSA public key")
	}

	// 使用 PKCS1v15 填充方案加密
	return rsa.EncryptPKCS1v15(rand.Reader, rsaPublicKey, src)
}

// JsEcryptEncode 加密密码（与前端 JSEncrypt 库兼容）
func JsEcryptEncode(password string, publicKey string) (encrypted string, err error) {
	cipherText, err := RSAEncode([]byte(password), []byte(publicKey))
	if err != nil {
		return "", err
	}
	// Base64 编码
	encrypted = base64.StdEncoding.EncodeToString(cipherText)
	return
}
func main() {
	if len(os.Args) < 3 {
		fmt.Fprintf(os.Stderr, "Usage: %s <password>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "Example: %s mypassword123\n", os.Args[0])
		os.Exit(1)
	}

	password := os.Args[1]
	publicKey := os.Args[2]
	encrypted, err := JsEcryptEncode(password, publicKey)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Encryption failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(encrypted)
}
