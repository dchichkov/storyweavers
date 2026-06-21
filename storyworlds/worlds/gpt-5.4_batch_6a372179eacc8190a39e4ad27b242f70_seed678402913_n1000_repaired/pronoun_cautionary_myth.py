#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pronoun_cautionary_myth.py
=====================================================

A standalone storyworld in a small mythic domain: a child is warned not to call
to an old echoing spirit with a careless pronoun at dusk. If the child ignores
the warning, the echo wakes a wind-spirit that tangles voices and darkens the
path. A calm elder uses a respectful ritual to settle the spirit, and the child
learns to speak kindly and carefully.

The world model prefers a narrow, plausible family of stories over wide coverage:
only echoing sacred places can wake the spirit, and only sensible calming
responses are allowed. The story text is generated from simulated state, not by
slotting nouns into a frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/pronoun_cautionary_myth.py
    python storyworlds/worlds/gpt-5.4/pronoun_cautionary_myth.py --place moon_well --forbidden mock_pronoun
    python storyworlds/worlds/gpt-5.4/pronoun_cautionary_myth.py --target market_square
    python storyworlds/worlds/gpt-5.4/pronoun_cautionary_myth.py --all
    python storyworlds/worlds/gpt-5.4/pronoun_cautionary_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pronoun_cautionary_myth.py --verify
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


# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "gentle", "thoughtful", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    sacred: bool = False
    echoing: bool = False
    calming: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother",
                "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    path: str
    danger_image: str
    safe_image: str
    sacred: bool = True
    echoing: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ForbiddenAct:
    id: str
    label: str
    line: str
    warning: str
    lesson: str
    wakes_echo: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    power: int
    ritual_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    use_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        return [e for e in self.entities.values() if e.role in {"speaker", "warner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
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


def _r_awaken(world: World) -> list[str]:
    place = world.get("place")
    spirit = world.get("spirit")
    if place.meters["disturbed"] < THRESHOLD:
        return []
    sig = ("awaken", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spirit.meters["awake"] += 1
    place.meters["wind"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__awakened__"]


def _r_tangle(world: World) -> list[str]:
    spirit = world.get("spirit")
    if spirit.meters["awake"] < THRESHOLD:
        return []
    sig = ("tangle", spirit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    speaker = world.get("speaker")
    speaker.meters["voice_tangle"] += 1
    world.get("path").meters["darkness"] += 1
    return ["__tangled__"]


CAUSAL_RULES = [
    Rule(name="awaken", tag="mythic", apply=_r_awaken),
    Rule(name="tangle", tag="mythic", apply=_r_tangle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                changed = True
                produced.extend(s for s in result if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(forbidden: ForbiddenAct, place: Place) -> bool:
    return forbidden.wakes_echo and place.sacred and place.echoing


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spirit_severity(place: Place, delay: int) -> int:
    return 1 + delay + (1 if "deep_echo" in place.tags else 0)


def is_settled(response: Response, place: Place, delay: int) -> bool:
    return response.power >= spirit_severity(place, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, speaker_age: int, warner_age: int, trait: str) -> bool:
    older_guide = relation == "siblings" and warner_age > speaker_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_guide else 0.0)
    return older_guide and authority > BRAVERY_INIT


def predict_disturbance(world: World) -> dict:
    sim = world.copy()
    place = sim.get("place")
    place.meters["disturbed"] += 1
    propagate(sim, narrate=False)
    return {
        "awake": sim.get("spirit").meters["awake"] >= THRESHOLD,
        "voice_tangle": sim.get("speaker").meters["voice_tangle"] >= THRESHOLD,
        "darkness": sim.get("path").meters["darkness"],
    }


def introduce(world: World, speaker: Entity, warner: Entity, place: Place) -> None:
    for kid in (speaker, warner):
        kid.memes["wonder"] += 1
    world.say(
        f"In the old days, when evening light still clung to the hills, {speaker.id} "
        f"and {warner.id} walked the {place.path} to {place.phrase}."
    )
    world.say(
        f"The elders said a listening spirit slept there, and that the stones remembered every voice."
    )


def desire(world: World, speaker: Entity, place: Place) -> None:
    speaker.memes["curiosity"] += 1
    world.say(
        f"{speaker.id} stopped beside {place.label} and smiled at the deep echo hiding in it."
    )
    world.say(
        f'"I want to try something," {speaker.pronoun()} whispered.'
    )


def tempt(world: World, speaker: Entity, forbidden: ForbiddenAct) -> None:
    speaker.memes["bravado"] += 1
    world.say(
        f'Then {speaker.id} grinned and said, "{forbidden.line}"'
    )
    world.say(
        "It felt bold and funny for one small breath."
    )


def warn(world: World, warner: Entity, speaker: Entity, elder: Entity,
         forbidden: ForbiddenAct, place: Place) -> None:
    pred = predict_disturbance(world)
    world.facts["predicted_darkness"] = pred["darkness"]
    warner.memes["caution"] += 1
    extra = ""
    if warner.memes["caution"] >= 6:
        extra = f" {warner.id} had heard the old tales so often that {warner.pronoun()} felt the warning in {warner.pronoun('possessive')} bones."
    world.say(
        f'{warner.id} touched {speaker.id}\'s sleeve. "Do not call the spirit with a careless pronoun," '
        f'{warner.pronoun()} said. "{forbidden.warning} {elder.label_word.capitalize()} always says names should be spoken kindly."{extra}'
    )


def back_down(world: World, speaker: Entity, warner: Entity, elder: Entity, gift: Gift) -> None:
    speaker.memes["relief"] += 1
    warner.memes["relief"] += 1
    speaker.memes["bravado"] = 0.0
    world.say(
        f"{speaker.id} looked at {warner.id}, heard the shake in {warner.pronoun('possessive')} voice, and let the joke fall away."
    )
    world.say(
        f'Together they kept the old silence and went home to {elder.label_word}.'
    )
    world.para()
    world.say(
        f"That night, {elder.label_word.capitalize()} praised them for wise tongues and set out {gift.phrase}."
    )
    world.say(
        f"{gift.use_text} The children listened to their own soft names ring back, and the hill stayed peaceful."
    )


def defy(world: World, speaker: Entity, warner: Entity) -> None:
    speaker.memes["defiance"] += 1
    older_sib = speaker.attrs.get("relation") == "siblings" and speaker.age > warner.age
    if older_sib:
        world.say(
            f'"It is only an echo," {speaker.id} said, and because {speaker.pronoun()} was the older child, {warner.id} could not stop {speaker.pronoun("object")}.'
        )
    else:
        world.say(
            f'"It is only an echo," {speaker.id} said, and spoke anyway.'
        )


def disturb(world: World, place: Entity) -> None:
    place.meters["disturbed"] += 1
    propagate(world, narrate=False)
    world.say(
        "The sound went down into the stone, struck the dark water, and came back wrong."
    )


def awaken(world: World, place: Place, speaker: Entity) -> None:
    world.say(
        f"A cold wind rose out of {place.label}, though the trees around it were still."
    )
    if world.get("speaker").meters["voice_tangle"] >= THRESHOLD:
        world.say(
            f"When {speaker.id} tried to speak again, the next word twisted in {speaker.pronoun('possessive')} mouth and would not come out straight."
        )


def alarm(world: World, warner: Entity, elder: Entity) -> None:
    world.say(
        f'"{elder.label_word.capitalize()}!" {warner.id} cried into the dusk.'
    )


def settle(world: World, elder: Entity, response: Response, place: Entity) -> None:
    world.get("spirit").meters["awake"] = 0.0
    world.get("speaker").meters["voice_tangle"] = 0.0
    world.get("path").meters["darkness"] = 0.0
    place.meters["wind"] = 0.0
    body = response.ritual_text.format(place=place.label)
    world.say(
        f"{elder.label_word.capitalize()} came with calm steps and {body}."
    )
    world.say(
        "Little by little, the wind folded itself back into silence."
    )


def fail_settle(world: World, elder: Entity, response: Response, place: Place) -> None:
    world.get("path").meters["darkness"] += 1
    world.get("speaker").meters["voice_tangle"] += 1
    body = response.fail_text.format(place=place.label)
    world.say(
        f"{elder.label_word.capitalize()} hurried near and {body}."
    )
    world.say(
        f"But the spirit rolled the sound around {place.label} and made the whole path darker."
    )


def lesson(world: World, elder: Entity, speaker: Entity, warner: Entity,
           forbidden: ForbiddenAct) -> None:
    for kid in (speaker, warner):
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{elder.label_word.capitalize()} laid a warm hand on both children and said, "{forbidden.lesson} Words that point carelessly can wound what they do not understand."'
    )
    world.say(
        f"{speaker.id} bowed {speaker.pronoun('possessive')} head, and {warner.id} leaned close beside {speaker.pronoun('object')}."
    )


def grim_lesson(world: World, elder: Entity, speaker: Entity, forbidden: ForbiddenAct, place: Place) -> None:
    speaker.memes["lesson"] += 1
    world.say(
        f"All that night, {speaker.id}'s voice came out thin and tangled, as if the hill still held part of it."
    )
    world.say(
        f'{elder.label_word.capitalize()} kept a lamp burning by the door and said, "{forbidden.lesson} Some wounds fade slowly."'
    )
    world.say(
        f"By dawn the voice returned, but {speaker.id} never again mocked the listening places of the world."
    )
    world.facts["lasting_mark"] = f"{place.label} remained a place {speaker.id} passed with lowered eyes."


def safe_gift(world: World, elder: Entity, speaker: Entity, warner: Entity, gift: Gift, place: Place) -> None:
    for kid in (speaker, warner):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next evening, {elder.label_word} brought out {gift.phrase} instead."
    )
    world.say(
        f"{gift.use_text} This time they called to {place.label} with gentle names, and the answer came back clear."
    )
    world.say(
        f"Above them, the first star shone over the quiet path, proving the hill had forgiven them."
    )


def tell(place: Place, forbidden: ForbiddenAct, response: Response, gift: Gift,
         speaker_name: str = "Neri", speaker_gender: str = "girl",
         warner_name: str = "Ivo", warner_gender: str = "boy",
         trait: str = "careful", elder_type: str = "grandmother",
         delay: int = 0, speaker_age: int = 5, warner_age: int = 7,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    speaker = world.add(Entity(
        id=speaker_name,
        kind="character",
        type=speaker_gender,
        role="speaker",
        age=speaker_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    warner = world.add(Entity(
        id=warner_name,
        kind="character",
        type=warner_gender,
        role="warner",
        age=warner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        phrase=place.phrase,
        sacred=place.sacred,
        echoing=place.echoing,
        tags=set(place.tags),
    ))
    world.add(Entity(id="path", kind="thing", type="path", label="the path"))
    world.add(Entity(id="spirit", kind="thing", type="spirit", label="the listening spirit"))

    speaker.memes["bravery"] = BRAVERY_INIT
    warner.memes["caution"] = initial_caution(trait)
    warner.memes["trust"] = float(trust)

    introduce(world, speaker, warner, place)
    desire(world, speaker, place)

    world.para()
    tempt(world, speaker, forbidden)
    warn(world, warner, speaker, elder, forbidden, place)

    averted = would_avert(relation, speaker_age, warner_age, trait)
    severity = 0
    settled = True

    if averted:
        back_down(world, speaker, warner, elder, gift)
        outcome = "averted"
    else:
        defy(world, speaker, warner)
        world.para()
        disturb(world, place_ent)
        awaken(world, place, speaker)
        alarm(world, warner, elder)
        severity = spirit_severity(place, delay)
        settled = is_settled(response, place, delay)
        world.para()
        if settled:
            settle(world, elder, response, place_ent)
            lesson(world, elder, speaker, warner, forbidden)
            world.para()
            safe_gift(world, elder, speaker, warner, gift, place)
            outcome = "settled"
        else:
            fail_settle(world, elder, response, place)
            grim_lesson(world, elder, speaker, forbidden, place)
            outcome = "marked"

    world.facts.update(
        place=place,
        forbidden=forbidden,
        response=response,
        gift=gift,
        speaker=speaker,
        warner=warner,
        elder=elder,
        outcome=outcome,
        severity=severity,
        delay=delay,
        disturbed=place_ent.meters["disturbed"] >= THRESHOLD,
        tangled=world.get("speaker").meters["voice_tangle"] >= THRESHOLD,
        relation=relation,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for forbidden_id, forbidden in FORBIDDEN_ACTS.items():
            if hazard_at_risk(forbidden, place):
                combos.append((place_id, forbidden_id))
    return combos


@dataclass
class StoryParams:
    place: str
    forbidden: str
    response: str
    gift: str
    speaker_name: str
    speaker_gender: str
    warner_name: str
    warner_gender: str
    elder: str
    trait: str
    delay: int = 0
    speaker_age: int = 5
    warner_age: int = 7
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


PLACES = {
    "moon_well": Place(
        id="moon_well",
        label="the Moon Well",
        phrase="the Moon Well beneath the cypress trees",
        path="stone path",
        danger_image="a cold wind rose from the well mouth",
        safe_image="the water held one bright moon without a ripple",
        tags={"echo", "well"},
    ),
    "echo_arch": Place(
        id="echo_arch",
        label="the Echo Arch",
        phrase="the Echo Arch cut into the hillside",
        path="goat path",
        danger_image="the arch moaned like a hollow horn",
        safe_image="the arch gave back each small word like a silver bell",
        tags={"echo", "arch", "deep_echo"},
    ),
    "reed_grotto": Place(
        id="reed_grotto",
        label="the Reed Grotto",
        phrase="the Reed Grotto behind the river bend",
        path="reed-lined path",
        danger_image="the reeds hissed though no feet touched them",
        safe_image="the reeds whispered like friends sharing secrets",
        tags={"echo", "grotto"},
    ),
    "market_square": Place(
        id="market_square",
        label="the market square",
        phrase="the market square at the foot of the hill",
        path="open road",
        danger_image="nothing mythic happened there",
        safe_image="children laughed among baskets and bread",
        sacred=False,
        echoing=False,
        tags={"ordinary"},
    ),
}

FORBIDDEN_ACTS = {
    "mock_pronoun": ForbiddenAct(
        id="mock_pronoun",
        label="a mocking pronoun",
        line="Hey, you! Let it answer if it can!",
        warning="A spirit should not be pointed at as if it were a toy.",
        lesson="Do not use a mocking pronoun to tease what listens in the dark.",
        tags={"pronoun", "respect"},
    ),
    "nameless_call": ForbiddenAct(
        id="nameless_call",
        label="a nameless call",
        line="Come out, whoever you are!",
        warning="Nameless calling stirs old things that would rather sleep.",
        lesson="Do not throw nameless words into sacred places.",
        tags={"name", "respect"},
    ),
    "laughing_echo": ForbiddenAct(
        id="laughing_echo",
        label="a laughing echo",
        line="Listen to it! It sounds silly!",
        warning="Laughter can be sharp when it is aimed at the hidden world.",
        lesson="Do not laugh at what you do not understand.",
        tags={"echo", "respect"},
    ),
}

RESPONSES = {
    "true_name_song": Response(
        id="true_name_song",
        label="the true-name song",
        sense=3,
        power=3,
        ritual_text='sang the old true-name song toward {place} until each note lay flat and gentle',
        fail_text='began the true-name song, but the wind was already tossing the notes apart',
        qa_text="sang the old true-name song to settle the spirit",
        tags={"song", "respect"},
    ),
    "reed_bell": Response(
        id="reed_bell",
        label="the reed bell",
        sense=3,
        power=2,
        ritual_text='rang the reed bell three times and spoke a respectful apology to {place}',
        fail_text='rang the reed bell, but the answer from {place} came back harsher each time',
        qa_text="rang the reed bell and spoke an apology",
        tags={"bell", "respect"},
    ),
    "shout_back": Response(
        id="shout_back",
        label="shouting back",
        sense=1,
        power=1,
        ritual_text='shouted louder into {place} until the hill shouted louder too',
        fail_text='shouted back at {place}, which only made the spirit fiercer',
        qa_text="shouted back at the spirit",
        tags={"shouting"},
    ),
}

GIFTS = {
    "shell_harp": Gift(
        id="shell_harp",
        label="shell harp",
        phrase="a little shell harp",
        use_text="They plucked it softly by the doorway, then practiced saying kind words to one another.",
        tags={"music"},
    ),
    "lamplight_bowl": Gift(
        id="lamplight_bowl",
        label="lamplight bowl",
        phrase="a bowl of lamplight with floating petals",
        use_text="They took turns speaking their own names over the warm light, careful and clear.",
        tags={"light"},
    ),
    "reed_whistle": Gift(
        id="reed_whistle",
        label="reed whistle",
        phrase="a reed whistle carved with tiny stars",
        use_text="They blew one soft note at a time and waited for silence before speaking again.",
        tags={"music"},
    ),
}

GIRL_NAMES = ["Neri", "Sela", "Mira", "Tala", "Luma", "Eda", "Rina", "Iris"]
BOY_NAMES = ["Ivo", "Tarin", "Pavel", "Oren", "Milo", "Daren", "Niko", "Soren"]
TRAITS = ["careful", "gentle", "thoughtful", "wise", "curious", "brisk"]
ELDERS = ["grandmother", "grandfather"]
CURATED = [
    StoryParams(
        place="moon_well",
        forbidden="mock_pronoun",
        response="true_name_song",
        gift="shell_harp",
        speaker_name="Neri",
        speaker_gender="girl",
        warner_name="Ivo",
        warner_gender="boy",
        elder="grandmother",
        trait="careful",
        delay=0,
        speaker_age=5,
        warner_age=7,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        place="echo_arch",
        forbidden="nameless_call",
        response="reed_bell",
        gift="lamplight_bowl",
        speaker_name="Milo",
        speaker_gender="boy",
        warner_name="Sela",
        warner_gender="girl",
        elder="grandfather",
        trait="thoughtful",
        delay=0,
        speaker_age=7,
        warner_age=6,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        place="echo_arch",
        forbidden="mock_pronoun",
        response="reed_bell",
        gift="reed_whistle",
        speaker_name="Oren",
        speaker_gender="boy",
        warner_name="Luma",
        warner_gender="girl",
        elder="grandmother",
        trait="gentle",
        delay=1,
        speaker_age=7,
        warner_age=5,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        place="reed_grotto",
        forbidden="laughing_echo",
        response="true_name_song",
        gift="lamplight_bowl",
        speaker_name="Mira",
        speaker_gender="girl",
        warner_name="Rina",
        warner_gender="girl",
        elder="grandmother",
        trait="wise",
        delay=0,
        speaker_age=4,
        warner_age=7,
        relation="siblings",
        trust=7,
    ),
]


KNOWLEDGE = {
    "pronoun": [
        (
            "What is a pronoun?",
            "A pronoun is a word like he, she, or they that can stand in for a name. It should be used carefully, because words can feel kind or rude depending on how they are spoken."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off a wall, cave, or hill and comes back to your ears. It can make one voice sound as if another voice answered."
        )
    ],
    "respect": [
        (
            "Why should we speak respectfully?",
            "Respectful words help people and places feel safe instead of mocked. Kind speech can calm fear before it grows bigger."
        )
    ],
    "bell": [
        (
            "What does a bell do in a story?",
            "A bell can mark a careful moment and call everyone to listen. In myths, a clear bell often stands for order returning after confusion."
        )
    ],
    "song": [
        (
            "Why does a song help in many myths?",
            "A song gives words a steady shape, so frightened hearts can calm down and listen together. In stories, singing often turns wild feelings into gentle ones."
        )
    ],
    "well": [
        (
            "What is a well?",
            "A well is a deep place where people draw water. Because it is deep and hollow, it can sometimes make sounds echo."
        )
    ],
    "arch": [
        (
            "What is an arch?",
            "An arch is a curved opening made of stone or wood. A stone arch can bounce sound back in a strong echo."
        )
    ],
    "grotto": [
        (
            "What is a grotto?",
            "A grotto is a small cave-like place, often cool, hidden, and full of echoes or dripping water."
        )
    ],
}
KNOWLEDGE_ORDER = ["pronoun", "echo", "respect", "song", "bell", "well", "arch", "grotto"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    speaker = f["speaker"]
    warner = f["warner"]
    place = f["place"]
    forbidden = f["forbidden"]
    outcome = f["outcome"]
    base = (
        'Write a short cautionary myth for a 3-to-5-year-old that includes the word "pronoun".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle myth where {speaker.id} is tempted to use {forbidden.label} at {place.label}, but {warner.id} warns {speaker.pronoun('object')} in time and nothing terrible happens.",
            "Write a mythic story about careful speech, an old listening place, and a child who chooses wisdom before trouble begins.",
        ]
    if outcome == "marked":
        return [
            base,
            f"Tell a cautionary myth where a child mocks a sacred echoing place and learns a hard lesson when the night itself seems to answer.",
            f"Write a myth-like story where careless words wake fear at {place.label}, and the ending stays safe but solemn.",
        ]
    return [
        base,
        f"Tell a myth where {speaker.id} ignores a warning, uses {forbidden.label} at {place.label}, and an elder must calm the awakened spirit.",
        "Write a child-facing cautionary myth about how respectful words can repair harm after a foolish moment.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    speaker = f["speaker"]
    warner = f["warner"]
    elder = f["elder"]
    place = f["place"]
    forbidden = f["forbidden"]
    response = f["response"]
    gift = f["gift"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(speaker, warner, relation)}, {speaker.id} and {warner.id}, and {elder.label_word} who knows the old rules of the hill."
        ),
        (
            f"Where did {speaker.id} and {warner.id} go?",
            f"They walked to {place.phrase}. The place mattered because the elders believed a listening spirit slept there."
        ),
        (
            f"What mistake did {speaker.id} almost make or make?",
            f"{speaker.id} wanted to use {forbidden.label} at the sacred place. The warning mattered because careless words were believed to wake the echoing spirit."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {speaker.id} stop?",
                f"{speaker.id} heard the fear and wisdom in {warner.id}'s warning and decided the joke was not worth the risk. Because {speaker.pronoun()} listened in time, the spirit never woke at all."
            )
        )
        qa.append(
            (
                f"What happened at the end?",
                f"The elder brought out {gift.phrase}, and the children practiced gentle speech instead. The peaceful ending shows that wisdom changed what they did next."
            )
        )
    elif f["outcome"] == "settled":
        qa.append(
            (
                "What happened when the careless words went into the sacred place?",
                f"The echo came back wrong, a cold wind rose, and {speaker.id}'s voice tangled. The trouble grew because the mocking call disturbed a place that was meant to be treated with respect."
            )
        )
        qa.append(
            (
                f"How did {elder.label_word} help?",
                f"{elder.label_word.capitalize()} {response.qa_text}. That calm ritual settled the spirit and gave the children a chance to learn instead of staying frightened."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that words matter, especially in moments of fear or pride. {forbidden.lesson}."
            )
        )
    else:
        qa.append(
            (
                f"Did the elder fix everything right away?",
                f"No. The elder tried, but the spirit left a while of fear behind, and {speaker.id}'s voice stayed tangled through the night. The story is cautionary because some harms do not disappear at once."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely but solemnly: by dawn the voice returned, yet {speaker.id} never forgot the lesson. The final image shows a child treating the old place with humble care."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["forbidden"].tags) | set(f["response"].tags) | set(f["place"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("sacred", e.sacred), ("echoing", e.echoing), ("calming", e.calming)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, forbidden: ForbiddenAct) -> str:
    if not place.sacred or not place.echoing:
        return (
            f"(No story: {place.label} is not a sacred echoing place, so {forbidden.label} would not wake any spirit. "
            f"Pick a place like moon_well, echo_arch, or reed_grotto.)"
        )
    if not forbidden.wakes_echo:
        return (
            f"(No story: {forbidden.label} would not disturb the spirit here.)"
        )
    return "(No story: this combination has no mythic danger.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too unreasonable for this world "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.speaker_age, params.warner_age, params.trait):
        return "averted"
    return "settled" if is_settled(RESPONSES[params.response], PLACES[params.place], params.delay) else "marked"


ASP_RULES = r"""
hazard(F, P) :- wakes_echo(F), sacred(P), echoing(P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, F) :- place(P), forbidden(F), hazard(F, P).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_guide :- relation(siblings), speaker_age(SA), warner_age(WA), WA > SA.
bonus(3) :- older_guide.
bonus(0) :- not older_guide.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_guide, authority(A), bravery_init(BR), A > BR.

severity(1 + D + X) :- chosen_place(P), delay(D), deep_echo(P, X).
resp_power(Pw) :- chosen_response(R), power(R, Pw).
settled :- resp_power(Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(settled) :- not averted, settled.
outcome(marked) :- not averted, not settled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.sacred:
            lines.append(asp.fact("sacred", place_id))
        if place.echoing:
            lines.append(asp.fact("echoing", place_id))
        extra = 1 if "deep_echo" in place.tags else 0
        lines.append(asp.fact("deep_echo", place_id, extra))
    for forbidden_id, forbidden in FORBIDDEN_ACTS.items():
        lines.append(asp.fact("forbidden", forbidden_id))
        if forbidden.wakes_echo:
            lines.append(asp.fact("wakes_echo", forbidden_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("speaker_age", params.speaker_age),
        asp.fact("warner_age", params.warner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  clingo:", sorted(clingo_sensible))
        print("  python:", sorted(python_sensible))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a cautionary myth about careless speech, an echoing spirit, and a wise repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--forbidden", choices=FORBIDDEN_ACTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the spirit troubles the place before the elder settles it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.forbidden:
        place = PLACES[args.place]
        forbidden = FORBIDDEN_ACTS[args.forbidden]
        if not hazard_at_risk(forbidden, place):
            raise StoryError(explain_rejection(place, forbidden))
    if args.place and not (PLACES[args.place].sacred and PLACES[args.place].echoing):
        forbidden = FORBIDDEN_ACTS[args.forbidden] if args.forbidden else next(iter(FORBIDDEN_ACTS.values()))
        raise StoryError(explain_rejection(PLACES[args.place], forbidden))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.forbidden is None or combo[1] == args.forbidden)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, forbidden_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gift_id = args.gift or rng.choice(sorted(GIFTS))
    speaker_name, speaker_gender = _pick_child(rng)
    warner_name, warner_gender = _pick_child(rng, avoid=speaker_name)
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    speaker_age, warner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(2, 8)

    return StoryParams(
        place=place_id,
        forbidden=forbidden_id,
        response=response_id,
        gift=gift_id,
        speaker_name=speaker_name,
        speaker_gender=speaker_gender,
        warner_name=warner_name,
        warner_gender=warner_gender,
        elder=elder,
        trait=trait,
        delay=delay,
        speaker_age=speaker_age,
        warner_age=warner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.forbidden not in FORBIDDEN_ACTS:
        raise StoryError(f"(Invalid forbidden act: {params.forbidden})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Invalid gift: {params.gift})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(FORBIDDEN_ACTS[params.forbidden], PLACES[params.place]):
        raise StoryError(explain_rejection(PLACES[params.place], FORBIDDEN_ACTS[params.forbidden]))

    world = tell(
        place=PLACES[params.place],
        forbidden=FORBIDDEN_ACTS[params.forbidden],
        response=RESPONSES[params.response],
        gift=GIFTS[params.gift],
        speaker_name=params.speaker_name,
        speaker_gender=params.speaker_gender,
        warner_name=params.warner_name,
        warner_gender=params.warner_gender,
        trait=params.trait,
        elder_type=params.elder,
        delay=params.delay,
        speaker_age=params.speaker_age,
        warner_age=params.warner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, forbidden) combos:\n")
        for place_id, forbidden_id in combos:
            print(f"  {place_id:12} {forbidden_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.speaker_name} and {p.warner_name}: {p.forbidden} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
