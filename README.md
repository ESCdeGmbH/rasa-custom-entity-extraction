# Custom Entity Extraction for RASA
This repository contains some custom entity extractors for RASA. Further details will follow below.

## Simple Entity Extractor
An entity extractor for Json files. A sample for such Json file can be found [here](rasa_simple_config_sample.json).

A sample config for RASA:

```yml
language: en
pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: simple_entity_extractor.SimpleEntityExtractor
    config: "myconfig.json"
    min_confidence: 0.8
```


## Database Entity Extractor
An entity extractor for [MySQL](https://www.mysql.com/). You can simply use the a database to extract entities via fuzzy sets. You have to define queries for the different entity types.

A sample config for the extractor is [here](rasa_cer_config_sample_db.json):

```json
{
  "database_config": {
    "host": "<host_ip_address>",
    "user": "<database_user>",
    "password": "<database_user_pw>",
    "database": "<database_name>"
  },
  "database_queries": {
    "firstnames": "SELECT name FROM NamesDB WHERE EntityType = 'firstname';",
    "lastnames": "SELECT name FROM NamesDB WHERE EntityType = 'lastname';"
  },
  "minimumConfidence": 0.81
}
```

A sample config for RASA could look like [here](rasa_config_sample_db.yml)
```yml
language: en
pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: database_entity_extractor.DatabaseEntityExtractor
    config: "/path/to/sample_config.json"
```

## LUIS Entity Extractor
An entity extractor for [LUIS](https://www.luis.ai). You can simply use the exported LUIS model to extract entities via fuzzy sets. Currently only list entities are supported.

A sample config for RASA:

```yml
language: en
pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: luis_entity_extractor.LuisEntityExtractor
    config: "luis.json"
    min_confidence: 0.8
```
