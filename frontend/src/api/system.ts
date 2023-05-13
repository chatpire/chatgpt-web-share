import axios from 'axios';

import { ConfigModel, CredentialsModel, LogFilterOptions, RequestStatistics, SystemInfo } from '@/types/schema';

import ApiUrl from './url';

export function getSystemInfoApi() {
  return axios.get<SystemInfo>(ApiUrl.SystemInfo);
}

export function getRequestStatisticsApi() {
  return axios.get<RequestStatistics>(ApiUrl.SystemRequestStatistics);
}

export function getServerLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ServerLogs, options);
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
