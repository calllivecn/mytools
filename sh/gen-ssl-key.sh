#!/bin/bash

COUNTRY="CN"
ST="Shanghai"
CITY="Shanghai"
O="bnq"

EMAIL="ap@bnq.in"

OU="bnq.in"

DOMAIN='logs.bnq.in'
DAYS=3650


OPENSSL_CNF=/etc/ssl/openssl.cnf

# Root CA
generateRootCertificate() {
    openssl genrsa -out ca.key 2048
    openssl req -new -x509 -days ${DAYS} -key ca.key -out ca.crt #\
	#-config ${OPENSSL_CNF} -subj "/C=$COUNTRY/ST=$ST/L=$CITY/O=$ORG/OU=$OU"
}

generateServerCertificate() {
    openssl genrsa -out ${DOMAIN}.key 2048

    openssl req -new -days ${DAYS} -key ${DOMAIN}.key -out ${DOMAIN}.csr #\
		#-config ${OPENSSL_CNF} -subj "/C=$COUNTRY/ST=$PROVINCE/L=$CITY/O=$ORG/OU=$OU/CN=$DOMAIN"

    openssl ca -in ${DOMAIN}.csr -out ${DOMAIN}.crt -cert ca.crt -keyfile ca.key -extensions v3_req #\
		#-config ${OPENSSL_CNF}
}

#generateRootCertificate
generateServerCertificate
