// 对于 enum array 需要设置 uniqueItems 才能渲染为复选框
export function setUniqueItemsForEnumProperties(obj: any) {
  if (obj['type'] == 'array' && obj['items']) {
    obj['uniqueItems'] = true;
  }
  if (obj['properties'] != undefined) {
    // 递归遍历
    for (const key in obj['properties']) {
      setUniqueItemsForEnumProperties(obj['properties'][key]);
    }
  } else if (obj['allOf'] != undefined) {
    if (obj['allOf'][0]['properties'] != undefined) {
      console.log(obj['allOf'][0]);
      for (const key in obj['allOf'][0]['properties']) {
        setUniqueItemsForEnumProperties(obj['allOf'][0]['properties'][key]);
      }
    }
  }
}
