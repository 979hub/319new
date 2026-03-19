from fastapi import FastAPI, Request
from binance.client import Client
import os
import uvicorn

app = FastAPI()

# --- 从环境变量读取 (在 claw.cloud 设置) ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
WEBHOOK_PASSPHRASE = os.getenv("WEBHOOK_PASSPHRASE", "ss9")
# 默认开仓金额（USDT），你可以通过环境变量灵活控制
DEFAULT_AMOUNT = float(os.getenv("TRADE_AMOUNT", "100"))

# 初始化并强制指向你提供的演示地址
client = Client(API_KEY, API_SECRET, testnet=True)
client.FUTURES_URL = 'https://demo-fapi.binance.com/fapi'

def get_quantity_precision(symbol):
    """【动态获取精度】不写死，直接从交易所获取规则"""
    info = client.futures_exchange_info()
    for s in info['symbols']:
        if s['symbol'] == symbol.upper():
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = f['stepSize']
                    # 动态计算小数点位数
                    return step_size.find('1') - step_size.find('.') if '.' in step_size else 0
    return 3

@app.post("/webhook")
async def handle_webhook(request: Request):
    # 1. 接收原始信号 (不管你传多少个字段，这里全部接收)
    signal = await request.json()
    
    # 2. 密码校验
    if signal.get("passphrase") != WEBHOOK_PASSPHRASE:
        return {"status": "error", "msg": "passphrase incorrect"}

    # 3. 提取核心参数
    symbol = signal.get("symbol").upper()
    side = signal.get("side").upper() # BUY/SELL
    
    print(f"信号转接成功: {symbol} | 方向: {side}")

    try:
        # 4. 获取当前价并计算下单量 (合约市价单必须传数量)
        ticker = client.futures_symbol_ticker(symbol=symbol)
        price = float(ticker['price'])
        
        # 动态计算精度，不写死任何数字
        precision = get_quantity_precision(symbol)
        quantity = round(DEFAULT_AMOUNT / price, precision)

        # 5. 执行【市价单】下单
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        
        return {"status": "success", "order_id": order['orderId']}
    except Exception as e:
        print(f"下单失败: {str(e)}")
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
