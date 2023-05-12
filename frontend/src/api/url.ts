enum ApiUrl {
  Register = '/auth/register',
  Login = '/auth/login',
  Logout = '/auth/logout',
  UserMe = '/user/me',

  Conversation = '/conv',
  AllConversation = '/conv/all',
  UserList = '/user',

  ServerStatus = '/status',
  SystemInfo = '/system/info',
  SystemRequestStatistics = '/system/request_statistics',
  ProxyLogs = '/system/proxy_logs',
  ServerLogs = '/system/server_logs',

  SystemConfig = '/system/config',
}

export default ApiUrl;
