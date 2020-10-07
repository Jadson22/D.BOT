from iqoptionapi.stable_api import IQ_Option
import PySimpleGUI as sg
import time
import requests
import logging
import configparser
import json
import os
import sys
import socket
import os
from datetime import datetime, date, timedelta
from dateutil import tz
import threading
from colorama import init, Fore, Back
from random import randint
import pyrebase

logging.disable(level=(logging.DEBUG))

sg.change_look_and_feel('Black')

direita = [
    [sg.Text('    ')],
    [sg.Output(size=(83, 35), font=('Helvetica', 11), key='-OUT-')],
    [sg.Button('  SALVAR CONFIGURACOES ', key='salvar')]
]

esquerda = [
    [sg.Text(''), sg.Image(r'log/log.png', size=(200, 205))],

    [sg.Text('       '), sg.Button('  INICIAR OPERACOES  ', key='iniciar')],

    [sg.Frame(' Acesso ', [
        [sg.Text('Email IQ: ', key='txtw'), sg.Input(size=(25, 0),
                                                     key='email', background_color='white', text_color='black')],
        [sg.Text('Senha IQ:'), sg.Input(size=(25, 0), key='senha',
                                        background_color='white', text_color='black', password_char='*')],
        [sg.Text(' '), sg.Radio('Treinamento', key='treinamento', group_id='1', default='true'), sg.Text(
            '     '), sg.Radio('Real', key='real', group_id='1'), sg.Text('       ')],
    ])],

    [sg.Frame(' Preco da Operacao ', [
        [sg.Checkbox('em %', key='porcentagem_preco'), sg.Text('Valor: '), sg.Input(size=(
            12, 0), key='preco', background_color='white', text_color='black'), sg.Text('       ')],
    ])],

    [sg.Frame(' Gerenciamento ', [
        [sg.Checkbox('Filtro D.BOT', key='filtroDbot')],
        [sg.Radio('Martingale', key='martingale', group_id='2'), sg.Radio(
            'Soros', key='soros', group_id='2'), sg.Radio('SorosGale', key='sorosGale', group_id='2')],
        [sg.Text('Nivel:        '), sg.Input(size=(17, 0), key='nivel_Estrategia',
                                             background_color='white', text_color='black'), sg.Text(' ')],
        [sg.Checkbox('Martingale PO', key='martingalePO')],
        [sg.Text('Nivel: '), sg.Input(size=(5, 0), key='nivel_Estrategia_PO',
                                      background_color='white', text_color='black'),
         sg.Text('Fator Mg: '), sg.Input(size=(5, 0), key='fatorMG',
                                         background_color='white', text_color='black'), sg.Text('X')],
        [sg.Text('Payout:    '), sg.Input(size=(17, 0), key='payout',
                                          background_color='white', text_color='black'), sg.Text(' ')],
        [sg.Text('Stop Win: '), sg.Input(size=(17, 0), key='stop_win',
                                         background_color='white', text_color='black'), sg.Text(' ')],
        [sg.Text('Stop Loss:'), sg.Input(size=(17, 0), key='stop_loss',
                                         background_color='white', text_color='black')],
        [sg.Checkbox('Stop em %', key='gerenciamento')],
    ])],
]

layout = [
    [sg.Column(esquerda), sg.Column(direita)]
]
janela = sg.Window('D.BOT', icon='log/log.ico', finalize=True).layout(layout)

janela.Finalize()
janela['iniciar'].update(disabled=True)

global trava
trava = True
global amount
global espera
espera = True
global abertasDigital
abertasDigital = []
global abertasBinaria
abertasBinaria = []
global quantidadeMg
quantidadeMg = 0
global quantidadeSoros
quantidadeSoros = 0
global nivel
nivel = 0
global perca
perca = 0
global nivel_SG
nivel_SG = 0
global lucro_total
lucro_total = 0
global quantidadeMgPO
quantidadeMgPO = 0

existe_arquivo = os.path.isfile('./setup.conf')
if existe_arquivo:
    try:
        file = open('setup.conf')
    except IOError:
        print('Ocorreu um erro, voce deve definir as configuracoes no Configurador primeiro. \n\n O sistema sera encerrado')
        time.sleep(5)

    arquivo = configparser.RawConfigParser()
    arquivo.read('setup.conf')
    try:
        global email
        email = arquivo.get('USER', 'email')
        global senha
        senha = arquivo.get('USER', 'senha')
        global error_password
        error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""
        global tipo_conta
        tipo_conta = arquivo.get('TRADE', 'tipo_conta').lower()
        global amount
        amount = float(arquivo.get('TRADE', 'preco_operacao'))
        global porc_preco
        porc_preco = arquivo.getboolean('TRADE', 'porc_preco')
        global filtroDbot
        filtroDbot = arquivo.getboolean('TRADE', 'filtroDbot')
        global martingale
        martingale = arquivo.getboolean('TRADE', 'martingale')
        global martingalePO
        martingalePO = arquivo.getboolean('TRADE', 'martingalePO')
        global soros
        soros = arquivo.getboolean('TRADE', 'soros')
        global sorosGale
        sorosGale = arquivo.getboolean('TRADE', 'sorosGale')
        global nivel_Estrategia
        nivel_Estrategia = arquivo.get('TRADE', 'nivel_Estrategia')
        global nivel_Estrategia_PO
        nivel_Estrategia_PO = arquivo.get('TRADE', 'nivel_Estrategia_PO')
        global fatorMG
        fatorMG = arquivo.get('TRADE', 'fatorMG')
        global payoutMinimo
        payoutMinimo = arquivo.get('TRADE', 'payout')
        global take_profit
        take_profit = float(arquivo.get('GERENCIAMENTO', 'take_profit'))
        if take_profit == '0' or take_profit == '':
            take_profit = 100000
        else:
            take_profit = take_profit
        global take_loss
        take_loss = arquivo.get('GERENCIAMENTO', 'stop_loss')
        if take_loss == '0' or take_loss == '':
            take_loss = 100000
        else:
            take_loss = float(take_loss)
        global porcentagem
        porcentagem = arquivo.getboolean('GERENCIAMENTO', 'porcentagem')

    except ValueError:
        print('\n\n    Inconsistencia nas configuracoes especificadas, \n    voce nao pode deixar campos em branco ou usar virgula em numero decimal!\n    Assista todos os videos de configuracao para nao ter nenhuma duvida!')

    janela['email'].update(email)
    janela['senha'].update(senha)
    if tipo_conta == 't':
        janela['treinamento'].update(True)
    else:
        janela['real'].update(True)
    janela['preco'].update(amount)
    janela['porcentagem_preco'].update(porc_preco)
    janela['stop_win'].update(arquivo.get('GERENCIAMENTO', 'take_profit'))
    janela['stop_loss'].update(arquivo.get('GERENCIAMENTO', 'stop_loss'))
    janela['gerenciamento'].update(porcentagem)
    janela['filtroDbot'].update(filtroDbot)
    janela['martingale'].update(martingale)
    janela['martingalePO'].update(martingalePO)
    janela['soros'].update(soros)
    janela['sorosGale'].update(sorosGale)
    janela['nivel_Estrategia'].update(nivel_Estrategia)
    janela['nivel_Estrategia_PO'].update(nivel_Estrategia_PO)
    janela['fatorMG'].update(fatorMG)
    janela['payout'].update(payoutMinimo)


def salvar_config():
    log_file = open('setup' + '.conf', 'w+', encoding='utf8')
    log_file.writelines('[USER]')
    log_file.writelines('\nemail=' + values['email'])
    log_file.writelines('\nsenha=' + values['senha'])
    log_file.writelines('\n[TRADE]')
    if values['real']:
        tconta = 'r'
    else:
        tconta = 't'
    log_file.writelines('\ntipo_conta=' + tconta)
    log_file.writelines('\nporc_preco=' + str(values['porcentagem_preco']))
    log_file.writelines('\npreco_operacao=' + values['preco'])
    log_file.writelines('\nfiltroDbot=' + str(values['filtroDbot']))
    log_file.writelines('\nmartingale=' + str(values['martingale']))
    log_file.writelines('\nmartingalePO=' + str(values['martingalePO']))
    log_file.writelines('\nsoros=' + str(values['soros']))
    log_file.writelines('\nsorosGale=' + str(values['sorosGale']))
    log_file.writelines('\nnivel_Estrategia=' + values['nivel_Estrategia'])
    log_file.writelines('\nnivel_Estrategia_PO=' +
                        values['nivel_Estrategia_PO'])
    log_file.writelines('\nfatorMG=' + values['fatorMG'])
    log_file.writelines('\npayout=' + values['payout'])
    log_file.writelines('\n[GERENCIAMENTO]')
    log_file.writelines('\nporcentagem=' + str(values['gerenciamento']))
    log_file.writelines('\ntake_profit=' + values['stop_win'])
    log_file.writelines('\nstop_loss=' + values['stop_loss'])
    log_file.close()


while True:
    event, values = janela.read()

    if event in (sg.WIN_CLOSED, 'Exit'):
        trava = False
        janela.close()
        sys.exit()
        break

    if event == 'salvar':
        janela['iniciar'].update(disabled=False)
        salvar_config()

    if event == 'iniciar':
        janela['iniciar'].update(disabled=True)
        janela['salvar'].update(disabled=True)
        #desabilitando botões

        def sair_sistema(msg='    Por favor, verifique as configuracoes de TRADE'):
            global trava
            print(msg)
            trava = False
            print('\n    Reinicie o sistema para tentar novamente... \n ')
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
                                dadoDB1 = db.child(
                                    "sinais/1").stream(ouvirOperacao)
                                print(
                                    '---> CONECTADO AO BANCO DE DADOS COM SUCESSO!\n')
                                mensagemConnectDB = True
                    except:
                        pass
                        if mensagemConnectDB == True:
                            dadoDB1.close()
                            print(
                                '\nPERDA DE CONEXAO COM O BANCO DE DADOS, VERIFIQUE SUA INTERNET OU UM POSSIVEL BLOQUEIO DO ANTIVIRUS')
                            print('---> TENTANDO RECONECTAR...\n')
                            mensagemConnectDB = False
                    a.close()

        def verificacaoConect():
            mensagemConnect = True
            while True:
                if API.check_connect() == False:
                    if mensagemConnect == True:
                        print(
                            '\nPERDA DE CONEXAO COM A IQ OPTION, VERIFIQUE SUA INTERNET OU UM POSSIVEL BLOQUEIO DO ANTIVIRUS')
                        print('---> TENTANDO RECONECTAR...\n')
                        mensagemConnect = False
                    API.connect()
                else:
                    if mensagemConnect == False:
                        print('---> CONECTADO A IQ OPTION COM SUCESSO!\n')
                        mensagemConnect = True

        def perfil():
            perfil = json.loads(json.dumps(API.get_profile_ansyc()))
            return perfil

        def entradaGale(moeda, resultado, valor, direcao, timeframe):
            if trava:
                print('---> MARTINGALE:\n')
                arquivoLOG = open('Log de operacoes/' +
                                  data_em_texto+'.txt', 'a', encoding='utf8')
                arquivoLOG.write('\n---> MARTINGALE:\n')
                arquivoLOG.close()
                valorMartingale = valor * float(fatorMG)
                if moeda in abertasBinaria:
                    threading.Thread(target=buy_binary, args=(
                        valorMartingale, moeda, direcao, timeframe), daemon=True).start()
                elif moeda in abertasDigital:
                    threading.Thread(target=buy_digital, args=(
                        moeda, valorMartingale, direcao, timeframe), daemon=True).start()

        def ouvirOperacao(message):
            global sinal
            global sinalinicio
            sinal = str(message["data"])
            if sinalinicio != sinal:
                sinalinicio = sinal
                if trava:
                    dados = sinal.split(';')
                    moeda = dados[0]
                    direcao = dados[1]
                    timeframe = int(dados[2])
                    horario = dados[3]
                    tendencia = dados[4]
                    valor = amount
                    global quantidadeMg
                    quantidadeMg = 0
                    if filtroDbot == False:
                        if moeda in abertasBinaria:
                            threading.Thread(target=buy_binary, args=(
                                valor, moeda, direcao, timeframe), daemon=True).start()
                        elif moeda in abertasDigital:
                            threading.Thread(target=buy_digital, args=(
                                moeda, valor, direcao, timeframe), daemon=True).start()
                    if filtroDbot == True and tendencia == 't':
                        if moeda in abertasBinaria:
                            threading.Thread(target=buy_binary, args=(
                                valor, moeda, direcao, timeframe), daemon=True).start()
                        elif moeda in abertasDigital:
                            threading.Thread(target=buy_digital, args=(
                                moeda, valor, direcao, timeframe), daemon=True).start()

        def payout(par, tipo, timeframe=1):
            if tipo == 'turbo':
                a = API.get_all_profit()
                return int(100 * a[par]['turbo'])
            elif tipo == 'digital':
                API.subscribe_strike_list(par, timeframe)
                while True:
                    d = API.get_digital_current_profit(par, timeframe)
                    if d != False:
                        d = int(d)
                        break
                    time.sleep(1)
                API.unsubscribe_strike_list(par, timeframe)
                return d

        def moedas_abertas():
            while True:
                global abertasDigital
                global abertasBinaria
                par = API.get_all_open_time()
                abertasDigital.clear()
                abertasBinaria.clear()
                for paridade in par['digital']:
                    if par['digital'][paridade]['open'] == True:
                        payouts = payout(paridade, 'digital')
                        if payouts >= int(payoutMinimo):
                            abertasDigital.append(paridade)
                    continue
                for paridade in par['turbo']:
                    if par['turbo'][paridade]['open'] == True:
                        payouts = payout(paridade, 'turbo')
                        if payouts >= int(payoutMinimo):
                            abertasBinaria.append(paridade)
                    continue
                time.sleep(1200)
                continue

        def stop(res):
            global trava
            if res == 'win':
                print('---> STOP WIN - FOI UM PRAZER BATER META PARA VOCE :)')
                arquivoLOG = open('Log de operacoes/'+data_em_texto +
                                  '.txt', 'a', encoding='utf8')
                arquivoLOG.write('\n---> ---> STOP WIN :)')
                arquivoLOG.close()
                trava = False
            elif res == 'loss':
                print('---> STOP LOSS - DESCULPE, HOJE NAO FOI MEU DIA :(')
                arquivoLOG = open('Log de operacoes/'+data_em_texto +
                                  '.txt', 'a', encoding='utf8')
                arquivoLOG.write('\n---> STOP LOSS :(')
                arquivoLOG.close()
                trava = False

        def buy_digital(moeda, valor, direcao, timeframe):
            trava = False
            global conta_lucro
            global conta_perca
            global conta_total
            global trava
            global amount
            global initial_value
            global nivel
            global perca
            global nivel_SG
            global lucro_total
            global quantidadeMgPO
            status, id = API.buy_digital_spot(
                moeda, valor, direcao.lower(), timeframe)
            if status:
                print('---> OPERACAO:')
                print('       ATIVO:', moeda, '| DIRECAO:', direcao, '| EXPIRACAO:',
                      timeframe, 'M', '| VALOR:', perfil()['currency_char'], round(valor, 2))
                arquivoLOG = open('Log de operacoes/' +
                                  data_em_texto+'.txt', 'a', encoding='utf8')
                arquivoLOG.write('\n---> OPERACAO:')
                arquivoLOG.write('\n     ATIVO:'+str(moeda) + '| DIRECAO:' + str(direcao) + '| EXPIRACAO:'+str(
                    timeframe) + 'M' + '| VALOR:'+str(dados_conta['currency_char'])+str(round(valor, 3)))
                arquivoLOG.close()
                while True:
                    status, resultado = API.check_win_digital_v2(id)
                    if status:
                        if resultado > 0:
                            conta_lucro += float(resultado)
                            print('       RESULTADO: WIN    |', 'LUCRO:' + str(perfil()
                                                                               ['currency_char'])+' ', round(resultado, 2), ' :)')
                            arquivoLOG = open(
                                'Log de operacoes/' + data_em_texto+'.txt', 'a', encoding='utf8')
                            arquivoLOG.write('\n     RESULTADO: WIN    |'+'LUCRO:'+str(
                                dados_conta['currency_char'])+' '+str(resultado)+' :)')
                            arquivoLOG.close()
                            amount = initial_value
                            conta()
                            if sorosGale:
                                if nivel_SG == 0:
                                    if nivel == int(nivel_Estrategia):
                                        amount = initial_value
                                        nivel = 0
                                        nivel_SG = 0
                                    elif nivel < int(nivel_Estrategia):
                                        amount = round(
                                            amount + resultado, 2)
                                        nivel += 1
                                else:
                                    primeira_entrada = amount
                                    lucro_total = round(
                                        lucro_total + resultado, 2)
                                    amount = round(amount + lucro_total, 2)
                                if nivel_SG != 0 and lucro_total >= perca:
                                    print(
                                        '    SOROSGALE VOLTANDO AO NIVEL 0')
                                    nivel_SG = 0
                                    amount = initial_value
                                    perca = 0
                                    lucro_total = 0
                                    nivel = 0
                            elif soros:
                                global quantidadeSoros
                                if int(nivel_Estrategia) > quantidadeSoros:
                                    print('\n---> SOROS:\n')
                                    amount = round(amount + resultado, 2)
                                    quantidadeSoros += 1
                                else:
                                    amount = initial_value
                                    quantidadeSoros = 0
                            trava = True

                        else:
                            conta_perca += float(resultado)
                            print('       RESULTADO: LOSS    |', 'PREJUIZO:' +
                                  str(perfil()['currency_char'])+' ', round(resultado, 2), ' :(')
                            arquivoLOG = open(
                                'Log de operacoes/' + data_em_texto+'.txt', 'a', encoding='utf8')
                            arquivoLOG.write('\n     RESULTADO: LOSS   |'+'PREJUIZO:'+str(
                                dados_conta['currency_char'])+' '+str(resultado)+' :(')
                            arquivoLOG.close()
                            amount = initial_value
                            quantidadeSoros = 0
                            conta()
                            global quantidadeMg
                            if martingale:
                                if int(nivel_Estrategia) > quantidadeMg:
                                    quantidadeMg += 1
                                    entradaGale(
                                        moeda, resultado, valor, direcao, timeframe)
                                else:
                                    if martingalePO:
                                        if int(nivel_Estrategia_PO) > quantidadeMgPO:
                                            print(
                                                '---> MARTINGALE PROXIMA OPERACAO:\n')
                                            quantidadeMgPO += 1
                                            amount = valor * float(fatorMG)

                            elif sorosGale:
                                if nivel_SG == 0:
                                    amount = initial_value / 2
                                    nivel_SG += 1
                                    perca = initial_value
                                    primeira_entrada = amount
                                else:
                                    lucro_total = 0
                                    perca += perca / 2
                                    amount = perca / 2
                                    nivel_SG += 1

                            elif martingalePO:
                                if int(nivel_Estrategia_PO) > quantidadeMgPO:
                                    print('---> MARTINGALE PROXIMA OPERACAO:\n')
                                    quantidadeMgPO += 1
                                    amount = valor * float(fatorMG)
                            trava = True
                        break
            else:
                trava = True
                print('---> RESULTADO:')
                print('    A QUERIDA IQ BLOQUEOU MINHA ENTRADA :(')
                print('-' * 131)

        def buy_binary(valor, moeda, direcao, timeframe):
            trava = False
            global conta_lucro
            global conta_perca
            global conta_total
            global trava
            global amount
            global initial_value
            global nivel
            global perca
            global nivel_SG
            global lucro_total
            global quantidadeMgPO
            while True:
                status, id = API.buy(
                    valor, moeda, direcao.lower(), timeframe)
                if status:
                    time.sleep(randint(0, 4))
                    print('---> OPERACAO:')
                    print('       ATIVO:', moeda, '| DIRECAO:', direcao, '| EXPIRACAO:',
                          timeframe, 'M', '| VALOR:', perfil()['currency_char'], round(valor, 3))
                    arquivoLOG = open('Log de operacoes/' +
                                      data_em_texto+'.txt', 'a', encoding='utf8')
                    arquivoLOG.write('\n---> OPERACAO:')
                    arquivoLOG.write('\n     ATIVO:'+str(moeda) + '| DIRECAO:' + str(direcao) + '| EXPIRACAO:'+str(
                        timeframe) + 'M' + '| VALOR:'+str(dados_conta['currency_char'])+str(round(valor, 3)))
                    arquivoLOG.close()
                    resultado = round(API.check_win_v3(id), 3)
                    if resultado > 0:
                        conta_lucro += float(resultado)
                        print('       RESULTADO: WIN    |', 'LUCRO:' + str(perfil()
                                                                           ['currency_char'])+' ', round(resultado, 2), ' :)')
                        arquivoLOG = open(
                            'Log de operacoes/' + data_em_texto+'.txt', 'a', encoding='utf8')
                        arquivoLOG.write('\n     RESULTADO: WIN    |'+'LUCRO:'+str(
                            dados_conta['currency_char'])+' '+str(resultado)+' :)')
                        arquivoLOG.close()
                        amount = initial_value
                        conta()
                        if sorosGale:
                            if nivel_SG == 0:
                                if nivel == int(nivel_Estrategia):
                                    amount = initial_value
                                    nivel = 0
                                    nivel_SG = 0
                                elif nivel < int(nivel_Estrategia):
                                    amount = round(amount + resultado, 2)
                                    nivel += 1
                            else:
                                primeira_entrada = amount
                                lucro_total = round(
                                    lucro_total + resultado, 2)
                                amount = round(amount + lucro_total, 2)
                            if nivel_SG != 0 and lucro_total >= perca:
                                print(
                                    '    SOROSGALE VOLTANDO AO NIVEL 0')
                                nivel_SG = 0
                                amount = initial_value
                                perca = 0
                                lucro_total = 0
                                nivel = 0
                        elif soros:
                            global quantidadeSoros
                            if int(nivel_Estrategia) > quantidadeSoros:
                                print('---> SOROS:\n')
                                arquivoLOG = open(
                                    'Log de operacoes/' + data_em_texto+'.txt', 'a', encoding='utf8')
                                arquivoLOG.write('\n---> SOROS:\n')
                                arquivoLOG.close()
                                amount = round(amount + resultado, 2)
                                quantidadeSoros += 1
                            else:
                                amount = initial_value
                                quantidadeSoros = 0
                        trava = True
                        break
                    elif resultado == 0:
                        print('     RESULTADO: DOJI    |', 'LUCRO:' +
                              str(perfil()['currency_char'])+' '+str(resultado) + ' :|')
                        arquivoLOG = open(
                            'Log de operacoes/' + data_em_texto+'.txt', 'a', encoding='utf8')
                        arquivoLOG.write('\n     RESULTADO: DOJI    |'+'LUCRO:'+str(
                            dados_conta['currency_char'])+' '+str(resultado)+' :|')
                        arquivoLOG.close()
                        trava = True
                        break
                    else:
                        conta_perca += float(resultado)
                        print('       RESULTADO: LOSS    |', 'PREJUIZO:' +
                              str(perfil()['currency_char'])+' ', round(resultado, 2), ' :(')
                        arquivoLOG = open(
                            'Log de operacoes/' + data_em_texto+'.txt', 'a', encoding='utf8')
                        arquivoLOG.write('\n     RESULTADO: LOSS   |'+'PREJUIZO:'+str(
                            dados_conta['currency_char'])+' '+str(resultado)+' :(')
                        arquivoLOG.close()
                        amount = initial_value
                        quantidadeSoros = 0
                        conta()
                        global quantidadeMg
                        if martingale:
                            if int(nivel_Estrategia) > quantidadeMg:
                                quantidadeMg += 1
                                entradaGale(moeda, resultado,
                                            valor, direcao, timeframe)
                            else:
                                if martingalePO:
                                    if int(nivel_Estrategia_PO) > quantidadeMgPO:
                                        print(
                                            '---> MARTINGALE PROXIMA OPERACAO:\n')
                                        quantidadeMgPO += 1
                                        amount = valor * float(fatorMG)

                        elif sorosGale:
                            if nivel_SG == 0:
                                amount = initial_value / 2
                                nivel_SG += 1
                                perca = initial_value
                                primeira_entrada = amount
                            else:
                                lucro_total = 0
                                perca += perca / 2
                                amount = perca / 2
                                nivel_SG += 1

                        elif martingalePO:
                            if int(nivel_Estrategia_PO) > quantidadeMgPO:
                                print('---> MARTINGALE PROXIMA OPERACAO:\n')
                                quantidadeMgPO += 1
                                amount = valor * float(fatorMG)
                        trava = True
                        break
            else:
                print('    A QUERIDA IQ BLOQUEOU MINHA ENTRADA :(')
                trava = True

        def conta():
            global conta_lucro
            global conta_perca
            global conta_total
            conta_total = float(conta_lucro) - (float(conta_perca) * -1)
            print(' ')
            print('       LUCRO PARCIAL: {} | PERDA PARCIAL: {} | TOTAL: {}'.format(
                round(conta_lucro, 2), round(conta_perca, 2), round(conta_total, 2)))
            print('-' * 131)
            arquivoLOG = open('Log de operacoes/' +
                              data_em_texto + '.txt', 'a', encoding='utf8')
            arquivoLOG.write('\n       LUCRO PARCIAL: {} | PERDA PARCIAL: {} | TOTAL: {}'.format(
                round(conta_lucro, 2), round(conta_perca, 2), round(conta_total, 2)))
            arquivoLOG.write('\n')
            arquivoLOG.write('-'*100)
            arquivoLOG.write('\n')
            arquivoLOG.close()
            if conta_total >= stop_win:
                stop('win')
            elif conta_total <= stop_loss:
                stop('loss')

        try:
            file = open('setup.conf')
        except IOError:
            print('Ocorreu um erro, voce deve definir as configuracoes no Configurador primeiro. \n\n O sistema sera encerrado')
            time.sleep(5)
            sys.exit()

        arquivo = configparser.RawConfigParser()
        arquivo.read('setup.conf')
        try:
            email = arquivo.get('USER', 'email')
            senha = arquivo.get('USER', 'senha')
            error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""
            tipo_conta = arquivo.get('TRADE', 'tipo_conta').lower()
            amount = float(arquivo.get('TRADE', 'preco_operacao'))
            porc_preco = arquivo.getboolean('TRADE', 'porc_preco')
            filtroDbot = arquivo.getboolean('TRADE', 'filtroDbot')
            martingale = arquivo.getboolean('TRADE', 'martingale')
            martingalePO = arquivo.getboolean('TRADE', 'martingalePO')
            soros = arquivo.getboolean('TRADE', 'soros')
            sorosGale = arquivo.getboolean('TRADE', 'sorosGale')
            nivel_Estrategia = arquivo.get('TRADE', 'nivel_Estrategia')
            nivel_Estrategia_PO = arquivo.get('TRADE', 'nivel_Estrategia_PO')
            fatorMG = arquivo.get('TRADE', 'fatorMG')
            payoutMinimo = arquivo.get('TRADE', 'payout')
            take_profit = float(arquivo.get('GERENCIAMENTO', 'take_profit'))
            if take_profit == '0' or take_profit == '':
                take_profit = 100000
            else:
                take_profit = take_profit
            take_loss = arquivo.get('GERENCIAMENTO', 'stop_loss')
            if take_loss == '0' or take_loss == '':
                take_loss = 100000
            else:
                take_loss = float(take_loss)
            porcentagem = arquivo.getboolean('GERENCIAMENTO', 'porcentagem')

        except ValueError:
            print('\n\n    Inconsistencia nas configuracoes especificadas, \n    voce nao pode deixar campos em branco ou usar virgula em numero decimal!\n    Assista todos os videos de configuracao para nao ter nenhuma duvida!')

        janela['email'].update(email, disabled=True)
        janela['senha'].update(senha, disabled=True)
        janela['treinamento'].update(disabled=True)
        janela['real'].update(disabled=True)
        janela['preco'].update(amount, disabled=True)
        janela['porcentagem_preco'].update(porc_preco, disabled=True)
        janela['stop_win'].update(arquivo.get('GERENCIAMENTO', 'take_profit'), disabled=True)
        janela['stop_loss'].update(arquivo.get('GERENCIAMENTO', 'stop_loss'), disabled=True)
        janela['gerenciamento'].update(porcentagem, disabled=True)
        janela['filtroDbot'].update(filtroDbot, disabled=True)
        janela['martingale'].update(martingale, disabled=True)
        janela['martingalePO'].update(martingalePO, disabled=True)
        janela['soros'].update(soros, disabled=True)
        janela['sorosGale'].update(sorosGale, disabled=True)
        janela['nivel_Estrategia'].update(nivel_Estrategia, disabled=True)
        janela['nivel_Estrategia_PO'].update(nivel_Estrategia_PO, disabled=True)
        janela['fatorMG'].update(fatorMG, disabled=True)
        janela['payout'].update(payoutMinimo, disabled=True)

        print('='*27 + ' COPYRIGHT TOP GAIN ' + '='*27)
        API = IQ_Option(email, senha)
        check, reason = API.connect()

        if check:
            configDBot = {
                "apiKey": "apiKey",
                "authDomain": "dtraders-86997.firebaseapp.com",
                "databaseURL": "https://dtraders-86997.firebaseio.com/",
                "storageBucket": "projectId.appspot.com"
            }
            firebase = pyrebase.initialize_app(configDBot)
            db = firebase.database()
            dados_conta = perfil()
            nome = dados_conta['first_name'].upper()
            mensagemBanco1 = db.child("mensagem1").get()
            mensagem1 = str(mensagemBanco1.val())
            mensagemBanco2 = db.child("mensagem2").get()
            mensagem2 = str(mensagemBanco2.val())
            mensagemBanco3 = db.child("mensagem3").get()
            mensagem3 = str(mensagemBanco3.val())

            confiaveis = ['demotrade-topgain.firebaseio.com']
            threading.Thread(target=verificacaoConect).start()
            threading.Thread(target=verificacaoConectDB).start()

            print('\n')
            for i in list(mensagem1):
                print(i, end='')
                sys.stdout.flush()
                time.sleep(0.05)
            print(nome)
            for u in list(mensagem2):
                print(u, end='')
                sys.stdout.flush()
                time.sleep(0.05)
            print(' ')
            for l in list(mensagem3):
                print(l, end='')
                sys.stdout.flush()
                time.sleep(0.05)
            print(' ')

            versaoOk = False
            versao = '1'
            request = requests.get('https://assinantes-dbot.herokuapp.com/assinantes')
            data = request.json()

            for i in data:
                if versao == i['email']:
                    versaoOk = True
                    break

            if versaoOk == False:
                print(
                    '\nHA UMA VERSAO MAIS ATUALIZADA, BAIXE NA AREA DE MEMBROS DA HOTMART')

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
                        print('\nSUA LICENCA VENCEU DIA: {}'.format(dt))
                        print('\nO SISTEMA FUNCIONARA APENAS EM MODO DE TREINAMENTO')
                        MODE = 'PRACTICE'
                        tipo_conta_saida = 'Conta de treinamento'
                    else:
                        print(
                            '\nRESTAM {} DIAS DE SUA LICENCA'.format(resta[0:3]))
                        if tipo_conta == 'r':
                            MODE = 'REAL'
                            tipo_conta_saida = 'Conta real'
                        else:
                            MODE = 'PRACTICE'
                            tipo_conta_saida = 'Conta de treinamento'
                    break

            if licenca == False:
                print('\nLICENCA INVALIDA PARA O EMAIL INFORMADO')
                print('\nO SISTEMA FUNCIONARA APENAS EM MODO DE TREINAMENTO')
                MODE = 'PRACTICE'
                tipo_conta_saida = 'Conta de treinamento'

            API.change_balance(MODE)

            saldo = API.get_balance()

            print('\nBANCA INICIAL: ', dados_conta['currency_char'], saldo)
            data_atual = date.today()
            data_em_texto = data_atual.strftime('%d%m%Y')
            arquivoLOG = open('log de operacoes/'+data_em_texto+'.txt', 'w')
            arquivoLOG.close()

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

            global conta_lucro
            conta_lucro = 0
            global conta_perca
            conta_perca = 0
            global conta_total
            conta_total = 0

            dadoDB = db.child("sinais/1").get()
            sinalinicio = str(dadoDB.val())
            sinal = ""
            dadoDB1 = db.child("sinais/1").stream(ouvirOperacao)
            threading.Thread(target=moedas_abertas).start()
            time.sleep(5)

            print('\n'+'-'*48 + ' ANALISANDO O GRAFICO ' + '-'*47 + '\n')

        else:
            if reason == "[Errno -2] Name or service not known":
                sair_sistema('    Sem conexao com a internet')
            elif reason == error_password:
                sair_sistema(
                    '    Acho que voce errou seu email ou senha da IQ Option :( por favor verifique e tente novamente')
            else:
                sair_sistema(
                    '    Nao foi possivel se conectar com a IQ Option \n    sua conta nao pode ter autenticacao de 2 fatores ou ter sido criada pelo Facebook.')
trava = False
janela.close()
sys.exit()

""" TODOS OS DIREITOS RESERVADOS 
. TOP GAIN OB 
. A UTILIZACAO DESSE SOFTWARE OU CODIGO FONTE DE FORMA NAO 
. AUTORIZADA OU ADQUIRIDA POR TERCEIROS E CABIVEL TODo O PROCESSO 
. QUE GARANTE A LEI N 9.279, DE 14 DE MAIO DE 1996. """
