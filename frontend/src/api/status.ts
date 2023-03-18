import { ServerStatusSchema } from "@/types/schema";
import axios from "axios";
import ApiUrl from "./url";

export function getServerStatusApi() {
  return axios.get<ServerStatusSchema>(ApiUrl.ServerStatus);
}

export function getProxyLogsApi(max_lines = 100) {
  return axios.get(ApiUrl.ProxyLogs, {
    params: { max_lines },
  });
}

export function getServerLogsApi(max_lines = 100) {
  return axios.get(ApiUrl.ServerLogs, {
    params: { max_lines },
  });
}