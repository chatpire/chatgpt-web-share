from enum import auto

from strenum import StrEnum


class ChatSourceTypes(StrEnum):
    rev = auto()
    api = auto()


chat_model_definitions = {
    "rev": {
        "gpt_3_5": "text-davinci-002-render-sha",
        "gpt_4": "gpt-4",
        "gpt_4_browsing": "__to_be_supported__"
    },
    "api": {
        "gpt_3_5": "gpt-3.5-turbo",
        "gpt_4": "gpt-4",
    }
}


# 这里处理model定义的逻辑是：
# rev 和 api 各自有不同的model code, model name可以重复
# 在需要并集的场景下，如 ChatMessage，使用 str 类型

class BaseChatModelEnum(StrEnum):
    __type: ChatSourceTypes

    def code(self, source_type: ChatSourceTypes):
        result = chat_model_definitions[source_type].get(self.name, None)
        assert result, f"model name not found: {self.name}"
        return result

    @classmethod
    def from_code(cls, code: str):
        for name, value in chat_model_definitions[cls.__type].items():
            if value == code:
                return cls[name]
        return None


class RevChatModels(BaseChatModelEnum):
    __type = ChatSourceTypes.rev

    gpt_3_5 = auto()
    gpt_4 = auto()
    gpt_4_browsing = auto()


class ApiChatModels(BaseChatModelEnum):
    __type = ChatSourceTypes.api

    gpt_3_5 = auto()
    gpt_4 = auto()


if __name__ == "__main__":
    print(list(RevChatModels))
