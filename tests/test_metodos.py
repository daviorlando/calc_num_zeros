import math

import pytest

from zeros.metodos import bisseccao, falsa_posicao, newton, secante
from zeros.problemas import PROBLEMAS
from zeros.resultado import Mensagem
from zeros.simulador import comparar_metodos

RAIZ_DE_COS_X_MENOS_X = 0.7390851332
EPSILON = 1e-6


def f(x):
    return math.cos(x) - x


def derivada_de_f(x):
    return -math.sin(x) - 1


METODOS_NO_EXEMPLO = {
    "bisseccao": lambda: bisseccao(f, 0, 1, EPSILON),
    "falsa_posicao": lambda: falsa_posicao(f, 0, 1, EPSILON),
    "newton": lambda: newton(f, derivada_de_f, 0.5, EPSILON),
    "secante": lambda: secante(f, 0, 1, EPSILON),
}


@pytest.mark.parametrize("executar", METODOS_NO_EXEMPLO.values(), ids=METODOS_NO_EXEMPLO.keys())
def test_metodos_encontram_a_raiz_de_cos_x_menos_x(executar):
    resultado = executar()

    assert resultado.convergiu
    assert resultado.mensagem == Mensagem.SUCESSO
    assert resultado.residuo < EPSILON
    assert resultado.raiz == pytest.approx(RAIZ_DE_COS_X_MENOS_X, abs=1e-6)
    assert resultado.iteracoes == len(resultado.historico) > 0
    assert resultado.tempo_ms >= 0


def test_metodos_abertos_usam_menos_iteracoes_que_a_bisseccao():
    iteracoes = {nome: executar().iteracoes for nome, executar in METODOS_NO_EXEMPLO.items()}

    assert iteracoes["newton"] < iteracoes["bisseccao"]
    assert iteracoes["secante"] < iteracoes["bisseccao"]


@pytest.mark.parametrize("metodo", [bisseccao, falsa_posicao])
def test_intervalo_sem_mudanca_de_sinal_falha_sem_excecao(metodo):
    resultado = metodo(lambda x: x**2 + 1, -1, 1)

    assert not resultado.convergiu
    assert resultado.mensagem == Mensagem.SEM_MUDANCA_DE_SINAL
    assert resultado.raiz is None


def test_newton_com_derivada_nula():
    resultado = newton(lambda x: x**2 + 1, lambda x: 2 * x, 0.0)

    assert not resultado.convergiu
    assert resultado.mensagem == Mensagem.DERIVADA_NULA


def test_secante_com_valores_iguais_de_f_indica_divisao_por_zero():
    resultado = secante(lambda x: x**2 - 4, -1, 1)

    assert resultado.mensagem == Mensagem.DIVISAO_POR_ZERO


def test_limite_de_iteracoes_e_respeitado():
    resultado = newton(lambda x: x**2 + 1, lambda x: 2 * x, 0.5, max_iter=10)

    assert resultado.mensagem == Mensagem.MAXIMO_DE_ITERACOES
    assert resultado.iteracoes == 10


def test_funcao_fora_do_dominio_nao_quebra_o_programa():
    resultado = newton(math.log, lambda x: 1 / x, 3.0)

    assert not resultado.convergiu
    assert resultado.mensagem == Mensagem.FORA_DO_DOMINIO


def test_raiz_exata_no_extremo_do_intervalo():
    resultado = bisseccao(lambda x: x - 1, 1, 3)

    assert resultado.raiz == 1
    assert resultado.convergiu


def test_metodo_aberto_que_termina_fora_do_intervalo():
    resultado = newton(lambda x: x**2 - 4, lambda x: 2 * x, -3, intervalo=(0, 5))

    assert not resultado.convergiu
    assert resultado.mensagem == Mensagem.FORA_DO_INTERVALO


@pytest.mark.parametrize("problema", PROBLEMAS, ids=lambda p: p.titulo.split(":")[0])
def test_problemas_do_enunciado_batem_com_a_solucao_analitica(problema):
    parametros = problema.montar_parametros()
    parametros.repeticoes = 1

    for resultado in comparar_metodos(parametros):
        assert resultado.convergiu, resultado.metodo
        assert resultado.raiz == pytest.approx(problema.raiz_de_referencia, abs=1e-5)
