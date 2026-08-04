# 内网拉取代码标准操作程序(SOP)

## 1. 概述
本文档描述在内网环境中配置开发环境并从GitLab同步代码的完整流程。

## 2. 前置条件
- 内网网络已连接
- 公司代理服务器地址和端口
- GitLab账号和访问权限
- VSCode已安装（或准备安装）

## 3. 操作步骤

### 3.1 配置公司代理

#### 3.1.1 系统代理配置
1. 打开Windows设置 → 网络和Internet → 代理
2. 在"手动设置代理"中输入：
   - 代理服务器地址：`[公司代理地址]`
   - 端口：`[代理端口]`
3. 勾选"使用代理服务器"
4. 点击"保存"

#### 3.1.2 Git代理配置
```bash
# 配置HTTP代理
git config --global http.proxy http://[代理地址]:[端口]
git config --global https.proxy http://[代理地址]:[端口]

# 验证配置
git config --global --get http.proxy
git config --global --get https.proxy
```

#### 3.1.3 VSCode代理配置
1. 打开VSCode
2. `Ctrl + ,` 打开设置
3. 搜索 `http.proxy`
4. 填入代理地址：`http://[代理地址]:[端口]`
5. 勾选 `http.proxySupport` 设置为 `on`

### 3.2 下载并安装VSCode插件

#### 3.2.1 安装Claude插件
1. 打开VSCode
2. 点击左侧扩展图标（或 `Ctrl + Shift + X`）
3. 搜索 `Claude Code` 或 `Claude`
4. 点击"安装"
5. 等待安装完成
6. 根据提示完成插件配置（如API Key等）

#### 3.2.2 推荐插件
- GitLens - Git增强工具
- Remote - SSH - 远程连接
- Chinese (Simplified) - 中文语言包

### 3.3 虚拟机配置

#### 3.3.1 下载虚拟机软件
1. 访问公司内网下载站点或外部网站（需代理）
2. 下载虚拟机软件：
   - VMware Workstation 或
   - VirtualBox
3. 运行安装程序，按提示完成安装

#### 3.3.2 配置虚拟机网络
1. 打开虚拟机软件
2. 网络适配器设置为：
   - **NAT模式**：共享主机IP，需配置代理
   - **桥接模式**：直接连接内网
3. 启动虚拟机，测试网络连接：
   ```bash
   ping [内网GitLab地址]
   ```

#### 3.3.3 虚拟机内代理配置（如需要）
```bash
# 在虚拟机终端中配置
export http_proxy=http://[代理地址]:[端口]
export https_proxy=http://[代理地址]:[端口]

# 永久配置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export http_proxy=http://[代理地址]:[端口]' >> ~/.bashrc
echo 'export https_proxy=http://[代理地址]:[端口]' >> ~/.bashrc
source ~/.bashrc
```

### 3.4 从GitLab同步代码

#### 3.4.1 配置Git用户信息
```bash
git config --global user.name "[您的姓名]"
git config --global user.email "[您的邮箱]"
```

#### 3.4.2 克隆仓库
```bash
# HTTPS方式（需代理）
git clone https://[gitlab地址]/[项目路径].git

# SSH方式（推荐，需配置SSH Key）
git clone git@[gitlab地址]:[项目路径].git
```

#### 3.4.3 SSH Key配置（如使用SSH）
```bash
# 1. 生成SSH Key
ssh-keygen -t ed25519 -C "[您的邮箱]"

# 2. 查看公钥
cat ~/.ssh/id_ed25519.pub

# 3. 复制公钥到GitLab
# GitLab → Settings → SSH Keys → 添加公钥

# 4. 测试连接
ssh -T git@[gitlab地址]
```

#### 3.4.4 VSCode中打开项目
1. VSCode → 文件 → 打开文件夹
2. 选择克隆的项目目录
3. 等待VSCode加载项目

### 3.5 验证环境

#### 3.5.1 网络连通性测试
```bash
# 测试代理
curl -I https://www.google.com

# 测试GitLab连接
git ls-remote https://[gitlab地址]/[项目路径].git
```

#### 3.5.2 Git配置验证
```bash
# 查看所有配置
git config --global --list

# 重点检查
git config --global --get http.proxy
git config --global --get user.name
git config --global --get user.email
```

## 4. 常见问题排查

### 4.1 代理连接失败
- 检查代理地址和端口是否正确
- 验证代理服务器是否运行
- 尝试在浏览器中测试代理
- 检查防火墙设置

### 4.2 Git克隆失败
```bash
# 增加Git缓冲区
git config --global http.postBuffer 524288000

# 降低SSL验证（仅限内网，不推荐生产环境）
git config --global http.sslVerify false

# 查看详细错误信息
GIT_CURL_VERBOSE=1 git clone [仓库地址]
```

### 4.3 VSCode插件安装失败
- 确认代理配置正确
- 尝试离线安装：下载 `.vsix` 文件后手动安装
- 检查VSCode版本是否兼容

### 4.4 虚拟机网络问题
- 检查虚拟机网络适配器模式
- 重启虚拟机网络服务
- 在虚拟机内重新配置代理

## 5. 安全注意事项
1. 不要在代码中硬编码代理地址和密码
2. 使用SSH Key而非HTTPS密码认证
3. 定期更新虚拟机和软件
4. 内网代理配置不要泄露到外网

## 6. 附录

### 6.1 常用命令速查
```bash
# 查看当前代理配置
git config --global --get http.proxy

# 临时取消代理
git -c http.proxy= clone [仓库地址]

# VSCode中查看代理设置
# 设置 → 搜索 http.proxy

# 测试代理连通性
curl -x http://[代理地址]:[端口] https://www.google.com
```

### 6.2 联系方式
- IT支持：[联系方式]
- GitLab管理员：[联系方式]
- 网络管理员：[联系方式]

---

**文档版本**: v1.0  
**更新日期**: 2026-07-10  
**维护人**: [姓名]
