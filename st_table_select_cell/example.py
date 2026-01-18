import streamlit as st
import pandas as pd
from st_table_select_cell import st_table_select_cell

st.subheader("Example of st_table_select_cell")

data = pd.DataFrame({'Dataset':['energy','traffic','syn'], 'Test':['ehistory','snapshot','aggmax'], 'PG': [3,6,9], 'TG':[2,5,7]})
st.dataframe(data)

selectedCell = st_table_select_cell(data)
st.write(selectedCell)

if selectedCell:
    rowId = selectedCell['rowId']
    colIndex = selectedCell['colIndex']
    st.info('cell "{}" selected at row {} and col {} ({})'.format(data.iat[int(rowId), colIndex], rowId, colIndex, data.columns[colIndex]))
    st.write('selected row data: ', data.iloc[int(rowId)].to_dict())
else:
    st.warning('no select')