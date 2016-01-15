# OpenFisca Web API Examples

You can also perform an HTTP request using [`curl`](http://curl.haxx.se/) and [`jq`](https://stedolan.github.io/jq/)
to format the response JSON:

```
curl http://localhost:2000/api/1/calculate -X POST --data @./examples/calculate_single_person_1.json --header 'content-type: application/json' | jq .
curl http://localhost:2000/api/1/simulate -X POST --data @./examples/simulate_single_person_1.json --header 'content-type: application/json' | jq .
```
