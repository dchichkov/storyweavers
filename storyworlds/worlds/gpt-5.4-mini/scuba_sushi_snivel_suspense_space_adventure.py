#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scuba_sushi_snivel_suspense_space_adventure.py
===============================================================================

A standalone story world for a small space-adventure suspense tale:
a child astronaut wants to reach a lost sushi lunch box through a flooded
maintenance tunnel, a nervous helper snivels about the dark, and a calm grown-up
uses scuba gear and a steady plan to turn worry into a safe rescue.

This world keeps the story child-facing and state-driven:
- physical meters: water, danger, oxygen, soggy
- emotional memes: courage, worry, relief, pride
- suspense comes from a short, ticking countdown and a dark flooded passage
- the ending image proves the change: the sushi is recovered, the helper is calm,
  and the station is safe again
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
SENSE_MIN = 2
OXYGEN_SAFE = 3.0


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
    attrs: dict = field(default_factory=dict)
    waterproof: bool = False
    makes_bubbles: bool = False
    edible: bool = False
    plural: bool = False

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
class Theme:
    id: str
    ship: str
    mission: str
    dark_passage: str
    opening: str
    ending: str

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
class Hazard:
    id: str
    label: str
    phrase: str
    where: str
    makes_water: bool = True
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
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    sound: str
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
class Reward:
    id: str
    label: str
    phrase: str
    tasty: str
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
    apply: Callable[[World], list[str]]

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


def _r_water_risk(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["water"] < THRESHOLD:
            continue
        sig = ("water_risk", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["danger"] += 1
        out.append("__risk__")
    return out


def _r_oxygen_drop(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["diving"] < THRESHOLD:
            continue
        sig = ("oxygen", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["oxygen"] += 1
        e.memes["worry"] += 1
        out.append("__oxygen__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


CAUSAL_RULES = [Rule("water_risk", _r_water_risk), Rule("oxygen_drop", _r_oxygen_drop)]


def hazard_at_risk(hazard: Hazard, reward: Reward) -> bool:
    return hazard.makes_water and "water" in reward.tags


def sensible_gears() -> list[Gear]:
    return [g for g in GEARS.values() if len(g.helps) >= 1]


def best_gear() -> Gear:
    return max(GEARS.values(), key=lambda g: len(g.helps))


def is_contained(gear: Gear, delay: int) -> bool:
    return gear.id in {"scuba", "submask"} and delay <= 2


def tell(theme: Theme, hazard: Hazard, reward: Reward, gear: Gear, delay: int,
         hero: str = "Mina", hero_gender: str = "girl",
         helper: str = "Pip", helper_gender: str = "boy",
         parent: str = "mother", helper_trait: str = "careful") -> World:
    world = World()
    a = world.add(Entity(hero, kind="character", type=hero_gender, role="hero"))
    b = world.add(Entity(helper, kind="character", type=helper_gender, role="helper",
                         traits=[helper_trait]))
    p = world.add(Entity("Parent", kind="character", type=parent, role="parent",
                         label="the captain"))
    tunnel = world.add(Entity("tunnel", label=theme.dark_passage))
    box = world.add(Entity("sushi", label=reward.label, edible=True))
    leak = world.add(Entity("leak", label=hazard.label))

    a.memes["courage"] = 1.0
    b.memes["worry"] = 1.0
    world.facts["delay"] = delay

    world.say(
        f"On {theme.ship}, {a.id} and {b.id} were ready for {theme.mission}. "
        f"Inside the galley sat {reward.phrase}, and everybody wanted it kept safe."
    )
    world.say(
        f"{theme.opening} But a leak had flooded the maintenance tunnel, so the dark "
        f"hallway looked like a black river under the station lights."
    )

    world.para()
    world.say(
        f'"We have to go through the tunnel to reach the lunch locker," {a.id} said, '
        f"peeking at the water."
    )
    world.say(
        f'{b.id} gave a little snivel and hugged {b.pronoun("possessive")} sleeves. '
        f'"It is spooky in there," {b.id} whispered.'
    )
    world.say(
        f'{p.label_word.capitalize()} knelt beside them. "That is why we use the '
        f'{gear.label} and move one step at a time."'
    )

    if gear.id == "scuba":
        a.meters["diving"] += 1
        b.meters["diving"] += 1
    if gear.id == "submask":
        a.meters["diving"] += 1

    world.para()
    if not is_contained(gear, delay):
        world.say(
            f'{a.id} followed {p.label_word} anyway, but the {gear.label} was not '
            f'enough for the flooding. The water swirled harder, and the suspense '
            f'made everyone hold still for a breath.'
        )
        world.say(
            f'{p.label_word.capitalize()} pulled them back before the tunnel got too deep. '
            f'With a bigger kit and a calmer plan, they could try again later.'
        )
        world.facts.update(outcome="blocked", recovered=False, gear=gear, hero=a, helper=b, parent=p,
                           hazard=hazard, reward=reward, theme=theme, tunnel=tunnel, box=box)
        return world

    world.say(
        f'{gear.sound} The {gear.label} fit snugly, and tiny bubbles flashed past the '
        f'visors like silver pearls.'
    )
    world.say(
        f'Together they slipped into the tunnel. The water was cold, the walls were '
        f'dark, and every drip sounded huge, but {a.id} kept going.'
    )
    world.say(
        f'At last they found the lunch locker. {reward.phrase} floated inside, still '
        f'safe and dry enough to take home.'
    )
    world.say(
        f'{p.label_word.capitalize()} lifted the box out carefully, and {b.id} stopped '
        f'sniveling at once.'
    )

    world.para()
    a.memes["pride"] += 1
    b.memes["relief"] += 1
    world.say(
        f'Back on the bright deck, the three of them ate {reward.phrase} together. '
        f'{theme.ending}'
    )
    world.say(
        f'{a.id} grinned at {b.id}, who now looked brave instead of scared. Even the '
        f'black tunnel seemed smaller with the lights on and the mission done.'
    )
    world.facts.update(outcome="recovered", recovered=True, gear=gear, hero=a, helper=b, parent=p,
                       hazard=hazard, reward=reward, theme=theme, tunnel=tunnel, box=box)
    return world


THEMES = {
    "station": Theme("station", "the Starbeam station", "a rescue mission",
                     "the flooded maintenance tunnel", "A soft alarm blinked at the hatch.",
                     "The station hummed happily again."),
    "moonbase": Theme("moonbase", "Moon Harbor base", "a lunch rescue",
                      "the flooded moon corridor", "A red light flashed over the door.",
                      "The base felt calm and bright again."),
}

HAZARDS = {
    "leak": Hazard("leak", "water leak", "a hidden water leak", "the tunnel"),
}

REWARDS = {
    "sushi": Reward("sushi", "sushi", "a tiny lunch box of sushi", "tasty", tags={"water", "food", "sushi"}),
}

GEARS = {
    "scuba": Gear("scuba", "scuba gear", "the scuba gear", {"water"}, {"water"}, "Swish!", tags={"scuba"}),
    "submask": Gear("submask", "a scuba mask and air tank", "the scuba mask and air tank", {"water"}, {"water"}, "Click!", tags={"scuba"}),
    "boots": Gear("boots", "space boots", "the space boots", set(), set(), "Clomp!", tags={"space"}),
}

GIRL_NAMES = ["Mina", "Nova", "Luna", "Zoe", "Ava"]
BOY_NAMES = ["Pip", "Kai", "Theo", "Max", "Leo"]
TRAITS = ["careful", "curious", "brave", "quiet"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    hazard: str
    reward: str
    gear: str
    delay: int
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
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
    out = []
    for t in THEMES:
        for h in HAZARDS:
            for r in REWARDS:
                if hazard_at_risk(HAZARDS[h], REWARDS[r]):
                    out.append((t, h, r))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure suspense story that includes the words "scuba", "sushi", and "snivel".',
        f"Tell a calm-but-tense rescue story where {f['hero'].id} uses scuba gear to reach sushi through a flooded tunnel, while {f['helper'].id} snivels about the dark.",
        f"Write a child-friendly space story with a flooded hallway, a steady grown-up, and a happy ending where the sushi is saved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    reward = f["reward"]
    qa = [
        QAItem(
            question="What was the mission?",
            answer=f"They were trying to reach {reward.phrase} in the lunch locker and bring it back safely."
        ),
        QAItem(
            question=f"Why did {helper.id} snivel?",
            answer=f"{helper.id} sniveled because the flooded tunnel looked dark and spooky. The water and the silence made the trip feel scary until the grown-up showed the safe plan."
        ),
        QAItem(
            question="How did they get through the tunnel?",
            answer=f"They wore scuba gear and moved carefully beside {parent.label_word}. The gear let them breathe and kept the water from winning."
        ),
    ]
    if f["outcome"] == "recovered":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"They brought the sushi back to the bright deck and ate it together. The scary tunnel was behind them, and {helper.id} was calm again."
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer="They had to pull back before the tunnel got too deep. The suspense stayed high, but the family stayed safe and planned a better try later."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is scuba gear for?", "Scuba gear helps a person breathe underwater by bringing air from a tank or other breathing system."),
        QAItem("What is sushi?", "Sushi is a kind of food, often made with rice and fish or vegetables, that people eat as a meal."),
        QAItem("What does it mean to snivel?", "To snivel means to whimper or sniffle in a worried way, usually because someone feels scared or upset."),
        QAItem("Why is a flooded tunnel dangerous?", "Water in a tunnel can hide the floor, slow you down, and make it hard to breathe or move safely."),
    ]


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
    StoryParams("station", "leak", "sushi", "scuba", 1, "Mina", "girl", "Pip", "boy", "mother", "careful"),
    StoryParams("moonbase", "leak", "sushi", "submask", 2, "Nova", "girl", "Kai", "boy", "father", "curious"),
]


def explain_rejection(hazard: Hazard, reward: Reward) -> str:
    return f"(No story: {hazard.label} cannot make a strong suspense setup for {reward.label}.)"


def outcome_of(params: StoryParams) -> str:
    return "recovered" if is_contained(GEARS[params.gear], params.delay) else "blocked"


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("makes_water", hid))
    for rid in REWARDS:
        lines.append(asp.fact("reward", rid))
        lines.append(asp.fact("water_reward", rid))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F,R) :- makes_water(F), water_reward(R).
sensible(G) :- gear(G), helps(G, water).
valid(T,F,R) :- theme(T), hazard(F,R), sensible(G), helps(G, water).
contained(G,D) :- gear(G), D <= 2, helps(G, water).
outcome(recovered) :- contained(G,D).
outcome(blocked) :- theme(_), not outcome(recovered).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_gear", params.gear), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP gate.")
    smoke = generate(CURATED[0])
    if not smoke.story or "sushi" not in smoke.story:
        rc = 1
        print("SMOKE TEST FAILED.")
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure suspense story world.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3])
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
    if args.delay is not None and args.delay > 2 and args.gear != "scuba":
        raise StoryError("The flood is too big for anything except scuba gear.")
    combos = valid_combos()
    if args.theme:
        combos = [c for c in combos if c[0] == args.theme]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    theme, hazard, reward = rng.choice(combos)
    gear = args.gear or rng.choice(sorted(GEARS))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    parent = rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    if gear not in GEARS:
        raise StoryError("(Unknown gear.)")
    return StoryParams(theme, hazard, reward, gear, delay, hero, hero_gender, helper, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], HAZARDS[params.hazard], REWARDS[params.reward], GEARS[params.gear], params.delay,
                 hero=params.hero, hero_gender=params.hero_gender,
                 helper=params.helper, helper_gender=params.helper_gender,
                 parent=params.parent, helper_trait=params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:\n")
        for t, h, r in asp_valid_combos():
            print(f"  {t:10} {h:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
