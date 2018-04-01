import sys
import time
from subprocess import PIPE, Popen
from threading  import Thread
from queue import Queue, Empty
from slackclient import SlackClient

def read_from_game(q):
    game_message = ''
    while True:
        try:  line = q.get(timeout=.1)
        except Empty:
            break
        else: # got line
            line = str(line)
            line = line.rstrip("'").rstrip('"')
            line = line.lstrip('b"').lstrip("b'")
            line = line.replace(r"\n",'\n')
            game_message += line

    return game_message

def enqueue_output(out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

def main():
    TOKEN = "TOKEN GOES HERE"
    GAME = "GAME.z5"
    CHANNEL = "#CHANNEL-NAME-HERE"
    CHANNEL_ID = "CHANNEL ID GOES HERE"
    USERNAME = "Testbot"
    ICON_EMOJI = ":robot_face:"
    DFROTZ_PATH = "./dfrotz"

    sc = SlackClient(TOKEN)
    if sc.rtm_connect():
        sc.api_call(
            "chat.postMessage",
            channel=CHANNEL,
            text="Let's play Interactive Fiction!",
            username=USERNAME,
            icon_emoji=ICON_EMOJI
            )

    p = Popen([DFROTZ_PATH, GAME], stdout=PIPE, stdin=PIPE, bufsize=1)

    q = Queue()
    t = Thread(target=enqueue_output, args=(p.stdout, q))
    t.daemon = True # thread dies with the program
    t.start()

    game_start_message = read_from_game(q)

    print(sc.api_call("chat.postMessage", channel=CHANNEL, text=game_start_message,username=USERNAME, icon_emoji=ICON_EMOJI))

    while True:
        msg = sc.rtm_read()
        if len(msg) > 0 and isinstance(msg[0],dict):
            messageInfo = msg[0]
            if "subtype" in messageInfo:
                if messageInfo["subtype"] == "bot_message":
                    print("smells like a bot")
                    continue
            if "channel" in messageInfo:
                if messageInfo["channel"] != CHANNEL_ID:
                    continue
            try:
                if messageInfo["type"] == "message":
                    print(messageInfo["user"] + " said: " + messageInfo["text"])
                    if messageInfo["text"].lower().find("quit") != -1:
                        print("Passing")
                        continue
                    if messageInfo["text"].lower().find("@") != -1:
                        print("Passing")
                        continue
                    if messageInfo["text"].lower().find("www") != -1:
                        print("URL?")
                        continue
                    if messageInfo["text"].find("`") != -1:
                        print("comment")
                        continue
                    p.stdin.write((messageInfo["text"].split("\n")[0] +"\n").encode())
                    p.stdin.flush()
                    game_message = read_from_game(q)
                    sc.api_call("chat.postMessage", channel=CHANNEL, text=game_message,username=USERNAME, icon_emoji=ICON_EMOJI)
            except:
                print("Didn't like message")
                print(messageInfo)

        time.sleep(1)

    print("done")

if __name__ == "__main__":
    ON_POSIX = 'posix' in sys.builtin_module_names
    main()
