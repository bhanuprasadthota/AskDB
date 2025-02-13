#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 13:25:31 2025

@author: bhanuprasadthota
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sqlite3

class AskDB:
    def __init__(self, db_path="askdb.db"):
        self.tokenizer = AutoTokenizer.from_pretrained("defog/sqlcoder")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("defog/sqlcoder")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def convert_to_sql(self, question):
        inputs = self.tokenizer(f"Convert to SQL: {question}", return_tensors="pt")
        outputs = self.model.generate(**inputs)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def execute_query(self, question):
        sql_query = self.convert_to_sql(question)
        try:
            self.cursor.execute(sql_query)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    askdb = AskDB()
    question = "Show all employees with salary above 50000"
    print(askdb.execute_query(question))
