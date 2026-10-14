"""Os quatro métodos iterativos para encontrar zeros de funções.

Cada método é escrito como um *gerador* que só sabe produzir a próxima
aproximação (x_k, f(x_k)). Tudo o que é comum aos quatro — critério de
parada, limite de iterações, histórico, medição de tempo e tratamento de
falhas — fica concentrado em `_executar_metodo`, evitando repetição.

Critério de parada: |x_k - x_(k-1)| < ε  ou  |f(x_k)| < ε.
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

# Erros que o próprio Python lança ao avaliar f e o motivo que mostramos ao usuário.
_FALHAS_DO_PYTHON = {
    ZeroDivisionError: Mensagem.DIVISAO_POR_ZERO,
    OverflowError: Mensagem.VALOR_NAO_FINITO,
    ValueError: Mensagem.FORA_DO_DOMINIO,
    TypeError: Mensagem.FORA_DO_DOMINIO,
}


class FalhaNumerica(Exception):
    """Interrompe um método explicando por que ele não pode continuar."""

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
    """`intervalo` é opcional: quando informado, avisa se as iterações saírem dele."""
    return _executar_metodo("Newton-Raphson", _aproximacoes_de_newton(f, df, x0), eps, max_iter,
                            aproximacao_anterior=x0, intervalo=intervalo)


def secante(f: Funcao, x0: float, x1: float,
            eps: float = EPSILON_PADRAO,
            max_iter: int = MAXIMO_DE_ITERACOES_PADRAO,
            intervalo: Intervalo | None = None) -> Resultado:
    return _executar_metodo("Secante", _aproximacoes_da_secante(f, x0, x1), eps, max_iter,
                            aproximacao_anterior=x1, intervalo=intervalo)


# --- Geradores: a fórmula de cada método -----------------------------------

def _aproximacoes_da_bisseccao(f: Funcao, a: float, b: float) -> Aproximacoes:
    fa, fb = f(a), f(b)
    yield from _raizes_nos_extremos(a, fa, b, fb)
    _exigir_mudanca_de_sinal(fa, fb)
    while True:
        meio = (a + b) / 2
        f_meio = f(meio)
        yield meio, f_meio
        if fa * f_meio < 0:
            b = meio
        else:
            a, fa = meio, f_meio


def _aproximacoes_da_falsa_posicao(f: Funcao, a: float, b: float) -> Aproximacoes:
    fa, fb = f(a), f(b)
    yield from _raizes_nos_extremos(a, fa, b, fb)
    _exigir_mudanca_de_sinal(fa, fb)
    while True:
        # Intersecção da reta que liga (a, f(a)) e (b, f(b)) com o eixo x.
        x = (a * fb - b * fa) / (fb - fa)
        fx = f(x)
        yield x, fx
        if fa * fx < 0:
            b, fb = x, fx
        else:
            a, fa = x, fx


def _aproximacoes_de_newton(f: Funcao, df: Funcao, x0: float) -> Aproximacoes:
    x, fx = x0, f(x0)
    while True:
        derivada = df(x)
        if abs(derivada) < LIMITE_DE_DERIVADA_NULA:
            raise FalhaNumerica(Mensagem.DERIVADA_NULA)
        x = x - fx / derivada
        fx = f(x)
        yield x, fx


def _aproximacoes_da_secante(f: Funcao, x0: float, x1: float) -> Aproximacoes:
    anterior, f_anterior = x0, f(x0)
    atual, f_atual = x1, f(x1)
    while True:
        if f_atual == f_anterior:
            raise FalhaNumerica(Mensagem.DIVISAO_POR_ZERO)
        proxima = atual - f_atual * (atual - anterior) / (f_atual - f_anterior)
        anterior, f_anterior = atual, f_atual
        atual, f_atual = proxima, f(proxima)
        yield atual, f_atual


def _raizes_nos_extremos(a: float, fa: float, b: float, fb: float) -> Aproximacoes:
    """Se um extremo já é raiz exata, ele é a resposta (a bissecção o perderia)."""
    if fa == 0:
        yield a, fa
    if fb == 0:
        yield b, fb


def _exigir_mudanca_de_sinal(fa: float, fb: float) -> None:
    if fa * fb > 0:
        raise FalhaNumerica(Mensagem.SEM_MUDANCA_DE_SINAL)


# --- Laço comum a todos os métodos -----------------------------------------

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
