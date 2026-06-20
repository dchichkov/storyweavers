#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grenade_tit_dim_circulate_magic_surprise_happy.py
==================================================================================

A small, standalone story world in a fable-like style.

Premise
-------
A little fox and a lantern-maker live by a windmill. A dim little bell
called Tit-Dim helps the night watchman know when to wake the village.
One evening a strange round charm called a grenade rolls into the story.
It is not a weapon here; in this world it is a magical seed-sphere that can
burst into sparks of flowers when handled wisely.

The tension comes from the bell going too dim, the surprise comes from magic
returning in an unexpected way, and the happy ending proves that the warmth
did circulate back through the village.

The seed words required by the prompt are included in the world and the text:
grenade, tit-dim, circulate.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/grenade_tit_dim_circulate_magic_surprise_happy.py
    python storyworlds/worlds/gpt-5.4-mini/grenade_tit_dim_circulate_magic_surprise_happy.py --all
    python storyworlds/worlds/gpt-5.4-mini/grenade_tit_dim_circulate_magic_surprise_happy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/grenade_tit_dim_circulate_magic_surprise_happy.py --verify
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
MILD_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    mood: str
    wind: str

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
class MagicItem:
    id: str
    label: str
    phrase: str
    glow: str
    kind: str = "magic"
    gentle: bool = True
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
class Trouble:
    id: str
    label: str
    phrase: str
    dimness: int
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
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
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


def _r_circulate(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.entities.get("lantern")
    if lantern and lantern.meters["warmth"] >= THRESHOLD:
        sig = ("circulate",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.kind == "character":
                    e.memes["hope"] += 1
                    e.memes["calm"] += 1
            out.append("__circulate__")
    return out


CAUSAL_RULES = [Rule("circulate", "social", _r_circulate)]


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


def reasonableness_gate(trouble: Trouble, remedy: Remedy) -> bool:
    return trouble.dimness >= 1 and remedy.sense >= MILD_MIN


def desired_end(remedy: Remedy, trouble: Trouble) -> bool:
    return remedy.power >= trouble.dimness


def tell(
    setting: Setting,
    hero_name: str = "Mira",
    companion_name: str = "Oren",
    parent_name: str = "Mother",
    tone: str = "patient",
    seed: Optional[int] = None,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="seeker", traits=["curious"]))
    companion = world.add(Entity(id=companion_name, kind="character", type="boy", role="watcher", traits=["wise"]))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="keeper", traits=[tone]))
    bell = world.add(Entity(id="tit_dim", type="thing", label="tit-dim bell"))
    grenade = world.add(Entity(id="grenade", type="thing", label="grenade charm"))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern"))
    world.facts["setting"] = setting
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["parent"] = parent
    world.facts["bell"] = bell
    world.facts["grenade"] = grenade
    world.facts["lantern"] = lantern

    hero.memes["wonder"] = 1
    companion.memes["care"] = 1
    bell.meters["dimness"] = 1.0
    lantern.meters["warmth"] = 0.0

    world.say(
        f"In {setting.place}, where {setting.mood} air moved with a {setting.wind} breath, "
        f"{hero.id} and {companion.id} listened to the little {bell.label_word} called tit-dim."
    )
    world.say(
        f"{hero.id} loved that the bell could guide the dark roads, but tonight its sound had grown thin and low."
    )

    trouble = Trouble("dim-bell", "dim bell", "tit-dim", 1, tags={"tit-dim", "dim"})
    remedy = Remedy("warm-light", "warm light", "circulate", 2, 3, tags={"circulate", "magic"})
    if not reasonableness_gate(trouble, remedy):
        raise StoryError("This story needs a dim bell and a sensible magical remedy.")

    world.para()
    world.say(
        f"Then a round {grenade.label} rolled from under the threshing step, bright as a beetle in moonlight."
    )
    world.say(
        f'{companion.id} blinked. "That looks like a grenade," {companion.pronoun()} whispered, '
        f'but the old orchard-keeper had taught them that in fables, a grenade can be a seed of surprise.'
    )
    world.say(
        f"{hero.id} touched it gently, and the charm answered with a tiny golden pop."
    )
    grenade.meters["spark"] += 1

    world.para()
    hero.memes["fear"] += 1
    companion.memes["hope"] += 1
    world.say(
        f"The pop did not hurt anyone. Instead, it sent a ring of light drifting outward, as if it meant to circulate."
    )
    world.say(
        f"{hero.id} hurried to the lantern and set the magical seed into its base."
    )
    lantern.meters["warmth"] += 2
    propagate(world, narrate=False)
    world.say(
        f"At once the lantern woke up, and the dim little tit-dim bell sounded clearer, as though the village had remembered its own song."
    )

    world.para()
    world.say(
        f"{parent.id} came to the doorway smiling, because {parent.pronoun()} had heard the bell and the happy hush after it."
    )
    world.say(
        f'"A surprise can be kind," {parent.id} said. "When magic is used wisely, light can {remedy.id} through a whole home."'
    )
    world.say(
        f"So {hero.id} and {companion.id} carried the lantern from house to house, and the glow did circulate from window to window."
    )
    world.say(
        "By bedtime the lane was soft and bright, the bell was no longer dim, and the village slept under a gentle gold."
    )

    world.facts.update(
        outcome="happy",
        trouble=trouble,
        remedy=remedy,
        grenade_used=True,
        bell_fixed=True,
        circulated=True,
    )
    return world


SETTINGS = {
    "orchard": Setting("the orchard village", "sweet apple", "a moon-pale"),
    "mill": Setting("the old mill lane", "dusty grain", "a turning"),
    "brook": Setting("the brook hamlet", "cool water", "a whispering"),
}

REMINDERS = {
    "tit-dim": MagicItem("tit-dim", "tit-dim", "the tit-dim bell", "a thin silver chime", tags={"tit-dim", "dim"}),
    "grenade": MagicItem("grenade", "grenade", "a grenade charm", "a bright golden pop", tags={"grenade", "magic"}),
    "circulate": MagicItem("circulate", "circulate", "the circulating light", "a ring of warm light", tags={"circulate", "magic"}),
}

TROBULES = {
    "dim": Trouble("dim", "dimness", "tit-dim", 1, tags={"tit-dim", "dim"}),
}

REMEDIES = {
    "magic": Remedy("magic", "magic", "let it circulate", 2, 3, tags={"circulate", "magic"}),
}

GIRL_NAMES = ["Mira", "Lina", "Nell", "Rosa", "Tessa", "Ivy"]
BOY_NAMES = ["Oren", "Pip", "Bram", "Eli", "Rowan", "Finn"]
TRAITS = ["patient", "gentle", "brave", "careful", "kind"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    hero: str
    companion: str
    parent: str
    trait: str
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
    return [(s, "tit-dim", "circulate") for s in SETTINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like magic story world with a surprise and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--companion")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos() if args.setting is None or c[0] == args.setting]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, _, _ = rng.choice(combos)
    hero = args.hero or rng.choice(GIRL_NAMES)
    companion = args.companion or rng.choice([n for n in BOY_NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, hero, companion, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story that includes the words "grenade", "tit-dim", and "circulate".',
        f"Tell a magical surprise story where {f['hero'].id} finds a grenade charm and helps a dim tit-dim bell brighten again.",
        f"Write a happy-ending story about a village where light can circulate from house to house after a tiny magical surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What surprised {hero.id} and {companion.id}?",
            answer="A round grenade charm rolled out of the shadows and gave them a magical surprise. It was gentle, not dangerous, and it made the village feel awake again.",
        ),
        QAItem(
            question="What happened to tit-dim by the end?",
            answer="The tit-dim bell sounded clear and bright again. The lantern was warmed, so the bell no longer seemed dim.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with light circulating from house to house. The village settled down under a soft gold glow and everyone slept safely.",
        ),
        QAItem(
            question=f"Who helped {hero.id} understand the surprise?",
            answer=f"{companion.id} noticed the old fable meaning, and {parent.id} confirmed that the magic was kind. Their calm response helped turn the surprise into a good ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does circulate mean?",
            answer="To circulate means to move around and spread from place to place. In this story, the light circulated through the village and reached many houses.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that appears or happens. Good stories often use a surprise to change the mood or solve a problem in a new way.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the characters are safe, the problem is solved, and the story closes with a peaceful image. Readers can feel that things turned out well.",
        ),
        QAItem(
            question="Why can magic be part of a fable?",
            answer="Fables often use magic or talking signs to teach a gentle lesson. The magic helps the story feel memorable while still pointing to wisdom and kindness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S) :- setting(S), trouble(dim), remedy(magic).
outcome(happy) :- valid(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("trouble", "dim"))
    lines.append(asp.fact("remedy", "magic"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set((s, "tit-dim", "circulate") for (s,) in asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    print("OK: normal generate smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.hero, params.companion, params.parent, params.trait, params.seed)
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


CURATED = [
    StoryParams("orchard", "Mira", "Oren", "mother", "gentle"),
    StoryParams("mill", "Lina", "Pip", "father", "patient"),
    StoryParams("brook", "Nell", "Bram", "mother", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
