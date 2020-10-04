from iqoptionapi.stable_api import IQ_Option
import time
import json, requests
import logging
import configparser
from datetime import datetime
from dateutil import tz
import threading
from datetime import date
import sys
import os
from colorama import init, Fore, Back
from firebase import firebase

""" logging.disable(level=(logging.DEBUG)) """

def Config():
    arquivo = configparser.RawConfigParser()
    arquivo.read('config.txt')
    return arquivo

def Conexao():

    # Responsavel por fazer a primeira conexao
    API.connect()

    if tipo_conta == 'real':
        # Responsavel por alterar o modo da conta entre TREINAMENTO e REAL
        API.change_balance('REAL')  # PRACTICE / REAL
    else:
        API.change_balance('PRACTICE')

    # Looping para realizar a verificação se a API se conectou corretamente ou se deve tentar se conectar novamente
    while True:
        if API.check_connect() == False:
            print('Erro ao se conectar')
        # No video é apresentado a função reconnect(), mas nas versão mais novas da API ela não está mais disponivel, sendo assim deve ser utilizado API.connect() para realizar a conexão novamente
            API.connect()
        else:
            frase = "OLÁ, SOU D.BOT E ESTOU INICIANDO A ANÁLISE DO MERCADO, QUANDO TIVER OPORTUNIDADE IREI EFETUAR OPERAÇÕES COM ESSAS CONFIGURAÇÕES: "
            for i in list(frase):
                print(i, end='')
                sys.stdout.flush()
                time.sleep(0.05)
            os.system('cls')
            break

def perfil():
    perfil = json.loads(json.dumps(API.get_profile_ansyc()))

    return perfil

def timestamp_converter(x):
    hora = datetime.strptime(datetime.utcfromtimestamp(
        x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]

def payout(par, tipo, timeframe=1):
    if tipo == 'turbo':
        a = API.get_all_profit()
        return int(100 * a[par]['turbo'])

def carregar_sinais():
    arquivo = str(firebase.get('/sinais/1', ''))
    return arquivo

def moedas_abertas():
    while True:
        par = API.get_all_open_time()
        abertas.clear()
        for paridade in par['turbo']:
            if par['turbo'][paridade]['open'] == True:
                payouts = payout(paridade, 'turbo')
                if payouts >= payoutMinimo:
                    abertas.append(paridade)
            continue
        time.sleep(1200)
        continue
        
def titulo():
    print('-'*119)
    print(Fore.GREEN + '                                      /$$$$$$$           /$$$$$$$   /$$$$$$  /$$$$$$$$')
    print(Fore.GREEN + '                                     | $$__  $$         | $$__  $$ /$$__  $$|__  $$__/')
    print(Fore.GREEN + '                                     | $$  \ $$         | $$  \ $$| $$  \ $$   | $$   ')
    print(Fore.GREEN + '                                     | $$  | $$         | $$$$$$$ | $$  | $$   | $$   ')
    print(Fore.GREEN + '                                     | $$  | $$         | $$__  $$| $$  | $$   | $$   ')
    print(Fore.GREEN + '                                     | $$  | $$         | $$  \ $$| $$  | $$   | $$   ')
    print(Fore.GREEN + '                                     | $$$$$$$//$$      | $$$$$$$/|  $$$$$$/   | $$   ')
    print(Fore.GREEN + '                                     |_______/|__/      |_______/  \______/    |__/   ')
    print('-'*119)

def dados_do_trader():
    print('\n')
    print(Fore.YELLOW + '---> DADOS DO TRADER')
    print('     TRADER:', dados_conta['name'])
    print('     TIPO DE CONTA:', tipo_conta)
    print('     BANCA INICIAL:', dados_conta['currency_char'], banca)
    print(Fore.YELLOW + '---> DADOS DE TRADING')
    print('     VALOR DAS OPERAÇÕES:',
          dados_conta['currency_char'], valorOperacao)
    print('     QUANTIDADE MARTINGALE:', quantidadeMg)
    print('     FATOR DE MULTIPLICAÇÃO GALE:', 'X'+str(fatorMartingale))
    print('     PAYOUT MÍNIMO:', str(payoutMinimo),'%')
    print('     ANÁLISE DE TENDÊNCIA:', str(ativa_tendencia))
    print(Fore.YELLOW + '---> GERENCIAMENTO')
    print('     SOROS:', soros)
    print('     NÍVEL DE SOROS:',quantidadeSoros)
    print('     STOP WIN:', dados_conta['currency_char'], takeProfit)
    print('     STOP LOSS:', dados_conta['currency_char'], stopLoss)
    print('-'*50, '\n')

    resposta = input('OS DADOS ESTÃO CORRETOS? (s) ou (n): ')
    if resposta == 's' or 'S':
        arquivoLOG = open('Log de operações/'+data_em_texto +
                      '.txt', 'a', encoding='utf8')
        arquivoLOG.write('\n---> DADOS DO TRADER')
        arquivoLOG.write('\n     TRADER:'+str(dados_conta['name']))
        arquivoLOG.write('\n     TIPO DE CONTA:'+str(tipo_conta))
        arquivoLOG.write('\n     BANCA INICIAL:' +
                     str(dados_conta['currency_char']+str(banca)))
        arquivoLOG.write('\n---> DADOS DE TRADING')
        arquivoLOG.write('\n     VALOR DAS OPERAÇÕES:' +
                     str(dados_conta['currency_char']+str(valorOperacao)))
        arquivoLOG.write('\n     QUANTIDADE MARTINGALE:'+str(quantidadeMg))
        arquivoLOG.write('\n     FATOR DE MULTIPLICAÇÃO GALE:' +
                     str('X'+str(fatorMartingale)))
        arquivoLOG.write('\n     PAYOUT MÍNIMO:'+str(payoutMinimo)+'%')
        arquivoLOG.write('\n     ANÁLISE DE TENDÊNCIA:'+str(ativa_tendencia))
        arquivoLOG.write('\n---> GERENCIAMENTO')
        arquivoLOG.write('\n     SOROS:' +
                     str(soros))
        arquivoLOG.write('\n     NIVEL DE SOROS:' +
                     str(quantidadeSoros))
        arquivoLOG.write('\n     STOP WIN:' +
                     str(dados_conta['currency_char']+str(takeProfit)))
        arquivoLOG.write('\n     STOP LOSS:' +
                     str(dados_conta['currency_char']+str(stopLoss)))
        arquivoLOG.write('\n')                
        arquivoLOG.write('-'*50)
        arquivoLOG.write('\n---> INICIANDO OPERAÇÕES')
        arquivoLOG.close()
    else:
        sys.exit()

def stop():
    lucro_float=round(lucro, 2)
    if lucro <= float('-' + str(abs(stopLoss))):
        print(Fore.RED+'\n---> STOP LOSS BATIDO!'+' | PREJUÍZO:' +
              str(dados_conta['currency_char'])+' '+str(lucro_float)+' :(')
        print(Fore.YELLOW + '---> RESPEITE SEU GERENCIAMENTO!')
        arquivoLOG = open('Log de operações/'+data_em_texto +
                      '.txt', 'a', encoding='utf8')
        arquivoLOG.write('\n---> STOP LOSS BATIDO!'+' | PREJUÍZO:' +
                     str(dados_conta['currency_char'])+' '+str(lucro_float)+' :(')
        arquivoLOG.close()
    if lucro >= float(abs(takeProfit)):
        print(Fore.GREEN + '\n---> STOP WIN BATIDO!'+' | LUCRO:' +
              str(dados_conta['currency_char'])+' '+str(lucro_float)+' :)')
        print(Fore.YELLOW + '---> RESPEITE SEU GERENCIAMENTO!')
        arquivoLOG = open('Log de operações/'+data_em_texto +
                      '.txt', 'a', encoding='utf8')
        arquivoLOG.write('\n---> STOP WIN BATIDO!'+' | LUCRO:' +
                     str(dados_conta['currency_char'])+' '+str(lucro_float)+' :)')
        arquivoLOG.close()

def noticias():
    for noticia in objeto['result']:

        # Separa a paridade em duas Ex: AUDUSD separa AUD e USD para comparar os dois
        paridade1 = moeda[0:3]
        paridade2 = moeda[3:6]

        horaAgora = datetime.now()
        tm = tz.gettz('America/Sao Paulo')
        hora_atual = horaAgora.astimezone(tm)
        AgoraHora = hora_atual.strftime('%H:%M:%S')

        # Pega a paridade, impacto e separa a data da hora da API
        tipoNoticia = noticia['economy']
        impacto = noticia['impact']
        atual = noticia['data']
        nome = noticia['name']
        data = atual.split(' ')[0]
        hora = atual.split(' ')[1]

        # Verifica se a paridade existe da noticia e se está na data atual
        if tipoNoticia == paridade1 or tipoNoticia == paridade2 and data == data_atual:
          formato = '%H:%M:%S'
          dif = (datetime.strptime(hora, formato) - datetime.strptime(AgoraHora, formato)).total_seconds()
          # Verifica a diferença entre a hora da noticia e a hora da operação
          minutesDiff = dif / 60

          # Verifica se a noticia irá acontencer 30 min antes ou depois da operação
          if minutesDiff >= -30 and minutesDiff <= 0 or minutesDiff <= 30 and minutesDiff >= 0:
            return True
            break

def operacao():
    while True:
            valor = valorOperacao
            status, id = API.buy(valor, moeda, direcao, timeframe)
            if status:
                print(Fore.YELLOW + '---> OPERAÇÃO:')
                print('     ATIVO:', moeda, '| DIREÇÃO:', direcao, '| EXPIRAÇÃO:',timeframe, 'M', '| VALOR:', dados_conta['currency_char'], round(valor,3))

                arquivoLOG = open('Log de operações/' +data_em_texto+'.txt', 'a', encoding='utf8')
                arquivoLOG.write('\n---> OPERAÇÃO:')
                arquivoLOG.write('\n     ATIVO:'+str(moeda)+ '| DIREÇÃO:' + str(direcao) + '| EXPIRAÇÃO:'+str(timeframe)+ 'M' + '| VALOR:'+str(dados_conta['currency_char'])+str(round(valor,3)))
                arquivoLOG.close()

                resultado = round(API.check_win_v3(id), 3)
                if resultado > 0:
                    print('     RESULTADO: WIN    |', Fore.GREEN + 'LUCRO:' +str(dados_conta['currency_char'])+' '+str(resultado) + ' :)')
                    print('\n')
                    print('-'*50)
                    print('\n')
                    arquivoLOG = open('Log de operações/' +data_em_texto+'.txt', 'a', encoding='utf8')
                    arquivoLOG.write('     RESULTADO: WIN    |'+'LUCRO:'+str(dados_conta['currency_char'])+' '+str(resultado)+' :)')
                    arquivoLOG.write('\n')
                    arquivoLOG.write('-'*50)
                    arquivoLOG.write('\n')
                    arquivoLOG.close()
                    break
                elif resultado==0:
                    print('     RESULTADO: DOJI    |', 'LUCRO:' +
                          str(dados_conta['currency_char'])+' '+str(resultado) + ' :|')
                    print('\n')
                    print('-'*50)
                    print('\n')
                    arquivoLOG = open('Log de operações/' +data_em_texto+'.txt', 'a', encoding='utf8')
                    arquivoLOG.write('     RESULTADO: DOJI    |'+'LUCRO:'+str(dados_conta['currency_char'])+' '+str(resultado)+' :|')
                    arquivoLOG.write('\n')
                    arquivoLOG.write('-'*50)
                    arquivoLOG.write('\n')
                    arquivoLOG.close()
                    break
                else:
                    print('     RESULTADO: LOSS   |', Fore.RED + 'PREJUÍZO:' +
                          str(dados_conta['currency_char'])+' '+str(resultado) + ' :(')
                    print('\n')
                    arquivoLOG = open('Log de operações/' +data_em_texto+'.txt', 'a', encoding='utf8')
                    arquivoLOG.write('     RESULTADO: LOSS   |'+'PREJUÍZO:'+str(dados_conta['currency_char'])+' '+str(resultado)+' :(')
                    arquivoLOG.write('\n')
                    arquivoLOG.write('-'*50)
                    arquivoLOG.write('\n')
                    arquivoLOG.close()
                    if quantidadeMg > martingale:
                        print(Fore.YELLOW + '---> MARTINGALE:\n')
                        arquivoLOG = open('Log de operações/' +data_em_texto+'.txt', 'a', encoding='utf8')
                        arquivoLOG.write('---> MARTINGALE:\n')
                        arquivoLOG.close()
                        valor = valor * fatorMartingale
                        martingale += 1
                        continue
                    print('-'*50)
                    break
            else:
                print('ENCONTREI UMA OPORTUNIDADE, MAS A QUERIDA CORRETORA BLOQUEOU A MINHA ENTRADA')
            break

init(convert=True, autoreset=True)

titulo()

data_atual = date.today()
data_em_texto = data_atual.strftime('%d%m%Y')
arquivoLOG = open('log de operações/'+data_em_texto+'.txt', 'w')
arquivoLOG.close()

arquivo = Config()
email = arquivo.get('USERS', 'email')
senha = arquivo.get('USERS', 'senha')
tipo_conta = str(arquivo.get('USERS', 'conta'))
valorOperacao = float(arquivo.get('TRADE', 'valorOperacao'))
quantidadeMg = int(arquivo.get('TRADE', 'quantidadeMg'))
fatorMartingale = float(arquivo.get('TRADE', 'fatorMartingale'))
payoutMinimo = int(arquivo.get('TRADE', 'payout'))
ativa_tendencia = str(arquivo.get('TRADE', 'ligar_tendencia'))
soros = str(arquivo.get('GERENCIAMENTO', 'soros'))
quantidadeSoros = int(arquivo.get('GERENCIAMENTO', 'quantidadeSoros'))
takeProfit = float(arquivo.get('GERENCIAMENTO', 'takeProfit'))
stopLoss = float('-' + str((arquivo.get('GERENCIAMENTO', 'stopLoss'))))

API = IQ_Option(email, senha)
Conexao()
firebase = firebase.FirebaseApplication('https://dtraders-86997.firebaseio.com/', None)
titulo()
dados_conta = perfil()
banca = API.get_balance()
dados_do_trader()
sinalinicio = carregar_sinais()
lucro = 0
sorosAplicados = 0
abertas = []
# Recebe o link da API de notícias
response = requests.get("https://botpro.com.br/calendario-economico/")
texto = response.content
objeto = json.loads(texto)
# Verifica se o status code é 200 de sucesso
if response.status_code != 200 or objeto['success'] != True:
  print('Erro ao verificar notícias')
# Pega a data atual
data = datetime.now()
tm = tz.gettz('America/Sao Paulo')
data_atual = data.astimezone(tm)
data_atual = data_atual.strftime('%Y-%m-%d')
threading.Thread(target=moedas_abertas).start() 

print(Fore.YELLOW + '\n---> AGUARDANDO OPORTUNIDADE')
print('\n')
while lucro >= stopLoss and lucro <= takeProfit:
    sinal = carregar_sinais()
    if sinalinicio != sinal:
        dados = sinal.split(';')
        moeda = str(dados[0])
        direcao = str(dados[1])
        timeframe = int(dados[2])
        horario = str(dados[3])
        sinalinicio = sinal
        martingale = 0
        if moeda in abertas:
            operacao()
            
        """resultadoNoticia = noticias()
        if resultadoNoticia != True:
            if ativa_tendencia=="sim":
                velas = API.get_candles(moeda, (int(timeframe) * 60), 60,  time.time())
                ultimo = round(velas[0]['close'], 4)
                primeiro = round(velas[-1]['close'], 4)
                diferenca = abs( round( ( (ultimo - primeiro) / primeiro ) * 100, 3) )
                tendencia = "CALL" if ultimo < primeiro and diferenca > 0.01 else "PUT" if ultimo > primeiro and diferenca > 0.01 else False
            else:
                tendencia = "nao"
            if tendencia == direcao or tendencia == "nao": """
    

stop()
time.sleep(86400)
# calculo %
#valorEntrada = (valorOperacao/100) * banca
#valorTakeProfit = (takeprofit/100) * banca
#valorStopLoss = (stopLoss/100) * banca