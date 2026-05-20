# Definizione dei modelli Pydantic per validare i dati inviati e ricevuti dall'API.
from pydantic import BaseModel,ConfigDict,Field

class PostBase(BaseModel):
    # Definisce i campi comuni a richiesta e risposta.
    title:str = Field(min_length=1,max_length=100)
    content:str = Field(min_length=1)
    author:str = Field(min_length=1,max_length=50)

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    model_config=ConfigDict(from_attributes=True)

    id:int
    date_posted:str