import enum


class ChatStatus(enum.Enum):
    asking = "asking"
    queueing = "queueing"
    idling = "idling"


class ChatModels(enum.Enum):
    gpt4 = "gpt-4"
    default = "text-davinci-002-render-sha"
    paid = "text-davinci-002-render-paid"
    unknown = ""
    
    gpt35_openai = "openai-gpt-3.5-turbo"
    gpt35_0301_openai = "openai-gpt-3.5-turbo-0301"
    gpt4_openai = "openai-gpt-4"
    gpt4_0314_openai = "openai-gpt-4-0314"
    gpt4_32k_openai= "openai-gpt-4-32k"
    
    gpt35_azure = 'azure-gpt-35-turbo'
    gpt4_azure = "azure-gpt-4"
    gpt4_32k_azure = "azure-gpt-4-32k"
    
    
    def is_api(self):
        return self.value.startswith("azure") or self.value.startswith("openai")