import plotly.graph_objects as go

def PlotSimpleChart(data,stock_ticker=""):
	# Create the candlestick chart
	fig = go.Figure(data=[go.Candlestick(x=data.index,
	                                     open=data['Open'],
	                                     high=data['High'],
	                                     low=data['Low'],
	                                     close=data['Close'],
	                                     name=stock_ticker)])

	# Customize chart appearance
	fig.update_layout(title=f'Candlestick chart for {stock_ticker}',
	                  xaxis_title='Date',
	                  yaxis_title='Price (USD)',
	                  xaxis_rangeslider_visible=False)

	# Show the chart
	fig.show()
