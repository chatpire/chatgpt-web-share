export const timeFormatter = (value: string | Date | number, withYear: boolean) => {
  // const date = typeof value === 'string' ? new Date(value) : value;
  if (typeof value === 'string' || typeof value === 'number') {
    value = new Date(value);
  }
  const date = value;
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const hour = date.getHours().toString().padStart(2, '0');
  const minute = date.getMinutes().toString().padStart(2, '0');
  return (withYear ? `${year}-` : '') + `${month}-${day} ${hour}:${minute}`;
};
