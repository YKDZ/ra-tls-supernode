UV=uv
PYTHON=python3

.PHONY: all dcap docker clean

all: dcap docker

csrc/libdcap_quoteverify_stub.o: csrc/dcap_stub.c
	$(CC) -c $< -o $@

csrc/libdcap_quoteverify_stub.a: csrc/libdcap_quoteverify_stub.o
	$(AR) rcs $@ $^

csrc/libdcap_quoteverify_stub.so: csrc/dcap_stub.c
	$(CC) -shared -fPIC $< -o $@

# Build the simulated DCAP verification library.
dcap: csrc/libdcap_quoteverify_stub.a csrc/libdcap_quoteverify_stub.so

# Build the docker image with proxy embedded.
docker: dcap
	docker buildx build -t ykdz/ra-tls-supernode:latest .

clean:
	rm -f csrc/libdcap_quoteverify_stub.o csrc/libdcap_quoteverify_stub.a csrc/libdcap_quoteverify_stub.so
	find . -type d -name "__pycache__" -exec rm -rf {} +
