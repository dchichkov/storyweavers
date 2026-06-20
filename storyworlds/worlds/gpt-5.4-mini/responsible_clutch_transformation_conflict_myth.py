#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/responsible_clutch_transformation_conflict_myth.py
===================================================================================

A tiny mythic storyworld about a child, a clutch of eggs, a responsible choice,
and a transformation caused by conflict and care.

Premise
-------
A young helper tends a clutch that is guarded by an old mythic creature.
A conflict threatens the clutch, but a responsible act leads to a transformation:
the creature changes, the mood changes, and the ending image proves the world
has become calmer and wiser.

This script is standalone and follows the Storyweavers storyworld contract.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CONFLICT_RISE = 1.0


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
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    sky: str
    ancient_detail: str

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
class Clutch:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    fertile: bool = True

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
class Creature:
    id: str
    label: str
    title: str
    form: str
    transformed_form: str
    change_phrase: str

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
class Trouble:
    id: str
    label: str
    pressure: str
    risk: str
    severity: int
    kind: str = "conflict"

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
@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    clutch: str
    creature: str
    trouble: str
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


SETTINGS = {
    "mountain": Setting("mountain", "the mountain shrine", "silver", "a ring of old stones"),
    "island": Setting("island", "the sea cave", "blue", "salt-smooth shells on the floor"),
    "forest": Setting("forest", "the hollow oak grove", "green", "roots braided like old hands"),
}

CLUTCHES = {
    "eggs": Clutch("eggs", "a clutch of eggs", "the clutch of pale eggs"),
    "shells": Clutch("shells", "a clutch of river shells", "the clutch of bright shells"),
}

CREATURES = {
    "dragon": Creature("dragon", "the dragon", "old dragon", "dragon", "young starling", "its scales softened into feathers"),
    "serpent": Creature("serpent", "the serpent", "river serpent", "serpent", "white heron", "its long body became wings"),
    "stag": Creature("stag", "the stag-spirit", "woodland stag-spirit", "stag-spirit", "golden deer", "its antlers blossomed into leaves"),
}

TROUBLES = {
    "storm": Trouble("storm", "the storm", "the wind pressed hard", "the clutch might scatter", 2),
    "hunters": Trouble("hunters", "hunters", "boots came too near", "the clutch might be taken", 1),
    "flood": Trouble("flood", "the rising water", "water lapped at the stones", "the clutch might drown", 3),
}

NAMES = ["Mira", "Evan", "Luna", "Ari", "Niko", "Tala", "Soren", "Iris"]
BOY_NAMES = ["Evan", "Ari", "Niko", "Soren"]
GIRL_NAMES = ["Mira", "Luna", "Tala", "Iris"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUTCHES:
            for t in TROUBLES:
                combos.append((s, c, t))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.clutch not in CLUTCHES:
        raise StoryError("Unknown clutch.")
    if params.creature not in CREATURES:
        raise StoryError("Unknown creature.")
    if params.trouble not in TROUBLES:
        raise StoryError("Unknown trouble.")


def is_conflict(trouble: Trouble) -> bool:
    return trouble.kind == "conflict"


def transformation_possible(creature: Creature, clutch: Clutch, trouble: Trouble) -> bool:
    return clutch.fertile and trouble.severity >= 1


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUTCHES:
        lines.append(asp.fact("clutch", cid))
    for rid in CREATURES:
        lines.append(asp.fact("creature", rid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("severity", tid, t.severity))
    return "\n".join(lines)


ASP_RULES = r"""
conflict(T) :- trouble(T), severity(T, S), S >= 1.
transformation(C) :- creature(C), clutch(_), conflict(_).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show transformation/1."))
    asp_conflicts = {a[0] for a in asp.atoms(model, "conflict")}
    asp_transform = {a[0] for a in asp.atoms(model, "transformation")}
    py_conflicts = {t for t in TROUBLES if is_conflict(TROUBLES[t])}
    py_transform = set(CREATURES) if py_conflicts else set()
    rc = 0
    if asp_conflicts == py_conflicts:
        print(f"OK: ASP conflict parity ({len(asp_conflicts)}).")
    else:
        print("MISMATCH: conflict parity failed.")
        rc = 1
    if asp_transform == py_transform:
        print(f"OK: ASP transformation parity ({len(asp_transform)}).")
    else:
        print("MISMATCH: transformation parity failed.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about responsibility and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clutch", choices=CLUTCHES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clutch = args.clutch or rng.choice(list(CLUTCHES))
    creature = args.creature or rng.choice(list(CREATURES))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    if args.setting and args.clutch and args.trouble:
        pass
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    reasonableness_check(StoryParams(setting, name, gender, clutch, creature, trouble))
    return StoryParams(setting, name, gender, clutch, creature, trouble)


def _story_setup(world: World, hero: Entity, clutch: Clutch, creature: Creature) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, {hero.id} found {clutch.phrase} beneath "
        f"{world.setting.ancient_detail}. The air was quiet, and the old place held its breath."
    )
    world.say(
        f"Near the stones waited {creature.title}, watching the clutch with patient eyes."
    )


def _conflict_beat(world: World, hero: Entity, trouble: Trouble) -> None:
    world.para()
    world.say(
        f"Then {trouble.label} came: {trouble.pressure}, and {trouble.risk}. "
        f"{hero.id} felt the pull of fear, but {hero.pronoun('possessive')} heart stayed steady."
    )
    hero.memes["responsibility"] += 1
    hero.memes["courage"] += 1
    hero.memes["clutch"] += 1


def _transform(world: World, hero: Entity, creature: Creature, clutch: Clutch, trouble: Trouble) -> None:
    creature_ent = world.get("creature")
    clutch_ent = world.get("clutch")
    world.para()
    creature_ent.attrs["form"] = creature.transformed_form
    creature_ent.meters["transformed"] += 1
    world.say(
        f"{hero.id} did the responsible thing. {hero.pronoun().capitalize()} sheltered "
        f"{clutch_ent.label_word if hasattr(clutch_ent, 'label_word') else clutch.label} with "
        f"{hero.pronoun('possessive')} own cloak and called out to the creature instead of fleeing."
    )
    world.say(
        f"At once, the old {creature.form} changed; {creature.change_phrase}. "
        f"{creature.label.capitalize()} was no longer only a guardian of old law, but something gentler."
    )
    world.say(
        f"The conflict eased. The wind still moved, yet it could not steal the clutch now."
    )


def _ending(world: World, hero: Entity, creature: Creature, clutch: Clutch) -> None:
    world.para()
    world.say(
        f"In the end, {hero.id} stood beside the shrine, and the new {creature.transformed_form} "
        f"kept watch over {clutch.label}. The stars shone on the stones like bright promise."
    )
    world.say(
        f"From that night on, people said {hero.id} was responsible, because {hero.pronoun()} "
        f"had guarded what was fragile and helped the old power transform."
    )


def tell(setting: Setting, clutch: Clutch, creature: Creature, trouble: Trouble,
         hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["responsible"]))
    world.add(Entity(id="clutch", type="thing", label=clutch.label))
    world.add(Entity(id="creature", type="thing", label=creature.label))
    world.add(Entity(id="trouble", type="thing", label=trouble.label))
    hero.memes["responsible"] = 1.0
    _story_setup(world, hero, clutch, creature)
    _conflict_beat(world, hero, trouble)
    _transform(world, hero, creature, clutch, trouble)
    _ending(world, hero, creature, clutch)
    world.facts.update(hero=hero, clutch=clutch, creature=creature, trouble=trouble, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child that includes the words "responsible" and "clutch".',
        f"Tell a mythic story about {f['hero'].id} guarding {f['clutch'].phrase} when {f['trouble'].label} arrives.",
        f"Write a story with conflict and transformation in an old shrine, where a responsible child helps change a creature.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clutch = f["clutch"]
    trouble = f["trouble"]
    creature = f["creature"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, who acts responsibly when the clutch is in danger. The story also follows the old creature that changes during the conflict."
        ),
        QAItem(
            question="What caused the conflict?",
            answer=f"{trouble.label} caused the conflict by pressing hard on the shrine and threatening {clutch.label}. That danger made the moment tense and forced {hero.id} to choose what to do."
        ),
        QAItem(
            question="What changed in the story?",
            answer=f"The creature transformed from {creature.form} into {creature.transformed_form}, and the danger around the clutch became calm. The responsible choice turned the conflict into a safer ending."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does responsible mean?",
            answer="Responsible means you take care of what needs protection and choose the safe, thoughtful thing to do."
        ),
        QAItem(
            question="What is a clutch?",
            answer="A clutch is a group of eggs or shells kept together, often needing careful protection."
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes into a new form or a new way of being. In myths, that change can be magical or symbolic."
        ),
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
        lines.append(f"  {e.id:8} ({e.type}) memes={dict(e.memes)} meters={dict(e.meters)} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mountain", "Ari", "boy", "eggs", "dragon", "storm"),
    StoryParams("island", "Mira", "girl", "shells", "serpent", "hunters"),
    StoryParams("forest", "Luna", "girl", "eggs", "stag", "flood"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUTCHES[params.clutch], CREATURES[params.creature],
                 TROUBLES[params.trouble], params.hero_name, params.hero_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show transformation/1."))
    conflicts = {a[0] for a in asp.atoms(model, "conflict")}
    if conflicts:
        return valid_combos()
    return []


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/1.\n#show transformation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for c in valid_combos():
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(json.dumps(samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
