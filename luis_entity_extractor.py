import json
from typing import Any, Dict, Optional, Text

import rasa.utils.io
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.extractors.extractor import EntityExtractor
from rasa.nlu.model import Metadata
from rasa.nlu.training_data import Message, TrainingData

try:
    from cfuzzyset import cFuzzySet as FuzzySet
except ImportError:
    from fuzzyset import FuzzySet


class LuisEntityExtractor(EntityExtractor):
    """
    This is a custom entity extractor accessing a LUIS configuration file that contains a list of entities.
    This class performs (fuzzy-)matching of an input against every known list entity. The most similar entities
    are returned as entities.
    """

    name = "LuisEntityExtractor"
    provides = ["entities"]
    requires = ["tokens"]

    def __init__(self, parameters: Dict[Text, Text]) -> None:
        super(LuisEntityExtractor, self).__init__(parameters)

        if parameters is None:
            raise AttributeError("No valid config given!")
        if not isinstance(parameters, dict):
            raise AttributeError(f"config has type {type(parameters)}")
        if "config" not in parameters.keys():
            raise AttributeError(f"config not given: parameters contains {parameters.keys()}")

        with open(parameters["config"]) as json_file:
            parsed = json.load(json_file)
        self._entities = self._load(parsed["closedLists"])

        self._min_confidence = 0.7 if "min_confidence" not in parameters.keys() else parameters["min_confidence"]

    def process(self, message: Message, **kwargs: Any) -> None:
        """
        Process an incoming message by determining the most similar (or matching) names.
        """
        extracted = self._match_entities(message)
        message.set("entities", message.get("entities", []) + extracted, add_to_output=True)

    def _load(self, parsed_entities):
        entities = []
        for group in parsed_entities:
            group_name = group["name"]
            for group_element in group["subLists"]:
                fuzzy = FuzzySet()
                for x in [group_element["canonicalForm"]] + group_element["list"]:
                    fuzzy.add(x)

                entity = {
                    "group": group_name,
                    "canonical": group_element["canonicalForm"],
                    "fuzzy": fuzzy
                }
                entities.append(entity)
        return entities

    def _match_entities(self, message: Message):
        """
        Perform fuzzy matching on each token of the message.
        A token contains its text, its offset, its end and optionally additional data.
        """
        extracted_entities = []
        tokens = message.get("tokens")
        for token in tokens:
            for entity in self._entities:
                matches = entity["fuzzy"].get(token.text)

                if matches is None:
                    continue
                for match in matches:
                    if match[0] < self._min_confidence:
                        continue
                    match = {
                        "start": token.start,
                        "end": token.end,
                        "value": entity["canonical"],
                        "confidence": match[0],
                        "entity": entity["group"],
                    }
                    extracted_entities.append(match)
        return extracted_entities
