
def gather(text, callback: str, digits=None, min_digits=None, max_digits=None):
    data = {
        "verb": "gather",
        "actionHook": callback,
        "input": ["digits"], #Can also include "speech"
        "bargein": False,
        "dtmfBargein": True,
        "finishOnKey": "#",
        "say": say(text),
        "interDigitTimeout": 5
    }

    del data["say"]["verb"]

    if digits is not None:
        data["numDigits"] = digits
    if min_digits is not None:
        data["minDigits"] = min_digits
    if max_digits is not None:
        data["maxDigits"] = max_digits

    return data

    #self.timeout = 8

    #self.  "recognizer": {
    #self.    "vendor": "Google",
    #self.    "language": "en-US",
    #self.    "hints": ["sales", "support"],
    #self.    "hintsBoost": 10
    #self.  },

def say(text):
    return {
        "verb": "say",
        "text": text
    }
