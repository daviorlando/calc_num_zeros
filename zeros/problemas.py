"""Exemplo de teste, Problema 1 e Problema 2 do enunciado.

Cada caso tem os dados iniciais e a raiz analítica, usada para conferir os métodos.
"""

import math
from dataclasses import dataclass

from zeros.entrada import criar_funcao
from zeros.simulador import ParametrosDoCalculo


@dataclass(frozen=True)
class Problema:
    titulo: str
    descricao: str
    funcao: str
    derivada: str
    a: float
    b: float
    x0_newton: float
    x0_secante: float
    x1_secante: float
    raiz_de_referencia: float
    unidade: str = ""

    def montar_parametros(self) -> ParametrosDoCalculo:
        funcao = criar_funcao(self.funcao)
        return ParametrosDoCalculo(
            funcao=funcao,
            derivada=criar_funcao(self.derivada, funcao.variavel),
            a=self.a,
            b=self.b,
            x0_newton=self.x0_newton,
            x0_secante=self.x0_secante,
            x1_secante=self.x1_secante,
        )


EXEMPLO_COSSENO = Problema(
    titulo="Exemplo de teste: cos(x) − x",
    descricao=(
        "f(x) = cos(x) − x aparece em modelos simplificados de equilíbrio entre uma "
        "resposta oscilatória e uma resposta linear. Raiz procurada em [0, 1]; "
        "Newton parte de x₀ = 0,5 e a Secante de x₀ = 0 e x₁ = 1."
    ),
    funcao="cos(x) - x",
    derivada="-sen(x) - 1",
    a=0.0,
    b=1.0,
    x0_newton=0.5,
    x0_secante=0.0,
    x1_secante=1.0,
    raiz_de_referencia=0.7390851332151607,
)

RESFRIAMENTO = Problema(
    titulo="Problema 1: Resfriamento de um componente eletrônico",
    descricao=(
        "Após o desligamento, a temperatura do componente segue T(t) = 20 + 90·e^(−0,15t) "
        "(°C, t em minutos): parte de 110 °C e decai até a temperatura ambiente de 20 °C. "
        "Queremos o instante em que T = 50 °C, isto é, f(t) = 20 + 90·e^(−0,15t) − 50 = 0.\n"
        "Intervalo [0, 20]: f(0) = 60 > 0 e f(20) ≈ −25,5 < 0, e só t ≥ 0 tem sentido físico. "
        "Newton parte de t₀ = 0 (extremo esquerdo) e a Secante usa os extremos 0 e 20.\n"
        "Solução analítica: t = ln(3)/0,15 ≈ 7,324 min."
    ),
    funcao="20 + 90*exp(-0.15*t) - 50",
    derivada="-13.5*exp(-0.15*t)",
    a=0.0,
    b=20.0,
    x0_newton=0.0,
    x0_secante=0.0,
    x1_secante=20.0,
    raiz_de_referencia=math.log(3) / 0.15,
    unidade="min",
)

CAPACITOR_RC = Problema(
    titulo="Problema 2: Carregamento de um capacitor em um circuito RC",
    descricao=(
        "Durante o carregamento, a tensão no capacitor é V(t) = 5(1 − e^(−t)) (V, t em s). "
        "Queremos o instante em que V = 3,8 V: f(t) = 5(1 − e^(−t)) − 3,8 = 0.\n"
        "Intervalo [0, 5]: f(0) = −3,8 < 0 e f(5) ≈ 1,17 > 0 (5 constantes de tempo ≈ carga completa). "
        "Newton parte de t₀ = 0 e a Secante usa os extremos 0 e 5.\n"
        "Relevância: o tempo que um capacitor leva para cruzar um limiar de tensão é a base de "
        "circuitos de temporização (ex.: 555), de atrasos de reset/power-on, de filtros e "
        "debouncing de sensores e da leitura de sensores capacitivos e conversores em sistemas "
        "embarcados, onde o firmware precisa saber quando o sinal estabilizou.\n"
        "Solução analítica: t = ln(5/1,2) ≈ 1,427 s."
    ),
    funcao="5*(1 - exp(-t)) - 3.8",
    derivada="5*exp(-t)",
    a=0.0,
    b=5.0,
    x0_newton=0.0,
    x0_secante=0.0,
    x1_secante=5.0,
    raiz_de_referencia=math.log(5 / 1.2),
    unidade="s",
)

PROBLEMAS = (EXEMPLO_COSSENO, RESFRIAMENTO, CAPACITOR_RC)
