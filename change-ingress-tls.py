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
OLD_SECRET = ""
NEW_SECRET = ""
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
    global DEST_PROJECT
    global AUTH_TOKEN
    global RANCHER_BIN
    global KUBECTL
    global OLD_SECRET
    global NEW_SECRET

    print("Checking params...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--server",
                        help="Set rancher instance url")
    parser.add_argument("--dest",
                        help="Set a rancher project ID where to update ingress, multiple values allowed")
    parser.add_argument("--token",
                        help="Set the rancher auth token")
    parser.add_argument("--rancher-path",
                        help="Set rancher binary path (default to ./rancher)")
    parser.add_argument("--old-secret",
                        help="secret tls to change")
    parser.add_argument("--new-secret",
                        help="new secret tls to set")

    args = parser.parse_args()
    if args.server:
        RANCHER_URL = args.server
    if args.dest:
        DEST_PROJECT = args.dest
    if args.token:
        AUTH_TOKEN = args.token
    if args.rancher_path:
        RANCHER_BIN = args.rancher_path
    if args.old_secret:
        OLD_SECRET = args.old_secret
    if args.new_secret:
        NEW_SECRET = args.new_secret

    if RANCHER_URL == "":
        print("ERR: No Rancher URL defined")
        exit()
    if DEST_PROJECT == "":
        print("ERR: No Destination Project defined")
        exit()
    if OLD_SECRET == "":
        print("ERR: No old Secret defined")
        exit()
    if NEW_SECRET == "":
        print("ERR: No new Secret defined")
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
    response = requests.post(api_url, headers = headers, data = json.dumps(data), verify=False)
    return response.status_code

def rancher_login(project):
    global AUTH_TOKEN
    global RANCHER_URL
    print("Login to rancher...")
    cmd = RANCHER_BIN + ' login ' + RANCHER_URL + ' -t ' + AUTH_TOKEN + ' --context ' + project
    result = os.popen(cmd).read()
    if result != '':
        print(result)
        exit()

if __name__ == "__main__":
    check_settings()

    dest_projects = DEST_PROJECT.split(',')

    rancher_login(dest_projects[0])
    
    for project in dest_projects:
        cmd = RANCHER_BIN + ' context switch ' + project
        os.popen(cmd + " > /dev/null 2>&1").read()
        print(bcolors.OKBLUE + "PROJECT: " + project + bcolors.ENDC)
        cmd = RANCHER_BIN + ' namespace ps'
        namespaces = os.popen(cmd).read()
        for namespace_line in namespaces.splitlines()[1:]: #1: skip the first element with header
            namespace_id = namespace_line.split()[0]
            namespace_name = namespace_line.split()[1]
            print(" NS: " + namespace_name)
            cmd = KUBECTL + ' get ingress -o json -n ' +  namespace_id
            ingresses = os.popen(cmd).read()
            ingresses_array = json.loads(ingresses)['items']
            for ingress in ingresses_array:
                if ('tls' in ingress['spec']):
                    tls_array = ingress['spec']['tls']
                    print(bcolors.OKGREEN + " - " + ingress['metadata']['name'] + bcolors.ENDC)
                    cmd = KUBECTL + ' patch ing/' + ingress['metadata']['name'] + ' -n ' +  namespace_id + ' --type=json -p=\'['
                    idx = 0
                    to_update = False
                    for tls in tls_array:
                        mode = ""
                        if (tls['secretName'] == OLD_SECRET):
                            to_update = True
                            mode = bcolors.WARNING
                            cmd = cmd + '{"op": "replace", "path": "/spec/tls/' + str(idx) + '/secretName", "value":"' + NEW_SECRET + '"},'
                        
                        print("\t" + mode + " ,".join(tls['hosts']) + " (" + tls['secretName'] + ")" + bcolors.ENDC )
                        idx = idx + 1
                    
                    if (to_update):
                        cmd = cmd[:-1] + "]' "
                        print("   " + os.popen(cmd).read())