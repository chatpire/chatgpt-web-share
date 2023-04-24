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
    gpt4 = "gpt-4"
    default = "text-davinci-002-render-sha"
    paid = "text-davinci-002-render-paid"


class ApiChatModels(Enum):
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4"
