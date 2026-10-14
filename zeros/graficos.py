"""Gráficos (bônus): a função com as raízes encontradas e a convergência dos métodos."""

import math
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from zeros.entrada import FuncaoMatematica
from zeros.resultado import Resultado

PASTA_DE_GRAFICOS = Path("graficos")
PONTOS_NA_CURVA = 500
MENOR_VALOR_NO_EIXO_LOG = 1e-17  # |f| = 0 exato não aparece em escala log
MARGEM_RELATIVA = 0.1

# Cores categóricas validadas para daltonismo, em ordem fixa, uma por método.
# Cada método também tem marcador próprio, para não depender só da cor.
ESTILO_DOS_METODOS = {
    "Bissecção": {"color": "#2a78d6", "marker": "o"},
    "Falsa Posição": {"color": "#eb6834", "marker": "s"},
    "Newton-Raphson": {"color": "#1baf7a", "marker": "^"},
    "Secante": {"color": "#eda100", "marker": "D"},
}
COR_DA_CURVA = "#0b0b0b"
COR_SECUNDARIA = "#52514e"


def gerar_graficos(funcao: FuncaoMatematica, resultados: list[Resultado],
                   intervalo: tuple[float, float], titulo: str, epsilon: float,
                   pasta: Path = PASTA_DE_GRAFICOS) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    prefixo = _nome_de_arquivo(titulo)
    return [
        plotar_funcao_e_raizes(funcao, resultados, intervalo, titulo, pasta / f"{prefixo}_funcao.png"),
        plotar_convergencia(resultados, titulo, epsilon, pasta / f"{prefixo}_convergencia.png"),
    ]


def plotar_funcao_e_raizes(funcao: FuncaoMatematica, resultados: list[Resultado],
                           intervalo: tuple[float, float], titulo: str, caminho: Path) -> Path:
    inicio, fim = _limites_do_eixo_x(intervalo, resultados)
    abscissas = [inicio + (fim - inicio) * i / PONTOS_NA_CURVA for i in range(PONTOS_NA_CURVA + 1)]
    ordenadas = [_avaliar_ou_nan(funcao, x) for x in abscissas]

    figura, eixo = plt.subplots(figsize=(9, 5.5))
    eixo.plot(abscissas, ordenadas, color=COR_DA_CURVA, linewidth=2, label=f"f({funcao.variavel}) = {funcao}")
    eixo.axhline(0, color=COR_SECUNDARIA, linewidth=1)
    eixo.axvspan(*intervalo, color=COR_SECUNDARIA, alpha=0.08, label="intervalo [a, b]")
    for tamanho, resultado in zip((14, 11, 8, 5), _resultados_com_raiz(resultados)):
        estilo = ESTILO_DOS_METODOS[resultado.metodo]
        eixo.plot(resultado.raiz, 0, linestyle="none", markersize=tamanho,
                  markerfacecolor="none", markeredgewidth=2, **estilo,
                  label=f"{resultado.metodo}: {resultado.raiz:.8f}")
    _formatar_eixos(eixo, titulo, str(funcao.variavel), f"f({funcao.variavel})")
    return _salvar(figura, caminho)


def plotar_convergencia(resultados: list[Resultado], titulo: str, epsilon: float, caminho: Path) -> Path:
    figura, eixo = plt.subplots(figsize=(9, 5.5))
    for resultado in resultados:
        if not resultado.historico:
            continue
        iteracoes = [passo.numero for passo in resultado.historico]
        residuos = [max(abs(passo.valor_da_funcao), MENOR_VALOR_NO_EIXO_LOG) for passo in resultado.historico]
        eixo.semilogy(iteracoes, residuos, linewidth=2, markersize=6,
                      label=f"{resultado.metodo} ({resultado.iteracoes} it.)",
                      **ESTILO_DOS_METODOS[resultado.metodo])
    eixo.axhline(epsilon, color=COR_SECUNDARIA, linestyle="--", linewidth=1, label=f"ε = {epsilon:g}")
    _formatar_eixos(eixo, f"Convergência — {titulo}", "iteração k", "|f(x_k)|  (escala log)")
    return _salvar(figura, caminho)


def exibir_graficos() -> None:
    plt.show()


def fechar_graficos() -> None:
    plt.close("all")


def pode_exibir_janelas() -> bool:
    return "agg" not in matplotlib.get_backend().lower()


def _resultados_com_raiz(resultados: list[Resultado]) -> list[Resultado]:
    return [r for r in resultados if r.raiz is not None and r.convergiu]


def _limites_do_eixo_x(intervalo: tuple[float, float], resultados: list[Resultado]) -> tuple[float, float]:
    """O eixo cobre o intervalo e também raízes que ficaram fora dele."""
    pontos = [*intervalo, *(r.raiz for r in _resultados_com_raiz(resultados))]
    inicio, fim = min(pontos), max(pontos)
    margem = (fim - inicio) * MARGEM_RELATIVA or 1.0
    return inicio - margem, fim + margem


def _avaliar_ou_nan(funcao: FuncaoMatematica, valor: float) -> float:
    try:
        return funcao(valor)
    except (ArithmeticError, ValueError, TypeError):
        return math.nan


def _formatar_eixos(eixo, titulo: str, rotulo_x: str, rotulo_y: str) -> None:
    eixo.set_title(titulo, loc="left", fontsize=12)
    eixo.set_xlabel(rotulo_x, color=COR_SECUNDARIA)
    eixo.set_ylabel(rotulo_y, color=COR_SECUNDARIA)
    eixo.grid(True, color="#e4e3df", linewidth=0.8)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.legend(frameon=False, fontsize=9)


def _salvar(figura, caminho: Path) -> Path:
    figura.tight_layout()
    figura.savefig(caminho, dpi=150)
    return caminho


def _nome_de_arquivo(titulo: str) -> str:
    simplificado = "".join(c if c.isalnum() else "_" for c in titulo.split(":")[0].lower())
    return simplificado.strip("_") or "grafico"
