import { ref } from 'vue';

type UseDrawerOption = {
  name: string;
  title: string;
  beforeOpen?: (row: any) => void;
  afterClose?: () => void;
};

export function useDrawer(options: UseDrawerOption[]) {
  const show = ref(false);
  const title = ref('');
  const name = ref('');
  const _options = options;

  // console.log('useDrawer', options);

  function open(_name: string, row: any) {
    const opt = _options.find((option) => option.name === _name);
    name.value = _name;
    title.value = opt?.title || '';
    opt?.beforeOpen?.(row);
    show.value = true;
    console.log('open', _name, opt);
  }

  function close() {
    const opt = _options.find((option) => option.name === name.value);
    show.value = false;
    opt?.afterClose?.();
  }

  return { show, title, name, open, close };
}
