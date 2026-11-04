"""Authored private exchanges and state-driven character initiative.

The kitchen is an actual audience boundary. No public goal executes while the
guest and one host are there. Every disclosure names its recipients in effects.
"""
from content import P, C, E, reveal, MARA_TRUTH, ELI_TRUTH


PRIVATE = {
    "mara": {
        "work": (
            P("mara_private_work",
              'Mara stands beside the sink rather than facing you. "There is a restoration residency. Six months, starting Monday. I accepted it."',
              'She watches a drop travel down the tap. "Eli doesn\'t know. I keep trying to find a version of the sentence that won\'t hurt him. There isn\'t one."',
              'You can hear a chair move in the other room, but not Eli\'s voice.',
              effects=(E("set", "people.player.knows.letter", True),)),
            P("mara_private_work_depth",
              'Mara: "They sent me a test piece. A woman\'s face under three layers of brown varnish. I spent two nights getting one eye clear."',
              '"When I sent it back, the director wrote that he wanted my judgment, not just my hands. Do you know how long it has been since someone asked for that?"',
              'She dries the same clean teaspoon twice. "I can want this without wanting to erase Eli. I need him to believe those can both be true."',
              effects=(E("set", "people.player.knows.mara_need", True), E("set", "people.mara.heard", True))),
        ),
        "fear": (
            P("mara_private_fear",
              'Mara: "My mother used to say she would paint when things settled down. When we were older. When the spare room was clear."',
              '"After she died, we found twenty-three untouched canvases in that room. Still in their wrapping."',
              'She looks through the doorway. "Eli isn\'t my father. I know that. Sometimes I punish him for a life he hasn\'t asked me to live."',
              effects=(E("set", "people.player.knows.mara_fear", True), E("set", "people.mara.heard", True))),
            P("mara_private_fear_depth",
              'Mara: "If I tell him before I am certain, I will hear all his reasons. They will be good reasons. Money. The roof. His father needing help."',
              '"Then I will say I chose to stay. And one day I\'ll hate him for a choice I didn\'t let him know he was making with me."',
              'She finally turns toward you. "Keeping him out of the decision is not freedom. It\'s just a different kind of locked door."',
              effects=(E("set", "people.mara.insight", True), E("add", "people.mara.memes.fear", -1))),
        ),
    },
    "eli": {
        "work": (
            P("eli_private_work",
              'Eli closes the kitchen door most of the way. "I paid a deposit on the shop downstairs. Out of our joint account."',
              '"I had this picture of telling her over dinner. Her laughing. Us going down with a tape measure."',
              'He turns a mug so the chipped side faces the wall. "Mara hasn\'t seen the amount. I know how this sounds."',
              effects=(E("set", "people.player.knows.receipt", True),)),
            P("eli_private_work_depth",
              'Eli: "The shop is not really the first thing I should have told her. The repair firm cut my hours in June. I\'ve been calling the extra days freelance time."',
              '"I wanted to arrive with a solution before I admitted there was a problem. A business with both our names seemed like a solution."',
              'He puts the mug down. "Mostly it meant I wouldn\'t have to tell her I was frightened."',
              effects=(E("set", "people.player.knows.eli_need", True), E("set", "people.eli.heard", True))),
        ),
        "fear": (
            P("eli_private_fear",
              'Eli: "When we met I could fix things for her. A lamp, a hinge, her bike. There was always a way to make myself useful."',
              '"Lately she needs things I can\'t build. I keep offering the things I can."',
              'He rubs a white scar on his thumb. "I\'m afraid that if I stop being useful, there won\'t be a reason to keep me."',
              effects=(E("set", "people.player.knows.eli_fear", True), E("set", "people.eli.heard", True))),
            P("eli_private_fear_depth",
              'Eli: "My father never asked anyone to stay. He just made leaving difficult. A broken car, an unpaid bill, one more thing that needed doing."',
              '"I used to despise that. Then I saw how much of our savings I had put into somewhere Mara would have to help me run."',
              'He draws the kitchen door open a little. "I don\'t want a business that keeps her here because she can\'t afford to go."',
              effects=(E("set", "people.eli.insight", True), E("add", "people.eli.memes.fear", -1))),
        ),
    },
}

OWNERSHIP = {
    "mara": P("mara_owns",
              'Mara holds up a hand before you can answer for her. "No. I need to say this myself."',
              '"I kept the residency from you because I was afraid of being talked out of it. But I didn\'t give you a chance to be anything except the person I was afraid of."',
              'Eli: "I would have been hurt. I am hurt. But I might have surprised you."',
              'Mara: "I know. I took that away from both of us."',
              effects=(E("set", "people.mara.accountable", True), E("add", "people.eli.trust_partner", 1),
                       E("add", "people.mara.memes.anger", -1))),
    "eli": P("eli_owns",
             'Eli draws the receipt toward his own plate. "This belongs on my side of the table."',
             '"I spent our money on a future I hadn\'t asked you to want. I called it a gift because that made it harder for you to refuse."',
             'Mara: "Thank you for saying it without explaining why I ought to be pleased."',
             'Eli: "I still wanted to make you happy. That doesn\'t make what I did fair."',
             effects=(E("set", "people.eli.accountable", True), E("add", "people.mara.trust_partner", 1),
                      E("add", "people.eli.memes.anger", -1))),
}


def return_to_table(session):
    who = session.private_with
    if not who:
        return []
    other = "eli" if who == "mara" else "mara"
    session.private_with = None
    session.interrupted = session.active is not None
    return session.emit(P("return",
        'You and ' + who.title() + ' return to the dining room. ' + other.title() + ' looks up but does not ask you to report the conversation.',
        effects=(E("set", "people.player.location", "dining_room"),
                 E("set", "people." + who + ".location", "dining_room"))), "movement", "kitchen")


def interact(session, command):
    people = session.state["people"]
    if command.startswith("talk "):
        who = command.split()[1]
        person = people[who]
        if person["trust_player"] < 2 or person["memes"]["anger"] > 6:
            return session.emit(P("refused",
                who.title() + ': "After that? If you have something to say, say it where we can both hear it."'),
                "private", who), False
        other = "eli" if who == "mara" else "mara"
        session.private_with = who
        return session.emit(P("enter",
            'You ask ' + who.title() + ' if you can help in the kitchen. ' + other.title() + ' stays at the table.',
            ( 'Mara runs the tap until the water covers the sound of your voices. "For a minute, I need to be a person, not half of a couple."'
              if who == "mara" else
              'Eli busies himself with a tea towel. "I don\'t want to make you choose sides. I just need someone who isn\'t already disappointed."'),
            effects=(E("set", "people.player.location", "kitchen"), E("set", "people." + who + ".location", "kitchen"),
                     E("set", "people." + who + ".private_silences", 0),
                     E("set", "people." + who + ".private_visited", True))), "private", who), True
    if command.startswith("tell "):
        who = command.split()[1]
        other = "eli" if who == "mara" else "mara"
        truth = ('Mara has accepted a residency. She is leaving on Monday.' if who == "mara"
                 else 'Eli paid a deposit on the shop from your joint savings.')
        promise = people["player"]["promises"][who]
        effects = list(reveal(who, "letter" if who == "mara" else "receipt"))
        effects += [E("set", "people." + who + ".privacy_breached", True),
                    E("set", "people.player.betrayal", True),
                    E("set", "people." + who + ".offenses", people[who]["offenses"] + 1),
                    E("set", "people.player.caused_harm", True),
                    E("add", "people." + who + ".trust_player", -4 if promise else -2),
                    E("add", "people." + who + ".memes.anger", 3)]
        lines = ['You: "' + truth + '"',
                 who.title() + (': "You promised you would let me say it."' if promise else ': "I told you that alone. It wasn\'t yours to announce."'),
                 other.title() + ': "I needed to know. I didn\'t need you to do it like that."',
                 who.title() + ' opens the paper on the sideboard with shaking hands. "There. Now everyone can look."']
        return session.emit(P("betrayal", *lines, effects=effects), "disclosure", who), True
    who = session.private_with
    person = people[who]
    if command == "return":
        return return_to_table(session), False
    if command.startswith("ask "):
        topic = command.split()[1]
        tier = session.private_tiers[who][topic]
        if tier >= len(PRIVATE[who][topic]):
            return session.emit(P("exhausted", who.title() + ': "That is as far as I can put it into words. Will you sit with that for a moment?"'), "private", who), True
        performance = PRIVATE[who][topic][tier]
        session.private_tiers[who][topic] += 1
        # A private retelling never makes the absent partner know a fact.
        if topic == "work" and tier == 0 and person["disclosed"]:
            performance = (P("known", 'Mara: "You heard what I said about Monday. In here I can tell you why I kept it from him."')
                           if who == "mara" else P("known", 'Eli: "You heard about the deposit. What I haven\'t explained is why I needed that shop so badly."'))
        return session.emit(performance, "private", who + "." + topic + "." + str(tier)), True
    if command == "promise privacy":
        if people["player"]["promises"][who]:
            return session.emit(P("remembered", who.title() + ': "I heard you promise. That matters more than hearing it twice."'), "private", who), True
        return session.emit(P("promise",
            'You: "I will let you tell your partner yourself. I won\'t carry the conversation back for you."',
            who.title() + ': "Thank you. That makes it easier to think about actually doing it."',
            effects=(E("set", "people.player.promises." + who, True), E("add", "people." + who + ".trust_player", 1))), "promise", who), True
    if command == "encourage honesty":
        fact = "letter" if who == "mara" else "receipt"
        if person["disclosed"]:
            return session.emit(P("already_public", who.title() + ': "That part is out now. What matters is what I do about it."'), "private", who), True
        if not people["player"]["knows"][fact] or person["trust_player"] < 3:
            return session.emit(P("not_ready", who.title() + ': "You are asking me to jump before I have found where to put my feet. Hear me out first."'), "private", who), True
        return session.emit(P("permission",
            'You: "I won\'t say it for you. I can stay beside you while you say it."',
            who.title() + ': "All right. When we go back, let me start. Even if I get it wrong."',
            effects=(E("set", "people." + who + ".willing_tell", True), E("set", "people." + who + ".heard", True))), "promise", who), True
    if command == "apologize":
        if person["offenses"] <= person["forgiven"]:
            return session.emit(P("not_needed", who.title() + ': "You don\'t need to apologize for being here."'), "private", who), True
        return session.emit(P("apology",
            'You apologize for the hurt you caused, without asking for reassurance in return.',
            who.title() + ': "I appreciate you saying that. I need a little time to believe it."',
            effects=(E("set", "people." + who + ".forgiven", person["offenses"]),
                     E("add", "people." + who + ".trust_player", 1), E("add", "people." + who + ".memes.anger", -1))), "private", who), True
    count = person["private_silences"] + 1
    if count >= 3:
        lines = session.emit(P("ready_to_return", who.title() + ': "We should go back. I don\'t want silence in here to become another thing we hide behind."',
                             effects=(E("set", "people." + who + ".private_silences", count),)), "private", who)
        return lines + return_to_table(session), False
    line = ("You leave the silence unfilled. " + who.title() + " dries a glass and sets it carefully on the counter." if count == 1
            else "For a while you both listen to the kitchen clock. Neither of you reaches for another task.")
    return session.emit(P("quiet_" + str(count), line,
                          effects=(E("set", "people." + who + ".private_silences", count),)), "private", who), True


def initiative(session):
    people = session.state["people"]
    for who, truth in (("mara", MARA_TRUTH), ("eli", ELI_TRUTH)):
        person = people[who]
        if person["willing_tell"] and not person["disclosed"]:
            return session.emit(truth, "initiative", who + ".voluntary_disclosure")
    if not people["player"]["opened_floor"]:
        return []
    for who, truth in (("mara", MARA_TRUTH), ("eli", ELI_TRUTH)):
        person = people[who]
        if person["trust_player"] >= 3 and person["heard"] and person["memes"]["anger"] <= 4:
            if not person["disclosed"]:
                return session.emit(truth, "initiative", who + ".voluntary_disclosure")
            if not person["accountable"] and not person["privacy_breached"]:
                return session.emit(OWNERSHIP[who], "initiative", who + ".ownership")
    if (all(people[p]["accountable"] and people[p]["memes"]["anger"] <= 4 for p in ("mara", "eli"))
            and not people["player"]["requested_talk"] and not people["player"]["requested_space"]
            and not people["player"]["requested_separation"] and not any(people[p]["privacy_breached"] for p in ("mara", "eli"))):
        return session.emit(P("mutual_proposal",
            'Mara looks past you to Eli. "Could we talk tomorrow without trying to win? Not about whether I am allowed to go. About what going means for us."',
            'Eli: "And about how I return the money, or as much of it as I can. Before I make another plan."',
            'They have stopped looking at you for permission. You move your glass out of the space between them.',
            effects=(E("set", "people.player.requested_talk", True),
                     E("add", "people.mara.trust_partner", 1), E("add", "people.eli.trust_partner", 1))), "initiative", "mutual_proposal")
    return []
