import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const npmRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(npmRoot, "..");

const srcPricing = path.join(repoRoot, "data", "pricing.json");
const destDataDir = path.join(npmRoot, "data");
const destPricing = path.join(destDataDir, "pricing.json");

if (fs.existsSync(srcPricing)) {
  fs.mkdirSync(destDataDir, { recursive: true });
  fs.copyFileSync(srcPricing, destPricing);
}

const srcLicense = path.join(repoRoot, "LICENSE");
const destLicense = path.join(npmRoot, "LICENSE");
if (fs.existsSync(srcLicense)) {
  fs.copyFileSync(srcLicense, destLicense);
}
