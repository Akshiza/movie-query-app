import pandas as pd
import sqlite3

df = pd.read_csv(
    '../data/mymoviedb.csv',
    encoding='latin-1',
    on_bad_lines='skip',    # skips any broken rows
    engine='python'         # more tolerant parser
)

df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

print("Columns found:", df.columns.tolist())
print("Total rows loaded:", len(df))
print(df.head(2))

conn = sqlite3.connect('../data/movies.db')
df.to_sql('movies', conn, if_exists='replace', index=False)
conn.close()

print("Database created successfully!")