# rancher-utilities

 This repo contains some useful scripts to use with Rancher 2.
 For use them, you need python and rancher-cli binary file.

## copy-resources-between-projects

 This script allows to copy TLS certificates and Registries Credentials between two different Rancher projects.   
 It reads every resource for every namespace of the source project and copy it to the destination project.   
 The new resource will be created without namespace, so it will be available for all namespaces in the destination project.   

 Parameters:
 ```
  --server SERVER       Set rancher instance url
  --source SOURCE       Set the rancher project ID from where to read data
  --dest DEST           Set the rancher project ID to copy data, multiple values allowed (comma separated)
  --token TOKEN         Set the rancher auth token
  --rancher-path RANCHER_PATH
                        Set rancher binary path (default to ./rancher)
  --copy-mode COPY_MODE
                        Copy tls certificates, registries credentials or both. Accepted
                        values: tls, creds, all
```
## check-tls-certs

 This script allows to check the expire date of all TLS certificates inside a cluster.   
 It cycles every project and list TLS certs with related ingress.  
 Green certs are OK, yellow certs are with expire date in less than 2 months and red certs are already expired certs. 

 Parameters:
 ```
  --server SERVER       Set rancher instance url
  --source SOURCE       Set any rancher project ID of the cluster to check
  --token TOKEN         Set the rancher auth token
  --secret SECRET       Set the secret name of a specific TLS certificate to check
  --rancher-path RANCHER_PATH
                        Set rancher binary path (default to ./rancher)
```

## change-ingress-tls

 This script allows to change the tls secret name for all ingress records in a specific project.   
 It will highlight in yellow tls records that match the `OLD_SECRET` value and it will change the ingress with the `NEW_SECRET` value. 
 It's useful if you want to change all ingress records that have an old certificate (identified with the `check-ssl-certs` script) and upgrade to a new one.

 Parameters:
 ```
  --server SERVER           Set rancher instance url
  --dest DESTINATION        Set any rancher project ID of the cluster for check ingress records, multiple values allowed (comma separated)
  --token TOKEN             Set the rancher auth token
  --old-secret OLD_SECRET   Set the secret name to search inside ingress records
  --new-secret NEW_SECRET   Set the secret name that will replace the old one
  --rancher-path RANCHER_PATH
                        Set rancher binary path (default to ./rancher)
```
