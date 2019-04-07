from telethon import TelegramClient, events, sync
from telethon.tl.types import InputChannel
import yaml
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)

output_channels_by_input_channel = {}
channel_entity_by_channel_name = {}

def configure_channels(config):
    """
    Map each input channel to the output channel, in order as they
    appear in the config file
    """
    if len(config["input_channel_names"]) != len(config["output_channel_names"]):
        logger.error("There must be an equal number of input channel names as output channel names in the config file")
        sys.exit(1)

    for index in range(len(config["input_channel_names"])):
        input_name = config["input_channel_names"][index]
        output_name = config["output_channel_names"][index]
        output_channels_by_input_channel[input_name] = output_name
        channel_entity_by_channel_name[input_name] = None
        channel_entity_by_channel_name[output_name] = None

def start(config):
    configure_channels(config)
    client = TelegramClient(config["session_name"], 
                            config["api_id"], 
                            config["api_hash"])
    client.start()
    input_channels_entities = []
    for d in client.iter_dialogs():
        if d.name in config["input_channel_names"] or d.name in config["output_channel_names"]:
            channel_entity_by_channel_name[d.name] = InputChannel(d.entity.id, d.entity.access_hash)
        if d.name in config["input_channel_names"]:
            input_channels_entities.append(channel_entity_by_channel_name.get(d.name))

        # if d.name in config["input_channel_names"]:
        #     input_channels_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
        # if d.name == config["output_channel_names"]:
        #     output_channel_entity = InputChannel(d.entity.id, d.entity.access_hash)
            
    if len(channel_entity_by_channel_name) != len(output_channels_by_input_channel) * 2:
        logger.error("One or more channels were not found in the dialogs")
        sys.exit(1)

    logging.info(f"Listening on {len(output_channels_by_input_channel)} channels.")

    @client.on(events.NewMessage(chats=input_channels_entities))
    async def handler(event):
        output_channel_name = output_channels_by_input_channel[event.message.chat.title]
        output_channel_entity = channel_entity_by_channel_name[output_channel_name]
        await client.forward_messages(output_channel_entity, event.message)

    client.run_until_disconnected()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} CONFIG_PATH")
        sys.exit(1)
    with open(sys.argv[1], 'rb') as f:
        config = yaml.load(f)
    start(config)
