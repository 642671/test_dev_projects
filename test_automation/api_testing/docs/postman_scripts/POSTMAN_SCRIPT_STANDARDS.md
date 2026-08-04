# Postman / Apifox 后置脚本编写规范

> 适用范围：`api_testing/docs/postman_scripts/` 目录下所有 Post Response Script。
> 目标：保证模块变量始终 **等于当前系统真实状态**，永不残留、永不错位。

---

## 0. 一句话总原则

> **每次执行 = 先清理旧的 → 再写入新的 → 没值就 unset。**

模块变量 / 环境变量不能"越滚越多"。同一份脚本运行 100 次，最终变量集合必须只反映**最后一次**接口响应。

---

## 1. 强制规范（Must）

### 1.1 每次请求必须删除旧变量

任何"批量生成一组变量"的脚本，**必须在写入前先清理同前缀的旧变量**。

**推荐方式 A：动态扫描前缀（无上限，最稳）**

```js
const all = pm.moduleVariables.toObject();
Object.keys(all)
    .filter(k => k.startsWith('cv_'))     // 换成你的前缀
    .forEach(k => pm.moduleVariables.unset(k));
```

**推荐方式 B：固定上限循环（简单直接）**

```js
for (let i = 0; i < 50; i++) {
    pm.moduleVariables.unset(`cap_disk${i}`);
}
```

> ⚠️ 禁止只清理"本次要写"的那几个变量 —— 上次多写的会漏掉。

---

### 1.2 有值就 set，没值就 unset —— 禁用 `|| ''` 兜底

**❌ 错误写法**：会把空字符串 / 0 写进变量，看上去像还在，实际是空的。

```js
pm.moduleVariables.set('cv_disk_0_path', freeDisks[0]?.value || '');
pm.moduleVariables.set('cv_new_pool_sort', poolInfo.sort || 0);
```

**✅ 正确写法**：

```js
if (freeDisks[0]?.value) {
    pm.moduleVariables.set('cv_disk_0_path', freeDisks[0].value);
} else {
    pm.moduleVariables.unset('cv_disk_0_path');
}
```

**✅ 更简洁**：封装小工具函数（推荐所有脚本复用）

```js
function setOrUnset(key, val) {
    if (val === undefined || val === null || val === '' || Number.isNaN(val)) {
        pm.moduleVariables.unset(key);
    } else {
        pm.moduleVariables.set(key, val);
    }
}
```

> 布尔值 `false` 有明确语义（"不可用"），应当直接 `set`，不属于本规则约束的空值。

---

### 1.3 字符串必须 `.trim()`

从响应体取出的设备名、池名等字符串，**在写入变量前必须 `.trim()`**，防止首尾空格导致 URL 里出现 `%20`。

```js
const disks = res.data.map(d => d.device.replace(/^\/dev\//, '').trim());
```

**血泪教训**：`{{cap_disk0}}` 变量显示 `sdc`，但请求实际发出 `sdc%20`，就是因为 device 字段末尾有一个空格没被裁掉。

---

### 1.4 变量编号采用 **sort - 1** 零基映射

用户看到的卷/池编号从 `1` 起（`sort=1`），但变量命名从 `0` 起（`lv0`、`vg0`）。

```js
volumes.forEach(v => {
    const idx = v.sort - 1;               // sort=1 → lv0
    pm.moduleVariables.set(`lv${idx}_uuid`, v.uuid);
    pm.moduleVariables.set(`lv${idx}_filesystem`, v.filesystem);
});
```

好处：中间删掉一个卷（比如原本 sort=1,2,3，删了 sort=2）时，变量名依旧准确对应，不会错位。

---

### 1.5 变量命名规范：接口专用前缀

**必须**用 2~3 字母前缀标识该变量归属于哪个接口/业务，方便一眼看出用途、避免冲突。

| 前缀 | 归属接口 | 示例 |
|---|---|---|
| `cv_` | GET `/v2/storage/create/volume` 创建卷资源 | `cv_disk_0_path`、`cv_selected_pool_name` |
| `cap_` | GET `/v2/storage/CheckAvailablePool/{disk}` 磁盘校验 | `cap_disk0`、`cap_disk_count` |
| `lv{N}_` | 卷列表同步 | `lv0_uuid`、`lv0_filesystem` |
| `vg{N}_` | 存储池列表同步 | `vg0_uuid` |

> 加前缀后，1.1 的"扫描前缀清理"才有意义。

---

### 1.6 保留注释

脚本头部必须写清楚：**做什么、为什么、变量清单**。已存在的注释**不要删**，用户会自己回看。

推荐结构：

```js
// ============================================================
// GET /v2/xxx/yyy 后置脚本
// 解析返回 → 写入模块变量 → 供后续 POST zzz 使用
// ------------------------------------------------------------
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 中的强制规范：
//   1. 每次执行必须先清理旧的同前缀变量
//   2. 有值就 set，没值就 unset
//   3. 变量按业务字段命名，不依赖数组下标
// ============================================================
```

---

## 2. 推荐规范（Should）

### 2.1 优先 `pm.moduleVariables`，不用 `pm.environment`

模块变量作用域小，不同项目/接口目录之间互不干扰。除非需要跨模块共享，否则一律用 `pm.moduleVariables`。

### 2.2 空响应容错

响应可能没有 `data` 字段（500、鉴权失败等），脚本前面加防御：

```js
const res = pm.response.json();
if (!res.data) {
    console.log('响应 data 为空，停止生成变量。');
    return;
}
```

### 2.3 加 `pm.test` 校验响应结构

对于关键字段，用 `pm.test` 断言，让脚本在响应结构变化时立刻报警。

```js
pm.test('响应结构正确', () => {
    pm.expect(data).to.have.property('free_disk');
    pm.expect(data.free_disk).to.be.an('array');
});
```

### 2.4 打印调试日志

每个脚本尾部固定打印一段"变量总览"，方便排查：

```js
console.log('==== xxx 资源一览 ====');
console.log(`磁盘数量: ${disks.length}`);
console.log(`已写入变量: ${Object.keys(pm.moduleVariables.toObject()).filter(k => k.startsWith('cv_')).join(', ')}`);
```

---

## 3. 禁止清单（Must Not）

| 禁止项 | 原因 |
|---|---|
| `pm.xxx.set(key, val \|\| '')` | 会写入空字符串，看似有值实为空 |
| `pm.xxx.set(key, val \|\| 0)` | 同上，`0` 会被后续接口当成合法输入 |
| 仅清理"本次要写"的变量 | 遗漏上次多写的变量 |
| 数组下标当变量编号（`lv0=arr[0]`） | 中间删项后编号错位 |
| 变量名不加接口前缀 | 后续接口共享变量池时冲突 |
| 删除现有脚本注释 | 用户需要回看注释 |
| 硬编码 `/dev/` 前缀截断（`sdb`） | 部分接口需要完整路径 `/dev/sdb` |

---

## 4. 脚本模板（复制即用）

```js
// ============================================================
// GET /v2/xxx/yyy 后置脚本
// 遵循 POSTMAN_SCRIPT_STANDARDS.md 强制规范
// ============================================================

const res = pm.response.json();
if (!res.data) {
    console.log('响应 data 为空，停止执行。');
    return;
}
const data = res.data;

// -- 工具函数 --
function setOrUnset(key, val) {
    if (val === undefined || val === null || val === '' || Number.isNaN(val)) {
        pm.moduleVariables.unset(key);
    } else {
        pm.moduleVariables.set(key, val);
    }
}

// -- 0. 清理旧变量 --
const PREFIX = 'xxx_';   // ← 改成你的前缀
Object.keys(pm.moduleVariables.toObject())
    .filter(k => k.startsWith(PREFIX))
    .forEach(k => pm.moduleVariables.unset(k));

// -- 1. 响应校验 --
pm.test('响应结构正确', () => {
    pm.expect(data).to.be.an('object');
});

// -- 2. 写入新变量 --
// setOrUnset('xxx_foo', data.foo);
// setOrUnset('xxx_bar', (data.bar || '').trim());

// -- 3. 调试输出 --
console.log(`==== ${PREFIX} 已同步 ====`);
console.log(pm.moduleVariables.toObject());
```

---

## 5. 现有脚本一览

| 文件 | 归属接口 | 前缀 |
|---|---|---|
| `extract_pool_check_disk.js` | GET `/v2/storage/edit/pool/:uuid` | `{池名}_check_disk` |
| `extract_volume_mntpath.js` | GET `/v2/storage/edit/volume/:uuid` | `{卷名}_mntpath` |
| `extract_create_volume_resources.js` | GET `/v2/storage/create/volume` | `cv_` |
| `sync_pool_uuid.js` | GET 存储池列表 | `vg{N}_uuid` |
| `sync_volume_uuid.js` | GET 卷列表 | `lv{N}_uuid`、`lv{N}_filesystem` |
| `sync_disk_device.js` | GET 磁盘列表 | `cap_disk{N}`、`cap_disk_count` |

---

## 6. 变更历史

| 日期 | 变更 |
|---|---|
| 2026-07-14 | 初版：确立"清理旧变量 + 有值就 set 没值就 unset + sort-1 零基映射 + trim + 前缀命名"六大铁则 |
