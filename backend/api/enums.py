import enum


class ChatStatus(enum.Enum):
    asking = "asking"
    queueing = "queueing"
    idling = "idling"


class ChatModels(enum.Enum):
    gpt4 = "gpt-4"
    gpt4_mobile = "gpt-4-mobile"
    default = "text-davinci-002-render-sha"
    paid = "text-davinci-002-render-paid"
    unknown = ""
