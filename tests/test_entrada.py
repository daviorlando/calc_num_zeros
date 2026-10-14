import math

import pytest

from zeros.entrada import EntradaInvalida, converter_numero, criar_funcao, sugerir_intervalo


@pytest.mark.parametrize("texto, ponto, esperado", [
    ("cos(x) - x", 0.0, 1.0),
    ("20 + 90*exp(-0.15*t) - 50", 0.0, 60.0),
    ("x^2 - 2", 3.0, 7.0),
    ("0,5*x", 4.0, 2.0),
    ("sen(x) + ln(x)", 1.0, math.sin(1.0)),
    ("2x + 1", 1.0, 3.0),
])
def test_criar_funcao_aceita_notacoes_usuais(texto, ponto, esperado):
    assert criar_funcao(texto)(ponto) == pytest.approx(esperado)


def test_variavel_e_detectada_no_texto():
    assert str(criar_funcao("exp(-t) - 0.5").variavel) == "t"


def test_derivada_automatica():
    derivada = criar_funcao("cos(x) - x").derivada()

    assert derivada(0.5) == pytest.approx(-math.sin(0.5) - 1)


@pytest.mark.parametrize("texto", ["", "cos(x", "x + y", "x ==== 2"])
def test_textos_invalidos_viram_entrada_invalida(texto):
    with pytest.raises(EntradaInvalida):
        criar_funcao(texto)


def test_derivada_precisa_usar_a_mesma_variavel():
    funcao = criar_funcao("exp(-t) - 0.5")

    with pytest.raises(EntradaInvalida):
        criar_funcao("-exp(-x)", funcao.variavel)


@pytest.mark.parametrize("texto, esperado", [("0,5", 0.5), ("1e-6", 1e-6), ("ln(3)/0,15", math.log(3) / 0.15)])
def test_converter_numero(texto, esperado):
    assert converter_numero(texto) == pytest.approx(esperado)


def test_converter_numero_rejeita_variaveis():
    with pytest.raises(EntradaInvalida):
        converter_numero("2x")


def test_sugerir_intervalo_encontra_troca_de_sinal():
    a, b = sugerir_intervalo(criar_funcao("x^2 - 2"), 0, 10)

    assert a <= math.sqrt(2) <= b


def test_sugerir_intervalo_sem_raiz():
    assert sugerir_intervalo(criar_funcao("x^2 + 1"), -10, 10) is None
