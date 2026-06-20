#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/certify_bad_ending_adventure.py
===============================================================

A standalone story world for a small adventure tale about a child explorer,
an uncertain route, and the word "certify". The story can end badly when the
main character ignores a warning and goes on before anything has been certified
safe.

The world is intentionally small: one explorer, one guide, one risky place, one
certificate/approval step, and one dangerous choice. The prose is driven by the
simulated world state, not by a frozen template with swapped names.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    broken: bool = False
    missing: bool = False

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
    place: str
    dark_spot: str
    journey: str
    ending_image: str

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
class Hazard:
    id: str
    label: str
    danger: str
    cause: str
    impact: str
    risky: bool = True
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
class Certification:
    id: str
    label: str
    action: str
    okay: str
    refused: str
    sense: int
    power: int
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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    bridge = world.entities.get("bridge")
    if not hero or not bridge:
        return out
    if hero.meters["crossed"] < THRESHOLD:
        return out
    if bridge.meters["stress"] < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bridge.broken = True
    hero.meters["danger"] += 1
    out.append("__damage__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if not hero.broken and not hero.missing:
        return out
    sig = ("loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sadness"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule("damage", "physical", _r_damage),
    Rule("loss", "emotional", _r_loss),
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


def danger_at_risk(hazard: Hazard, setting: Setting) -> bool:
    return hazard.risky and setting.id in {"canyon", "jungle", "mountain"}


def sensible_certifications() -> list[Certification]:
    return [c for c in CERTIFICATIONS.values() if c.sense >= SENSE_MIN]


def path_severity(hazard: Hazard, delay: int) -> int:
    return 1 + delay


def is_certified(cert: Certification, hazard: Hazard, delay: int) -> bool:
    return cert.power >= path_severity(hazard, delay)


def predict(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _take_path(sim, narrate=False)
    bridge = sim.get("bridge")
    hero = sim.get("hero")
    return {
        "broken": bridge.broken,
        "lost": hero.missing,
    }


def _take_path(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    bridge = world.get("bridge")
    hero.meters["crossed"] += 1
    bridge.meters["stress"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, guide: Entity, setting: Setting, hazard: Hazard) -> None:
    hero.memes["wonder"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} and {guide.id} reached {setting.place} on a bright adventure day. "
        f"{setting.journey}"
    )
    world.say(
        f"They could see {setting.dark_spot}, where the path narrowed and every step felt important."
    )
    world.say(
        f"{hero.id} wanted to explore it right away."
    )


def warn(world: World, guide: Entity, hero: Entity, hazard: Hazard, cert: Certification, delay: int) -> None:
    pred = predict(world, hazard.id)
    guide.memes["caution"] += 1
    world.facts["predicted_broken"] = pred["broken"]
    world.facts["delay"] = delay
    world.say(
        f'{guide.id} pointed at the path. "{hero.id}, we cannot go yet. '
        f'This place needs to be {cert.label} before anyone crosses. '
        f"If the bridge gives way, the whole adventure could turn sour."
    )


def insist(world: World, hero: Entity, cert: Certification) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I want to go now," {hero.id} said. "I can be careful." '
        f"{hero.pronoun().capitalize()} held the map tight and stepped toward the bridge."
    )


def certify_or_not(world: World, guide: Entity, cert: Certification, hazard: Hazard, delay: int) -> bool:
    if is_certified(cert, hazard, delay):
        world.say(
            f'{guide.id} checked the rope and nodded. "{cert.action}," {guide.id} said. '
            f"Only then did the path feel ready."
        )
        return True
    world.say(
        f'{guide.id} looked at the shaky ropes and frowned. "{cert.refused}," '
        f'{guide.id} said. "It is not safe enough yet."'
    )
    return False


def cross_badly(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.meters["crossed"] += 1
    world.say(
        f"{hero.id} went anyway. The boards shivered under {hero.pronoun('possessive')} feet, "
        f"and the wind tugged at the map."
    )
    _take_path(world)
    world.say(
        f"Then the bridge snapped with a sharp crack. {hazard.impact}."
    )


def ending_bad(world: World, hero: Entity, guide: Entity, setting: Setting) -> None:
    hero.missing = True
    hero.broken = True
    hero.memes["fear"] += 1
    guide.memes["fear"] += 1
    world.say(
        f"There was no heroic catch, no quick fix. {guide.id} shouted for help, "
        f"but the trail was empty and the storm was already rolling in."
    )
    world.say(
        f"By the time the sky grew dark, {hero.id}'s map was gone and the adventure had ended in tears."
    )
    world.say(
        f"Only {setting.ending_image} remained."
    )


def tell(setting: Setting, hazard: Hazard, cert: Certification,
         hero_name: str = "Mia", hero_gender: str = "girl",
         guide_name: str = "Nina", guide_gender: str = "girl",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="explorer"))
    guide = world.add(Entity(id="guide", kind="character", type=guide_gender, label=guide_name, role="guide"))
    bridge = world.add(Entity(id="bridge", type="thing", label="rope bridge"))
    world.facts.update(setting=setting, hazard=hazard, cert=cert, hero=hero, guide=guide, delay=delay)
    setup(world, hero, guide, setting, hazard)
    world.para()
    warn(world, guide, hero, hazard, cert, delay)
    insist(world, hero, cert)
    certify_or_not(world, guide, cert, hazard, delay)
    world.para()
    cross_badly(world, hero, hazard)
    ending_bad(world, hero, guide, setting)
    world.facts["outcome"] = "bad"
    return world


SETTINGS = {
    "canyon": Setting("canyon", "the red canyon", "the shadowed bridge", "The trail curled beside a deep drop.", "the broken bridge lay in splinters below"),
    "jungle": Setting("jungle", "the green jungle", "the muddy bridge", "The vines hung like curtains around the trail.", "only crushed leaves and a torn map were left"),
    "mountain": Setting("mountain", "the mountain pass", "the icy bridge", "The wind whistled between the rocks.", "the snow swallowed every footprint"),
}

HAZARDS = {
    "bridge": Hazard("bridge", "rope bridge", "a bridge that could snap", "heavy steps and wind", "the bridge could break", True, {"bridge", "danger"}),
    "trail": Hazard("trail", "narrow trail", "a trail that could crumble", "careless steps", "the path could collapse", True, {"trail", "danger"}),
}

CERTIFICATIONS = {
    "stamp": Certification("stamp", "certified safe", "The crossing was certified safe", "It is certified", "It cannot be certified yet", 3, 2, {"certify"}),
    "badge": Certification("badge", "certified safe", "The route was certified safe", "It is certified", "It is not certified yet", 2, 3, {"certify"}),
    "seal": Certification("seal", "certified safe", "The path was certified safe", "It is certified", "Not certified yet", 3, 1, {"certify"}),
}

HERO_NAMES = ["Mia", "Lia", "Nora", "Zoe", "Ava", "Ivy", "June", "Lena"]
GUIDE_NAMES = ["Nina", "Maya", "Rose", "Ella", "Tess", "Wren", "Ada"]
TRAITS = ["brave", "curious", "quick", "bold", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, hazard in HAZARDS.items():
            if not danger_at_risk(hazard, setting):
                continue
            for cid, cert in CERTIFICATIONS.items():
                if cert.sense >= SENSE_MIN:
                    combos.append((sid, hid, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    cert: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
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


KNOWLEDGE = {
    "certify": [("What does certify mean?", "To certify something means to say it is officially checked and safe. A certification is a clear approval, not just a guess.")],
    "bridge": [("What is a bridge for?", "A bridge helps people cross over water, rocks, or a gap. If it is weak, it can be dangerous.")],
    "canyon": [("What is a canyon?", "A canyon is a deep place with steep sides in the earth. Paths there can be tricky and unsafe.")],
    "jungle": [("What is a jungle like?", "A jungle is full of plants, vines, and hidden paths. It can feel exciting, but it can also be hard to see through.")],
    "mountain": [("Why can mountain paths be risky?", "Mountain paths can be windy, icy, or steep. One wrong step can be a big problem.")],
    "danger": [("Why should you listen to a warning on a dangerous path?", "Warnings help you avoid getting hurt. A careful pause can stop a small problem from becoming a big one.")],
}
KNOWLEDGE_ORDER = ["certify", "bridge", "canyon", "jungle", "mountain", "danger"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    cert = f["cert"]
    return [
        f'Write an adventure story for a small child that uses the word "{cert.id}" and ends badly because a risky path was not certified in time.',
        f"Tell a short adventure where {f['hero'].label} wants to cross at {setting.place} even though the guide says it must be {cert.label} first.",
        f"Write a tense exploration story with a bad ending, a warning, and the word certify somewhere in the middle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, setting, hazard, cert = f["hero"], f["guide"], f["setting"], f["hazard"], f["cert"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.label} and {guide.label}, two explorers on a dangerous adventure. They were trying to cross a risky place in {setting.place}."),
        ("What did the guide want to do before anyone crossed?",
         f"{guide.label} wanted the path to be {cert.label} before anyone went over it. That was the safe way to keep the adventure from turning into trouble."),
        ("Why did the guide warn the hero?",
         f"{guide.label} warned {hero.label} because {hazard.danger}. The guide could tell the crossing was not ready yet."),
        ("What did the hero do?",
         f"{hero.label} rushed ahead anyway and tried to cross before it was safe. That choice made the danger much worse."),
        ("How did the story end?",
         f"It ended badly. The bridge broke, the trail failed, and the adventure was left in a sad, unsafe mess."),
    ]
    if world.facts.get("outcome") == "bad":
        qa.append((
            "What proof shows it was a bad ending?",
            f"The bridge snapped and {hero.label} was left in danger. The last image was {setting.ending_image}, which shows the adventure did not end happily."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cert"].tags) | set(world.facts["hazard"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.broken:
            bits.append("broken=True")
        if e.missing:
            bits.append("missing=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
danger(Setting, Hazard) :- setting(Setting), hazard(Hazard), risky(Hazard).
sensible(C) :- cert(C), sense(C, S), sense_min(M), S >= M.
valid(Setting, Hazard, Cert) :- danger(Setting, Hazard), sensible(Cert).
outcome(bad) :- chosen(H), chosen_setting(S), danger(S, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.risky:
            lines.append(asp.fact("risky", hid))
    for cid, c in CERTIFICATIONS.items():
        lines.append(asp.fact("cert", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen", params.hazard),
        asp.fact("chosen_setting", params.setting),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    smoke = [CURATED[0]] if CURATED else []
    try:
        for p in smoke:
            generate(p)
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    for p in CURATED:
        if asp_outcome(p) != "bad":
            rc = 1
            print("MISMATCH: ASP outcome failed on curated case.")
            break
    else:
        print("OK: ASP outcome smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with certify and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--cert", choices=CERTIFICATIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting and args.hazard and (args.setting, args.hazard, args.cert or "stamp") not in combos:
        raise StoryError("No valid adventure fits those choices.")
    if args.cert and CERTIFICATIONS[args.cert].sense < SENSE_MIN:
        raise StoryError("That certification is too weak for this adventure.")
    filtered = [c for c in combos if (not args.setting or c[0] == args.setting)
                and (not args.hazard or c[1] == args.hazard)
                and (not args.cert or c[2] == args.cert)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, cert = rng.choice(sorted(filtered))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice([n for n in GUIDE_NAMES if n != hero])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, hazard, cert, hero, hero_gender, guide, guide_gender, delay)


CURATED = [
    StoryParams("canyon", "bridge", "stamp", "Mia", "girl", "Nina", "girl", 2),
    StoryParams("jungle", "bridge", "badge", "Ava", "girl", "Rose", "girl", 1),
    StoryParams("mountain", "bridge", "seal", "Lena", "girl", "Tess", "girl", 2),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        HAZARDS[params.hazard],
        CERTIFICATIONS[params.cert],
        params.hero,
        params.hero_gender,
        params.guide,
        params.guide_gender,
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
        print(f"{len(asp_valid_combos())} compatible adventure combos:")
        for t in asp_valid_combos():
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero} at {p.setting} ({p.hazard}, {p.cert})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
