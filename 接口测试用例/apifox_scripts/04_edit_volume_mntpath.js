// ============================================================
// GET /v2/storage/edit/volume/{uuid} 后置脚本
// 按卷名生成变量，空就删，每次执行得到最新结果
// ------------------------------------------------------------
// 生成变量：
//   {卷名}_mnt_path  - 卷挂载路径（environment）
//   {卷名}_sort      - 卷 sort 编号（moduleVariables）
// 如：lv0_mnt_path = /Volume1, lv0_sort = 1
// ============================================================

const data = pm.response.json().data;

const mntPath = data.mntpath || '';
const sort = data.sort;

console.log('卷名:', data.name);
console.log('挂载路径:', mntPath);
console.log('sort:', sort);

// --- {卷名}_mnt_path ---
if (mntPath) {
    pm.environment.set(`${data.name}_mnt_path`, mntPath);
    console.log(`已设置 ${data.name}_mnt_path = ${mntPath}`);
} else {
    pm.environment.unset(`${data.name}_mnt_path`);
    console.log(`已删除 ${data.name}_mnt_path`);
}

// --- {卷名}_sort ---
if (sort !== undefined && sort !== null && sort !== '') {
    pm.moduleVariables.set(`${data.name}_sort`, sort);
    console.log(`已设置 ${data.name}_sort = ${sort}`);
} else {
    pm.moduleVariables.unset(`${data.name}_sort`);
    console.log(`已删除 ${data.name}_sort`);
}
