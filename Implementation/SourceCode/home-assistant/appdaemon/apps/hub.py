# import json
from enum import Enum
from typing import Union

import appdaemon.plugins.hass.hassapi as hass

NETFLIX = "com.netflix.ninja"
DISNEY_PLUS = "com.disney.disneyplus"
YOUTUBE = "YouTube (FireTV)"  # "com.google.android.youtube.tv"

# this is crunchyrolls id but it doesn't seem to be working
CRUNCHYROLL = "com.crunchyroll.crunchyroid"

# this source is not really working there are 3 different names pointing to prime
PRIME = "Amazon Video"  # "com.amazon.avod"

FIRE_TV = "media_player.fire_tv_smart_lab"
HARMONY = {
    "id": "remote.harmony_hub",
    "command_service": "remote/send_command"
}


class FireTvCommand(Enum):
    """Enum that has all available commands that can be used"""
    POWER = "POWER"
    SLEEP = "SLEEP"
    HOME = "HOME"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    CENTER = "CENTER"
    BACK = "BACK"
    MENU = "MENU"


class Hub(hass.Hass):
    """
        Listens to the webhook event and
        executes the code needed to toggle the 
        devices
    """
    async def initialize(self):
        # state = self.get_state()
        # self.log(json.dumps(state, indent=4))
        self.listen_event(self.toggle_tv, event="room")

    async def toggle_tv(self, event: Union[str, list], data: dict, kwargs):
        try:
            if self.entity_exists(HARMONY["id"]):
                person_in_room: bool = data["data"]["person_in_room"]
                if person_in_room:
                    self.log("Turning on TV")
                    await self.send_to_tv("PowerOn")
                    await self.go_to_home()
                    # We wait until the tvs display starts and then we do something
                    # it's not necessary but to see what happens we wait
                    await self.sleep(5)
                    # open the selected app
                    await self.open_app(NETFLIX)

                    for _ in range(2):
                        await self.firetv_click(FireTvCommand.CENTER)
                        await self.sleep(1)
                else:
                    self.log("Turning off TV")
                    await self.send_to_tv("PowerOff")
        except Exception as err:
            self.error(err)

    async def go_to_home(self):
        """simulates a click on the Home button on the firetv stick"""
        await self.call_service(
            "androidtv/adb_command",
            entity_id=FIRE_TV,
            command=FireTvCommand.HOME.value,
            return_result=True
        )

    async def firetv_click(self, command: FireTvCommand):
        """helper method to send a command to the firetv stick"""
        await self.call_service(
            "androidtv/adb_command",
            entity_id=FIRE_TV,
            command=command.value
        )

    async def open_app(self, app_id):
        """
        opens an app by selecting source

        Parameters
        ----------
            app_id
                the id of the id. example: "Netflix" or "com.netflix.ninja"
        """
        res = await self.call_service(
            "media_player/select_source",
            entity_id=FIRE_TV,
            source=app_id,
            return_result=True)
        self.log(f"res: {res}")

    async def send_to_tv(self, command):
        """helper method for the tv in the lab"""
        device = "77186046"  # can also be the name: Smart Lab Fernseher
        await self.send_to_hub(command, device)

    async def send_to_hub(self, command, device):
        """Sends a command to the specified device.

            The command list for each registered device is availabe in 
            the root directory of home assistant os 
        """
        await self.call_service(
            HARMONY["command_service"],
            entity_id=HARMONY["id"],
            command=command,
            device=device,
            return_result=True)
