"""Métodos da Bissecção, Falsa Posição, Newton-Raphson e Secante.

Cada função `_aproximacoes_...` só calcula a sequência x_k do seu método.
O critério de parada e o limite de iterações ficam em `_executar_metodo`,
iguais para os quatro.

Critério de parada: |x_k − x_(k−1)| < ε  ou  |f(x_k)| < ε.
"""

import math
import time
from collections.abc import Callable, Iterator

from zeros.resultado import MENSAGENS_DE_CONVERGENCIA, Iteracao, Mensagem, Resultado

EPSILON_PADRAO = 1e-6
MAXIMO_DE_ITERACOES_PADRAO = 100
LIMITE_DE_DERIVADA_NULA = 1e-14

Funcao = Callable[[float], float]
Aproximacoes = Iterator[tuple[float, float]]
Intervalo = tuple[float, float]

# Erro do Python ao avaliar f  ->  motivo mostrado ao usuário.
_FALHAS_DO_PYTHON = {
    ZeroDivisionError: Mensagem.DIVISAO_POR_ZERO,
    OverflowError: Mensagem.VALOR_NAO_FINITO,
    ValueError: Mensagem.FORA_DO_DOMINIO,
    TypeError: Mensagem.FORA_DO_DOMINIO,
}


class FalhaNumerica(Exception):
    """Interrompe o método e guarda o motivo da falha."""

    def __init__(self, motivo: Mensagem):
        super().__init__(motivo)
        self.motivo = motivo


def bisseccao(f: Funcao, a: float, b: float,
              eps: float = EPSILON_PADRAO,
              max_iter: int = MAXIMO_DE_ITERACOES_PADRAO) -> Resultado:
    return _executar_metodo("Bissecção", _aproximacoes_da_bisseccao(f, a, b), eps, max_iter)


def falsa_posicao(f: Funcao, a: float, b: float,
                  eps: float = EPSILON_PADRAO,
                  max_iter: int = MAXIMO_DE_ITERACOES_PADRAO) -> Resultado:
    return _executar_metodo("Falsa Posição", _aproximacoes_da_falsa_posicao(f, a, b), eps, max_iter)


def newton(f: Funcao, df: Funcao, x0: float,
           eps: float = EPSILON_PADRAO,
           max_iter: int = MAXIMO_DE_ITERACOES_PADRAO,
           intervalo: Intervalo | None = None) -> Resultado:
    """Se `intervalo` for informado, avisa quando algum x_k sai de [a, b]."""
    return _executar_metodo("Newton-Raphson", _aproximacoes_de_newton(f, df, x0), eps, max_iter,
                            aproximacao_anterior=x0, intervalo=intervalo)


def secante(f: Funcao, x0: float, x1: float,
            eps: float = EPSILON_PADRAO,
            max_iter: int = MAXIMO_DE_ITERACOES_PADRAO,
            intervalo: Intervalo | None = None) -> Resultado:
    return _executar_metodo("Secante", _aproximacoes_da_secante(f, x0, x1), eps, max_iter,
                            aproximacao_anterior=x1, intervalo=intervalo)


# --- Fórmula de cada método ------------------------------------------------

def _aproximacoes_da_bisseccao(f: Funcao, a: float, b: float) -> Aproximacoes:
    fa, fb = f(a), f(b)
    yield from _raizes_nos_extremos(a, fa, b, fb)
    _exigir_mudanca_de_sinal(fa, fb)
    while True:
        meio = (a + b) / 2                  # x_(k+1) = (a_k + b_k)/2
        f_meio = f(meio)
        yield meio, f_meio
        if fa * f_meio < 0:                 # raiz em [a_k, x_(k+1)]
            b = meio
        else:                               # raiz em [x_(k+1), b_k]
            a, fa = meio, f_meio


def _aproximacoes_da_falsa_posicao(f: Funcao, a: float, b: float) -> Aproximacoes:
    fa, fb = f(a), f(b)
    yield from _raizes_nos_extremos(a, fa, b, fb)
    _exigir_mudanca_de_sinal(fa, fb)
    while True:
        # Raiz da reta que liga (a, f(a)) a (b, f(b)).
        x = (a * fb - b * fa) / (fb - fa)
        fx = f(x)
        yield x, fx
        if fa * fx < 0:                     # raiz em [a_k, x_(k+1)]
            b, fb = x, fx
        else:                               # raiz em [x_(k+1), b_k]
            a, fa = x, fx


def _aproximacoes_de_newton(f: Funcao, df: Funcao, x0: float) -> Aproximacoes:
    x, fx = x0, f(x0)
    while True:
        derivada = df(x)
        if abs(derivada) < LIMITE_DE_DERIVADA_NULA:   # tangente horizontal
            raise FalhaNumerica(Mensagem.DERIVADA_NULA)
        x = x - fx / derivada               # x_(k+1) = x_k − f(x_k)/f'(x_k)
        fx = f(x)
        yield x, fx


def _aproximacoes_da_secante(f: Funcao, x0: float, x1: float) -> Aproximacoes:
    anterior, f_anterior = x0, f(x0)
    atual, f_atual = x1, f(x1)
    while True:
        if f_atual == f_anterior:           # secante horizontal
            raise FalhaNumerica(Mensagem.DIVISAO_POR_ZERO)
        # x_(k+1) = x_k − f(x_k)·(x_k − x_(k−1)) / (f(x_k) − f(x_(k−1)))
        proxima = atual - f_atual * (atual - anterior) / (f_atual - f_anterior)
        anterior, f_anterior = atual, f_atual
        atual, f_atual = proxima, f(proxima)
        yield atual, f_atual


def _raizes_nos_extremos(a: float, fa: float, b: float, fb: float) -> Aproximacoes:
    """Se f(a) = 0 ou f(b) = 0, o extremo já é a raiz."""
    if fa == 0:
        yield a, fa
    if fb == 0:
        yield b, fb


def _exigir_mudanca_de_sinal(fa: float, fb: float) -> None:
    if fa * fb > 0:
        raise FalhaNumerica(Mensagem.SEM_MUDANCA_DE_SINAL)


# --- Critério de parada (comum aos quatro métodos) --------------------------

def _executar_metodo(nome: str, aproximacoes: Aproximacoes, eps: float, max_iter: int,
                     aproximacao_anterior: float | None = None,
                     intervalo: Intervalo | None = None) -> Resultado:
    historico: list[Iteracao] = []
    inicio = time.perf_counter_ns()
    try:
        _iterar_ate_convergir(aproximacoes, eps, max_iter, aproximacao_anterior, historico)
        motivo = _verificar_intervalo(historico, intervalo)
    except FalhaNumerica as falha:
        motivo = falha.motivo
    except tuple(_FALHAS_DO_PYTHON) as erro:
        motivo = _motivo_do_erro_do_python(erro)
    tempo_ms = (time.perf_counter_ns() - inicio) / 1_000_000
    return _montar_resultado(nome, historico, tempo_ms, motivo)


def _iterar_ate_convergir(aproximacoes: Aproximacoes, eps: float, max_iter: int,
                          anterior: float | None, historico: list[Iteracao]) -> None:
    for numero, (x, fx) in enumerate(aproximacoes, start=1):
        if not (math.isfinite(x) and math.isfinite(fx)):
            raise FalhaNumerica(Mensagem.VALOR_NAO_FINITO)
        erro = None if anterior is None else abs(x - anterior)
        historico.append(Iteracao(numero, x, fx, erro))
        if _atingiu_a_precisao(fx, erro, eps):
            return
        if numero >= max_iter:
            raise FalhaNumerica(Mensagem.MAXIMO_DE_ITERACOES)
        anterior = x


def _atingiu_a_precisao(fx: float, erro: float | None, eps: float) -> bool:
    return abs(fx) < eps or (erro is not None and erro < eps)


def _verificar_intervalo(historico: list[Iteracao], intervalo: Intervalo | None) -> Mensagem:
    """Newton e Secante: indica se algum x_k ficou fora de [a, b]."""
    if intervalo is None:
        return Mensagem.SUCESSO
    a, b = intervalo
    dentro = [a <= passo.aproximacao <= b for passo in historico]
    if not dentro[-1]:
        return Mensagem.FORA_DO_INTERVALO
    if not all(dentro):
        return Mensagem.EXTRAPOLOU_O_INTERVALO
    return Mensagem.SUCESSO


def _motivo_do_erro_do_python(erro: Exception) -> Mensagem:
    for tipo, motivo in _FALHAS_DO_PYTHON.items():
        if isinstance(erro, tipo):
            return motivo
    raise erro


def _montar_resultado(nome: str, historico: list[Iteracao], tempo_ms: float,
                      motivo: Mensagem) -> Resultado:
    ultimo_passo = historico[-1] if historico else None
    return Resultado(
        metodo=nome,
        raiz=ultimo_passo.aproximacao if ultimo_passo else None,
        iteracoes=len(historico),
        tempo_ms=tempo_ms,
        residuo=abs(ultimo_passo.valor_da_funcao) if ultimo_passo else None,
        convergiu=motivo in MENSAGENS_DE_CONVERGENCIA,
        mensagem=motivo,
        historico=historico,
    )
