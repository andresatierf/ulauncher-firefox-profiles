import os
import subprocess
import json
import configparser
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction


def readConfig(firefox_config_folder):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(os.path.join(firefox_config_folder, "profiles.ini"))
    return config


def scan_firefox_folder(firefox_config_folder):
    profiles = []

    config = readConfig(firefox_config_folder)

    profile_list = list(
        filter(lambda section: "profile" in section.lower(), config.sections())
    )

    profile_list.sort(),
    return list(
        filter(
            lambda profile: "release" not in profile["name"],
            map(
                lambda profile: {
                    "name": config[profile]["Name"],
                    "description": profile,
                },
                profile_list,
            ),
        )
    )


class FirefoxProfilesExtension(Extension):
    def __init__(self):
        super(FirefoxProfilesExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        firefox_config_folder = os.path.expanduser(
            extension.preferences["firefox_folder"]
        )
        profiles = scan_firefox_folder(firefox_config_folder)

        # Filter by query if inserted
        query = event.get_argument()
        if query:
            query = query.strip().lower()
            for profile in profiles:
                name = profile["name"].lower()
                if query not in name:
                    profiles.remove(profile)

        # Create launcher entries
        entries = []
        for profile in profiles:
            entries.append(
                ExtensionResultItem(
                    icon="images/icon.png",
                    name=profile["name"],
                    description=profile["description"],
                    on_enter=ExtensionCustomAction(
                        {
                            "firefox_cmd": extension.preferences["firefox_cmd"],
                            "opt": ["-P", profile["name"]],
                        },
                        keep_app_open=False,
                    ),
                )
            )
        entries.append(
            ExtensionResultItem(
                icon="images/incognito.png",
                name="Incognito",
                description="Launch browser in a private window",
                on_enter=ExtensionCustomAction(
                    {
                        "firefox_cmd": extension.preferences["firefox_cmd"],
                        "opt": ["--private-window"],
                    },
                    keep_app_open=False,
                ),
            )
        )
        return RenderResultListAction(entries)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        # Open Firefox when user selects an entry
        data = event.get_data()
        firefox_path = data["firefox_cmd"]
        opt = data["opt"]
        command = []
        command.append(firefox_path)
        command.extend(opt)
        subprocess.Popen(command)


if __name__ == "__main__":
    FirefoxProfilesExtension().run()
