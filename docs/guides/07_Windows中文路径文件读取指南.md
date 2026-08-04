# Windows 中文路径文件读取指南

## 问题背景

在 Qoder 终端（PowerShell）中读取含中文路径的文件时，经常出现乱码问题。

### 典型表现

```powershell
# PowerShell 直接读取 → 乱码
Get-ChildItem "D:\test_dev_projects\接口测试用例"
# 输出: 鎺ュ彛娴嬭瘯鐢緥

# PowerShell COM 打开 Excel → 路径乱码找不到文件
$wb = $excel.Workbooks.Open("D:\test_dev_projects\接口测试用例\test.xlsx")
# 错误: 找不到路径 "D:\test_dev_projects\鎺ュ彛娴嬭瘯鐢ㄤ緥\test.xlsx"
```

### 根本原因

Qoder 终端的 PowerShell 使用 Node fallback 模式执行命令，该模式下 **终端编码与文件系统编码不一致**，导致中文字符串在传递过程中被错误解码。

---

## 解决方案

### 核心原则

> **让 Node.js 处理文件 I/O，PowerShell 只负责读取 Node.js 输出的 UTF-8 文件。**

Node.js 的 `fs` 模块原生支持 UTF-8，不受终端编码影响。

---

### 方案一：读取 JSON 文件

```javascript
// read_json.js
const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', '接口测试用例', 'api.json');
const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));

// 将结果写入 UTF-8 文件
const output = JSON.stringify(data, null, 2);
fs.writeFileSync(path.join(__dirname, 'output.txt'), output, 'utf-8');
console.log('Done');
```

执行：
```bash
node d:\test_dev_projects\temp_scripts\read_json.js
```

然后用 PowerShell 读取输出文件（此时无乱码）：
```powershell
Get-Content "d:\test_dev_projects\temp_scripts\output.txt" -Encoding UTF8
```

---

### 方案二：读取 Excel 文件（.xlsx）

#### 前置条件

安装 `xlsx` 包（只需一次）：
```bash
cd d:\test_dev_projects\temp_scripts
npm install xlsx
```

#### 脚本模板

```javascript
// read_excel.js
const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx');

// 1. 用 Node.js 定位文件（中文路径无问题）
const dir = path.join(__dirname, '..', '接口测试用例', '单个接口测试用例');
const files = fs.readdirSync(dir).filter(f => f.endsWith('.xlsx') && !f.startsWith('~$'));
const excelFile = files.find(f => f.includes('存储管理'));

if (!excelFile) {
  console.log('Excel file not found');
  process.exit(1);
}

const excelPath = path.join(dir, excelFile);
console.log(`Reading: ${excelFile}`);

// 2. 用 xlsx 库读取（纯 JS，无编码问题）
const workbook = XLSX.readFile(excelPath);
const sheetName = workbook.SheetNames[0];
const worksheet = workbook.Sheets[sheetName];
const data = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

// 3. 格式化输出
let output = `=== Sheet: ${sheetName} ===\n`;
output += `Rows: ${data.length}, Cols: ${data[0]?.length || 0}\n`;
output += `Headers: ${data[0]?.join(' | ')}\n`;

for (let i = 1; i < data.length; i++) {
  output += `--- Row ${i + 1} ---\n`;
  const row = data[i];
  for (let j = 0; j < row.length; j++) {
    if (row[j] && data[0][j]) {
      output += `[${data[0][j]}]: ${row[j]}\n`;
    }
  }
}

// 4. 写入 UTF-8 文件
const outputPath = path.join(__dirname, 'excel_output.txt');
fs.writeFileSync(outputPath, output, 'utf-8');
console.log(`Done: ${outputPath}`);
```

执行：
```bash
node d:\test_dev_projects\temp_scripts\read_excel.js
```

读取结果：
```powershell
Get-Content "d:\test_dev_projects\temp_scripts\excel_output.txt" -Encoding UTF8
```

---

### 方案三：读取任意文本文件

```javascript
// read_file.js
const fs = require('fs');
const path = require('path');

const filePath = process.argv[2]; // 从命令行参数获取路径
const content = fs.readFileSync(filePath, 'utf-8');

const outputPath = path.join(__dirname, 'file_output.txt');
fs.writeFileSync(outputPath, content, 'utf-8');
console.log('Done');
```

执行：
```bash
node d:\test_dev_projects\temp_scripts\read_file.js "D:\test_dev_projects\接口测试用例\test.txt"
```

---

## 已封装的工具脚本

以下脚本已保存在 `temp_scripts/` 目录，可直接复用：

| 脚本 | 用途 | 依赖 |
|------|------|------|
| `read_docs.js` | 读取 JSON 接口文档并输出 | 无（Node.js 内置） |
| `read_excel_xlsx.js` | 读取 Excel 测试用例并输出 | `xlsx` npm 包 |

### 快速使用

```bash
# 读取 JSON API 文档
node d:\test_dev_projects\temp_scripts\read_docs.js

# 读取 Excel 测试用例
node d:\test_dev_projects\temp_scripts\read_excel_xlsx.js
```

输出文件统一保存在 `temp_scripts/` 目录下：
- `api_output.txt` — JSON 文档输出
- `excel_output.txt` — Excel 文档输出

---

## 注意事项

1. **不要**在 PowerShell 命令中直接写中文路径字符串
2. **不要**依赖 PowerShell COM 对象打开中文路径的 Excel
3. **优先**使用 Node.js `fs` 模块处理文件 I/O
4. 读取输出文件时务必加 `-Encoding UTF8` 参数
5. `xlsx` 包只需安装一次，安装在 `temp_scripts/node_modules/` 下

---

## 为什么不用 Python？

当前环境的 Python 是 Microsoft Store 占位符（`C:\Users\twm\AppData\Local\Microsoft\WindowsApps\python.exe`），实际不可用。Node.js v24.14.0 已安装且可正常使用。
