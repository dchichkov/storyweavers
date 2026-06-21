#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/phonetic_symphony_teamwork_nursery_rhyme.py
======================================================================

A standalone storyworld about a little nursery-rhyme recital where a small team
helps one singer through a tricky opening sound. The domain is deliberately
tiny: a lead child or animal stands up to start a rhyme, stage jitters make the
first sound feel hard, and friends use a concrete teamwork method to turn the
wobble into a cheerful symphony.

The world model tracks both physical meters (beat, rustle, voice, music) and
emotional memes (jitters, confidence, togetherness). A simple forward-chaining
rule system turns stage fright into a wobble and active teamwork into steadier
music. The story prose reads those live states rather than filling one frozen
template.

Run it
------
    python storyworlds/worlds/gpt-5.4/phonetic_symphony_teamwork_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/phonetic_symphony_teamwork_nursery_rhyme.py --rhyme pebbles --method stepping_circle --helpers 2
    python storyworlds/worlds/gpt-5.4/phonetic_symphony_teamwork_nursery_rhyme.py --rhyme pebbles --method bell_points --helpers 1
    python storyworlds/worlds/gpt-5.4/phonetic_symphony_teamwork_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/phonetic_symphony_teamwork_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/phonetic_symphony_teamwork_nursery_rhyme.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose"}
        male = {"boy", "father", "gander"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    decor: str
    soundscape: str
    floor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    title: str
    opening_word: str
    sound: str
    sound_kind: str
    difficulty: int
    couplet_a: str
    couplet_b: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    power: int
    supports: set[str] = field(default_factory=set)
    lead_in: str = ""
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def helpers(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "helper"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_wobble(world: World) -> list[str]:
    lead = world.get("lead")
    hall = world.get("hall")
    if lead.meters["attempt"] < THRESHOLD:
        return []
    if lead.memes["confidence"] >= lead.memes["jitters"]:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.meters["wobble"] += 1
    hall.meters["confusion"] += 1
    return ["__wobble__"]


def _r_team_steady(world: World) -> list[str]:
    hall = world.get("hall")
    if hall.meters["cue"] < THRESHOLD:
        return []
    sig = ("steady", int(hall.meters["cue"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead = world.get("lead")
    helpers = len(world.helpers())
    lead.memes["confidence"] += float(helpers)
    lead.meters["voice"] += 1
    hall.memes["together"] += 1
    return ["__steady__"]


def _r_music(world: World) -> list[str]:
    lead = world.get("lead")
    hall = world.get("hall")
    if lead.meters["voice"] < THRESHOLD or hall.memes["together"] < THRESHOLD:
        return []
    sig = ("music",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["music"] += 1
    return ["__music__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="emotional", apply=_r_wobble),
    Rule(name="steady", tag="social", apply=_r_team_steady),
    Rule(name="music", tag="physical", apply=_r_music),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the daisy meadow",
        decor="Daisies made a soft white ring around the little stage.",
        soundscape="bees hummed beyond the clover",
        floor="springy grass",
        tags={"meadow", "outside"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the nursery playroom",
        decor="A bright quilt lay under a row of wooden stools.",
        soundscape="blocks clicked in a basket by the wall",
        floor="a patchwork rug",
        tags={"playroom", "inside"},
    ),
    "moon_garden": Setting(
        id="moon_garden",
        place="the moonlit garden",
        decor="Paper stars bobbed from the bean poles over the path.",
        soundscape="crickets stitched tiny sounds into the dark",
        floor="warm stepping stones",
        tags={"garden", "night"},
    ),
}

RHYMES = {
    "bunny": Rhyme(
        id="bunny",
        title="Bunny Bell",
        opening_word="Bunny",
        sound="b",
        sound_kind="sharp",
        difficulty=1,
        couplet_a="Bunny bell, bounce and sing,",
        couplet_b="bring the morning on a string.",
        ending_image="even the buttercups seemed to bob in time",
        tags={"bunny", "phonetic"},
    ),
    "sheep": Rhyme(
        id="sheep",
        title="Sleepy Sheep",
        opening_word="Sheep",
        sound="sh",
        sound_kind="soft",
        difficulty=2,
        couplet_a="Sheep go sh-sh by the gate,",
        couplet_b="hushing twilight while they wait.",
        ending_image="the lane looked tucked in, as if the song had pulled up a blanket",
        tags={"sheep", "phonetic"},
    ),
    "pebbles": Rhyme(
        id="pebbles",
        title="Pebble Plink",
        opening_word="Plink",
        sound="pl",
        sound_kind="blend",
        difficulty=3,
        couplet_a="Plink, little pebbles, bright in a row,",
        couplet_b="roll to the river where moon-mice go.",
        ending_image="the river answered with silver rings",
        tags={"pebbles", "phonetic"},
    ),
    "twirl": Rhyme(
        id="twirl",
        title="Twirl Star",
        opening_word="Twirl",
        sound="tw",
        sound_kind="blend",
        difficulty=3,
        couplet_a="Twirl, tiny star on a shoelace swing,",
        couplet_b="turn the dark into a golden ring.",
        ending_image="the hanging paper stars spun as if they had heard their own names",
        tags={"star", "phonetic"},
    ),
}

METHODS = {
    "clap_chain": Method(
        id="clap_chain",
        label="a clap-chain",
        power=2,
        supports={"sharp", "blend"},
        lead_in="made a neat ladder of claps",
        action_text="One friend clapped the first beat, another clapped the next, and the sound laid little stepping stones under the opening word.",
        qa_text="used a chain of claps so the lead singer could step into the first sound",
        tags={"clap", "teamwork"},
    ),
    "hum_cradle": Method(
        id="hum_cradle",
        label="a humming cradle",
        power=2,
        supports={"soft"},
        lead_in="hummed a soft cradle-note together",
        action_text="The helpers held one warm hum under the line, so the shy sound had somewhere gentle to land.",
        qa_text="hummed under the line to make the soft sound feel safe",
        tags={"hum", "teamwork"},
    ),
    "bell_points": Method(
        id="bell_points",
        label="bell points",
        power=1,
        supports={"sharp", "soft", "blend"},
        lead_in="rang tiny bells at the start of each beat",
        action_text="Each clear ring pointed to the next mouth-move, like little shining arrows.",
        qa_text="rang tiny bells to point at the beats of the opening sound",
        tags={"bells", "teamwork"},
    ),
    "stepping_circle": Method(
        id="stepping_circle",
        label="a stepping circle",
        power=3,
        supports={"blend", "soft"},
        lead_in="walked a small circle on the beat",
        action_text="They stepped around the lead singer in a round ring, and every footfall held a piece of the tricky sound steady.",
        qa_text="walked a careful circle so each beat of the tricky sound had support",
        tags={"steps", "teamwork"},
    ),
}

LEAD_TYPES = ["girl", "boy", "duckling", "lamb"]
GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo"]
ANIMAL_NAMES = ["Pip", "Dot", "Moss", "Wren", "Nib", "Poppy"]
HELPER_TYPES = ["girl", "boy", "duckling", "lamb", "goose"]

KNOWLEDGE = {
    "phonetic": [
        (
            "What does phonetic mean?",
            "Phonetic means about the sounds in words. When children practice a word one sound at a time, they are paying attention to its phonetic parts.",
        )
    ],
    "symphony": [
        (
            "What is a symphony?",
            "A symphony is many sounds working together as one piece of music. Different parts join in, but they fit together instead of bumping into each other.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help one another do something none of them could do as well alone. They listen, take turns, and share the job.",
        )
    ],
    "clap": [
        (
            "How can clapping help a singer?",
            "Clapping can make a steady beat. A steady beat helps a singer know when to start and how to keep going.",
        )
    ],
    "hum": [
        (
            "Why can a humming sound feel calming?",
            "A soft hum stays smooth and gentle. That can help a nervous singer feel less shaky and more ready to speak or sing.",
        )
    ],
    "bells": [
        (
            "What do little bells do in music?",
            "Little bells make bright, clear sounds. Their tiny rings can mark the beat so everyone knows where the music is going.",
        )
    ],
    "steps": [
        (
            "How can stepping together help a group?",
            "Stepping together gives the whole group one shared rhythm. When bodies move in time, voices often follow that same pattern.",
        )
    ],
}
KNOWLEDGE_ORDER = ["phonetic", "symphony", "teamwork", "clap", "hum", "bells", "steps"]


def method_supports(rhyme: Rhyme, method: Method) -> bool:
    return rhyme.sound_kind in method.supports


def support_score(method: Method, helpers: int) -> int:
    return method.power + helpers


def demand_score(rhyme: Rhyme, noise: int) -> int:
    return rhyme.difficulty + noise


def is_reasonable(rhyme: Rhyme, method: Method, helpers: int, noise: int) -> bool:
    return method_supports(rhyme, method) and support_score(method, helpers) > demand_score(rhyme, noise)


def outcome_of(params: "StoryParams") -> str:
    rhyme = RHYMES[params.rhyme]
    method = METHODS[params.method]
    margin = support_score(method, params.helpers) - demand_score(rhyme, params.noise)
    return "smooth" if margin >= 2 else "recovered"


def valid_combos() -> list[tuple[str, str, str, int, int]]:
    combos: list[tuple[str, str, str, int, int]] = []
    for setting_id in SETTINGS:
        for rhyme_id, rhyme in RHYMES.items():
            for method_id, method in METHODS.items():
                for helpers in [1, 2, 3]:
                    for noise in [0, 1]:
                        if is_reasonable(rhyme, method, helpers, noise):
                            combos.append((setting_id, rhyme_id, method_id, helpers, noise))
    return combos


@dataclass
class StoryParams:
    setting: str
    rhyme: str
    method: str
    helpers: int
    noise: int
    lead_name: str
    lead_type: str
    mentor_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="meadow",
        rhyme="bunny",
        method="clap_chain",
        helpers=2,
        noise=0,
        lead_name="Lily",
        lead_type="girl",
        mentor_type="mother",
    ),
    StoryParams(
        setting="playroom",
        rhyme="sheep",
        method="hum_cradle",
        helpers=2,
        noise=1,
        lead_name="Pip",
        lead_type="duckling",
        mentor_type="father",
    ),
    StoryParams(
        setting="moon_garden",
        rhyme="pebbles",
        method="stepping_circle",
        helpers=2,
        noise=1,
        lead_name="Ben",
        lead_type="boy",
        mentor_type="mother",
    ),
    StoryParams(
        setting="meadow",
        rhyme="twirl",
        method="clap_chain",
        helpers=3,
        noise=1,
        lead_name="Moss",
        lead_type="lamb",
        mentor_type="father",
    ),
]


def helper_phrase(world: World) -> str:
    names = [h.id for h in world.helpers()]
    if not names:
        return "no one"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def choose_helper_names(rng: random.Random, lead_name: str, count: int) -> list[str]:
    pool = [n for n in GIRL_NAMES + BOY_NAMES + ANIMAL_NAMES if n != lead_name]
    rng.shuffle(pool)
    return pool[:count]


def article_for_sound(sound: str) -> str:
    return "an" if sound[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def introduce(world: World, lead: Entity, mentor: Entity) -> None:
    setting = world.setting
    hall = world.get("hall")
    world.say(
        f"In {setting.place}, {setting.decor} {setting.soundscape}, and the {setting.floor} waited under little tapping feet."
    )
    world.say(
        f"{lead.id} had come with {lead.pronoun('possessive')} {mentor.label_word} to join the nursery band, where spoon taps, bell rings, and hums could grow into a child-sized symphony."
    )
    hall.meters["beat"] += 1


def gather_helpers(world: World, lead: Entity) -> None:
    names = helper_phrase(world)
    if len(world.helpers()) == 1:
        world.say(f"{names} stood close beside {lead.id}, ready to help if help was needed.")
    else:
        world.say(f"{names} crowded around {lead.id} with bright eyes and patient faces, ready to work as one team.")
    for helper in world.helpers():
        helper.memes["care"] += 1


def choose_rhyme(world: World, lead: Entity, rhyme: Rhyme) -> None:
    lead.memes["pride"] += 1
    world.say(
        f"When it was {lead.id}'s turn to begin {rhyme.title}, everyone hushed for the opening word, {rhyme.opening_word!r}, because its phonetic start had to be said clearly for the rhyme to sparkle."
    )


def stir_jitters(world: World, lead: Entity, rhyme: Rhyme, noise: int) -> None:
    hall = world.get("hall")
    lead.memes["jitters"] += float(rhyme.difficulty)
    if noise:
        hall.meters["rustle"] += 1
        lead.memes["jitters"] += 1
        world.say(
            "Just then, a small rustle ran through the room. A stool scraped, a bell knocked, and the waiting air suddenly felt much bigger."
        )
    else:
        world.say(
            "Even in the gentle hush, the first sound felt large in the lead singer's mouth."
        )


def first_attempt(world: World, lead: Entity, rhyme: Rhyme) -> None:
    lead.meters["attempt"] += 1
    propagate(world, narrate=False)
    if lead.meters["wobble"] >= THRESHOLD:
        world.say(
            f"{lead.id} opened {lead.pronoun('possessive')} mouth and tried to start with {article_for_sound(rhyme.sound)} {rhyme.sound!r} sound, but the word trembled and came out thin at the edge."
        )
    else:
        world.say(
            f"{lead.id} drew one careful breath and almost had the word, though {lead.pronoun('possessive')} eyes still looked for a little help."
        )


def teamwork(world: World, lead: Entity, method: Method) -> None:
    hall = world.get("hall")
    hall.meters["cue"] += 1
    world.say(
        f"Then {helper_phrase(world)} {method.lead_in}. {method.action_text}"
    )
    propagate(world, narrate=False)
    for helper in world.helpers():
        helper.memes["teamwork"] += 1
    lead.memes["confidence"] += float(method.power)
    hall.memes["together"] += 1


def retry(world: World, lead: Entity, rhyme: Rhyme, method: Method) -> None:
    hall = world.get("hall")
    margin = world.facts["margin"]
    if margin >= 2:
        world.say(
            f"With the steady help around {lead.id}, the hard little beginning no longer felt lonely. {lead.pronoun().capitalize()} set {lead.pronoun('possessive')} voice on the shared beat and sang,"
        )
    else:
        world.say(
            f"{lead.id} listened to the beat, the bells, and the feet around {lead.pronoun('object')}. This time {lead.pronoun()} tried the opening again, one brave bit at a time, and sang,"
        )
    world.say(f'"{rhyme.couplet_a}"')
    world.say(f'"{rhyme.couplet_b}"')
    lead.meters["voice"] += 1
    hall.meters["music"] += 1
    hall.meters["glow"] += 1
    propagate(world, narrate=False)


def ending(world: World, lead: Entity, mentor: Entity, rhyme: Rhyme) -> None:
    hall = world.get("hall")
    outcome = world.facts["outcome"]
    for helper in world.helpers():
        helper.memes["joy"] += 1
    lead.memes["joy"] += 1
    if outcome == "smooth":
        world.say(
            f"The whole room answered softly, and the little symphony held together from first beat to last. {rhyme.ending_image}, and {mentor.label_word} smiled as if the teamwork itself were music."
        )
    else:
        world.say(
            f"A tiny cheer skipped around the stage, because everyone had heard the turn from wobble to song. {rhyme.ending_image}, and {mentor.label_word} smiled at the brave teamwork that had carried the line home."
        )


def tell(
    setting: Setting,
    rhyme: Rhyme,
    method: Method,
    helpers: int,
    noise: int,
    lead_name: str,
    lead_type: str,
    mentor_type: str,
    helper_names: list[str],
    helper_types: list[str],
) -> World:
    world = World(setting=setting)
    lead = world.add(Entity(id="lead", kind="character", type=lead_type, label=lead_name, role="lead"))
    lead.attrs["display"] = lead_name
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, label="the grown-up", role="mentor"))
    hall = world.add(Entity(id="hall", kind="thing", type="hall", label=setting.place))
    for i in range(helpers):
        helper = world.add(
            Entity(
                id=f"helper{i+1}",
                kind="character",
                type=helper_types[i],
                label=helper_names[i],
                role="helper",
            )
        )
        helper.attrs["display"] = helper_names[i]

    lead.id = lead_name
    del world.entities["lead"]
    world.entities[lead_name] = lead
    mentor.id = "Mentor"
    del world.entities["mentor"]
    world.entities["Mentor"] = mentor

    hall.id = "Hall"
    del world.entities["hall"]
    world.entities["Hall"] = hall

    for i, helper in enumerate(list(world.helpers())):
        old = helper.id
        helper.id = helper_names[i]
        del world.entities[old]
        world.entities[helper_names[i]] = helper

    world.facts["lead_id"] = lead_name
    world.facts["mentor_id"] = "Mentor"
    world.facts["hall_id"] = "Hall"

    lead = world.get(lead_name)
    mentor = world.get("Mentor")
    hall = world.get("Hall")

    lead.memes["confidence"] = 0.0
    lead.memes["jitters"] = 0.0
    hall.meters["music"] = 0.0

    margin = support_score(method, helpers) - demand_score(rhyme, noise)
    world.facts.update(
        setting=setting,
        rhyme=rhyme,
        method=method,
        helpers=helpers,
        noise=noise,
        margin=margin,
        outcome="smooth" if margin >= 2 else "recovered",
        lead=lead,
        mentor=mentor,
        hall=hall,
    )

    introduce(world, lead, mentor)
    gather_helpers(world, lead)
    choose_rhyme(world, lead, rhyme)

    world.para()
    stir_jitters(world, lead, rhyme, noise)
    first_attempt(world, lead, rhyme)

    world.para()
    teamwork(world, lead, method)
    retry(world, lead, rhyme, method)
    ending(world, lead, mentor, rhyme)

    world.facts["helper_names"] = [h.id for h in world.helpers()]
    world.facts["wobbled"] = lead.meters["wobble"] >= THRESHOLD
    world.facts["music"] = hall.meters["music"] >= THRESHOLD
    return world


def display_name(ent: Entity) -> str:
    return str(ent.attrs.get("display") or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    rhyme = f["rhyme"]
    method = f["method"]
    setting = f["setting"]
    return [
        f'Write a short nursery-rhyme-style story that includes the words "phonetic" and "symphony" and takes place in {setting.place}.',
        f"Tell a child-facing story where {display_name(lead)} struggles with the opening sound {rhyme.sound!r} in a rhyme, and friends use teamwork with {method.label} to help.",
        f"Write a tiny musical story about a team turning a shaky start into a happy chorus, with a clear beginning, a wobble in the middle, and an ending image of everyone making music together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    mentor = f["mentor"]
    rhyme = f["rhyme"]
    method = f["method"]
    helper_names = f["helper_names"]
    who = ", ".join(helper_names[:-1]) + f", and {helper_names[-1]}" if len(helper_names) > 2 else (
        f"{helper_names[0]} and {helper_names[1]}" if len(helper_names) == 2 else helper_names[0]
    )
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {display_name(lead)}, a little singer in a nursery band, and the friends who stood nearby to help. {mentor.label_word.capitalize()} watched while the group tried to begin the rhyme together.",
        ),
        (
            "What was the problem at the start of the song?",
            f"The opening word of {rhyme.title} began with the sound {rhyme.sound!r}, and that phonetic start felt tricky when it was time to say it clearly. The lead singer's jitters made the first try wobble instead of ring out.",
        ),
        (
            f"How did the others help {display_name(lead)}?",
            f"{who} used {method.label} to support the first beats of the line. They worked as one team, which gave the lead singer something steady to lean on.",
        ),
    ]
    if f["outcome"] == "smooth":
        qa.append(
            (
                "How did the song go after the helpers joined in?",
                f"Once the beat and support were in place, the rhyme flowed smoothly from beginning to end. The teamwork was strong enough that the whole little symphony stayed together the first time they tried again.",
            )
        )
    else:
        qa.append(
            (
                "Did the lead singer get it right immediately?",
                f"No. The first start wobbled, but the group did not give up. Their teamwork changed the room from shaky to steady, and the second try carried the rhyme through.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the rhyme singing out clearly and the room sounding like one cheerful symphony. The final picture shows that sharing the work changed a frightened start into a joined-up song.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"phonetic", "symphony", "teamwork"} | set(f["method"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


def explain_rejection(rhyme: Rhyme, method: Method, helpers: int, noise: int) -> str:
    if not method_supports(rhyme, method):
        kinds = ", ".join(sorted(method.supports))
        return (
            f"(No story: {method.label} does not suit the {rhyme.sound!r} opening of {rhyme.title}. "
            f"It supports {kinds} sounds, but this rhyme needs help with a {rhyme.sound_kind} sound.)"
        )
    need = demand_score(rhyme, noise) + 1
    have = support_score(method, helpers)
    return (
        f"(No story: the teamwork is too weak for this recital. With noise={noise}, "
        f"{rhyme.title} needs support above {demand_score(rhyme, noise)}, so at least {need}; "
        f"this plan only gives {have}.)"
    )


ASP_RULES = r"""
supports_sound(M, R) :- method(M), rhyme(R), supports(M, K), sound_kind(R, K).
enough_support(R, M, H, N) :- rhyme(R), method(M), helper_count(H), noise(N),
                              difficulty(R, D), power(M, P), P + H > D + N.
valid_story(S, R, M, H, N) :- setting(S), rhyme(R), method(M), helper_count(H), noise(N),
                              supports_sound(M, R), enough_support(R, M, H, N).

margin(R, M, H, N, P + H - D - N) :- rhyme(R), method(M), helper_count(H), noise(N),
                                     power(M, P), difficulty(R, D).
outcome(smooth) :- chosen_rhyme(R), chosen_method(M), chosen_helpers(H), chosen_noise(N),
                   margin(R, M, H, N, X), X >= 2.
outcome(recovered) :- chosen_rhyme(R), chosen_method(M), chosen_helpers(H), chosen_noise(N),
                      margin(R, M, H, N, X), X = 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for rhyme_id, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rhyme_id))
        lines.append(asp.fact("sound_kind", rhyme_id, rhyme.sound_kind))
        lines.append(asp.fact("difficulty", rhyme_id, rhyme.difficulty))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("power", method_id, method.power))
        for kind in sorted(method.supports):
            lines.append(asp.fact("supports", method_id, kind))
    for helpers in [1, 2, 3]:
        lines.append(asp.fact("helper_count", helpers))
    for noise in [0, 1]:
        lines.append(asp.fact("noise", noise))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_rhyme", params.rhyme),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_helpers", params.helpers),
            asp.fact("chosen_noise", params.noise),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a nursery-rhyme recital where teamwork steadies a tricky opening sound."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helpers", type=int, choices=[1, 2, 3])
    ap.add_argument("--noise", type=int, choices=[0, 1], help="0=calm, 1=extra rustle")
    ap.add_argument("--lead")
    ap.add_argument("--lead-type", choices=LEAD_TYPES)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rhyme and args.method and args.helpers is not None and args.noise is not None:
        rhyme = RHYMES[args.rhyme]
        method = METHODS[args.method]
        if not is_reasonable(rhyme, method, args.helpers, args.noise):
            raise StoryError(explain_rejection(rhyme, method, args.helpers, args.noise))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.rhyme is None or combo[1] == args.rhyme)
        and (args.method is None or combo[2] == args.method)
        and (args.helpers is None or combo[3] == args.helpers)
        and (args.noise is None or combo[4] == args.noise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, rhyme_id, method_id, helpers, noise = rng.choice(sorted(combos))
    lead_type = args.lead_type or rng.choice(LEAD_TYPES)
    if lead_type == "girl":
        default_name = rng.choice(GIRL_NAMES)
    elif lead_type == "boy":
        default_name = rng.choice(BOY_NAMES)
    else:
        default_name = rng.choice(ANIMAL_NAMES)
    lead_name = args.lead or default_name
    mentor_type = args.mentor or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        rhyme=rhyme_id,
        method=method_id,
        helpers=helpers,
        noise=noise,
        lead_name=lead_name,
        lead_type=lead_type,
        mentor_type=mentor_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme: {params.rhyme})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helpers not in {1, 2, 3}:
        raise StoryError(f"(Invalid helper count: {params.helpers})")
    if params.noise not in {0, 1}:
        raise StoryError(f"(Invalid noise level: {params.noise})")

    rhyme = RHYMES[params.rhyme]
    method = METHODS[params.method]
    if not is_reasonable(rhyme, method, params.helpers, params.noise):
        raise StoryError(explain_rejection(rhyme, method, params.helpers, params.noise))

    rng = random.Random(params.seed if params.seed is not None else 0)
    helper_names = choose_helper_names(rng, params.lead_name, params.helpers)
    helper_types = [rng.choice(HELPER_TYPES) for _ in range(params.helpers)]

    world = tell(
        setting=SETTINGS[params.setting],
        rhyme=rhyme,
        method=method,
        helpers=params.helpers,
        noise=params.noise,
        lead_name=params.lead_name,
        lead_type=params.lead_type,
        mentor_type=params.mentor_type,
        helper_names=helper_names,
        helper_types=helper_types,
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


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = copy.deepcopy(CURATED[0])
        smoke.seed = 123
        sample = generate(smoke)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_story/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, rhyme, method, helpers, noise) combos:\n")
        for setting_id, rhyme_id, method_id, helpers, noise in combos:
            print(f"  {setting_id:11} {rhyme_id:8} {method_id:15} helpers={helpers} noise={noise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, params in enumerate(CURATED):
            cp = copy.deepcopy(params)
            cp.seed = base_seed + i
            samples.append(generate(cp))
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
            header = (
                f"### {p.lead_name}: {p.rhyme} in {p.setting} "
                f"({p.method}, helpers={p.helpers}, noise={p.noise}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
