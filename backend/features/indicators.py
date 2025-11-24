"""
Technical indicators for stock data analysis.

Implements various technical indicators including:
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- ATR (Average True Range)
- ADX (Average Directional Index)
- Momentum
- Volatility
- OBV (On-Balance Volume)
"""
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        series: Price series (typically close prices)
        period: Number of periods for the moving average
        
    Returns:
        Series with SMA values
    """
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        series: Price series (typically close prices)
        period: Number of periods for the EMA
        
    Returns:
        Series with EMA values
    """
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.
    
    RSI = 100 - (100 / (1 + RS))
    where RS = average gain / average loss over the period
    
    Args:
        series: Price series (typically close prices)
        period: Number of periods (default: 14)
        
    Returns:
        Series with RSI values (0-100)
    """
    # Calculate price changes
    delta = series.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    
    # Calculate average gain and loss using EMA
    avg_gain = gains.ewm(span=period, adjust=False, min_periods=period).mean()
    avg_loss = losses.ewm(span=period, adjust=False, min_periods=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi_values = 100.0 - (100.0 / (1.0 + rs))
    
    # Handle division by zero (when avg_loss is 0)
    rsi_values = rsi_values.fillna(100.0)
    
    return rsi_values


def macd(series: pd.Series, fast_period: int = 12, slow_period: int = 26, 
         signal_period: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal_period)
    Histogram = MACD Line - Signal Line
    
    Args:
        series: Price series (typically close prices)
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    # Calculate fast and slow EMAs
    ema_fast = ema(series, fast_period)
    ema_slow = ema(series, slow_period)
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate signal line
    signal_line = ema(macd_line, signal_period)
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.
    
    True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
    ATR = EMA of True Range
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Number of periods (default: 14)
        
    Returns:
        Series with ATR values
    """
    # Calculate true range components
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    # True range is the maximum of the three
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR as EMA of true range
    atr_values = true_range.ewm(span=period, adjust=False, min_periods=period).mean()
    
    return atr_values


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index.
    
    ADX measures trend strength (not direction).
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: Number of periods (default: 14)
        
    Returns:
        Series with ADX values (0-100)
    """
    # Calculate +DM and -DM
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0.0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0.0)
    
    # Calculate ATR
    atr_values = atr(high, low, close, period)
    
    # Calculate +DI and -DI
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr_values)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr_values)
    
    # Calculate DX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    dx = dx.fillna(0.0)
    
    # Calculate ADX as EMA of DX
    adx_values = dx.ewm(span=period, adjust=False, min_periods=period).mean()
    
    return adx_values


def momentum(series: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Momentum indicator.
    
    Momentum = (Current Price - Price N periods ago) / Price N periods ago * 100
    
    Args:
        series: Price series (typically close prices)
        period: Number of periods to look back (default: 20)
        
    Returns:
        Series with momentum values (percentage change)
    """
    shifted = series.shift(period)
    # Avoid division by zero
    return ((series - shifted) / shifted.replace(0, np.nan)) * 100


def volatility(series: pd.Series, period: int = 30) -> pd.Series:
    """
    Calculate rolling volatility (standard deviation).
    
    Args:
        series: Price series (typically close prices or returns)
        period: Number of periods for rolling window (default: 30)
        
    Returns:
        Series with volatility values
    """
    return series.rolling(window=period, min_periods=period).std()


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Calculate On-Balance Volume.
    
    OBV = cumulative sum of volume when price goes up,
          minus volume when price goes down
    
    Args:
        close: Close prices
        volume: Volume
        
    Returns:
        Series with OBV values
    """
    # Calculate price direction
    price_change = close.diff()
    
    # Volume is positive when price goes up, negative when down
    obv_values = volume.where(price_change > 0, 0) - volume.where(price_change < 0, 0)
    
    # Cumulative sum
    obv_values = obv_values.cumsum()
    
    return obv_values


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators for a DataFrame.
    
    Expected DataFrame columns:
    - close: Close price (required)
    - high: High price (required for ATR, ADX)
    - low: Low price (required for ATR, ADX)
    - volume: Volume (required for OBV)
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all indicator columns added
    """
    result = df.copy()
    
    # SMA indicators
    result['sma_10'] = sma(df['close'], 10)
    result['sma_50'] = sma(df['close'], 50)
    result['sma_200'] = sma(df['close'], 200)
    
    # EMA indicators
    result['ema_20'] = ema(df['close'], 20)
    result['ema_50'] = ema(df['close'], 50)
    
    # RSI
    result['rsi_14'] = rsi(df['close'], 14)
    
    # MACD
    macd_line, signal_line, histogram = macd(df['close'], 12, 26, 9)
    result['macd'] = macd_line
    result['macd_signal'] = signal_line
    result['macd_histogram'] = histogram
    
    # ATR (requires high, low, close)
    if 'high' in df.columns and 'low' in df.columns:
        result['atr_14'] = atr(df['high'], df['low'], df['close'], 14)
        # ATR-based volatility (normalized by price)
        result['atr_volatility'] = result['atr_14'] / df['close']
    
    # ADX (requires high, low, close)
    if 'high' in df.columns and 'low' in df.columns:
        result['adx_14'] = adx(df['high'], df['low'], df['close'], 14)
    
    # Momentum
    result['momentum_20'] = momentum(df['close'], 20)
    
    # Volatility (standard deviation)
    result['volatility_30'] = volatility(df['close'], 30)
    
    # OBV (requires volume)
    if 'volume' in df.columns:
        result['obv'] = obv(df['close'], df['volume'])
    
    return result
