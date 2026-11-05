import fs from 'node:fs/promises';
import validator from 'gltf-validator';
const path='public/assets/XR_Guild_Library_v2.glb';
const report=await validator.validateBytes(new Uint8Array(await fs.readFile(path)), {uri:path,maxIssues:100});
await fs.writeFile('../evidence/gltf_validation.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report.issues,null,2));
if(report.issues.numErrors) process.exitCode=1;
