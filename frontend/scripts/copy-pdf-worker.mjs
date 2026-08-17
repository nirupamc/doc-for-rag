import { copyFile, mkdir } from "node:fs/promises"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const workerSource = resolve(
  frontendRoot,
  "node_modules/pdfjs-dist/build/pdf.worker.min.js",
)
const workerTarget = resolve(frontendRoot, "public/pdf.worker.min.js")

await mkdir(dirname(workerTarget), { recursive: true })
await copyFile(workerSource, workerTarget)

console.log("Copied the installed PDF.js worker to public/pdf.worker.min.js")
