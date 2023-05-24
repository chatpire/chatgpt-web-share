import axios from 'axios';

import { OpenAIChatPlugin } from '@/types/schema';

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

export function getOpenaiChatPluginsApi() {
  return axios.get<OpenAIChatPlugin[]>(ApiUrl.ChatPlugins);
}