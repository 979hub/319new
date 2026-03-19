from fastapi import FastAPI, Request, HTTPException
from binance.client import Client
import os
import uvicorn

app = FastAPI()

# --- 配置 (从 claw.cloud 环境变量读取) ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
WEBHOOK_PASSPHRASE = os.getenv("WEBHOOK_PASSPHRASE", "ss9")

# 初始化币安客户端
client = Client(API_KEY, API_SECRET)

@app.get("/")
def home():
    return {"status": "online"}

@app.post("/webhook")
async def webhook(request: Request):
    # 1. 直接获取原始 JSON，不进行严格格式校验，防止多字段报错
    data = await request.json()
    
    # 2. 提取核心 4 个字段
    passphrase = data.get("passphrase")
    symbol = data.get("symbol")
    side = data.get("side") # buy 或 sell
    amount = data.get("amount") # 开仓金额 (USDT)

    # 3. 验证密码
    if passphrase != WEBHOOK_PASSPHRASE:
        return {"status": "error", "msg": "wrong password"}

    print(f"收到指令: {symbol} | 方向: {side} | 金额: {amount} USDT")

    # 4. 强制执行【市价成交】 (Market Order)
    try:
        side_type = Client.SIDE_BUY if side.lower() == "buy" else Client.SIDE_SELL
        
        # 使用 quoteOrderQty，直接花指定的 USDT 金额买入/卖出，不传价格
        order = client.create_order(
            symbol=symbol.upper(),
            side=side_type,
            type=Client.ORDER_TYPE_MARKET,
            quoteOrderQty=amount
        )
        
        print(f"市价成交成功: ID {order['orderId']}")
        return {"status": "success", "id": order['orderId']}

    except Exception as e:
        print(f"下单失败: {str(e)}")
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
