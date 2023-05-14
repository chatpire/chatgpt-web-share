// eslint-disable-next-line import/no-unresolved
import chatgptIcon from '/chatgpt-icon.svg';
// eslint-disable-next-line import/no-unresolved
import chatgptIconBlack from '/chatgpt-icon-black.svg';
import { i18n } from '@/i18n';
import { allChatModelNames } from '@/types/json_schema';
import { ApiChatModels, RevChatModels } from '@/types/schema';

const t = i18n.global.t as any;

export const chatModelIconMap: Record<string, any> = {
  gpt_3_5: chatgptIcon,
  gpt_4: chatgptIconBlack,
};

export const getChatModelIconSVG = (model_name: RevChatModels | ApiChatModels | string | null) => {
  if (model_name == null) return chatgptIcon;
  if (chatModelIconMap[model_name as keyof typeof chatModelIconMap])
    return chatModelIconMap[model_name as keyof typeof chatModelIconMap];
  else return chatgptIcon;
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
