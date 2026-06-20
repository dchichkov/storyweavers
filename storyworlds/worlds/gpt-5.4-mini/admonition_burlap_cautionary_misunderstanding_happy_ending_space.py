#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/admonition_burlap_cautionary_misunderstanding_happy_ending_space.py
===================================================================================================

A standalone story world for a small Space Adventure tale:
a child explorers' misunderstanding around a burlap sack, a calm admonition from
a grown-up, a brief risky moment, and a happy ending that proves the safer choice.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- state-driven prose that changes with the simulation
- a reasonableness gate plus an inline ASP twin
- QA sets grounded in the world state, not by parsing rendered text

Seed words and features:
- admonition
- burlap
- cautionary
- misunderstanding
- happy ending
- style: Space Adventure
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
class Module:
    id: str
    label: str
    place: str
    dark: str
    keyword: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    unsafe: bool = False
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
class Remedy:
    id: str
    label: str
    phrase: str
    use: str
    power: int
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["risk"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "child":
                kid.memes["unease"] += 1
        out.append("__worry__")
    return out


RULES = [Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def module_at_risk(mod: Module, tool: Tool) -> bool:
    return tool.unsafe and mod.id == "hangar" and "cargo" in tool.tags


def can_remedy(remedy: Remedy, delay: int) -> bool:
    return remedy.power >= 1 + delay


def warn(world: World, parent: Entity, child: Entity, tool: Tool, mod: Module) -> None:
    world.say(
        f'{parent.label_word.capitalize()} gave an admonition: "{tool.label} is not '
        f'a toy, and the {mod.label} is no place for it."'
    )
    child.memes["curiosity"] += 1


def misread(world: World, child: Entity, tool: Tool, mod: Module) -> None:
    child.memes["misunderstanding"] += 1
    world.say(
        f'{child.id} peered at the {tool.label} and smiled. "It looks like a '
        f'handy space helper," {child.pronoun()} said, but {child.pronoun("possessive")} '
        f'idea was wrong.'
    )
    world.say(
        f'{child.id} thought the burlap would catch the {mod.dark} drifts, like a '
        f'net for floating dust.'
    )


def act(world: World, child: Entity, tool: Tool, mod: Module) -> None:
    child.memes["defiance"] += 1
    child.meters["risk"] += 1
    world.say(
        f'{child.id} picked up the burlap {tool.label} anyway and swung it open. '
        f'For a moment it fluttered like a tiny sail inside the ship.'
    )
    propagate(world, narrate=False)


def alarm(world: World, sibling: Entity, child: Entity, mod: Module) -> None:
    sibling.memes["fear"] += 1
    world.say(f'"{child.id}! The {mod.label}!" {sibling.id} shouted.')
    world.say(f'"{world.facts["parent"].label_word.upper()}!"')


def rescue(world: World, parent: Entity, remedy: Remedy, mod: Module, delay: int) -> None:
    if can_remedy(remedy, delay):
        world.get(mod.id).meters["risk"] = 0.0
        body = remedy.use.replace("{module}", mod.label)
        world.say(
            f'{world.facts["parent"].label_word.capitalize()} rushed in and {body}.'
        )
        world.say(
            f'The {mod.dark} settled down, and the little ship was safe again.'
        )
    else:
        world.say(
            f'{world.facts["parent"].label_word.capitalize()} rushed in, but the '
            f'problem was already too big for that quick fix.'
        )


def lesson(world: World, parent: Entity, child: Entity, sibling: Entity, tool: Tool) -> None:
    child.memes["relief"] += 1
    sibling.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "I am not angry '
        f'about the scare," {parent.pronoun()} said. "I am glad you called me. '
        f'But remember the admonition: {tool.label} belongs with grown-ups."'
    )
    world.say(
        f'{child.id} and {sibling.id} nodded and promised to listen next time.'
    )


def safe_finish(world: World, parent: Entity, child: Entity, sibling: Entity, remedy: Remedy) -> None:
    child.memes["joy"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"The next morning, {parent.label_word.capitalize()} brought them {remedy.phrase}. "
        f'It could do the same job safely.'
    )
    world.say(
        f'{child.id} used the {remedy.label}, {sibling.id} held the door, and '
        f'the little crew laughed as the ship glowed bright and calm.'
    )
    world.say(
        "This time, the space adventure ended happily, with the burlap tucked away "
        "and the stars shining through the window."
    )


def tell(module: Module, tool: Tool, remedy: Remedy, delay: int = 0,
         child_name: str = "Mila", sibling_name: str = "Toby",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(child_name, kind="character", type="girl", role="child"))
    sibling = world.add(Entity(sibling_name, kind="character", type="boy", role="sibling"))
    parent = world.add(Entity("Parent", kind="character", type=parent_type, role="parent"))
    world.facts["parent"] = parent
    world.add(Entity(module.id, type="place", label=module.label))
    world.facts["module"] = module
    world.facts["tool"] = tool
    world.facts["remedy"] = remedy
    world.facts["delay"] = delay

    child.memes["curiosity"] = 1
    sibling.memes["curiosity"] = 1

    world.say(
        f'On a quiet afternoon aboard the little starship, {child.id} and '
        f'{sibling.id} turned the {module.label} into a pretend mission. '
        f'Their blankets were seats, their flashlights were stars, and the '
        f'floor hummed like a road to the moon.'
    )
    world.say(
        f'Then {child.id} noticed {tool.phrase} in a storage crate near the '
        f'{module.place}. It was only burlap, but it looked important.'
    )

    world.para()
    warn(world, parent, child, tool, module)
    misread(world, child, tool, module)
    act(world, child, tool, module)
    alarm(world, sibling, child, module)

    world.para()
    rescue(world, parent, remedy, module, delay)
    lesson(world, parent, child, sibling, tool)
    world.para()
    safe_finish(world, parent, child, sibling, remedy)

    world.facts.update(
        child=child,
        sibling=sibling,
        outcome="happy",
        risk=child.meters["risk"],
    )
    return world


MODULES = {
    "hangar": Module("hangar", "star hangar", "hangar bay", "dusty hatch", "dust", {"cargo"}),
    "bridge": Module("bridge", "bridge deck", "bridge deck", "glimmering screen", "lights", {"cargo"}),
    "cabin": Module("cabin", "sleep cabin", "sleep cabin", "soft bunk shadow", "shadows", set()),
}

TOOLS = {
    "burlap_sack": Tool("burlap_sack", "burlap sack", "a burlap sack", "carry moon rocks", unsafe=True, tags={"cargo"}),
    "burlap_sheet": Tool("burlap_sheet", "burlap sheet", "a burlap sheet", "cover crates", unsafe=True, tags={"cargo"}),
}

REMEDIES = {
    "net": Remedy("net", "cargo net", "a cargo net", "catch drifting dust", power=2, tags={"cargo"}),
    "cloth": Remedy("cloth", "safety cloth", "a safety cloth", "cover the drift", power=1, tags={"cargo"}),
    "seal": Remedy("seal", "hatch seal", "a hatch seal", "seal the hatch", power=3, tags={"cargo"}),
}

GIRLS = ["Mila", "Nia", "Zoe", "Ava", "Luna", "Ivy"]
BOYS = ["Toby", "Leo", "Max", "Finn", "Eli", "Noah"]


@dataclass
@dataclass
class StoryParams:
    module: str
    tool: str
    remedy: str
    delay: int
    child: str = "Mila"
    sibling: str = "Toby"
    parent: str = "mother"
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
    for m in MODULES:
        for t in TOOLS:
            for r in REMEDIES:
                if module_at_risk(MODULES[m], TOOLS[t]) and can_remedy(REMEDIES[r], 0):
                    out.append((m, t, r))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a cautionary misunderstanding.")
    ap.add_argument("--module", choices=MODULES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--child")
    ap.add_argument("--sibling")
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
    if args.module and args.tool:
        if not module_at_risk(MODULES[args.module], TOOLS[args.tool]):
            raise StoryError("(No story: that tool would not create a real misunderstanding in that module.)")
    combos = [c for c in valid_combos()
              if (args.module is None or c[0] == args.module)
              and (args.tool is None or c[1] == args.tool)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    module, tool, remedy = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRLS)
    sibling = args.sibling or rng.choice(BOYS)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay
    return StoryParams(module, tool, remedy, delay, child, sibling, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary space adventure story that includes the words '
        f'"admonition" and "burlap".',
        f'Tell a story where {f["child"].id} misunderstands a burlap tool in a '
        f'starship module, ignores an admonition at first, then ends happily.',
        f'Write a child-friendly space story with a brief mistake, a calm grown-up '
        f'response, and a happy ending around a burlap sack.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, sibling, parent = f["child"], f["sibling"], f["parent"]
    mod, tool, remedy = f["module"], f["tool"], f["remedy"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {sibling.id}, two little space explorers, and {parent.label_word} who stepped in to help."),
        ("What did {0} misunderstand?".format(child.id),
         f"{child.id} thought the burlap {tool.label} was a handy space helper. It was really just storage, and the idea was unsafe in the {mod.label}."),
        ("What did the grown-up say?",
         f"{parent.label_word.capitalize()} gave an admonition and warned that {tool.label} was not a toy. {parent.label_word.capitalize()} wanted them to stay safe in the {mod.label}."),
        ("How did the problem get fixed?",
         f"{parent.label_word.capitalize()} used {remedy.phrase} to settle the problem, and then everyone chose the safer plan. That let the adventure continue without danger."),
        ("How did the story end?",
         f"It ended happily. The children learned from the mistake, used the safer gear, and kept exploring under the stars."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is burlap?",
         "Burlap is a rough cloth, often used for sacks and bags. It is useful for carrying things, but it is not a toy."),
        ("What is an admonition?",
         "An admonition is a firm warning or reminder. A grown-up gives one to help someone stay safe."),
        ("What is a starship hangar?",
         "A starship hangar is a big room where ships are kept, fixed, or loaded. It is usually full of tools and gear."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hangar", "burlap_sack", "net", 0, "Mila", "Toby", "mother"),
    StoryParams("bridge", "burlap_sheet", "seal", 1, "Ava", "Leo", "father"),
    StoryParams("hangar", "burlap_sheet", "cloth", 0, "Nia", "Finn", "mother"),
]


def explain_response(remedy: Remedy) -> str:
    return f"(Refusing remedy '{remedy.id}': it is too weak for the safer happy ending we want.)"


ASP_RULES = r"""
risk(M, T) :- module(M), tool(T), unsafe(T), cargo(T).
valid(M, T, R) :- risk(M, T), remedy(R), power(R, P), P >= 1.
outcome(happy) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MODULES:
        lines.append(asp.fact("module", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.unsafe:
            lines.append(asp.fact("unsafe", tid))
        for tag in t.tags:
            lines.append(asp.fact("cargo", tid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("seed_word", "admonition"))
    lines.append(asp.fact("seed_word", "burlap"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _r
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _r.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: default generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        MODULES[params.module],
        TOOLS[params.tool],
        REMEDIES[params.remedy],
        params.delay,
        params.child,
        params.sibling,
        params.parent,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
