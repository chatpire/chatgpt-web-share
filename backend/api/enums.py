import enum


class RevChatStatus(enum.Enum):
    asking = "asking"
    queueing = "queueing"
    idling = "idling"


class RevChatModels(enum.Enum):
    gpt4 = "gpt-4"
    default = "text-davinci-002-render-sha"
    paid = "text-davinci-002-render-paid"


class ApiChatModels(enum.Enum):
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4"
