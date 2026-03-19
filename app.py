from fastapi import FastAPI, Request
from binance.client import Client
import os
import uvicorn
import math

app = FastAPI()

# --- 配置 (从 claw.cloud 环境变量读取) ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
WEBHOOK_PASSPHRASE = os.getenv("WEBHOOK_PASSPHRASE", "ss9")

# 初始化合约客户端 (testnet=True 表示测试网)
# 如果以后切到实盘，只需把 testnet=True 改为 False 即可
client = Client(API_KEY, API_SECRET, testnet=True)

def get_tick_precision(symbol):
    """获取合约币种的数量精度 (stepSize)"""
    info = client.futures_exchange_info()
    for s in info['symbols']:
        if s['symbol'] == symbol.upper():
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    return int(round(-math.log(step_size, 10), 0))
    return 3 # 默认保留3位

@app.get("/")
def home():
    return {"status": "Binance Futures Robot Running"}

@app.post("/webhook")
async def futures_webhook(request: Request):
    data = await request.json()
    
    # 验证密码
    if data.get("passphrase") != WEBHOOK_PASSPHRASE:
        return {"status": "error", "msg": "password error"}

    # 提取字段
    symbol = data.get("symbol").upper()
    side = data.get("side").upper()      # BUY 或 SELL
    amount_usdt = float(data.get("amount", 0)) # 你想开多少 USDT 的仓位

    print(f"收到合约信号: {symbol} | 方向: {side} | 金额: {amount_usdt} USDT")

    try:
        # 1. 获取当前市价
        price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
        
        # 2. 计算下单数量并处理精度 (合约不支持直接传USDT金额，必须传币数)
        precision = get_tick_precision(symbol)
        quantity = round(amount_usdt / price, precision)

        # 3. 执行【合约市价下单】
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        
        print(f"合约成交成功: ID {order['orderId']} | 实际成交数量: {quantity}")
        return {"status": "success", "order": order}

    except Exception as e:
        print(f"合约下单失败: {str(e)}")
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
