from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from binance.client import Client
import os

app = FastAPI()

# --- 配置区 (从环境变量读取，安全第一) ---
# 在 claw.cloud 的环境变量里设置这些值
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
WEBHOOK_PASSPHRASE = os.getenv("WEBHOOK_PASSPHRASE", "ss9")

# 初始化币安客户端
client = Client(API_KEY, API_SECRET)

# 定义信号结构 (严格按照你要求的: 密码, 币种, 金额, 方向)
class Signal(BaseModel):
    passphrase: str
    symbol: str    # 例如: BTCUSDT
    amount: float  # 开仓金额 (USDT)
    side: str      # buy 或 sell

@app.get("/")
def health_check():
    return {"status": "running"}

@app.post("/webhook")
async def binance_webhook(signal: Signal):
    # 1. 验证密码
    if signal.passphrase != WEBHOOK_PASSPHRASE:
        raise HTTPException(status_code=401, detail="Invalid password")

    print(f"收到信号: {signal.symbol} | 方向: {signal.side} | 金额: {signal.amount} USDT")

    # 2. 执行市价单逻辑
    try:
        side_type = Client.SIDE_BUY if signal.side.lower() == "buy" else Client.SIDE_SELL
        
        # 下市价单 (Market Order)
        # quoteOrderQty 代表你想花多少 USDT 买入/卖出
        order = client.create_order(
            symbol=signal.symbol.upper(),
            side=side_type,
            type=Client.ORDER_TYPE_MARKET,
            quoteOrderQty=signal.amount
        )
        
        print(f"下单成功: {order['orderId']}")
        return {"status": "success", "order_id": order['orderId']}

    except Exception as e:
        print(f"下单失败: {str(e)}")
        return {"status": "error", "message": str(e)}
