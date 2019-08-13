# rancher-utilities

 This repo contains some useful scripts to use with Rancher 2.
 For use them, you need python and rancher-cli binary file.

## copy-resources-between-projects

 This script allows to copy TLS certificates and Registries Credentials between two different Rancher projects.

 Parameters:
 ```
  --server SERVER       set rancher instance url
  --source SOURCE       Set the rancher project from where to read data
  --dest DEST           Set the rancher project to copy data
  --token TOKEN         Set the rancher auth token
  --rancher-path RANCHER_PATH
                        Set rancher binary path (default to ./rancher)
  --copy-mode COPY_MODE
                        Copy tls certificates, registries credentials or both. Accepted
                        values: tls, creds, all
```
