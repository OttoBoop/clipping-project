# Câmara's missing TLS intermediate

On 2026-09-09, camara.rio served its valid `*.camara.rio` certificate without
the Sectigo Public Server Authentication CA OV R36 intermediate. Standard
Requests and the system CA bundle both failed with `unable to get local issuer
certificate`.

The included public intermediate was downloaded from the leaf certificate's
CA Issuers address:
http://crt.sectigo.com/SectigoPublicServerAuthenticationCAOVR36.crt

`openssl verify` validated it against the existing Requests root bundle before
inclusion. Appending this intermediate to that unchanged bundle restored an
HTTP 200 response from the actual news archive. Hostname and certificate
verification remain enabled; no publisher leaf certificate is trusted directly.
The additional chain is used only for camara.rio and its subdomains.
