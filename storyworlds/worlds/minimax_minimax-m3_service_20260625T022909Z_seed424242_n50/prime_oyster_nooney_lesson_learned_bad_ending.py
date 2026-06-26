#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/prime_oyster_nooney_lesson_learned_bad_ending.py
=========================================================================================================================

A standalone *story world* for the seed tale of Prime the oyster and the
Nooney twins, told with a Heartwarming style but offering both a Lesson
Learned ending and a Bad Ending -- two close variants the world model
can actually justify from the same starting state.

Initial story (used to build the world model):
---
Once upon a time, there was a small, shiny oyster who lived in a quiet
tide pool. His name was Prime, and he was the brightest, smoothest shell
in the whole bay. Every morning the little Nooney twins, Pip and Pop,
came down the rocks to say hello. They were curious Nooneys who loved
peeking under shells to see what lived there.

One day, a big storm rolled in from the sea. Prime had a tight, latched
shell, but the Nooney twins were so small and silly that they could not
keep their footing on the slippery rocks. The waves splashed over the
tide pool, and the twins tumbled down toward a jagged crab who pinched
at anything that came close.

Prime remembered his grandmother's lesson about courage: a kind heart
opens its shell even when it is scared. He unlatched himself, rolled
toward the twins, and let them climb inside. He carried them through the
stormy water until they were safe on a soft, sandy bar.

When the storm cleared, the twins hugged Prime's smooth lip and promised
to listen when the tide got rough. Prime smiled inside his shell, glad
he had been brave. And that is the lesson the tide pool keeps: courage
fits inside the smallest, shiniest oyster.

The Heartwarming, Lesson Learned arc above is the *default* arc. The
Bad Ending branch keeps the same setup and conflict, but Prime keeps
his shell closed out of fear -- and the Nooneys learn that closed shells
can only protect the oyster inside.

Causal state updates:
---
    do storm roll in                  -> tide.meters["rough"]  += 1
                                        world.memes["alarm"]   += 1
    twins fall in                     -> twin.meters["wobble"] += 1
                                        twin.memes["scared"]   += 1
    crab threatens                    -> world.memes["danger"] += 1
                                        twin.meters["alarm"]   += 1
    open shell (lesson)               -> prime.memes["courage"] += 1
                                        prime.memes["love"]     += 1
    close shell (bad)                 -> prime.memes["fear"]    += 1
                                        twin.meters["hurt"]     += 1
    rescue completes                  -> twin.memes["safe"]     += 1
                                        prime.memes["pride"]    += 1
    promise / learned                 -> world.memes["wisdom"]  += 1

Scripted social/emotional beats:
---
    Prime remembers grandmother's words -> prime.memes["lesson"] = 1
    Nooneys promise to listen           -> world.memes["promise"] = 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # oyster, twin, crab, tide, ...
    label: str = ""                # short reference
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    group: Optional[str] = None    # "twins" link for Pip/Pop
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"twin_sister", "oyster_mom", "grandmother"}
        male = {"twin_brother", "oyster_dad", "crab"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "oyster":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother", "oyster_mom": "mother",
            "oyster_dad": "father", "twin_sister": "sister",
            "twin_brother": "brother",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the tide pool"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which events this place allows


@dataclass
class Event:
    """A thing that happens at the tide pool -- a storm, a wave, a pinch."""
    id: str
    label: str                # "storm"
    phrase: str               # "a big storm rolled in from the sea"
    verb: str                 # used in "<subject> ... rolled in"
    threat: str               # what kind of danger it brings
    tags: set[str] = field(default_factory=set)


@dataclass
class Threat:
    """The thing that scares the twins in the water."""
    id: str
    label: str                # "crab"
    phrase: str               # "a jagged crab"
    action: str               # "pinched at anything that came close"
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    """Grandmother's saying that Prime remembers in the Lesson Learned arc."""
    id: str
    phrase: str               # full saying, in quotes
    short: str                # one-line summary for Q&A
    tags: set[str] = field(default_factory=set)


@dataclass
class Ending:
    """Which arc to run -- the Heartwarming lesson OR the Bad Ending."""
    id: str                   # "lesson" | "bad"
    label: str                # "Lesson Learned" | "Bad Ending"
    style: str                # "heartwarming"
    shell_decision: str       # "open" | "close"
    summary: str              # one-sentence story ending for Q&A
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rescue(world: World) -> list[str]:
    """Open shell + scared twins + danger -> twins become safe, Prime gains pride."""
    prime = world.entities.get("Prime")
    if prime is None or prime.memes.get("courage", 0) < THRESHOLD:
        return []
    out: list[str] = []
    if world.memes.get("danger", 0) < THRESHOLD:
        return []
    for twin in world.characters():
        if twin.group != "twins":
            continue
        if twin.memes.get("safe", 0) >= THRESHOLD:
            continue
        sig = ("rescue", twin.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        twin.memes["safe"] += 1
        twin.memes["scared"] = 0.0
        prime.memes["pride"] += 1
        out.append(f"{twin.id} huddled safe inside Prime's shell.")
    return out


def _r_wisdom(world: World) -> list[str]:
    """Rescued twins + safe -> world gains wisdom (the moral)."""
    if world.memes.get("wisdom", 0) >= THRESHOLD:
        return []
    safe = all(
        e.memes.get("safe", 0) >= THRESHOLD
        for e in world.characters() if e.group == "twins"
    )
    if not safe:
        return []
    world.memes["wisdom"] += 1
    return ["__wisdom__"]


def _r_hurt(world: World) -> list[str]:
    """Closed shell + danger -> twins take hurt (the Bad Ending path)."""
    prime = world.entities.get("Prime")
    if prime is None or prime.memes.get("fear", 0) < THRESHOLD:
        return []
    if world.memes.get("danger", 0) < THRESHOLD:
        return []
    out: list[str] = []
    for twin in world.characters():
        if twin.group != "twins":
            continue
        if twin.meters.get("hurt", 0) >= THRESHOLD:
            continue
        sig = ("hurt", twin.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        twin.meters["hurt"] += 1
        twin.memes["scared"] += 1
        out.append(f"The waves knocked {twin.id} against the rocks.")
    return out


def _r_promise(world: World) -> list[str]:
    """Rescued twins + wisdom -> world gains promise (twins will listen)."""
    if world.memes.get("promise", 0) >= THRESHOLD:
        return []
    if world.memes.get("wisdom", 0) < THRESHOLD:
        return []
    world.memes["promise"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="rescue", tag="physical", apply=_r_rescue),
    Rule(name="wisdom", tag="social", apply=_r_wisdom),
    Rule(name="hurt", tag="physical", apply=_r_hurt),
    Rule(name="promise", tag="social", apply=_r_promise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__wisdom__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def introduce(world: World, prime: Entity) -> None:
    prime.memes["shine"] += 1
    world.say(
        f"Once upon a time, there was a small, shiny oyster named {prime.id}, "
        f"and he lived in a quiet {world.setting.place}."
    )
    world.say(
        f"He was the smoothest, brightest shell in the whole bay, and every "
        f"morning he liked to feel the sun on his back."
    )


def meet_twins(world: World, prime: Entity, twins: list[Entity]) -> None:
    prime.memes["friendship"] += 1
    for t in twins:
        t.memes["curious"] += 1
        t.memes["friendship"] = t.memes.get("friendship", 0) + 1
    names = " and ".join(t.id for t in twins)
    world.say(
        f"Every morning the little Nooney twins, {names}, came down the "
        f"rocks to say hello."
    )
    world.say(
        f"They were curious Nooneys who loved peeking under shells to see "
        f"what lived there, and {prime.id} always peeked back."
    )


def storm_rolls_in(world: World, event: Event) -> None:
    world.memes["alarm"] += 1
    world.facts["storm"] = event
    world.say(
        f"One day, {event.phrase}, and the sky turned the color of wet stones."
    )


def twins_in_trouble(world: World, twins: list[Entity], threat: Threat) -> None:
    world.memes["danger"] += 1
    world.facts["threat"] = threat
    for t in twins:
        t.meters["wobble"] += 1
        t.memes["scared"] += 1
    names = " and ".join(t.id for t in twins)
    world.say(
        f"{prime_pronoun(world).capitalize()} had a tight, latched shell, "
        f"but the Nooney twins were so small and silly that they could not "
        f"keep their footing on the slippery rocks."
    )
    world.say(
        f"The waves splashed over the {world.setting.place}, and {names} "
        f"tumbled down toward {threat.phrase} who {threat.action}."
    )


def prime_pronoun(world: World) -> str:
    return world.entities["Prime"].pronoun("subject")


def remembers_lesson(world: World, prime: Entity, lesson: Lesson) -> None:
    prime.memes["lesson"] += 1
    world.facts["lesson"] = lesson
    world.say(
        f"But {prime.id} remembered his grandmother's words: "
        f"{lesson.phrase}"
    )


def opens_shell(world: World, prime: Entity, twins: list[Entity]) -> None:
    prime.memes["courage"] += 1
    prime.memes["love"] += 1
    world.say(
        f"So {prime.id} took a deep breath, unlatched his shell, and rolled "
        f"toward the twins."
    )
    world.say(
        f'"Hop in," {prime.id} said, and the twins tumbled inside his '
        f"smooth, safe shell."
    )


def rescues(world: World, prime: Entity, twins: list[Entity]) -> None:
    world.say(
        f"{prime.id} carried them through the stormy water with slow, careful "
        f"flips, until they were safe on a soft, sandy bar."
    )
    propagate(world, narrate=True)


def promises(world: World, twins: list[Entity], prime: Entity) -> None:
    world.memes["promise"] = 1
    world.facts["promised"] = True
    names = " and ".join(t.id for t in twins)
    world.say(
        f"When the storm cleared, {names} hugged {prime.id}'s smooth lip and "
        f"promised to listen when the tide got rough."
    )


def shell_stays_closed(world: World, prime: Entity) -> None:
    prime.memes["fear"] += 1
    world.say(
        f"But {prime.id} was afraid. He held his shell tight and hoped the "
        f"storm would pass on its own."
    )


def waves_crash(world: World, twins: list[Entity]) -> None:
    world.memes["danger"] += 1
    for t in twins:
        t.meters["wobble"] += 1
        t.memes["scared"] += 1
    world.say(
        f"The waves grew bigger and the {world.entities['Threat'].label} "
        f"snapped closer."
    )


def lesson_ending(world: World, prime: Entity) -> None:
    prime.memes["pride"] += 1
    world.say(
        f"{prime.id} smiled inside his shell, glad he had been brave."
    )
    world.say(
        f"And that is the lesson the {world.setting.place} keeps: courage "
        f"fits inside the smallest, shiniest oyster."
    )


def bad_ending(world: World, prime: Entity, twins: list[Entity]) -> None:
    prime.memes["shame"] = prime.memes.get("shame", 0) + 1
    world.say(
        f"The waves washed the twins back to the rocks with sore flippers, "
        f"and the {world.entities['Threat'].label} went back into its crack."
    )
    world.say(
        f"{prime.id} stayed shut inside his shell, and the {world.setting.place} "
        f"felt very quiet."
    )
    world.say(
        f"That night the tide whispered a hard lesson: a shell that never "
        f"opens can only ever keep the oyster inside."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, event: Event, threat: Threat, lesson: Lesson,
         ending: Ending, twin_names: tuple[str, str],
         twin_types: tuple[str, str]) -> World:
    world = World(setting)

    prime = world.add(Entity(
        id="Prime", kind="character", type="oyster",
        traits=["small", "shiny", "kind"],
    ))
    pip = world.add(Entity(
        id=twin_names[0], kind="character", type=twin_types[0],
        traits=["little", "curious"], group="twins",
    ))
    pop = world.add(Entity(
        id=twin_names[1], kind="character", type=twin_types[1],
        traits=["little", "cheerful"], group="twins",
    ))
    world.add(Entity(
        id="Threat", kind="character", type="crab",
        label=threat.label, phrase=threat.phrase,
    ))
    twins = [pip, pop]

    # Act 1 -- who lives here, who visits, what kind of place.
    introduce(world, prime)
    meet_twins(world, prime, twins)
    world.facts["tide_description"] = setting_detail(setting, event)

    # Act 2 -- conflict: a storm, the twins in trouble, a decision point.
    world.para()
    storm_rolls_in(world, event)
    twins_in_trouble(world, twins, threat)

    # The two arcs diverge on Prime's decision.
    world.para()
    if ending.shell_decision == "open":
        remembers_lesson(world, prime, lesson)
        opens_shell(world, prime, twins)
        rescues(world, prime, twins)
        promises(world, twins, prime)
    else:
        shell_stays_closed(world, prime)
        waves_crash(world, twins)

    # Act 3 -- the resolution, matching the chosen ending.
    world.para()
    if ending.shell_decision == "open":
        lesson_ending(world, prime)
    else:
        propagate(world, narrate=False)            # fires _r_hurt on the twins
        bad_ending(world, prime, twins)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        prime=prime, twins=twins, event=event, threat=threat,
        lesson=lesson, ending=ending, setting=setting,
        opened=ending.shell_decision == "open",
        promised=world.memes.get("promise", 0) >= THRESHOLD,
        wisdom=world.memes.get("wisdom", 0) >= THRESHOLD,
        rescued=any(t.memes.get("safe", 0) >= THRESHOLD for t in twins),
        hurt=any(t.meters.get("hurt", 0) >= THRESHOLD for t in twins),
        prime_brave=prime.memes.get("courage", 0) >= THRESHOLD,
        prime_afraid=prime.memes.get("fear", 0) >= THRESHOLD,
    )
    return world


def setting_detail(setting: Setting, event: Event) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the small light waited."
    return (
        f"The {setting.place} smelled of salt, and tiny shells lined the rim like "
        f"little hats."
    )


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "tide_pool": Setting(place="the tide pool", indoor=False, affords={"storm"}),
    "cove": Setting(place="the little cove", indoor=False, affords={"storm"}),
    "rocky_pool": Setting(place="the rocky pool", indoor=False, affords={"storm"}),
}

EVENTS = {
    "storm": Event(
        id="storm",
        label="storm",
        phrase="a big storm rolled in from the sea",
        verb="rolled in",
        threat="rough",
        tags={"storm", "weather"},
    ),
    "squall": Event(
        id="squall",
        label="squall",
        phrase="a sudden squall came racing over the water",
        verb="came racing",
        threat="sudden",
        tags={"storm", "weather"},
    ),
}

THREATS = {
    "crab": Threat(
        id="crab",
        label="crab",
        phrase="a jagged crab",
        action="pinched at anything that came close",
        tags={"crab", "pinch"},
    ),
    "eel": Threat(
        id="eel",
        label="eel",
        phrase="a long, slippery eel",
        action="slithered toward anything that moved",
        tags={"eel", "slither"},
    ),
}

LESSONS = {
    "courage": Lesson(
        id="courage",
        phrase=(
            '"A kind heart opens its shell even when it is scared, because '
            'being brave is not being unafraid -- it is choosing love."'
        ),
        short="A kind heart opens its shell even when it is scared.",
        tags={"courage", "kindness"},
    ),
    "kindness": Lesson(
        id="kindness",
        phrase=(
            '"The smallest shells can hold the biggest kindness, and a friend '
            'who shares his shelter is never really small."'
        ),
        short="The smallest shells can hold the biggest kindness.",
        tags={"courage", "kindness"},
    ),
}

ENDINGS = {
    "lesson": Ending(
        id="lesson",
        label="Lesson Learned",
        style="heartwarming",
        shell_decision="open",
        summary=(
            "Prime remembered grandmother's lesson, opened his shell, and "
            "carried the Nooney twins to safety."
        ),
        tags={"lesson", "courage", "heartwarming"},
    ),
    "bad": Ending(
        id="bad",
        label="Bad Ending",
        style="heartwarming",
        shell_decision="close",
        summary=(
            "Prime was too afraid to open his shell, and the Nooney twins "
            "were hurt by the waves."
        ),
        tags={"bad", "fear"},
    ),
}

TWIN_PAIRS = [
    ("Pip", "Pop"),
    ("Mip", "Mop"),
    ("Tik", "Tok"),
    ("Lulu", "Lala"),
]
TWIN_TYPES = [
    ("twin_brother", "twin_sister"),
    ("twin_sister", "twin_brother"),
    ("twin_brother", "twin_brother"),
    ("twin_sister", "twin_sister"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    """(setting, event, threat, ending) sets where the world actually runs."""
    out: list[tuple[str, str, str, str]] = []
    for sid, s in SETTINGS.items():
        for eid in s.affords:
            for tid in THREATS:
                for ending_id in ENDINGS:
                    out.append((sid, eid, tid, ending_id))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    event: str
    threat: str
    lesson: str
    ending: str
    twin_a: str
    twin_b: str
    twin_a_type: str
    twin_b_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "oyster": [(
        "What is an oyster?",
        "An oyster is a small sea animal that lives inside a hard, hinged "
        "shell at the bottom of shallow water.",
    )],
    "tide_pool": [(
        "What is a tide pool?",
        "A tide pool is a small pool of seawater left on the rocks when "
        "the tide goes out, where little sea creatures live.",
    )],
    "storm": [(
        "Why are storms scary at the seashore?",
        "Storms at the seashore bring big waves and slippery rocks, so it "
        "is easy for small animals to be knocked around.",
    )],
    "crab": [(
        "Are crabs dangerous?",
        "Crabs have strong claws that they use to pinch when they feel "
        "scared or hungry, so it is best to keep a safe distance.",
    )],
    "courage": [(
        "What does courage mean?",
        "Courage means doing the right thing even when you feel afraid, "
        "because being brave is choosing kindness over being safe inside.",
    )],
    "kindness": [(
        "Why does kindness matter?",
        "Kindness matters because small acts of help can rescue a friend "
        "who is in trouble, even when we are scared ourselves.",
    )],
}
KNOWLEDGE_ORDER = ["oyster", "tide_pool", "storm", "crab", "courage", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prime = f["prime"]
    twin_a, twin_b = f["twins"][0].id, f["twins"][1].id
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a small '
        f'oyster, two curious Nooneys, and a lesson about courage" that '
        f'includes the word "prime".',
        f"Tell a gentle story where a small oyster named {prime.id} decides "
        f"whether to open his shell when {twin_a} and {twin_b} are in trouble.",
        f'Write a simple story that uses the word "oyster" and ends with a '
        f"moral about choosing love over fear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    prime, twins = f["prime"], f["twins"]
    event, threat, lesson, ending = f["event"], f["threat"], f["lesson"], f["ending"]
    place = world.setting.place
    sub, obj, pos = (prime.pronoun("subject"), prime.pronoun("object"),
                     prime.pronoun("possessive"))
    twin_a, twin_b = twins[0].id, twins[1].id
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who lives in {place} and greets {twin_a} and {twin_b} every "
                f"morning in the oyster story?"
            ),
            answer=(
                f"A small, shiny oyster named {prime.id} lives in {place}. "
                f"Every morning the little Nooney twins, {twin_a} and {twin_b}, "
                f"come down the rocks to say hello."
            ),
        ),
        QAItem(
            question=(
                f"What happened to {twin_a} and {twin_b} when {event.label} "
                f"came to {place} in the oyster story?"
            ),
            answer=(
                f"When {event.phrase}, the twins could not keep their footing "
                f"on the slippery rocks and tumbled toward {threat.phrase}, "
                f"who {threat.action}."
            ),
        ),
        QAItem(
            question=(
                f"What lesson did {prime.id} remember when {twin_a} and "
                f"{twin_b} needed help?"
            ),
            answer=(
                f"{sub.capitalize()} remembered his grandmother's words: "
                f"{lesson.phrase} That saying helped {obj} decide what to do."
            ),
        ),
    ]
    if f["opened"]:
        qa.append(QAItem(
            question=(
                f"How did {prime.id} save {twin_a} and {twin_b} in the "
                f"Lesson Learned version of the oyster story?"
            ),
            answer=(
                f"{sub.capitalize()} unlatched {pos} shell and let the twins "
                f"climb inside. {sub.capitalize()} carried them through the "
                f"stormy water to a soft, sandy bar, where they promised to "
                f"listen when the tide got rough."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What is the moral of the Lesson Learned oyster story about "
                f"{prime.id} and the Nooneys?"
            ),
            answer=(
                f"The moral is that courage fits inside the smallest, shiniest "
                f"oyster -- a kind heart can open its shell even when it is "
                f"scared, and that is how friends rescue each other."
            ),
        ))
    else:
        qa.append(QAItem(
            question=(
                f"What went wrong in the Bad Ending version of the oyster "
                f"story when {twin_a} and {twin_b} needed help?"
            ),
            answer=(
                f"{prime.id} was too afraid to open {pos} shell. The waves "
                f"knocked the twins against the rocks, and the tide pool "
                f"whispered a hard lesson: a shell that never opens can only "
                f"ever keep the oyster inside."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did {prime.id} learn from the Bad Ending of the oyster "
                f"story?"
            ),
            answer=(
                f"{sub.capitalize()} learned that fear can keep {obj} safe "
                f"inside but leaves {twin_a} and {twin_b} outside in the "
                f"storm. Closed shells protect only the oyster inside."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"Which ending did the oyster story take this time, the Lesson "
            f"Learned one or the Bad Ending?"
        ),
        answer=(
            f"This time the story took the {ending.label} ending, where "
            f"{ending.summary}"
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["event"].tags) | set(f["threat"].tags) | set(f["lesson"].tags)
    tags.add("oyster")
    tags.add("tide_pool")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.group:
            bits.append(f"group={e.group}")
        lines.append(f"  {e.id:10} ({e.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  world memes: {dict((k, v) for k, v in world.memes.items() if v)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="tide_pool",
        event="storm",
        threat="crab",
        lesson="courage",
        ending="lesson",
        twin_a="Pip",
        twin_b="Pop",
        twin_a_type="twin_brother",
        twin_b_type="twin_sister",
    ),
    StoryParams(
        place="cove",
        event="squall",
        threat="eel",
        lesson="kindness",
        ending="lesson",
        twin_a="Mip",
        twin_b="Mop",
        twin_a_type="twin_sister",
        twin_b_type="twin_brother",
    ),
    StoryParams(
        place="rocky_pool",
        event="storm",
        threat="crab",
        lesson="courage",
        ending="bad",
        twin_a="Tik",
        twin_b="Tok",
        twin_a_type="twin_brother",
        twin_b_type="twin_brother",
    ),
    StoryParams(
        place="tide_pool",
        event="squall",
        threat="eel",
        lesson="kindness",
        ending="bad",
        twin_a="Lulu",
        twin_b="Lala",
        twin_a_type="twin_sister",
        twin_b_type="twin_sister",
    ),
    StoryParams(
        place="cove",
        event="storm",
        threat="crab",
        lesson="courage",
        ending="lesson",
        twin_a="Pip",
        twin_b="Pop",
        twin_a_type="twin_brother",
        twin_b_type="twin_sister",
    ),
]


def explain_rejection(event: Event, threat: Threat, ending: Ending) -> str:
    return (
        f"(No story: the {event.label} does not threaten {threat.label} in this "
        f"domain, or the {ending.label} arc cannot be run with the chosen pieces. "
        f"Try another combination.)"
    )


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of valid_combos().  The rules
# are inline below; the facts are generated from the registries above so the
# two cannot drift.  Uses the shared `asp` helper + clingo, imported lazily so
# the prose engine runs without them.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting affords an event, an event can pair with any threat.
valid(Place, Event, Threat) :- setting(Place), event(Event),
                               affords(Place, Event), threat(Threat).

% Both endings are valid for any (Place, Event, Threat) -- the arc differs.
valid_ending(Place, Event, Threat, Ending) :-
    valid(Place, Event, Threat), ending(Ending).

% A lesson is compatible when the ending is Lesson Learned.
lesson_compatible(Lesson) :- lesson(Lesson), ending(lesson).
lesson_compatible(Lesson) :- lesson(Lesson), ending(bad).

% A full story is valid when every piece lines up.
valid_story(Place, Event, Threat, Ending, Lesson) :-
    valid_ending(Place, Event, Threat, Ending), lesson_compatible(Lesson).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for e in sorted(s.affords):
            lines.append(asp.fact("affords", sid, e))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    for eid in ENDINGS:
        lines.append(asp.fact("ending", eid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Prime the oyster, the Nooney twins, "
                    "and a choice between a Lesson Learned and a Bad Ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--twin-a")
    ap.add_argument("--twin-b")
    ap.add_argument("--twin-a-type", choices=["twin_brother", "twin_sister"])
    ap.add_argument("--twin-b-type", choices=["twin_brother", "twin_sister"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    place = args.place
    event = args.event
    threat = args.threat
    ending = args.ending
    lesson = args.lesson

    if place and event and place not in {s for s, cfg in SETTINGS.items() if event in cfg.affords}:
        raise StoryError(
            f"(No story: {place} does not afford {event}. "
            f"Try another place or event.)"
        )

    place = place or rng.choice(sorted(SETTINGS.keys()))
    event = event or rng.choice(sorted(SETTINGS[place].affords))
    threat = threat or rng.choice(sorted(THREATS.keys()))
    ending = ending or rng.choice(sorted(ENDINGS.keys()))
    lesson = lesson or rng.choice(sorted(LESSONS.keys()))

    if args.twin_a and args.twin_b and args.twin_a == args.twin_b:
        raise StoryError("(No story: the two twins must have different names.)")

    twin_a = args.twin_a or rng.choice([n for pair in TWIN_PAIRS for n in pair])
    twin_b = args.twin_b or rng.choice(
        [n for pair in TWIN_PAIRS for n in pair if n != twin_a]
    )
    twin_a_type = args.twin_a_type or rng.choice([t for pair in TWIN_TYPES for t in pair])
    twin_b_type = args.twin_b_type or rng.choice(
        [t for pair in TWIN_TYPES for t in pair if t != twin_a_type or True]
    )

    return StoryParams(
        place=place, event=event, threat=threat, lesson=lesson, ending=ending,
        twin_a=twin_a, twin_b=twin_b,
        twin_a_type=twin_a_type, twin_b_type=twin_b_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS[params.event], THREATS[params.threat],
                 LESSONS[params.lesson], ENDINGS[params.ending],
                 (params.twin_a, params.twin_b),
                 (params.twin_a_type, params.twin_b_type))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, event, threat) combos "
              f"({len(stories)} full stories with ending + lesson):\n")
        for place, event, threat in triples:
            ends = sorted(set(en for (pl, ev, th, en, _ls) in stories
                              if (pl, ev, th) == (place, event, threat)))
            print(f"  {place:11} {event:7} {threat:5}  [{', '.join(ends)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.twin_a} & {p.twin_b}: {p.ending} "
                      f"({p.event} at {p.place}, threat: {p.threat})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
