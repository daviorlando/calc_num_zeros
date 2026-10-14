"""Executa os quatro métodos com os mesmos dados e mede o tempo médio de cada um."""

import statistics
from collections.abc import Callable
from dataclasses import dataclass, replace

from zeros.entrada import FuncaoMatematica
from zeros.metodos import (
    EPSILON_PADRAO,
    MAXIMO_DE_ITERACOES_PADRAO,
    bisseccao,
    falsa_posicao,
    newton,
    secante,
)
from zeros.resultado import Resultado

# Uma única execução leva poucos microssegundos, perto da resolução do relógio;
# a média de muitas execuções torna o tempo comparável entre os métodos.
REPETICOES_PADRAO = 1000


@dataclass
class ParametrosDoCalculo:
    funcao: FuncaoMatematica
    derivada: FuncaoMatematica
    a: float
    b: float
    x0_newton: float
    x0_secante: float
    x1_secante: float
    epsilon: float = EPSILON_PADRAO
    maximo_de_iteracoes: int = MAXIMO_DE_ITERACOES_PADRAO
    repeticoes: int = REPETICOES_PADRAO

    @property
    def intervalo(self) -> tuple[float, float]:
        return self.a, self.b


def comparar_metodos(parametros: ParametrosDoCalculo) -> list[Resultado]:
    return [_executar_com_tempo_medio(execucao, parametros.repeticoes)
            for execucao in _execucoes_dos_metodos(parametros)]


def _execucoes_dos_metodos(p: ParametrosDoCalculo) -> list[Callable[[], Resultado]]:
    f, df, eps, max_iter = p.funcao, p.derivada, p.epsilon, p.maximo_de_iteracoes
    return [
        lambda: bisseccao(f, p.a, p.b, eps, max_iter),
        lambda: falsa_posicao(f, p.a, p.b, eps, max_iter),
        lambda: newton(f, df, p.x0_newton, eps, max_iter, intervalo=p.intervalo),
        lambda: secante(f, p.x0_secante, p.x1_secante, eps, max_iter, intervalo=p.intervalo),
    ]


def _executar_com_tempo_medio(executar: Callable[[], Resultado], repeticoes: int) -> Resultado:
    resultado = executar()
    tempos = [resultado.tempo_ms] + [executar().tempo_ms for _ in range(repeticoes - 1)]
    return replace(resultado, tempo_ms=statistics.fmean(tempos))
