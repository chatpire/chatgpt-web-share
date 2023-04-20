import axios from 'axios';

import { ServerStatusSchema } from '@/types/schema';

import ApiUrl from './url';

export function getServerStatusApi() {
  return axios.get<ServerStatusSchema>(ApiUrl.ServerStatus);
}
