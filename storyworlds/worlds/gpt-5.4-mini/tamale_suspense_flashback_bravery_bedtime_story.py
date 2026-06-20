#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tamale_suspense_flashback_bravery_bedtime_story.py
===================================================================================

A small bedtime storyworld about a child, a warm tamale, a spooky sound, a
flashback to a forgotten promise, and a brave choice that makes the night feel
safe again.

The domain is intentionally tiny:
- a child wants to keep a special tamale safe for bedtime;
- a suspense beat appears when a small worry is triggered by a sound or smell;
- a flashback reminds the child of a past lesson;
- bravery turns the ending from anxious to calm.

The story is simulated from state:
- physical meters: warmth, tucked, dropped, suspense, saved
- emotional memes: sleepy, worry, bravery, comfort, pride

The prose is child-facing and bedtime-soft, with a clear beginning, tension,
turn, and closing image.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/tamale_suspense_flashback_bravery_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/tamale_suspense_flashback_bravery_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/tamale_suspense_flashback_bravery_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/tamale_suspense_flashback_bravery_bedtime_story.py --verify
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
BRAVERY_MIN = 2.0
SUSPENSE_MIN = 1.0


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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scenario:
    id: str
    place: str
    time: str
    sound: str
    scent: str
    hiding_spot: str
    comfort_word: str


@dataclass
class Tamale:
    id: str
    phrase: str
    label: str = "tamale"
    warmth: int = 2
    wrapped: bool = True
    shared: bool = False
    edible: bool = True


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SCENARIOS = {
    "kitchen": Scenario("kitchen", "the warm kitchen", "late evening", "a tiny clink", "sweet corn and butter", "the breadbox", "cozy"),
    "hallway": Scenario("hallway", "the hallway", "nighttime", "the floorboard creak", "warm steam", "the pillow fort", "soft"),
    "porch": Scenario("porch", "the porch", "just before bed", "the screen door tap", "spice and smoke", "the blanket basket", "gentle"),
}


@dataclass
class StoryParams:
    scenario: str
    tamale: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


def danger_at_risk(scenario: Scenario, tamale: Tamale) -> bool:
    return tamale.wrapped and scenario.id in SCENARIOS


def _rule_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["dropped"] < THRESHOLD:
        return out
    sig = ("spill", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["suspense"] += 1
    child.memes["worry"] += 1
    out.append("__spill__")
    return out


def _rule_brave(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["bravery"] < BRAVERY_MIN:
        return out
    if child.meters["suspense"] < SUSPENSE_MIN:
        return out
    sig = ("brave", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["comfort"] += 1
    out.append("__brave__")
    return out


RULES = [_rule_spill, _rule_brave]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_drop(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["dropped"] += 1
    propagate(sim, narrate=False)
    return {
        "suspense": sim.get("child").meters["suspense"],
        "worry": sim.get("child").memes["worry"],
    }


def setup(world: World, child: Entity, parent: Entity, scenario: Scenario, tamale: Tamale) -> None:
    child.memes["sleepy"] += 1
    child.memes["bravery"] += 1
    child.memes["love"] += 1
    world.say(
        f"At bedtime, {child.id} padded through {scenario.place} with a sleepy smile. "
        f"{parent.id} had saved one warm {tamale.label} for later, and the whole room smelled of {scenario.scent}."
    )
    world.say(
        f"{child.id} wanted to keep the {tamale.label} safe, because it felt like a tiny treasure tucked into the night."
    )


def suspense_beat(world: World, child: Entity, scenario: Scenario, tamale: Tamale) -> None:
    child.meters["suspense"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Then {scenario.sound} came from {scenario.hiding_spot}, and {child.id} stopped very still. "
        f"The {tamale.label} felt warm in {child.pronoun('possessive')} hands, but the little sound made the dark seem bigger."
    )


def flashback(world: World, child: Entity, parent: Entity, scenario: Scenario) -> None:
    world.facts["flashback"] = True
    child.memes["memory"] += 1
    world.say(
        f"Right then, {child.id} remembered something {parent.id} had said before bed on another night: "
        f'"When a worry feels large, take a breath, look again, and use your brave voice."'
    )
    world.say(
        f"The memory was small and bright, like a lamp inside {child.pronoun('possessive')} chest."
    )


def brave_choice(world: World, child: Entity, parent: Entity, tamale: Tamale, scenario: Scenario) -> None:
    child.memes["bravery"] += 2
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    child.meters["saved"] += 1
    world.say(
        f"So {child.id} took a slow breath and called for {parent.label_word} in a steady voice instead of hiding."
    )
    world.say(
        f"{parent.id} came right away, smiled at the little worry, and helped {child.id} tuck the {tamale.label} into {scenario.hiding_spot} where it was safe and snug."
    )


def ending(world: World, child: Entity, parent: Entity, scenario: Scenario, tamale: Tamale) -> None:
    child.memes["comfort"] += 1
    child.memes["pride"] += 1
    world.say(
        f"After that, the room grew quiet again. {child.id} sat close to {parent.id}, listening to the soft night sounds, "
        f"and the warm {tamale.label} waited safely for morning."
    )
    world.say(
        f"{child.id} felt brave, cozy, and proud, and the bedtime feeling was gentle all around."
    )


def tell(scenario: Scenario, tamale: Tamale, child_name: str = "Mia", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="tamale", kind="thing", type="food", label="tamale"))

    setup(world, child, parent, scenario, tamale)
    world.para()
    suspense_beat(world, child, scenario, tamale)
    flashback(world, child, parent, scenario)
    world.para()
    brave_choice(world, child, parent, tamale, scenario)
    ending(world, child, parent, scenario, tamale)

    world.facts.update(
        child=child,
        parent=parent,
        scenario=scenario,
        tamale=tamale,
        suspense=child.meters["suspense"] >= THRESHOLD,
        flashback=bool(world.facts.get("flashback")),
        brave=child.memes["bravery"] >= BRAVERY_MIN,
    )
    return world


SCENARIO_REGISTRY = SCENARIOS
TAMALES = {
    "classic": Tamale("classic", "a warm tamale"),
    "honey": Tamale("honey", "a sweet tamale"),
    "cheese": Tamale("cheese", "a cheesy tamale"),
}

GIRL_NAMES = ["Mia", "Luna", "Nina", "Ella", "Zoe", "Ruby"]
BOY_NAMES = ["Leo", "Noah", "Ben", "Eli", "Kai", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SCENARIOS for t in TAMALES]


@dataclass
class StoryParams:
    scenario: str
    tamale: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    s = f["scenario"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "tamale" and a tiny moment of suspense.',
        f"Tell a gentle story where {c.id} is near {s.place}, hears a small scary sound, remembers a brave lesson, and feels calm again.",
        f'Write a cozy story with a flashback and bravery in which a child keeps a tamale safe until morning.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, p, s = f["child"], f["parent"], f["scenario"]
    qa = [
        ("Who is the story about?", f"It is about {c.id}, who was getting ready for bed with {p.id}. The night is cozy, but a small worry gives the story a little suspense."),
        ("What made the child feel uneasy?", f"{s.sound} came from {s.hiding_spot}, so {c.id} paused and listened carefully. That small sound made the room feel extra quiet for a moment."),
        ("What did the child remember?", f"{c.id} remembered {p.id}'s brave bedtime advice: take a breath, look again, and use a steady voice. The flashback helped turn worry into calm."),
        ("How did the story end?", f"{c.id} asked for help, stayed brave, and kept the tamale safe for morning. The ending is soft and peaceful, with the child feeling proud."),
    ]
    return qa


KNOWLEDGE = {
    "tamale": [("What is a tamale?", "A tamale is a warm food made with dough and filling, wrapped up before it is cooked. People often eat it as a special treat.")],
    "bedtime": [("What should bedtime feel like?", "Bedtime should feel calm, safe, and sleepy, with soft lights and gentle voices.")],
    "bravery": [("What does bravery mean?", "Bravery means doing the right thing even when you feel a little scared. It does not mean never being afraid.")],
    "flashback": [("What is a flashback in a story?", "A flashback is when a story briefly remembers something that happened before. It helps explain why a character acts the way they do now.")],
    "suspense": [("What is suspense?", "Suspense is the feeling of wondering what will happen next. It can make a story feel exciting for a moment.")],
    "night": [("Why can the night feel spooky?", "At night, things look less clear and small sounds can seem bigger. That can make a child feel unsure until they remember they are safe.")],
}
KNOWLEDGE_ORDER = ["tamale", "bedtime", "bravery", "flashback", "suspense", "night"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"tamale", "bedtime", "bravery", "flashback", "suspense", "night"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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


CURATED = [
    StoryParams("kitchen", "classic", "Mia", "girl", "Mom", "mother"),
    StoryParams("hallway", "honey", "Leo", "boy", "Dad", "father"),
    StoryParams("porch", "cheese", "Nina", "girl", "Mom", "mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime storyworld with tamale, suspense, flashback, and bravery.")
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--tamale", choices=TAMALES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.scenario is None or c[0] == args.scenario)
              and (args.tamale is None or c[1] == args.tamale)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scenario, tamale = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent_name or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(scenario, tamale, child_name, child_gender, parent_name, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENARIOS[params.scenario], TAMALES[params.tamale],
                 params.child_name, params.child_gender, params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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


ASP_RULES = r"""
suspense(C) :- child(C), worried(C).
brave(C) :- child(C), bravery(C, B), B >= bravery_min.
flashback(C) :- child(C), remembers(C).
calm(C) :- brave(C), flashback(C), suspense(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
    for tid, t in TAMALES.items():
        lines.append(asp.fact("tamale", tid))
    lines.append(asp.fact("bravery_min", BRAVERY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show tamale/1."))
    return sorted(set(asp.atoms(model, "tamale")))


def asp_verify() -> int:
    rc = 0
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: empty story")
        rc = 1
    try:
        _ = generate(CURATED[1]).story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"MISMATCH: generation crashed: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
