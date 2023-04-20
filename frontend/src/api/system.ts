import axios from 'axios';

import { LogFilterOptions } from '@/types/schema';

import ApiUrl from './url';

export function getSystemInfoApi() {
  return axios.get(ApiUrl.SystemInfo);
}

export function getRequestStatisticsApi() {
  return axios.get(ApiUrl.SystemRequestStatistics);
}

export function getServerLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ServerLogs, options);
}

export function getProxyLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ProxyLogs, options);
}
