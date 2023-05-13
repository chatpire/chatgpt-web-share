// eslint-disable-next-line import/no-unresolved
import chatgptIcon from '/chatgpt-icon.svg';
// eslint-disable-next-line import/no-unresolved
import chatgptIconBlack from '/chatgpt-icon-black.svg';
import { i18n } from '@/i18n';
import { ChatModel } from '@/types/schema';

const t = i18n.global.t as any;

export const chatModelNames = ['gpt_3_5', 'gpt_4'] as ChatModel[];

export const chatModelNameMap: Record<ChatModel, string> = {
  gpt_3_5: 'GPT 3.5',
  gpt_4: 'GPT 4',
};

export const chatModelIconMap: Record<ChatModel, any> = {
  gpt_3_5: chatgptIcon,
  gpt_4: chatgptIconBlack,
};

export const getChatModelIconSVG = (model_name: ChatModel | string | null) => {
  if (model_name == null) return chatgptIcon;
  if (chatModelIconMap[model_name as keyof typeof chatModelIconMap])
    return chatModelIconMap[model_name as keyof typeof chatModelIconMap];
  else return chatgptIcon;
};



export const getChatModelNameTrans = (model_name: ChatModel | string | null) => {
  if (model_name == null) return t('commons.unknown');
  if (chatModelNameMap[model_name as keyof typeof chatModelNameMap])
    return chatModelNameMap[model_name as keyof typeof chatModelNameMap];
  else return model_name;
};

export const getCountTrans = (count: number | undefined | null): string => {
  if (count == undefined || count == null) return t('commons.unlimited');
  return count == -1 ? t('commons.unlimited') : `${count}`;
};
