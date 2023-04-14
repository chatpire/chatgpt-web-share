enum ApiUrl {
  Register = "/auth/register",
  Login = "/auth/login",
  Logout = "/auth/logout",
  UserInfo = "/user/me",

  Conversation = "/conv",
  UserList = "/user",
  ApiList = "/system/api",
  UserApi = "/system/user/api/",
  MyModels = "/api/user/models/",

  ServerStatus = "/status",
  SystemInfo = "/system/info",
  SystemRequestStatistics = "/system/request_statistics",
  ProxyLogs = "/system/proxy_logs",
  ServerLogs = "/system/server_logs"
}

export default ApiUrl;
