enum ApiUrl {
  Register = "/auth/register",
  Login = "/auth/login",
  Logout = "/auth/logout",
  UserInfo = "/user/me",

  Conversation = "/conv",
  UserList = "/user",

  ServerStatus = "/status",
  ProxyLogs = "/logs/proxy",
  ServerLogs = "/logs/server"
}

export default ApiUrl;
