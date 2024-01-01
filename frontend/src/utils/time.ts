import { i18n } from '@/i18n';
import { useAppStore } from '@/store';
const appStore = useAppStore();
const t = i18n.global.t as any;

export const shouldFixUTC = (create_time: string) => !create_time.endsWith('Z') && !/[+-]\d\d:?\d\d/.test(create_time);

export const parseTimeString = (time: string) => {
  if (shouldFixUTC(time)) {
    time += 'Z';
  }
  const lang = appStore.language;
  return new Date(time).toLocaleString(lang == 'zh-CN' ? 'zh-CN' : 'en-US', {
    hour12: false,
    timeZone: lang == 'zh-CN' ? 'Asia/Shanghai' : 'America/New_York',
  });
};

export const parseTimeToRelative = (time: string) => {
  if (shouldFixUTC(time)) {
    time += 'Z';
  }

  const diff = (new Date().getTime() - new Date(time).getTime()) / 1000;

  if (diff < 60) {
    return t('commons.justNow');
  } else if (diff < 24 * 60 * 60) {
    const minutes = Math.floor(diff / 60);
    const hours = Math.floor(minutes / 60);
    if (hours > 0) {
      return t('commons.hoursMinutesAgo', [hours, minutes % 60]);
    } else {
      return t('commons.minutesAgo', [minutes]);
    }
  } else {
    return parseTimeString(time);
  }
};