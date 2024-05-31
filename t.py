import pandas as pd

df = pd.read_csv('abc.csv', index_col=0)
# print(df['0'])
# print(df[['date','0','1','2']].loc[:3].to_string())
# l1 = df[['date', '0']]
# l2 = df[['date', '1']]
# l1['0'] = l1['0'].str.split('_')
# l1['0'] = l1['0'].apply(lambda x: x[0])
# print(l1)

# Function to extract symbol and quantity
def extract_symbol_quantity(cell_value):
    symbol, quantity = cell_value.split('_')
    return symbol, float(quantity)

# Dictionary to track the quantity transitions for each symbol
symbol_transitions = {}
date_transitions = {}

# Process each cell to track transitions
for i, row in df.iterrows():
    date = row['date']
    for column in df.columns[1:]:
        cell = row[column]
        symbol, quantity = extract_symbol_quantity(cell)
        if symbol not in symbol_transitions:
            symbol_transitions[symbol] = []
            date_transitions[symbol] = []
        symbol_transitions[symbol].append(quantity)
        date_transitions[symbol].append(date)

# Identify symbols with the desired transition pattern and record dates
symbols_with_transition = []
transition_dates = {}

def find_transition_dates(quantities, dates):
    start_date = end_date = None
    has_positive = has_negative = False
    for quantity, date in zip(quantities, dates):
        if quantity > 0 and not has_positive:
            has_positive = True
        elif quantity < 0 and has_positive and not has_negative:
            has_negative = True
            start_date = date
        elif quantity > 0 and has_positive and has_negative:
            end_date = date
            break
    return start_date, end_date

for symbol, quantities in symbol_transitions.items():
    start_date, end_date = find_transition_dates(quantities, date_transitions[symbol])
    symbols_with_transition.append(symbol)
    transition_dates[symbol] = (start_date, end_date)

print(transition_dates)
for idx, val in transition_dates.items():
    print(idx, val[0], val[1])