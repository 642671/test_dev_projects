# Git 提交与同步指南

> 适用于本项目（test_dev_projects）的日常提交操作

---

## 一、基本概念

| 术语 | 含义 |
|------|------|
| **工作区** | 你正在编辑的文件（本地磁盘上的文件） |
| **暂存区** | 准备提交的文件（执行 `git add` 后进入） |
| **本地仓库** | 已提交的文件版本库（执行 `git commit` 后保存） |
| **远程仓库** | GitHub 上的仓库，需要 `git push` 同步 |

---

## 二、方式一：终端命令行（推荐）

### 2.1 查看当前变更状态

```bash
git status          # 查看哪些文件有改动
git status --short  # 简短格式（M=修改, D=删除, ??=未跟踪）
```

### 2.2 提交所有变更（最常用）

```bash
# 第一步：将所有变更加入暂存区
git add .

# 第二步：提交到本地仓库（必须写有意义的提交信息）
git commit -m "描述你做了什么，例如：修复登录测试用例的定位器"

# 第三步：推送到 GitHub 远程仓库
git push origin main
```

### 2.3 只提交特定文件

```bash
# 只提交某个文件
git add test_automation/ui_automation/testcases/smoke/test_tos_login.py

# 提交某个目录下的所有变更
git add test_automation/ui_automation/pages/

# 然后提交并推送
git commit -m "更新登录页面的 Page 对象"
git push origin main
```

### 2.4 查看提交历史

```bash
git log --oneline      # 简短格式，每行一条提交
git log --oneline -10  # 最近 10 条提交
```

### 2.5 撤销操作

```bash
# 撤销工作区的改动（恢复到上次提交的状态）
git checkout -- 文件名

# 取消暂存（从暂存区移出，但不修改文件）
git reset HEAD 文件名

# 撤销上一次 commit（保留文件改动）
git reset --soft HEAD~1
```

### 2.6 分支操作

```bash
git branch           # 查看本地分支
git checkout win     # 切换到 win 分支（Windows 开发用）
git checkout main    # 切回 main 分支
git merge win        # 将 win 分支的改动合并到 main
```

---

## 三、方式二：VS Code 左侧边栏（图形界面）

### 3.1 找到源代码管理面板

- 点击左侧边栏的 **源代码管理图标**（分支形状的图标，第三个）
- 或按快捷键 `Ctrl+Shift+G`（Win） / `Cmd+Shift+G`（Mac）

### 3.2 提交文件（Commit）

**步骤：**

1. **查看变更列表**：左侧面板会列出所有已修改/新增/删除的文件
   - `M` 标记 = 修改（Modified）
   - `U` 标记 = 未跟踪（Untracked）
   - `D` 标记 = 删除（Deleted）

2. **暂存文件**：点击每个文件右侧的 **`+`** 按钮（或 `Stage Changes`）
   - 全部暂存：点击 "Changes" 标题右侧的 `+` 按钮

3. **填写提交信息**：在顶部的输入框中输入本次提交的说明

4. **提交**：点击输入框上方的 **`✓`** 按钮（Commit）

> **注意**：Commit 只是保存到本地仓库，还没有推送到 GitHub

### 3.3 同步到远程（Sync）

**方法一：使用"同步"按钮**
- 提交后，VS Code 左下角状态栏会显示 **↑数字 ↓数字**（待推送/待拉取的提交数）
- 点击这个按钮，即可同时完成 **Pull（拉取）+ Push（推送）**

**方法二：手动推送**
- 按 `Cmd+Shift+P`（Mac） / `Ctrl+Shift+P`（Win）
- 输入 `Git: Push` → 回车

**方法三：推送并拉取（推荐）**
- 按 `Cmd+Shift+P` → 输入 `Git: Pull (Rebase)` 或 `Git: Sync`

### 3.4 查看单个文件的变更

- 在源代码管理面板中点击某个文件
- 会打开 **Diff 视图**：左边是旧版本，右边是新版本
- 红色 = 删除，绿色 = 新增

### 3.5 丢弃某个文件的改动

- 在源代码管理面板中找到该文件
- 点击文件右侧的 **撤销图标**（弯箭头，Discard Changes）
- ⚠️ 这会永久丢失该文件的修改，请谨慎使用

---

## 四、日常操作标准流程

```
编写/修改代码
      ↓
git status  →  确认改了哪些文件
      ↓
git add .   →  全部暂存（或 git add 指定文件）
      ↓
git commit -m "说明"  →  提交到本地
      ↓
git push origin main  →  推送到 GitHub
```

---

## 五、提交信息规范

好的提交信息应该简洁描述"做了什么"：

| 前缀 | 含义 | 示例 |
|------|------|------|
| `feat:` | 新功能 | `feat: 添加存储管理页面 Page 对象` |
| `fix:` | 修复 Bug | `fix: 修复登录用例的元素定位器` |
| `refactor:` | 重构代码 | `refactor: 将配置迁移至模块内部` |
| `docs:` | 更新文档 | `docs: 补充 API 接口文档` |
| `test:` | 添加测试 | `test: 增加导航栏冒烟测试用例` |
| `chore:` | 其他杂项 | `chore: 更新 requirements.txt` |

---

## 六、常见问题

### Q：push 时报错 `RPC failed; curl 16 Error`

这是 HTTP/2 协议不稳定的问题，临时切换到 HTTP/1.1：

```bash
git config --global http.version HTTP/1.1
git push origin main
git config --global --unset http.version   # 推送完成后恢复
```

### Q：push 时报错 `rejected` / `non-fast-forward`

远程仓库有你本地没有的新提交，需要先拉取：

```bash
git pull origin main
git push origin main
```

### Q：误提交了不需要的文件怎么办

```bash
git reset HEAD~1              # 撤销上一次提交（文件不变）
# 然后重新 git add 正确的文件，再次 commit
```

### Q：VS Code 侧边栏提交后 GitHub 上没有变化

Commit 只保存到本地，还需要 **Push（推送）** 才能到 GitHub。点击左下角的同步按钮或在命令面板执行 `Git: Push`。

---

## 七、本项目远程仓库地址

```
https://github.com/642671/test_dev_projects.git
```

分支说明：
- `main` — Mac 主开发分支
- `win` — Windows 开发分支（跨平台协作时使用）
