import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- CONFIG ---------------- #

NEWS_API_KEY = "164c2853c0d54e62931727c86396f99d"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
REFRESH_INTERVAL = 30000  # 30 seconds

STOCKS = {
    "Tata Consultancy Services": ("TCS.NS", "Tata Consultancy Services Ltd"),
    "Reliance Industries": ("RELIANCE.NS", "Reliance Industries Ltd"),
    "HDFC Bank": ("HDFCBANK.NS", "HDFC Bank Ltd"),
    "State Bank of India": ("SBIN.NS", "State Bank of India"),
    "ICICI Bank": ("ICICIBANK.NS", "ICICI Bank Ltd")
}

# ---------------- GUI APP ---------------- #

class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Indian Stock Tracker")
        self.root.geometry("1200x700")

        self.selected_stock = tk.StringVar()
        self.alert_threshold = tk.IntVar(value=5)

        self.create_widgets()
        self.auto_refresh()

    # ---------------- UI ---------------- #

    def create_widgets(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="Select Company:").pack(side="left")
        self.company_cb = ttk.Combobox(
            top_frame,
            textvariable=self.selected_stock,
            values=list(STOCKS.keys()),
            state="readonly",
            width=30
        )
        self.company_cb.pack(side="left", padx=10)
        self.company_cb.current(0)

        ttk.Label(top_frame, text="Alert Threshold (%):").pack(side="left")
        ttk.Combobox(
            top_frame,
            textvariable=self.alert_threshold,
            values=[3, 5, 10],
            width=5,
            state="readonly"
        ).pack(side="left", padx=5)

        ttk.Button(top_frame, text="Refresh", command=self.update_data).pack(side="left", padx=10)

        # Table
        self.tree = ttk.Treeview(self.root, columns=("Date", "Open", "High", "Low", "Close"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill="x", padx=10, pady=5)

        # Chart
        self.figure = plt.Figure(figsize=(6, 4))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        # News
        news_frame = ttk.LabelFrame(self.root, text="Latest News")
        news_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        self.news_text = tk.Text(news_frame, wrap="word", height=20)
        self.news_text.pack(fill="both", expand=True)

    # ---------------- DATA ---------------- #

    def update_data(self):
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.news_text.delete("1.0", tk.END)

        symbol, company_name = STOCKS[self.selected_stock.get()]
        stock = yf.Ticker(symbol)

        data = stock.history(period="1mo")

        # Table data (last 5 days)
        for index, row in data.tail(5).iterrows():
            self.tree.insert("", "end", values=(
                index.date(),
                round(row["Open"], 2),
                round(row["High"], 2),
                round(row["Low"], 2),
                round(row["Close"], 2)
            ))

        # Chart
        self.ax.plot(data.index, data["Close"])
        self.ax.set_title(f"{symbol} - 1 Month Trend")
        self.ax.set_ylabel("Price")
        self.canvas.draw()

        # Percentage change
        today_close = data["Close"].iloc[-1]
        yesterday_close = data["Close"].iloc[-2]
        diff_percent = ((today_close - yesterday_close) / yesterday_close) * 100

        if abs(diff_percent) >= self.alert_threshold.get():
            messagebox.showwarning(
                "Stock Alert",
                f"{symbol} moved {diff_percent:.2f}%"
            )
            self.fetch_news(company_name)

    def fetch_news(self, company_name):
        params = {
            "apiKey": NEWS_API_KEY,
            "q": company_name,
            "language": "en",
            "sortBy": "publishedAt"
        }
        response = requests.get(NEWS_ENDPOINT, params=params)
        articles = response.json().get("articles", [])[:3]

        for article in articles:
            self.news_text.insert(tk.END, f"📰 {article['title']}\n")
            self.news_text.insert(tk.END, f"{article['description']}\n\n")

    # ---------------- AUTO REFRESH ---------------- #

    def auto_refresh(self):
        self.update_data()
        self.root.after(REFRESH_INTERVAL, self.auto_refresh)


# ---------------- RUN ---------------- #

root = tk.Tk()
app = StockApp(root)
root.mainloop()
