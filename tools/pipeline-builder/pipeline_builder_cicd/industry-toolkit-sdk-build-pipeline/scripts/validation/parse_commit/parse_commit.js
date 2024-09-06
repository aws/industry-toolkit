import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

function parseAngularCommitMessage(commitMessage) {
    const commitRegex = /^(?<type>build|ci|chore|docs|feat|fix|perf|refactor|revert|style|test)(\((?<scope>[a-z\-]+)\))?: (?<subject>[a-z].{1,100})(\n\n(?<body>.+?))?(\n\nBREAKING CHANGE: (?<footer>.+))?$/s;
  
    const match = commitRegex.exec(commitMessage);
  
    if (!match) {
      throw new Error("Invalid commit message format");
    }
  
    const { type, scope, subject, body, footer } = match.groups;
  
    return {
      type,
      scope: scope || null,
      subject,
      body: body || null,
      footer: footer || null
    };
}
  
try {
  // Read the commit message from environment variable
  const commitMessage = process.env.COMMIT_MSG;

  const parsedCommit = parseAngularCommitMessage(commitMessage.trim());
  console.log('Parsed Commit: '+JSON.stringify(parsedCommit));
  
  // Set environment variables
  process.env.COMMIT_TYPE = parsedCommit.type;
  process.env.COMMIT_SCOPE = parsedCommit.scope;
  process.env.COMMIT_SUBJECT = parsedCommit.subject;
  process.env.COMMIT_BODY = parsedCommit.body;
  process.env.COMMIT_FOOTER = parsedCommit.footer;

} catch (error) {
    console.error(error.message);
}

// Console log environment variables
const envVars = {
    COMMIT_TYPE: process.env.COMMIT_TYPE,
    COMMIT_SCOPE: process.env.COMMIT_SCOPE,
    COMMIT_SUBJECT: process.env.COMMIT_SUBJECT,
    COMMIT_BODY: process.env.COMMIT_BODY,
    COMMIT_FOOTER: process.env.COMMIT_FOOTER
};

// Convert the object to a JSON string
const jsonContent = JSON.stringify(envVars, null, 2);

// Define the file path
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const filePath = join(__dirname, 'env-vars.json');

// Write the JSON string to a file
fs.writeFile(filePath, jsonContent, 'utf8', (err) => {
  if (err) {
    console.error('An error occurred while writing JSON to file:', err);
  } else {
    console.log(`Environment variables written to ${filePath}`);
  }
});