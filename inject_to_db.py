# read full_table_of_cases.csv and inject to db.sqlite3

import csv
import sqlite3
import pandas as pd

# connect by deleting db.sqlite3 if exists

import os

if os.path.exists("db.sqlite3"):
    print("db.sqlite3 exists, deleting it...")
    os.remove("db.sqlite3")

conn = sqlite3.connect("db.sqlite3")


df = pd.read_csv("../academic_freedom/ed_cases_df.csv")

print(df.head(5))


# df = df.drop(columns=["casenumber", "hyphenated_date", "nameofparties"])

# df = df.rename(columns={"in-the-matter-of": "in_the_matter_of"})

print(df.keys())

# df = df[col_names]

# create a column named id and make it the index

df["id"] = df.index

print(df.head(5))

print(df.keys())


conn = sqlite3.connect("db.sqlite3")

# df_text = pd.read_csv("primary_key_to_judgement_text.csv")

# df_text = df_text.drop(columns=["filename"])

# df_text = df_text.rename(columns={"text": "judgement_text"})
# 
# print("df_text keys", df_text.keys())
# 
# print("shape of df_text", df_text.shape, "shape of df", df.shape)
# 
# df = df.merge(df_text, on="primary_key", how="inner")
# 
# print("df shape after merge", df.shape)

df.to_sql("pages_judgement", conn, if_exists="replace", index=False)


conn.close()