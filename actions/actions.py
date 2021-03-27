# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, Form, EventType, UserUtteranceReverted
from rasa_sdk.forms import FormAction
from rasa_sdk.types import DomainDict
import os, json

import logging
import pathlib
import requests
import datetime as dt
from typing import Dict, Text, Any, List, Union, Optional, Tuple
from actions import ChitchatTulin


logger = logging.getLogger(__name__)
REQUESTED_SLOT = "requested_slot"
cities = pathlib.Path("data/dict.txt").read_text().split("\n")

ENDPOINTS = {
	"covid19_fromtopolicy": "http://wjt.newayz.com/api/ncp_news/ncov_policy?depart_place={}&destination={}"
}

def _create_path(base: Text, from_city: Text, to_city: Text) -> Text:
    return base.format(from_city, to_city)

class SearchCovid19Fromtopolicy(Action):

    def name(self) -> Text:
        return "action_search_covid19_fromtopolicy"



    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        from_city_code = tracker.get_slot("departure")
        to_city_code = tracker.get_slot("destination")
        intent = tracker.get_intent_of_latest_message()
        print("得到的slot是")
        print(tracker.get_slot("departure"))
        print(tracker.get_slot("destination"))
        print("识别意图结果是" + intent)
#        if intent == "query_covid19_fromtopolicy":
#            from_city_code = next(tracker.get_latest_entity_values(entity_type="city", entity_role='departure'))
#            to_city_code = next(tracker.get_latest_entity_values(entity_type="city", entity_role='destination'))
        print(from_city_code, to_city_code)
        request_path = _create_path(ENDPOINTS["covid19_fromtopolicy"], from_city_code, to_city_code)
        results = requests.get(request_path)
        results = results.content.decode('utf-8')
        results = json.loads(results)
        results = results['data']
        print(results)
        if results:
            from_city_name = results['depart_place']['city_name']
            from_city_policy = results['depart_place']['leave_policy']
            to_city_name = results['destination']['city_name']
            to_city_policy = results['destination']['entrance_policy']
            print(from_city_name,'\n',from_city_policy,'\n',to_city_name,'\n',to_city_policy)
            return [SlotSet("from_city_name", from_city_name), SlotSet("from_city_policy", from_city_policy), SlotSet("to_city_name", to_city_name), SlotSet("to_city_policy", to_city_policy)]
        else:
            print("No policy found.")
            return [SlotSet("from_city_policy", "not found"), SlotSet("to_city_policy", "not found")]

class UtterFromtoCityPolicy(Action):

    def name(self):
        return "action_utter_covid19_fromtopolicy"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        from_city_name = tracker.get_slot("from_city_name")
        from_city_policy = tracker.get_slot("from_city_policy")
        to_city_name = tracker.get_slot("to_city_name")
        to_city_policy = tracker.get_slot("to_city_policy")
        print(from_city_name,'\n',from_city_policy,'\n',to_city_name,'\n',to_city_policy)
        if (from_city_name == None) & (to_city_name == None):
            dispatcher.utter_message(text=f"没有找到这些城市")
        elif from_city_name == None:
            dispatcher.utter_message(text=f"没有找到离开的城市呢，不过为您找到以下信息\n\n前往{to_city_name}的政策是{to_city_policy}")
        elif to_city_name == None:
            dispatcher.utter_message(text=f"没有找到前往的城市呢，不过为您找到以下信息\n\n离开{from_city_name}的政策是{from_city_policy}")
        elif from_city_policy == None:
            dispatcher.utter_message(text=f"没有找到离开{from_city_name}的政策\n\n前往{to_city_name}的政策是{to_city_policy}")
        elif to_city_policy == None:
            dispatcher.utter_message(text=f"没有找到前往{to_city_name}的政策\n\n离开{from_city_name}的政策是{from_city_policy}")
        else:
            dispatcher.utter_message(text=f"离开{from_city_name}的政策是{from_city_policy}\n\n前往{to_city_name}的政策是{to_city_policy}")
        return [SlotSet("departure", None), SlotSet("destination", None), SlotSet("from_city_name", None), SlotSet("from_city_policy", None), SlotSet("to_city_name", None), SlotSet("to_city_policy", None)]

class ValidateFromtoCityForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_fromto_city_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Optional[List[Text]]:
        from_city = tracker.slots.get("departure")
        if from_city is not None:
            if from_city not in cities:
                return ["city_spelled_correctly"] + slots_mapped_in_domain
        return slots_mapped_in_domain

    async def extract_city_spelled_correctly(
        self, dispatcher: CollectingDispatcher, tracker: Tracker,domain: Dict
    ) -> Dict[Text, Any]:
        intent = tracker.get_intent_of_latest_message()
        return {"city_spelled_correctly": intent == "affirm"}

    def validate_city_spelled_correctly(
        self, 
        slot_value: Any, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        if tracker.get_slot("city_spelled_correctly"):
            return {"departure": tracker.get_slot("departure"), "city_spelled_correctly": True}
        return {"departure": None, "city_spelled_correctly": None}

    def validate_departure(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(f"离开的城市代码是{slot_value}")
        if len(slot_value) != 6:
            dispatcher.utter_message(text=f"城市名称不对哦")
            return {"departure": None}
        else:
            return {"departure": slot_value}

    def validate_destination(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(f"前往的城市代码是{slot_value}")
        if len(slot_value) != 6:
            dispatcher.utter_message(text=f"城市名称不对哦")
            return {"destination": None}
        else:
            return {"destination": slot_value}

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_show_time"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text=f"Hello, World! It's {dt.datetime.now()} now.")
        
        return []

class ActionDefaultFallback(Action):

    def name(self):
        return "action_default_fallback"

    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get('text')
        message = ChitchatTulin.get_response(text)
        if message is not None:
            dispatcher.utter_message(message)
        else:
            dispatcher.utter_template('utter_default', tracker, silent_fail=True)
        return [UserUtteranceReverted()]

