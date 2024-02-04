import modelDefinitions from './json/model_definitions.json';
import jsonSchemas from './json/schemas.json';
import { OpenaiApiChatModels, OpenaiWebChatModels } from './schema';

export const jsonRevSourceSettingSchema = jsonSchemas.OpenaiWebSourceSettingSchema;
export const jsonApiSourceSettingSchema = jsonSchemas.OpenaiApiSourceSettingSchema;

export const jsonConfigModelSchema = jsonSchemas['ConfigModel-Output'];
export const jsonCredentialsModelSchema = jsonSchemas.CredentialsModel;

export const openaiWebChatModelNames = modelDefinitions.openai_web as OpenaiWebChatModels[];
export const openaiApiChatModelNames = modelDefinitions.openai_api as OpenaiApiChatModels[];
export const allChatModelNames = [...openaiWebChatModelNames, ...openaiApiChatModelNames] as string[];
