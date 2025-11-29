from product_table import PriceDataManager 
import pandas as pd
import matplotlib.pyplot as plot
from tabulate import tabulate


class PriceVisualizer:
    def __init__(self):
        self.manager = PriceDataManager()
        self.df = self.convert_to_dataframe()

    
#   ====== Fetching and converting data into dataframe ======
    def convert_to_dataframe(self):
        rows = self.manager.get_price_history()
        if not rows:
            print("Error: No price data was found")
            return pd.DataFrame
        
        df = pd.DataFrame(rows, columns=["Product", "Tier", "Points", "Price", "Date"]) #df = dataframe
        df["Date"] = pd.to_datetime(df["Date"])
        return df

#   ====== Chart visualization ======
    def plot_price_history(self, product_name):
        if self.df.empty:
            print("Error: No data available to plot graph")
            return
        
        product_df = self.df[self.df["Product"] == product_name]

        if product_df.empty:
            print(f"No data found for product: {product_name}")
            return
        
        plot.figure(figsize=(10, 5))
        plot.plot(product_df["Date"], product_df["Price"], marker="o")
        plot.title(f"Price History - {product_name}")
        plot.xlabel("Date")
        plot.ylabel("Price")
        plot.grid(True)
        plot.tight_layout()
        plot.show()

# ====== Table visualization ======
    def table_price_history(self):
        if self.df.empty:
            print("No data was found")
            return
        
        print("\n===Price History Table===\n")
        print(
            tabulate(
                self.df,
                headers="keys",
                tablefmt="fancy_grid",
                showindex=False
            )
        )

# ======
if __name__ == "__main__":
    vis = PriceVisualizer()

# ======TESTING USAGE======
vis.table_price_history()
vis.plot_price_history("SQLite")