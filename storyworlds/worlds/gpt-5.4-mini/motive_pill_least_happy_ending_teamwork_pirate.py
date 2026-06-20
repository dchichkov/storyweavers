#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/motive_pill_least_happy_ending_teamwork_pirate.py
==================================================================================

A tiny standalone storyworld for a pirate-tale style story with a happy ending
and teamwork. The seed words are woven into a small simulation: a pirate crew
has a motive to search for a hidden pill-shaped clue, but the least likely
helper proves the most useful when the team cooperates.

This world keeps the narrative simple, concrete, and state-driven:
- typed entities with meters and memes
- a small causal engine
- a reasonableness gate
- an inline ASP twin for parity checks
- three QA sets grounded in the simulated world
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class CrewConfig:
    id: str
    scene: str
    ship: str
    treasure: str
    dark_place: str
    end_image: str

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
class MotiveItem:
    id: str
    label: str
    phrase: str
    hidden: str
    value: str
    clue: bool = True

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
class HelperTool:
    id: str
    label: str
    helps_with: str
    text: str
    plural: bool = False

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    captain = world.entities.get("captain")
    helper = world.entities.get("least")
    clue = world.entities.get("pill")
    if not captain or not helper or not clue:
        return out
    if captain.memes["hope"] < THRESHOLD or helper.memes["trust"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    captain.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    clue.meters["found"] += 1
    out.append("__teamwork__")
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("pill")
    if not clue or clue.meters["found"] < THRESHOLD:
        return out
    sig = ("happy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ship").memes["joy"] += 1
    world.get("crew").memes["joy"] += 1
    out.append("__happy__")
    return out


CAUSAL_RULES = [Rule("teamwork", "social", _r_teamwork), Rule("happy", "social", _r_happy)]


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


def reasonableness_gate(cfg: CrewConfig, clue: MotiveItem, helper: HelperTool) -> bool:
    return cfg.id in CREWS and clue.clue and helper.helps_with == clue.id


def valid_combos() -> list[tuple[str, str, str]]:
    return [(cid, mid, hid) for cid in CREWS for mid in MOTIVES for hid in HELPERS
            if reasonableness_gate(CREWS[cid], MOTIVES[mid], HELPERS[hid])]


def _smoke_text(kind: str) -> str:
    return {
        "trail": "The crew found the clue in a twist of sand and sea air.",
        "reef": "The crew found the clue tucked behind the reef stones.",
        "cove": "The crew found the clue in a quiet cove under the moon.",
    }[kind]


def tell(cfg: CrewConfig, clue: MotiveItem, helper: HelperTool, hero: str = "Pip",
         hero_gender: str = "boy", least: str = "Mara", least_gender: str = "girl") -> World:
    world = World()
    captain = world.add(Entity(id=hero, kind="character", type=hero_gender, role="captain"))
    helper_ent = world.add(Entity(id=least, kind="character", type=least_gender, role="helper",
                                  traits=["least"]))
    crew = world.add(Entity(id="crew", kind="group", type="crew", label="the crew"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    pill = world.add(Entity(id="pill", kind="thing", type="clue", label=clue.label))

    captain.memes["motive"] = 1.0
    captain.memes["hope"] = 1.0
    helper_ent.memes["trust"] = 1.0

    world.say(
        f"On a bright pirate morning, {hero} and {least} sailed on {cfg.ship}. "
        f"{cfg.scene}"
    )
    world.say(
        f"{hero} had a motive to search for {clue.phrase}. The crew thought it "
        f"might hide near {cfg.dark_place}."
    )
    world.para()
    world.say(
        f"{least} was the least likely helper on the ship, but {least} noticed "
        f"the smallest signs first and pointed to the right place."
    )
    world.say(
        f'"Let us work together," said {hero}, and the whole crew moved as one.'
    )
    captain.memes["hope"] += 1
    helper_ent.memes["trust"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"They searched the shadows, checked the ropes, and followed the tiny clue "
        f"until {cfg.dark_place} gave up its secret."
    )
    world.say(
        f"{least} reached in first, and {hero} steadied the lantern. Together they "
        f"lifted {clue.label} out of hiding."
    )
    world.say(
        f"It was only a pill-shaped clue, but it led them straight to {cfg.treasure}."
    )
    world.para()
    world.say(
        f"In the end, {cfg.end_image}. The crew laughed, the ship felt warm with joy, "
        f"and the least likely helper had become the most important one."
    )

    world.facts.update(cfg=cfg, clue=clue, helper=helper, hero=captain, least=helper_ent,
                       crew=crew, ship=ship, outcome="happy", found=True)
    return world


CREWS = {
    "gull": CrewConfig("gull", "The sails snapped in the wind.", "the Sea Gull", "a chest of gold",
                       "the reef cave", "their flags fluttered above a bright, safe deck"),
    "maroon": CrewConfig("maroon", "The deck shone after the rain.", "the Red Maroon", "pearls in a shell",
                         "the captain's dark cabin", "their bowls of stew steamed beside a smiling map"),
}

MOTIVES = {
    "map": MotiveItem("map", "the pill-shaped compass bead", "a pill-shaped compass bead",
                      "under a loose plank", "guidance"),
    "gold": MotiveItem("gold", "the pill-shaped gold charm", "a pill-shaped gold charm",
                       "behind a rope knot", "treasure"),
    "song": MotiveItem("song", "the pill-shaped song token", "a pill-shaped song token",
                       "inside an old bottle", "music"),
}

HELPERS = {
    "least": HelperTool("least", "the least likely helper", "map",
                        "knew how to read tiny marks in the dark"),
    "small": HelperTool("small", "the smallest lookout", "gold",
                        "could slip through the narrow space"),
    "quiet": HelperTool("quiet", "the quiet cabin mate", "song",
                        "could hear the soft click of hidden things"),
}

GIRL_NAMES = ["Mara", "Nia", "Luna", "Ivy", "Rose"]
BOY_NAMES = ["Pip", "Finn", "Toby", "Eli", "Noah"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a small child that includes the words "motive", "pill", and "least".',
        f"Tell a teamwork story where {f['hero'].id} has a motive, {f['least'].id} is the least likely helper, and a pill-shaped clue leads to treasure.",
        f"Write a happy ending pirate story where the crew works together to find a hidden pill-shaped clue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    least = f["least"]
    clue = f["clue"]
    cfg = f["cfg"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {least.id}, who sailed with a pirate crew and worked together."),
        ("Why did the crew search the ship?",
         f"{hero.id} had a motive to find {clue.phrase}. The clue could lead them to {cfg.treasure}."),
        ("How did the crew solve the problem?",
         f"{least.id} noticed the smallest signs first, and {hero.id} steadied the lantern. Together they found {clue.label} and the crew stayed calm."),
        ("How did the story end?",
         f"It ended happily, with the crew finding {cfg.treasure} and celebrating on the ship."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a motive?",
         "A motive is the reason a character wants to do something. It is the why behind a choice."),
        ("What is teamwork?",
         "Teamwork means people help each other and do a job together. It often makes hard tasks easier."),
        ("What is a pill-shaped clue?",
         "It is a small clue that is round and smooth like a pill. In this story it helps lead the crew to treasure."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combo does not form a sensible pirate clue search.)"


ASP_RULES = r"""
valid(C, M, H) :- crew(C), motive(M), helper(H), clue(M), helps(H, M).
teamwork :- chosen_hero(_), chosen_least(_), chosen_clue(_).
happy :- teamwork.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CREWS:
        lines.append(asp.fact("crew", cid))
    for mid in MOTIVES:
        lines.append(asp.fact("motive", mid))
        lines.append(asp.fact("clue", mid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helps", hid, h.helps_with))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            crew=None, clue=None, helper=None, hero=None, hero_gender=None,
            least=None, least_gender=None, seed=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    print("OK: verify passed.")
    return rc


@dataclass
@dataclass
class StoryParams:
    crew: str
    clue: str
    helper: str
    hero: str
    hero_gender: str
    least: str
    least_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate teamwork storyworld.")
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--clue", choices=MOTIVES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--least")
    ap.add_argument("--least-gender", choices=["boy", "girl"])
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
    if args.crew and args.clue and args.helper:
        if not reasonableness_gate(CREWS[args.crew], MOTIVES[args.clue], HELPERS[args.helper]):
            raise StoryError(explain_rejection())
    crew = args.crew or rng.choice(sorted(CREWS))
    clue = args.clue or rng.choice(sorted(MOTIVES))
    helper = args.helper or "least"
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    least_gender = args.least_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or (rng.choice(BOY_NAMES) if hero_gender == "boy" else rng.choice(GIRL_NAMES))
    least = args.least or (rng.choice(GIRL_NAMES) if least_gender == "girl" else rng.choice(BOY_NAMES))
    if least == hero:
        least = "Mara" if hero != "Mara" else "Pip"
    return StoryParams(crew, clue, helper, hero, hero_gender, least, least_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(CREWS[params.crew], MOTIVES[params.clue], HELPERS[params.helper],
                 hero=params.hero, hero_gender=params.hero_gender,
                 least=params.least, least_gender=params.least_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("gull", "map", "least", "Pip", "boy", "Mara", "girl"),
            StoryParams("maroon", "gold", "small", "Mia", "girl", "Eli", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
