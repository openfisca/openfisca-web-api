# OpenFisca Web API Examples

You can also perform an HTTP request using [`curl`](http://curl.haxx.se/) and [`jq`](https://stedolan.github.io/jq/)
to format the response JSON:

```
curl http://localhost:2000/api/1/calculate -X POST --data @./examples/calculate_single_person_1.json --header 'content-type: application/json' | jq .

{
  "apiVersion": 1,
  "method": "/api/1/calculate",
  "params": {
    ... skipped ...
  },
  "url": "http://localhost:2000/api/1/calculate",
  "value": [
    {
      "familles": [
        {
          "id": 0,
          "parents": [
            "individu0"
          ]
        }
      ],
      "foyers_fiscaux": [
        {
          "id": 0,
          "declarants": [
            "individu0"
          ]
        }
      ],
      "individus": [
        {
          "id": "individu0",
          "birth": "1980-01-01"
        }
      ],
      "menages": [
        {
          "id": 0,
          "personne_de_reference": "individu0",
          "revdisp": {
            "2015": 5332.3701171875
          }
        }
      ]
    }
  ]
}
```
