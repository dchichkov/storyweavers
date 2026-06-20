#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/carve_gerund_bump_dim_lesson_learned_teamwork.py
=================================================================================

A small superhero story world: a child hero and a teammate try to carve a
training emblem in a secret hideout, accidentally bump a dim lantern, learn to
work together, and finish with a brighter, safer solution.

This world keeps the classical Storyweavers shape:
- typed entities with meters and memes
- state-driven story generation
- three QA sets from world state
- Python validity checks plus an inline ASP twin
- --verify smoke tests that exercise normal generation
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
class Tool:
    id: str
    label: str
    verb: str
    noun: str
    danger: str
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
class DimThing:
    id: str
    label: str
    noun: str
    can_bump: bool = True
    dims: int = 1
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
class TeamAid:
    id: str
    label: str
    noun: str
    glow: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    hero: str
    teammate: str
    tool: str
    target: str
    aid: str
    parent: str
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


TOOLS = {
    "carve_gerund": Tool(
        "carve_gerund", "carve tool", "carving", "carved emblem", "can nick a wall",
        {"carve-gerund", "carve"},
    ),
    "chalk_marker": Tool(
        "chalk_marker", "chalk marker", "drawing", "chalk outline", "can smudge",
        {"chalk"},
    ),
    "paint_brush": Tool(
        "paint_brush", "paint brush", "painting", "painted badge", "can drip",
        {"paint"},
    ),
}

DIM_THINGS = {
    "bump_dim": DimThing(
        "bump_dim", "bump-dim lantern", "dim lantern", True, 2, {"bump-dim", "dim"},
    ),
    "weak_window": DimThing(
        "weak_window", "weak window lamp", "lamp", True, 1, {"dim"},
    ),
    "shadow_panel": DimThing(
        "shadow_panel", "shadow panel", "panel", False, 0, {"shadow"},
    ),
}

AIDS = {
    "teamwork": TeamAid("teamwork", "teamwork beacon", "beacon", "glowed like a tiny star", {"teamwork"}),
    "flash_belt": TeamAid("flash_belt", "flash belt", "belt light", "shone white and steady", {"flash"}),
    "signal_gloves": TeamAid("signal_gloves", "signal gloves", "gloves", "blinked together in bright dots", {"signal"}),
}

NAMES = ["Nova", "Rex", "Maya", "Kai", "Iris", "Zane", "Tessa", "Leo"]
TRAITS = ["brave", "careful", "clever", "steady", "kind"]
PARENT_TYPES = ["mother", "father"]


def reasonableness_ok(tool: Tool, target: DimThing, aid: TeamAid) -> bool:
    return tool.id == "carve_gerund" and target.can_bump and aid.id == "teamwork"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid, tool in TOOLS.items():
        for did, dim in DIM_THINGS.items():
            for aid in AIDS.values():
                if reasonableness_ok(tool, dim, aid):
                    combos.append((tid, did, aid.id))
    return combos


def bump_happens(tool: Tool, target: DimThing) -> bool:
    return tool.id == "carve_gerund" and target.dims >= 1


def fix_works(aid: TeamAid, target: DimThing) -> bool:
    return aid.id == "teamwork" and target.dims >= 1


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["shaken"] < THRESHOLD:
            continue
        sig = ("bump", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["dim"] += 1
        out.append("__bump__")
    return out


CAUSAL_RULES = [_r_bump]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, tool: Tool, target: DimThing) -> dict:
    sim = world.copy()
    sim.get("hero").meters["shaken"] += 1
    propagate(sim, narrate=False)
    return {"dim": sim.get("room").meters["dim"]}


def setup(world: World, hero: Entity, teammate: Entity, parent: Entity, tool: Tool, target: DimThing) -> None:
    hero.memes["hope"] += 1
    teammate.memes["hope"] += 1
    world.say(
        f"At the Secret Star HQ, {hero.id} and {teammate.id} were planning a hero job. "
        f"They wanted to {tool.verb} a new team badge while the {target.noun} buzzed softly in the corner."
    )
    world.say(
        f'"Let’s make it shine," {hero.id} said, and {teammate.id} nodded as {parent.label_word} watched nearby.'
    )


def warn(world: World, teammate: Entity, hero: Entity, tool: Tool, target: DimThing, parent: Entity) -> None:
    pred = predict(world, tool, target)
    teammate.memes["caution"] += 1
    world.facts["predicted_dim"] = pred["dim"]
    world.say(
        f'{teammate.id} pointed at the {target.noun}. "{hero.id}, if you keep {tool.verb}, '
        f'the room will get even dimmer, and we will not be able to see the badge well."'
    )
    if pred["dim"] >= 1:
        world.say(f'{parent.label_word.capitalize()} agreed. "Teamwork means noticing trouble before it grows."')


def act(world: World, hero: Entity, teammate: Entity, tool: Tool, target: DimThing) -> None:
    hero.memes["boldness"] += 1
    hero.meters["shaken"] += 1
    world.say(
        f'{hero.id} tried to keep going, but the tool bumped the {target.noun}. '
        f'It wobbled once, and the light turned fuzzier.'
    )
    propagate(world, narrate=False)
    world.get("room").meters["dim"] += 1


def teamwork_turn(world: World, teammate: Entity, hero: Entity, aid: TeamAid) -> None:
    hero.memes["trust"] += 1
    teammate.memes["trust"] += 1
    world.say(
        f'Then {teammate.id} held up the {aid.label}. Its {aid.glow}, and the two heroes worked side by side.'
    )


def learn_lesson(world: World, parent: Entity, hero: Entity, teammate: Entity, tool: Tool, target: DimThing) -> None:
    hero.memes["lesson_learned"] += 1
    teammate.memes["lesson_learned"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and said, "
        f'"A hero can be strong and still slow down. That is how teamwork keeps the mission safe."'
    )
    world.say(
        f'{hero.id} and {teammate.id} fixed the badge together, and the {target.noun} stayed steady instead of wobbling again.'
    )
    world.say(
        f'By the end, the carved team symbol shone proudly on the wall, proof that {tool.noun} and teamwork worked best together.'
    )


def tell(hero_name: str, teammate_name: str, parent_type: str, tool: Tool, target: DimThing, aid: TeamAid, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Rex", "Kai", "Zane", "Leo"} else "girl", role="hero", traits=[trait]))
    teammate = world.add(Entity(id=teammate_name, kind="character", type="girl" if teammate_name in {"Maya", "Iris", "Tessa", "Nova"} else "boy", role="teammate", traits=["careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="their mentor"))
    room = world.add(Entity(id="room", type="room", label="the hideout"))
    room.meters["dim"] = 0.0
    world.facts.update(hero=hero, teammate=teammate, parent=parent, tool=tool, target=target, aid=aid, room=room)

    setup(world, hero, teammate, parent, tool, target)
    world.para()
    warn(world, teammate, hero, tool, target, parent)
    act(world, hero, teammate, tool, target)
    world.para()
    teamwork_turn(world, teammate, hero, aid)
    learn_lesson(world, parent, hero, teammate, tool, target)
    world.facts["outcome"] = "lesson_learned"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a superhero story for a young child that includes the words "carve-gerund" and "bump-dim".',
        f"Tell a teamwork story where {f['hero'].id} and {f['teammate'].id} solve a dim-room problem while carving a badge.",
        "Write a gentle hero story where the characters learn a lesson about teamwork and finish with a bright ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, teammate, parent = f["hero"], f["teammate"], f["parent"]
    tool, target, aid = f["tool"], f["target"], f["aid"]
    return [
        QAItem(
            question="What problem did the heroes have?",
            answer=f"They were trying to make a team badge, but the {target.noun} made the room dimmer when it got bumped. That meant they had to slow down and work together.",
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"{teammate.id} noticed the trouble first and brought the {aid.noun}. Then {hero.id} and {teammate.id} worked side by side, which made the mission safe and steady.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=f"They learned that a hero should not rush alone when the room gets dark. Using {tool.noun} and teamwork together made the best result.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together toward one goal. It can make a hard job safer and easier.",
        ),
        QAItem(
            question="Why can a dim room be a problem?",
            answer="A dim room is hard to see in, so people may bump into things or make mistakes. Bright light helps them stay safe.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives out light so people can see in dark places. It helps them keep working without stumbling around.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World knowledge questions ==")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Nova", "Rex", "mother", TOOLS["carve_gerund"], DIM_THINGS["bump_dim"], AIDS["teamwork"]),
    StoryParams("Maya", "Kai", "father", TOOLS["carve_gerund"], DIM_THINGS["weak_window"], AIDS["teamwork"]),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero teamwork story world with a carved badge and a dim room.")
    ap.add_argument("--hero")
    ap.add_argument("--teammate")
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=DIM_THINGS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.tool and args.target and args.aid:
        if not reasonableness_ok(TOOLS[args.tool], DIM_THINGS[args.target], AIDS[args.aid]):
            raise StoryError("This story needs the carving tool, a bumpable dim thing, and teamwork as the fix.")
    combos = [c for c in valid_combos()
              if (args.tool is None or c[0] == args.tool)
              and (args.target is None or c[1] == args.target)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tool_id, target_id, aid_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    teammate = args.teammate or rng.choice([n for n in NAMES if n != hero])
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(hero, teammate, parent, TOOLS[tool_id], DIM_THINGS[target_id], AIDS[aid_id], trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.hero, params.teammate, params.parent, params.tool, params.target, params.aid, params.trait)
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


ASP_RULES = r"""
valid(Tool, Target, Aid) :- carve_tool(Tool), bumpable(Target), teamwork_aid(Aid).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for tid in TOOLS:
        lines.append(asp.fact("carve_tool", tid))
    for did, d in DIM_THINGS.items():
        if d.can_bump:
            lines.append(asp.fact("bumpable", did))
    for aid in AIDS:
        lines.append(asp.fact("teamwork_aid", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity for valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for tool, target, aid in combos:
            print(f"  {tool:14} {target:12} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.teammate}: {p.tool.id} near {p.target.id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
