import { dereference } from '@apidevtools/json-schema-ref-parser';
import fs from 'fs';
import path from 'path';

const currentModulePath = new URL(import.meta.url).pathname;
const currentDirectory = path.dirname(currentModulePath);

const sourceFilePath = path.join(currentDirectory, '../src/types/json/openapi.json');
const targetFilePath = path.join(currentDirectory, '../src/types/json/schemas.json');

dereference(sourceFilePath)
  .then((dereferencedSchema) => {
    const dereferencedSchemaString = JSON.stringify(dereferencedSchema.components.schemas, null, 2);

    fs.writeFileSync(targetFilePath, dereferencedSchemaString, 'utf8');

    console.log('dereference success!');
  })
  .catch((error) => {
    console.error('error:', error);
  });
