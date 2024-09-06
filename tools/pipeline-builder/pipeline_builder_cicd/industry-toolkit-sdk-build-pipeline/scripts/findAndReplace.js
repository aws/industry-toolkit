// Recursively read all .ts files in current directory, find if string 'rxjs/Observable' exists in that file, if it does replace it with string 'rxjs'. Ignore the node_modules directory.
const fs = require('fs');
const path = require('path');

const currentDir = process.cwd();
const ignoreDirs = ['node_modules'];

function findAndReplace(dir) {
    const files = fs.readdirSync(dir);
    files.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        if (stat.isDirectory() && !ignoreDirs.includes(file)) {
            findAndReplace(filePath);
        } else if (path.extname(file) === '.ts') {
            let content = fs.readFileSync(filePath, 'utf8');
            const updatedContent = content.replace(/rxjs\/Observable/g, 'rxjs');
            if (updatedContent !== content) {
                fs.writeFileSync(filePath, updatedContent);
                console.log(`Updated: ${filePath}`);
            }
        }
    });
};
findAndReplace(currentDir);
console.log('Done');


// Read tsconfig.json in current directory, find if "suppressImplicitAnyIndexErrors": true, exists, if it does remove it.
const tsconfigPath = path.join(currentDir, 'tsconfig.json');
let tsconfigContent = fs.readFileSync(tsconfigPath, 'utf8');
const tsconfig = JSON.parse(tsconfigContent);

if (tsconfig.compilerOptions.suppressImplicitAnyIndexErrors) {
    delete tsconfig.compilerOptions.suppressImplicitAnyIndexErrors;
    tsconfigContent = JSON.stringify(tsconfig, null, 2);
    fs.writeFileSync(tsconfigPath, tsconfigContent);
    console.log(`Updated tsconfig.json`);
};

// Add import { from } from 'rxjs' to HttpClient.ts in current directory
const httpClientPath = path.join(currentDir, 'HttpClient.ts');
let httpClientContent = fs.readFileSync(httpClientPath, 'utf8');
const importStatement = `import { from } from 'rxjs';`;

if (!httpClientContent.includes(importStatement)) {
    httpClientContent = importStatement + '\n' + httpClientContent;
    fs.writeFileSync(httpClientPath, httpClientContent);
    console.log(`Updated HttpClient.ts`);
};

// Find Observable.fromPromise in HttpClient.ts in current directory, and replace with from
httpClientContent = httpClientContent.replace(/Observable\.fromPromise/g, 'from');
fs.writeFileSync(httpClientPath, httpClientContent);
console.log(`Updated HttpClient.ts`);
