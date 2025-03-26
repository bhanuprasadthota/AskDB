from transformers import T5Tokenizer, T5ForConditionalGeneration

# Load model and tokenizer
model_name = "ThotaBhanu/t5_sql_askdb"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Function to convert natural language query to clean SQL
def generate_sql(query):
    input_text = f"Convert to SQL: {query}"
    inputs = tokenizer(input_text, return_tensors="pt")

    output = model.generate(
        **inputs,
        max_length=128,
        num_beams=4,
        early_stopping=True
    )

    result = tokenizer.decode(output[0], skip_special_tokens=True)

    # Clean unwanted structured parts like 'sel', 'agg', etc.
    if "'human_readable':" in result:
        result = result.split("'human_readable':")[-1].strip(" '\"{},\n")
    if "', 'sel'" in result:
        result = result.split("', 'sel'")[0].strip(" '\"{},\n")
    if "'sel'" in result:
        result = result.split("'sel'")[0].strip(" '\"{},\n")

    return result

# Example usage
if __name__ == "__main__":
    query = "Find all employees who joined in 2020"
    sql_query = generate_sql(query)

    print(f"📝 Query: {query}")
    print(f"🛠 Generated SQL: {sql_query}")
