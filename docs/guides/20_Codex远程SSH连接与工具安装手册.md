# Codex 远程 SSH 连接与 NAS 工具安装手册

> 验证日期：2026-08-14  
> 适用主机：10.18.15.135、10.18.15.141  
> 连接端口：9222，登录用户：`test`  
> 官方依据：OpenAI 官方文档（Codex CLI、Remote connections、Authentication）

## 1. 结论摘要

1. SSH 连接问题已解决：10.18.15.135 和 10.18.15.141 现在都支持使用本机 `id_ed25519_codex` 密钥免密连接。
2. Codex 远程项目对 SSH 主机的核心要求：
   - 本机 `~/.ssh/config` 中有可被 OpenSSH 解析的主机别名；
   - 本机能直接 `ssh <别名>` 连到远端；
   - 远端已安装 Codex CLI；
   - 远端登录 shell 的 `PATH` 中能找到 `codex`；
   - 远端 Codex 已完成登录认证。
3. 10.18.15.141 已自动安装并验证：
   - `codex-cli 0.147.0`
   - Node.js `v22.23.2`
   - npm `10.9.8`
   - git `2.34.1`
4. 当前唯一剩余步骤：10.18.15.141 的 `codex login status` 显示 `Not logged in`，需要完成一次登录认证后才能被 Codex 桌面端作为 SSH 远端项目使用。

## 2. 本机 SSH 配置

本机配置文件：`C:\Users\twm\.ssh\config`

```text
Host 15.135
    HostName 10.18.15.135
    User test
    Port 9222
    IdentityFile ~/.ssh/id_ed25519_codex

Host 15.141
    HostName 10.18.15.141
    User test
    Port 9222
    IdentityFile ~/.ssh/id_ed25519_codex
```

主机密钥指纹（用于首次连接确认或 `plink -hostkey`）：

| 主机 | SSH 密钥类型 | SHA256 指纹 |
| --- | --- | --- |
| 10.18.15.135:9222 | ssh-ed25519 | `SHA256:4ldRJXmw5vUbYdUwcmuH/ZUU2OQL42ZMCeTnQrubJjQ` |
| 10.18.15.141:9222 | ssh-ed25519 | `SHA256:ikQbEZqlmBFWFcZAQQMzAsRwE2eVx3N2Ya6mox4zCyE` |

## 3. 连接方法

### 3.1 推荐方式：OpenSSH 密钥

两台 NAS 的公钥认证都已配置完成，直接使用配置别名：

```bash
ssh 15.135
ssh 15.141
```

非交互验证：

```bash
ssh -o BatchMode=yes -p 9222 -i ~/.ssh/id_ed25519_codex test@10.18.15.135 "id; hostname"
ssh -o BatchMode=yes -p 9222 -i ~/.ssh/id_ed25519_codex test@10.18.15.141 "id; hostname"
```

预期输出中包含 `uid=0(test)` 和 `TNAS`。

### 3.2 密码回退方式：PuTTY plink

当密钥不可用时，可用本机已安装的 PuTTY 非交互登录，密码不要写入文档或脚本：

```powershell
plink -batch -ssh -P 9222 -l test -pw <NAS密码> `
  -hostkey "ssh-ed25519 255 SHA256:4ldRJXmw5vUbYdUwcmuH/ZUU2OQL42ZMCeTnQrubJjQ" `
  10.18.15.135 "id; hostname"
```

### 3.3 首次连接

首次连接时确认主机指纹与第 2 节一致后输入 `y`。不要只凭提示直接接受；如果主机密钥变化，先确认 NAS 是否重装或变更过 SSH 服务。

### 3.4 已遇到的连接故障

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `Permission denied (publickey,password,...)` | `authorized_keys` 中没有本机公钥 | 追加 `id_ed25519_codex.pub` 到 `/home/test/.ssh/authorized_keys`，权限设为 `700/600` |
| `The host key is not cached` | PuTTY 没有该主机记录 | 使用 `-hostkey` 固定指纹，或首次交互确认 |
| `scp` / SFTP `Connection closed` | 该 NAS 对文件传输通道兼容性差 | 使用 `scp -O` 传统协议，或用 plink 标准输入 base64 传文件 |
| `chatgpt.com` 连接超时 | NAS 外网访问受限 | 本机下载官方安装包后再传给 NAS，或使用 GitHub 发布源 |

## 4. Codex 对 SSH 远端的要求

官方 Remote connections 文档说明，桌面端连接 SSH 主机后，远端项目聊天会在远端文件系统与 shell 上执行命令。具体要求：

1. 把主机加入本机 `~/.ssh/config`，Codex 只读取具体主机别名，并交给 OpenSSH 解析；纯 pattern 主机不会自动发现。
2. 从运行桌面端的机器确认 `ssh <别名>` 可以连通。
3. 在远端主机安装 Codex CLI。
4. 在远端主机完成 Codex 登录认证。
5. 桌面端会通过 SSH 启动远端 Codex app server，使用远端用户的登录 shell，因此 `codex` 必须出现在该登录 shell 的 `PATH` 中。

登录认证方式：

```bash
# 有浏览器时
codex login

# 无头/远端环境优先
codex login --device-auth

# API Key
printenv OPENAI_API_KEY | codex login --with-api-key
```

也可以把已登录机器的 `~/.codex/auth.json` 复制到远端；该文件等同密码，不能提交到仓库、不能写入文档。

官方安装命令：

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

实际环境中，NAS 访问 `chatgpt.com` 会超时，因此 10.18.15.141 采用本机下载官方包后传输安装的方式。

## 5. 示例：10.18.15.135

### 5.1 初始状态

- OpenSSH 密钥连接失败：`Permission denied (publickey,password,keyboard-interactive)`。
- 系统：TNAS，Ubuntu 22.04.3 LTS，内核 `6.12.63+`，x86_64。
- 用户：`test`，`uid=0`，属于 `admin` 组，具备 root 权限。
- 工具状态：`node`、`npm`、`codex`、`git` 均为 MISSING。

### 5.2 处理结果

通过 plink 密码登录后，把本机公钥追加到：

```text
/home/test/.ssh/authorized_keys
```

再次验证：

```bash
ssh -o BatchMode=yes -p 9222 -i ~/.ssh/id_ed25519_codex test@10.18.15.135 "echo KEY_OK_135; id"
```

结果：`KEY_OK_135`，连接问题解决。

### 5.3 与 Codex 的差距

10.18.15.135 目前只完成了 SSH 连接，仍缺少 Codex 远程项目所需的 Node.js、npm、Codex CLI。若需要在这台机器运行 Codex 远端项目，按第 6 节对 10.18.15.141 执行的同一套安装步骤操作。

## 6. 示例：10.18.15.141 工具安装

### 6.1 安装前状态

- `node`、`npm`、`codex`、`git` 均为 MISSING。
- 系统：TNAS，Ubuntu 22.04.3 LTS，内核 `6.12.63+`，x86_64。
- 用户：`test`，`uid=0`，`apt`、`systemd` 可用。
- 网络：`chatgpt.com` 超时、`releases.openai.com` 403、GitHub 可达、`nodejs.org` 可达、Ubuntu apt 源可达。

### 6.2 安装结果

| 工具 | 版本 | 安装位置 |
| --- | --- | --- |
| Codex CLI | `codex-cli 0.147.0` | `/usr/local/bin/codex` |
| Node.js | `v22.23.2` | `/usr/local/bin/node` |
| npm | `10.9.8` | `/usr/local/bin/npm` |
| npx | `10.9.8` | `/usr/local/bin/npx` |
| git | `2.34.1` | `/usr/bin/git` |

### 6.3 Codex 安装命令（离线包方式）

本机下载官方发布包并校验：

```bash
curl -L -o codex-package.tar.gz \
  https://github.com/openai/codex/releases/download/rust-v0.147.0/codex-package-x86_64-unknown-linux-musl.tar.gz
sha256sum codex-package.tar.gz
```

传送到 NAS（该 NAS 的 SFTP 通道会断开，使用 `scp -O`）：

```bash
scp -O -P 9222 -i ~/.ssh/id_ed25519_codex \
  codex-package.tar.gz test@10.18.15.141:/home/test/
```

远端按官方 standalone 目录布局安装：

```bash
REL=/home/test/.codex/packages/standalone/releases/0.147.0
mkdir -p "$REL"
tar -xzf /home/test/codex-package.tar.gz -C "$REL"
chmod 0755 "$REL/bin/codex" "$REL/bin/codex-code-mode-host" "$REL/codex-path/rg"
chmod 0755 "$REL/codex-resources/bwrap"
ln -sfn "$REL" /home/test/.codex/packages/standalone/current
ln -sfn /home/test/.codex/packages/standalone/current/bin/codex /usr/local/bin/codex
ln -sfn /home/test/.codex/packages/standalone/current/bin/codex-code-mode-host /usr/local/bin/codex-code-mode-host
```

### 6.4 Node.js 与 npm 安装命令

```bash
BASE=https://nodejs.org/dist/latest-v22.x
VER=$(curl -sS "$BASE/SHASUMS256.txt" | awk '/linux-x64.tar.xz/{print $2; exit}')
curl -sS -o "/home/test/$VER" "$BASE/$VER"
curl -sS -o /home/test/SHASUMS256.txt "$BASE/SHASUMS256.txt"
cd /home/test && grep "$VER" SHASUMS256.txt | sha256sum -c -
mkdir -p /usr/local/lib/nodejs
tar -xJf "/home/test/$VER" -C /usr/local/lib/nodejs
NODE_DIR="/usr/local/lib/nodejs/${VER%.tar.xz}"
ln -sfn "$NODE_DIR/bin/node" /usr/local/bin/node
ln -sfn "$NODE_DIR/bin/npm" /usr/local/bin/npm
ln -sfn "$NODE_DIR/bin/npx" /usr/local/bin/npx
```

### 6.5 git 安装命令

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git
```

## 7. 验证结果

10.18.15.141 最终验证：

```text
command -v codex   => /usr/local/bin/codex
codex --version    => codex-cli 0.147.0
node -v            => v22.23.2
npm -v             => 10.9.8
npx --version      => 10.9.8
git --version      => git version 2.34.1
codex login status => Not logged in
```

登录 shell 验证：

```text
bash -lc 'command -v codex; codex --version'
=> /usr/local/bin/codex
=> codex-cli 0.147.0
```

## 8. 剩余操作

1. 在 10.18.15.141 执行 `codex login --device-auth`，或把已登录机器的 `~/.codex/auth.json` 复制过去。
2. 在 ChatGPT/Codex 桌面端打开 `Settings > Connections > SSH`，添加别名 `15.141` 并选择远端项目目录。
3. 若 10.18.15.135 也需要跑 Codex，按第 6 节安装 Node.js、npm、git、Codex CLI，并完成登录。

## 9. 安全说明

- NAS 密码不得写入脚本、文档或记忆文件；优先使用密钥认证。
- `~/.codex/auth.json` 包含访问令牌，等同密码，不能提交或粘贴到聊天中。
- `authorized_keys` 只添加信任的公钥，保持 `~/.ssh` 权限为 `700`、`authorized_keys` 为 `600`。

## 10. 官方参考

- [Codex CLI 官方文档](https://learn.chatgpt.com/codex/cli)
- [Remote connections 官方文档](https://learn.chatgpt.com/codex/remote-connections)
- [Authentication 官方文档](https://learn.chatgpt.com/codex/auth)
