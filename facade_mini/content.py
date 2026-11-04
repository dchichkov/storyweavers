"""Original authored material for The Last Place Setting.

Beats, performances, social influence rules, and effects live outside the director.
This is intentionally a small authoring surface, not a general narrative language.
"""
from engine import Beat, Exchange, Goal, Performance


def P(id, *lines, effects=(), when=()):
    return Performance(id, tuple(lines), tuple(effects), tuple(when))


def G(id, *variants):
    return Goal(id, tuple(variants))


def C(path, op, value):
    return (path, op, value)


def E(op, path, value):
    return (op, path, value)


def person(anger, fear, trust, letter=False, receipt=False):
    return {"location": "dining_room", "memes": {"anger": anger, "fear": fear},
            "trust_player": trust, "trust_partner": 3, "accountable": False,
            "disclosed": False, "knows": {"letter": letter, "receipt": receipt}}


INITIAL = {
    "turn": 0,
    "people": {
        "mara": person(1, 3, 2, letter=True),
        "eli": person(1, 3, 2, receipt=True),
        "player": {"location": "dining_room", "insults": 0,
                   "caused_harm": False,
                   "knows": {"letter": False, "receipt": False},
                   "requested_space": False, "requested_talk": False},
    },
    "props": {
        "letter": {"owner": "mara", "location": "sideboard", "state": "folded"},
        "receipt": {"owner": "eli", "location": "sideboard", "state": "face_down"},
        "photo": {"owner": "couple", "location": "sideboard", "state": "upright"},
        "plates": {"owner": "couple", "location": "table", "state": "three_places"},
        "music": {"owner": "eli", "location": "shelf", "state": "playing"},
        "coat": {"owner": "player", "location": "hall_hook", "state": "hanging"},
        "key": {"owner": "mara", "location": "mara_pocket", "state": "carried"},
        "bag": {"owner": "mara", "location": "bedroom", "state": "empty"},
    },
}


def reveal(who, prop):
    return tuple([E("set", "people." + who + ".disclosed", True),
                  E("set", "props." + prop + ".state", "face_up")]
                 + [E("set", "people." + n + ".knows." + prop, True)
                    for n in ("mara", "eli", "player")]
                 + [E("add", "people." + ("eli" if who == "mara" else "mara") + ".memes.anger", 1)])


MARA_TRUTH = P("mara_truth",
    'Mara unfolds the letter. "I accepted a six-month restoration residency in another city. I leave on Monday."',
    'Eli: "Accepted. Not applied."',
    'Mara: "Yes. I told myself I would tell you when the right evening came."',
    effects=reveal("mara", "letter"))
ELI_TRUTH = P("eli_truth",
    'Eli turns over the receipt. "I paid the deposit on the shop downstairs. From our joint savings."',
    'Mara: "You spent the money I thought we were keeping for choices."',
    'Eli: "I thought a workshop of our own would make you want to stay."',
    effects=reveal("eli", "receipt"))


BEATS = (
    Beat("arrival", "arrival", "dinner", 2, (
        G("threshold", P("welcome",
            "THE LAST PLACE SETTING",
            "You arrive at Mara and Eli's flat for their anniversary dinner. They asked you, an old friend, to be their only guest.",
            "Three plates wait under a low lamp. On the sideboard are a folded letter, a face-down receipt, and a photograph of the two of them outside an empty shop.",
            'Eli takes your coat. "Perfect timing. We were just deciding what to celebrate."',
            'Mara: "Our anniversary, Eli. That was the invitation."')),
        G("invitation", P("sit",
            'Mara pulls out the third chair. "Sit beside whoever you like. Apparently that matters tonight."',
            'Eli: "It doesn\'t." He straightens the fork beside your plate without looking at her.')),
    ), resume='Mara keeps a hand on your chair. "Come and sit down."'),
    Beat("photograph", "topics", "photo", 4, (
        G("entry", P("remember",
            'Eli turns the photograph toward you. "Remember this place? We said we could make anything there."',
            'Mara: "We were twenty-three. We said a lot of things."')),
        G("dispute", P("past_tense",
            'Eli: "You used to like that picture."',
            'Mara: "I still do. I don\'t want to live inside it."',
            effects=(E("add", "people.eli.memes.fear", 1),))),
        G("exit", P("set_down",
            "Eli sets the photograph down carefully, leaving it facing Mara.",
            'Mara: "Ask me what I want now. Not what I wanted when that was taken."')),
    ), resume='Eli touches the photograph\'s frame. "About what we wanted then—"'),
    Beat("letter", "topics", "letter", 4, (
        G("entry", P("already_open", 'Eli looks at the open letter. "Monday. You had a date all this time."',
                     when=(C("people.mara.disclosed", "eq", True),)),
          P("fold", 'Mara notices you looking at the letter and folds it smaller.',
            'Eli: "More work?"', 'Mara: "Something like that."')),
        G("dispute", P("owned", 'Mara: "I still want to go. I want to be able to say that to you honestly."',
                       'Eli: "I am trying to hear the difference."',
                       when=(C("people.mara.accountable", "eq", True),)),
          P("choice", 'Mara: "I need to do something that belongs to me."',
                       'Eli: "I thought we were building something together."',
                       effects=(E("add", "people.mara.memes.fear", 1),))),
        G("exit", P("disclosed", 'Mara leaves the letter where Eli can read it. "At least it isn\'t hidden now."',
                     when=(C("people.mara.disclosed", "eq", True),)),
          P("waiting", 'Mara leaves the folded letter on the sideboard, within reach.',
            'Mara: "If you want to ask about it, ask me directly."')),
    ), resume='Mara looks back at the letter. "We were talking about my work."'),
    Beat("receipt", "topics", "receipt", 4, (
        G("entry", P("known", 'Mara taps the face-up receipt. "You made a future and charged both of us for it."',
                     when=(C("people.eli.disclosed", "eq", True),)),
          P("hidden", 'Eli moves the receipt away from a ring of spilled water.',
            'Mara: "What did you buy?"', 'Eli: "An opportunity."')),
        G("dispute", P("owned", 'Eli: "The workshop is something I wanted. I can see I put your name on my wish."',
                       'Mara: "Then we can start by calling it yours."',
                       when=(C("people.eli.accountable", "eq", True),)),
          P("plan", 'Eli: "I wanted to give you somewhere to work."',
                       'Mara: "Then you could have asked where I wanted to work."',
                       effects=(E("add", "people.eli.memes.fear", 1),))),
        G("exit", P("known", 'Eli leaves the receipt face up. "I can\'t call it a surprise anymore."',
                     when=(C("people.eli.disclosed", "eq", True),)),
          P("hidden", 'Eli leaves the receipt on the sideboard. His thumb has creased one corner.',
            'Eli: "It was meant to be good news."')),
    ), resume='Eli smooths the receipt\'s corner. "About that opportunity—"'),
    Beat("place_setting", "topics", "plates", 4, (
        G("entry", P("dinner", 'Mara: "We could eat before everything gets cold."',
                     'Eli: "I thought we might have a toast first."')),
        G("dispute", P("audience", 'Mara: "Did you invite our friend for dinner, or for an audience?"',
                       'Eli: "I thought we behaved better with someone here."',
                       effects=(E("add", "people.mara.memes.anger", 1),))),
        G("exit", P("not_judge", 'Mara looks at you. "You don\'t have to decide who wins."',
                     'Eli draws his glass back from the center of the table.')),
    ), resume='Mara nudges her plate. "We haven\'t even started dinner."'),
    Beat("record", "topics", "music", 4, (
        G("entry", P("song", 'The record reaches a song Mara knows. She reaches toward the player, then stops.',
                     'Eli: "Our song."', 'Mara: "Your favorite song."')),
        G("dispute", P("volume", 'Eli: "You never said you didn\'t like it."',
                       'Mara: "I\'m saying it now. Can that be enough?"',
                       effects=(E("add", "people.mara.memes.anger", 1),))),
        G("exit", P("quiet", "Eli lifts the needle. In the sudden quiet, the refrigerator sounds loud.",
                     'Eli: "All right. I can hear you."',
                     effects=(E("set", "props.music.state", "stopped"),))),
    ), resume='Eli glances toward the record player. "I thought we both liked it."'),
    Beat("reckoning", "crisis", "truth", 6, (
        G("mara", P("known", 'Mara: "The residency starts on Monday. That date is not going to move because we avoid it."',
                     when=(C("people.mara.disclosed", "eq", True),)),
          P("voluntary", *MARA_TRUTH.lines, effects=MARA_TRUTH.effects,
            when=(C("people.mara.trust_player", "ge", 3), C("people.mara.memes.anger", "le", 5))),
          P("withheld", 'Mara places her hand over the letter. "There is something I should say. I don\'t feel safe saying it like this."')),
        G("eli", P("known", 'Eli: "The deposit is paid. I need to find out how much we can recover."',
                     when=(C("people.eli.disclosed", "eq", True),)),
          P("voluntary", *ELI_TRUTH.lines, effects=ELI_TRUTH.effects,
            when=(C("people.eli.trust_player", "ge", 3), C("people.eli.memes.anger", "le", 5))),
          P("withheld", 'Eli covers the receipt with his palm. "I had a plan. I can hear how it would sound now."')),
        G("question", P("turn", 'Mara: "We keep making decisions around each other."',
                       'Eli looks at you. "How do we stop doing that?"')),
    ), priority=1, resume='Mara draws her chair back to the table. "There is still something we need to say."'),
    Beat("decision", "decision", "future", 3, (
        G("opening", P("choice", 'Eli: "We can\'t leave tonight exactly where we started."',
                       'Mara: "Then let\'s choose one thing we can actually do. Not a whole life."')),
        G("pause", P("space", "Mara takes her flat key from her pocket and lays it beside her plate.",
                     'Mara: "I\'m keeping my key. A night apart isn\'t a verdict on everything."',
                     effects=(E("set", "props.key.location", "table"), E("set", "props.key.state", "set_down")),
                     when=(C("people.player.requested_space", "eq", True),)),
          P("pause", "Mara and Eli wait. For once, neither fills the silence for the other.")),
        G("last_chance", P("ready", "Eli lowers the hall light. The evening has come to its last decision.")),
    ), resume='Eli: "Before you go—what do we do with tonight?"'),
)


MIXINS = {
    "letter": (
        (P("known", 'Mara: "That is the residency acceptance. Six months away, starting Monday."',
           when=(C("people.mara.disclosed", "eq", True),)),
         P("hint", 'Mara: "The conservation institute wrote to me. It isn\'t a bill."',
           'Eli: "You applied?"', 'Mara: "Yes."')),
        (P("known", 'Mara: "The acceptance has my name on it. The dates are there in writing."',
           when=(C("people.mara.disclosed", "eq", True),)),
         P("refused", 'Mara holds the letter against her chest. "Stop pushing. I need you to listen first."',
           when=(C("people.mara.memes.anger", "gt", 5),)), MARA_TRUTH),
    ),
    "receipt": (
        (P("known", 'Eli: "It\'s the workshop deposit. I used our joint savings."',
           when=(C("people.eli.disclosed", "eq", True),)),
         P("hint", 'Eli: "It\'s a deposit. For the empty shop in the photograph."',
           'Mara: "A deposit? Eli, how much planning have you done?"')),
        (P("known", 'Eli: "I have to call the agent tomorrow. I don\'t know how much we can recover."',
           when=(C("people.eli.disclosed", "eq", True),)),
         P("refused", 'Eli puts his hand over the receipt. "Stop pushing. I need you to listen first."',
           when=(C("people.eli.memes.anger", "gt", 5),)), ELI_TRUTH),
    ),
    "photo": (
        (P("memory", 'Mara: "We posed outside that empty shop on our first anniversary."',
           'Eli: "You said you wanted a studio with those windows."',
           'Mara: "I remember. I want you to remember that I can change."'),),
        (P("difference", 'Mara: "I liked the light. Eli liked that we would work together."',
           'Eli: "I didn\'t know those were different wishes."'),),
    ),
}


EXCHANGES = {}
for who, other, name, other_name in (("mara", "eli", "Mara", "Eli"), ("eli", "mara", "Eli", "Mara")):
    base, partner = "people." + who + ".", "people." + other + "."
    EXCHANGES["empathize " + who] = Exchange("empathize", "Give " + name + " room to speak without taking sides.", (
        P("heard", name + ': "Thank you. Let me find a way to say this without making it another accusation."',
          other_name + ': "I can wait for that."', effects=(
              E("add", base + "trust_player", 2), E("add", base + "memes.anger", -1),
              E("add", base + "memes.fear", -1))),))
    EXCHANGES["support " + who] = Exchange("support", "Take " + name + "'s side.", (
        P("alliance", name + ': "At least you understand why I feel cornered."',
          other_name + ': "So I\'m the problem. That was quick."', effects=(
              E("add", base + "trust_player", 1), E("add", partner + "trust_player", -1),
              E("add", partner + "memes.anger", 1))),))
    EXCHANGES["blame " + who] = Exchange("blame", "Tell " + name + " this is their fault.", (
        P("defensive", name + ': "You came here for dinner. Don\'t tell me what my whole life means."',
          other_name + ': "I didn\'t ask you to attack anyone."', effects=(
              E("set", "people.player.caused_harm", True),
              E("add", base + "trust_player", -2), E("add", base + "memes.anger", 2),
              E("add", base + "trust_partner", -1))),))
    responsibility = ('"I chose not to tell you about the residency. Being afraid of the argument doesn\'t excuse that."'
                      if who == "mara" else
                      '"I used our money without asking. Calling it a gift doesn\'t make that fair."')
    EXCHANGES["reflect " + who] = Exchange("reflect", "Ask " + name + " to take responsibility for their concealed decision.", (
        P("accountability", name + ": " + responsibility,
          other_name + ': "That is the first time I\'ve heard you say it without a but."', effects=(
              E("set", base + "accountable", True), E("add", base + "memes.anger", -1),
              E("add", base + "memes.fear", -1), E("add", partner + "trust_partner", 1))),),
        influences=(
            ((C(base + "disclosed", "eq", True),), 2, "The decision is public"),
            ((C(base + "trust_player", "ge", 3),), 2, "The speaker trusts the guest"),
            ((C(base + "memes.anger", "le", 5),), 2, "Anger leaves room to listen"),
        ), threshold=6)

EXCHANGES["apologize"] = Exchange("apologize", "Apologize for your own part in the argument.", (
    P("not_needed", 'You: "I\'m sorry. I don\'t want to make this harder."',
      'Mara: "You haven\'t. This isn\'t yours to apologize for."',
      when=(C("people.player.caused_harm", "eq", False),)),
    P("apology", 'You: "I came here as your friend. I\'m sorry I made this harder."',
      'Mara: "All right. Start again, but more gently."',
      'Eli lets out a breath.', effects=tuple(
          effect for who in ("mara", "eli") for effect in (
              E("add", "people." + who + ".trust_player", 1),
              E("add", "people." + who + ".memes.anger", -1)))),))
EXCHANGES["mediate"] = Exchange("mediate", "Ask them to agree on one honest conversation tomorrow.", (
    P("agreement", 'You: "Tomorrow, could you talk about both decisions before making another one?"',
      'Mara: "A conversation. Not a promise that I stay."',
      'Eli: "Yes. I can agree to that."', effects=(
          E("set", "people.player.requested_talk", True),
          E("add", "people.mara.trust_partner", 1),
          E("add", "people.eli.trust_partner", 1))),), influences=(
              ((C("people.mara.accountable", "eq", True),), 2, "Mara owns her decision"),
              ((C("people.eli.accountable", "eq", True),), 2, "Eli owns his decision"),
              ((C("people.mara.memes.anger", "le", 5), C("people.eli.memes.anger", "le", 5)), 2, "Both can listen"),
          ), threshold=6)
EXCHANGES["space"] = Exchange("space", "Suggest that they take a night apart before deciding anything.", (
    P("space", 'You: "Would a night apart give you room to think?"',
      'Mara: "I can stay with my sister. One night, for now."',
      'Eli: "I won\'t try to stop you."',
      effects=(E("set", "people.player.requested_space", True),)),))


def ending_effects(plates):
    return (E("set", "people.player.location", "hallway"),
            E("set", "props.coat.location", "player"), E("set", "props.coat.state", "worn"),
            E("set", "props.plates.state", plates))


ENDINGS = (
    ("space", (P("night_apart",
        "Mara retrieves her key, packs a small overnight bag, and joins you at the door. Eli holds it without standing in it.",
        'Mara: "Tomorrow. We can decide what tomorrow means then."',
        "You walk with her as far as the stairs. Behind you, Eli carries one untouched plate to the kitchen; two remain under the lamp.",
        effects=ending_effects("two_places") + (
            E("set", "people.mara.location", "hallway"), E("set", "props.key.location", "mara_pocket"),
            E("set", "props.key.state", "carried"), E("set", "props.bag.location", "mara"),
            E("set", "props.bag.state", "packed"))),),
     (C("people.player.requested_space", "eq", True),)),
    ("repair", (P("tomorrow",
        "Eli places the receipt beside the open letter, where neither can cover the other.",
        'Eli: "I\'ll call the agent tomorrow. Then we talk about Monday."',
        'Mara: "And I\'ll tell you what I want from those six months. The actual answer."',
        "You collect your coat. As the door closes, Mara moves her chair beside Eli's. The two papers stay between their plates.",
        effects=ending_effects("two_chairs_together") + (
            E("set", "props.letter.location", "table"), E("set", "props.receipt.location", "table"))),),
     (C("people.player.requested_talk", "eq", True),
      C("people.mara.accountable", "eq", True), C("people.eli.accountable", "eq", True),
      C("people.mara.trust_partner", "ge", 4), C("people.eli.trust_partner", "ge", 4),
      C("people.mara.memes.anger", "le", 5), C("people.eli.memes.anger", "le", 5))),
    ("unresolved", (
        P("truth_without_repair",
          'Mara: "We have finally said what happened. I don\'t know what to do with it yet."',
          'Eli: "Neither do I."',
          "You take your coat. The letter and receipt lie face up on the sideboard, but the hosts leave their chairs on opposite sides of the table. All three plates are still untouched.",
          effects=ending_effects("three_untouched"),
          when=(C("people.mara.disclosed", "eq", True), C("people.eli.disclosed", "eq", True))),
        P("one_truth",
          'Mara: "That is enough for tonight." Eli doesn\'t argue.',
          "You take your coat. One paper lies face up on the sideboard; a hand still guards the other. The three untouched plates look like places reserved for people who never arrived.",
          effects=ending_effects("three_untouched"), when=(C("people.mara.disclosed", "eq", True),)),
        P("one_truth_eli",
          'Eli: "That is enough for tonight." Mara doesn\'t argue.',
          "You take your coat. One paper lies face up on the sideboard; a hand still guards the other. The three untouched plates look like places reserved for people who never arrived.",
          effects=ending_effects("three_untouched"), when=(C("people.eli.disclosed", "eq", True),)),
        P("polite",
          'Eli: "We should do this again when we\'re less tired."',
          'Mara opens the door for you. "Good night."',
          "You take your coat. Behind you, the letter stays folded and the receipt stays face down. Three untouched plates shine under the lamp.",
          effects=ending_effects("three_untouched")),
     ), ()),
    ("ejected", (P("door",
        "Mara takes your coat from the hook and hands it to you. Eli opens the door.",
        'Mara: "Whatever happens between us, this isn\'t how you get to treat us."',
        "The door shuts behind you. Through it comes the small, sharp sound of your plate being stacked on the other two.",
        effects=ending_effects("stacked")),), ()),
    ("left", (P("departure",
        'You: "I should go." You take your coat from the hall hook.',
        "Neither host asks you to stay. As you step into the hallway, Eli lifts your unused fork and puts it beside his own. Your empty chair remains between them.",
        effects=ending_effects("guest_fork_removed")),), ()),
)

from content_ext import extend
BEATS, EXCHANGES, MIXINS, ENDINGS = extend(INITIAL, BEATS, EXCHANGES, MIXINS, ENDINGS)
