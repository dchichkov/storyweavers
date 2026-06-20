#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rob_quadracycle_quarter_magic_mystery.py
========================================================================

A standalone story world for a tiny mystery with a little magic:
someone tries to rob a market stall, a child's quadracycle gets involved,
a missing quarter becomes the clue, and a small spell-like trick helps
solve the puzzle.

The world is built as a causal simulation, not a frozen paragraph:
- typed entities with meters and memes
- state-driven beats that create a beginning, turn, and ending
- explicit reasonableness gates
- a Python check plus an inline ASP twin
- three distinct QA sets grounded in the simulated world
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    mood: str
    magic_hint: str
    clue_place: str
    clue_shadow: str
    safe_finish: str

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
class Tool:
    id: str
    label: str
    role: str
    can_take: bool = False
    can_lose: bool = False

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
class Clue:
    id: str
    label: str
    hidden: str
    found_by_magic: bool = False

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


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    if world.get("stall").meters["disturbed"] >= THRESHOLD and ("alert",) not in world.fired:
        world.fired.add(("alert",))
        for eid in ("child", "adult"):
            world.get(eid).memes["worry"] += 1
        out.append("__alert__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.get("quarter").meters["hidden"] >= THRESHOLD and world.get("magic").meters["glow"] >= THRESHOLD:
        sig = ("reveal",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.get("quarter").meters["found"] += 1
        world.get("child").memes["curiosity"] += 1
        out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("alert", "social", _r_alert), Rule("reveal", "magic", _r_reveal)]


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


def reasonableness_gate(scene: Scene, tool: Tool, clue: Clue) -> bool:
    return scene.id in SCENES and tool.id in TOOLS and clue.id in CLUES


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for tid, tool in TOOLS.items():
            for cid, clue in CLUES.items():
                if tool.can_take and clue.found_by_magic and scene.id == "market" and tool.id == "quadracycle" and clue.id == "quarter":
                    combos.append((sid, tid, cid))
                if tool.can_take and clue.found_by_magic and scene.id == "lantern" and tool.id == "quadracycle" and clue.id == "quarter":
                    combos.append((sid, tid, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    scene: str
    tool: str
    clue: str
    protagonist: str
    parent: str
    magic_kind: str
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


SCENES = {
    "market": Scene("market", "the busy market", "noisy", "a bright charm on the spokes", "under the cloth stall", "near the red crate", "The stall looked ordinary again."),
    "lantern": Scene("lantern", "the lantern shop", "quiet", "a spark in the air", "behind the lantern shelf", "under the dusty mat", "The shop fell still and neat."),
}
TOOLS = {
    "quadracycle": Tool("quadracycle", "quadracycle", "ride", can_take=True, can_lose=True),
}
CLUES = {
    "quarter": Clue("quarter", "quarter", "hidden in a slot", found_by_magic=True),
}
MAGIC = {
    "magic": "magic",
}
NAMES = ["Mia", "Noah", "Zoe", "Eli", "Ava", "Theo"]
PARENTS = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with magic and a quadracycle clue.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    if args.scene and args.tool and args.clue:
        if not valid_combos() or (args.scene, args.tool, args.clue) not in valid_combos():
            raise StoryError("No reasonable mystery exists for that combination.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.tool is None or c[1] == args.tool)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, tool, clue = rng.choice(sorted(combos))
    protagonist = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    magic_kind = "magic"
    return StoryParams(scene, tool, clue, protagonist, parent, magic_kind)


def _make_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("child", kind="character", type="girl" if params.protagonist in {"Mia", "Zoe", "Ava"} else "boy", role="mystery-solver"))
    hero.id = params.protagonist
    hero.label = params.protagonist
    parent = world.add(Entity("adult", kind="character", type=params.parent, label=f"the {params.parent}", role="helper"))
    stall = world.add(Entity("stall", type="stall", label="the stall"))
    quarter = world.add(Entity("quarter", type="coin", label="a quarter"))
    magic = world.add(Entity("magic", type="spark", label="magic", role="mystery"))
    world.facts["scene"] = SCENES[params.scene]
    world.facts["tool"] = TOOLS[params.tool]
    world.facts["clue"] = CLUES[params.clue]
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["stall"] = stall
    world.facts["quarter"] = quarter
    world.facts["magic"] = magic
    return world


def tell(world: World, params: StoryParams) -> None:
    scene = SCENES[params.scene]
    hero = world.get(params.protagonist)
    parent = world.get("adult")
    tool = TOOLS[params.tool]
    clue = CLUES[params.clue]
    stall = world.get("stall")
    quarter = world.get("quarter")
    magic = world.get("magic")

    world.say(f"At {scene.place}, {hero.id} noticed a strange little mystery.")
    world.say(f"{hero.id} rode {hero.pronoun('possessive')} {tool.label} past the stalls while {scene.magic_hint}.")
    world.say(f"Then {hero.id} saw that a quarter had gone missing from the story, and {hero.pronoun('possessive')} eyes got wide.")

    world.para()
    stall.meters["disturbed"] += 1
    world.get("quarter").meters["hidden"] += 1
    magic.meters["glow"] += 1
    propagate(world, narrate=False)
    world.say(f"Someone had tried to rob the stall, but the only clear clue was a tiny {clue.label} clue.")
    world.say(f"{hero.id} followed the glow of {scene.magic_hint} and looked where the clue said to look.")

    world.para()
    quarter.meters["found"] += 1
    world.say(f"{parent.label_word.capitalize()} came close and listened.")
    world.say(f"{hero.id} pointed under {scene.clue_place} and found the missing quarter hidden there.")
    world.say(f"It was a small theft, a small clue, and a clever bit of magic, but it solved the mystery.")

    world.para()
    world.say(f"In the end, the stall was calm, the quarter was back where it belonged, and {hero.id} smiled at {scene.safe_finish}")
    world.facts["outcome"] = "solved"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "rob", "quadracycle", and "quarter", and has a little magic.',
        f"Tell a gentle mystery where {f['hero'].id} rides a quadracycle, notices a missing quarter, and uses magic to solve the clue.",
        f'Write a child-friendly mystery with the word "quarter" in it, where someone tries to rob a stall and a magic clue helps find what was missing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    scene = world.facts["scene"]
    quarter = world.facts["quarter"]
    return [
        QAItem(question="Who solved the mystery?", answer=f"{hero.id} solved it with a careful look and a little magic."),
        QAItem(question="What was missing?", answer=f"A quarter was missing, and that tiny clue helped point the way to the answer. It was hidden before {hero.id} found it."),
        QAItem(question=f"Where did {hero.id} look for the clue?", answer=f"{hero.id} looked under {scene.clue_place} and found the quarter there. {parent.label_word.capitalize()} stayed nearby to help."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quadracycle?", answer="A quadracycle is a ride with four wheels that a child can pedal or push along."),
        QAItem(question="What is a quarter?", answer="A quarter is a small coin. It is money, and people can keep it in a pocket or a coin slot."),
        QAItem(question="What does rob mean?", answer="To rob means to take something that does not belong to you. It is wrong, so a story can use it as a mystery clue or a problem."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market", "quadracycle", "quarter", "Mia", "mother", "magic"),
    StoryParams("lantern", "quadracycle", "quarter", "Noah", "father", "magic"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("can_take", "quadracycle"))
    lines.append(asp.fact("found_by_magic", "quarter"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, C) :- scene(S), tool(T), clue(C), can_take(T), found_by_magic(C), S = market, T = quadracycle, C = quarter.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magical mystery about rob, quadracycle, and quarter.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if not combos:
        raise StoryError("No valid story combination exists.")
    combos = [c for c in combos if (args.scene is None or c[0] == args.scene) and (args.tool is None or c[1] == args.tool) and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, tool, clue = rng.choice(sorted(combos))
    protagonist = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(scene=scene, tool=tool, clue=clue, protagonist=protagonist, parent=parent, magic_kind="magic")


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
        for combo in asp_valid_combos():
            print("  ", combo)
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
