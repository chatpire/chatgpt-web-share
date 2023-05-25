enum ApiUrl {
  Register = '/auth/register',
  Login = '/auth/login',
  Logout = '/auth/logout',
  UserMe = '/user/me',

  Conversation = '/conv',
  AllConversation = '/conv/all',
  UserList = '/user',

  ChatPlugins = '/chat/openai-plugins',

  ServerStatus = '/status',

  SystemInfo = '/system/info',
  SystemRequestStatistics = '/system/stats/request',
  SystemAskStatistics = '/system/stats/ask',
  ServerLogs = '/system/logs/server',

  SystemConfig = '/system/config',
  SystemCredentials = '/system/credentials',
}

export default ApiUrl;
