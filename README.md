# Simulador de Zeros de Funções

Projeto 2 de Cálculo Numérico (UNIVASF, 2026.2). Compara **Bissecção**, **Falsa Posição**,
**Newton-Raphson** e **Secante** na mesma função, medindo raiz, iterações, tempo médio (µs)
e |f(raiz)|.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

```bash
python main.py                   # simulador interativo
python -m pytest tests/          # testes automáticos
```

Menu principal:

```
1) Exemplo de teste: cos(x) − x
2) Problema 1: Resfriamento de um componente eletrônico
3) Problema 2: Carregamento de um capacitor em um circuito RC
4) Inserir função personalizada
5) Sobre os métodos
0) Sair
```

Depois do cálculo é possível ver a tabela de iterações de cada método, gerar gráficos
(salvos em `graficos/`), exportar a tabela em CSV/Markdown (`resultados/`), refazer o
cálculo com outros dados, voltar ao menu ou sair.

### Como digitar a função

- `cos(x) - x`, `20 + 90*exp(-0.15*t) - 50`, `5*(1 - exp(-t)) - 3.8`
- `^` vale como potência (`x^3 - 2x - 5`), multiplicação implícita (`2x`) e vírgula decimal (`0,5`)
- Nomes em português: `sen`, `tg`, `ln`, `raiz`; constantes `e` e `pi`
- A variável pode ser `x`, `t` ou qualquer outra letra (uma só)
- A derivada pode ser digitada ou calculada automaticamente (Enter vazio)
- Campos numéricos aceitam expressões: `pi/2`, `ln(3)/0,15`, `1e-6`

## Critérios adotados

- Parada: |x_k − x_(k−1)| < ε **ou** |f(x_k)| < ε, limitado ao máximo de iterações
  (padrões: ε = 10⁻⁶, 100 iterações — iguais para os quatro métodos).
- Tempo: média de N execuções (padrão 1000) medida com `time.perf_counter_ns`.
- Falhas não interrompem o programa; aparecem em vermelho abaixo da tabela comparativa: sem mudança de sinal,
  derivada nula, divisão por zero, máx. iterações, overflow/NaN, fora do domínio de f,
  saiu do intervalo, ou "OK (extrapolou o intervalo)" quando um método aberto passou
  por pontos fora de [a, b] mas terminou dentro dele.

## Organização do código

```
main.py                ponto de entrada
zeros/resultado.py     Resultado, Iteracao e Mensagem (contrato comum)
zeros/metodos.py       os quatro métodos + laço comum de iteração
zeros/entrada.py       interpretação de f(x) com sympy e leitura validada dos dados
zeros/problemas.py     exemplo de teste, Problema 1 e Problema 2
zeros/simulador.py     roda os quatro métodos e calcula o tempo médio
zeros/interface.py     menus e tabelas (rich)
zeros/graficos.py      f(x) com as raízes e gráfico de convergência (matplotlib)
zeros/exportacao.py    exportação CSV/Markdown
tests/                 testes com pytest
```
