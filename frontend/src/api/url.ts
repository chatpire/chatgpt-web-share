enum ApiUrl {
  Register = '/auth/register',
  Login = '/auth/login',
  Logout = '/auth/logout',
  UserMe = '/user/me',

  Conversation = '/conv',
  AllConversation = '/conv/all',
  UserList = '/user',

  ChatPlugin = '/chat/openai-plugin',
  AllChatPlugins = '/chat/openai-plugins/all',
  InstalledChatPlugins = '/chat/openai-plugins/installed',

  ServerStatus = '/status/common',

  SystemInfo = '/system/info',
  SystemRequestStatistics = '/system/stats/request',
  SystemAskStatistics = '/system/stats/ask',
  ServerLogs = '/system/logs/server',

  SystemConfig = '/system/config',
  SystemCredentials = '/system/credentials',
}

export default ApiUrl;
