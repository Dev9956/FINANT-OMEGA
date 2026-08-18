//! FININT OMEGA — Technical indicators.

/// Simple Moving Average.
pub fn sma(prices: &[f64], period: usize) -> Vec<Option<f64>> {
    if prices.is_empty() || period == 0 {
        return vec![];
    }
    let mut result = vec![None; prices.len()];
    for i in (period - 1)..prices.len() {
        let sum: f64 = prices[(i + 1 - period)..=i].iter().sum();
        result[i] = Some(sum / period as f64);
    }
    result
}

/// Exponential Moving Average.
pub fn ema(prices: &[f64], period: usize) -> Vec<Option<f64>> {
    if prices.is_empty() || period == 0 {
        return vec![];
    }
    let mut result = vec![None; prices.len()];
    let multiplier = 2.0 / (period as f64 + 1.0);
    // First EMA value is SMA
    let sum: f64 = prices[..period].iter().sum();
    result[period - 1] = Some(sum / period as f64);
    for i in period..prices.len() {
        let prev = result[i - 1].unwrap_or(0.0);
        result[i] = Some((prices[i] - prev) * multiplier + prev);
    }
    result
}

/// Relative Strength Index.
pub fn rsi(prices: &[f64], period: usize) -> Vec<Option<f64>> {
    if prices.len() < period + 1 {
        return vec![None; prices.len()];
    }
    let mut result = vec![None; prices.len()];
    let returns = super::returns::simple_returns(prices).unwrap_or_default();
    if returns.len() < period {
        return vec![None; prices.len()];
    }
    let mut avg_gain = 0.0;
    let mut avg_loss = 0.0;
    for i in 0..period {
        if returns[i] > 0.0 {
            avg_gain += returns[i];
        } else {
            avg_loss += -returns[i];
        }
    }
    avg_gain /= period as f64;
    avg_loss /= period as f64;
    if avg_loss == 0.0 {
        result[period] = Some(100.0);
    } else {
        let rs = avg_gain / avg_loss;
        result[period] = Some(100.0 - 100.0 / (1.0 + rs));
    }
    for i in period..returns.len() {
        let gain = if returns[i] > 0.0 { returns[i] } else { 0.0 };
        let loss = if returns[i] < 0.0 { -returns[i] } else { 0.0 };
        avg_gain = (avg_gain * (period as f64 - 1.0) + gain) / period as f64;
        avg_loss = (avg_loss * (period as f64 - 1.0) + loss) / period as f64;
        if avg_loss == 0.0 {
            result[i + 1] = Some(100.0);
        } else {
            let rs = avg_gain / avg_loss;
            result[i + 1] = Some(100.0 - 100.0 / (1.0 + rs));
        }
    }
    result
}

/// Bollinger Bands: returns (upper, middle, lower).
pub fn bollinger_bands(
    prices: &[f64],
    period: usize,
    num_std: f64,
) -> (Vec<Option<f64>>, Vec<Option<f64>>, Vec<Option<f64>>) {
    let middle = sma(prices, period);
    let mut upper = vec![None; prices.len()];
    let mut lower = vec![None; prices.len()];
    for i in (period - 1)..prices.len() {
        if let Some(mid) = middle[i] {
            let window = &prices[(i + 1 - period)..=i];
            let mean = mid;
            let variance: f64 = window.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / period as f64;
            let std = variance.sqrt();
            upper[i] = Some(mid + num_std * std);
            lower[i] = Some(mid - num_std * std);
        }
    }
    (upper, middle, lower)
}

/// MACD: returns (macd_line, signal_line, histogram).
pub fn macd(
    prices: &[f64],
    fast: usize,
    slow: usize,
    signal: usize,
) -> (Vec<Option<f64>>, Vec<Option<f64>>, Vec<Option<f64>>) {
    let ema_fast = ema(prices, fast);
    let ema_slow = ema(prices, slow);
    let mut macd_line = vec![None; prices.len()];
    for i in 0..prices.len() {
        if let (Some(f), Some(s)) = (ema_fast[i], ema_slow[i]) {
            macd_line[i] = Some(f - s);
        }
    }
    // Signal line: EMA of MACD line
    let macd_values: Vec<f64> = macd_line.iter().filter_map(|&v| v).collect();
    let signal_ema = if macd_values.len() >= signal {
        ema(&macd_values, signal)
    } else {
        vec![None; macd_values.len()]
    };
    let mut signal_line = vec![None; prices.len()];
    let mut j = 0;
    for i in 0..prices.len() {
        if macd_line[i].is_some() {
            if j < signal_ema.len() {
                signal_line[i] = signal_ema[j];
            }
            j += 1;
        }
    }
    let mut histogram = vec![None; prices.len()];
    for i in 0..prices.len() {
        if let (Some(m), Some(s)) = (macd_line[i], signal_line[i]) {
            histogram[i] = Some(m - s);
        }
    }
    (macd_line, signal_line, histogram)
}

/// Average True Range.
pub fn atr(
    highs: &[f64],
    lows: &[f64],
    closes: &[f64],
    period: usize,
) -> Vec<Option<f64>> {
    let n = highs.len().min(lows.len()).min(closes.len());
    if n < 2 || period == 0 {
        return vec![None; n];
    }
    let mut tr = vec![0.0; n];
    tr[0] = highs[0] - lows[0];
    for i in 1..n {
        let hl = highs[i] - lows[i];
        let hc = (highs[i] - closes[i - 1]).abs();
        let lc = (lows[i] - closes[i - 1]).abs();
        tr[i] = hl.max(hc).max(lc);
    }
    let mut result = vec![None; n];
    if n >= period {
        let sum: f64 = tr[..period].iter().sum();
        result[period - 1] = Some(sum / period as f64);
        for i in period..n {
            let prev = result[i - 1].unwrap_or(0.0);
            result[i] = Some((prev * (period as f64 - 1.0) + tr[i]) / period as f64);
        }
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    fn test_prices() -> Vec<f64> {
        vec![100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 109.0]
    }

    #[test]
    fn test_sma() {
        let prices = test_prices();
        let result = sma(&prices, 3);
        assert_eq!(result.len(), 10);
        assert!(result[0].is_none());
        assert!(result[1].is_none());
        assert_relative_eq!(result[2].unwrap(), (100.0 + 102.0 + 101.0) / 3.0);
    }

    #[test]
    fn test_ema() {
        let prices = test_prices();
        let result = ema(&prices, 3);
        assert_eq!(result.len(), 10);
        assert!(result[0].is_none());
        assert!(result[1].is_none());
        assert!(result[2].is_some());
        assert!(result[3].is_some());
    }

    #[test]
    fn test_rsi_uptrend() {
        let prices: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = rsi(&prices, 14);
        assert!(result[19].is_some());
        assert!(result[19].unwrap() > 50.0);
    }

    #[test]
    fn test_bollinger_bands() {
        let prices = test_prices();
        let (upper, mid, lower) = bollinger_bands(&prices, 5, 2.0);
        assert!(upper[4].is_some());
        assert!(lower[4].is_some());
        assert!(upper[4].unwrap() > mid[4].unwrap());
        assert!(lower[4].unwrap() < mid[4].unwrap());
    }

    #[test]
    fn test_macd() {
        let prices: Vec<f64> = (0..50).map(|i| 100.0 + i as f64 * 0.5).collect();
        let (macd_line, signal, hist) = macd(&prices, 12, 26, 9);
        assert!(macd_line[49].is_some());
        assert!(signal[49].is_some());
        assert!(hist[49].is_some());
    }

    #[test]
    fn test_atr() {
        let highs = vec![105.0, 110.0, 108.0, 112.0, 115.0];
        let lows = vec![95.0, 100.0, 98.0, 102.0, 105.0];
        let closes = vec![100.0, 105.0, 103.0, 108.0, 110.0];
        let result = atr(&highs, &lows, &closes, 3);
        assert!(result[2].is_some());
        assert!(result[2].unwrap() > 0.0);
    }
}
