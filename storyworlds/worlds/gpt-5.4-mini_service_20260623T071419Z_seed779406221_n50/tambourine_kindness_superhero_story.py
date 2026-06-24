#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T071419Z_seed779406221_n50/tambourine_kindness_superhero_story.py
==============================================================================================================

A tiny superhero story world about a child hero, a noisy tambourine, and a kindness-based
solution. The premise is small and concrete: a city block has a noisy problem, the hero
wants to perform, a neighbor needs peace, and a gentle act of kindness turns the scene
into a bright ending.

This world uses typed entities with physical meters and emotional memes, a causal world
model, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    noise: float = 0.0
    mess: float = 0.0
    tags: set[str] = field(default_factory=set)


@dataclass
class SuperPower:
    id: str
    label: str
    method: str
    kindness: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    object: str
    power: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    seed: Optional[int] = None


SETTINGS = {
    "city_park": Setting(place="the city park", vibe="bright", affords={"concert", "parade"}),
    "rooftop": Setting(place="the rooftop garden", vibe="windy", affords={"concert"}),
    "block": Setting(place="the neighborhood block", vibe="busy", affords={"concert", "parade"}),
}

OBJECTS = {
    "tambourine": ObjectConfig(
        id="tambourine",
        label="tambourine",
        phrase="a shiny red tambourine",
        noise=3.0,
        tags={"tambourine", "music", "noise"},
    ),
    "megaphone": ObjectConfig(
        id="megaphone",
        label="megaphone",
        phrase="a bright megaphone",
        noise=4.0,
        tags={"megaphone", "noise"},
    ),
    "drum": ObjectConfig(
        id="drum",
        label="drum",
        phrase="a small drum",
        noise=2.0,
        tags={"drum", "music", "noise"},
    ),
}

POWERS = {
    "kindness": SuperPower(
        id="kindness",
        label="Kindness",
        method="share a calm plan and help everyone feel included",
        kindness=True,
        tags={"kindness", "help"},
    ),
    "listening": SuperPower(
        id="listening",
        label="Listening",
        method="listen closely and match the crowd's need",
        kindness=True,
        tags={"listening", "help"},
    ),
    "smile": SuperPower(
        id="smile",
        label="A warm smile",
        method="smile, pause, and invite a quieter song",
        kindness=True,
        tags={"smile", "help"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Zoe", "Nia", "Ruby", "Iris"]
BOY_NAMES = ["Leo", "Eli", "Noah", "Jude", "Theo", "Milo"]
TRAITS = ["brave", "kind", "cheerful", "quick", "curious"]


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    object_ = world.entities.get("object")
    if not hero or not object_:
        return out
    if object_.meters.get("noise", 0.0) < THRESHOLD:
        return out
    sig = ("noise", object_.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "neighbor" in world.entities:
        world.get("neighbor").memes["worry"] = world.get("neighbor").memes.get("worry", 0.0) + 1
    hero.memes["spark"] = hero.memes.get("spark", 0.0) + 1
    out.append("__noise__")
    return out


def _r_kindness(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return []
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return []
    sig = ("kindness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    return ["__kind__"]


CAUSAL_RULES = [Rule(name="noise", apply=_r_noise), Rule(name="kindness", apply=_r_kindness)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for object_id, obj in OBJECTS.items():
            for power_id, power in POWERS.items():
                if "concert" in setting.affords and obj.noise >= 2 and power.kindness:
                    combos.append((setting_id, object_id, power_id))
    return combos


def explain_rejection(setting_id: str, object_id: str) -> str:
    return f"(No story: {OBJECTS[object_id].label} isn't a good fit for {SETTINGS[setting_id].place}.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("noise", oid, int(o.noise)))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        if p.kindness:
            lines.append(asp.fact("kindness_power", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,P) :- setting(S), object(O), power(P), affords(S,concert), noise(O,N), N >= 2, kindness_power(P).
"""


@dataclass
class StoryParams:
    setting: str
    object: str
    power: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="city_park", object="tambourine", power="kindness", hero_name="Maya", hero_gender="girl", helper_name="Leo", helper_gender="boy", parent_name="Mom"),
    StoryParams(setting="rooftop", object="drum", power="listening", hero_name="Eli", hero_gender="boy", helper_name="Nia", helper_gender="girl", parent_name="Dad"),
    StoryParams(setting="block", object="megaphone", power="smile", hero_name="Zoe", hero_gender="girl", helper_name="Noah", helper_gender="boy", parent_name="Mom"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero kindness story world with a tambourine.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.power is None or c[2] == args.power)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, object_, power = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_name = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    parent = args.parent or rng.choice(["Mom", "Dad"])
    hero_gender = "girl" if hero_name in GIRL_NAMES else "boy"
    helper_gender = "girl" if helper_name in GIRL_NAMES else "boy"
    return StoryParams(setting=setting, object=object_, power=power, hero_name=hero_name, hero_gender=hero_gender, helper_name=helper_name, helper_gender=helper_gender, parent_name=parent)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, traits=["superhero", "kind"], meters={"speed": 1.0}, memes={"kindness": 1.0}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, traits=["helper"], meters={"calm": 0.0}, memes={"hope": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type="adult", label=params.parent_name, traits=["grown-up"], meters={}, memes={}))
    neighbor = world.add(Entity(id="neighbor", kind="character", type="adult", label="Ms. Green", traits=["neighbor"], meters={}, memes={"worry": 0.0}))
    obj_cfg = OBJECTS[params.object]
    obj = world.add(Entity(id="object", kind="thing", type=obj_cfg.label, label=obj_cfg.label, traits=["loud"], meters={"noise": obj_cfg.noise}, memes={}, tags=set(obj_cfg.tags)))
    hero.memes["kindness"] = 1.0
    world.say(f"{hero.label} was a little superhero who loved helping in {world.setting.place}.")
    world.say(f"{hero.label} carried {obj_cfg.phrase}, and the sound bounced between the trees and windows.")
    world.para()
    world.say(f"But {neighbor.label} covered her ears because the noise felt too big.")
    world.say(f"{hero.label} wanted to perform anyway, yet {hero.label} also had a hero heart.")
    propagate(world, narrate=False)
    world.para()
    if hero.memes.get("hope", 0.0) < THRESHOLD:
        hero.memes["kindness"] = 1.0
        helper.memes["calm"] = 1.0
    world.say(f"{helper.label} stepped beside {hero.label} and reminded {hero.pronoun()} that being kind could be a superpower.")
    world.say(f"So {hero.label} smiled, lowered {obj_cfg.label}, and used {POWERS[params.power].method}.")
    neighbor.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    world.para()
    world.say(f"{neighbor.label} smiled, the park felt peaceful again, and {parent.label} cheered for the gentle rescue.")
    world.say(f"In the end, {hero.label} still got to be a hero -- just a kinder, quieter one.")
    world.facts.update(hero=hero, helper=helper, parent=parent, neighbor=neighbor, object=obj, object_cfg=obj_cfg, power=POWERS[params.power], setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a superhero story for a young child about {world.facts["hero"].label}, kindness, and a {world.facts["object_cfg"].label}.',
        f"Tell a gentle superhero story where a noisy {world.facts['object_cfg'].label} is calmed by kindness.",
        "Write a child-facing story with a brave hero, a worried neighbor, and a kinder ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question=f"Who is the story about?", answer=f"It is about {f['hero'].label}, a little superhero who loves helping."),
        QAItem(question=f"What made the neighborhood feel too loud?", answer=f"{f['hero'].label} was playing a {f['object_cfg'].label}, and the sound felt very big."),
        QAItem(question=f"How did the hero fix the problem?", answer=f"{f['hero'].label} used kindness, listened, and chose a gentler plan."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is kindness?", answer="Kindness means being gentle, helpful, and caring about how other people feel."),
        QAItem(question="What is a tambourine?", answer="A tambourine is a music instrument you shake or tap so it makes a jingling sound."),
    ]


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        parts.append(f"  {e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(parts)


def format_qa(sample: StorySample) -> str:
    out = []
    for item in sample.story_qa:
        out.append(f"Q: {item.question}\nA: {item.answer}")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n\n".join(out)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.object not in OBJECTS or params.power not in POWERS:
        raise StoryError("invalid params")
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH")
        print("only python", sorted(py - asp_set))
        print("only asp", sorted(asp_set - py))
        return 1
    sample = generate(CURATED[0])
    if not sample.story:
        print("Story generation failed.")
        return 1
    print("OK: story generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
