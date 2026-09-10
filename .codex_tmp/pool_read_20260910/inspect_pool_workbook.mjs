import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "D:/test_dev_projects/接口测试用例/单个接口测试用例/Storage_Management_03_存储池接口测试用例.xlsx";
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const overview = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 9000,
  tableMaxRows: 8,
  tableMaxCols: 12,
  tableMaxCellChars: 120,
});
console.log("OVERVIEW");
console.log(overview.ndjson);

for (const term of [
  "正常|降阶|损坏|可用池|创建中|挂载中|删除中|同步中|修复中|配置中|更换磁盘|数据清理",
  "RAID0|RAID1|RAID5|RAID6|RAID10|JBOD|Single|TRAID\\+?|single disk",
  "阵列修复|添加磁盘|更换磁盘|阵列迁移|Data Scrubbing|Bitmap|创建存储池|删除存储池|挂载存储池",
]) {
  const matches = await workbook.inspect({
    kind: "match",
    searchTerm: term,
    options: { useRegex: true, maxResults: 300 },
    maxChars: 30000,
  });
  console.log(`MATCH ${term}`);
  console.log(matches.ndjson);
}
