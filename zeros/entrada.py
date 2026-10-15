"""Leitura e validação dos dados digitados.

f(x) é interpretada com sympy: `cos(x) - x`, `x^2 - 2`, `0,5*x`, `sen(x)`, `ln(x)`.
Se a entrada for inválida, mostra o erro e pergunta de novo.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

import sympy
from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm, InvalidResponse, Prompt
from rich.text import Text
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

console = Console()


class Pergunta(Prompt):
    """Prompt do rich com mensagens de erro em português."""

    illegal_choice_message = "[red]Escolha uma das opções disponíveis.[/]"
    validate_error_message = "[red]Valor inválido.[/]"


class Confirmacao(Confirm):
    """Pergunta de sim/não respondida com s/n."""

    choices = ["s", "n"]
    validate_error_message = "[red]Responda s (sim) ou n (não).[/]"

    def render_default(self, default):
        return Text(f"({'s' if default else 'n'})", style="prompt.default")

    def process_response(self, value: str) -> bool:
        resposta = value.strip().lower()
        if resposta not in self.choices:
            raise InvalidResponse(self.validate_error_message)
        return resposta == "s"

VARIAVEL_PADRAO = sympy.Symbol("x")
SUBDIVISOES_DA_BUSCA_DE_INTERVALO = 1000

_TRANSFORMACOES = standard_transformations + (implicit_multiplication_application, convert_xor)
_NOMES_ACEITOS = {
    "sen": sympy.sin,
    "tg": sympy.tan,
    "ln": sympy.log,
    "raiz": sympy.sqrt,
    "e": sympy.E,
    "pi": sympy.pi,
}
_VIRGULA_DECIMAL = re.compile(r"(\d),(\d)")


class EntradaInvalida(ValueError):
    """Texto digitado que não pode ser interpretado."""


@dataclass(frozen=True)
class FuncaoMatematica:
    """Uma f(x) digitada pelo usuário, pronta para ser avaliada numericamente."""

    expressao: sympy.Expr
    variavel: sympy.Symbol
    avaliar: Callable[[float], float]
    texto: str | None = None  # como o usuário digitou (mais legível que a forma do sympy)

    def __call__(self, valor: float) -> float:
        return self.avaliar(valor)

    def __str__(self) -> str:
        return self.texto or sympy.sstr(self.expressao)

    def derivada(self) -> "FuncaoMatematica":
        return _compilar(sympy.diff(self.expressao, self.variavel), self.variavel)


# --- Interpretação de textos (sem interação) -------------------------------

def criar_funcao(texto: str, variavel: sympy.Symbol | None = None) -> FuncaoMatematica:
    """Converte texto em função. Se `variavel` for dada, exige que o texto a use."""
    expressao = _interpretar_expressao(texto)
    variavel_do_texto = _variavel_unica(expressao)
    if variavel is not None and variavel_do_texto not in (None, variavel):
        raise EntradaInvalida(f"use a mesma variável de f ({variavel}).")
    return _compilar(expressao, variavel or variavel_do_texto or VARIAVEL_PADRAO, texto.strip())


def converter_numero(texto: str) -> float:
    """Aceita `0,5`, `1e-6`, `pi/2`, `ln(3)/0.15`..."""
    expressao = _interpretar_expressao(texto)
    if expressao.free_symbols:
        raise EntradaInvalida("digite um número, não uma expressão com variáveis.")
    valor = complex(expressao.evalf())
    if valor.imag != 0:
        raise EntradaInvalida("o número precisa ser real.")
    return valor.real


def sugerir_intervalo(funcao: FuncaoMatematica, inicio: float, fim: float,
                      subdivisoes: int = SUBDIVISOES_DA_BUSCA_DE_INTERVALO) -> tuple[float, float] | None:
    """Varre [inicio, fim] e devolve o primeiro subintervalo com troca de sinal."""
    passo = (fim - inicio) / subdivisoes
    pontos = [inicio + i * passo for i in range(subdivisoes + 1)]
    for esquerda, direita in zip(pontos, pontos[1:]):
        valor_esquerda, valor_direita = _avaliar_sem_erro(funcao, esquerda), _avaliar_sem_erro(funcao, direita)
        if valor_esquerda is not None and valor_direita is not None and valor_esquerda * valor_direita <= 0:
            return esquerda, direita
    return None


def tem_mudanca_de_sinal(funcao: FuncaoMatematica, a: float, b: float) -> bool:
    valor_a, valor_b = _avaliar_sem_erro(funcao, a), _avaliar_sem_erro(funcao, b)
    return valor_a is not None and valor_b is not None and valor_a * valor_b <= 0


def _interpretar_expressao(texto: str) -> sympy.Expr:
    texto_normalizado = _VIRGULA_DECIMAL.sub(r"\1.\2", texto.strip())
    if not texto_normalizado:
        raise EntradaInvalida("nada foi digitado.")
    try:
        expressao = parse_expr(texto_normalizado, local_dict=dict(_NOMES_ACEITOS),
                               transformations=_TRANSFORMACOES)
    except Exception as erro:  # o parser do sympy lança vários tipos diferentes
        raise EntradaInvalida(f"não entendi '{texto}'.") from erro
    if not isinstance(expressao, sympy.Expr):
        raise EntradaInvalida(f"'{texto}' não é uma expressão matemática.")
    return expressao


def _variavel_unica(expressao: sympy.Expr) -> sympy.Symbol | None:
    variaveis = expressao.free_symbols
    if len(variaveis) > 1:
        nomes = ", ".join(sorted(str(v) for v in variaveis))
        raise EntradaInvalida(f"a função deve ter uma só variável (encontrei {nomes}).")
    return next(iter(variaveis), None)


def _compilar(expressao: sympy.Expr, variavel: sympy.Symbol, texto: str | None = None) -> FuncaoMatematica:
    funcao_compilada = sympy.lambdify(variavel, expressao, modules="math")
    return FuncaoMatematica(expressao, variavel, lambda valor: float(funcao_compilada(valor)), texto)


def _avaliar_sem_erro(funcao: FuncaoMatematica, valor: float) -> float | None:
    try:
        return funcao(valor)
    except (ArithmeticError, ValueError, TypeError):
        return None


# --- Perguntas ao usuário (repetem até receber algo válido) ----------------

def ler_funcao(rotulo: str = "f(x)", padrao: str | None = None) -> FuncaoMatematica:
    return _perguntar_ate_ser_valido(rotulo, criar_funcao, padrao)


def ler_derivada(funcao: FuncaoMatematica, padrao: str | None = None) -> FuncaoMatematica:
    """Enter vazio calcula a derivada automaticamente com sympy."""
    variavel = funcao.variavel
    rotulo = f"f'({variavel}) [Enter = calcular automaticamente]"
    while True:
        texto = Pergunta.ask(rotulo, default=padrao or "", show_default=bool(padrao), console=console)
        if not texto.strip():
            derivada = funcao.derivada()
            console.print(f"  Derivada calculada: f'({variavel}) = [cyan]{escape(str(derivada))}[/]")
            return derivada
        try:
            return criar_funcao(texto, variavel)
        except EntradaInvalida as erro:
            _avisar(erro)


def ler_numero(rotulo: str, padrao: float | None = None) -> float:
    return _perguntar_ate_ser_valido(rotulo, converter_numero, _formatar_padrao(padrao))


def ler_numero_positivo(rotulo: str, padrao: float | None = None) -> float:
    while True:
        valor = ler_numero(rotulo, padrao)
        if valor > 0:
            return valor
        _avisar("o valor precisa ser maior que zero.")


def ler_inteiro_positivo(rotulo: str, padrao: int | None = None) -> int:
    while True:
        valor = ler_numero(rotulo, padrao)
        if valor > 0 and float(valor).is_integer():
            return int(valor)
        _avisar("digite um número inteiro maior que zero.")


def ler_intervalo(funcao: FuncaoMatematica, padrao: tuple[float, float] | None = None) -> tuple[float, float]:
    """Lê [a, b] com a < b; se não houver troca de sinal, oferece um intervalo sugerido."""
    padrao_a, padrao_b = padrao or (None, None)
    while True:
        a = ler_numero("a (início do intervalo)", padrao_a)
        b = ler_numero("b (fim do intervalo)", padrao_b)
        if a >= b:
            _avisar("é preciso que a < b.")
            continue
        if tem_mudanca_de_sinal(funcao, a, b):
            return a, b
        sugestao = sugerir_intervalo(funcao, a, b)
        if sugestao and confirmar(f"f(a)·f(b) > 0. Usar o intervalo sugerido "
                                  f"[{sugestao[0]:.6g}, {sugestao[1]:.6g}]?", padrao=True):
            return sugestao
        if confirmar("Manter \\[a, b] mesmo assim? (Bissecção e Falsa Posição vão falhar)", padrao=False):
            return a, b


def confirmar(pergunta: str, padrao: bool = True) -> bool:
    return Confirmacao.ask(pergunta, default=padrao, console=console)


def _perguntar_ate_ser_valido(rotulo: str, converter: Callable, padrao: str | None):
    while True:
        texto = Pergunta.ask(rotulo, default=padrao, console=console)
        try:
            return converter(texto or "")
        except EntradaInvalida as erro:
            _avisar(erro)


def _formatar_padrao(valor: float | None) -> str | None:
    return None if valor is None else f"{valor:g}"


def _avisar(mensagem) -> None:
    console.print(f"  [red]Entrada inválida:[/] {escape(str(mensagem))}")
