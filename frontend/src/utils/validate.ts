import { FormItemRule } from 'naive-ui';

import { i18n } from '@/i18n';

const t = i18n.global.t as any;

export function getEmailRule(required: boolean) {
  return {
    required,
    trigger: 'input',
    validator: (rule: any, email: string) => {
      // 用正则检查邮箱地址
      const reg = /^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$/;
      if (!reg.test(email)) {
        return new Error(t('tips.invalidEmail'));
      }
      return true;
    },
  } as FormItemRule;
}

export function getPasswordRule(required: boolean) {
  return {
    required,
    trigger: 'input',
    validator: (rule: any, password: string) => {
      if (!required && !password) {
        return true;
      }
      const reg = /^[\w!@#$%^&*()_+|{}:;<>?~`-]{6,}$/;
      if (!reg.test(password)) {
        return new Error(t('tips.invalidPassword'));
      }
      return true;
    },
  } as FormItemRule;
}
