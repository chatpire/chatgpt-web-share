import axios from 'axios';

import { CommonStatusSchema } from '@/types/schema';

import ApiUrl from './url';

export function getServerStatusApi() {
  return axios.get<CommonStatusSchema>(ApiUrl.ServerStatus);
}
