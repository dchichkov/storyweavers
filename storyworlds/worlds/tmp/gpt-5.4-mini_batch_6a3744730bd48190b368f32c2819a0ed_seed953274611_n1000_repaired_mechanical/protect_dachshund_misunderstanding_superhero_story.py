#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/protect_dachshund_misunderstanding_superhero_story.py
====================================================================================

A small storyworld about a superhero-style misunderstanding: a child thinks a
dachshund is in danger, rushes to protect it, and the mix-up turns into a gentle
rescue and a warm ending.

The story is intentionally constrained and state-driven. Emotional and physical
state both change the prose, and the ending proves what changed.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "dachshund":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    vibe: str
    dark_spot: str
    route: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class HeroConfig:
    id: str
    title: str
    costume: str
    call: str
    move: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Misunderstanding:
    id: str
    clue: str
    mistaken_threat: str
    actual_issue: str
    safety_fix: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Helper:
    id: str
    label: str
    comfort: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    misunderstanding: str
    response: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("dog").meters["safe"] >= THRESHOLD and world.get("hero").memes["fear"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["relief"] += 1
            world.get("dog").memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [_r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                out.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "alley": Setting(
        id="alley",
        place="a narrow city alley",
        vibe="the alley was full of shadows and fluttering wrappers",
        dark_spot="the dark space behind a trash bin",
        route="between two brick walls",
        tags={"city", "shadow"},
    ),
    "rooftop": Setting(
        id="rooftop",
        place="a bright rooftop garden",
        vibe="the rooftop hummed with wind and distant sirens",
        dark_spot="the space behind a blue water tank",
        route="beside a skylight",
        tags={"roof", "wind"},
    ),
    "park": Setting(
        id="park",
        place="a city park at dusk",
        vibe="the park had long grass, benches, and a glowing fountain",
        dark_spot="the path under a big oak tree",
        route="near the fountain",
        tags={"park", "dusk"},
    ),
}

HEROES = {
    "spark": HeroConfig(
        id="spark",
        title="Captain Spark",
        costume="a red cape with a silver star",
        call="Shield Up!",
        move="shot across the pavement",
        tags={"hero", "cape"},
    ),
    "glow": HeroConfig(
        id="glow",
        title="Glow Kid",
        costume="a blue mask and shiny boots",
        call="Bright and brave!",
        move="dashed forward",
        tags={"hero", "mask"},
    ),
}

MISUNDERSTANDINGS = {
    "shadow": Misunderstanding(
        id="shadow",
        clue="a moving shadow with little legs",
        mistaken_threat="a sneaky monster",
        actual_issue="the dachshund was stuck under a crate",
        safety_fix="slid the crate aside and called softly",
        reveal="the shadow belonged to a dachshund in a striped sweater",
        tags={"misunderstanding", "shadow"},
    ),
    "leash": Misunderstanding(
        id="leash",
        clue="a loose leash dragging like a ribbon",
        mistaken_threat="a villain's trap",
        actual_issue="the dachshund had tangled its leash on a bike stand",
        safety_fix="unlooped the leash and checked the little paws",
        reveal="the leash belonged to a very small dachshund with bright eyes",
        tags={"misunderstanding", "leash"},
    ),
}

HELPERS = {
    "owner": Helper(
        id="owner",
        label="the dog's owner",
        comfort="a tiny blanket",
        tags={"owner", "dog"},
    ),
    "neighbor": Helper(
        id="neighbor",
        label="a friendly neighbor",
        comfort="a treat pouch",
        tags={"neighbor", "dog"},
    ),
}

RESPONSES = {
    "careful": Response(
        id="careful",
        sense=3,
        power=3,
        text="took a slow breath, knelt down, and helped {target} calmly",
        fail="called too fast and only made the dog wobble more",
        qa_text="took a slow breath, knelt down, and helped {target} calmly",
        tags={"careful"},
    ),
    "blanket": Response(
        id="blanket",
        sense=3,
        power=2,
        text="wrapped a soft blanket around {target} and kept the little dog steady",
        fail="wrapped the blanket the wrong way and confused everyone",
        qa_text="wrapped a soft blanket around {target} and kept the little dog steady",
        tags={"blanket"},
    ),
    "whistle": Response(
        id="whistle",
        sense=1,
        power=1,
        text="blew a loud whistle and pointed dramatically",
        fail="blew a loud whistle, which scared the dachshund even more",
        qa_text="blew a loud whistle and pointed dramatically",
        tags={"whistle"},
    ),
}


GIRL_NAMES = ["Maya", "Nina", "Luna", "Ivy", "Zoe", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Jasper", "Leo", "Owen", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid in HEROES:
            for mid in MISUNDERSTANDINGS:
                combos.append((sid, hid, mid))
    return combos


def parse_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(setting: Setting, hero_cfg: HeroConfig, mis: Misunderstanding,
         response: Response, helper: Helper, hero_name: str, helper_name: str,
         hero_gender: str, helper_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender,
                            label=hero_cfg.title, role="hero",
                            traits=["brave", "quick"], attrs={"costume": hero_cfg.costume}))
    helper_ent = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                                  label=helper.label, role="helper",
                                  traits=["gentle", "careful"], attrs={"comfort": helper.comfort}))
    dog = world.add(Entity(id="dog", kind="character", type="dachshund",
                           label="the dachshund", role="focus",
                           traits=["small", "wiggly"]))
    world.facts.update(setting=setting, hero=hero, helper=helper_ent, dog=dog,
                       hero_cfg=hero_cfg, mis=mis, response=response)
    hero.memes["heroic"] = 1
    dog.meters["visible"] = 1
    world.say(
        f"At {setting.place}, {hero.id} was {hero_cfg.title}, wearing {hero_cfg.costume}. "
        f"{setting.vibe}."
    )
    world.say(
        f'{hero.id} heard a strange rustle near {setting.dark_spot}. "{hero_cfg.call}" '
        f"{hero.id} cried, ready to protect {dog.label} from trouble."
    )
    world.para()
    world.say(
        f"But the clue was only {mis.clue}. {hero.id} thought it meant {mis.mistaken_threat}, "
        f"so {hero.pronoun()} rushed in on {hero_cfg.move}."
    )
    world.say(
        f"Then {helper_ent.id} pointed and said, \"Wait -- {mis.reveal}!\" "
        f"It was just {mis.actual_issue}."
    )
    hero.memes["fear"] += 1
    if response.sense < 2:
        raise StoryError(f"(Refusing response '{response.id}': it is too loud for a calm rescue.)")
    world.para()
    dog.meters["safe"] = 1
    world.say(
        f"{helper_ent.id} and {hero.id} worked together. {hero.id} {response.text.format(target='the dachshund')} "
        f"while {helper_ent.id} {mis.safety_fix}."
    )
    propagate(world, narrate=False)
    world.say(
        f"In the end, {dog.label} was safe, and the little dog wagged its tail beside "
        f"{helper_ent.id}'s {helper.comfort}."
    )
    world.say(
        f"{hero.id} smiled under {hero.pronoun('possessive')} mask. \"I thought I was fighting a villain,\" "
        f"{hero.id} said, \"but I was protecting a dachshund.\""
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story for a young child that includes the words protect and dachshund.",
        f"Tell a story where {f['hero'].id} thinks the dachshund is in danger, but the hero discovers a misunderstanding and helps gently.",
        f"Write a brave-but-kind superhero tale in which a child tries to protect a dachshund, then learns what is really happening.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    dog = f["dog"]
    mis = f["mis"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a superhero-style kid, {helper.id}, and a dachshund. The story starts with a misunderstanding, so the hero rushes in before knowing the full truth."),
        ("What did the hero think was happening?",
         f"{hero.id} thought {mis.mistaken_threat} was happening. That is why {hero.pronoun()} tried to protect the dachshund so quickly."),
        ("What was really going on?",
         f"The clue was only {mis.clue}, and the real problem was that {mis.actual_issue}. Once that was clear, everyone could help the little dog safely."),
        ("How did they fix the problem?",
         f"{helper.id} spoke up, and {hero.id} {resp.qa_text.format(target='the dachshund')}. Then {helper.id} {mis.safety_fix}, which was the calm and sensible thing to do."),
        ("How did the story end?",
         f"It ended with the dachshund safe and wagging its tail. {hero.id} learned that a brave hero should stop, look, and listen before rushing in."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dachshund?",
         "A dachshund is a small dog with a long body and short legs. It can look funny and brave at the same time."),
        ("What does protect mean?",
         "Protect means to keep someone safe from harm or danger. A hero who protects helps first and asks questions too."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone thinks one thing is true, but the real situation is different. It can be fixed by looking again and listening."),
        ("Why do superheroes listen carefully?",
         "Superheroes listen carefully so they do not make the problem worse. Listening helps them help the right way."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_cfg(H).
helper(X) :- helper_cfg(X).
misunderstanding(M) :- misunderstanding_cfg(M).
valid(Hero, Helper, Mis) :- hero_cfg(Hero), helper_cfg(Helper), misunderstanding_cfg(Mis).

happens(Protect) :- misunderstanding(M), clue(M, _), actual_issue(M, _).
safe_end :- dog_safe, misunderstanding(M), reveal(M, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HEROES:
        lines.append(asp.fact("hero_cfg", hid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding_cfg", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper_cfg", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP vs Python valid_combos()")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about a dachshund misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(f"(Refusing response '{args.response}': too loud for this calm rescue.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hero is None or c[1] == args.hero)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hero, mis = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    response = args.response or rng.choice([r for r, v in RESPONSES.items() if v.sense >= 2])
    return StoryParams(setting=setting, hero=hero, helper=helper, misunderstanding=mis, response=response)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hero not in HEROES or params.helper not in HELPERS or params.misunderstanding not in MISUNDERSTANDINGS or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    rng = random.Random(params.seed or 0)
    hero_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    hero_gender = rng.choice(["girl", "boy"])
    helper_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    helper_gender = rng.choice(["girl", "boy"])
    world = tell(
        SETTINGS[params.setting],
        HEROES[params.hero],
        MISUNDERSTANDINGS[params.misunderstanding],
        RESPONSES[params.response],
        HELPERS[params.helper],
        hero_name,
        helper_name,
        hero_gender,
        helper_gender,
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


CURATED = [
    StoryParams(setting="alley", hero="spark", helper="owner", misunderstanding="shadow", response="careful"),
    StoryParams(setting="park", hero="glow", helper="neighbor", misunderstanding="leash", response="blanket"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
