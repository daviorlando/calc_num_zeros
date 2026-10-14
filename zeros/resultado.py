"""Contrato comum entre os métodos numéricos, a interface e os gráficos.

Todo método devolve um `Resultado`; assim a interface não precisa saber
como cada algoritmo funciona por dentro para montar a tabela comparativa.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import NamedTuple


class Mensagem(StrEnum):
    """Situação final de um método (aparece na coluna "Status" da tabela)."""

    SUCESSO = "OK"
    EXTRAPOLOU_O_INTERVALO = "OK (extrapolou o intervalo)"
    SEM_MUDANCA_DE_SINAL = "sem mudança de sinal"
    DERIVADA_NULA = "derivada nula"
    DIVISAO_POR_ZERO = "divisão por zero"
    MAXIMO_DE_ITERACOES = "máx. iterações"
    FORA_DO_INTERVALO = "saiu do intervalo"
    VALOR_NAO_FINITO = "overflow/NaN"
    FORA_DO_DOMINIO = "fora do domínio de f"


MENSAGENS_DE_CONVERGENCIA = frozenset({Mensagem.SUCESSO, Mensagem.EXTRAPOLOU_O_INTERVALO})


class Iteracao(NamedTuple):
    """Um passo do método: (k, x_k, f(x_k), erro)."""

    numero: int
    aproximacao: float
    valor_da_funcao: float
    erro: float | None  # |x_k - x_(k-1)|; None quando ainda não há x_(k-1)


@dataclass
class Resultado:
    metodo: str
    raiz: float | None
    iteracoes: int
    tempo_ms: float
    residuo: float | None  # |f(raiz)|
    convergiu: bool
    mensagem: str
    historico: list[Iteracao] = field(default_factory=list)

    @property
    def tempo_us(self) -> float:
        return self.tempo_ms * 1000
