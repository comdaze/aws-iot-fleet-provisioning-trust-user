import json
import os
import re
import sys

def cert_set_result(body, path, filename):

    if not os.path.exists(path):
        os.makedirs(path)

    #body = json.load(body)

    raw_pem = body['certificatePem']
    if raw_pem:
        pem = re.sub("\\n", "\n", raw_pem)
        pem_filename = os.path.join(path, filename + ".cert.pem")
        with open(pem_filename, 'w') as file:
            file.write(pem)

    try:
        raw_pub_key = body['keyPair']['PublicKey']
        if raw_pub_key:
            pub_key = re.sub("\\n", "\n", raw_pub_key)
            pub_key_filename = os.path.join(path, filename + ".public.key")
            with open(pub_key_filename, 'w') as file:
                file.write(pub_key)

        raw_private_key = body['keyPair']['PrivateKey']
        if raw_private_key:
            private_key = re.sub("\\n", "\n", raw_private_key)
            private_key_filename = os.path.join(path, filename + ".private.key")
            with open(private_key_filename, 'w') as file:
                file.write(private_key)
    except KeyError:
        pass

    print("Success!")
