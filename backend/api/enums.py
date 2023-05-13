from enum import auto
from strenum import StrEnum

model_name_to_code_mapping = {
    "rev": {
        "gpt_3_5": "text-davinci-002-render-sha",
        "gpt_4": "gpt-4",
    },
    "api": {
        "gpt_3_5": "gpt-3.5-turbo",
        "gpt_4": "gpt-4",
    }
}


class RevChatStatus(StrEnum):
    asking = auto()
    queueing = auto()
    idling = auto()


class ChatSourceTypes(StrEnum):
    rev = auto()
    api = auto()


class ChatModel(StrEnum):
    gpt_3_5 = auto()
    gpt_4 = auto()

    def code(self, source_type: ChatSourceTypes):
        result = model_name_to_code_mapping[source_type].get(self.name, None)
        assert result, f"model name not found: {self.name}"
        return result

    @classmethod
    def from_code(cls, code: str):
        model_code_to_name_mapping = {
            "text-davinci-002-render-sha": ChatModel.gpt_3_5,
            "gpt-4": ChatModel.gpt_4,
            "gpt-3.5-turbo": ChatModel.gpt_3_5,
        }
        return model_code_to_name_mapping.get(code, None)
