import axios from 'axios';

import {
  AskLogAggregation,
  ConfigModel,
  CredentialsModel,
  LogFilterOptions,
  OpenaiWebAccountsCheckResponse,
  RequestLogAggregation,
  SystemInfo,
} from '@/types/schema';

import ApiUrl from './url';

export function getSystemInfoApi() {
  return axios.get<SystemInfo>(ApiUrl.SystemInfo);
}

export function getRequestStatisticsApi(granularity: number) {
  return axios.get<RequestLogAggregation[]>(ApiUrl.SystemRequestStatistics, {
    params: { granularity },
  });
}

export function getAskStatisticsApi(granularity: number) {
  return axios.get<AskLogAggregation[]>(ApiUrl.SystemAskStatistics, {
    params: { granularity },
  });
}

export function getSystemConfig() {
  return axios.get<ConfigModel>(ApiUrl.SystemConfig);
}

export function updateSystemConfig(config: ConfigModel) {
  return axios.put<ConfigModel>(ApiUrl.SystemConfig, config);
}

export function getSystemCredentials() {
  return axios.get<CredentialsModel>(ApiUrl.SystemCredentials);
}

export function updateSystemCredentials(credentials: CredentialsModel) {
  return axios.put<CredentialsModel>(ApiUrl.SystemCredentials, credentials);
}

export function runActionSyncOpenaiWebConversations() {
  return axios.post(ApiUrl.SystemActionSyncOpenaiWebConversations);
}

export function SystemCheckOpenaiWebAccount() {
  return axios.get<OpenaiWebAccountsCheckResponse>(ApiUrl.SystemCheckOpenaiWebAccount);
}