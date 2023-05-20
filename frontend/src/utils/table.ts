import { i18n } from '@/i18n';
const t = i18n.global.t as any;

// return a function which compare a['fieldName'] and b['fieldName']
export function getDateStringSorter<T>(fieldName: keyof T) {
  return (a: T, b: T) => {
    const aDate = new Date(a[fieldName] as any);
    const bDate = new Date(b[fieldName] as any);
    return aDate.getTime() - bDate.getTime();
  };
}
