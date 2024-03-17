enum ApiUrl {
  Register = '/auth/register',
  Login = '/auth/login',
  Logout = '/auth/logout',
  UserMe = '/user/me',

  Conversation = '/conv',
  AllConversation = '/conv/all',
  UserList = '/user',

  ChatPlugin = '/chat/openai-plugin',
  ChatPlugins = '/chat/openai-plugins',
  InstalledChatPlugins = '/chat/openai-plugins/installed',

  ServerStatus = '/status/common',

  SystemInfo = '/system/info',
  SystemRequestStatistics = '/system/stats/request',
  SystemAskStatistics = '/system/stats/ask',
  SystemActionSyncOpenaiWebConversations = '/system/action/sync-openai-web-conv',
  SystemCheckOpenaiWebAccount = '/system/check-openai-web-account',

  ServerLogs = '/logs/server',
  CompletionLogs = '/logs/completions',

  SystemConfig = '/system/config',
  SystemCredentials = '/system/credentials',


  FilesLocalUpload = '/files/local/upload',
  FilesLocalDownload = '/files/local/download',
  FilesOpenaiWebUploadStart = '/files/openai-web/upload-start',
  FilesOpenaiWebUploadComplete = '/files/openai-web/upload-complete',
  FilesLocalUploadToOpenaiWeb = '/files/local/upload-to-openai-web',

  ArkoseInfo = '/arkose/info',
}

export default ApiUrl;
