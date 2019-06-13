from channels.generic.websocket import JsonWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
class NotifyConsumer(JsonWebsocketConsumer):

    def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['room_id']
        self.group_name = "group_" + self.event_id
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        print("Closed websocket with code: ", close_code)
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )
        self.close()

    def receive_json(self, content, **kwargs):
        print("Received event: {}".format(content))
        self.send_json(content)

    # ------------------------------------------------------------------------------------------------------------------
    # Handler definitions! handlers will accept their corresponding message types. A message with type event.alarm
    # has to have a function event_alarm
    # ------------------------------------------------------------------------------------------------------------------

    def events_alarm(self, event):
        self.send_json(
            {
                'type': 'events.alarm',
                'content': event['content']
            }
        )