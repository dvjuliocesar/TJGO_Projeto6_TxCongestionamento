# Importando bibliotecas
import pandas as pd
import plotly.express as px

class ProcessosAnalisador:
    def __init__(self, arquivo_csv):
       
        self.df = self._carregar_dados(arquivo_csv)
    
    def _carregar_dados(self, arquivo_csv):
        """
        Carrega o arquivo CSV e realiza o pré-processamento dos dados
        """
        # Ler o CSV
        df = pd.read_csv(arquivo_csv, sep=',', low_memory=False)
        
        # Verificar o nome correto das colunas (pode haver diferenças de acentuação ou espaços)
        colunas = df.columns.tolist()
        
        # Encontrar as colunas de data corretamente
        coluna_serventia = [col for col in colunas if 'serventia' in col.lower()][0]
        coluna_distribuicao = [col for col in colunas if 'data_distribuicao' in col.lower()][0]
        coluna_baixa = [col for col in colunas if 'data_baixa' in col.lower()][0]
        coluna_area_acao = [col for col in colunas if 'nome_area_acao' in col.lower()][0]
        coluna_processo_id = [col for col in colunas if 'processo_id' in col.lower()][0]
        coluna_comarca = [col for col in colunas if 'comarca' in col.lower()][0]
        
        # Renomear colunas para garantir consistência
        df = df.rename(columns={
            coluna_distribuicao: 'data_distribuicao',
            coluna_baixa: 'data_baixa',
            coluna_area_acao: 'nome_area_acao',
            coluna_processo_id: 'processo_id',
            coluna_comarca: 'comarca',
            coluna_serventia: 'serventia'
        })
        
        # Converter colunas de data para datetime com tratamento de erros
        df['data_distribuicao'] = pd.to_datetime(df['data_distribuicao'], errors='coerce')
        df['data_baixa'] = pd.to_datetime(df['data_baixa'], errors='coerce')
        
        return df
    
    def obter_comarcas_disponiveis(self):
        """
        Retorna as comarcas disponíveis
        """
        return sorted(self.df['comarca'].unique())
    
    def obter_anos_disponiveis(self):
        """
        Retorna os anos disponíveis na coluna de data de distribuição
        """
        return sorted(self.df['data_distribuicao'].dt.year.unique())
    
    def calcular_estatisticas(self, comarca, ano_selecionado):
        """
        Calcula as estatísticas por área de ação para o ano selecionado
        """

        # Filtrar pela comarca
        df_comarca = self.df[self.df['comarca'] == comarca]
        
        # Filtrar processos distribuídos no ano selecionado
        df_ano = df_comarca[df_comarca['data_distribuicao'].dt.year == ano_selecionado]
        
        # Agrupar por nome_area_acao
        estatisticas = df_ano.groupby(['nome_area_acao', 'comarca','serventia']).agg(
            Distribuídos=('data_distribuicao', 'count') # Quantidade de datas distribuídas
        ).reset_index()
        
        # Calcular baixados no ano
        baixados_no_ano = df_comarca[
            (df_comarca['data_baixa'].dt.year == ano_selecionado) & 
            (df_comarca['data_baixa'].notna())
        ]
        
        # Agrupar baixados da mesma forma que os distribuídos
        baixados_por_area = baixados_no_ano.groupby(['nome_area_acao', 'comarca','serventia']).size()
        
        # Mesclar corretamente com estatisticas
        estatisticas = estatisticas.merge(
            baixados_por_area.rename('Baixados'), 
            on=['nome_area_acao', 'comarca','serventia'], 
            how='left'
        ).fillna(0)
        
        # Calcular pendentes
        pendentes_por_area = df_ano[df_ano['data_baixa'].isna()].groupby(
            ['nome_area_acao', 'comarca','serventia']
        ).size()
        
        estatisticas = estatisticas.merge(
            pendentes_por_area.rename('Pendentes'), 
            on=['nome_area_acao', 'comarca', 'serventia'], 
            how='left'
        ).fillna(0).astype({'Pendentes': 'int'})
       
        # Calcular taxa de congestionamento no ano
        estatisticas['Taxa de Congestionamento (%)'] = (
            (estatisticas['Pendentes'] / (estatisticas['Pendentes'] + estatisticas['Baixados'])) * 100
        ).round(2)

        # Adicionar linha de totais
        totais = {
            'nome_area_acao': 'TOTAL',
            'comarca': '',
            'serventia':'',
            'Distribuídos': estatisticas['Distribuídos'].sum(),
            'Baixados': estatisticas['Baixados'].sum(),
            'Pendentes': estatisticas['Pendentes'].sum(),
        }

        # Evitar divisão por zero
        if (totais['Pendentes'] + totais['Baixados']) > 0:
            totais['Taxa de Congestionamento (%)'] = round(
                (totais['Pendentes'] / (totais['Pendentes'] + totais['Baixados'])) * 100, 2
            )
        else:
            totais['Taxa de Congestionamento (%)'] = 0.00

        # Adicionar a linha de totais ao DataFrame
        estatisticas = pd.concat([estatisticas, pd.DataFrame([totais])], ignore_index=True)
                
        return estatisticas
    
   # Criar tabela para gráfico
    
    def plotar_graficos(self, comarca_selecionada, ano_selecionado):
            
            # Gera gráficos para os dados filtrados por ano  
        

            # Filtrar dados pela comarca e ano
            df_comarca = self.df[(self.df['comarca'] == comarca_selecionada)]
            df_ano = df_comarca[df_comarca['data_distribuicao'].dt.year == ano_selecionado]

            # Agrupar por nome_area_acao
            estatisticas = df_ano.groupby(['nome_area_acao', 'serventia']).agg(
                Distribuídos=('data_distribuicao', 'count'),  # Quantidade de datas distribuídas
                ).reset_index()

            # Calcular baixados no ano
            baixados_no_ano = df_comarca[
                (df_comarca['data_baixa'].dt.year == ano_selecionado) & 
                (df_comarca['data_baixa'].notna())
            ]
            
            # Agrupar baixados da mesma forma que os distribuídos
            baixados_por_area = baixados_no_ano.groupby(['nome_area_acao', 'serventia']).size()
            
            # Mesclar corretamente com estatisticas
            estatisticas = estatisticas.merge(
                baixados_por_area.rename('Baixados'), 
                on=['nome_area_acao', 'serventia'], 
                how='left'
            ).fillna(0).astype({'Baixados': 'int'})
            
            # Calcular pendentes
            pendentes_por_area = df_ano[df_ano['data_baixa'].isna()].groupby(
                ['nome_area_acao', 'serventia']
            ).size()
        
            estatisticas = estatisticas.merge(
                pendentes_por_area.rename('Pendentes'), 
                on=['nome_area_acao', 'serventia'], 
                how='left'
            ).fillna(0).astype({'Pendentes': 'int'})
            
            # Calcular total de processos Baixados e Pendentes
            estatisticas['Total Baixados'] = estatisticas['Baixados'].sum()
            estatisticas['Total Pendentes'] = estatisticas['Pendentes'].sum()      

            # Calcular taxa de congestionamento
            estatisticas['Taxa de Congestionamento (%)'] = (
                (estatisticas['Total Pendentes'] / (estatisticas['Total Pendentes'] + estatisticas['Total Baixados'])) * 100
                ).round(2)

            #
            fig = px.bar(
                estatisticas,
                x="nome_area_acao",
                y=["Distribuídos", "Baixados", "Pendentes"],
                barmode="group",
                title=f"Comarcas X Taxa de Congestionamento (%) X Área de Ação - {ano_selecionado}",
                labels={"value": "Quantidade", "variable": "Tipo"}
            )

            # Adicionar indicadores
            Distribuidos = estatisticas["Distribuídos"].sum()
            Baixados = estatisticas["Baixados"].sum()
            Pendentes = estatisticas["Pendentes"].sum()
            Taxa_Cong = round(estatisticas["Taxa de Congestionamento (%)"].mean(), 2)

            # Retornar o gráfico para visualização posterior
            return fig, Distribuidos, Baixados, Pendentes, Taxa_Cong
    
    def plotar_graficos_ano(self, ano_selecionado): 

        df_grafico = pd.read_csv('uploads\dados_je_geral_25042025.csv', sep=',', low_memory=False)
        df_grafico = df_grafico[['processo_id','nome_area_acao', 'comarca', 'data_distribuicao', 'data_baixa']]
        df_grafico['data_distribuicao'] = pd.to_datetime(df_grafico['data_distribuicao'], errors='coerce')
        df_grafico['data_baixa'] = pd.to_datetime(df_grafico['data_baixa'], errors='coerce')
        df_grafico['ano_distribuicao'] = df_grafico['data_distribuicao'].dt.year

        # Baixar dados do ano selecionado
        baixados_por_area = df_grafico[
                (df_grafico['data_baixa'].dt.year == ano_selecionado) & 
                (df_grafico['data_baixa'].notna())].groupby(
                ['nome_area_acao', 'comarca']).size()
        
        # Pendentes no ano selecionado
        pendentes_por_area = df_grafico[
                (df_grafico['data_distribuicao'].dt.year == ano_selecionado) & 
                (df_grafico['data_baixa'].isna())].groupby(
                ['nome_area_acao', 'comarca']).size()
        
        # Taxa de congestionamento
        taxa_cong = (pendentes_por_area / (pendentes_por_area + baixados_por_area)) * 100
        taxa_cong = taxa_cong.fillna(0).round(2)
        taxa_cong = taxa_cong.reset_index(name='Taxa de Congestionamento (%)')
        taxa_cong['Taxa de Congestionamento (%)'] = taxa_cong['Taxa de Congestionamento (%)'].astype(float)

        # Taxa de congestionamento para juizados
        taxa_cong = taxa_cong[(taxa_cong['nome_area_acao'].str.contains('civel')) | 
                                       (taxa_cong['nome_area_acao'].str.contains('criminal')) | 
                                       (taxa_cong['nome_area_acao'].str.contains('infancia e juventude civel')) |
                                       (taxa_cong['nome_area_acao'].str.contains('infancia e juventude infracional')) |
                                       (taxa_cong['nome_area_acao'].str.contains('fazenda publica mista')) |
                                       (taxa_cong['nome_area_acao'].str.contains('juizado especial fazenda publica'))]
                                                                                
        # Mapa de cores personalizado (exemplo para 2 comarcas)
        '''color_map = {
            'juizado especial civel': 'darkblue',
            'juizado especial criminal': 'lightblue'    
        }'''
        
        # Adiciona uma coluna com rótulo formatado
        taxa_cong['label_text'] = taxa_cong[
            'Taxa de Congestionamento (%)'].apply(lambda x: f'{x:.2f}%')

        # Gráfico de barras
        fig = px.bar(
            taxa_cong,
            x='comarca',
            y=['Taxa de Congestionamento (%)'],
            color='nome_area_acao',
            barmode='group',
            title=f'Taxa de Congestionamento - {ano_selecionado}',
            labels={'Taxa de Congestionamento (%)': 'Taxa de Congestionamento (%)', 
                    'nome_area_acao': 'Área de Ação'}
            #color_discrete_map=color_map
        )
        
        # Força os rótulos a aparecerem dentro ou fora, conforme necessário
        fig.update_traces(
            textposition='auto',  # Plotly decide o melhor lugar
            textfont=dict(size=12, color='black'),  # você pode ajustar
            insidetextanchor='start'
        )

        fig.update_layout(
            yaxis_title='Taxa de Congestionamento (%)',
            uniformtext_minsize=8,
            uniformtext_mode='show',
            legend_title_text='Área de Ação por Comarca'
        )
        return fig
    