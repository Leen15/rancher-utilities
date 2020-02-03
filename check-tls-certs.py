import os
from datetime import datetime, date, timedelta
from operator import itemgetter

try:
    import requests
    import json
    import argparse
except ImportError:
    print('\nYou have to install "requests" module with:\n python -m pip install requests')
    exit()


RANCHER_URL = ""
SOURCE_PROJECT = ""
AUTH_TOKEN = ""
SECRET = ""
RANCHER_BIN = './rancher '
KUBECTL = RANCHER_BIN + ' kubectl'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def check_settings():
    global RANCHER_URL
    global SOURCE_PROJECT
    global AUTH_TOKEN
    global RANCHER_BIN
    global KUBECTL
    global SECRET

    print("Checking params...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--server",
                        help="Set rancher instance url")
    parser.add_argument("--source",
                        help="Set a rancher project ID of the cluster to check")
    parser.add_argument("--token",
                        help="Set the rancher auth token")
    parser.add_argument("--rancher-path",
                        help="Set rancher binary path (default to ./rancher)")
    parser.add_argument("--secret",
                        help="Search for a specific secret name")

    args = parser.parse_args()
    if args.server:
        RANCHER_URL = args.server
    if args.source:
        SOURCE_PROJECT = args.source
    if args.token:
        AUTH_TOKEN = args.token
    if args.rancher_path:
        RANCHER_BIN = args.rancher_path
    if args.secret:
        SECRET = args.secret

    if RANCHER_URL == "":
        print("ERR: No Rancher URL defined")
        exit()
    if SOURCE_PROJECT == "":
        print("ERR: No Source Project defined")
        exit()
    if AUTH_TOKEN == "":
        print("ERR: No Auth Token defined")
        exit()

    KUBECTL = RANCHER_BIN + ' kubectl'

def rancher_login():
    global AUTH_TOKEN
    global RANCHER_URL
    global SOURCE_PROJECT
    print("Login to rancher...")
    cmd = RANCHER_BIN + ' login ' + RANCHER_URL + ' -t ' + AUTH_TOKEN + ' --context ' + SOURCE_PROJECT
    result = os.popen(cmd).read()
    if result != '':
        print(result)
        exit()

if __name__ == "__main__":
    check_settings()

    rancher_login()

    cmd = RANCHER_BIN + ' context current'
    result = os.popen(cmd).read()
    cluster = result.split()[0]
    print("Get projects for " + cluster + "...")
    cmd = RANCHER_BIN + ' projects list'
    projects = os.popen(cmd).read()
    projects_array = []
    for line in projects.splitlines()[1:]: #1: skip the first element with header
        projects_array.append({
            'id': line.split()[0], 
            'name': line.split()[1], 
            'state': line.split()[2]
            })
    projects_array = sorted(projects_array, key=itemgetter('name')) 

    for project in projects_array: 
            project_id = project['id']
            project_name = project['name']
            cmd = RANCHER_BIN + ' context switch ' + project_id
            os.popen(cmd + " > /dev/null 2>&1").read()
            print(bcolors.OKBLUE + "PROJECT: " + project_name + " (" + project_id + ")" + bcolors.ENDC)
            cmd = RANCHER_BIN + ' namespace ps'
            namespaces = os.popen(cmd).read()
            certs = []
            load_balancing = []
            for namespace_line in namespaces.splitlines()[1:]: #1: skip the first element with header
                namespace_id = namespace_line.split()[0]
                namespace_name = namespace_line.split()[1]
                # print(" NS: " + namespace_name)
                cmd = KUBECTL + ' get secrets -o json -n ' +  namespace_id
                secrets = os.popen(cmd).read()
                secrets_array = json.loads(secrets)['items']
                for secret in secrets_array:
                    type = secret['type']
                    name = secret['metadata']['name']
                    if type == 'kubernetes.io/tls':
                        mode = bcolors.OKGREEN
                        # 2021-08-06T23:59:59Z
                        expiresAt = ""
                        if ('annotations' in secret['metadata'] and 'field.cattle.io/expiresAt' in secret['metadata']['annotations']):
                            expiresAt = secret['metadata']['annotations']['field.cattle.io/expiresAt'] 
                            expires_date = datetime.strptime(expiresAt[0:19], '%Y-%m-%dT%H:%M:%S')
                        
                            if (expires_date.date() < date.today()):
                                mode = bcolors.FAIL
                            elif (expires_date.date() < date.today() + timedelta(days=60)):
                                mode = bcolors.WARNING
                            else:
                                mode = bcolors.OKGREEN
                        cert = {'mode': mode, 'name': name, 'expire': expiresAt}
                        if (cert not in certs and (SECRET == "" or SECRET == cert['name'])):
                            certs.append(cert)
                cmd = KUBECTL + ' get ingress -o json -n ' +  namespace_id
                ingresses = os.popen(cmd).read()
                ingresses_array = json.loads(ingresses)['items']
                for ingress in ingresses_array:
                    if ('tls' in ingress['spec']):
                        tls_array = ingress['spec']['tls']
                        for tls in tls_array:
                            lb = {'hosts': tls['hosts'], 'secretName': tls['secretName'] }
                            load_balancing.append(lb)

            for cert in certs:
                print(cert['mode'] + " - " + cert['name'] + " (" + cert['expire'] + ")" + bcolors.ENDC)
                for lb in load_balancing:
                    if (lb['secretName'] == cert['name']):
                        print("    - " + " ".join(lb['hosts']))
