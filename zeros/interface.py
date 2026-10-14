"""Interface de terminal: menus, tabela comparativa e fluxo novo cálculo/sair."""

from dataclasses import replace

from rich.console import Console
from rich.panel import Panel
from rich.markup import escape
from rich.table import Table

from zeros.entrada import (
    Pergunta,
    confirmar,
    ler_derivada,
    ler_funcao,
    ler_inteiro_positivo,
    ler_intervalo,
    ler_numero,
    ler_numero_positivo,
)
from zeros.exportacao import exportar_resultados, linha_da_tabela
from zeros.graficos import exibir_graficos, fechar_graficos, gerar_graficos, pode_exibir_janelas
from zeros.problemas import PROBLEMAS, Problema
from zeros.resultado import Resultado
from zeros.simulador import ParametrosDoCalculo, comparar_metodos

console = Console()

OPCAO_FUNCAO_PERSONALIZADA = "4"
OPCAO_SOBRE_OS_METODOS = "5"
OPCAO_SAIR = "0"
PROBLEMAS_POR_OPCAO = {str(numero): problema for numero, problema in enumerate(PROBLEMAS, start=1)}

ACAO_VER_ITERACOES = "1"
ACAO_GERAR_GRAFICOS = "2"
ACAO_EXPORTAR = "3"
ACAO_NOVO_CALCULO = "4"
ACAO_VOLTAR = "5"

TEXTO_SOBRE_OS_METODOS = """\
[bold]Bissecção[/] — divide [a, b] ao meio e fica com a metade onde f troca de sinal.
  x = (a + b)/2. Convergência linear (o erro cai pela metade a cada passo).
  [green]+[/] sempre converge se f(a)·f(b) < 0.  [red]−[/] lenta; exige o intervalo.

[bold]Falsa Posição[/] — troca o ponto médio pela raiz da reta que liga (a, f(a)) e (b, f(b)).
  x = (a·f(b) − b·f(a)) / (f(b) − f(a)). Convergência linear.
  [green]+[/] garantida como a bissecção e costuma ser mais rápida.
  [red]−[/] em funções muito curvas um extremo fica "preso" e ela fica lenta.

[bold]Newton-Raphson[/] — segue a reta tangente: x_(k+1) = x_k − f(x_k)/f'(x_k).
  Convergência quadrática (dobra os dígitos corretos a cada passo, perto da raiz).
  [green]+[/] muito rápido.  [red]−[/] precisa de f'(x); falha se f'(x) ≈ 0; pode divergir com x₀ ruim.

[bold]Secante[/] — Newton com a derivada trocada pela inclinação entre os dois últimos pontos:
  x_(k+1) = x_k − f(x_k)·(x_k − x_(k−1)) / (f(x_k) − f(x_(k−1))).
  Convergência superlinear (ordem ≈ 1,618).
  [green]+[/] não precisa da derivada.  [red]−[/] pode divergir; falha se f(x_k) = f(x_(k−1)).

[bold]Critério de parada[/] (todos): |x_k − x_(k−1)| < ε  ou  |f(x_k)| < ε, até o máximo de iterações.
Métodos de intervalo (Bissecção, Falsa Posição) são garantidos porém lentos; métodos abertos
(Newton, Secante) são rápidos porém dependem das estimativas iniciais."""


def executar() -> None:
    """Ponto de entrada da aplicação."""
    try:
        _laco_do_menu_principal()
    except (KeyboardInterrupt, EOFError):
        console.print()
    console.print("[bold]Até logo![/]")


def _laco_do_menu_principal() -> None:
    console.print(Panel.fit("[bold]Simulador de Zeros de Funções[/]\n"
                            "Bissecção · Falsa Posição · Newton-Raphson · Secante\n"
                            "Cálculo Numérico — UNIVASF", border_style="cyan"))
    while True:
        opcao = _escolher_no_menu_principal()
        if opcao == OPCAO_SAIR:
            return
        if opcao == OPCAO_SOBRE_OS_METODOS:
            console.print(Panel(TEXTO_SOBRE_OS_METODOS, title="Sobre os métodos", border_style="cyan"))
            continue
        problema = PROBLEMAS_POR_OPCAO.get(opcao)
        parametros = _preparar_problema(problema) if problema else _ler_funcao_personalizada()
        if not _sessao_de_calculo(parametros, problema):
            return


def _escolher_no_menu_principal() -> str:
    console.rule("[bold cyan]Menu principal")
    for numero, problema in PROBLEMAS_POR_OPCAO.items():
        console.print(f"  [cyan]{numero}[/]) {problema.titulo}")
    console.print(f"  [cyan]{OPCAO_FUNCAO_PERSONALIZADA}[/]) Inserir função personalizada")
    console.print(f"  [cyan]{OPCAO_SOBRE_OS_METODOS}[/]) Sobre os métodos")
    console.print(f"  [cyan]{OPCAO_SAIR}[/]) Sair")
    opcoes = [*PROBLEMAS_POR_OPCAO, OPCAO_FUNCAO_PERSONALIZADA, OPCAO_SOBRE_OS_METODOS, OPCAO_SAIR]
    return Pergunta.ask("Escolha uma opção", choices=opcoes, console=console)


# --- Preparação dos dados ---------------------------------------------------

def _preparar_problema(problema: Problema) -> ParametrosDoCalculo:
    console.print(Panel(problema.descricao, title=problema.titulo, border_style="cyan"))
    parametros = problema.montar_parametros()
    _mostrar_parametros(parametros)
    if confirmar("Usar esses dados?", padrao=True):
        return parametros
    return _editar_parametros(parametros)


def _ler_funcao_personalizada() -> ParametrosDoCalculo:
    console.print("[dim]Exemplos: cos(x) - x  |  x^3 - 2x - 5  |  exp(-t) - 0,5  "
                  "(aceita sen, ln, raiz, ^ e vírgula decimal)[/]")
    funcao = ler_funcao()
    derivada = ler_derivada(funcao)
    a, b = ler_intervalo(funcao)
    parametros = ParametrosDoCalculo(funcao=funcao, derivada=derivada, a=a, b=b,
                                     x0_newton=a, x0_secante=a, x1_secante=b)
    return _ler_estimativas_e_criterios(parametros)


def _editar_parametros(parametros: ParametrosDoCalculo) -> ParametrosDoCalculo:
    """Pergunta cada dado de novo, sugerindo o valor atual como padrão (Enter mantém)."""
    if confirmar("Trocar a função?", padrao=False):
        return _ler_funcao_personalizada()
    if confirmar("Trocar a derivada?", padrao=False):
        parametros = replace(parametros, derivada=ler_derivada(parametros.funcao))
    a, b = ler_intervalo(parametros.funcao, padrao=parametros.intervalo)
    return _ler_estimativas_e_criterios(replace(parametros, a=a, b=b))


def _ler_estimativas_e_criterios(p: ParametrosDoCalculo) -> ParametrosDoCalculo:
    x = p.funcao.variavel
    parametros = replace(
        p,
        x0_newton=ler_numero(f"{x}₀ para Newton-Raphson", p.x0_newton),
        x0_secante=ler_numero(f"{x}₀ para a Secante", p.x0_secante),
        x1_secante=ler_numero(f"{x}₁ para a Secante", p.x1_secante),
        epsilon=ler_numero_positivo("Precisão ε", p.epsilon),
        maximo_de_iteracoes=ler_inteiro_positivo("Máximo de iterações", p.maximo_de_iteracoes),
        repeticoes=ler_inteiro_positivo("Repetições para medir o tempo médio", p.repeticoes),
    )
    _mostrar_parametros(parametros)
    return parametros


def _mostrar_parametros(p: ParametrosDoCalculo) -> None:
    x = p.funcao.variavel
    tabela = Table(title="Dados de entrada", show_header=False, title_justify="left")
    tabela.add_column(style="cyan")
    tabela.add_column()
    tabela.add_row(f"f({x})", escape(str(p.funcao)))
    tabela.add_row(f"f'({x})", escape(str(p.derivada)))
    tabela.add_row("Intervalo \\[a, b]", f"[{p.a:g}, {p.b:g}]")
    tabela.add_row(f"Newton: {x}₀", f"{p.x0_newton:g}")
    tabela.add_row(f"Secante: {x}₀, {x}₁", f"{p.x0_secante:g}, {p.x1_secante:g}")
    tabela.add_row("Precisão ε", f"{p.epsilon:g}")
    tabela.add_row("Máx. iterações", str(p.maximo_de_iteracoes))
    tabela.add_row("Tempo", f"média de {p.repeticoes} execuções")
    console.print(tabela)


# --- Resultados -------------------------------------------------------------

def _sessao_de_calculo(parametros: ParametrosDoCalculo, problema: Problema | None) -> bool:
    """Calcula e oferece as ações sobre o resultado. Devolve False se o usuário quiser sair."""
    while True:
        with console.status("Executando os quatro métodos..."):
            resultados = comparar_metodos(parametros)
        _mostrar_tabela_comparativa(resultados, parametros, problema)
        acao = _laco_de_acoes(resultados, parametros, problema)
        if acao == ACAO_NOVO_CALCULO:
            parametros = _editar_parametros(parametros)
            continue
        return acao == ACAO_VOLTAR


def _laco_de_acoes(resultados: list[Resultado], parametros: ParametrosDoCalculo,
                   problema: Problema | None) -> str:
    titulo = problema.titulo if problema else f"f({parametros.funcao.variavel}) = {parametros.funcao}"
    while True:
        acao = _escolher_acao()
        if acao == ACAO_VER_ITERACOES:
            _mostrar_iteracoes(_escolher_metodo(resultados))
        elif acao == ACAO_GERAR_GRAFICOS:
            _gerar_graficos(resultados, parametros, titulo)
        elif acao == ACAO_EXPORTAR:
            _exportar(resultados, titulo)
        else:
            return acao


def _escolher_acao() -> str:
    console.rule("[bold cyan]O que deseja fazer?")
    console.print(f"  [cyan]{ACAO_VER_ITERACOES}[/]) Ver as iterações de um método")
    console.print(f"  [cyan]{ACAO_GERAR_GRAFICOS}[/]) Gerar gráficos")
    console.print(f"  [cyan]{ACAO_EXPORTAR}[/]) Exportar resultados (CSV e Markdown)")
    console.print(f"  [cyan]{ACAO_NOVO_CALCULO}[/]) Novo cálculo (alterar os dados)")
    console.print(f"  [cyan]{ACAO_VOLTAR}[/]) Voltar ao menu principal")
    console.print(f"  [cyan]{OPCAO_SAIR}[/]) Sair")
    opcoes = [ACAO_VER_ITERACOES, ACAO_GERAR_GRAFICOS, ACAO_EXPORTAR, ACAO_NOVO_CALCULO, ACAO_VOLTAR, OPCAO_SAIR]
    return Pergunta.ask("Escolha uma opção", choices=opcoes, console=console)


def _mostrar_tabela_comparativa(resultados: list[Resultado], parametros: ParametrosDoCalculo,
                                problema: Problema | None) -> None:
    """Verde: menos iterações e menor tempo entre os que convergiram. Linhas em vermelho: falhas."""
    convergiram = [r for r in resultados if r.convergiu]
    menos_iteracoes = min((r.iteracoes for r in convergiram), default=None)
    menor_tempo = min((r.tempo_ms for r in convergiram), default=None)
    referencia = problema.raiz_de_referencia if problema else None

    tabela = Table(title=f"Comparativo dos métodos — f({parametros.funcao.variavel}) = {escape(str(parametros.funcao))}",
                   title_justify="left")
    for coluna in ("Método", "Raiz", "Iterações", "Tempo (µs)", "|f(raiz)|"):
        tabela.add_column(coluna, justify="left" if coluna == "Método" else "right")
    if referencia is not None:
        tabela.add_column("|raiz − ref.|", justify="right")

    for resultado in resultados:
        metodo, raiz, iteracoes, tempo, residuo = linha_da_tabela(resultado)
        if resultado.convergiu and resultado.iteracoes == menos_iteracoes:
            iteracoes = f"[bold green]{iteracoes}[/]"
        if resultado.convergiu and resultado.tempo_ms == menor_tempo:
            tempo = f"[bold green]{tempo}[/]"
        celulas = [metodo, raiz, iteracoes, tempo, residuo]
        if referencia is not None:
            celulas.append(_distancia_da_referencia(resultado, referencia))
        tabela.add_row(*celulas, style=None if resultado.convergiu else "red")

    console.print(tabela)
    _mostrar_falhas(resultados)
    if referencia is not None:
        console.print(f"Raiz de referência (analítica): [cyan]{referencia:.10f}[/] {problema.unidade}")
    console.print("[dim]Em verde: menos iterações e menor tempo médio entre os métodos que convergiram.[/]")


def _mostrar_falhas(resultados: list[Resultado]) -> None:
    for resultado in resultados:
        if not resultado.convergiu:
            console.print(f"[bold red]{resultado.metodo} falhou:[/] {resultado.mensagem}")


def _distancia_da_referencia(resultado: Resultado, referencia: float) -> str:
    return "—" if resultado.raiz is None else f"{abs(resultado.raiz - referencia):.3e}"


def _escolher_metodo(resultados: list[Resultado]) -> Resultado:
    for numero, resultado in enumerate(resultados, start=1):
        console.print(f"  [cyan]{numero}[/]) {resultado.metodo}")
    escolha = Pergunta.ask("Qual método?", choices=[str(n) for n in range(1, len(resultados) + 1)],
                         console=console)
    return resultados[int(escolha) - 1]


def _mostrar_iteracoes(resultado: Resultado) -> None:
    if not resultado.historico:
        console.print(f"[red]{resultado.metodo} não chegou a iterar: {resultado.mensagem}.[/]")
        return
    tabela = Table(title=f"Iterações — {resultado.metodo} ({resultado.mensagem})", title_justify="left")
    for coluna in ("k", "x_k", "f(x_k)", "|x_k − x_(k−1)|"):
        tabela.add_column(coluna, justify="right")
    for passo in resultado.historico:
        erro = "—" if passo.erro is None else f"{passo.erro:.3e}"
        tabela.add_row(str(passo.numero), f"{passo.aproximacao:.10f}", f"{passo.valor_da_funcao:.3e}", erro)
    console.print(tabela)


def _gerar_graficos(resultados: list[Resultado], parametros: ParametrosDoCalculo, titulo: str) -> None:
    caminhos = gerar_graficos(parametros.funcao, resultados, parametros.intervalo, titulo, parametros.epsilon)
    for caminho in caminhos:
        console.print(f"  Gráfico salvo em [cyan]{caminho}[/]")
    if pode_exibir_janelas() and confirmar("Abrir os gráficos agora? (feche as janelas para continuar)"):
        exibir_graficos()
    else:
        fechar_graficos()


def _exportar(resultados: list[Resultado], titulo: str) -> None:
    for caminho in exportar_resultados(resultados, titulo):
        console.print(f"  Resultados salvos em [cyan]{caminho}[/]")
