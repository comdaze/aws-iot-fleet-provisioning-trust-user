#!/usr/bin/env python
# coding: utf-8

from keycloak import KeycloakOpenID
import boto3
from utils.parse_cert_set_result import cert_set_result
from utils.long_term_cert_set_result import long_term_cert_set_result
from botocore.config import Config

aws_config = Config(
    region_name = 'cn-north-1',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    }
)

# Configure client
keycloak_openid = KeycloakOpenID(
                    server_url="https://keycloak.aws.comdaze.com/auth/",
                    client_id="iotfleetclient",
                    realm_name="iotfleet",
                    client_secret_key="2742bc8a-9ce3-451f-83d0-e014d12442bf"
)



# Get WellKnow
#config_well_know = keycloak_openid.well_know()

token = keycloak_openid.token("user1", "Amazon@2021")

access_token=token['access_token']

IdentityPoolId =  'cn-north-1:f815bc17-e94c-47df-953b-840c67c27eb4'
AccountId ='456370280007'
cognito_identity_client = boto3.client('cognito-identity',config=aws_config)


IdentityId_response = cognito_identity_client.get_id(
    AccountId=AccountId,
    IdentityPoolId=IdentityPoolId,
    Logins={
        'keycloak.aws.comdaze.com/auth/realms/iotfleet':access_token
    }
)


IdentityId=IdentityId_response['IdentityId']




credentials_response = cognito_identity_client.get_credentials_for_identity(
    IdentityId=IdentityId,
    Logins={
        'keycloak.aws.comdaze.com/auth/realms/iotfleet':access_token
    }
)


ACCESS_KEY = credentials_response['Credentials']['AccessKeyId']
SECRET_KEY = credentials_response['Credentials']['SecretKey']
SESSION_TOKEN = credentials_response['Credentials']['SessionToken']




iotclient = boto3.client(
    'iot',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN
)



provisioning_claim_response = iotclient.create_provisioning_claim(
    templateName= 'TrustedUserProvisioningTemplate'
)



cert_set_result(provisioning_claim_response, './certs', 'provision')






