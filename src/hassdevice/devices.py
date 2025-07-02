import json
import logging
from types import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



class mqttClient():
    def device_type(self, device_type):
        self.device_type = device_type

    def connect(self, mqtt_client, discovery_prefix="homeassistant", node_id=None):
        """
        Connect this device to an MQTT broker

        :param mqtt_client: A connected MQTT client
        :param discovery_prefix: The discovery prefix set in the HomeAssistant config
        :param node_id: Will be included in the MQTT topics if set
        """
        self.discovery_prefix = discovery_prefix
        self.node_id = node_id
        self.client = mqtt_client
        if self.device_type == 'switch':
            self.client.message_callback_add(self.command_topic, self._on_command)
            self.client.subscribe(self.command_topic)

        self.client.publish(self.config_topic, json.dumps(self.config), retain=self.retain)
        logger.debug("Connected to broker, sent config to {}".format(self.config_topic))
 
    @property
    def config(self):
        if  self.device_type == 'switch':
            return {
                'name': self.name,
                'state_topic': self.state_topic,
                'command_topic': self.command_topic,
                'payload_on': self.payload_on,
                'payload_off': self.payload_off,
                'retain': self.retain
            }
        else:
            return {
                'name': self.name,
                'unit_of_measurement': 'W',
                # 'retain': self.retain
                }
        


    def _on_command(self, client, userdata, message):
        new_state = message.payload.decode('utf-8')
        logger.debug("Got command for new state {}, current state {}".format(new_state, self.state))
        if self._is_valid_state(new_state) and new_state != self.state:
            self.on_state_change(new_state)

    def _is_valid_state(self, state):
        return state in [self.payload_on, self.payload_off]

    def on_state_change(self, new_state):
        """
        Called when a state update request is recieved from the broker

        :param new_state: The state to set
        """
        self.state = new_state

    @property
    def state(self):
        """
        The state of the switch. Must be one of ``self.payload_on`` or ``self.payload_off``

        :getter: The last state the switch was set to (May be ``None`` if the state has never been set)
        :setter: Record the state change, and report it to the broker
        """
        return self._state

    @state.setter
    def state(self, value):
        if not self._is_valid_state(value):
            raise ValueError("New state must be one of {}, {}".format(self.payload_on, self.payload_off))

        self._state = value
        logger.debug("Publishing new state {}".format(value))
        #self.client.publish(self.state_topic, value, retain=self.retain)
    
    @property
    def base_topic(self):
        if self.discovery_prefix is None:
            raise ValueError("Must call .connect() first")

        path = filter(lambda x: x is not None, [self.discovery_prefix, self.device_type, self.node_id, self.entity_id])
        return "/".join(path)

    @property
    def config_topic(self):
        return "/".join([self.base_topic, "config"])

    @property
    def state_topic(self):
        return "/".join([self.base_topic, "state"])

    @property
    def command_topic(self):
        return "/".join([self.base_topic, "command"])

    @property
    def payload_on(self):
        """
        Payload to use to indicate the switch is on. Defaults to ``"ON"``
        """
        return "ON"

    @property
    def payload_off(self):
        """
        Payload to use to indicate the switch is off. Defaults to ``"OFF"``
        """
        
        return "OFF"

    @property
    def retain(self):
        """
        Should the messages sent to the broker have the 'retain' flag set. Defaults to ``True``
        """
        return True

    

class Switch(mqttClient):
    """
    An MQTT switch
    """

    def __init__(self, name, entity_id):
        """
        :param name: The display name to use in HomeAssistant
        :param entity_id: The entity_id to use in HomeAssistant
        """
        self.name = name
        self.entity_id = entity_id

        self.node_id = None
        self.client = None
        self.discovery_prefix = None
        self.device_type = "switch"
        self._state = None

class Sensor(mqttClient):
   """
   An MQTT sensor
   """
   pass

   def __init__(self, name, entity_id):
        """
        :param name: The display name to use in HomeAssistant
        :param entity_id: The entity_id to use in HomeAssistant
        """
        self.name = name
        self.entity_id = entity_id

        self.node_id = None
        self.client = None
        self.discovery_prefix = None
        self.device_type = "sensor"
        self._state = None
   

   def payload_energy_update(self, energy):
        """
        Payload to use to send energy updates.
        """
        self.client.publish(self.state_topic, energy, retain=self.retain)
