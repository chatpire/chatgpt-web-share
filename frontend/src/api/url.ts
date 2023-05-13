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
  SystemRequestStatistics = '/system/stats/request',
  ServerLogs = '/system/logs/server',

  SystemConfig = '/system/config',
  SystemCredentials = '/system/credentials',
}

export default ApiUrl;
