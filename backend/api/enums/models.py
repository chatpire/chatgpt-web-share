from enum import auto

from strenum import StrEnum


class ChatSourceTypes(StrEnum):
    rev = auto()
    api = auto()


chat_model_definitions = {
    "rev": {
        "gpt_3_5": "text-davinci-002-render-sha",
        "gpt_4": "gpt-4",
        "gpt_4_browsing": "gpt-4-browsing",
        "gpt_4_plugins": "gpt-4-plugins",
    },
    "api": {
        "gpt_3_5": "gpt-3.5-turbo",
        "gpt_4": "gpt-4",
    }
}

# 这里处理model定义的逻辑是：
# rev 和 api 各自有不同的model code, model name可以重复
# 在需要并集的场景下，如 ChatMessage，使用 str 类型


cls_to_source_type = {
    "RevChatModels": ChatSourceTypes.rev,
    "ApiChatModels": ChatSourceTypes.api,
}


class BaseChatModelEnum(StrEnum):
    def code(self):
        source_type = cls_to_source_type.get(self.__class__.__name__, None)
        result = chat_model_definitions[source_type].get(self.name, None)
        assert result, f"model name not found: {self.name}"
        return result

    @classmethod
    def from_code(cls, code: str):
        source_type = cls_to_source_type.get(cls.__name__, None)
        for name, value in chat_model_definitions[source_type].items():
            if value == code:
                return cls[name]
        return None


class RevChatModels(BaseChatModelEnum):
    gpt_3_5 = auto()
    gpt_4 = auto()
    gpt_4_browsing = auto()
    gpt_4_plugins = auto()


class ApiChatModels(BaseChatModelEnum):
    gpt_3_5 = auto()
    gpt_4 = auto()


if __name__ == "__main__":
    print(list(RevChatModels))
