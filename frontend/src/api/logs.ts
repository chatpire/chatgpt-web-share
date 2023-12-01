import axios from 'axios';

import {
  AskLogAggregation,
  AskLogDocument,
  ConfigModel,
  CredentialsModel,
  LogFilterOptions,
  RequestLogAggregation,
  SystemInfo,
} from '@/types/schema';

import ApiUrl from './url';

export function getServerLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ServerLogs, options);
}

export function getCompletionLogsApi(start_time?: string, end_time?: string, limit = 100) {
  return axios.get<AskLogDocument[]>(ApiUrl.CompletionLogs, { params: { start_time, end_time, limit } });
}
