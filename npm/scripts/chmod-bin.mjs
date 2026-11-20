import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const entryFile = path.resolve(__dirname, "..", "dist", "index.js");

if (fs.existsSync(entryFile)) {
  fs.chmodSync(entryFile, 0o755);
}
