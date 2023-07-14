import axios from 'axios';

import { OpenaiChatPlugin, OpenaiChatPluginUserSettings } from '@/types/schema';

import ApiUrl from './url';

export type AskInfo = {
  message: string;
  new_title?: string;
  conversation_id?: string;
  parent_id?: string;
  model_name?: string;
  timeout?: number;
};

export function getAskWebsocketApiUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${protocol}://${window.location.host}${import.meta.env.VITE_API_BASE_URL}chat`;
  console.log('getAskWebsocketApiUrl', url);
  return url;
}

export function getAllOpenaiChatPluginsApi() {
  return axios.get<OpenaiChatPlugin[]>(ApiUrl.AllChatPlugins);
}

export function getInstalledOpenaiChatPluginsApi() {
  return axios.get<OpenaiChatPlugin[]>(ApiUrl.InstalledChatPlugins);
}

export function patchOpenaiChatPluginsUsersSettingsApi(pluginId: string, setting: OpenaiChatPluginUserSettings) {
  return axios.patch(`${ApiUrl.ChatPlugin}/${pluginId}/user-settings`, setting, {
    params: {
      plugin_id: pluginId,
    },
  });
}

export function getOpenaiChatPluginApi(pluginId: string) {
  return axios.get<OpenaiChatPlugin>(`${ApiUrl.ChatPlugin}/${pluginId}`);
}
