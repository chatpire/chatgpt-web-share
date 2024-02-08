import axios from 'axios';

import ApiUrl from './url';

export function getArkoseInfo() {
  return axios.get<{ enabled: boolean, url: string }>(ApiUrl.ArkoseInfo);
}
