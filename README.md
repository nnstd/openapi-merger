# Openapi Merger


A simple microservice to merge upstream openapi servers.


## Config

env CONFIG_FILE - path to configuration (yaml)

example config:
```yaml
plugins:
  app:
    title: "Openapi merger" # title of app
    openapi_url: /openapi.json # optional
    docs_url: /docs # swagger optional 
    redoc_url: /redoc # redoc optional
  serving:
    port: 7560
  merge:
    upstreams:
      - http://localhost/openapi.json
```