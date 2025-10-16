# 包装透明代理的 supernode 镜像

这个项目在 `flwr/supernode:1.22.0`（内部环境是 Python 3.12 & Ubuntu 24.04） 镜像的基础上包装了一个被动透明代理，并将其导出为一个名为 `ykdz/ra-tls-supernode:latest` 的新镜像。

这个透明代理由 `Python` 实现，功能如下：

被动地透明代理与给定 `superlink`（`host:port` 二元组）的流量，从 `TLS 1.2` 握手过程中的 `Certificate` 中的 `X509` 证书中提取其中可能包含的 `Intel SGX Remote Attestation` 并使用 `DCAP` 方法做验证，如果验证不通过，则不做转发从而阻止 `supernode` 继续连接到 `superlink`。

由于是被动透明代理，所以这个过程不涉及到任何破坏安全性的 TLS 中断。

Intel 官方提供了 DCAP 验证 C 库，相关 [API 文档](./dcap_quoteverify_api.txt) 和 [库 README](./DCAP_VERIFY_LIB_README.md) 已提供。

## 依赖管理

项目的依赖管理应该由 `uv` 完成。

## 构建

```shell
docker buildx build . -t ykdz/ra-tls-supernode
```

## 测试

```shell
docker compose up
```
