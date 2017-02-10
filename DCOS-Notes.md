# DCOS Notes

Troubleshooting and setup notes for working with DC/OS from Spinnaker

## Certificates

The admin router for DC/OS uses a self-signed certificate which can cause issues for clouddriver being able to connect to it.  The problem can be addressed manually in a few steps:

* Make sure you're connecting to a DNS name that's in the Subject Alternative Name (SAN) list for the cert.    
  * If none of those IPs/hostnames are usable outside of the cluster's network then add an entry to your /etc/hosts for master.mesos
  * To check the SANs:

```
openssl s_client -connect $DCOS_MASTER:443 | openssl x509 -noout -text | grep DNS:
```



* Add the certificate to the JVM keystore for clouddriver

```bash
docker exec -it /bin/bash clouddriver
openssl s_client -showcerts -connect $DCOS_MASTER:443 </dev/null 2>/dev/null|openssl x509 -outform PEM > dcoscert.pem
keytool -importcert -file dcoscert.pem -keystore $JAVA_HOME/jre/lib/security/cacerts
# default password: changeit
exit
docker restart clouddriver
```
