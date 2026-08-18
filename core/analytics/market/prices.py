"""FININT OMEGA — Market price analytics."""

from __future__ import annotations

from datetime import date

from core.data.schemas import MarketOHLCV


class MarketPriceAnalyzer:
    """Analyzes market OHLCV data."""

    def compute_returns(self, prices: list[float]) -> list[float]:
        """Compute simple returns from a list of prices."""
        if len(prices) < 2:
            return []
        return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]

    def compute_log_returns(self, prices: list[float]) -> list[float]:
        """Compute log returns from a list of prices."""
        import math
        if len(prices) < 2:
            return []
        return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices)) if prices[i - 1] > 0]

    def compute_cagr(self, prices: list[float]) -> float | None:
        """Compute CAGR from a list of prices."""
        if len(prices) < 2 or prices[0] <= 0:
            return None
        years = len(prices) - 1
        return (prices[-1] / prices[0]) ** (1 / years) - 1

    def compute_volatility(self, returns: list[float], annualize: bool = True) -> float | None:
        """Compute volatility from returns."""
        if len(returns) < 2:
            return None
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        vol = variance ** 0.5
        if annualize:
            vol *= 252 ** 0.5
        return vol

    def compute_max_drawdown(self, prices: list[float]) -> float | None:
        """Compute maximum drawdown from prices."""
        if not prices:
            return None
        peak = prices[0]
        max_dd = 0.0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def compute_sharpe_ratio(
        self, returns: list[float], risk_free_rate: float = 0.05
    ) -> float | None:
        """Compute Sharpe ratio."""
        if not returns:
            return None
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std = variance ** 0.5
        if std == 0:
            return None
        daily_rf = risk_free_rate / 252
        return (mean_return - daily_rf) / std * 252 ** 0.5

    def compute_vwap(self, ohlcv: list[MarketOHLCV]) -> list[float]:
        """Compute Volume Weighted Average Price for each bar."""
        vwap_values = []
        cumulative_volume = 0
        cumulative_tpv = 0.0
        for bar in ohlcv:
            typical_price = (bar.high + bar.low + bar.close) / 3
            cumulative_tpv += typical_price * bar.volume
            cumulative_volume += bar.volume
            vwap = cumulative_tpv / cumulative_volume if cumulative_volume > 0 else 0
            vwap_values.append(vwap)
        return vwap_values

    def compute_sma(self, prices: list[float], period: int) -> list[float | None]:
        """Compute Simple Moving Average."""
        result = [None] * len(prices)
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1 : i + 1]
            result[i] = sum(window) / period
        return result

    def compute_ema(self, prices: list[float], period: int) -> list[float | None]:
        """Compute Exponential Moving Average."""
        if not prices or period < 1:
            return [None] * len(prices)
        result = [None] * len(prices)
        multiplier = 2 / (period + 1)
        # Start with SMA for first value
        result[period - 1] = sum(prices[:period]) / period
        for i in range(period, len(prices)):
            result[i] = (prices[i] - result[i - 1]) * multiplier + result[i - 1]
        return result

    def compute_rsi(self, prices: list[float], period: int = 14) -> list[float | None]:
        """Compute Relative Strength Index."""
        if len(prices) < period + 1:
            return [None] * len(prices)
        returns = self.compute_returns(prices)
        result = [None] * len(prices)
        gains = []
        losses = []
        for r in returns[:period]:
            gains.append(max(r, 0))
            losses.append(max(-r, 0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            result[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[period] = 100 - 100 / (1 + rs)
        for i in range(period, len(returns)):
            gain = max(returns[i], 0)
            loss = max(-returns[i], 0)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            if avg_loss == 0:
                result[i + 1] = 100.0
            else:
                rs = avg_gain / avg_loss
                result[i + 1] = 100 - 100 / (1 + rs)
        return result

    def compute_bollinger_bands(
        self, prices: list[float], period: int = 20, num_std: float = 2.0
    ) -> tuple[list[float | None], list[float | None], list[float | None]]:
        """Compute Bollinger Bands (upper, middle, lower)."""
        sma = self.compute_sma(prices, period)
        upper = [None] * len(prices)
        lower = [None] * len(prices)
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1 : i + 1]
            mean = sma[i]
            std = (sum((x - mean) ** 2 for x in window) / period) ** 0.5
            upper[i] = mean + num_std * std
            lower[i] = mean - num_std * std
        return upper, sma, lower

    def compute_macd(
        self, prices: list[float], fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[list[float | None], list[float | None], list[float | None]]:
        """Compute MACD (line, signal, histogram)."""
        ema_fast = self.compute_ema(prices, fast)
        ema_slow = self.compute_ema(prices, slow)
        macd_line = [None] * len(prices)
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line[i] = ema_fast[i] - ema_slow[i]
        # Signal line is EMA of MACD line
        macd_values = [v for v in macd_line if v is not None]
        if len(macd_values) >= signal:
            signal_ema = self.compute_ema(macd_values, signal)
        else:
            signal_ema = [None] * len(macd_values)
        signal_line = [None] * len(prices)
        j = 0
        for i in range(len(prices)):
            if macd_line[i] is not None:
                if j < len(signal_ema):
                    signal_line[i] = signal_ema[j]
                j += 1
        histogram = [None] * len(prices)
        for i in range(len(prices)):
            if macd_line[i] is not None and signal_line[i] is not None:
                histogram[i] = macd_line[i] - signal_line[i]
        return macd_line, signal_line, histogram
