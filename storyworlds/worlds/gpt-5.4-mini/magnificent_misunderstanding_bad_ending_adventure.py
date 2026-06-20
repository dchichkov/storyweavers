#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/magnificent_misunderstanding_bad_ending_adventure.py
====================================================================================

A standalone story world for a small adventure tale built around a
misunderstanding and a bad ending.

Domain:
- Two kids go on a tiny adventure to a hillfort, cave, lighthouse, or trail.
- One child finds a "magnificent" clue and assumes it means treasure or rescue.
- The other child misreads the clue or misses the warning.
- Their misunderstanding leads them deeper into trouble.
- A grown-up arrives too late to fully fix the situation, so the ending is sad
  or costly, but still concrete and complete.

This is intentionally a compact, classical simulation. State changes drive the
prose: distance, darkness, fear, loss, and damage accumulate into the ending.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FEAR_LIMIT = 2.0
DANGER_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str
    atmosphere: str
    path: str
    hidden: str
    hazard: str
    ending_image: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    phrase: str
    appears: str
    meaning: str
    misread_as: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


SETTINGS = {
    "lighthouse": Setting(
        "lighthouse",
        "the old lighthouse",
        "salt wind and white stone",
        "a spiral stair",
        "a bright lamp room",
        "slick steps and a loose latch",
        "the lighthouse stood with one window dark and one window shining",
        tags={"sea", "light", "adventure"},
    ),
    "cave": Setting(
        "cave",
        "the cliff cave",
        "cool shadows and echoing drops",
        "a narrow tunnel",
        "a hidden chamber",
        "a steep drop beyond a crumbly ledge",
        "the cave mouth yawned wide over the rocks",
        tags={"cave", "dark", "adventure"},
    ),
    "trail": Setting(
        "trail",
        "the forest trail",
        "pine needles and wind in the branches",
        "a twisting path",
        "an old stone arch",
        "a washout after the rain",
        "the trail vanished under tall ferns and roots",
        tags={"forest", "path", "adventure"},
    ),
    "ruins": Setting(
        "ruins",
        "the river ruins",
        "mossy blocks and whispering grass",
        "a broken bridge",
        "a carved doorway",
        "a collapsing wall",
        "the ruins leaned over the river like a giant old secret",
        tags={"ruins", "river", "adventure"},
    ),
}

CLUES = {
    "map": Clue(
        "map",
        "a magnificent map",
        "glittered on the floor",
        "showed the safe way home",
        "meant there must be treasure nearby",
        tags={"map", "paper", "adventure"},
    ),
    "beacon": Clue(
        "beacon",
        "a magnificent beacon lamp",
        "flickered from far away",
        "signaled danger and a helper's path",
        "meant a welcome from treasure hunters",
        tags={"light", "signal", "adventure"},
    ),
    "shell": Clue(
        "shell",
        "a magnificent shell",
        "glowed in the sand",
        "showed that the tide had moved fast",
        "meant the sea was giving a gift",
        tags={"sea", "object", "adventure"},
    ),
}

RESPONSES = {
    "call": Response(
        "call",
        3,
        4,
        "called for help right away and guided the children back along the safe path",
        "called, but the answer came too late to stop the trouble",
        "called for help and brought the children back to safety",
        tags={"help", "adult"},
    ),
    "rope": Response(
        "rope",
        3,
        2,
        "threw down a rope and tried to pull them back",
        "threw down a rope, but the wet ledge broke before it could help",
        "threw down a rope to pull them back",
        tags={"rope", "rescue"},
    ),
    "lantern": Response(
        "lantern",
        2,
        1,
        "held up a lantern and shouted the warning again",
        "held up a lantern, but the dark corner had already swallowed the warning",
        "held up a lantern and repeated the warning",
        tags={"light", "warning"},
    ),
}

GIRLS = ["Mia", "Lena", "Zoe", "Nora", "Ava", "June"]
BOYS = ["Eli", "Noah", "Theo", "Finn", "Sam", "Ben"]
TRAITS = ["brave", "curious", "careful", "bold", "restless"]
COMFORTS = ["small backpack", "toy compass", "blue scarf", "tiny whistle"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            if setting.id == "trail" and cid == "shell":
                continue
            for rid, resp in RESPONSES.items():
                if resp.sense >= 2:
                    combos.append((sid, cid, rid))
    return combos


def reason_for_rejection(setting: Setting, clue: Clue) -> str:
    return (
        f"(No story: {clue.phrase} does not fit {setting.place} in a way that can"
        f" plausibly mislead the children into the bad adventure beat.)"
    )


def reason_response(rid: str) -> str:
    resp = RESPONSES[rid]
    good = ", ".join(sorted(r.id for r in RESPONSES.values() if r.sense >= 2))
    return (
        f"(Refusing response '{rid}': it is too weak or too odd for this world "
        f"(sense={resp.sense}); try one of: {good}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world with a magnificent misunderstanding and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid_story(S,C,R) :- setting(S), clue(C), response(R), sensible(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRLS if gender == "girl" else BOYS
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(reason_response(args.response))
    if args.setting and args.clue:
        if args.setting == "trail" and args.clue == "shell":
            raise StoryError(reason_for_rejection(SETTINGS[args.setting], CLUES[args.clue]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, response = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    helper = args.helper or helper_gender.capitalize()
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, clue, response, hero, hero_gender, friend, friend_gender, helper, helper_gender, trait)


def predict_bad(world: World, clue: Clue) -> dict:
    sim = world.copy()
    _do_misunderstanding(sim, clue, narrate=False)
    return {"danger": sim.get("danger").meters["danger"], "lost": sim.get("path").meters["lost"]}


def _do_misunderstanding(world: World, clue: Clue, narrate: bool = True) -> None:
    world.get("hero").meters["misread"] += 1
    world.get("friend").meters["trust"].append if False else None  # no-op to keep pure stdlib, not used
    world.get("path").meters["danger"] += 1
    world.get("hero").memes["hope"] += 1
    if narrate:
        world.say(f"The clue seemed to promise something wonderful, so the children went farther in.")


def tell(setting: Setting, clue: Clue, response: Response,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         helper_gender: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label="the helper", role="helper"))
    path = world.add(Entity(id="path", type="path", label=setting.path))
    danger = world.add(Entity(id="danger", type="danger", label=setting.hazard))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.phrase))

    hero.memes["curiosity"] = 2.0
    friend.memes["trust"] = 1.0

    world.say(f"On a bright day, {hero_name} and {friend_name} went on an adventure to {setting.place}.")
    world.say(f"{setting.atmosphere.capitalize()} filled the air, and {setting.ending_image}.")

    world.para()
    world.say(f"Then they found {clue.phrase}, and it {clue.appears}.")
    world.say(f"{hero_name} thought it {clue.misread_as}, but {friend_name} did not understand the warning.")

    world.para()
    world.say(f"That misunderstanding sent them toward {setting.hidden} by {setting.path}.")
    world.get("path").meters["danger"] += 1
    world.get("danger").meters["danger"] += 1
    hero.memes["excitement"] += 1
    friend.memes["confusion"] += 1

    world.para()
    world.say(f"At last, {helper_gender} {response.text}.")
    if response.power < 2:
        world.say(f"But the problem was already too far gone for a quick fix.")
        world.get("danger").meters["danger"] += 2
    else:
        world.say(f"Still, the children were already trapped by the mistake they had made.")
        world.get("danger").meters["danger"] += 1

    world.para()
    if response.id == "call":
        world.say(
            f"The help came too late, and {setting.hazard} took the safe path away from them."
        )
    elif response.id == "rope":
        world.say(
            f"The rope held for a moment, then snapped against the wet stone."
        )
    else:
        world.say(
            f"The warning was bright, but it could not undo the choice they had already made."
        )
    world.say(
        f"In the end, {hero_name} and {friend_name} reached home with empty hands and heavy hearts."
    )
    world.say(
        f"The magnificent clue was still magnificent, but it had pointed them the wrong way."
    )

    world.facts.update(
        setting=setting,
        clue=clue,
        response=response,
        hero=hero,
        friend=friend,
        helper=helper,
        outcome="bad",
        clue_seen=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        RESPONSES[params.response],
        params.hero, params.hero_gender,
        params.friend, params.friend_gender,
        params.helper_gender,
        params.trait,
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
    return [
        f'Write an adventure story for a young child that includes the word "magnificent" and ends badly after a misunderstanding.',
        f"Tell a small adventure story where {f['hero'].label} and {f['friend'].label} misread a magnificent clue and get into trouble.",
        f'Write a story with a magnificent object, a wrong guess, and a sad ending in a cave-or-trail adventure tone.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    clue = f["clue"]
    setting = f["setting"]
    response = f["response"]
    return [
        ("What kind of story is this?",
         "It is an adventure story about children exploring a dangerous place and making a wrong guess. The mistake leads to a bad ending instead of a happy one."),
        ("What did the children find?",
         f"They found {clue.phrase}, and it seemed exciting and special. {clue.appears.capitalize()} made it look important, which helped cause the misunderstanding."),
        ("Why did the trip go wrong?",
         f"{hero.label} thought the clue meant one thing, but {friend.label} missed the warning and went along with it. That misunderstanding led them deeper into {setting.hidden}, where the danger was waiting."),
        ("How did the story end?",
         f"It ended badly: the helper arrived too late to fully fix the problem, and the children went home sad. The magnificent clue did not save them; it pointed them the wrong way."),
    ]


KNOWLEDGE = {
    "map": [("What is a map?",
             "A map is a drawing that shows places and paths. People use maps to find their way and avoid getting lost.")],
    "beacon": [("What is a beacon?",
                "A beacon is a signal that can help people find a place or know that help is nearby.")],
    "shell": [("What is a shell?",
               "A shell is the hard outer covering of some sea animals. People also pick up shells at the beach because they look pretty.")],
    "cave": [("Why can caves be dangerous?",
              "Caves can be dark, slippery, and easy to get lost in. A wrong step can lead to trouble fast.")],
    "lighthouse": [("What does a lighthouse do?",
                    "A lighthouse shines a bright light to help boats and people find their way near the shore.")],
    "trail": [("What is a trail?",
               "A trail is a path made for walking through a place like a forest or hill.")],
    "ruins": [("What are ruins?",
                "Ruins are old buildings that are broken or partly fallen down. They can be interesting, but they can also be unsafe.")],
    "adventure": [("What is an adventure?",
                   "An adventure is an exciting trip where people discover something new and may face danger or surprises.")],
}
KNOWLEDGE_ORDER = ["adventure", "map", "beacon", "shell", "cave", "lighthouse", "trail", "ruins"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["setting"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lighthouse", "map", "call", "Mia", "girl", "Eli", "boy", "mother", "careful"),
    StoryParams("cave", "beacon", "rope", "Theo", "boy", "Nora", "girl", "father", "brave"),
    StoryParams("ruins", "shell", "lantern", "Ava", "girl", "Ben", "boy", "mother", "curious"),
]


def valid_story_outcome(params: StoryParams) -> str:
    return "bad"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in RESPONSES.values() if r.sense >= 2}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test produced a non-empty story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def explain_rejection(setting: Setting, clue: Clue) -> str:
    return f"(No story: {clue.phrase} does not fit {setting.place} in a plausible adventure misunderstanding.)"


def explain_combo() -> str:
    return "(No valid combination matches the given options.)"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(reason_response(args.response))
    if args.setting and args.clue:
        if args.setting == "trail" and args.clue == "shell":
            raise StoryError(rejection_text(SETTINGS[args.setting], CLUES[args.clue]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError(explain_combo())
    setting, clue, response = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    helper = args.helper or helper_gender.capitalize()
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, clue, response, hero, hero_gender, friend, friend_gender, helper, helper_gender, trait)


def rejection_text(setting: Setting, clue: Clue) -> str:
    return reason_for_rejection(setting, clue)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for rid, resp in RESPONSES.items():
                if resp.sense >= 2:
                    combos.append((sid, cid, rid))
    return combos


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        RESPONSES[params.response],
        params.hero, params.hero_gender,
        params.friend, params.friend_gender,
        params.helper_gender,
        params.trait,
    )
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
        print(asp_program("", "#show valid_story/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, response) combos:\n")
        for s, c, r in combos:
            print(f"  {s:10} {c:8} {r}")
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
            header = f"### {p.hero} & {p.friend}: {p.clue} at {p.setting} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
