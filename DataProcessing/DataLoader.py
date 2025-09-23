import os,logging
import pandas as pd
import numpy as np
from DataLoad import getData
logging.basicConfig(level=logging.INFO,  # You can use DEBUG, INFO, WARNING, ERROR, CRITICAL
                    format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')

logger=logging.getLogger(__name__)
class StocksLoader:
    def __init__(self, stock_symbol=None,ndays=5,addComadity=False,comptidypath="StockData/INDEXData/Comudities.csv"):
        """
        Initialize the StocksLoader with a stock symbol.
        
        Args:
            stock_symbol (str, optional): Stock symbol (e.g., "HDFCBANK")
        """
        self.stock_symbol = stock_symbol
        self.labeled_data = None
        self.Benchmark_Close = "NIFTY50_Close"
        self.ndays=ndays
        self.addComadity=False
        self.comptidypath=comptidypath
        self.load_comadity()
        self.load_data()


    def load_comadity(self):
        self.comadity=None
        if self.comptidypath is None:
            print("Comadity is None so not using")
        elif not os.path.exists(self.comptidypath):
            print(f"Comadity file {self.comptidypath} not exists")
        else:
            self.comadity=pd.read_csv(self.comptidypath)
            self.comadity["Date"]=pd.to_datetime(self.comadity["Date"])
            self.comadity=self.comadity.set_index("Date")
            self.comadity=self.comadity.drop(columns=["NIFTY50_Adj Close","gold_Adj Close","crude_Adj Close"])
            self.comadity=self.comadity.dropna(how="all")

    def load_StockData(self,stock_Symbol):
        # Get data using DataLoad.getData
        stock_data = getData(stock_Symbol)
        stock_data.index=pd.to_datetime(stock_data.index)
        stock_data["Adj Close"]=stock_data["Adj Close"].fillna(stock_data["Close"])
        return stock_data

    def load_data(self):
        """
        Load stock data using DataLoad.getData.
        
        Args:
            stock_symbol (str, optional): Stock symbol to load. If None, uses self.stock_symbol
            
        Returns:
            pd.DataFrame: Loaded stock data
        """            
        assert self.stock_symbol is not None, "No stock symbol provided"
        self.stock_data=self.load_StockData(self.stock_symbol)
        if self.comadity is not None:
            self.stock_data=self.stock_data.merge(self.comadity,left_index=True,right_index=True,how="left")
        # self.prepare_data(self.ndays)
        self.Labels=pd.DataFrame()
        self.label_data(methods=["combined","quantile","risk_adjusted","dynamic"])
        self.stock_data=self.stock_data[filter(lambda x:x not in self.comadity, self.stock_data.columns)]
        self.stock_data=self.stock_data.ffill()
        self.stock_data.to_csv(f"Data.csv")
        self.Labels.to_csv(f"Label.csv")


    
    def get_future_return(self, df, window=5):
        """
        Calculate future returns over a window (forward return).
        
        Args:
            df (pd.DataFrame): Input dataframe
            window (int): Number of days for future return calculation
            
        Returns:
            pd.DataFrame: Dataframe with future returns
        """
        df = df.copy()
        df['Future_Close'] = df['Close'].shift(-window)
        # Calculate forward return (percentage change over the window)
        df['Future_Return'] = (df['Future_Close'] / df['Close']) - 1
        return (df['Future_Close'] / df['Close']) - 1

    
    def label_combined(self, df, fixed_threshold=0.03, relative_margin=0.02):
        """
        Labels a day as 1 if:
          - Future return >= fixed_threshold, and
          - Future return exceeds the benchmark's return by relative_margin.
        """
        # df = df.copy()
        # Calculate benchmark future return
        self.Labels["Future_Return"] = self.get_future_return(df,self.ndays)
        Benchmark_Future_Close = df[self.Benchmark_Close].shift(-5)
        Benchmark_Future_Return= (Benchmark_Future_Close / df[self.Benchmark_Close]) - 1

        # Label if stock's future return exceeds both fixed threshold and benchmark + margin
        conditions = (self.Labels["Future_Return"] >= fixed_threshold) & \
                     (self.Labels["Future_Return"] >= Benchmark_Future_Return + relative_margin)
        self.Labels['Label_Combined'] = np.where(conditions, 1, 0)
        return self.Labels
    
    def label_quantile(self, df, quantile=0.8):
        """
        Labels a day as 1 if the stock's future return is in the top quantile among all stocks on that day.
        """
        # df = df.copy()

        # For each day, compute the quantile cutoff for Future_Return
        def quantile_label(group):
            threshold = group['Future_Return'].quantile(quantile)
            group['Label_Quantile'] = np.where(group['Future_Return'] >= threshold, 1, 0)
            return group
        self.Labels = self.Labels.groupby(level=0).apply(quantile_label)
        return self.Labels
    
    def label_risk_adjusted(self, df, return_threshold=0.03, risk_multiple=1.0, risk_window=20):
        """
        Labels a day as 1 if the future return is above a return threshold adjusted for risk.
        Risk is estimated as the rolling standard deviation of past returns.
        """
        # df = df.copy()
        # Calculate daily returns (historical)
        self.Labels['Daily_Return'] = df['Close'].pct_change()
        # Rolling volatility over past risk_window days
        self.Labels['Volatility'] = self.Labels['Daily_Return'].rolling(risk_window).std()
        # Fill missing volatility with a small number to avoid NaNs
        self.Labels['Volatility'] = self.Labels['Volatility'].fillna(0)

        # Adjust threshold for risk
        self.Labels['Risk_Adjusted_Threshold'] = return_threshold + risk_multiple * self.Labels['Volatility']

        conditions = (self.Labels['Future_Return'] >= self.Labels['Risk_Adjusted_Threshold'])
        self.Labels['Label_RiskAdjusted'] = np.where(conditions, 1, 0)
        return self.Labels
    
    def label_dynamic_threshold(self, df, base_threshold=0.03, dynamic_factor=1.5, risk_window=20):
        """
        Uses historical volatility to dynamically adjust the threshold.
        """
        # df = df.copy()
        # Calculate daily returns (historical)
        self.Labels['Daily_Return'] = df['Close'].pct_change()
        self.Labels['Volatility'] = self.Labels['Daily_Return'].rolling(risk_window).std()
        self.Labels['Volatility'] = self.Labels['Volatility'].fillna(0)

        # Dynamic threshold adjusted for volatility
        self.Labels['Dynamic_Threshold'] = base_threshold * (1 + dynamic_factor * self.Labels['Volatility'])
        conditions = (self.Labels['Future_Return'] >= self.Labels['Dynamic_Threshold'])
        self.Labels['Label_Dynamic'] = np.where(conditions, 1, 0)
        return self.Labels
    
    def label_data(self, methods=['combined','quantile','risk_adjusted','dynamic'], **kwargs):
        """
        Label the data using specified method.
        
        Args:
            method (str): Labeling method to use ('combined', 'quantile', 'risk_adjusted', 'dynamic')
            **kwargs: Additional parameters for the labeling method
            
        Returns:
            pd.DataFrame: Labeled data
        """
        if self.stock_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
            
            
        labeling_methods = {
            'combined': self.label_combined,
            'quantile': self.label_quantile,
            'risk_adjusted': self.label_risk_adjusted,
            'dynamic': self.label_dynamic_threshold
        }
        
        for method in methods:
            if method not in labeling_methods:
                raise ValueError(f"Unknown labeling method: {method}")
            labeling_methods[method](self.stock_data, **kwargs)
        
    def get_labeled_data(self):
        """
        Get the labeled data.
        
        Returns:
            pd.DataFrame: Labeled data
        """
        if self.labeled_data is None:
            raise ValueError("No labeled data available. Call label_data() first.")
        return self.labeled_data
    
    def load_and_label(self, stock_symbol=None, window=5, method='combined', **kwargs):
        """
        Load data, prepare it, and label it in one step.
        
        Args:
            stock_symbol (str, optional): Stock symbol to load
            window (int): Number of days for future return calculation
            method (str): Labeling method to use
            **kwargs: Additional parameters for the labeling method
            
        Returns:
            pd.DataFrame: Labeled data
        """
        self.load_data(stock_symbol)
        self.prepare_data(window)
        return self.label_data(method, **kwargs)
    
    
    def __getitem__(self, idx):
        """
        Get a slice of data using sliding window.
        
        Args:
            idx (int or slice): Index or slice of data to get
            
        Returns:
            pd.DataFrame: Slice of the labeled data
        """
        if self.labeled_data is None:
            raise ValueError("No labeled data available. Call load_and_label() first.")
            
        if isinstance(idx, int):
            # Return single row
            return self.labeled_data.iloc[idx]
        elif isinstance(idx, slice):
            # Return slice of data
            return self.labeled_data.iloc[idx]
        else:
            raise TypeError("Index must be an integer or slice")

if __name__ == "__main__":
    # Test the StocksLoader class
    print("Testing StocksLoader class...")
    
    # Initialize loader with HDFCBANK
    loader = StocksLoader("HDFCBANK")
    # print(list(loader.stock_data.columns))
    # print(loader.stock_data.tail())
    
    # # Test 1: Load and label in one step
    # print("\nTest 1: Loading and labeling data in one step")
    # labeled_data = loader.load_and_label(
    #     window=5,
    #     method='combined',
    #     fixed_threshold=0.03,
    #     relative_margin=0.02
    # )
    # print(f"Data shape: {labeled_data.shape}")
    # print("\nFirst few rows of labeled data:")
    # print(labeled_data[['Date', 'Close', 'Future_Return', 'Label_Combined']].head())
    
    # # Test 2: Access data using indexing
    # print("\nTest 2: Accessing data using indexing")
    # first_row = loader[0]
    # print("\nFirst row:")
    # print(first_row[['Date', 'Close', 'Future_Return', 'Label_Combined']])
    
    # # Test 3: Access data using slicing
    # print("\nTest 3: Accessing data using slicing")
    # first_5_rows = loader[:5]
    # print("\nFirst 5 rows:")
    # print(first_5_rows[['Date', 'Close', 'Future_Return', 'Label_Combined']])
    
    # # Test 4: Try different labeling methods
    # print("\nTest 4: Testing different labeling methods")
    # methods = ['quantile', 'risk_adjusted', 'dynamic']
    # for method in methods:
    #     print(f"\nTesting {method} labeling method:")
    #     labeled_data = loader.load_and_label(
    #         window=5,
    #         method=method
    #     )
    #     label_col = f'Label_{method.capitalize()}'
    #     print(f"Data shape: {labeled_data.shape}")
    #     print(f"Label distribution for {label_col}:")
    #     print(labeled_data[label_col].value_counts())