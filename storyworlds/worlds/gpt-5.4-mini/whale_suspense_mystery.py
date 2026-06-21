#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whale_suspense_mystery.py
=========================================================

A standalone storyworld for a small mystery-suspense tale about a child,
a missing whale, and a careful search that turns scary sounds into a clear
ending.

The domain is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a frozen paragraph with swapped nouns
- a reasonableness gate in Python plus an inline ASP twin
- three Q&A sets grounded in the simulated world
- support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
SUSPENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    label: str
    sky: str
    water: str
    sounds: str
    detail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    reveal: str
    phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mystery:
    id: str
    label: str
    truth: str
    risk: int
    patience: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("search_started") and not world.facts.get("truth_revealed"):
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.characters():
                if e.role in {"child", "parent"}:
                    e.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_seen") and not world.facts.get("truth_revealed"):
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            if "sea" in world.entities:
                world.get("sea").meters["mystery"] += 1
            out.append("__clue__")
    return out


CAUSAL_RULES = [
    Rule("fear", "social", _r_fear),
    Rule("clue", "mystery", _r_clue),
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
        for s in produced:
            world.say(s)
    return produced


def reasonable_pair(setting: Setting, clue: Clue, mystery: Mystery) -> bool:
    return setting.id in {"harbor", "cliff"} and clue.kind in {"sound", "trace"} and mystery.risk >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SUSPENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def danger_level(mystery: Mystery, delay: int) -> int:
    return mystery.risk + delay


def is_resolved(response: Response, mystery: Mystery, delay: int) -> bool:
    return response.power >= danger_level(mystery, delay)


def predict(world: World, mystery_id: str) -> dict:
    sim = world.copy()
    _search(sim, sim.get(mystery_id), narrate=False)
    return {
        "fear": sum(e.memes["fear"] for e in sim.characters()),
        "mystery": sim.get("sea").meters["mystery"] if "sea" in sim.entities else 0,
    }


def _search(world: World, mystery_ent: Entity, narrate: bool = True) -> None:
    mystery_ent.meters["unseen"] += 1
    world.facts["search_started"] = True
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a gray afternoon, {child.id} and {parent.label_word} stood by {setting.label}. "
        f"{setting.sky} {setting.water} {setting.sounds}"
    )
    world.say(
        f"{child.id} liked the hush there, because every little splash seemed like it might hide a secret."
    )


def notice_missing(world: World, child: Entity, mystery: Mystery, setting: Setting) -> None:
    world.say(
        f"Then {child.id} noticed something strange: the water near the pier was too still."
        f" A small shape had vanished where {setting.detail}."
    )
    world.say(
        f'"Where did the {mystery.label} go?" {child.id} whispered.'
    )


def cue_search(world: World, parent: Entity, child: Entity, clue: Clue) -> None:
    world.say(
        f"{parent.label_word.capitalize()} pointed to a tiny {clue.label}. "
        f"{clue.phrase} {clue.reveal}"
    )
    world.facts["clue_seen"] = True
    world.facts["clue_kind"] = clue.kind
    propagate(world, narrate=False)


def worry(world: World, child: Entity, mystery: Mystery, parent: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id}'s throat felt tight. The {mystery.label} could be lost, or hurt, "
        f"and the fog made every guess feel bigger."
    )
    world.say(
        f'"Maybe we should call the harbor office," {parent.label_word} said calmly.'
    )


def search_and_find(world: World, child: Entity, parent: Entity, mystery: Mystery,
                    setting: Setting, response: Response, delay: int) -> None:
    world.para()
    world.say(
        f"They followed the clue along {setting.label}, listening for one more sound."
    )
    if delay > 0:
        world.say("For a little while, only the water moved, and the wait felt long.")
    world.facts["truth_revealed"] = True
    mystery_ent = world.get("mystery")
    mystery_ent.meters["seen"] += 1
    world.say(
        f"At last, a dark back rose from the water. It was the {mystery.label}, not gone at all."
    )
    if is_resolved(response, mystery, delay):
        body = response.text.replace("{target}", mystery.label)
        world.say(f"{parent.label_word.capitalize()} {body}.")
        world.say(
            f"The calm answer turned the scary search into relief, and the water went quiet again."
        )
    else:
        body = response.fail.replace("{target}", mystery.label)
        world.say(f"{parent.label_word.capitalize()} {body}.")
        world.say(
            f"They had to keep waiting, because the problem was bigger than one quick fix."
        )


def ending(world: World, child: Entity, parent: Entity, mystery: Mystery, response: Response,
           delay: int) -> None:
    if is_resolved(response, mystery, delay):
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        world.say(
            f"Then the {mystery.label} floated back beside the pier, safe and blinking in the foam."
        )
        world.say(
            f"{child.id} smiled at {parent.label_word}, because the mystery had become a known thing again."
        )
    else:
        child.memes["fear"] += 1
        world.say(
            f"Even so, the {mystery.label} was finally found, and they kept watch until help arrived."
        )
        world.say(
            f"{child.id} stayed close to {parent.label_word}, with the fog lifting a little at last."
        )


def tell(setting: Setting, clue: Clue, mystery: Mystery, response: Response,
         child_name: str = "Maya", child_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    sea = world.add(Entity(id="sea", type="water", label="the sea"))
    mystery_ent = world.add(Entity(id="mystery", type="mystery", label=mystery.label))

    opening(world, child, parent, setting)
    world.para()
    notice_missing(world, child, mystery, setting)
    cue_search(world, parent, child, clue)
    worry(world, child, mystery, parent)
    search_and_find(world, child, parent, mystery, response, delay)
    ending(world, child, parent, mystery, response, delay)

    world.facts.update(
        child=child,
        parent=parent,
        sea=sea,
        mystery=mystery_ent,
        setting=setting,
        clue=clue,
        mystery_cfg=mystery,
        response=response,
        delay=delay,
        resolved=is_resolved(response, mystery, delay),
    )
    return world


SETTINGS = {
    "harbor": Setting(
        "harbor",
        "the harbor",
        "A pale fog sat over the docks, and the ropes made soft creaking sounds.",
        "The tide slipped under the boards.",
        "Every buoy knocked gently in the swell.",
        "the little inlet between the boats",
        tags={"sea", "fog"},
    ),
    "cliff": Setting(
        "cliff",
        "the cliff path",
        "The wind tugged at the grass, and the waves sounded far below.",
        "The water flashed silver at the bottom.",
        "Somewhere below, the rocks answered with a low hush.",
        "the hidden cove below the path",
        tags={"sea", "fog"},
    ),
}

CLUES = {
    "whistle": Clue(
        "whistle",
        "whistle",
        "sound",
        "That meant the whale was close by.",
        "A thin whistle drifted up from the water.",
        tags={"sound", "whale"},
    ),
    "bubble": Clue(
        "bubble",
        "bubble trail",
        "trace",
        "The bubbles showed where the whale had passed.",
        "A trail of silver bubbles curled across the waves.",
        tags={"trace", "whale"},
    ),
    "tail": Clue(
        "tail",
        "tail splash",
        "trace",
        "The splash proved the whale had only turned around the bend.",
        "A quick tail splash flashed and vanished.",
        tags={"trace", "whale"},
    ),
}

MYSTERIES = {
    "whale": Mystery(
        "whale",
        "whale",
        "a curious hump and a careful tail broke the surface",
        risk=2,
        patience=2,
        tags={"whale", "sea"},
    ),
    "whale_calf": Mystery(
        "whale_calf",
        "whale calf",
        "a smaller back bobbed beside the bigger one",
        risk=1,
        patience=1,
        tags={"whale", "sea"},
    ),
    "whale_scout": Mystery(
        "whale_scout",
        "whale scout",
        "the whale was simply circling the harbor",
        risk=1,
        patience=2,
        tags={"whale", "sea"},
    ),
}

RESPONSES = {
    "radio": Response(
        "radio",
        sense=3,
        power=3,
        text="used the radio to call the harbor keeper, who sent a boat right away",
        fail="called on the radio, but nobody answered quickly enough",
        qa_text="used the radio to call the harbor keeper",
        tags={"help", "harbor"},
    ),
    "lantern": Response(
        "lantern",
        sense=3,
        power=2,
        text="held up a lantern so the crew could see the water line better",
        fail="held up a lantern, but the fog still hid the little trail",
        qa_text="held up a lantern",
        tags={"light", "fog"},
    ),
    "whistle_back": Response(
        "whistle_back",
        sense=2,
        power=2,
        text="whistled back softly, and the whale answered with a splash",
        fail="whistled back, but the sound only echoed into the fog",
        qa_text="whistled back softly",
        tags={"sound", "whale"},
    ),
    "shout": Response(
        "shout",
        sense=1,
        power=1,
        text="shouted too loudly, which only made the night feel more nervous",
        fail="shouted, but it didn't help at all",
        qa_text="shouted",
        tags={"noisy"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Iris"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Ben", "Owen", "Max", "Noah", "Eli"]
TRAITS = ["curious", "careful", "quiet", "brave", "patient"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    mystery: str
    response: str
    name: str
    gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for mid, mystery in MYSTERIES.items():
                if reasonable_pair(setting, clue, mystery):
                    combos.append((sid, cid, mid))
    return combos


def explain_rejection(setting: Setting, clue: Clue, mystery: Mystery) -> str:
    return (
        f"(No story: this combination doesn't fit the tiny mystery. "
        f"Try a harbor or cliff setting, a sound or trace clue, and the whale.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SUSPENSE_MIN}). Try: {better}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small whale mystery with suspense."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SUSPENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.setting and args.clue and args.mystery:
        if not reasonable_pair(SETTINGS[args.setting], CLUES[args.clue], MYSTERIES[args.mystery]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], CLUES[args.clue], MYSTERIES[args.mystery]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, mystery = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, clue, mystery, response, name, gender, parent, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        MYSTERIES[params.mystery],
        RESPONSES[params.response],
        params.name,
        params.gender,
        params.parent,
        params.trait,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    clue = f["clue"]
    mystery = f["mystery_cfg"]
    return [
        f'Write a suspenseful mystery story for a 3-to-5-year-old that includes the word "whale" and takes place at {setting.label}.',
        f"Tell a gentle mystery where {child.id} notices {clue.label} near the water and learns what happened to the {mystery.label}.",
        f"Write a child-friendly suspense story with a whale, a clue, and a calm ending where the mystery is solved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    setting = f["setting"]
    clue = f["clue"]
    mystery = f["mystery_cfg"]
    response = f["response"]
    delay = f["delay"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word}, who went to {setting.label} and noticed a mystery in the water."),
        ("What clue did they notice?",
         f"They noticed {clue.phrase}. {clue.reveal}"),
        ("Why did the scene feel suspenseful?",
         f"The water was quiet and the whale was missing for a moment, so {child.id} did not know what was happening. That uncertainty made the search feel tense until the clue made it clearer."),
    ]
    if f.get("resolved"):
        body = response.qa_text
        qa.append((
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {body}, which brought help to the water. That calm action was enough to solve the mystery after the waiting."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the whale safe beside the pier and the mystery solved. {child.id} could see that the scary moment was only a puzzling one, not a disaster."
        ))
    else:
        qa.append((
            f"What did {parent.label_word} try to do?",
            f"{parent.label_word.capitalize()} tried to use the radio and help, but the problem was still too slow to settle. They kept watch until the answer came into view."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery_cfg"].tags) | set(world.facts["clue"].tags) | set(world.facts["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


KNOWLEDGE = {
    "whale": [("What is a whale?",
               "A whale is a very big sea animal. It swims in the ocean and can make splashes and sounds." )],
    "sound": [("What is a clue you can hear?",
               "A clue you can hear is a sound that helps you figure something out, like a whistle or a splash.")],
    "trace": [("What is a trace?",
               "A trace is a small sign that something passed by, like bubbles or a trail in the water.")],
    "harbor": [("What is a harbor?",
                "A harbor is a safe place where boats stay close to land and the water is calmer.")],
    "fog": [("What is fog?",
             "Fog is a cloud near the ground. It can make it hard to see far away.")],
    "light": [("Why can a lantern help in fog?",
               "A lantern gives off light, so it can make dark shapes easier to see when the fog is thick.")],
    "help": [("What should you do if you need help finding something?",
              "You should tell a grown-up and ask for help. Working together makes the search safer and calmer.")],
}
KNOWLEDGE_ORDER = ["whale", "sound", "trace", "harbor", "fog", "light", "help"]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_possible(S, C, M) :- setting(S), clue(C), mystery(M), setting_ok(S), clue_ok(C), mystery_ok(M).

setting_ok(harbor).
setting_ok(cliff).

clue_ok(C) :- clue(C), clue_kind(C, sound).
clue_ok(C) :- clue(C), clue_kind(C, trace).

mystery_ok(M) :- mystery(M), risk(M, R), R >= 1.

resolved(R) :- response(R), sense(R, S), sense_min(M), S >= M.
danger(D) :- chosen_mystery(M), risk(M, R), delay(D), danger_level(RD), RD = R + D.
outcome(solved) :- resolved(R), danger(D), chosen_mystery(M), response_power(R, P), risk(M, X), P >= X + D.
outcome(still_unsure) :- chosen_mystery(_), not outcome(solved).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, c.kind))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("risk", mid, m.risk))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("response_power", rid, r.power))
    lines.append(asp.fact("sense_min", SUSPENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonably_possible/3."))
    return sorted(set(asp.atoms(model, "reasonably_possible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_mystery", params.mystery),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke test story is empty.")
    else:
        print("OK: smoke test generation produced a story.")
    if asp_outcome(CURATED[0]) == outcome_of(CURATED[0]):
        print("OK: ASP outcome matches Python outcome.")
    else:
        rc = 1
        print("MISMATCH: ASP outcome differs from Python outcome.")
    return rc


def outcome_of(params: StoryParams) -> str:
    return "solved" if is_resolved(RESPONSES[params.response], MYSTERIES[params.mystery], params.delay) else "unsure"


CURATED = [
    StoryParams("harbor", "whistle", "whale", "radio", "Maya", "girl", "mother", "curious", 0),
    StoryParams("harbor", "bubble", "whale_calf", "lantern", "Finn", "boy", "father", "careful", 1),
    StoryParams("cliff", "tail", "whale_scout", "whistle_back", "Nora", "girl", "father", "patient", 0),
]


def generate_world_from_params(params: StoryParams) -> World:
    return tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        MYSTERIES[params.mystery],
        RESPONSES[params.response],
        params.name,
        params.gender,
        params.parent,
        params.trait,
        params.delay,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world_from_params(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show reasonably_possible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, mystery) combos:\n")
        for s, c, m in combos:
            print(f"  {s:8} {c:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.setting}, {p.clue}, {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
