"""Finite question grammar over committed snapshots, with explicit evidence.

Reader exposure is an authored semantic annotation, not an entailment model.
Facts are historical: an answer about exile must not use Wolf's final location.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Fact:
    event: str
    key: str
    value: object


@dataclass
class Answer:
    question: str
    answer: str
    topic: str | None
    perspective: str
    answerable: bool
    facts: list[Fact] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)


CATALOG = {
    "straw": "Why did the straw house fall?",
    "wood": "Where was Wolf when the wooden house fell?",
    "cottage": "Who owned the cottage when the pigs moved in?",
    "theft": "Who took the cheese?",
    "accusation": "Who did the pigs blame for the cheese theft?",
    "witness": "Did Mira see who took the cheese?",
    "books": "Could the young pigs reach the books during construction?",
    "drain": "Did Mira's drain work?",
    "bridge": "Did Tansy's bridge work?",
    "coalition": "Did the young pigs act together at the opening?",
    "ending": "What became of the palace?",
    "wolf": "Did Wolf get his cottage back?",
}


def unavailable(question, perspective, topic=None, reason=None):
    return Answer(question, reason or "The recorded story does not supply an answer to that question.",
                  topic, perspective, False)


class Conversation:
    def __init__(self, story, perspective="world", through=None):
        if perspective not in ("world", "reader"):
            raise ValueError("Perspective must be world or reader")
        self.story = story
        self.perspective = perspective
        self.through = len(story.paragraphs) if through is None else through
        if not 0 <= self.through <= len(story.paragraphs):
            raise ValueError("Reader position is outside this story")
        self.focus = None
        self.event_focus = None

    def ask(self, question):
        query = question.strip().lower().rstrip("?.!")
        why = query == "why"
        if query in ("what happened next", "next"):
            return self._next(question)
        if why:
            if self.focus is None:
                return unavailable(question, self.perspective, reason="There is no earlier question to explain. Ask about an event first.")
            topic = self.focus
        else:
            lookup = {v.lower().rstrip("?"): k for k, v in CATALOG.items()}
            topic = lookup.get(query, query if query in CATALOG else None)
        if topic is None:
            return unavailable(question, self.perspective)
        episodes = {ep.id: ep for ep in self.story.episodes}
        facts = []

        def get(drama, key):
            ep = episodes[drama]
            value = ep.after[key]
            fact = Fact(ep.event_ids[-1], key, value)
            if fact not in facts:
                facts.append(fact)
            return value

        primary = "ending"
        if topic == "straw":
            primary = "wind"
            cause = get(primary, "straw.cause")
            assert cause == "wind"
            text = "Wind pulled the weak straw house apart. The accusation against Wolf did not change the physical cause of its collapse."
        elif topic == "wood":
            primary = "rain"
            assert get("exile", "wolf.location") == "shore"
            assert get(primary, "wood.cause") == "mud"
            text = "Wolf had already left for the shore when the wooden house fell. Rain weakened its footing into mud while he was away."
        elif topic == "cottage":
            primary = "occupation"
            assert get(primary, "cottage.owner") == "wolf"
            assert get(primary, "cottage.occupant") == "pigs"
            text = "The cottage still belonged to Wolf. The pigs occupied it after their brick house cracked; occupying it did not make them its owners."
        elif topic in ("theft", "accusation", "witness"):
            primary = "fox"
            if topic == "theft":
                assert get(primary, "fox.took_cheese")
                assert get(primary, "cheese.portions") == 0
                text = "Story Fox took the cheese. She ate the three portions while attention was directed toward wolves."
            elif topic == "accusation":
                assert get(primary, "pigs.blame_cheese")
                assert get(primary, "fox.took_cheese")
                text = "The pigs blamed Wolf for the missing cheese. Their accusation contradicted the recorded theft by Story Fox."
            else:
                saw = get(primary, "mira.saw_theft")
                blamed = get(primary, "pigs.blame_cheese")
                text = ("Mira saw Fox take the cheese and rejected the accusation against Wolf. " if saw else
                        "Mira did not see the theft and had no direct observation of who took the cheese. ")
                text += "The pigs continued to blame Wolf." if blamed else "The pigs made no accusation."
        elif topic == "books":
            primary = "commission"
            opened = get(primary, "books.accessible")
            assert get(primary, "books.delivered")
            text = ("The shelves were open, so the young pigs could reach the books. The pigs displayed their collection without preventing workers from reading it." if opened else
                    "The books arrived, but the pigs locked the cupboards. The young pigs could see the titles without being able to read the books.")
        elif topic in ("drain", "bridge"):
            child = "mira" if topic == "drain" else "tansy"
            name = child.title()
            primary = "practice_" + topic
            if primary not in episodes:
                primary = "commission"
                assert not get(primary, "books.accessible")
                text = f"{name} did not attempt the {topic} trial. The locked cupboards kept the instructions out of " + ("her" if child == "mira" else "his") + " reach."
            else:
                worked = get(primary, topic + ".works")
                assert get("read_" + child, child + ".read")
                text = (f"{name}'s {topic} worked under its trial conditions. " if worked else
                        f"{name}'s {topic} failed its trial. ")
                text += (("The water ran away from the bricks." if topic == "drain" else "The supported plank carried the test load.") if worked else
                         ("The channel lacked enough fall to carry the water away." if topic == "drain" else "The plank lacked enough support for the test load of bricks."))
                if why:
                    craft = "DrainCraft" if topic == "drain" else "BridgeCraft"
                    get("read_" + child, child + ".meme." + craft)
                    taught = "mentor" in episodes and get("mentor", child + ".mentored")
                    text += (" Reading and Wolf's demonstration informed the attempt." if taught else
                             " The attempt drew on the instructions retained from reading, without a demonstration from Wolf.")
        elif topic == "coalition":
            primary = "confrontation"
            coalition = get(primary, "palace.coalition")
            count = get(primary, "palace.dissenters")
            text = ("Mira and Tansy defended the shelves together. Their successful work and shared signals let them support one another in front of the pigs." if coalition else
                    ("The young pigs voiced objections but did not act as a coalition. Their separate work had not given them the shared signals used by a coordinated group." if count > 1 else
                     "Mira objected, but Tansy did not join her. One capable reader could not provide the joint response needed to hold the hall." if count else
                     "Neither young pig spoke against the order. Neither could point to a successful trial that gave them a practical reason to defend the books."))
        elif topic == "ending":
            outcome = get("ending", "palace.outcome")
            coalition = get("confrontation", "palace.coalition")
            count = get("confrontation", "palace.dissenters")
            if outcome == "library":
                assert coalition and get("ending", "palace.public")
                text = "The palace became a public library. A coordinated defense of the shelves led the pigs to yield the building while claiming credit for a public gift."
            elif outcome == "night_school":
                assert count and get("ending", "foundations.location") == "brick"
                text = "The palace remained under the pigs' control, but a private night school began in the brick house. Mira carried the foundations book there after the protest failed to hold the hall."
            else:
                assert not count and not get("ending", "books.accessible")
                text = "The pigs kept the palace and locked away its books. Without successful practical learning, the young pigs did not resist the removal order."
        elif topic == "wolf":
            restored = get("ending", "wolf.home_restored")
            occupant = get("ending", "cottage.occupant")
            if restored:
                assert occupant == "wolf"
                text = "Wolf returned to his own cottage and lit his stove. The pigs explicitly agreed to leave it after the workers secured the library."
            else:
                assert occupant == "pigs"
                text = "Wolf did not recover his cottage. The pigs still occupied it, and he remained required to sleep in their brick house."
        return self._finish(question, text, topic, primary, facts)

    def _finish(self, question, text, topic, primary, facts):
        visible = self.story.paragraphs[:self.through]
        exposed = {(e, key) for p in visible for e in p.evidence for key in p.reveals}
        if self.perspective == "reader" and any((f.event, f.key) not in exposed for f in facts):
            return unavailable(question, self.perspective, topic,
                               "The story has not revealed enough at this reading position to answer that. Read farther before asking again.")
        ids = {f.event for f in facts}
        supporting = [p.id for p in (visible if self.perspective == "reader" else self.story.paragraphs)
                      if ids.intersection(p.evidence)]
        self.focus, self.event_focus = topic, primary
        return Answer(question, text, topic, self.perspective, True, facts, supporting)

    def _next(self, question):
        if self.event_focus is None:
            return unavailable(question, self.perspective, reason="There is no earlier event to continue from. Ask about an event first.")
        index = next(i for i, ep in enumerate(self.story.episodes) if ep.id == self.event_focus)
        if index + 1 == len(self.story.episodes):
            return unavailable(question, self.perspective, self.focus, "The recorded story ends there. It supplies no later event.")
        ep = self.story.episodes[index + 1]
        paragraphs = [p for p in self.story.paragraphs if p.drama == ep.id]
        facts = [Fact(ep.event_ids[-1], key, ep.after[key]) for key in paragraphs[-1].reveals]
        # Return the actual next committed performance, not a guessed sequel.
        next_topic = {"wind": "straw", "rain": "wood", "occupation": "cottage",
                      "fox": "theft", "commission": "books", "practice_drain": "drain",
                      "practice_bridge": "bridge", "confrontation": "coalition", "ending": "ending"}.get(ep.id)
        return self._finish(question, "Next in the recorded story:\n\n" + "\n\n".join(p.text for p in paragraphs),
                            next_topic, ep.id, facts)


def questions(story, perspective="reader"):
    conversation = Conversation(story, perspective)
    return [conversation.ask(question) for question in CATALOG.values()]
