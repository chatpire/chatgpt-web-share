import { components } from './openapi';

export type UserRead = components['schemas']['UserRead'];
export type UserReadAdmin = components['schemas']['UserReadAdmin'];
export type UserCreate = components['schemas']['UserCreate'];
export type UserUpdate = components['schemas']['UserUpdate'];
export type UserUpdateAdmin = components['schemas']['UserUpdateAdmin'];

export type UserSettingSchema = components['schemas']['UserSettingSchema'];
export type RevSourceSettingSchema = components['schemas']['RevSourceSettingSchema'];
export type ApiSourceSettingSchema = components['schemas']['ApiSourceSettingSchema'];

export type ServerStatusSchema = components['schemas']['ServerStatusSchema'];
export type RevChatStatus = components['schemas']['RevChatStatus'];

export type RevChatModels = components['schemas']['RevChatModels'];
export type ApiChatModels = components['schemas']['ApiChatModels'];

export type RevChatMessageMetadata = components['schemas']['RevChatMessageMetadata'];
export type ApiChatMessageMetadata = components['schemas']['ApiChatMessageMetadata'];
export type RevChatMessageTextContent = components['schemas']['RevChatMessageTextContent'];
export type RevChatMessageCodeContent = components['schemas']['RevChatMessageCodeContent'];
export type RevChatMessageTetherBrowsingDisplayContent = components['schemas']['RevChatMessageTetherBrowsingDisplayContent'];
export type RevChatMessageTetherQuoteContent = components['schemas']['RevChatMessageTetherQuoteContent'];
export type ApiChatMessageTextContent  = components['schemas']['ApiChatMessageTextContent'];
export type BaseChatMessage = components['schemas']['BaseChatMessage'];
export type ApiChatMessage = components['schemas']['ApiChatMessage'];
export type RevChatMessage = components['schemas']['RevChatMessage'];

export type BaseConversationSchema = components['schemas']['BaseConversationSchema'];
export type RevConversationSchema = components['schemas']['RevConversationSchema'];
export type ApiConversationSchema = components['schemas']['ApiConversationSchema'];

export type BaseConversationHistory = components['schemas']['BaseConversationHistory'];
export type ApiConversationHistoryDocument = components['schemas']['ApiConversationHistoryDocument'];
export type RevConversationHistoryDocument = components['schemas']['RevConversationHistoryDocument'];

export type OpenAIChatPluginCategory = components['schemas']['OpenAIChatPluginCategory'];
export type OpenAIChatPluginManifest = components['schemas']['OpenAIChatPluginManifest'];
export type OpenAIChatPluginUserSettings = components['schemas']['OpenAIChatPluginUserSettings'];
export type OpenAIChatPlugin = components['schemas']['OpenAIChatPlugin'];

export type AskRequest = components['schemas']['AskRequest'];
export type AskResponse = components['schemas']['AskResponse'];

export type SystemInfo = components['schemas']['SystemInfo'];
export type RequestLogAggregation = components['schemas']['RequestLogAggregation'];
export type AskLogAggregation = components['schemas']['AskLogAggregation'];

export type LogFilterOptions = components['schemas']['LogFilterOptions'];

export type ConfigModel = components['schemas']['ConfigModel'];
export type CredentialsModel = components['schemas']['CredentialsModel'];

export const chatStatusMap = {
  asking: 'commons.askingChatStatus',
  queueing: 'commons.queueingChatStatus',
  idling: 'commons.idlingChatStatus',
};
