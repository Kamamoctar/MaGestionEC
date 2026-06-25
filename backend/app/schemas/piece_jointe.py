from datetime import datetime
from pydantic import BaseModel


class PieceJointeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    courrier_id: str
    nom_fichier: str
    taille_octets: int
    mime_type: str
    uploaded_at: datetime
