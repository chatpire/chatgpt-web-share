// 对于 enum array 需要设置 uniqueItems 才能渲染为复选框
function setUniqueItemsForEnumProperties(obj: any) {
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
      // console.log(obj['allOf'][0]);
      for (const key in obj['allOf'][0]['properties']) {
        setUniqueItemsForEnumProperties(obj['allOf'][0]['properties'][key]);
      }
    }
  }
}

/**
   pydantic V2 会将 optional 的字段转换为 anyOf，例如：
   "valid_until": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Valid Until"
    }
  见：https://github.com/pydantic/pydantic/issues/7161
  这显然不是我们想要的，它会让 form 中出现一个选择性下拉框。应当去除这一层 anyOf。
  具体来说：遍历 properties 中的字段. 假如一个字段：
    1. 在 required 中没有出现
    2. 具有 anyOf，且 anyOf 中有一个 type 为 null
  那么，去除 anyOf，将 type 设置为原本的 type。
  在上面的情况下，就应该转换为：
  "valid_until": {
    "type": "string",
    "format": "date-time",
    "title": "Valid Until"
  }
*/
function fixModelOptionalTypeAnyOf(model: any) {
  // console.log('fixModelOptionalTypeAnyOf', model);
  if (model['properties'] == undefined) {
    return;
  }
  const requiredProperties = model['required'] || [];
  for (const key in model['properties']) {
    const property = model['properties'][key];
    if (requiredProperties.indexOf(key) == -1 && property['anyOf'] != undefined) {
      const anyOf = property['anyOf'] as Array<any>;
      let hasNull = false;
      for (const item of anyOf) {
        if (item['type'] == 'null') {
          hasNull = true;
          break;
        }
      }
      if (hasNull) {
        delete property['anyOf'];
        property['type'] = anyOf[0]['type'];
      }
    }
    if (property['allOf'] != undefined) {
      for (const item of property['allOf']) {
        fixModelOptionalTypeAnyOf(item);
      }
    }
  }
}

export function fixModelSchema(model: any) {
  // console.log('fixModelSchema: before', model);
  setUniqueItemsForEnumProperties(model);
  fixModelOptionalTypeAnyOf(model);
  // console.log('fixModelSchema: after', model);
}