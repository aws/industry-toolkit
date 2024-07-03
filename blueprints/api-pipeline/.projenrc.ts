import { ProjenBlueprint } from '@amazon-codecatalyst/blueprint-util.projen-blueprint';

const project = new ProjenBlueprint({
  authorName: 'AWS',
  publishingOrganization: 'aws-industry-framework',
  packageName: '@amazon-codecatalyst/aws-industry-framework.api-pipeline',
  name: 'api-pipeline',
  displayName: 'API Pipeline',
  defaultReleaseBranch: 'main',
  license: 'Apache-2.0',
  projenrcTs: true,
  sampleCode: false,
  github: false,
  eslint: true,
  jest: false,
  npmignoreEnabled: true,
  tsconfig: {
    compilerOptions: {
      esModuleInterop: true,
      noImplicitAny: false,
    },
  },
  copyrightOwner: 'aws-industry-framework',
  deps: [
    'projen',
    '@amazon-codecatalyst/blueprints.blueprint',
    '@amazon-codecatalyst/blueprint-component.workflows',
    '@amazon-codecatalyst/blueprint-component.source-repositories',
    '@amazon-codecatalyst/blueprint-component.dev-environments',
    '@amazon-codecatalyst/blueprint-component.environments',
    '@amazon-codecatalyst/blueprint-component.issues',
  ],
  description: 'This blueprint creates an API pipeline that builds Smithy IDL model definitions into client and server SDKs, documentation, and other artifacts.',
  devDeps: [
    'ts-node@^10',
    'typescript',
    '@amazon-codecatalyst/blueprint-util.projen-blueprint',
    '@amazon-codecatalyst/blueprint-util.cli',
    'fast-xml-parser',
  ],
  keywords: [
    'api',
    'smithy',
    'gradle',
    'typescript',
  ],
  homepage: '',
});

project.synth();