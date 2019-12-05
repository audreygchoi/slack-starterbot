import os
import time
import random
import re
from slackclient import SlackClient


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
PICK_COMMAND = "pick"
EXAMPLE_COMMAND = "do"
ASSIGN_DIFF_COMMAND = "assign-diff"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
DEFAULT_PICK_ERROR_RESPONSE = """I couldn't understand your command...
Try `@choosy pick [number] from [comma separated list of choices]`"""
DEFAULT_ASSIGN_DIFF_ERROR_RESPONSE = """I couldn't understand your command...
Try `@choosy assign-diff [diff id] from [comma separated list of reviewers]`"""

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(PICK_COMMAND):
        response = _handle_pick_command(command)
    elif command.startswith(ASSIGN_DIFF_COMMAND):
        response = _handle_assign_diff_command(command)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


def _handle_pick_command(command):
    response = None

    try:
        command_inputs = command.split(' ', 2)
        number_of_picks = command_inputs[1]

        if not number_of_picks.isdigit():
            response =  DEFAULT_PICK_ERROR_RESPONSE

        choices_input = command_inputs[2]

        if not choices_input.startswith("from"):
            response = DEFAULT_PICK_ERROR_RESPONSE

        choices = choices_input.split(' ', 1)[1].split(',')
        response_list = []
        for n in range(int(number_of_picks)):
            pick = random.choice(choices)
            response_list.append(pick.strip())
            choices.remove(pick)

        response = "I pick " + ", ".join(response_list)

    except IndexError:
        response = DEFAULT_PICK_ERROR_RESPONSE

    return response


def _handle_assign_diff_command(command):
    response = None
    try:
        command_inputs = command.split(' ', 2)
        diff_id = command_inputs[1]

        if not diff_id.upper().startswith("D"):
            response = "That isn't a valid diff id, it should start with `D`"

        choices_input = command_inputs[2]
        print choices_input

        if not choices_input.startswith("from"):
            response = DEFAULT_ASSIGN_DIFF_ERROR_RESPONSE

        choices = choices_input.split(' ', 1)[1].split(',')
        response_list = []
        pick = random.choice(choices)

        _add_reviewer_to_diff(diff_id, pick)

        response = "I assigned {diff_id} to {pick}".format(diff_id=diff_id, pick=pick)
    except IndexError:
        response = DEFAULT_ASSIGN_DIFF_ERROR_RESPONSE

    return response


def _add_reviewer_to_diff(diff_id, pick):
    pass


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Choosy connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
