import json
import os
import re
import sys

def long_term_cert_set_result(body, path, filename):
    
    if not os.path.exists(path):
        os.makedirs(path)

    cert_begin_str = "-----BEGIN CERTIFICATE-----"
    cert_end_str = "', private_key"
    raw_pem = (body[body.index(cert_begin_str):body.index(cert_end_str)])
    raw_pem = raw_pem.replace('\\n', '\n')
    if raw_pem:
        pem_filename = os.path.join(path, filename + ".cert.pem")
        with open(pem_filename, 'w') as file:
            file.write(raw_pem)
            
    key_begin_str = "-----BEGIN RSA PRIVATE KEY-----"
    key_end_str = "')"

    raw_private_key = (body[body.index(key_begin_str):body.index(key_end_str)]) 
    raw_private_key = raw_private_key.replace('\\n', '\n')
    try:
        if raw_private_key:
            private_key_filename = os.path.join(path, filename + ".private.key")
            with open(private_key_filename, 'w') as file:
                file.write(raw_private_key)
    except KeyError:
        pass

    print("Cert and Key Save Success!")
