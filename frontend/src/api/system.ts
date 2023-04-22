import axios from 'axios';

import { ConfigRead, ConfigUpdate, LogFilterOptions, RequestStatistics, SystemInfo } from '@/types/schema';

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

export function getProxyLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ProxyLogs, options);
}

export function getSystemConfig() {
  return axios.get<ConfigRead>(ApiUrl.SystemConfig);
}

export function updateSystemConfig(config: Partial<ConfigUpdate>) {
  return axios.patch<ConfigRead>(ApiUrl.SystemConfig, config);
}
