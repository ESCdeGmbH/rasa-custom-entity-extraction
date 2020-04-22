import json
from typing import Any, Dict, Optional, Text

import pymysql
import rasa.utils.io
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.extractors import EntityExtractor
from rasa.nlu.model import Metadata
from rasa.nlu.training_data import Message, TrainingData

try:
    from cfuzzyset import cFuzzySet as FuzzySet
except ImportError:
    from fuzzyset import FuzzySet

class DatabaseEntityExtractor(EntityExtractor):
    """
    This is a custom name extractor accessing a database that contains a list of first- and lastnames.
    Infos about the database are stored in the config-file config.json.
    This class performs (fuzzy-)matching of an input against every known name. The most similar names
    are returned as entities.
    """

    name = "DatabaseEntityExtractor"
    provides = ["entities"]
    requires = ["tokens"]

    def __init__(self, parameters: Dict[Text, Text]) -> None:
        super(DatabaseEntityExtractor, self).__init__(parameters)

        if parameters is None: raise AttributeError("No valid config given!")        
        
        if not isinstance(parameters, dict): raise AttributeError(f"config has type {type(parameters)}")
        
        if "config" not in parameters.keys():
            raise AttributeError(f"config not given: parameters contains {parameters.keys()}")

        component_config = None
        with open(parameters["config"]) as json_file:
            component_config = json.load(json_file)
        
        
        self.min_confidence = float(component_config["minimumConfidence"])
        self.ents = {}
        try:
            self._get_entity_groups(component_config["database_config"], component_config["database_queries"])
        except Exception:
            import warnings
            warnings.warn("An error occured while fetching the database")
    
    def _get_entity_groups(self, database_config: Dict[Text, Text], database_queries: Dict[Text, Text]):
        db = pymysql.connect(host=database_config["host"],
                             user=database_config["user"],
                             passwd=database_config["password"],
                             db=database_config["database"])
        cur = db.cursor()
        print(f"Queries are: {database_queries.keys()}")
        for entity_key in database_queries.keys():
            cur.execute(database_queries[entity_key])
            current_entity = FuzzySet()
            for row in cur.fetchall():
                if len(row) != 1: raise SyntaxError(f"{entity_key}: query returned more than one column!")
                current_entity.add(row[0])
            self.ents[entity_key] = current_entity
        db.close()

    def train(self, training_data: TrainingData, config: RasaNLUModelConfig, **kwargs: Any) -> None:
        """
        Currently no training is needed for fuzzy matching.
        """
        pass

    def persist(self, file_name: Text, model_dir: Text) -> Optional[Dict[Text, Any]]:
        """
        Persist this component to disk for future loading.
        Currently does nothing because there is nothing to be persisted.
        """
        pass

    def process(self, message: Message, **kwargs: Any) -> None:
        """
        Process an incoming message by determining the most similar (or matching) names.
        """
        extracted = self.match_entities(message)
        message.set("entities", message.get("entities", []) + extracted, add_to_output=True)

    def match_entities(self, message: Message):
        """
        Perform fuzzy matching on each token of the message.
        A token contains its text, its offset, its end and optionally additional data.
        """
        extracted_entities = []
        tokens = message.get("tokens")
        for token in tokens:
            for entity_type in self.ents.keys():
                fuzzy_matches = self.ents[entity_type].get(token.text)
                for match in fuzzy_matches:
                    if match[0] < self.min_confidence: continue # skip low-confidence entities
                    entity = {
                        "start": token.offset,
                        "end": token.end,
                        "value": match[1],
                        "confidence": match[0],
                        "entity": entity_type,
                    }
                    extracted_entities.append(entity)    
        return extracted_entities
