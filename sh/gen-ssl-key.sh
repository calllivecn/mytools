#!/bin/bash

COUNTRY="CN"
PROVINCE="Shanghai"
CITY="Shanghai"
ORG="bnq"
EMAIL="ap@bnq.in"
OU="bnq.in"
NAME="EasyRSA"
DOMAIN='logs.bnq.in'
DAYS=3650

generateRootCertificate() {
    openssl genrsa -out ca.key 2048
    openssl req -new -x509 -days ${DAYS} -key ca.key -out ca.crt -config openssl.cnf -subj \
    "/C=$COUNTRY/ST=$PROVINCE/L=$CITY/O=$ORG/OU=$OU"
}

generateServerCertificate() {
    openssl genrsa -out ${DOMAIN}.key 2048
    openssl req -new -days ${DAYS} -key ${DOMAIN}.key -out ${DOMAIN}.csr -config openssl.cnf -subj \
    "/C=$COUNTRY/ST=$PROVINCE/L=$CITY/O=$ORG/OU=$OU/CN=$DOMAIN"
    openssl ca -in ${DOMAIN}.csr -out ${DOMAIN}.crt -cert ca.crt -keyfile ca.key -extensions v3_req -config openssl.cnf
}

#generateRootCertificate
generateServerCertificate
