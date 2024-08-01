import json
import threading
import statistics
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.dates import date2num
from websocket import WebSocketApp, enableTrace
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# WebSocket設定
enableTrace(True)
ws_url = 'wss://forex-api.coin.z.com/ws/public/v1'

ask_list = []
bid_list = []
time_list = []

def calculate_difference_and_percentage(new_value, previous_value):
    if previous_value is None:
        return "N/A"
    
    difference = new_value - previous_value
    abs_difference = abs(difference)
    percentage = (abs_difference / previous_value) * 100 if previous_value != 0 else 0
    
    if difference > 0:
        return (f"{abs_difference:.3f}({percentage:.3f}%)☝", "green")  # 差分と色
    elif difference < 0:
        return (f"{abs_difference:.3f}({percentage:.3f}%)☟", "red")    # 差分と色
    else:
        return (f"{abs_difference:.3f}", "black")   # 絵文字なし

def on_open(ws):
 subscribe_to_symbol()

def on_message(ws, message):
    data = json.loads(message)
    
    symbol = data.get('symbol', '')
    ask = float(data.get('ask', 0))
    bid = float(data.get('bid', 0))
    timestamp = data.get('timestamp', 'N/A')
    status = data.get('status', '')

    if timestamp == 'N/A':
        formatted_timestamp = '取得時刻: 不明'
    else:
        try:
            timestamp_datetime = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_timestamp = timestamp_datetime.strftime('%Y年%m月%d日(%A)%H時%M分%S秒%fミリ秒')
            formatted_timestamp = formatted_timestamp.replace("Monday", "月曜日").replace("Tuesday", "火曜日").replace("Wednesday", "水曜日")
            formatted_timestamp = formatted_timestamp.replace("Thursday", "木曜日").replace("Friday", "金曜日").replace("Saturday", "土曜日").replace("Sunday", "日曜日")
        except ValueError:
            formatted_timestamp = '取得時刻: 無効なフォーマット'

    if ask_list:
        ask_diff, ask_color = calculate_difference_and_percentage(ask, ask_list[-1])
    else:
        ask_diff, ask_color = ("N/A", "black")

    if bid_list:
        bid_diff, bid_color = calculate_difference_and_percentage(bid, bid_list[-1])
    else:
        bid_diff, bid_color = ("N/A", "black")

    ask_list.append(ask)
    bid_list.append(bid)
    time_list.append(datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp != 'N/A' else datetime.now())

    ask_label.config(text=f"買値(Ask): {ask}円 ({ask_diff}) 平均値:{statistics.mean(ask_list):.5f}円" , fg=ask_color)
    bid_label.config(text=f"売値(Bid): {bid}円 ({bid_diff}) 平均値:{statistics.mean(bid_list):.5f}円", fg=bid_color)
    timestamp_label.config(text=f"取得時刻: {formatted_timestamp}")
    
    # Transaction_Information_labelの更新
    if status == "OPEN":
        transaction_status = "現在、市場が開いています。(月曜日7:00〜土曜日5:59)"
    elif status == "CLOSE":
        transaction_status = "現在、市場が休場しています。"
    else:
        transaction_status = "不明"
    
    Transaction_Information_label.config(text=f"{symbol} - {transaction_status}")
    
    message_text.insert(tk.END, f"{message}\n")
    message_text.see(tk.END)  # スクロールを最下部に
    update_graph()

def update_graph():
    ax.clear()
    
    if not time_list or not ask_list or not bid_list:
        return  # データがない場合は更新しない
    
    time_num = [date2num(t) for t in time_list]
    
    ax.plot(time_num, ask_list, linestyle='-', color='blue', linewidth=2, label='Ask')
    ax.plot(time_num, bid_list, linestyle='-', color='red', linewidth=2, label='Bid')

    # x軸とy軸のラベルを非表示
    ax.set_xlabel('')
    ax.set_ylabel('')

    # x軸とy軸の目盛りとラベルを非表示
    ax.xaxis.set_visible(False)  # x軸を非表示
    ax.yaxis.set_visible(False)  # y軸を非表示
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
    
    fig.autofmt_xdate()
    ax.legend()
    canvas.draw()

def subscribe_to_symbol():
        message = {"command": "subscribe", "channel": "ticker", "symbol": "USD_JPY"}
        if ws.sock and ws.sock.connected:
            ws.send(json.dumps(message))
        else:
            print("WebSocket connection is not open")

def update_subscription():
    subscribe_to_symbol()  

root = tk.Tk()
root.title("GMOコインWebsocket為替レートモニター -USD/JPY-")
root.resizable(False, False)
root.geometry("800x700")  # 幅 x 高さ

# フォントサイズの定義
font_size = (18)

# 上部のフレーム
top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X)

# Transaction_Information_labelと入力ボックス用のフレーム
info_frame = tk.Frame(top_frame)
info_frame.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=10)

Transaction_Information_label = tk.Label(info_frame, text="", font=font_size)
Transaction_Information_label.pack(side=tk.LEFT, anchor='w', padx=0, pady=1)

# ラベルの追加
ask_label = tk.Label(root, text="Ask: ", font=font_size)
ask_label.pack(side=tk.TOP, anchor='w', padx=10, pady=1)

bid_label = tk.Label(root, text="Bid: ", font=font_size)
bid_label.pack(side=tk.TOP, anchor='w', padx=10, pady=1)

timestamp_label = tk.Label(root, text="Timestamp: ", font=font_size)
timestamp_label.pack(side=tk.TOP, anchor='w', padx=10, pady=1)

# グラフとメッセージテキスト用のフレームを作成
frame = tk.Frame(root)
frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# matplotlibの図と軸を作成
fig = Figure(figsize=(8, 3), dpi=100)
ax = fig.add_subplot()

# matplotlibの図を作成してパック
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# メッセージテキストエリアを追加
message_text = scrolledtext.ScrolledText(frame, width=80, height=10, wrap=tk.WORD, font=font_size)
message_text.pack(side=tk.BOTTOM, padx=10, pady=10, fill=tk.BOTH, expand=True)

# WebSocket接続を別スレッドで開始
ws = WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
thread = threading.Thread(target=ws.run_forever)
thread.daemon = True
thread.start()

# Tkinterのメインループを開始
root.mainloop()
