import {existsSync, mkdirSync, copyFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
// This script lives at frontend/scripts/sync-docs.mjs. Two levels up is the
// repo root in local dev; in the Docker build, README.md/REPORT.md are
// copied to the filesystem root (one level above /app) at the same
// relative distance -- see frontend/Dockerfile.
const repoRoot = join(__dirname, "..", "..");
const destDir = join(__dirname, "..", "public", "docs");

mkdirSync(destDir, {recursive: true});

for (const name of ["README.md", "REPORT.md"]) {
    const src = join(repoRoot, name);
    if (existsSync(src)) {
        copyFileSync(src, join(destDir, name));
        console.log(`[sync-docs] copied ${name}`);
    } else {
        console.warn(`[sync-docs] ${name} not found at ${src} -- /doc page will show a fetch error for it`);
    }
}
