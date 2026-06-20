#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/groove_paint_gerund_bravery_surprise_rhyme_space.py
====================================================================================

A standalone storyworld for a tiny Space Adventure tale: a child crew member
must cross a dark groove in an alien hull, discovers a surprise, keeps up their
bravery, and finishes with a rhyme about safe, careful exploration.

The world is small on purpose:
- a rover or ship has a groove that needs attention,
- a child uses paint while painting,
- a surprise helper or obstacle changes the plan,
- bravery rises and fear falls,
- a short rhyme closes the story with a clear ending image.

This file is self-contained and uses only the Python stdlib plus the shared
story result containers from ``storyworlds/results.py``.
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
BRAVERY_START = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    dark_spot: str
    ship_name: str
    afford_paint: bool = True

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
class Task:
    id: str
    verb: str
    gerund: str
    paint_gerund: str
    groove_risk: bool
    surprise: str
    rhyme: str
    result_image: str

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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

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


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["painted"] >= THRESHOLD and hero.memes["surprise"] >= THRESHOLD:
        sig = ("bravery", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["bravery"] += 1
            hero.memes["fear"] = 0
            out.append("__brave__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    panel = world.entities.get("panel")
    if not panel:
        return out
    if panel.meters["sealed"] >= THRESHOLD and panel.meters["painted"] >= THRESHOLD:
        sig = ("repair", panel.id)
        if sig not in world.fired:
            world.fired.add(sig)
            panel.meters["secure"] += 1
            out.append("__secure__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_bravery, _r_repair):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, task: Task) -> dict:
    sim = world.copy()
    do_paint(sim, sim.get("hero"), task, narrate=False)
    return {
        "bravery": sim.get("hero").memes["bravery"],
        "secure": sim.get("panel").meters["secure"],
        "painted": sim.get("panel").meters["painted"],
    }


def do_paint(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    hero.meters["painted"] += 1
    hero.memes["surprise"] += 1
    if narrate:
        world.say(
            f"{hero.id} started {task.paint_gerund} along the groove, using bright blue paint."
        )
    if task.groove_risk:
        panel = world.get("panel")
        panel.meters["painted"] += 1
        panel.meters["sealed"] += 1
        panel.meters["shine"] += 1
        if narrate:
            world.say(
                f"The paint settled into the groove like a tiny river, and the line looked smooth again."
            )
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    hero.memes["bravery"] = BRAVERY_START
    hero.memes["fear"] = 1
    helper.memes["surprise"] = 0
    world.say(
        f"On the {world.setting.place}, {hero.id} and {helper.id} floated beside {world.setting.ship_name}."
    )
    world.say(
        f"A long groove crossed the hull near {world.setting.dark_spot}, and the mission called for {task.verb}."
    )


def surprise_beat(world: World, helper: Entity, task: Task) -> None:
    helper.memes["surprise"] += 1
    world.say(
        f"Then came a surprise: {task.surprise}. {helper.id} blinked twice and grinned."
    )


def brave_choice(world: World, hero: Entity, task: Task) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took a breath and said, \"I can do it.\" {hero.pronoun().capitalize()} kept {hero.pronoun('possessive')} hands steady."
    )


def ending(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    panel = world.get("panel")
    world.say(
        f"When the work was done, {panel.label_word} looked whole, and the {task.result_image}."
    )
    world.say(
        f"{hero.id} and {helper.id} drifted on, smiling, while a small rhyme rang in the cabin: \"{task.rhyme}\""
    )


def tell(setting: Setting, task: Task, hero_name: str = "Nia", hero_gender: str = "girl",
         helper_name: str = "Milo", helper_gender: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="pilot"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="mate"))
    world.add(Entity(id="panel", type="ship", label="the hull panel"))
    setup(world, hero, helper, task)
    world.para()
    surprise_beat(world, helper, task)
    brave_choice(world, hero, task)
    do_paint(world, hero, task)
    world.para()
    ending(world, hero, helper, task)
    world.facts.update(hero=hero, helper=helper, task=task, setting=setting, outcome="fixed")
    return world


SETTINGS = {
    "orbit": Setting("orbit", "the quiet orbit lane", "the shadowed curve", "Star Kite"),
    "dock": Setting("dock", "the moon dock", "the cracked seam", "Comet Door"),
    "asteroid": Setting("asteroid", "the rocky ring", "the narrow groove", "Pebble Runner"),
}

TASKS = {
    "seal": Task("seal", "seal", "sealing", "painted sealing", True,
                 "a tiny tool floated out from behind a magnet strip",
                 "Paint the groove, keep it light; brave little hands make the ship feel right.",
                 "the groove shone smooth under the lantern light"),
    "mark": Task("mark", "mark", "marking", "painted marking", True,
                "a surprise star sticker drifted from a pouch",
                "Paint the groove, sing a tune; steady hands can brighten noon.",
                "the groove wore a bright blue ribbon of paint"),
    "stripe": Task("stripe", "stripe", "striping", "painted striping", True,
                  "a surprise comet decal spun in the air",
                  "Paint the groove, brave and clear; safe repair will keep us near.",
                  "the groove gleamed like a smiling path"),
}

GIRL_NAMES = ["Nia", "Luna", "Ivy", "Mara", "Zuri", "Tess"]
BOY_NAMES = ["Milo", "Finn", "Arlo", "Jace", "Pax", "Otto"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TASKS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with groove, paint, bravery, surprise, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.setting and args.task:
        if (args.setting, args.task) not in valid_combos():
            raise StoryError("No valid story fits those choices.")
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(setting, task, hero, hero_gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the word "groove" and the idea of {f["task"].paint_gerund}.',
        f"Tell a story where {f['hero'].id} shows bravery, notices a surprise, and repairs a groove on {f['setting'].ship_name}.",
        f'Write a gentle sci-fi story that ends with a rhyme about safe repair and painted metal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    setting = f["setting"]
    panel = world.get("panel")
    return [
        QAItem(
            question="What was the child fixing?",
            answer=f"{hero.label_word} was fixing a groove in the hull of {setting.ship_name}. The paint helped seal the line so the ship felt safe again."
        ),
        QAItem(
            question="What surprised them?",
            answer=f"They got a surprise when {task.surprise}. That surprise made the moment exciting, but it also helped them stay alert and brave."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the groove painted smooth and {panel.label_word} looking whole again. The last line was a rhyme, which made the ending feel cheerful and complete."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a groove?", "A groove is a long, narrow line or dent. Paint can flow into it and help fill or cover it."),
        QAItem("What does bravery mean?", "Bravery means doing something hard or a little scary while you stay steady. It does not mean you feel no fear at all."),
        QAItem("What is a rhyme?", "A rhyme is when words sound alike at the end, like tune and moon. Rhymes can make a story feel playful and memorable."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], params.hero_name, params.hero_gender, params.helper_name, params.helper_gender)
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
    StoryParams("orbit", "seal", "Nia", "girl", "Milo", "boy"),
    StoryParams("dock", "mark", "Luna", "girl", "Pax", "boy"),
    StoryParams("asteroid", "stripe", "Mara", "girl", "Finn", "boy"),
]


ASP_RULES = r"""
valid(S, T) :- setting(S), task(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    try:
        generate(CURATED[0]).story
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    else:
        print("OK: generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print("\n".join(f"{s} {t}" for s, t in combos))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
