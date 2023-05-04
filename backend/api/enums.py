import enum


class Enum(enum.Enum):
    @classmethod
    def names(cls):
        return [e.name for e in cls]

    @classmethod
    def values(cls):
        return [e.value for e in cls]


class RevChatStatus(Enum):
    asking = "asking"
    queueing = "queueing"
    idling = "idling"


class RevChatModels(Enum):
    default = "text-davinci-002-render-sha"
    gpt4 = "gpt-4"
    legacy = "text-davinci-002-render-paid"


class ApiChatModels(Enum):
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4"


class ChatGPTAPISource(Enum):
    openai = "openai"
    azure = "azure"
    custom = "custom"
