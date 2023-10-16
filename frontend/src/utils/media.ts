import { useWindowSize } from '@vueuse/core';

const { width } = useWindowSize();

export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const;

export function screenWidthGreaterThan(breakpoint: keyof typeof breakpoints | number) {
  // return computed(() => width.value >= (typeof breakpoint === 'number' ? breakpoint : breakpoints[breakpoint]));
  return () => {
    const result = width.value >= (typeof breakpoint === 'number' ? breakpoint : breakpoints[breakpoint]);
    // console.log('screenWidthGreaterThan', breakpoint, result);
    return result;
  };
}

export function sizeToHumanReadable(size: number) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  let unitIndex = 0;
  while (size > 1024) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
}
