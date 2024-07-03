import { BedrockAgentRuntimeClient, InvokeAgentCommand } from '@aws-sdk/client-bedrock-agent-runtime';
import { v4 as uuidv4 } from 'uuid';
import { readFile } from 'fs/promises';
import { fileURLToPath } from "url";

const args = process.argv.slice(2);

if (args.length < 4) {
  console.error('Usage: node script.js <apiName> <apiDescription> <crudOperations> <additionalOperations> <additionalContext>');
  process.exit(1);
}

const apiName = args[0];
const apiDescription = args[1];
const crudOperations = args[2] === 'true';
const additionalOperations = args[3];
const additionalContext = args[4];

const smithyExample = await readFile('./format.smithy');

export const invokeBedrockAgent = async (prompt, sessionId) => {
  console.log("Invoking Bedrock Agent", {
    "prompt": prompt,
    "sessionId": sessionId
  });
  const client = new BedrockAgentRuntimeClient({region:"us-east-1"});

  const agentId = "VFLRLFTQYF";
  const agentAliasId = "JZF82RCGEU";

  const command = new InvokeAgentCommand({
    agentId,
    sessionId,
    agentAliasId,
    inputText: prompt
  });
  try {
    let completion = "";
    const response = await client.send(command);

    if (response.completion === undefined) {
      throw new Error("Completion is undefined");
    }

    for await (let chunkEvent of response.completion) {
      const chunk = chunkEvent.chunk;
      console.log(chunk);
      const decodedResponse = new TextDecoder("utf-8").decode(chunk.bytes);
      completion += decodedResponse;
    }

    return { sessionId, completion };
  } catch (err) {
    console.error(err);
  }
}

// Call function if run directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const newSessionId = uuidv4();
  const prompt = `Generate API model for: ${apiName}\nDescription: ${apiDescription}\nCRUD operations: ${crudOperations}\nAdditional operations: ${additionalOperations}\nAdditional context: ${additionalContext}`;
  const result = await invokeBedrockAgent(prompt, newSessionId);
  console.log({
    "result": result.completion
  });

  // Print the generated document
  console.log("Generated API model:");
  console.log(result.completion);
}

