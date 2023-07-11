enum ApiUrl {
  Register = '/auth/register',
  AdminRegister = '/auth/adminregister',
  Login = '/auth/login',
  Logout = '/auth/logout',
  UserMe = '/user/me',
  GetInviteCode = '/user/createcode',

  Conversation = '/conv',
  AllConversation = '/conv/all',
  UserList = '/user',

  ChatPlugin = '/chat/openai-plugin',
  AllChatPlugins = '/chat/openai-plugins/all',
  InstalledChatPlugins = '/chat/openai-plugins/installed',

  ServerStatus = '/status',

  SystemInfo = '/system/info',
  SystemRequestStatistics = '/system/stats/request',
  SystemAskStatistics = '/system/stats/ask',
  ServerLogs = '/system/logs/server',

  SystemConfig = '/system/config',
  SystemCredentials = '/system/credentials',
}

export default ApiUrl;
