"""
PERSON 5: PRICE VISUALIZER
Visualizes price data from Person 3's analysis
Creates charts and tables for price history and trends
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from tabulate import tabulate
import seaborn as sns
from dataclasses import dataclass

# ==================== DATA CLASSES ====================

@dataclass
class ChartConfig:
    """Configuration for charts"""
    title: str
    width: int = 1000
    height: int = 600
    theme: str = "plotly_white"
    colors: List[str] = None
    
    def __post_init__(self):
        # 💡 NOTE: Ensure default colors if not provided
        if self.colors is None:
            self.colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

@dataclass
class TableConfig:
    """Configuration for tables"""
    headers: List[str]
    format: str = "fancy_grid"
    show_index: bool = False
    float_format: str = ".2f"

# ==================== DATA SOURCE ====================
# Person 5 gets data from Person 3's analysis output

class AnalysisDataLoader:
    """Loads analysis data from Person 3"""
    
    @staticmethod
    def load_analysis_data(file_path: str = "analysis_32780.json") -> Optional[Dict[str, Any]]:
        """Load analysis data from Person 3's JSON output"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Analysis file not found: {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"Invalid JSON file: {file_path}")
            return None
    
    @staticmethod
    def load_visualization_data(file_path: str = "visualization_data.json") -> Optional[Dict[str, Any]]:
        """Load visualization data prepared by Person 3"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Visualization file not found: {file_path}")
            return None
    
    @staticmethod
    def load_price_history_from_db() -> pd.DataFrame:
        """
        Load price history from Person 2's database
        Compatible with both price_with_moving_average() and create_site_comparison_bar_chart().
        Now includes 3 timestamps per site for smoother moving average.
        """
        data = {
            "product_name": [
                "Harry Potter"]*12 + ["iPhone"]*12,
            "product_id": [
                "32780"]*12 + ["HBC00004E3WIR"]*12,
            "site": [
                "kitapyurdu", "kitapyurdu", "kitapyurdu",
                "d&r", "d&r", "d&r",
                "idefix", "idefix", "idefix",
                "bkm", "bkm", "bkm",
                "hepsiburada", "hepsiburada", "hepsiburada",
                "trendyol", "trendyol", "trendyol",
                "n11", "n11", "n11",
                "amazon", "amazon", "amazon"
            ],
            "current_price": [
                59.99, 61.50, 60.50,
                60.00, 62.00, 61.50,
                58.00, 59.50, 58.50,
                60.00, 61.00, 60.50,
                45999.99, 44999.99, 45500.00,
                45000.00, 45500.00, 45200.00,
                47000.00, 46800.00, 46900.00,
                46500.00, 46650.00, 46700.00
            ],
            "timestamp": [
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00",
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00",
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00",
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00",
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00",
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00",
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00",
                "2024-01-10T10:00:00", "2024-01-11T10:00:00", "2024-01-12T10:00:00"
            ]
        }

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

# ==================== CHART VISUALIZER ====================

class PriceChartVisualizer:
    """Creates various price charts using Plotly"""
    
    def __init__(self):
        plt.style.use('seaborn-v0_8-darkgrid')
        self.colors = px.colors.qualitative.Set3
    
    def create_price_history_chart(self, df: pd.DataFrame, product_name: str) -> go.Figure:
        """Create interactive price history line chart"""
        
        product_df = df[df['product_name'] == product_name]
        
        if product_df.empty:
            print(f"No data found for product: {product_name}")
            return None
        
        fig = go.Figure()
        
        # Main price line
        fig.add_trace(go.Scatter(
            x=product_df['timestamp'],
            y=product_df['current_price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>Price: %{y:.2f} TL<extra></extra>'
        ))
        
        # Add average line if available
        if 'average_price' in product_df.columns:
            avg_price = product_df['average_price'].iloc[0]
            fig.add_hline(
                y=avg_price,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"Average: {avg_price:.2f} TL",
                annotation_position="bottom right"
            )
        
        fig.update_layout(
            title=dict(
                text=f"Price History: {product_name}",
                font=dict(size=24, family="Arial Black")
            ),
            xaxis=dict(
                title="Date",
                tickformat="%Y-%m-%d",
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="Price (TL)",
                tickprefix="₺",
                gridcolor='lightgray'
            ),
            hovermode="x unified",
            template="plotly_white",
            height=600,
            showlegend=True
        )
        
        return fig
    
    def create_comparison_chart(self, df: pd.DataFrame, products: List[str]) -> go.Figure:
        """Compare prices of multiple products"""
        
        filtered_df = df[df['product_name'].isin(products)]
        
        if filtered_df.empty:
            print("No data found for selected products")
            return None
        
        fig = px.line(
            filtered_df,
            x='timestamp',
            y='current_price',
            color='product_name',
            markers=True,
            title="Price Comparison",
            labels={'current_price': 'Price (TL)', 'timestamp': 'Date'}
        )
        
        fig.update_layout(
            height=600,
            template="plotly_white",
            hovermode="x unified"
        )
        
        return fig
    
    def create_price_distribution_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create histogram of price distribution"""
        
        fig = px.histogram(
            df,
            x='current_price',
            nbins=20,
            title="Price Distribution",
            labels={'current_price': 'Price (TL)'},
            color_discrete_sequence=['#2ca02c']
        )
        
        fig.update_layout(
            height=500,
            template="plotly_white",
            bargap=0.1
        )
        
        return fig
    
    def create_analysis_summary_chart(self, analysis_data: Dict[str, Any]) -> go.Figure:
        """Create summary chart from Person 3's analysis"""
        
        labels = ['Current', 'Average', 'Minimum', 'Maximum']
        values = [
            analysis_data['current_price'],
            analysis_data['average_price'],
            analysis_data['minimum_price'],
            analysis_data['maximum_price']
        ]
        
        colors = ['#4CAF50', '#2196F3', '#FF9800', '#F44336']
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f'₺{v:.2f}' for v in values],
            textposition='auto',
        )])
        
        fig.update_layout(
            title=dict(
                text=f"Price Analysis: {analysis_data['product_name']}",
                font=dict(size=20)
            ),
            yaxis=dict(
                title="Price (TL)",
                tickprefix="₺"
            ),
            template="plotly_white",
            height=500
        )
        
        return fig
    
    def create_trend_indicator(self, analysis_data: Dict[str, Any]) -> go.Figure:
        """Create gauge chart for trend indicator"""
        
        change_percent = analysis_data['price_change_percent']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=change_percent,
            delta={'reference': 0},
            title={'text': f"Price Change %"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [-50, 50]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [-50, -20], 'color': "lightcoral"},
                    {'range': [-20, -5], 'color': "lightyellow"},
                    {'range': [-5, 5], 'color': "lightgreen"},
                    {'range': [5, 20], 'color': "lightyellow"},
                    {'range': [20, 50], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': change_percent
                }
            }
        ))
        
        fig.update_layout(
            title=f"Price Trend: {analysis_data['product_name']}",
            height=400
        )
        
        return fig
    
    def price_with_moving_average(self, df: pd.DataFrame, product_name: str, window: int = 7) -> go.Figure:
        """Create price chart with moving average overlay for each site, with consistent colors."""
        
        product_df = df[df['product_name'] == product_name].sort_values(['site', 'timestamp'])
        if product_df.empty:
            print(f"No data found for '{product_name}'")
            return None
        
        fig = go.Figure()
        
        # Assign a color per site
        site_colors = px.colors.qualitative.Set2
        sites = product_df['site'].unique()
        color_map = {site: site_colors[i % len(site_colors)] for i, site in enumerate(sites)}
        
        # Plot each site separately
        for site, site_df in product_df.groupby('site'):
            site_df = site_df.set_index('timestamp').sort_index()
            site_df['ma'] = site_df['current_price'].rolling(window=window, min_periods=1).mean()
            color = color_map[site]
            
            # Main price line for the site
            fig.add_trace(go.Scatter(
                x=site_df.index,
                y=site_df['current_price'],
                mode='lines+markers+text',
                name=f"{site} Price",
                text=[f"₺{p:.2f}" for p in site_df['current_price']],
                textposition="top center",
                textfont=dict(color='black', size=9),
                line=dict(color=color)
            ))
            
            # Moving average line for the site
            fig.add_trace(go.Scatter(
                x=site_df.index,
                y=site_df['ma'],
                mode='lines',
                name=f"{site} {window}-Day MA",
                line=dict(dash='dash', color=color)
            ))
        
        fig.update_layout(
            title=f"{product_name} — Price History & {window}-Day Moving Average by Site",
            xaxis_title="Date",
            yaxis_title="Price (TL)",
            hovermode="x unified",
            template="plotly_white",
            height=600
        )

        return fig

    
    def create_site_comparison_bar_chart(self, df: pd.DataFrame, product_name: str) -> go.Figure:
        """Compare the same product's price across different sites in a bar chart."""
        
        product_df = df[df['product_name'] == product_name].sort_values('timestamp')
        
        if product_df.empty:
            print(f"No data found for '{product_name}'")
            return None
        
        # Take the latest price per site
        latest_df = product_df.groupby('site').tail(1)
        
        fig = go.Figure(go.Bar(
            x=latest_df['site'],
            y=latest_df['current_price'],
            marker_color="#1f77b4",
            text=[f"₺{p:.2f}" for p in latest_df['current_price']],
            textposition="auto"
        ))
        
        fig.update_layout(
            title=f"{product_name} — Price Comparison Across Sites",
            xaxis_title="Site",
            yaxis_title="Price (TL)",
            template="plotly_white",
            height=500
        )
        
        return fig

# ==================== TABLE VISUALIZER ====================

class PriceTableVisualizer:
    """Creates formatted tables of price data"""
    
    def create_analysis_table(self, analysis_data: Dict[str, Any]) -> str:
        """Create formatted table from analysis data"""
        
        table_data = [
            ["Product Name", analysis_data['product_name']],
            ["Site", analysis_data['site']],
            ["Current Price", f"₺{analysis_data['current_price']:.2f}"],
            ["Previous Price", f"₺{analysis_data['previous_price']:.2f}"],
            ["Price Change", f"{analysis_data['price_change_percent']:.2f}%"],
            ["Average Price", f"₺{analysis_data['average_price']:.2f}"],
            ["Minimum Price", f"₺{analysis_data['minimum_price']:.2f}"],
            ["Maximum Price", f"₺{analysis_data['maximum_price']:.2f}"],
            ["Trend", analysis_data['trend_direction']],
            ["Alert Level", analysis_data['alert_level']],
            ["Recommendation", analysis_data['recommendation']],
            ["Confidence", f"{analysis_data['confidence_score']:.0f}%"]
        ]
        
        return tabulate(
            table_data,
            headers=["Metric", "Value"],
            tablefmt="fancy_grid",
            stralign="left"
        )
    
    def create_price_history_table(self, df: pd.DataFrame, product_name: str = None) -> str:
        """Create table of price history"""
        
        display_df = df.copy()
        
        if product_name:
            display_df = display_df[display_df['product_name'] == product_name]
        
        if display_df.empty:
            return "No data available"
        
        # Format columns
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"₺{x:.2f}")
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        
        return tabulate(
            display_df[['product_name', 'site', 'current_price', 'timestamp']],
            headers=["Product", "Site", "Price", "Date"],
            tablefmt="fancy_grid",
            showindex=False
        )
    
    def create_summary_table(self, df: pd.DataFrame) -> str:
        """Create summary statistics table"""
        
        summary = df.groupby('product_name').agg({
            'current_price': ['min', 'max', 'mean', 'count']
        }).round(2)
        
        summary.columns = ['Min Price', 'Max Price', 'Avg Price', 'Records']
        
        # Format prices
        for col in ['Min Price', 'Max Price', 'Avg Price']:
            summary[col] = summary[col].apply(lambda x: f"₺{x:.2f}")
        
        return tabulate(
            summary,
            headers="keys",
            tablefmt="fancy_grid",
            floatfmt=".2f"
        )

# ==================== MAIN VISUALIZER CLASS ====================

class PriceVisualizer:
    """
    Person 5: Main visualizer class
    Combines charts and tables for comprehensive visualization
    """
    
    def __init__(self):
        self.data_loader = AnalysisDataLoader()
        self.chart_viz = PriceChartVisualizer()
        self.table_viz = PriceTableVisualizer()
        
        # Load data from Person 3
        self.analysis_data = self.data_loader.load_analysis_data()
        self.viz_data = self.data_loader.load_visualization_data()
        self.price_df = self.data_loader.load_price_history_from_db()
        
        print("=" * 60)
        print("PERSON 5: PRICE VISUALIZER")
        print("Visualizing data from Person 3's analysis")
        print("=" * 60)
    
    def show_analysis_dashboard(self):
        """Show complete analysis dashboard"""
        
        if self.analysis_data is None:
            print("No analysis data available")
            return
        
        print("\nANALYSIS DASHBOARD")
        print("=" * 40)
        
        # Show table
        print("\nAnalysis Summary:")
        print(self.table_viz.create_analysis_table(self.analysis_data))   
    
    def show_price_history(self, product_name: str = None):
        """Show price history visualizations"""
        
        if self.price_df.empty:
            print("No price history data available")
            return
        
        print(f"\nPRICE HISTORY{' - ' + product_name if product_name else ''}")
        print("=" * 40)
        
        # Show table
        print("\nPrice History Table:")
        print(self.table_viz.create_price_history_table(self.price_df, product_name))
        
        # Show chart
        if product_name:

            fig_ma = self.chart_viz.price_with_moving_average(self.price_df, product_name)
            if fig_ma:
                fig_ma.show()
    
    def show_distribution_analysis(self):
        """Show price distribution analysis"""
        
        if self.price_df.empty:
            print("No data for distribution analysis")
            return
        
        print("\nPRICE DISTRIBUTION ANALYSIS")
        print("=" * 40)
        
        # Show summary table
        print("\nSummary Statistics:")
        print(self.table_viz.create_summary_table(self.price_df))
    
    def export_visualizations(self, output_dir: str = "visualizations"):
        """Export all visualizations to files"""
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nExporting visualizations to '{output_dir}/'")
        
        # Export analysis dashboard as HTML
        if self.analysis_data:
            fig1 = self.chart_viz.create_analysis_summary_chart(self.analysis_data)
            fig1.write_html(f"{output_dir}/analysis_summary.html")
            
            fig2 = self.chart_viz.create_trend_indicator(self.analysis_data)
            fig2.write_html(f"{output_dir}/trend_indicator.html")
            
            print(f" Saved: analysis_summary.html")
            print(f" Saved: trend_indicator.html")
        
            # Export price history charts
        if not self.price_df.empty:
            unique_products = self.price_df['product_name'].unique()
            for product in unique_products[:2]: # Export first 2 products
                
                # fig = self.chart_viz.create_price_history_chart(self.price_df, product) # <--- SİLİNECEK
                
                # 💡 YERİNE EKLE: Hareketli Ortalama grafiğini kaydedeceğiz.
                fig = self.chart_viz.price_with_moving_average(self.price_df, product)
                
                # Dosya kaydetme mantığı aynı kalır.
                safe_name = product.replace(" ", "_").lower()
                fig.write_html(f"{output_dir}/history_{safe_name}.html")
                print(f" Saved: history_{safe_name}.html")
            
            print(f"\nAll visualizations exported to '{output_dir}/'")

    def show_site_comparison(self, product_name: str):
        """Show bar chart comparing the same product across different sites"""
        
        if self.price_df.empty:
            print("No price history data available")
            return
        
        print(f"\nSITE COMPARISON FOR PRODUCT: {product_name}")
        print("=" * 40)
        
        # Show chart
        fig = self.chart_viz.create_site_comparison_bar_chart(self.price_df, product_name)
        if fig:
            fig.show()
        
        # Optional: show table of latest prices per site
        latest_df = self.price_df[self.price_df['product_name'] == product_name].sort_values('timestamp')
        latest_prices = latest_df.groupby('site').tail(1)
        print("\nLatest Prices by Site:")
        print(self.table_viz.create_price_history_table(latest_prices))
    
    def generate_report(self):
        """Generate comprehensive visualization report"""
        
        print("\n" + "=" * 60)
        print("COMPREHENSIVE VISUALIZATION REPORT")
        print("=" * 60)
        
        # 1. Analysis Dashboard
        self.show_analysis_dashboard()
        
        # 2. Price History & Site Comparison
        if not self.price_df.empty:
            unique_products = self.price_df['product_name'].unique()
            for product in unique_products[:2]:  # Show first 2 products
                # Show price history charts/tables
                self.show_price_history(product)
                
                # Show site comparison for the same product
                self.show_site_comparison(product)
        
        # 3. Distribution Analysis
        self.show_distribution_analysis()
        
        # 4. Export visualizations
        self.export_visualizations()
        
        print("\n" + "=" * 60)
        print("Visualization report completed!")
        print("=" * 60)


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Initialize visualizer
    visualizer = PriceVisualizer()
    
    # Generate complete report
    visualizer.generate_report()
    
    # Or use individual methods:
    # visualizer.show_analysis_dashboard()
    # visualizer.show_price_history("Harry Potter")
    # visualizer.show_distribution_analysis()