"""Exporta a tabela comparativa em CSV e Markdown."""

import csv
from datetime import datetime
from pathlib import Path

from zeros.resultado import Resultado

PASTA_DE_RESULTADOS = Path("resultados")
CABECALHO = ["Método", "Raiz", "Iterações", "Tempo (µs)", "|f(raiz)|", "Erro em x"]


def exportar_resultados(resultados: list[Resultado], titulo: str,
                        pasta: Path = PASTA_DE_RESULTADOS) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    base = pasta / f"comparacao_{datetime.now():%Y%m%d_%H%M%S}"
    return [_salvar_csv(resultados, base.with_suffix(".csv")),
            _salvar_markdown(resultados, titulo, base.with_suffix(".md"))]


def linha_da_tabela(resultado: Resultado) -> list[str]:
    return [
        resultado.metodo,
        "—" if resultado.raiz is None else f"{resultado.raiz:.10f}",
        str(resultado.iteracoes),
        f"{resultado.tempo_us:.2f}",
        "—" if resultado.residuo is None else f"{resultado.residuo:.3e}",
        _erro_em_x(resultado),
    ]


def _erro_em_x(resultado: Resultado) -> str:
    """|x_k − x_(k−1)| da última iteração."""
    erro = resultado.historico[-1].erro if resultado.historico else None
    return "—" if erro is None else f"{erro:.3e}"


def _salvar_csv(resultados: list[Resultado], caminho: Path) -> Path:
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")  # ";" é o separador do Excel em pt-BR
        escritor.writerow(CABECALHO)
        escritor.writerows(linha_da_tabela(r) for r in resultados)
    return caminho


def _salvar_markdown(resultados: list[Resultado], titulo: str, caminho: Path) -> Path:
    linhas = [f"### {titulo}", "", _linha_markdown(CABECALHO), _linha_markdown(["---"] * len(CABECALHO))]
    linhas += [_linha_markdown(linha_da_tabela(r)) for r in resultados]
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def _linha_markdown(celulas: list[str]) -> str:
    return "| " + " | ".join(c.replace("|", "\\|") for c in celulas) + " |"
