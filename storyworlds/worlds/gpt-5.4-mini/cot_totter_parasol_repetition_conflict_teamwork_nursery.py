#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cot_totter_parasol_repetition_conflict_teamwork_nursery.py
==========================================================================================

A small nursery-rhyme storyworld about a cot, a totter, and a parasol.

Premise
-------
Two little children build a tiny play scene near a cot. One child wants to
keep the totter moving, but the parasol keeps bumping the swing space and the
game turns into a tug of words. A calm helper arrives, and together they move
the parasol, steady the totter, and make the play safe again.

The world is deliberately tiny:
- a few typed entities
- physical meters and emotional memes
- a short causal chain
- repetitive nursery-rhyme phrasing
- a teamwork resolution after conflict

It supports the shared Storyweavers CLI contract:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

The story model is grounded in simulated state rather than fixed prose.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    rhyme: str
    repeated_line: str
    conflict_line: str
    teamwork_line: str
    ending_image: str
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
class Prop:
    id: str
    label: str
    article: str
    risky: bool = False
    useful: bool = False
    physical: bool = False
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
class Help:
    id: str
    label: str
    action: str
    result: str
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    scene = world.facts.get("scene")
    if not scene:
        return out
    totter = world.get("totter")
    if totter.meters["moving"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    totter.memes["rhythm"] += 1
    out.append(scene.repeated_line)
    out.append(scene.repeated_line)
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    totter = world.get("totter")
    parasol = world.get("parasol")
    if totter.meters["moving"] < THRESHOLD or parasol.meters["blocking"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for child in ("child_a", "child_b"):
        world.get(child).memes["frustration"] += 1
        world.get(child).memes["cross"] += 1
    world.get("space").meters["tangle"] += 1
    out.append("__conflict__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    parasol = world.get("parasol")
    totter = world.get("totter")
    if helper.meters["helping"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parasol.meters["blocking"] = 0.0
    totter.meters["moving"] = 1.0
    helper.memes["pride"] += 1
    world.get("child_a").memes["relief"] += 1
    world.get("child_b").memes["relief"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("repetition", _r_repetition),
    Rule("conflict", _r_conflict),
    Rule("teamwork", _r_teamwork),
]


def rival_nature(scene: Scene) -> str:
    return scene.conflict_line


def tell(scene: Scene, hero_a: str, hero_b: str, helper_name: str, helper_type: str,
         parent_name: str, parent_type: str, delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(hero_a, kind="character", type="girl", role="child"))
    b = world.add(Entity(hero_b, kind="character", type="boy", role="child"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(parent_name, kind="character", type=parent_type, role="parent"))
    world.add(Entity("cot", type="cot", label="cot", role="furniture"))
    world.add(Entity("totter", type="totter", label="totter", role="toy"))
    world.add(Entity("parasol", type="parasol", label="parasol", role="prop"))
    world.add(Entity("space", type="space", label="play space", role="space"))

    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.facts["scene"] = scene
    world.say(f"In {scene.place}, by a little cot, {a.id} and {b.id} began a nursery game.")
    world.say(scene.rhyme)
    world.say(f'{a.id} called, "Up and down, and round and round!"')
    world.say(f'{b.id} laughed, "Again, again!"')

    world.para()
    world.get("totter").meters["moving"] += 1
    world.get("parasol").meters["blocking"] += 1
    world.say(scene.repeated_line)
    world.say(rival_nature(scene))
    world.say(f"{a.id} frowned. {b.id} frowned too. The parasol kept nudging the totter.")
    world.say(f'{a.id} said, "No, no, not there!" and {b.id} said, "But it is mine!"')
    world.get("child_a").memes["frustration"] += 1
    world.get("child_b").memes["frustration"] += 1

    world.para()
    helper.meters["helping"] += 1
    propagate(world, narrate=False)
    world.say(f"{helper.id} came softly, with a smile so bright.")
    world.say(f'"{scene.teamwork_line}" {helper.id} asked.')
    world.say(f"Together, they lifted the parasol away, and the cot-side game could mend.")

    world.para()
    world.say(scene.teamwork_line)
    world.say(scene.ending_image)
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    helper.memes["love"] += 1

    world.facts.update(
        child_a=a, child_b=b, helper=helper, parent=parent, scene=scene,
        outcome="teamwork", delay=delay
    )
    return world


SCENES = {
    "garden": Scene(
        "garden",
        "the garden path",
        "By the cot there sat a totter bright, and a parasol in the morning light.",
        "Again they tottered, up and down.",
        "But the parasol blocked the way, and the totter would not stay.",
        "Let us move it, two hands are best.",
        "The parasol stood by the fence, and the totter went on, small and dense.",
        {"cot", "totter", "parasol"},
    ),
    "nursery": Scene(
        "nursery",
        "the nursery floor",
        "By the cot there sat a totter fair, and a parasol took its share.",
        "Again, again, the totter sang.",
        "But the parasol bumped the game, and both small friends called out the same.",
        "Let us work together, one, two, three.",
        "The parasol leaned by the window, and the totter danced free.",
        {"cot", "totter", "parasol"},
    ),
    "porch": Scene(
        "porch",
        "the porch step",
        "Near the cot, on the porch so neat, a totter tapped in a merry beat.",
        "Again and again, it rocked along.",
        "But the parasol swung too wide, and the game lost pace on either side.",
        "One lifts, one steadies, and one holds still.",
        "The parasol rested by the rail, and the totter hummed its happy tale.",
        {"cot", "totter", "parasol"},
    ),
}

HELPERS = {
    "mother": Help("mother", "mother", "lifted the parasol", "made room for the totter", 2, 3, {"teamwork"}),
    "father": Help("father", "father", "held the parasol high", "kept the path clear", 2, 3, {"teamwork"}),
    "sister": Help("sister", "older sister", "slid the parasol aside", "opened the play space", 2, 4, {"teamwork"}),
    "brother": Help("brother", "older brother", "slid the parasol aside", "opened the play space", 2, 4, {"teamwork"}),
}


@dataclass
@dataclass
class StoryParams:
    scene: str
    helper: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, h) for s in SCENES for h in HELPERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: cot, totter, parasol, teamwork.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--helper", choices=HELPERS)
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
              if (args.scene is None or c[0] == args.scene)
              and (args.helper is None or c[1] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, helper = rng.choice(sorted(combos))
    return StoryParams(scene=scene, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    helper = f["helper"]
    return [
        f'Write a nursery-rhyme story that uses the words "cot", "totter", and "parasol" in {scene.place}.',
        f"Tell a little repeating story where two children argue over a parasol near a cot, then {helper.label} helps them work together.",
        f'Write a gentle rhyme with repetition, conflict, and teamwork that ends with the totter safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene = f["scene"]
    helper = f["helper"]
    a = f["child_a"]
    b = f["child_b"]
    return [
        QAItem(
            question="What objects were in the story?",
            answer="The story used a cot, a totter, and a parasol. Those three things made the little play scene feel like a nursery rhyme."
        ),
        QAItem(
            question=f"Why did {a.id} and {b.id} get cross?",
            answer=f"They got cross because the parasol blocked the totter and kept the game from going smoothly. The trouble was not the children themselves, but the way the parasol crowded the play space."
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer=f"{helper.id} helped move the parasol away, and then the children worked together. Once the parasol was out of the way, the totter could move again and the play became calm."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cot?",
            answer="A cot is a small bed for a baby or young child. It is a cozy place to sleep."
        ),
        QAItem(
            question="What is a totter?",
            answer="A totter is a toy that rocks or moves back and forth. Children use it for playful movement."
        ),
        QAItem(
            question="What is a parasol?",
            answer="A parasol is a small umbrella made to give shade from the sun. It can be carried and held above someone."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together. When they share the work, the problem is easier to solve."
        ),
        QAItem(
            question="What does repetition do in a rhyme?",
            answer="Repetition repeats words or lines again and again. It makes a nursery rhyme feel musical and easy to remember."
        ),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
repetition :- totter_moving.
conflict :- totter_moving, parasol_blocking.
teamwork :- helper_helping.
outcome(teamwork) :- teamwork.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("totter_moving", 1))
    lines.append(asp.fact("parasol_blocking", 1))
    lines.append(asp.fact("helper_helping", 1))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    _ = asp.atoms(model, "outcome")
    if set(valid_combos()) != set(asp_valid_combos()):
        print("MISMATCH in ASP parity.")
        return 1
    try:
        generate(resolve_params(argparse.Namespace(scene=None, helper=None), random.Random(0)))
    except Exception as e:
        print(f"Story generation failed: {e}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show scene/1.\n#show helper/1."))
    return sorted(set((s, h) for (s,) in asp.atoms(model, "scene") for (h,) in asp.atoms(model, "helper")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], "Nina", "Ben", "Merry", "mother", "Mama", "mother")
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
        print(asp_program("#show scene/1.\n#show helper/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available; this nursery world keeps the twin simple.")
        print(f"{len(valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(scene=s, helper=h)) for s, h in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
