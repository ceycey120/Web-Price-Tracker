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
    
    def _post__init__(self):
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
    def load_analysis_data(file_path: str = "price_analysis_hp.json") -> Optional[Dict[str, Any]]:
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
        In real implementation, this would connect to the database
        """
        # Mock data for demonstration
        data = {
            "product_name": ["Harry Potter", "Harry Potter", "Harry Potter", "iPhone", "iPhone", "iPhone"],
            "product_id": ["32780", "32780", "32780", "HBC00004E3WIR", "HBC00004E3WIR", "HBC00004E3WIR"],
            "site": ["kitapyurdu", "kitapyurdu", "kitapyurdu", "hepsiburada", "hepsiburada", "hepsiburada"],
            "current_price": [59.99, 62.50, 55.00, 45999.99, 44999.99, 46999.99],
            "timestamp": [
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
        """Create price chart with moving average overlay."""

        product_df = df[df['product_name'] == product_name].sort_values('timestamp')
        if product_df.empty:
            print(f"No data found for '{product_name}'")
            return None

        df2 = product_df.copy().set_index('timestamp')
        df2['ma'] = df2['current_price'].rolling(window=window, min_periods=1).mean()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df2.index,
            y=df2['current_price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='<b>Price</b>: %{y:.2f} TL<extra></extra>'
        ))

        fig.add_trace(go.Scatter(
            x=df2.index,
            y=df2['ma'],
            mode='lines',
            name=f'{window}-Day Moving Average',
            line=dict(color='orange', width=3, dash='dash'),
            hovertemplate=f'<b>{window}-Day MA</b>: %{{y:.2f}} TL<extra></extra>'
        ))

        fig.update_layout(
            title=f"{product_name} — {window}-Day Moving Average",
            xaxis_title="Date",
            yaxis_title="Price (TL)",
            template="plotly_white",
            hovermode="x unified",
            height=600
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
        
        # Create and show charts
        print("\nVisualizations:")
        
        # Summary chart
        fig1 = self.chart_viz.create_analysis_summary_chart(self.analysis_data)
        if fig1:
            fig1.show()
        
        # Trend indicator
        fig2 = self.chart_viz.create_trend_indicator(self.analysis_data)
        if fig2:
            fig2.show()
    
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

            fig = self.chart_viz.create_price_history_chart(self.price_df, product_name)
            if fig:
                fig.show()

            fig_ma = self.chart_viz.price_with_moving_average(self.price_df, product_name)
            if fig_ma:
                fig_ma.show()
                
        else:
            # Show comparison if no specific product
            unique_products = self.price_df['product_name'].unique()[:3]  # Limit to 3
            fig = self.chart_viz.create_comparison_chart(self.price_df, list(unique_products))
            if fig:
                fig.show()
    
    def show_distribution_analysis(self):
        """Show price distribution analysis"""
        
        if self.price_df.empty:
            print("No data for distribution analysis")
            return
        
        print("\nPRICE DISTRIBUTION ANALYSIS")
        print("=" * 40)
        
        # Show summary table
        print("\Summary Statistics:")
        print(self.table_viz.create_summary_table(self.price_df))
        
        # Show distribution chart
        fig = self.chart_viz.create_price_distribution_chart(self.price_df)
        if fig:
            fig.show()
    
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
            for product in unique_products[:2]:  # Export first 2 products
                fig = self.chart_viz.create_price_history_chart(self.price_df, product)
                safe_name = product.replace(" ", "_").lower()
                fig.write_html(f"{output_dir}/history_{safe_name}.html")
                print(f" Saved: history_{safe_name}.html")
        
        print(f"\nAll visualizations exported to '{output_dir}/'")
    
    def generate_report(self):
        """Generate comprehensive visualization report"""
        
        print("\n" + "=" * 60)
        print("COMPREHENSIVE VISUALIZATION REPORT")
        print("=" * 60)
        
        # 1. Analysis Dashboard
        self.show_analysis_dashboard()
        
        # 2. Price History
        if not self.price_df.empty:
            unique_products = self.price_df['product_name'].unique()
            for product in unique_products[:2]:  # Show first 2 products
                self.show_price_history(product)
        
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
