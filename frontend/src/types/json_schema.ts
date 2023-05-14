import modelDefinitions from './json/model_definitions.json';
import jsonSchemas from './json/schemas.json';
import { ApiChatModels, RevChatModels } from './schema';

export const jsonRevSourceSettingSchema = jsonSchemas.RevSourceSettingSchema;
export const jsonApiSourceSettingSchema = jsonSchemas.ApiSourceSettingSchema;

export const jsonConfigModelSchema = jsonSchemas.ConfigModel;
export const jsonCredentialsModelSchema = jsonSchemas.CredentialsModel;

export const revChatModelNames = modelDefinitions.rev as RevChatModels[];
export const apiChatModelNames = modelDefinitions.api as ApiChatModels[];
export const allChatModelNames = [...revChatModelNames, ...apiChatModelNames] as string[];