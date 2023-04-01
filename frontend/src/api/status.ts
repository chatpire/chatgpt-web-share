import { ServerStatusSchema } from "@/types/schema";
import axios from "axios";
import ApiUrl from "./url";



export function getServerStatusApi() {
  return axios.get<ServerStatusSchema>(ApiUrl.ServerStatus);
}
