import ccxt
import pandas as pd
import talib
import requests
import datetime
import time

# Bitget API 설정
exchange = ccxt.bitget({
    'rateLimit': 1000,  # 요청 속도 제한
    'enableRateLimit': True,  # 요청 속도 제한 사용
    'apiKey': 'bg_ec0f0e9e34212d8cd9679d9f25e7c600',  # Bitget API 키
    'secret': '7c598fd6d619a036e8a77722276f9467284c5dc769c3e33382773590b7d74b9a',  # Bitget API 시크릿 키
    'password': 'dlwlrma12',  # Bitget API 패스워드
    'options': {
        'defaultType': 'swap',
    }
})

symbol = 'ARPA/USDT:USDT'
length = 99
mult = 1.0
capital = 100  # 1000 USDT를 가지고 있다고 가정

# Discord 웹훅 URL 설정
webhook_url = 'https://discord.com/api/webhooks/1144471248244572301/eogR13OBRVc-9meQ4B8Jbv8LxVOuUz8srhDjYx3-04MIx6uC_leVi2skZG_ohyb-v_bQ'

# Discord 알림을 보내는 함수 수정
def send_discord_notification(signal, symbol, position_color):
    payload = {
        "embeds": [
            {
                "title": f"{symbol} 30분 시그널",
                "description": signal,
                "color": position_color  # 포지션에 따른 색상을 지정
            }
        ]
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(webhook_url, json=payload, headers=headers)

    if response.status_code == 204:
        print(f"{symbol}에 대한 Discord 신호 전송 성공: {signal}")
    else:
        print(f"{symbol}에 대한 Discord 신호 전송 실패: {signal}")

# 이전 포지션 초기화
prev_position = None

# 주기적으로 포지션을 확인하고 업데이트하는 무한 루프
while True:
    # OHLCV 데이터 가져오기
    src = exchange.fetch_ohlcv(symbol, timeframe='30m', limit=300)
    src = pd.DataFrame(src, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # 볼린저 밴드 계산
    basis = talib.SMA(src['close'], timeperiod=length)
    dev = mult * talib.STDDEV(src['close'], timeperiod=length)
    upper = basis + dev
    lower = basis - dev

    # 현재 포지션 확인
    last_close = src['close'].iloc[-1]

    # 현재 포지션을 확인하고 알림을 보냅니다.
    if last_close > upper.iloc[-1]:
        current_position = "Long"  # 롱 포지션
        position_color = 0x00ff00  # 롱 포지션일 때 초록색
    else:
        current_position = "Short"  # 숏 포지션
        position_color = 0xff0000  # 숏 포지션일 때 빨간색

    # 현재 시간 확인
    current_time = datetime.datetime.now().strftime('%m-%d %H:%M:%S')
    # 현재 포지션 출력
    print(f"{current_time}, 현재 포지션: {current_position} 대기 (30분)")

    # 포지션 변경 확인 및 거래 실행
    if prev_position is not None and prev_position != current_position:
        # 롱에서 숏으로 변경될 때 2배로 진입
        if current_position == "Short":
            # 보유 자본의 2배로 매도할 양 계산
            quantity_to_sell = 2 * capital

            # 시장가 매도 주문 실행
            try:
                order = exchange.create_market_sell_order(symbol, quantity_to_sell)
                print(f"롱 포지션 - 시장가 매도 주문이 완료되었습니다: {order}")

                # 주문이 성공한 경우에만 웹훅 메시지를 보냅니다.
                send_discord_notification(f"주문 성공 - 롱 포지션: {current_position}", symbol, position_color)
            except Exception as e:
                print(f"롱 포지션 - 롱 주문 오류: {e}")

        elif current_position == "Long":
            # 보유 자본을 기반으로 매수할 양 계산
            quantity_to_buy = capital  # 보유 자본 전부를 사용

            # 시장가 매수 주문 실행
            try:
                order = exchange.create_market_buy_order(symbol, quantity_to_buy)
                print(f"숏 포지션 - 시장가 매수 주문이 완료되었습니다: {order}")

                # 주문이 성공한 경우에만 웹훅 메시지를 보냅니다.
                send_discord_notification(f"주문 성공 - 숏 포지션: {current_position}", symbol, position_color)
            except Exception as e:
                print(f"숏 포지션 - 숏 주문 오류: {e}")

    # 이전 포지션 업데이트
    prev_position = current_position

    # 30분마다 다음 반복을 기다립니다.
    time.sleep(1800)  # 30분 = 30 * 60 초