from iqoptionapi.stable_api import IQ_Option
import time
import requests
import logging
import configparser
import json
import os
import sys
import socket
from datetime import datetime, date, timedelta
from dateutil import tz
import threading
from colorama import init, Fore, Back
from firebase import firebase
from random import randint
import pyrebase

init(convert=True, autoreset=True)
logging.disable(level=(logging.DEBUG))


global trava
trava = True
abertas = []


def titulo():
    linha()
    print(Fore.GREEN + '                                      /$$$$$$$           /$$$$$$$   /$$$$$$  /$$$$$$$$')
    print(Fore.GREEN + '                                     | $$__  $$         | $$__  $$ /$$__  $$|__  $$__/')
    print(Fore.GREEN + '                                     | $$  \ $$         | $$  \ $$| $$  \ $$   | $$   ')
    print(Fore.GREEN + '                                     | $$  | $$         | $$$$$$$ | $$  | $$   | $$   ')
    print(Fore.GREEN + '                                     | $$  | $$         | $$__  $$| $$  | $$   | $$   ')
    print(Fore.GREEN + '                                     | $$  | $$         | $$  \ $$| $$  | $$   | $$   ')
    print(Fore.GREEN + '                                     | $$$$$$$//$$      | $$$$$$$/|  $$$$$$/   | $$   ')
    print(Fore.GREEN + '                                     |_______/|__/      |_______/  \______/    |__/   ')
    linha()


def linha():
    print('-' * 119)


titulo()


def sair_sistema(msg='    Por favor, verifique as configuracoes de TRADE'):
    global trava
    print(msg)
    trava = False
    input('\n    Pressione qualquer tecla para encerrar o sistema... \n ')
    sys.exit()


def timestamp_converter(x, retorno=1):
    hora = datetime.strptime(datetime.utcfromtimestamp(
        x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))
    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6] if retorno == 1 else hora.astimezone(tz.gettz('America/Sao Paulo'))


def converterTimestamp(x, y):
    mintime1 = timedelta(milliseconds=x)
    mintime2 = timedelta(milliseconds=y)
    min1 = mintime1.seconds
    min2 = mintime2.seconds

    exptime = min2 - min1
    expminutes = (exptime % 3600) // 60
    if expminutes == 0:
        expminutes = 1
    return expminutes


def verificacaoConectDB():
    global confiaveis
    global dadoDB1
    mensagemConnectDB = True
    while True:
        for host in confiaveis:
            a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            a.settimeout(.5)
            try:
                b = a.connect_ex((host, 80))
                if b == 0:  # ok, conectado
                    if mensagemConnectDB == False:
                        dadoDB1 = db.child("sinais/1").stream(ouvirOperacao)
                        print(
                            Fore.GREEN+'---> CONECTADO AO BANCO DE DADOS COM SUCESSO!\n')
                        mensagemConnectDB = True
            except:
                pass
                if mensagemConnectDB == True:
                    dadoDB1.close()
                    print(
                        Fore.YELLOW+'\nPERDA DE CONEXAO COM O BANCO DE DADOS, VERIFIQUE SUA INTERNET OU UM POSSIVEL BLOQUEIO DO ANTIVIRUS')
                    print(Fore.YELLOW+'---> TENTANDO RECONECTAR...\n')
                    mensagemConnectDB = False
            a.close()


def verificacaoConect():
    mensagemConnect = True
    while True:
        if API.check_connect() == False:
            if mensagemConnect == True:
                print(Fore.YELLOW +
                      '\nPERDA DE CONEXAO COM A IQ OPTION, VERIFIQUE SUA INTERNET OU UM POSSIVEL BLOQUEIO DO ANTIVIRUS')
                print(Fore.YELLOW+'---> TENTANDO RECONECTAR...\n')
                mensagemConnect = False
            API.connect()
        else:
            if mensagemConnect == False:
                print(Fore.GREEN+'---> CONECTADO A IQ OPTION COM SUCESSO!\n')
                mensagemConnect = True


try:
    file = open('setup.conf')
except IOError:
    sair_sistema(
        '    Ocorreu um erro, voce deve definir as configuracoes no Configurador primeiro')


arquivo = configparser.RawConfigParser()
arquivo.read('setup.conf')

try:
    email = arquivo.get('USER', 'email')
    senha = arquivo.get('USER', 'senha')
    error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""
    tipo_conta = arquivo.get('TRADE', 'tipo_conta').lower()
    global amount
    amount = float(arquivo.get('TRADE', 'preco_operacao'))
    porc_preco = arquivo.getboolean('TRADE', 'porc_preco')
    quantidadeMg = int(arquivo.get('TRADE', 'quantidadeMg'))
    fatorMartingale = float(arquivo.get('TRADE', 'fatorMartingale'))
    payoutMinimo = int(arquivo.get('TRADE', 'payout'))
    soros = str(arquivo.get('TRADE', 'soros'))
    quantidadeSoros = int(arquivo.get('TRADE', 'quantidadeSoros'))
    take_profit = arquivo.get('GERENCIAMENTO', 'take_profit')
    if take_profit == '0' or take_profit == '':
        take_profit = 100000
    else:
        take_profit = float(take_profit)
    take_loss = arquivo.get('GERENCIAMENTO', 'stop_loss')
    if take_loss == '0' or take_loss == '':
        take_loss = 100000
    else:
        take_loss = float(take_loss)
    porcentagem = arquivo.getboolean('GERENCIAMENTO', 'porcentagem')

except ValueError:
    sair_sistema('    Inconsistencia nas configuracoes especificadas, \n    voce nao pode deixar campos em branco ou usar virgula em numero decimal!\n Assista todos os videos de configuracao para nao ter nenhuma duvida!')

API = IQ_Option(email, senha)
check, reason = API.connect()

if check:
    frase = "OLÁ, SOU D.BOT E ESTOU INICIANDO A ANÁLISE DO MERCADO, QUANDO TIVER OPORTUNIDADE IREI EFETUAR OPERAÇÕES COM ESSAS CONFIGURAÇÕES: "
    for i in list(frase):
        print(i, end='')
        sys.stdout.flush()
        time.sleep(0.05)
    os.system('cls')
    titulo()
    confiaveis = ['demotrade-topgain.firebaseio.com']
    threading.Thread(target=verificacaoConect).start()
    threading.Thread(target=verificacaoConectDB).start()
    versaoOk = False
    versao = '270720'
    request = requests.get('https://api-copy.herokuapp.com/assinantes')
    data = request.json()

    for i in data:
        if versao == i['email']:
            versaoOk = True
            print(Fore.GREEN + '--> VERSAO ATUALIZADA!')
            break

    if versaoOk == False:
        print(Fore.RED + '--> HA UMA VERSAO MAIS ATUALIZADA, BAIXE NA AREA DE MEMBROS DA HOTMART')

    now = timestamp_converter(API.get_server_timestamp(), 2)
    current_date = now.strftime('%d/%m/%Y')
    licenca = False

    for i in data:
        if email == i['email']:
            licenca = True
            data_licenca = datetime.strptime(i['data'], '%d/%m/%Y')
            due_date = (data_licenca + timedelta(days=31))
            current_date = datetime.strptime(current_date, '%d/%m/%Y')
            dt = due_date.strftime('%d/%m/%Y')
            resta = due_date - current_date
            resta = str(resta)[:-9]

            if current_date > due_date:
                print(Fore.RED + '--> Sua licenca venceu dia: {}'.format(dt))
                print(Fore.RED + '--> O sistema funcionara apenas em modo treinamento')
                MODE = 'PRACTICE'
                tipo_conta_saida = 'Conta de treinamento'
            else:
                print(Fore.GREEN + '--> Licenca OK! {} restantes'.format(resta))
                if tipo_conta == 'r':
                    MODE = 'REAL'
                    tipo_conta_saida = 'Conta real'
                else:
                    MODE = 'PRACTICE'
                    tipo_conta_saida = 'Conta de treinamento'
            break

    if licenca == False:
        print(Fore.RED + '--> Licenca invalida para o email informado')
        print(Fore.RED + '--> O sistema funcionara apenas em modo treinamento')
        MODE = 'PRACTICE'
        tipo_conta_saida = 'Conta de treinamento'

    API.change_balance(MODE)

    def perfil():
        perfil = json.loads(json.dumps(API.get_profile_ansyc()))
        return perfil
    saldo = API.get_balance()

    if porcentagem == True:
        stop_win = (take_profit * saldo) / 100
        stop_loss = ((take_loss * saldo) / 100) * -1

    else:
        stop_win = take_profit
        stop_loss = take_loss * -1

    global initial_value

    if porc_preco == True:
        amount = (amount * saldo) / 100
        current_price = amount
        initial_value = amount
    elif porc_preco == False:
        amount = amount
        current_price = amount
        initial_value = amount

    def ouvirOperacao(message):
        global sinal
        sinal = str(message["data"])

    def payout(par, tipo, timeframe=1):
        if tipo == 'turbo':
            a = API.get_all_profit()
            return int(100 * a[par]['turbo'])

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
                dif = (datetime.strptime(hora, formato) -
                       datetime.strptime(AgoraHora, formato)).total_seconds()
                # Verifica a diferença entre a hora da noticia e a hora da operação
                minutesDiff = dif / 60

                # Verifica se a noticia irá acontencer 30 min antes ou depois da operação
                if minutesDiff >= -30 and minutesDiff <= 0 or minutesDiff <= 30 and minutesDiff >= 0:
                    return True
                    break

    print(Fore.YELLOW + '\n--> Dados de Usuario')
    print('    Nome: {}'.format(perfil()['name']))
    print('    Tipo de conta: {}'.format(tipo_conta_saida))
    print('    Saldo: {} {} '.format(perfil()['currency_char'], saldo))
    print(Fore.YELLOW + '--> Dados de Trading')
    print('    Preco: {} {} '.format(perfil()['currency_char'], amount))
    print('    Quantidade de Martingale:', quantidadeMg)
    print('    Fator de multiplicação Martingale:', 'X'+str(fatorMartingale))
    print('    Soros:', soros)
    print('    Nivel de soros:', quantidadeSoros)
    print('    Payout minimo:', str(payoutMinimo), '%')
    print(Fore.YELLOW + '--> Gerenciamento')
    print('    Take Profit: {}'.format(
        arquivo.get('GERENCIAMENTO', 'take_profit')), end='')
    print(' %', end='') if porcentagem == True else print('', end='')
    print(Fore.RED + ' Sem Stop') if arquivo.get('GERENCIAMENTO',
                                                 'take_profit') == '' or arquivo.get('GERENCIAMENTO', 'take_profit') == '0' else print('')
    print('    Stop Loss: {}'.format(
        arquivo.get('GERENCIAMENTO', 'stop_loss')), end='')
    print(' %', end='') if porcentagem == True else print('', end='')
    print(Fore.RED + ' Sem Stop') if arquivo.get('GERENCIAMENTO',
                                                 'stop_loss') == '' or arquivo.get('GERENCIAMENTO', 'stop_loss') == '0' else print('')

    while True:
        verifica = input(
            '--> Os dados acima estao corretos? [s] Sim | [n] Nao: ').lower()
        if verifica != 's' and verifica != 'n':
            print('    Por favor, informe se os dados estao corretos...')
        elif verifica == 'n':
            sair_sistema(
                '    Por favor, corrija os dados no arquivo de configuracoes')
        else:
            break
    linha()

    def stop(res):
        global trava
        if res == 'win':
            print(Fore.GREEN +
                  '---> STOP WIN ALCANCADO - Finalizando todas as operacoes')
            trava = False
        elif res == 'loss':
            print(Fore.RED + '---> STOP LOSS BATIDO - Finalizando todas as operacoes')
            trava = False

    global conta_lucro
    conta_lucro = 0
    global conta_perca
    conta_perca = 0
    global conta_total
    conta_total = 0

    def conta():
        global conta_lucro
        global conta_perca
        global conta_total

        conta_total = float(conta_lucro) - (float(conta_perca) * -1)

        print(Fore.YELLOW+'---> SALDO')
        print('     Lucro: {} | Perda: {} | Total: {} | Stop Win: {} | Stop Loss: {}'.format(conta_lucro, conta_perca,
                                                                                             conta_total, arquivo.get('GERENCIAMENTO', 'take_profit'), arquivo.get('GERENCIAMENTO', 'stop_loss')))

        if conta_total >= stop_win:
            stop('win')
        elif conta_total <= stop_loss:
            stop('loss')

    def buy_binary(valor, moeda, direcao, timeframe):
        global conta_lucro
        global conta_perca
        global conta_total
        
        while True:
            status, id = API.buy(valor, moeda, direcao.lower(), timeframe)
            if status:
                time.sleep(randint(0, 4))
                print(Fore.YELLOW + '---> OPERACAO:')
                print('     ATIVO:', moeda, '| DIREÇÃO:', direcao, '| EXPIRAÇÃO:',
                      timeframe, 'M', '| VALOR:', perfil()['currency_char'], round(valor, 3))
                resultado = round(API.check_win_v3(id), 3)
                if resultado > 0:
                    """ time.sleep(randint(0, 9)) """
                    conta_lucro += float(resultado)
                    print('     RESULTADO: WIN    |', Fore.GREEN + 'LUCRO:' +
                          str(perfil()['currency_char'])+' '+str(resultado) + ' :)')
                    print('\n')
                    print('-'*50)
                    print('\n')
                    conta()
                    break
                elif resultado == 0:
                    """ time.sleep(randint(0, 9)) """
                    print('     RESULTADO: DOJI    |', 'LUCRO:' +
                          str(perfil()['currency_char'])+' '+str(resultado) + ' :|')
                    print('\n')
                    print('-'*50)
                    print('\n')
                    break
                else:
                    """ time.sleep(randint(0, 9)) """
                    conta_perca += float(resultado)
                    print('     RESULTADO: LOSS   |', Fore.RED + 'PREJUÍZO:' +
                          str(perfil()['currency_char'])+' '+str(resultado) + ' :(')
                    print('\n')
                    conta()
                    if quantidadeMg > martingale:
                        print(Fore.YELLOW + '---> MARTINGALE:\n')
                        valor = valor * fatorMartingale
                        martingale += 1
                        continue
                    print('-'*50)
                    break
        else:
            print('    A QUERIDA IQ BLOQUEOU MINHA ENTRADA :(')

    def buy_digital(moeda, valor, direcao, timeframe):

        global conta_lucro
        global conta_perca
        global conta_total

        status, id = API.buy_digital_spot(moeda, valor, direcao, timeframe)
        if status:
            """ time.sleep(randint(0, 4)) """
            print(Fore.YELLOW + '---> OPERACAO:')
            print('     ATIVO:', moeda, '| DIREÇÃO:', direcao, '| EXPIRAÇÃO:',
                  timeframe, 'M', '| VALOR:', perfil()['currency_char'], round(valor, 3))
            while True:
                status, resultado = API.check_win_digital_v2(id)
                if status:
                    if resultado > 0:
                        """ time.sleep(randint(0, 9)) """
                        conta_lucro += float(resultado)
                        print('     RESULTADO: WIN    |', Fore.GREEN + 'LUCRO:' +
                              str(perfil()['currency_char'])+' '+str(resultado) + ' :)')
                        print('\n')
                        print('-'*50)
                        print('\n')
                        conta()
                    else:
                        """ time.sleep(randint(0, 9)) """
                        conta_perca += float(resultado)
                        print(Fore.YELLOW + '---> RESULTADO:')
                        print('     ID: {} | ATIVO: {} | DIRECAO: {} | RESULTADO: '.format(
                            id, moeda, direcao), end='')
                        print(Fore.RED + 'LOSS | LUCRO: {} '.format(resultado))
                        conta()
                    break
        else:
            print(Fore.YELLOW + '---> RESULTADO:')
            print('    A QUERIDA IQ BLOQUEOU MINHA ENTRADA :(')

    configDBot = {
        "apiKey": "apiKey",
        "authDomain": "dtraders-86997.firebaseapp.com",
        "databaseURL": "https://dtraders-86997.firebaseio.com/",
        "storageBucket": "projectId.appspot.com"
    }

    # PARA ALTERAR O BANCO APENAS DETERMINE configDEMO OU configTopGain NA PROPRIEDADE DO pyrebase.initialize_app
    firebase = pyrebase.initialize_app(configDBot)
    db = firebase.database()
    dadoDB = db.child("sinais/1").get()
    sinalinicio = str(dadoDB.val())
    sinal = ""
    dadoDB1 = db.child("sinais/1").stream(ouvirOperacao)
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
    time.sleep(2)
    print('-'*36 + ' ANALISANDO O GRÁFICO E AGUARDANDO OPORTUNIDADE ' + '-'*35)
    """ print(Fore.YELLOW + '--> OPERAÇÕES:') """
    while True:
        if trava:
            if sinalinicio != sinal:
                dados = sinal.split(';')
                moeda = dados[0]
                direcao = dados[1]
                timeframe = int(dados[2])
                horario = dados[3]
                valor = amount
                martingale = 0
                sinalinicio = sinal
                print(sinal)
                if moeda in abertas:
                    print(moeda)
                    resultadoNoticia = noticias()
                    if resultadoNoticia != True:
                        threading.Thread(target=buy_binary, args=(
                            valor, moeda, direcao, timeframe)).start()
                        """ else:
                            threading.Thread(target=buy_digital, args=(moeda, valor, direcao, timeframe)).start() """

else:
    if reason == "[Errno -2] Name or service not known":
        sair_sistema('    Sem conexao com a internet')
    elif reason == error_password:
        sair_sistema(
            '    Acho que voce errou seu email ou senha da IQ Option :( por favor verifique e tente novamente')
    else:
        sair_sistema(
            '    Nao foi possivel se conectar com a IQ Option \n    sua conta nao pode ter autenticacao de 2 fatores ou ter sido criada pelo Facebook.')
