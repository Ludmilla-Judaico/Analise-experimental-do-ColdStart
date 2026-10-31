FROM golang:1.22 AS build
ARG WORKLOAD=minimal
WORKDIR /src
COPY go.mod .
COPY main_${WORKLOAD}.go main.go
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /server main.go

FROM gcr.io/distroless/static
COPY --from=build /server /server
ENTRYPOINT ["/server"]