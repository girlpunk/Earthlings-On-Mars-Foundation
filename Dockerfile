FROM nixos/nix:2.31.2 AS builder

COPY . /tmp/build
WORKDIR /tmp/build
RUN nix \
    --extra-experimental-features "nix-command flakes" \
    --option filter-syscalls false \
    build --show-trace
RUN mkdir /tmp/nix-store-closure
RUN cp -R $(nix-store -qR result/) /tmp/nix-store-closure

#RUN nix-env --install busybox
#RUN addgroup -S appgroup && adduser -S appuser -G appgroup
#RUN chown -R appuser:appgroup /app

FROM scratch

WORKDIR /app
COPY --from=builder /tmp/nix-store-closure /nix/store
COPY --from=builder /tmp/build/result /app

EXPOSE 8000
#USER appuser
CMD ["/app/bin/app"]
