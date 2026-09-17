import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath = process.env.WB_PATH;
const outputPath = process.env.OUT_PNG;

if (!workbookPath || !outputPath) {
  throw new Error("WB_PATH and OUT_PNG are required");
}

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
workbook.recalculate();

const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  range: "A1:K34",
  maxChars: 12000,
  tableMaxRows: 34,
  tableMaxCols: 11,
  tableMaxCellChars: 120,
});
console.log(summary.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "测试用例",
  range: "A1:K34",
  scale: 1,
  format: "png",
});
await fs.writeFile(outputPath, new Uint8Array(await preview.arrayBuffer()));
console.log(outputPath);
