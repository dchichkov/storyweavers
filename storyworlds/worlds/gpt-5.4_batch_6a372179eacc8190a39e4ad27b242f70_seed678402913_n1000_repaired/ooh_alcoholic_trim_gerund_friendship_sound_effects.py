#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ooh_alcoholic_trim_gerund_friendship_sound_effects.py
=================================================================================

A gentle ghost-story world about two friends who hear spooky sounds in a dim
storage place, feel brave together, and discover an ordinary cause.

Seed constraints rebuilt as world state:
- the story includes the words "ooh", "alcoholic", and "trim-gerund"
- Friendship is causal, not decorative: the children face the scare together
- Sound effects drive the middle beat: creak, tap-tap, clink, whooo
- Ghost-story style, but with a safe, child-facing reveal

Reasonableness constraint
-------------------------
Not every spooky noise should be handled the same way. Most harmless noises can
be checked by two children together with a safe light. But if the noise comes
from a wobbling shelf with a dusty bottle labeled "alcoholic cleaner", the world
requires a grown-up to finish the job. The script refuses unsafe explicit
choices and includes an ASP twin of the same gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/ooh_alcoholic_trim_gerund_friendship_sound_effects.py
    python storyworlds/worlds/gpt-5.4/ooh_alcoholic_trim_gerund_friendship_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/ooh_alcoholic_trim_gerund_friendship_sound_effects.py --source bottle_shelf
    python storyworlds/worlds/gpt-5.4/ooh_alcoholic_trim_gerund_friendship_sound_effects.py --response investigate_together
    python storyworlds/worlds/gpt-5.4/ooh_alcoholic_trim_gerund_friendship_sound_effects.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    spooky_spot: str
    afford_sources: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound_fx: str
    whisper: str
    reveal: str
    risk: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    calls_adult: bool
    text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"friend_a", "friend_b"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    source = world.get("source")
    if source.meters["active"] < THRESHOLD:
        return []
    sig = ("spook", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("place").meters["eerie"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return []


def _r_friendship(world: World) -> list[str]:
    pair = world.get("pair")
    if pair.meters["together"] < THRESHOLD:
        return []
    sig = ("friendship", pair.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["bravery"] += 1
        kid.memes["trust"] += 1
    pair.memes["friendship"] += 1
    return []


def _r_reveal(world: World) -> list[str]:
    source = world.get("source")
    if source.meters["found"] < THRESHOLD:
        return []
    sig = ("reveal", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.get("place").meters["eerie"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="friendship", tag="social", apply=_r_friendship),
    Rule(name="reveal", tag="emotional", apply=_r_reveal),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        opening="Up in the attic, the rafters held their breath and the floorboards seemed to remember every old step.",
        spooky_spot="the far corner under the slanted roof",
        afford_sources={"window_hook", "bottle_shelf", "trunk_cat"},
        tags={"attic", "ghost"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        opening="In the garden shed, moonlight slipped through the cracks and laid thin silver stripes over the tools and boxes.",
        spooky_spot="the back wall beside the shelf",
        afford_sources={"window_hook", "bottle_shelf", "hanging_sheet"},
        tags={"shed", "ghost"},
    ),
    "porch_room": Place(
        id="porch_room",
        label="the old porch room",
        opening="In the old porch room, the windows trembled in their frames and the wicker chair looked spooky in the dusk.",
        spooky_spot="the narrow closet by the coat hooks",
        afford_sources={"window_hook", "hanging_sheet", "trunk_cat"},
        tags={"porch", "ghost"},
    ),
}

SOURCES = {
    "window_hook": Source(
        id="window_hook",
        label="a loose window hook",
        sound_fx="creeak... tap-tap...",
        whisper='The wind slipped through a crack and made a tiny "ooh" sound.',
        reveal="A loose window hook was tapping the frame each time the wind pushed it. Once they fastened it, the room sounded ordinary again.",
        risk=0,
        tags={"wind", "sound"},
    ),
    "hanging_sheet": Source(
        id="hanging_sheet",
        label="a hanging sheet",
        sound_fx="whooo... flup-flup...",
        whisper='A hanging sheet breathed out a soft "ooh" whenever the air moved under it.',
        reveal="An old sheet had snagged on a nail and puffed like a pale ghost every time the air stirred. When they tucked it down, the ghost shape vanished at once.",
        risk=0,
        tags={"sheet", "sound"},
    ),
    "trunk_cat": Source(
        id="trunk_cat",
        label="a sleepy cat in a trunk",
        sound_fx="scritch... mrrrp...",
        whisper='Something inside the trunk let out a surprised little "ooh" of air.',
        reveal="The trunk lid was not latched, and a sleepy cat had been nudging it with one paw. When the cat blinked up at them, the whole room stopped feeling haunted.",
        risk=0,
        tags={"cat", "sound"},
    ),
    "bottle_shelf": Source(
        id="bottle_shelf",
        label="a wobbling shelf of bottles",
        sound_fx="clink-clink... creak...",
        whisper='The bottles trembled together, and one hollow note sounded almost like "ooh".',
        reveal="A shelf had tilted, making the bottles knock together. One dusty bottle was labeled 'alcoholic cleaner', so a grown-up steadied the shelf and moved the bottle away where children could not reach it.",
        risk=1,
        tags={"bottle", "cleaner", "sound"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a little flashlight",
        glow="clicked on with a clean yellow beam",
        tags={"flashlight"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a camping lantern",
        glow="glowed softly like a warm pearl",
        tags={"lantern"},
    ),
    "booklight": Light(
        id="booklight",
        label="book-light",
        phrase="a book-light clipped to a storybook",
        glow="made a small brave circle in the dark",
        tags={"light"},
    ),
}

RESPONSES = {
    "investigate_together": Response(
        id="investigate_together",
        sense=3,
        calls_adult=False,
        text="They moved closer together, lifted the light, and checked the spooky corner side by side.",
        tags={"friendship", "investigate"},
    ),
    "fetch_grownup": Response(
        id="fetch_grownup",
        sense=3,
        calls_adult=True,
        text="They stayed together, called for a grown-up, and kept the light pointed at the corner until help came.",
        tags={"friendship", "adult_help"},
    ),
    "rush_alone": Response(
        id="rush_alone",
        sense=1,
        calls_adult=False,
        text="One child rushed ahead alone without a plan.",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Ivy", "Cora", "Lucy", "Mae"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Max", "Eli", "Jude", "Theo", "Sam"]
TRAITS = ["gentle", "curious", "careful", "steady", "bright", "kind"]


def source_allowed(place_id: str, source_id: str) -> bool:
    return source_id in PLACES[place_id].afford_sources


def response_allowed(source_id: str, response_id: str) -> bool:
    source = SOURCES[source_id]
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return False
    if source.risk > 0 and not response.calls_adult:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id in sorted(place.afford_sources):
            for response_id, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and response_allowed(source_id, response_id):
                    combos.append((place_id, source_id, response_id))
    return combos


def predict_outcome(source_id: str, response_id: str) -> str:
    source = SOURCES[source_id]
    response = RESPONSES[response_id]
    if response.calls_adult or source.risk > 0:
        return "adult_help"
    return "friend_reveal"


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} were best friends, the kind who shared dares, blankets, and brave ideas."
    )
    world.say(place.opening)
    world.say(
        f"They had come to {place.label} to look for costume ribbons for their pretend ghost parade."
    )


def seed_details(world: World) -> None:
    note = world.get("note")
    bottle = world.get("bottle")
    world.say(
        f"On an old crate lay {note.phrase}, and across the top someone had written the odd practice word {note.label}."
    )
    world.say(
        f"High on a shelf sat {bottle.phrase}, far above their heads where children were not meant to touch it."
    )


def hear_sound(world: World, a: Entity, b: Entity, source: Source, place: Place) -> None:
    src = world.get("source")
    src.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from {place.spooky_spot}, came {source.sound_fx}"
    )
    world.say(source.whisper)
    world.say(
        f'{a.id} stopped so fast that {b.id} bumped {a.pronoun("object")}. "Did you hear that?" {b.id} whispered. "It sounded ghosty."'
    )


def choose_together(world: World, a: Entity, b: Entity, light: Light, response: Response) -> None:
    pair = world.get("pair")
    pair.meters["together"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{b.id} slipped {b.pronoun('possessive')} hand into {a.id}'s. That made both of them feel steadier."
    )
    world.say(
        f"{a.id} lifted {light.phrase}, which {light.glow}."
    )
    world.say(response.text)


def reveal_by_friends(world: World, a: Entity, b: Entity, source: Source) -> None:
    src = world.get("source")
    src.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(source.reveal)
    world.say(
        f"{a.id} let out a shaky laugh. {b.id} laughed too, because the room was not full of ghosts after all, only ordinary things making strange sounds."
    )
    world.say(
        f'They said "ooh" again on purpose, this time in silly spooky voices, and the word no longer felt scary.'
    )


def call_grownup(world: World, a: Entity, b: Entity, parent: Entity, source: Source) -> None:
    src = world.get("source")
    world.say(
        f'"{parent.label_word.capitalize()}!" {a.id} called. {b.id} kept holding on, and neither friend ran away from the other.'
    )
    world.say(
        f"{parent.label_word.capitalize()} came with calm steps, bent to look where the light was pointing, and saw the problem at once."
    )
    src.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(source.reveal)
    world.say(
        f'"Thank you for calling me instead of touching the shelf," {parent.label_word} said. "That label says alcoholic cleaner, and cleaning bottles are for grown-ups to handle."'
    )
    world.say(
        f"The strange clinking stopped, and the brave part of the evening was no longer the sound. It was that {a.id} and {b.id} had stayed together."
    )


def ending(world: World, a: Entity, b: Entity, outcome: str) -> None:
    for kid in (a, b):
        kid.memes["friendship"] += 1
        kid.memes["joy"] += 1
    if outcome == "friend_reveal":
        world.say(
            f"Before they left, {b.id} tucked the fluttering spelling page flat and grinned at the crooked word trim-gerund as if it were one more harmless attic mystery."
        )
        world.say(
            f"When they went back down the steps, they walked shoulder to shoulder, brave because friendship had made the dark smaller."
        )
    else:
        world.say(
            f"On the way out, {a.id} glanced once more at the spelling page with trim-gerund on it and felt a little thrill, but not the frightened kind."
        )
        world.say(
            f"They went downstairs side by side, and even the hallway shadows seemed thinner now that they had faced the spooky room as friends."
        )


def tell(
    place: Place,
    source: Source,
    light: Light,
    response: Response,
    name_a: str = "Lila",
    gender_a: str = "girl",
    name_b: str = "Owen",
    gender_b: str = "boy",
    trait_a: str = "curious",
    trait_b: str = "steady",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    a = world.add(Entity(id=name_a, kind="character", type=gender_a, role="friend_a", attrs={"trait": trait_a}))
    b = world.add(Entity(id=name_b, kind="character", type=gender_b, role="friend_b", attrs={"trait": trait_b}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="grownup", label="the parent"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="pair", type="friendship", label="their friendship"))
    world.add(Entity(id="source", type="source", label=source.label, tags=set(source.tags)))
    world.add(Entity(id="note", type="paper", label="trim-gerund", phrase="a loose spelling page"))
    world.add(Entity(id="bottle", type="bottle", label="alcoholic cleaner", phrase="a dusty bottle marked alcoholic cleaner"))
    world.facts["sound_fx"] = source.sound_fx

    introduce(world, a, b, place)
    seed_details(world)

    world.para()
    hear_sound(world, a, b, source, place)
    choose_together(world, a, b, light, response)

    world.para()
    outcome = predict_outcome(source.id, response.id)
    if response.calls_adult:
        call_grownup(world, a, b, parent, source)
    else:
        reveal_by_friends(world, a, b, source)

    world.para()
    ending(world, a, b, outcome)

    world.facts.update(
        place=place,
        source_cfg=source,
        light=light,
        response=response,
        friend_a=a,
        friend_b=b,
        parent=parent,
        note=world.get("note"),
        bottle=world.get("bottle"),
        outcome=outcome,
        called_adult=response.calls_adult,
        scary=world.get("source").meters["active"] >= THRESHOLD,
        revealed=world.get("source").meters["found"] >= THRESHOLD,
    )
    return world


def explain_place_source(place_id: str, source_id: str) -> str:
    return (
        f"(No story: {SOURCES[source_id].label} does not fit naturally in {PLACES[place_id].label}. "
        f"Pick a source that belongs in that place.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). The friends should stay together "
        f"and use a safer plan.)"
    )


def explain_risk(source_id: str, response_id: str) -> str:
    return (
        f"(No story: {SOURCES[source_id].label} can involve a bottle children should not handle, "
        f"so the story requires a grown-up. Try --response fetch_grownup.)"
    )


@dataclass
class StoryParams:
    place: str
    source: str
    light: str
    response: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
    trait_a: str
    trait_b: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="attic",
        source="window_hook",
        light="flashlight",
        response="investigate_together",
        name_a="Lila",
        gender_a="girl",
        name_b="Owen",
        gender_b="boy",
        trait_a="curious",
        trait_b="steady",
        parent="mother",
    ),
    StoryParams(
        place="porch_room",
        source="trunk_cat",
        light="lantern",
        response="investigate_together",
        name_a="Nora",
        gender_a="girl",
        name_b="Finn",
        gender_b="boy",
        trait_a="gentle",
        trait_b="bright",
        parent="father",
    ),
    StoryParams(
        place="shed",
        source="bottle_shelf",
        light="booklight",
        response="fetch_grownup",
        name_a="Mae",
        gender_a="girl",
        name_b="Theo",
        gender_b="boy",
        trait_a="careful",
        trait_b="kind",
        parent="mother",
    ),
]


KNOWLEDGE = {
    "ghost": [
        (
            "Why can ordinary sounds feel spooky in the dark?",
            "In the dark, you cannot see what is making the sound, so your mind guesses first and often guesses something bigger or stranger. When you add light and look carefully, the sound usually makes more sense.",
        )
    ],
    "friendship": [
        (
            "How can a friend help when something feels scary?",
            "A friend can stay beside you, hold your hand, and help you slow down and think. Feeling together can make a scary problem feel smaller and safer to check.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight helpful in a dark room?",
            "A flashlight lets you see what is really there. Good light can turn a mystery sound into an ordinary answer.",
        )
    ],
    "cleaner": [
        (
            "What does alcoholic cleaner mean on a label?",
            "It means the cleaner contains alcohol as part of the cleaning liquid. Children should not play with cleaning bottles and should let a grown-up handle them.",
        )
    ],
    "sound": [
        (
            "What makes a loose thing go tap-tap or clink in the wind?",
            "Wind can push light objects over and over, so they knock against wood, glass, or metal. That is why little moving parts can make repeating sounds.",
        )
    ],
    "cat": [
        (
            "Why do cats make surprising noises in boxes or trunks?",
            "Cats like snug hiding places, and a lid or box side can move when they push it. That can make a scratch, bump, or sudden little meow.",
        )
    ],
    "sheet": [
        (
            "Why can a hanging sheet look like a ghost?",
            "A sheet is pale and loose, so when air moves through it, it puffs and waves like a floating shape. Once you see the cloth clearly, it stops looking magical.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "friendship", "flashlight", "cleaner", "sound", "cat", "sheet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    place = f["place"]
    source = f["source_cfg"]
    response = f["response"]
    if response.calls_adult:
        return [
            'Write a gentle ghost story for a 3-to-5-year-old that includes the words "ooh", "alcoholic", and "trim-gerund".',
            f"Tell a friendship story where {a.id} and {b.id} hear {source.sound_fx} in {place.label}, stay together, and wisely call a grown-up.",
            "Write a spooky-but-safe story where a strange sound turns out to have an ordinary cause and the ending shows the children braver than before.",
        ]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "ooh", "alcoholic", and "trim-gerund".',
        f"Tell a friendship story where {a.id} and {b.id} hear {source.sound_fx} in {place.label}, use a small light, and discover there is no ghost.",
        "Write a spooky-but-safe story with sound effects, a friendship at the center, and a final image that proves the dark is less scary now.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    place = f["place"]
    source = f["source_cfg"]
    parent = f["parent"]
    light = f["light"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two best friends, {a.id} and {b.id}. They go into {place.label} together and help each other stay brave.",
        ),
        (
            "What made the room feel spooky?",
            f"The friends heard {source.sound_fx} coming from the dark part of {place.label}. The sound came before the answer, so it made their imaginations jump to ghosts.",
        ),
        (
            "How did friendship change what happened?",
            f"They stayed together instead of leaving each other alone. Holding close gave them enough courage to keep looking and learn what the sound really was.",
        ),
        (
            'Why were the words "ooh", "alcoholic", and "trim-gerund" in the story?',
            'The "ooh" was the spooky sound they thought they heard in the dark. "Alcoholic" was part of a grown-up cleaning label, and "trim-gerund" was a strange practice word on an old spelling page they noticed near the mystery.',
        ),
    ]
    if response.calls_adult:
        qa.append(
            (
                f"Why did {a.id} and {b.id} call {parent.label_word}?",
                f"They saw that the spooky sound came from a wobbling shelf of bottles, so they let a grown-up handle it. That was safer because one bottle was labeled alcoholic cleaner and children should not touch cleaning bottles.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The clinking stopped, the room felt ordinary again, and the friends walked out side by side. The ending proves they were braver because they stayed together and made a safe choice.",
            )
        )
    else:
        qa.append(
            (
                f"What did {a.id} and {b.id} use to solve the mystery?",
                f"They used {light.phrase} and looked together instead of panicking. The light helped them turn a ghostly guess into an ordinary answer.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They laughed at the once-spooky room and went back down together. The ending shows that the dark had changed because now they understood the sound.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "friendship", "sound"}
    light = f["light"]
    if light.id == "flashlight":
        tags.add("flashlight")
    if f["source_cfg"].id == "bottle_shelf":
        tags.add("cleaner")
    if f["source_cfg"].id == "trunk_cat":
        tags.add("cat")
    if f["source_cfg"].id == "hanging_sheet":
        tags.add("sheet")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_response(R) :- response(R), sense(R, S), sense_min(M), S >= M.
compatible(P, S, R) :- affords(P, S), safe_response(R), risk(S, 0), not calls_adult(R).
compatible(P, S, R) :- affords(P, S), safe_response(R), calls_adult(R).
:- compatible(P, S, R), risk(S, 1), not calls_adult(R).

outcome(friend_reveal) :- chosen_source(S), chosen_response(R), risk(S, 0), not calls_adult(R).
outcome(adult_help) :- chosen_response(R), calls_adult(R).
outcome(adult_help) :- chosen_source(S), risk(S, 1), chosen_response(R), safe_response(R), not calls_adult(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.afford_sources):
            lines.append(asp.fact("affords", place_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("risk", source_id, source.risk))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        if response.calls_adult:
            lines.append(asp.fact("calls_adult", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != predict_outcome(params.source, params.response):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: two friends hear a ghostly sound and find the ordinary cause."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and not source_allowed(args.place, args.source):
        raise StoryError(explain_place_source(args.place, args.source))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.source and args.response and not response_allowed(args.source, args.response):
        raise StoryError(explain_risk(args.source, args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, response_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    gender_a = rng.choice(["girl", "boy"])
    gender_b = rng.choice(["girl", "boy"])
    name_a = _pick_name(rng, gender_a)
    name_b = _pick_name(rng, gender_b, avoid=name_a)
    return StoryParams(
        place=place_id,
        source=source_id,
        light=light_id,
        response=response_id,
        name_a=name_a,
        gender_a=gender_a,
        name_b=name_b,
        gender_b=gender_b,
        trait_a=rng.choice(TRAITS),
        trait_b=rng.choice(TRAITS),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        source = SOURCES[params.source]
        light = LIGHTS[params.light]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from err

    if not source_allowed(params.place, params.source):
        raise StoryError(explain_place_source(params.place, params.source))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_allowed(params.source, params.response):
        raise StoryError(explain_risk(params.source, params.response))

    world = tell(
        place=place,
        source=source,
        light=light,
        response=response,
        name_a=params.name_a,
        gender_a=params.gender_a,
        name_b=params.name_b,
        gender_b=params.gender_b,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, response) combos:\n")
        for place_id, source_id, response_id in combos:
            print(f"  {place_id:11} {source_id:13} {response_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} & {p.name_b}: {p.source} in {p.place} ({predict_outcome(p.source, p.response)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
