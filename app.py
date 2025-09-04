from flask import Flask, request, render_template, Response, session
from util import ProcessosAnalisador  # Certifique-se de que a classe está no arquivo correto
import pandas as pd
import io

app = Flask(__name__, template_folder='templates', static_folder='static')

app.secret_key = '125blablabla'

filepath = 'uploads/dados_je_geral_25042025.csv'  # Caminho para o arquivo CSV

# Inicializa a classe ProcessosAnalisador com o arquivo CSV
analisador = ProcessosAnalisador(filepath)

@app.route('/')
def tabela():

    # Pega o parâmetro de filtro da URL
    filtro_comarca = request.args.get('comarca', 'GOIÁS')
    filtro_ano = request.args.get('ano', '2020')

    # Verifica se o filtro de ano está vazio ou é inválido
    if filtro_ano == '' or not filtro_ano.isdigit():
        filtro_ano = '2020'  # Se vazio ou inválido, força o valor padrão '2020'

    # Converte filtro_ano para inteiro
    filtro_ano = int(filtro_ano)

    session['args']=[filtro_comarca,filtro_ano]

    comarcas = analisador.obter_comarcas_disponiveis()
    anos = analisador.obter_anos_disponiveis()
    anos = [str(ano) for ano in anos]


    estatisticas = analisador.calcular_estatisticas(filtro_comarca, filtro_ano)

    # Agrupa os dados por área de ação e calcula as estatísticas
    estatisticas_df = pd.DataFrame(estatisticas)
    estatisticas_df = estatisticas_df.rename(
        columns={
            "nome_area_acao":"Área de Ação",
            "comarca":"Comarca",
            "serventia":"Serventia"
    })
    print(estatisticas_df)

    # Reorganiza as colunas para exibição
    estatisticas_df = estatisticas_df[
        ["Área de Ação", 
         "Comarca", 
         "Serventia",
         "Distribuídos", 
         "Baixados",
         "Pendentes", 
         "Taxa de Congestionamento (%)"
    ]]
    
    # Converte o DataFrame filtrado e com as estatísticas em HTML para exibição no dashboard
    tabela_html = estatisticas_df.to_html(classes='table table-bordered')

    return render_template('base.html', 
                           tabela_html=tabela_html, comarcas=comarcas, anos=anos)

@app.route('/grafico')
def grafico():

    # Pega o parâmetro de filtro da URL
    filtro_ano = request.args.get('ano', '2020')

    # Verifica se o filtro de ano está vazio ou é inválido
    if filtro_ano == '' or not filtro_ano.isdigit():
        filtro_ano = '2020'  # Se vazio ou inválido, força o valor padrão '2020'

    # Converte filtro_ano para inteiro
    filtro_ano = int(filtro_ano)

    anos = analisador.obter_anos_disponiveis()
    anos = [str(ano) for ano in anos]

    # Gráfico
    fig = analisador.plotar_graficos_ano(filtro_ano)
    fig.update_layout(
        title= None,
        xaxis_title='Comarca',
        yaxis_title='Taxa de Congestionamento (%)',
        legend_title='Área de Ação'
    )
    
    figura_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

   
    return render_template('grafico.html',
                           figura_html=figura_html, anos=anos)

@app.route('/download')
def download():

    filtro_comarca, filtro_ano = session.get('args', ['GOIÁS', '2020'])

    estatisticas = analisador.calcular_estatisticas(filtro_comarca, filtro_ano)

    # Agrupa os dados por área de ação e calcula as estatísticas
    estatisticas_df = pd.DataFrame(estatisticas)
    estatisticas_df = estatisticas_df.rename(columns={
        "nome_area_acao":"Área de Ação", 
        "serventia":"Serventia"
    })
    
    # Converte o DataFrame para CSV em memória
    output = io.StringIO()
    estatisticas_df.to_csv(output, index=False)
    output.seek(0)
    
    # Cria uma resposta HTTP para download
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=tabela_estatistica_{filtro_comarca}_{filtro_ano}.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)