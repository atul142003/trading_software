from backtesting import Strategy

class EMARSIMACDStrategy(Strategy):

    def init(self):
        pass

    def next(self):

        if len(self.data.Close) < 50:
            return

        ema20 = self.data.EMA20[-1]
        ema50 = self.data.EMA50[-1]
        ema200 = self.data.EMA200[-1]

        rsi = self.data.RSI[-1]
        macd = self.data.MACD[-1]

        price = self.data.Close[-1]

        # ======================
        # ENTRY
        # ======================

        buy_signal = (
            ema20 > ema50
            and ema50 > ema200
            and rsi > 50
            and macd > 0
        )

        sell_signal = (
            ema20 < ema50
            and ema50 < ema200
            and rsi < 50
            and macd < 0
        )

        # ======================
        # RISK MANAGEMENT
        # ======================

        stop_loss_pct = 0.02   # 2%
        take_profit_pct = 0.04 # 4%

        # BUY
        if buy_signal and not self.position:
            self.buy()
            self.entry_price = price

        # EXIT CONDITIONS
        if self.position:

            # Stop Loss
            if price < self.entry_price * (1 - stop_loss_pct):
                self.position.close()

            # Take Profit
            elif price > self.entry_price * (1 + take_profit_pct):
                self.position.close()

            # Trend reversal exit
            elif sell_signal:
                self.position.close()