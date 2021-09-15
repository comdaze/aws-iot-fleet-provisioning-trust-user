
from awscrt import auth, http, io, mqtt
from awsiot import iotidentity
from awsiot import mqtt_connection_builder
from concurrent.futures import Future
import sys
import threading
import time
import traceback
from uuid import uuid4
import json
import os
from utils.long_term_cert_set_result import long_term_cert_set_result

class LockedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.disconnect_called = False

locked_data = LockedData()

# Function for gracefully quitting this sample
def exit(msg_or_exception):
    if isinstance(msg_or_exception, Exception):
        print("Exiting Sample due to exception.")
        traceback.print_exception(msg_or_exception.__class__, msg_or_exception, sys.exc_info()[2])
    else:
        print("Exiting Sample:", msg_or_exception)

    with locked_data.lock:
        if not locked_data.disconnect_called:
            print("Disconnecting...")
            locked_data.disconnect_called = True
            future = mqtt_connection.disconnect()
            future.add_done_callback(on_disconnected)

def on_disconnected(disconnect_future):
    # type: (Future) -> None
    print("Disconnected.")

    # Signal that sample is finished
    is_sample_done.set()

def on_publish_register_thing(future):
    # type: (Future) -> None
    try:
        future.result() # raises exception if publish failed
        print("Published RegisterThing request..")

    except Exception as e:
        print("Failed to publish RegisterThing request.")
        exit(e)

def on_publish_create_keys_and_certificate(future):
    # type: (Future) -> None
    try:
        future.result() # raises exception if publish failed
        print("Published CreateKeysAndCertificate request..")

    except Exception as e:
        print("Failed to publish CreateKeysAndCertificate request.")
        exit(e)

def on_publish_create_certificate_from_csr(future):
    # type: (Future) -> None
    try:
        future.result() # raises exception if publish failed
        print("Published CreateCertificateFromCsr request..")

    except Exception as e:
        print("Failed to publish CreateCertificateFromCsr request.")
        exit(e)

def createkeysandcertificate_execution_accepted(response):
    # type: (iotidentity.CreateKeysAndCertificateResponse) -> None
    try:
        global createKeysAndCertificateResponse
        createKeysAndCertificateResponse = response
        
        print("Received a new message {}".format(createKeysAndCertificateResponse))

        return

    except Exception as e:
        exit(e)

def createkeysandcertificate_execution_rejected(rejected):
    # type: (iotidentity.RejectedError) -> None
    exit("CreateKeysAndCertificate Request rejected with code:'{}' message:'{}' statuscode:'{}'".format(
        rejected.error_code, rejected.error_message, rejected.status_code))

def createcertificatefromcsr_execution_accepted(response):
    # type: (iotidentity.CreateCertificateFromCsrResponse) -> None
    try:
        global createCertificateFromCsrResponse
        createCertificateFromCsrResponse = response
        print("Received a new message {}".format(createCertificateFromCsrResponse))
        global certificateOwnershipToken
        certificateOwnershipToken = response.certificate_ownership_token

        return

    except Exception as e:
        exit(e)

def createcertificatefromcsr_execution_rejected(rejected):
    # type: (iotidentity.RejectedError) -> None
    exit("CreateCertificateFromCsr Request rejected with code:'{}' message:'{}' statuscode:'{}'".format(
        rejected.error_code, rejected.error_message, rejected.status_code))

def registerthing_execution_accepted(response):
    # type: (iotidentity.RegisterThingResponse) -> None
    try:
        global registerThingResponse
        registerThingResponse = response
        print("Received a new message {} ".format(registerThingResponse))
        return

    except Exception as e:
        exit(e)

def registerthing_execution_rejected(rejected):
    # type: (iotidentity.RejectedError) -> None
    exit("RegisterThing Request rejected with code:'{}' message:'{}' statuscode:'{}'".format(
        rejected.error_code, rejected.error_message, rejected.status_code))

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)

def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))

def waitForCreateKeysAndCertificateResponse():
    # Wait for the response.
    loopCount = 0
    while loopCount < 10 and createKeysAndCertificateResponse is None:
        if createKeysAndCertificateResponse is not None:
            break
        print('Waiting... CreateKeysAndCertificateResponse: ' + json.dumps(createKeysAndCertificateResponse))
        loopCount += 1
        time.sleep(1)

def waitForCreateCertificateFromCsrResponse():
    # Wait for the response.
    loopCount = 0
    while loopCount < 10 and createCertificateFromCsrResponse is None:
        if createCertificateFromCsrResponse is not None:
            break
        print('Waiting...CreateCertificateFromCsrResponse: ' + json.dumps(createCertificateFromCsrResponse))
        loopCount += 1
        time.sleep(1)

def waitForRegisterThingResponse():
    # Wait for the response.
    loopCount = 0
    while loopCount < 20 and registerThingResponse is None:
        if registerThingResponse is not None:
            break
        loopCount += 1
        print('Waiting... RegisterThingResponse: ' + json.dumps(registerThingResponse))
        time.sleep(1)


is_sample_done = threading.Event()
verbosity = io.LogLevel.NoLogs.name
io.init_logging(getattr(io.LogLevel, verbosity), 'stderr')
mqtt_connection = None
identity_client = None
    
createKeysAndCertificateResponse = None
createCertificateFromCsrResponse = None
registerThingResponse = None


def fleet_provisioning(endpoint, cert, key, root_ca, client_id, use_websocket, signing_region, proxy_host, proxy_port, verbosity, csr, templateName, templateParameters):
   
    
    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    proxy_options = None
    if (proxy_host):
        proxy_options = http.HttpProxyOptions(host_name = proxy_host, port= proxy_port)

    if  use_websocket == True:
        credentials_provider = auth.AwsCredentialsProvider.new_default_chain(client_bootstrap)
        mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
            endpoint= endpoint,
            client_bootstrap=client_bootstrap,
            region= signing_region,
            credentials_provider=credentials_provider,
            http_proxy_options=proxy_options,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            ca_filepath= root_ca,
            client_id= client_id,
            clean_session=False,
            keep_alive_secs=30)

    else:
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint= endpoint,
            cert_filepath= cert,
            pri_key_filepath= key,
            client_bootstrap=client_bootstrap,
            ca_filepath= root_ca,
            client_id= client_id,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            clean_session=False,
            keep_alive_secs=30,
            http_proxy_options=proxy_options)

    print("Connecting to {} with client ID '{}'...".format(
         endpoint, client_id))

    connected_future = mqtt_connection.connect()

    identity_client = iotidentity.IotIdentityClient(mqtt_connection)

    # Wait for connection to be fully established.
    # Note that it's not necessary to wait, commands issued to the
    # mqtt_connection before its fully connected will simply be queued.
    # But this sample waits here so it's obvious when a connection
    # fails or succeeds.
    connected_future.result()
    print("Connected!")

    try:
        # Subscribe to necessary topics.
        # Note that is **is** important to wait for "accepted/rejected" subscriptions
        # to succeed before publishing the corresponding "request".

        # Keys workflow if csr is not provided
        if  csr is None:
            createkeysandcertificate_subscription_request = iotidentity.CreateKeysAndCertificateSubscriptionRequest()

            print("Subscribing to CreateKeysAndCertificate Accepted topic...")
            createkeysandcertificate_subscribed_accepted_future, _ = identity_client.subscribe_to_create_keys_and_certificate_accepted(
                request=createkeysandcertificate_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=createkeysandcertificate_execution_accepted)

            # Wait for subscription to succeed
        
            createkeysandcertificate_subscribed_accepted_future.result()
        
            print("Subscribing to CreateKeysAndCertificate Rejected topic...")
            createkeysandcertificate_subscribed_rejected_future, _ = identity_client.subscribe_to_create_keys_and_certificate_rejected(
                request=createkeysandcertificate_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=createkeysandcertificate_execution_rejected)

            # Wait for subscription to succeed
            createkeysandcertificate_subscribed_rejected_future.result()
        else:
            createcertificatefromcsr_subscription_request = iotidentity.CreateCertificateFromCsrSubscriptionRequest()

            print("Subscribing to CreateCertificateFromCsr Accepted topic...")
            createcertificatefromcsr_subscribed_accepted_future, _ = identity_client.subscribe_to_create_certificate_from_csr_accepted(
                request=createcertificatefromcsr_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=createcertificatefromcsr_execution_accepted)

            # Wait for subscription to succeed
            createcertificatefromcsr_subscribed_accepted_future.result()

            print("Subscribing to CreateCertificateFromCsr Rejected topic...")
            createcertificatefromcsr_subscribed_rejected_future, _ = identity_client.subscribe_to_create_certificate_from_csr_rejected(
                request=createcertificatefromcsr_subscription_request,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=createcertificatefromcsr_execution_rejected)

            # Wait for subscription to succeed
            createcertificatefromcsr_subscribed_rejected_future.result()


        registerthing_subscription_request = iotidentity.RegisterThingSubscriptionRequest(template_name= templateName)

        print("Subscribing to RegisterThing Accepted topic...")
        registerthing_subscribed_accepted_future, _ = identity_client.subscribe_to_register_thing_accepted(
            request=registerthing_subscription_request,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=registerthing_execution_accepted)

        # Wait for subscription to succeed
        registerthing_subscribed_accepted_future.result()

        print("Subscribing to RegisterThing Rejected topic...")
        registerthing_subscribed_rejected_future, _ = identity_client.subscribe_to_register_thing_rejected(
            request=registerthing_subscription_request,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=registerthing_execution_rejected)
        # Wait for subscription to succeed
        registerthing_subscribed_rejected_future.result()

        if  csr is None:
            print("Publishing to CreateKeysAndCertificate...")
            publish_future = identity_client.publish_create_keys_and_certificate(
                request=iotidentity.CreateKeysAndCertificateRequest(), qos=mqtt.QoS.AT_LEAST_ONCE)
            publish_future.add_done_callback(on_publish_create_keys_and_certificate)

            waitForCreateKeysAndCertificateResponse()

            if createKeysAndCertificateResponse is None:
                raise Exception('CreateKeysAndCertificate API did not succeed')

            registerThingRequest = iotidentity.RegisterThingRequest(
                template_name= templateName,
                certificate_ownership_token=createKeysAndCertificateResponse.certificate_ownership_token,
                parameters=json.loads( templateParameters))
            
            body=str(createKeysAndCertificateResponse)
            long_term_cert_set_result(body, './certs', 'long-term')
        else:
            print("Publishing to CreateCertificateFromCsr...")
            csrPath = open( csr, 'r').read()
            publish_future = identity_client.publish_create_certificate_from_csr(
                request=iotidentity.CreateCertificateFromCsrRequest(certificate_signing_request=csrPath),
                qos=mqtt.QoS.AT_LEAST_ONCE)
            publish_future.add_done_callback(on_publish_create_certificate_from_csr)

            waitForCreateCertificateFromCsrResponse()

            if createCertificateFromCsrResponse is None:
                raise Exception('CreateCertificateFromCsr API did not succeed')

            registerThingRequest = iotidentity.RegisterThingRequest(
                template_name= templateName,
                certificate_ownership_token=createCertificateFromCsrResponse.certificate_ownership_token,
                parameters=json.loads( templateParameters))

        print("Publishing to RegisterThing topic...")
        registerthing_publish_future = identity_client.publish_register_thing(registerThingRequest, mqtt.QoS.AT_LEAST_ONCE)
        registerthing_publish_future.add_done_callback(on_publish_register_thing)
        waitForRegisterThingResponse()
#        exit("success")
        future = mqtt_connection.disconnect()
        future.add_done_callback(on_disconnected)
        

    except Exception as e:
        exit(e)

    # Wait for the sample to finish
#    is_sample_done.wait()



fleet_provisioning(
    endpoint = 'a2jtec7plm36gl.ats.iot.cn-north-1.amazonaws.com.cn',
    root_ca =  './certs/root.ca.pem',
    cert =  './certs/provision.cert.pem',
    key =  './certs/provision.private.key',
    templateName =  'TrustedUserProvisioningTemplate',
    templateParameters= "{\"SerialNumber\":\"1\",\"DeviceLocation\":\"Seattle\"}",
    client_id = "test-" + str(uuid4()),
    use_websocket = False,
    signing_region  = 'cn-north-1',
    proxy_host = None,
    proxy_port = None,
    csr = None,
    verbosity = io.LogLevel.NoLogs.name
)



#os.system('python3 pubsub.py --endpoint a2jtec7plm36gl.ats.iot.cn-north-1.amazonaws.com.cn --root-ca ./certs/root.ca.pem --key  ./certs/long-term.private.key --cert ./certs/long-term.cert.pem --topic test/topic')
