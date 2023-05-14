// eslint-disable-next-line import/no-unresolved
import chatgptIcon from '/chatgpt-icon.svg';
// eslint-disable-next-line import/no-unresolved
import chatgptIconBlack from '/chatgpt-icon-black.svg';
import { i18n } from '@/i18n';
import { allChatModelNames } from '@/types/json_schema';
import { ApiChatModels, RevChatModels } from '@/types/schema';

const t = i18n.global.t as any;

export const chatModelColorMap: Record<string, string> = {
  gpt_3_5: 'green',
  gpt_4: 'purple',
  gpt_4_browsing: 'blue'
};

export const getChatModelColor = (model_name: RevChatModels | ApiChatModels | string | null) => {
  if (model_name == null) return 'black';
  if (chatModelColorMap[model_name]) return chatModelColorMap[model_name];
  else return 'black';
};

export const getChatModelNameTrans = (model_name: RevChatModels | ApiChatModels | string | null) => {
  if (model_name == null) return t('commons.unknown');
  if (allChatModelNames.includes(model_name))
    return t(`models.${model_name}`);
  else return model_name;
};

export const getCountTrans = (count: number | undefined | null): string => {
  if (count == undefined || count == null) return t('commons.unlimited');
  return count == -1 ? t('commons.unlimited') : `${count}`;
};
