import { components } from './openapi';

export type ChatSourceTypes = components['schemas']['ChatSourceTypes'];

export type UserRead = components['schemas']['UserRead'];
export type UserReadAdmin = components['schemas']['UserReadAdmin'];
export type UserCreate = components['schemas']['UserCreate'];
export type UserUpdate = components['schemas']['UserUpdate'];
export type UserUpdateAdmin = components['schemas']['UserUpdateAdmin'];

export type UserSettingSchema = components['schemas']['UserSettingSchema-Input'];
export type OpenaiWebSourceSettingSchema = components['schemas']['OpenaiWebSourceSettingSchema'];
export type OpenaiApiSourceSettingSchema = components['schemas']['OpenaiApiSourceSettingSchema'];
export type TimeWindowRateLimit = components['schemas']['TimeWindowRateLimit'];
export type DailyTimeSlot = components['schemas']['DailyTimeSlot'];

export type CommonStatusSchema = components['schemas']['CommonStatusSchema'];
export type OpenaiWebChatStatus = components['schemas']['OpenaiWebChatStatus'];

export type OpenaiWebChatModels = components['schemas']['OpenaiWebChatModels'];
export type OpenaiApiChatModels = components['schemas']['OpenaiApiChatModels'];

export type OpenaiWebChatMessageMetadata = components['schemas']['OpenaiWebChatMessageMetadata'];
export type OpenaiApiChatMessageMetadata = components['schemas']['OpenaiApiChatMessageMetadata'];
export type OpenaiWebChatMessageMetadataAttachment = components['schemas']['OpenaiWebChatMessageMetadataAttachment'];
export type OpenaiWebChatMessageTextContent = components['schemas']['OpenaiWebChatMessageTextContent'];
export type OpenaiWebChatMessageMultimodalTextContent =
  components['schemas']['OpenaiWebChatMessageMultimodalTextContent'];
export type OpenaiWebChatMessageCodeContent = components['schemas']['OpenaiWebChatMessageCodeContent'];
export type OpenaiWebChatMessageExecutionOutputContent =
  components['schemas']['OpenaiWebChatMessageExecutionOutputContent'];
export type OpenaiWebChatMessageStderrContent = components['schemas']['OpenaiWebChatMessageStderrContent'];
export type OpenaiWebChatMessageTetherBrowsingDisplayContent =
  components['schemas']['OpenaiWebChatMessageTetherBrowsingDisplayContent'];
export type OpenaiWebChatMessageMetadataCiteData = components['schemas']['OpenaiWebChatMessageMetadataCiteData'];
export type OpenaiWebChatMessageTetherQuoteContent = components['schemas']['OpenaiWebChatMessageTetherQuoteContent'];
export type OpenaiWebChatMessageSystemErrorContent = components['schemas']['OpenaiWebChatMessageSystemErrorContent'];
export type OpenaiApiChatMessageTextContent = components['schemas']['OpenaiApiChatMessageTextContent'];
export type OpenaiWebChatMessageMultimodalTextContentImagePart =
  components['schemas']['OpenaiWebChatMessageMultimodalTextContentImagePart-Input'];

export type BaseChatMessage = components['schemas']['BaseChatMessage'];
export type OpenaiApiChatMessage = components['schemas']['OpenaiApiChatMessage'];
export type OpenaiWebChatMessage = components['schemas']['OpenaiWebChatMessage'];
export type OpenaiChatInterpreterInfo = components['schemas']['OpenaiChatInterpreterInfo'];

export type BaseConversationSchema = components['schemas']['BaseConversationSchema'];
export type OpenaiWebConversationSchema = components['schemas']['OpenaiWebConversationSchema'];
export type OpenaiApiConversationSchema = components['schemas']['OpenaiApiConversationSchema'];

export type BaseConversationHistory = components['schemas']['BaseConversationHistory'];
export type OpenaiApiConversationHistoryDocument = components['schemas']['OpenaiApiConversationHistoryDocument'];
export type OpenaiWebConversationHistoryDocument = components['schemas']['OpenaiWebConversationHistoryDocument'];
export type OpenaiWebAccountsCheckResponse = components['schemas']['OpenaiWebAccountsCheckResponse'];

export type OpenaiChatPluginCategory = components['schemas']['OpenaiChatPluginCategory'];
export type OpenaiChatPluginManifest = components['schemas']['OpenaiChatPluginManifest'];
export type OpenaiChatPluginUserSettings = components['schemas']['OpenaiChatPluginUserSettings'];
export type OpenaiChatPlugin = components['schemas']['OpenaiChatPlugin'];
export type OpenaiChatPluginListResponse = components['schemas']['OpenaiChatPluginListResponse'];

export type OpenaiChatFileUploadUrlRequest = components['schemas']['OpenaiChatFileUploadUrlRequest'];

export type AskRequest = components['schemas']['AskRequest'];
export type AskResponse = components['schemas']['AskResponse'];

export type SystemInfo = components['schemas']['SystemInfo'];
export type RequestLogAggregation = components['schemas']['RequestLogAggregation'];
export type AskLogAggregation = components['schemas']['AskLogAggregation'];
export type AskLogDocument = components['schemas']['AskLogDocument'];

export type LogFilterOptions = components['schemas']['LogFilterOptions'];

export type ConfigModel = components['schemas']['ConfigModel-Output'];
export type CredentialsModel = components['schemas']['CredentialsModel'];

export type UploadedFileInfoSchema = components['schemas']['UploadedFileInfoSchema'];
export type StartUploadRequestSchema = components['schemas']['StartUploadRequestSchema'];
export type StartUploadResponseSchema = components['schemas']['StartUploadResponseSchema'];

export const chatStatusMap = {
  asking: 'commons.askingChatStatus',
  queueing: 'commons.queueingChatStatus',
  idling: 'commons.idlingChatStatus',
};
