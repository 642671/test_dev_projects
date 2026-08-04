// GET /v2/storage/edit/volume/:uuid 后置脚本
// 按卷名生成 {卷名}_mnt_path，空就删

const data = pm.response.json().data;

const mntPath = data.mntpath || '';

console.log('卷名:', data.name);
console.log('挂载路径:', mntPath);

if (mntPath) {
    pm.environment.set(`${data.name}_mnt_path`, mntPath);
    console.log(`已设置 ${data.name}_mnt_path = ${mntPath}`);
} else {
    pm.environment.unset(`${data.name}_mnt_path`);
    console.log(`已删除 ${data.name}_mnt_path`);
}
