import { ServerStatusSchema, LogFilterOptions } from "@/types/schema";
import axios from "axios";
import ApiUrl from "./url";


export function getServerStatusApi() {
  return axios.get<ServerStatusSchema>(ApiUrl.ServerStatus);
}

export function getProxyLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ProxyLogs, options);
}

export function getServerLogsApi(options: LogFilterOptions | null) {
  return axios.post(ApiUrl.ServerLogs, options);
}