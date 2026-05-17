from werkzeug.security import generate_password_hash

print("--- COPIA ISTO PARA O TEU INIT.SQL ---")
print(f"('admin', '{generate_password_hash('L|fP1D%327mB')}', FALSE),")
print(f"('alice', '{generate_password_hash('tth1mJj5?£58')}', FALSE),")
print(f"('bob', '{generate_password_hash('De586:Iq6}?!')}', FALSE);")