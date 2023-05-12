from enum import auto
from strenum import StrEnum

model_name_mapping = {
    "chatgpt_3_5": "text-davinci-002-render-sha",
    "gpt_4": "gpt-4",
    "gpt_3_5_turbo": "gpt-3.5-turbo"
}


class RevChatStatus(StrEnum):
    asking = "asking"
    queueing = "queueing"
    idling = "idling"


class ModelEnum(StrEnum):
    def model_value(self):
        return model_name_mapping.get(self.name, None)


class RevChatModels(ModelEnum):
    chatgpt_3_5 = auto()
    gpt_4 = auto()


class ApiChatModels(ModelEnum):
    gpt_3_5_turbo = auto()
    gpt_4 = auto()


class ChatModels(ModelEnum):
    """merge RevChatModels and ApiChatModels"""
    chatgpt_3_5 = auto()
    gpt_4 = auto()
    gpt_3_5_turbo = auto()


if __name__ == '__main__':
    print([e.value for e in ChatModels])
