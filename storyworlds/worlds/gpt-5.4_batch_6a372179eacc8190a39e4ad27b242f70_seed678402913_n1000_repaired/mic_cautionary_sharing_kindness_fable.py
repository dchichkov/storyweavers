#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mic_cautionary_sharing_kindness_fable.py
===================================================================

A standalone story world for a small fable-like domain about one shining mic,
two little animals, and the lesson that a voice sounds sweeter when it makes
room for another voice too.

Premise
-------
At a woodland gathering, one young animal is eager to speak or sing into the
only mic. A kind friend is waiting for a turn. If the eager performer clutches
the mic and chases all the attention, the crowd grows quiet in the wrong way:
the friend feels hurt, the listeners stop smiling, and the performance loses
its warmth. A kind repair can still save the evening -- but only if the repair
fits the act. A chorus makes sense for a song, not for a thank-you speech.

Why the constraint exists
-------------------------
This world is about *sharing a mic* honestly, not just swapping nouns. The
repair must fit the kind of performance:

* pass_turn works for any act;
* duet works for songs, poems, and riddles;
* chorus works only for songs.

The world rejects mismatched fixes because they would weaken the problem/repair
logic. The declarative ASP twin mirrors both the compatibility gate and the
outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/mic_cautionary_sharing_kindness_fable.py
    python storyworlds/worlds/gpt-5.4/mic_cautionary_sharing_kindness_fable.py --act song --repair chorus
    python storyworlds/worlds/gpt-5.4/mic_cautionary_sharing_kindness_fable.py --act speech --repair chorus
    python storyworlds/worlds/gpt-5.4/mic_cautionary_sharing_kindness_fable.py --all
    python storyworlds/worlds/gpt-5.4/mic_cautionary_sharing_kindness_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/mic_cautionary_sharing_kindness_fable.py --qa --json
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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

EGO_BASE = 5
CURIOSITY_TRAITS = {"showy", "proud"}
BRAVE_TRAITS = {"brave", "steady"}
KIND_TRAITS = {"kind", "gentle", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "duck", "goose", "ewe"}
        male = {"boy", "fox", "badger", "bear", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    opening: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    label: str
    verb: str
    gerund: str
    opening: str
    can_duet: bool = False
    can_chorus: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mic:
    id: str
    label: str
    phrase: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    kindness: int
    courage_need: int
    text: str
    success: str
    failure: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    act: str
    mic: str
    repair: str
    hero_name: str
    hero_type: str
    hero_trait: str
    friend_name: str
    friend_type: str
    friend_trait: str
    seed: Optional[int] = None


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


def _r_crowd_reacts(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    crowd = world.get("crowd")
    mic = world.get("mic")
    if mic.meters["shared"] < THRESHOLD and hero.meters["holding_mic"] >= THRESHOLD:
        sig = ("crowd_reacts",)
        if sig not in world.fired:
            world.fired.add(sig)
            crowd.memes["restless"] += 1
            friend.memes["hurt"] += 1
            hero.memes["lonely"] += 1
            out.append("__restless__")
    return out


def _r_shared_joy(world: World) -> list[str]:
    out: list[str] = []
    mic = world.get("mic")
    if mic.meters["shared"] < THRESHOLD:
        return out
    sig = ("shared_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    crowd = world.get("crowd")
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    crowd.memes["warmth"] += 1
    crowd.memes["restless"] = 0.0
    out.append("__warmth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="crowd_reacts", tag="social", apply=_r_crowd_reacts),
    Rule(name="shared_joy", tag="social", apply=_r_shared_joy),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the meadow stump",
        opening="At the edge of the meadow, the animals had set a smooth stump like a tiny stage.",
        affords={"song", "poem", "riddle", "speech"},
        tags={"gathering"},
    ),
    "barn": Place(
        id="barn",
        label="the warm barn loft",
        opening="In the warm barn loft, lantern light swung softly over a row of hay-bale seats.",
        affords={"song", "poem", "riddle", "speech"},
        tags={"gathering"},
    ),
    "pond": Place(
        id="pond",
        label="the pond-side platform",
        opening="Beside the pond, a little plank platform waited among the reeds.",
        affords={"song", "poem", "riddle"},
        tags={"gathering"},
    ),
}

ACTS = {
    "song": Act(
        id="song",
        label="song",
        verb="sing a little song",
        gerund="singing",
        opening="Everyone had come to hear cheerful sounds before dusk.",
        can_duet=True,
        can_chorus=True,
        tags={"song"},
    ),
    "poem": Act(
        id="poem",
        label="poem",
        verb="recite a short poem",
        gerund="reciting",
        opening="Everyone had come to hear neat, careful words before supper.",
        can_duet=True,
        can_chorus=False,
        tags={"poem"},
    ),
    "riddle": Act(
        id="riddle",
        label="riddle",
        verb="tell a bright riddle",
        gerund="telling riddles",
        opening="Everyone had come to guess and giggle together.",
        can_duet=True,
        can_chorus=False,
        tags={"riddle"},
    ),
    "speech": Act(
        id="speech",
        label="thank-you speech",
        verb="give a thank-you speech",
        gerund="speaking",
        opening="Everyone had come to clap for small good deeds done all week.",
        can_duet=False,
        can_chorus=False,
        tags={"speech"},
    ),
}

MICS = {
    "shell": Mic(
        id="shell",
        label="shell mic",
        phrase="a shiny shell mic",
        shine="Its round top caught the sunset and made the little stage look grand.",
        tags={"mic"},
    ),
    "tin": Mic(
        id="tin",
        label="tin mic",
        phrase="a polished tin mic",
        shine="It gleamed like a small moon on a stick.",
        tags={"mic"},
    ),
    "sunflower": Mic(
        id="sunflower",
        label="sunflower mic",
        phrase="a bright sunflower mic",
        shine="Its yellow petals bobbed as if they were already clapping.",
        tags={"mic"},
    ),
}

REPAIRS = {
    "pass_turn": Repair(
        id="pass_turn",
        label="pass the mic",
        kindness=2,
        courage_need=1,
        text='"{friend}, would you like a turn too?"',
        success="The mic changed paws at last, and the whole gathering leaned in again.",
        failure="But the words stayed only words, and the mic never left the first pair of paws.",
        qa_text="passed the mic and made room for a turn",
        tags={"sharing", "kindness"},
    ),
    "duet": Repair(
        id="duet",
        label="share it as a duet",
        kindness=3,
        courage_need=2,
        text='"{friend}, come stand by me. We can do this together."',
        success="Two voices met beside the mic, and the sound grew fuller instead of smaller.",
        failure="But one voice still pushed over the other, and the together-part never truly began.",
        qa_text="invited a shared duet at the mic",
        tags={"sharing", "kindness"},
    ),
    "chorus": Repair(
        id="chorus",
        label="start a chorus",
        kindness=3,
        courage_need=2,
        text='"{friend}, start with me, and then everyone can join the chorus."',
        success="Soon the whole crowd was humming, and no one cared who had started first.",
        failure="But the invitation came too late, and the crowd had already fallen quiet and cold.",
        qa_text="turned the moment into a shared chorus",
        tags={"sharing", "kindness", "song"},
    ),
}

ANIMALS = [
    ("Pip", "sparrow"),
    ("Mara", "mouse"),
    ("Tansy", "duck"),
    ("Bram", "badger"),
    ("Nell", "hen"),
    ("Otis", "otter"),
    ("Wren", "sparrow"),
    ("Moss", "mouse"),
]

HERO_TRAITS = ["showy", "proud", "bouncy", "eager"]
FRIEND_TRAITS = ["kind", "gentle", "patient", "brave", "steady"]


def valid_repair_for(act: Act, repair: Repair) -> bool:
    if repair.id == "pass_turn":
        return True
    if repair.id == "duet":
        return act.can_duet
    if repair.id == "chorus":
        return act.can_chorus
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for act_id in sorted(place.affords):
            act = ACTS[act_id]
            for repair_id, repair in REPAIRS.items():
                if valid_repair_for(act, repair):
                    combos.append((place_id, act_id, repair_id))
    return combos


def hero_ego(trait: str) -> int:
    return EGO_BASE + (2 if trait in CURIOSITY_TRAITS else 0)


def friend_courage(trait: str) -> int:
    return 2 if trait in BRAVE_TRAITS else 1


def friend_kindness(trait: str) -> int:
    return 2 if trait in KIND_TRAITS else 1


def sharing_succeeds(hero_trait: str, friend_trait: str, repair_id: str) -> bool:
    repair = REPAIRS[repair_id]
    strength = friend_courage(friend_trait) + friend_kindness(friend_trait) + repair.kindness
    return strength > hero_ego(hero_trait)


def explain_rejection(place: Place, act: Act, repair: Repair) -> str:
    if act.id not in place.affords:
        return (
            f"(No story: {place.label} is not used here for a {act.label}. "
            f"Pick an act that fits the gathering.)"
        )
    return (
        f"(No story: '{repair.label}' does not fit a {act.label}. "
        f"The repair must match the performance, so this combination is refused.)"
    )


def predict_hogging(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    mic = sim.get("mic")
    hero.meters["holding_mic"] += 1
    mic.meters["shared"] = 0.0
    propagate(sim, narrate=False)
    return {
        "restless": sim.get("crowd").memes["restless"],
        "hurt": sim.get("friend").memes["hurt"],
        "lonely": sim.get("hero").memes["lonely"],
    }


def introduce(world: World, hero: Entity, friend: Entity, mic_cfg: Mic, act: Act) -> None:
    place = world.place
    mic = world.get("mic")
    world.say(place.opening)
    world.say(act.opening)
    world.say(
        f"On the stump stood {mic_cfg.phrase}. {mic_cfg.shine}"
    )
    world.say(
        f"{hero.id} and {friend.id} had both practiced for the evening, and both hoped for a turn with the mic."
    )
    hero.memes["eager"] += 1
    friend.memes["hope"] += 1
    mic.meters["ready"] += 1


def desire(world: World, hero: Entity, friend: Entity, act: Act) -> None:
    world.say(
        f"{hero.id}, a {hero.type} with a {hero.traits[0]} heart, stepped first and wanted to {act.verb}. "
        f"{friend.id}, a {friend.type} known for being {friend.traits[0]}, waited close by with patient eyes."
    )


def hog(world: World, hero: Entity, friend: Entity, act: Act) -> None:
    mic = world.get("mic")
    hero.meters["holding_mic"] += 1
    hero.memes["pride"] += 1
    mic.meters["shared"] = 0.0
    pred = predict_hogging(world)
    world.facts["predicted_restless"] = pred["restless"]
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f"When the music shell rang, {hero.id} wrapped both paws around the mic and began {act.gerund} as if the whole evening belonged only to {hero.pronoun('object')}."
    )
    world.say(
        f"{friend.id} opened {friend.pronoun('possessive')} mouth for a turn, but the mic never moved."
    )
    propagate(world, narrate=False)
    if pred["hurt"] >= THRESHOLD:
        world.say(
            f"A hush spread through the seats. It was not the warm listening hush. It was the hush that comes when one small heart is left out."
        )


def consequence(world: World, hero: Entity, friend: Entity) -> None:
    crowd = world.get("crowd")
    if crowd.memes["restless"] >= THRESHOLD:
        world.say(
            f"The listeners stopped smiling. Even the crickets seemed to tuck their music away."
        )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s ears drooped, and {friend.pronoun()} looked not angry, only hurt."
        )
    if hero.memes["lonely"] >= THRESHOLD:
        world.say(
            f"Then {hero.id} noticed something strange: holding the mic all alone made the stage feel smaller, not bigger."
        )


def attempt_repair(world: World, hero: Entity, friend: Entity, repair: Repair) -> None:
    hero.memes["remorse"] += 1
    friend.memes["kindness"] += 1
    line = repair.text.format(friend=friend.id)
    world.say(
        f"{hero.id} lowered the mic a little and said, {line}"
    )


def succeed(world: World, hero: Entity, friend: Entity, act: Act, repair: Repair) -> None:
    mic = world.get("mic")
    crowd = world.get("crowd")
    mic.meters["shared"] += 1
    friend.meters["holding_mic"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["generosity"] += 1
    friend.memes["hurt"] = 0.0
    crowd.memes["warmth"] += 1
    propagate(world, narrate=False)
    world.say(repair.success)
    if repair.id == "pass_turn":
        world.say(
            f"{friend.id} took a neat little turn, and then passed the mic back with a grateful smile."
        )
    elif repair.id == "duet":
        world.say(
            f"One voice was bright and one was soft, and because each made room for the other, both could be heard."
        )
    else:
        world.say(
            f"Before long the meadow was full of shared song, and the mic seemed happiest in the middle of many voices."
        )
    world.say(
        f"When the applause came, {hero.id} grinned at {friend.id} instead of bowing alone."
    )
    world.say(
        f"That night they walked home side by side, and the mic had taught what the moon already knew: light is lovelier when it is shared."
    )


def fail(world: World, hero: Entity, friend: Entity, repair: Repair) -> None:
    hero.memes["pride"] += 1
    world.say(repair.failure)
    world.say(
        f"{friend.id} stepped back so quietly that only the nearest firefly noticed."
    )
    world.say(
        f"The performance ended, but it did not feel finished. The clapping was thin, and {hero.id} carried the mic home in silence."
    )
    world.say(
        f"From then on, {hero.id} remembered that a greedy paw may hold a mic, yet still lose the music of friendship."
    )


def tell(
    place: Place,
    act: Act,
    mic_cfg: Mic,
    repair: Repair,
    hero_name: str,
    hero_type: str,
    hero_trait: str,
    friend_name: str,
    friend_type: str,
    friend_trait: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[hero_trait],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_type,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        traits=[friend_trait],
    ))
    mic = world.add(Entity(
        id="mic",
        kind="thing",
        type="mic",
        label=mic_cfg.label,
        phrase=mic_cfg.phrase,
        role="prop",
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="thing",
        type="crowd",
        label="the listeners",
        phrase="the listeners",
        role="crowd",
    ))

    introduce(world, hero, friend, mic_cfg, act)
    desire(world, hero, friend, act)

    world.para()
    hog(world, hero, friend, act)
    consequence(world, hero, friend)

    world.para()
    attempt_repair(world, hero, friend, repair)
    success = sharing_succeeds(hero_trait, friend_trait, repair.id)
    if success:
        succeed(world, hero, friend, act, repair)
        outcome = "shared"
    else:
        fail(world, hero, friend, repair)
        outcome = "soured"

    world.facts.update(
        hero=hero,
        friend=friend,
        crowd=crowd,
        mic_cfg=mic_cfg,
        act=act,
        place=place,
        repair=repair,
        outcome=outcome,
        success=success,
        hero_name=hero_name,
        friend_name=friend_name,
    )
    return world


def animal_label(ent: Entity, name: str) -> str:
    return f"{name} the {ent.type}"


KNOWLEDGE = {
    "mic": [
        (
            "What is a mic?",
            "A mic, short for microphone, helps a voice sound louder so many listeners can hear. It works best when people take turns and use it gently."
        )
    ],
    "sharing": [
        (
            "Why is sharing important?",
            "Sharing makes room for more than one person to join in. When everyone gets a turn, the group feels fairer and kinder."
        )
    ],
    "kindness": [
        (
            "What does kindness look like when two friends want the same thing?",
            "Kindness means noticing the other friend's feelings and making room for them too. It often means taking turns, inviting them in, or using gentle words."
        )
    ],
    "song": [
        (
            "What is a chorus in a song?",
            "A chorus is the part of a song that comes back again, and many voices can sing it together. That is why a chorus can turn one voice into a shared sound."
        )
    ],
    "poem": [
        (
            "What is a poem?",
            "A poem is a piece of writing with careful, special words. People often read poems slowly so the words can be heard clearly."
        )
    ],
    "riddle": [
        (
            "What is a riddle?",
            "A riddle is a little puzzle told in words. It gives clues so listeners can guess the answer."
        )
    ],
    "speech": [
        (
            "What is a thank-you speech?",
            "A thank-you speech is a short talk where someone tells others they are grateful. It works best when the speaker is thoughtful and clear."
        )
    ],
}
KNOWLEDGE_ORDER = ["mic", "sharing", "kindness", "song", "poem", "riddle", "speech"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    act = world.facts["act"]
    repair = world.facts["repair"]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the word "mic" and teaches sharing.',
        f"Tell a cautionary woodland story where {world.facts['hero_name']} wants to {act.verb} into a mic and must learn to make room for {world.facts['friend_name']}.",
        f'Write a gentle kindness fable where the right repair is "{repair.label}" and the ending proves that shared attention feels better than lonely attention.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    act = world.facts["act"]
    repair = world.facts["repair"]
    mic_cfg = world.facts["mic_cfg"]
    hero_name = world.facts["hero_name"]
    friend_name = world.facts["friend_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {animal_label(hero, hero_name)} and {animal_label(friend, friend_name)} at a woodland gathering. They both hoped to use {mic_cfg.phrase}."
        ),
        (
            f"What did {hero_name} want to do with the mic?",
            f"{hero_name} wanted to {act.verb}. That is why {hero.pronoun()} stepped up first and held the mic so tightly."
        ),
        (
            f"Why did the gathering start to feel wrong?",
            f"It felt wrong because {hero_name} kept the mic and did not make room for {friend_name}. That hurt {friend_name}'s feelings and made the listeners stop smiling."
        ),
    ]
    if world.facts["success"]:
        qa.append(
            (
                f"How was the problem fixed?",
                f"{hero_name} {repair.qa_text}. The repair worked because it turned the moment from one small performance into something shared and kind."
            )
        )
        qa.append(
            (
                f"How did {hero_name} change by the end?",
                f"{hero_name} learned that holding attention alone felt lonely, but sharing the mic brought back warmth and applause. {hero.pronoun().capitalize()} ended the evening beside {friend_name}, not above {friend.pronoun('object')}."
            )
        )
    else:
        qa.append(
            (
                f"Did the repair work?",
                f"No. {hero_name} tried too late or too weakly, and the sharing never truly began. The crowd stayed cold because kindness needs real room, not just a quick word."
            )
        )
        qa.append(
            (
                "What is the lesson of the story?",
                f"The lesson is that grabbing all the attention can spoil both friendship and the joyful part of performing. A mic sounds poorest when only pride is speaking into it."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mic", "sharing", "kindness"} | set(world.facts["act"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="meadow",
        act="song",
        mic="sunflower",
        repair="chorus",
        hero_name="Pip",
        hero_type="sparrow",
        hero_trait="showy",
        friend_name="Mara",
        friend_type="mouse",
        friend_trait="kind",
        seed=1,
    ),
    StoryParams(
        place="barn",
        act="poem",
        mic="shell",
        repair="duet",
        hero_name="Bram",
        hero_type="badger",
        hero_trait="proud",
        friend_name="Nell",
        friend_type="hen",
        friend_trait="steady",
        seed=2,
    ),
    StoryParams(
        place="meadow",
        act="speech",
        mic="tin",
        repair="pass_turn",
        hero_name="Otis",
        hero_type="otter",
        hero_trait="eager",
        friend_name="Tansy",
        friend_type="duck",
        friend_trait="gentle",
        seed=3,
    ),
    StoryParams(
        place="pond",
        act="riddle",
        mic="shell",
        repair="duet",
        hero_name="Moss",
        hero_type="mouse",
        hero_trait="showy",
        friend_name="Wren",
        friend_type="sparrow",
        friend_trait="patient",
        seed=4,
    ),
]


ASP_RULES = r"""
valid(Place, Act, Repair) :- affords(Place, Act), repair(Repair), fits(Repair, Act).

fits(pass_turn, Act) :- act(Act).
fits(duet, Act)      :- duet_ok(Act).
fits(chorus, Act)    :- chorus_ok(Act).

ego(7) :- hero_trait(T), high_ego(T).
ego(5) :- hero_trait(T), not high_ego(T).

courage(2)  :- friend_trait(T), brave_friend(T).
courage(1)  :- friend_trait(T), not brave_friend(T).

kindness(2) :- friend_trait(T), kind_friend(T).
kindness(1) :- friend_trait(T), not kind_friend(T).

repair_strength(K) :- chosen_repair(R), repair_kindness(R, K).
strength(C + K + R) :- courage(C), kindness(K), repair_strength(R).

outcome(shared) :- strength(S), ego(E), S > E.
outcome(soured) :- strength(S), ego(E), S <= E.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for act_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, act_id))
    for act_id, act in ACTS.items():
        lines.append(asp.fact("act", act_id))
        if act.can_duet:
            lines.append(asp.fact("duet_ok", act_id))
        if act.can_chorus:
            lines.append(asp.fact("chorus_ok", act_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_kindness", repair_id, repair.kindness))
    for trait in sorted(CURIOSITY_TRAITS):
        lines.append(asp.fact("high_ego", trait))
    for trait in sorted(BRAVE_TRAITS):
        lines.append(asp.fact("brave_friend", trait))
    for trait in sorted(KIND_TRAITS):
        lines.append(asp.fact("kind_friend", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("hero_trait", params.hero_trait),
            asp.fact("friend_trait", params.friend_trait),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared" if sharing_succeeds(params.hero_trait, params.friend_trait, params.repair) else "soured"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    scenarios = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    bad = [p for p in scenarios if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes on {len(bad)} scenarios.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mic, a selfish turn, and the kinder sound of sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--mic", choices=MICS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, act, repair) combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_animal(rng: random.Random, avoid_name: str = "") -> tuple[str, str]:
    options = [pair for pair in ANIMALS if pair[0] != avoid_name]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.act and args.repair:
        place = PLACES[args.place]
        act = ACTS[args.act]
        repair = REPAIRS[args.repair]
        if not (args.act in place.affords and valid_repair_for(act, repair)):
            raise StoryError(explain_rejection(place, act, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.act is None or combo[1] == args.act)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, act_id, repair_id = rng.choice(sorted(combos))
    mic_id = args.mic or rng.choice(sorted(MICS))
    hero_name, hero_type = pick_animal(rng)
    friend_name, friend_type = pick_animal(rng, avoid_name=hero_name)
    hero_trait = rng.choice(HERO_TRAITS)
    friend_trait = rng.choice(FRIEND_TRAITS)

    return StoryParams(
        place=place_id,
        act=act_id,
        mic=mic_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_type=hero_type,
        hero_trait=hero_trait,
        friend_name=friend_name,
        friend_type=friend_type,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.act not in ACTS:
        raise StoryError(f"(Unknown act: {params.act})")
    if params.mic not in MICS:
        raise StoryError(f"(Unknown mic: {params.mic})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    place = PLACES[params.place]
    act = ACTS[params.act]
    repair = REPAIRS[params.repair]
    if not (params.act in place.affords and valid_repair_for(act, repair)):
        raise StoryError(explain_rejection(place, act, repair))

    world = tell(
        place=place,
        act=act,
        mic_cfg=MICS[params.mic],
        repair=repair,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        hero_trait=params.hero_trait,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        friend_trait=params.friend_trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("friend", params.friend_name),
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, act, repair) combos:\n")
        for place, act, repair in combos:
            print(f"  {place:8} {act:8} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.act} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
