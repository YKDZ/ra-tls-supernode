# Intel(R) Software Guard Extensions Data Center Attestation Primitives (Intel(R) SGX DCAP) Quote Verification Enclave Quick Start Guide

## Build QvE and dcap_quoteverify libraries, non-production only (for debug purposes). For production you must use Intel(R) signed QvE.

## Linux

Supported operating systems:

- Ubuntu\* 18.04 LTS Desktop 64bits
- Ubuntu\* 18.04 LTS Server 64bits
- Ubuntu\* 20.04 LTS Server 64bits
- Red Hat Enterprise Linux Server release 8.2 64bits
- CentOS 8.2 64bits

Requirements:

- make
- gcc
- g++
- ZIP
- bash shell

Pre-requisites:

- Intel(R) SGX SDK
- Intel(R) SgxSSL: Follow instructions in https://github.com/intel/intel-sgx-ssl (By default SgxSSL will automatically be downloaded and built if not in SGX Docker container). You should use latest OpenSSL to build SgxSSL.

### Build `dcap_quoteverify.so` and `libsgx_qve.signed.so` (Only for debug purposes):

```
$ cd QuoteVerification/
$ make
Generate a key and sign generated QvE enclave:
$ /opt/intel/sgxsdk/bin/x64/sgx_sign sign -key Enclave/<GENERATED_KEY>.pem -enclave qve.so -out libsgx_qve.signed.so -config Enclave/qve.config.xml
```

### Build `qve.so` in SGX Docker container:

Use the script prepare_sgxssl.sh to download SgxSSL outside SGX Docker container firstly:
Note: You may need set https proxy for the wget tool used by the script (such as export https_proxy=http://test-proxy:test-port)

```
$ cd QuoteVerification/
Outside SGX Docker container, download SgxSSL to ./sgxssl folder
$ ./prepare_sgxssl.sh nobuild
Inside SGX Docker container, build QvE enclave
$ make -C QvE
```
