import matplotlib as plt
import pandas as pd

def send_dataframe_as_image(df):
    columns = ['1h', '4h', '8h', '24h']
    row_header = [str(i) for i in range(1, 11)]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=columns, rowLabels=row_header, cellLoc='center', loc='center')
    plt.savefig('table.png', bbox_inches='tight', dpi=300)

def extract_symbol_quantity(cell_value):
    symbol, rs_value = cell_value.split('_')
    return symbol, float(rs_value)

for time_interval in ['4h', '8h', '24h']:
    df = pd.read_csv(f'rs_value_{time_interval}.csv', index_col=0)
    len_col = len(df.columns)
    for _, row in df.iterrows():
        # for column in df.columns[1:n+2]: # get weakest top-n
        for column in df.columns[len_col - 5:len_col]: # get strongest top-n
            cell = row[column]
            symbol, rs_value = extract_symbol_quantity(cell)
            if rs_value == 0:
                continue
            tmp.add(symbol)