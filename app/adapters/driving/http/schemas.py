import base64
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ImagemRequest(BaseModel):
    """
    Modelo de entrada para imagens recebidas pela API.

    A imagem é recebida em Base64 para atender ao critério
    de imagens incorporadas no JSON.
    """

    nome: str = Field(..., min_length=1)
    conteudo_base64: str = Field(..., min_length=1)
    tipo_mime: str = Field(default="image/png")
    legenda: str | None = None

    @field_validator("conteudo_base64")
    @classmethod
    def validar_base64(cls, valor: str) -> str:
        try:
            base64.b64decode(valor, validate=True)
        except Exception as exc:
            raise ValueError(
                "conteudo_base64 deve ser uma string Base64 válida."
            ) from exc

        return valor


class SecaoRequest(BaseModel):
    """
    Modelo de entrada para cada seção do relatório.
    """

    titulo: str = Field(..., min_length=1)
    paragrafos: list[str] = Field(default_factory=list)
    listas: list[list[str]] = Field(default_factory=list)
    imagens: list[ImagemRequest] = Field(default_factory=list)


class RelatorioRequest(BaseModel):
    """
    Modelo principal recebido pelo endpoint POST /reports.
    """

    titulo: str = Field(..., min_length=1)
    formato: Literal["md", "markdown", "docx", "pdf"] = "md"
    subtitulo: str | None = None
    autor: str | None = None
    metadados: dict[str, str] = Field(default_factory=dict)
    secoes: list[SecaoRequest] = Field(..., min_length=1)