import axios from 'axios';

import {
  AskLogDocument,
  LogFilterOptions,
} from '@/types/schema';

import ApiUrl from './url';

export function getServerLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ServerLogs, options);
}

export function getCompletionLogsApi(start_time?: string, end_time?: string, max_results = 100) {
  return axios.get<AskLogDocument[]>(ApiUrl.CompletionLogs, { params: { start_time, end_time, max_results } });
}
