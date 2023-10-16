import axios from 'axios';

import { BaseConversationHistory, BaseConversationSchema, OpenaiChatInterpreterInfo } from '@/types/schema';

import ApiUrl from './url';

export function getAllConversationsApi() {
  return axios.get<Array<BaseConversationSchema>>(ApiUrl.Conversation);
}

export function getAdminAllConversationsApi(valid_only = false) {
  return axios.get<Array<BaseConversationSchema>>(ApiUrl.AllConversation, {
    params: { valid_only },
  });
}

export function getConversationHistoryApi(conversation_id: string) {
  return axios.get<BaseConversationHistory>(ApiUrl.Conversation + '/' + conversation_id);
}

export function getConversationHistoryFromCacheApi(conversation_id: string) {
  return axios.get<BaseConversationHistory>(`${ApiUrl.Conversation}/${conversation_id}/cache`);
}

export function deleteConversationApi(conversation_id: string) {
  return axios.delete(ApiUrl.Conversation + '/' + conversation_id);
}

export function clearAllConversationApi() {
  return axios.delete(ApiUrl.Conversation);
}

export function vanishConversationApi(conversation_id: string) {
  return axios.delete(ApiUrl.Conversation + '/' + conversation_id + '/vanish');
}

export function setConversationTitleApi(conversation_id: string, title: string) {
  return axios.patch<BaseConversationSchema>(ApiUrl.Conversation + '/' + conversation_id, null, {
    params: { title },
  });
}

export function generateConversationTitleApi(conversation_id: string, message_id: string) {
  return axios.patch<string>(ApiUrl.Conversation + '/' + conversation_id + '/gen_title', null, {
    params: { message_id },
  });
}

export function assignConversationToUserApi(conversation_id: string, username: string) {
  return axios.patch(`${ApiUrl.Conversation}/${conversation_id}/assign/${username}`);
}

export function getFileDownloadUrlApi(file_id: string) {
  return axios.get<string>(`/files/${file_id}/download-url`);
}

export function getInterpreterInfoApi(conversation_id: string) {
  return axios.get<OpenaiChatInterpreterInfo>(`${ApiUrl.Conversation}/${conversation_id}/interpreter`);
}

export function getInterpreterSandboxFileDownloadUrlApi(
  conversation_id: string,
  message_id: string,
  sandbox_path: string
) {
  return axios.get<string>(`${ApiUrl.Conversation}/${conversation_id}/interpreter/download-url`, {
    params: { message_id, sandbox_path },
  });
}
