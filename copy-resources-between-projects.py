import os

try:
    import requests
    import json
    import argparse
except ImportError:
    print('\nYou have to install "requests" module with:\n python -m pip install requests')
    exit()


RANCHER_URL = ""
SOURCE_PROJECT = ""
DEST_PROJECT = ""
AUTH_TOKEN = ""
RANCHER_BIN = './rancher'
KUBECTL = RANCHER_BIN + ' kubectl'
COPY_TLS = False
COPY_CREDS = False


def check_settings():
    global RANCHER_URL
    global SOURCE_PROJECT
    global DEST_PROJECT
    global AUTH_TOKEN
    global RANCHER_BIN
    global KUBECTL
    global COPY_TLS
    global COPY_CREDS

    print("Checking params...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--server",
                        help="set rancher instance url")
    parser.add_argument("--source",
                        help="Set the rancher project from where to read data")
    parser.add_argument("--dest",
                        help="Set the rancher project to copy data")
    parser.add_argument("--token",
                        help="Set the rancher auth token")
    parser.add_argument("--rancher-path",
                        help="Set rancher binary path (default to ./rancher)")
    parser.add_argument("--copy-mode",
                        help="tls certificates and registries credentials.\nAccepted values: tls, creds, all")

    args = parser.parse_args()
    if args.server:
        RANCHER_URL = args.server
    if args.source:
        SOURCE_PROJECT = args.source
    if args.dest:
        DEST_PROJECT = args.dest
    if args.token:
        AUTH_TOKEN = args.token
    if args.rancher_path:
        RANCHER_BIN = args.rancher_path
    if args.copy_mode:
        if (args.copy_mode == 'tls'):
            COPY_TLS = True
        elif (args.copy_mode == 'creds'):
            COPY_CREDS = True
        elif (args.copy_mode == 'all'):
            COPY_TLS = True
            COPY_CREDS = True
    else:
        print("ERR: No Copy Mode defined")
        exit()



    if RANCHER_URL == "":
        print("ERR: No Rancher URL defined")
        exit()
    if SOURCE_PROJECT == "":
        print("ERR: No Source Project defined")
        exit()
    if DEST_PROJECT == "":
        print("ERR: No Destination Project defined")
        exit()
    if AUTH_TOKEN == "":
        print("ERR: No Auth Token defined")
        exit()

    KUBECTL = RANCHER_BIN + ' kubectl'


def create_tls(name, key, crt):
    global AUTH_TOKEN
    global RANCHER_URL
    global DEST_PROJECT

    headers = {
        'Authorization': 'Bearer ' + AUTH_TOKEN,
        'Content-type': 'application/json',
    }
    data = {
        'type': 'certificate',
        'name': name,
        'key': key,
        'certs': crt
    }
    #print(json.dumps(data))
    api_url = RANCHER_URL + '/v3/project/'+ DEST_PROJECT + '/certificate'
    response = requests.post(api_url, headers = headers, data = json.dumps(data))
    return response.status_code

def create_registry_credentials(name, registry):
    global AUTH_TOKEN
    global RANCHER_URL
    global DEST_PROJECT

    headers = {
        'Authorization': 'Bearer ' + AUTH_TOKEN,
        'Content-type': 'application/json',
    }
    data = {
        'type': 'dockerCredential',
        'name': name,
        'registries': {
                }
    }
    data['registries'] = json.loads(registry)['auths']
    api_url = RANCHER_URL + '/v3/project/'+ DEST_PROJECT + '/dockercredential'
    response = requests.post(api_url, headers = headers, data = json.dumps(data))
    return response.status_code

def rancher_login():
    global AUTH_TOKEN
    global RANCHER_URL
    global SOURCE_PROJECT
    print("Login to rancher...")
    cmd = RANCHER_BIN + ' login ' + RANCHER_URL + ' -t ' + AUTH_TOKEN + '  --context ' + SOURCE_PROJECT
    result = os.popen(cmd).read()
    if result != '':
        print(result)
        exit()

if __name__ == "__main__":
    check_settings()

    rancher_login()

    print("Get namespaces from source project...")
    cmd = RANCHER_BIN + ' namespaces ps'
    result = os.popen(cmd).read()

    for line in result.splitlines()[1:]: #1: skip the first element with header
        namespace = line.split()[0]
        print("Namespace: " + namespace)
        print("Check secrets...")
        cmd = KUBECTL + ' get secrets -o json -n ' +  namespace
        secrets = os.popen(cmd).read()
        secrets_array = json.loads(secrets)['items']
        for secret in secrets_array:
            type = secret['type']
            name = secret['metadata']['name']
            print("- " + name + " (" + type + ")")
            if type == 'kubernetes.io/tls' and COPY_TLS:
                crt = secret['data']['tls.crt'].decode('base64')
                key = secret['data']['tls.key'].decode('base64')
                result = create_tls(name, key, crt)
                print("\tcreate tls: " + str(result))
            elif type == "kubernetes.io/dockerconfigjson" and COPY_CREDS:
                registry = secret['data']['.dockerconfigjson'].decode('base64')
                #print(registry)
                result = create_registry_credentials(name, registry)
                print("\tcreate_registry_credentials: " + str(result))
