import { i18n } from '@/i18n';
import { RevChatModels } from '@/types/schema';

const t = i18n.global.t as any;

export const revChatModelNames: RevChatModels[] = ['text-davinci-002-render-sha', 'text-davinci-002-render-paid', 'gpt-4'];

export const revChatModelNameMap: Record<RevChatModels, string> = {
  'text-davinci-002-render-sha': t('commons.shaModel'),
  'text-davinci-002-render-paid': t('commons.paidModel'),
  'gpt-4': t('commons.gpt4Model'),
};

export const getRevChatModelNameTrans = (model_name: RevChatModels | string) => {
  if (revChatModelNameMap[model_name as keyof typeof revChatModelNameMap]) return revChatModelNameMap[model_name as keyof typeof revChatModelNameMap];
  else return model_name;
};

export const getCountTrans = (count: number | undefined | null): string => {
  if (count == undefined || count == null) return t('commons.unlimited');
  return count == -1 ? t('commons.unlimited') : `${count}`;
};
