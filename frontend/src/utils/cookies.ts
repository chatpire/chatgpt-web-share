// 参考：https://github.com/cmp-cc/vue-cookies/blob/master/vue-cookies.js

const defaultConfig = {
  expires: '1d',
  path: '; path=/',
  domain: '',
  secure: '',
  sameSite: '; SameSite=Lax',
};

export function hasCookie(key: string): boolean {
  return new RegExp(`(?:^|;\\s*)${encodeURIComponent(key).replace(/[-.+*]/g, '\\$&')}\\s*\\=`).test(document.cookie);
}

export function removeCookie(key: string, path: string | null = null, domain: string | null = null): boolean {
  if (!key || !hasCookie(key)) {
    return false;
  }
  document.cookie = `${encodeURIComponent(key)}=; expires=Thu, 01 Jan 1970 00:00:00 GMT${
    domain ? `; domain=${domain}` : defaultConfig.domain
  }${path ? `; path=${path}` : defaultConfig.path}; SameSite=Lax`;
  return true;
}
