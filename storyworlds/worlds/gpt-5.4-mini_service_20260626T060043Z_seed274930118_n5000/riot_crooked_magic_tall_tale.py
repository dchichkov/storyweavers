#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/riot_crooked_magic_tall_tale.py
===============================================================================================================

A tall-tale story world about a small town, a crooked magical thing, and the
uproar it causes before someone clever sets it right.

Seed tale:
---
In a tiny prairie town, Old Zeke found a crooked magic horn in a trunk under
the schoolhouse floorboards. The horn was said to wake up the wind, and when
Zeke blew it, every gate in town swung open and every tin pail began to sing.

Soon the whole town was in a riot of noise. Chickens ran backward, hats flew
off heads, and the mayor shouted over the racket. Folks thought the horn was
cursed, but Zeke could see it was only crooked: its bend made the magic spill
every which way.

So Zeke climbed the water tower, tied the horn to a long string, and used the
string to steady its bend. When he blew again, the wind came out tidy as a
whistle, the gates shut soft, and the town settled down with a laugh.

Causal world model:
---
- A crooked magical object leaks force when used while bent.
- Leaked magic boosts chaos, noise, and surprise in nearby people.
- A steadying method can align the object and reduce chaos.
- Once the object is straightened or braced, the same magic becomes helpful.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    crooked: bool = False
    magical: bool = False
    fixed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "ma", "aunt"}
        male = {"boy", "man", "father", "pa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    vibe: str
    supports_magic: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    result: str
    steady: str
    fits: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    tool: str
    object: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.place)
        clone.entities = dataclasses.replace(self) if False else {}
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _narrate_world_surge(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters.get("chaos", 0) >= THRESHOLD and ("surge", e.id) not in world.fired:
            world.fired.add(("surge", e.id))
            e.memes["alarm"] = e.memes.get("alarm", 0) + 1
            out.append(f"{e.label or e.id} got swept up in the uproar.")
    return out


def _narrate_magic_leak(world: World) -> list[str]:
    out = []
    obj = next((e for e in world.entities.values() if e.magical), None)
    if not obj:
        return out
    if obj.crooked and obj.meters.get("used", 0) >= THRESHOLD and ("leak", obj.id) not in world.fired:
        world.fired.add(("leak", obj.id))
        for e in world.entities.values():
            if e.kind == "character":
                e.meters["noise"] = e.meters.get("noise", 0) + 1
                e.meters["chaos"] = e.meters.get("chaos", 0) + 1
                e.memes["startle"] = e.memes.get("startle", 0) + 1
        out.append(f"The crooked magic {obj.label} spilled its power all over the place.")
    return out


def _narrate_fix(world: World) -> list[str]:
    out = []
    obj = next((e for e in world.entities.values() if e.magical), None)
    if not obj:
        return out
    if obj.fixed and ("fix", obj.id) not in world.fired:
        world.fired.add(("fix", obj.id))
        for e in world.entities.values():
            if e.kind == "character":
                e.meters["chaos"] = max(0.0, e.meters.get("chaos", 0) - 1)
                e.meters["noise"] = max(0.0, e.meters.get("noise", 0) - 1)
                e.memes["relief"] = e.memes.get("relief", 0) + 1
        out.append(f"The magic settled down and started behaving itself.")
    return out


RULES = [_narrate_magic_leak, _narrate_world_surge, _narrate_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def may_use(tool: Tool, magical_obj: Entity) -> bool:
    return magical_obj.magical and tool.id in tool.fits


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_kind,
        label=params.hero_name,
        traits=["tall-tale", "steady"],
        meters={"noise": 0.0, "chaos": 0.0},
        memes={"curiosity": 1.0, "courage": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_kind,
        label=params.helper_name,
        traits=["wise", "laughing"],
        meters={"noise": 0.0, "chaos": 0.0},
        memes={"calm": 1.0},
    ))
    obj_cfg = OBJECTS[params.object]
    magic_obj = world.add(Entity(
        id="magic_obj",
        kind="thing",
        type=obj_cfg["type"],
        label=obj_cfg["label"],
        phrase=obj_cfg["phrase"],
        crooked=True,
        magical=True,
        fixed=False,
        meters={"used": 0.0},
    ))
    tool = TOOLS[params.tool]
    fix_tool = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        meters={},
    ))
    world.facts.update(hero=hero, helper=helper, magic_obj=magic_obj, tool=tool, fix_tool=fix_tool, place=place)

    world.say(f"{hero.id} lived where the {place.name} felt bigger than the sky.")
    world.say(f"One day, {hero.id} found {magic_obj.phrase}.")
    world.say(f"{magic_obj.label.capitalize()} looked { 'crooked' if magic_obj.crooked else 'straight' } and full of old-time magic.")
    world.para()
    world.say(f"{hero.id} meant to use {magic_obj.label} at the {place.name}, because {place.vibe}.")
    world.say(f"But the moment {hero.pronoun()} gave {magic_obj.label} a try, the air began to quiver like a fiddle string.")
    magic_obj.meters["used"] += 1
    propagate(world)
    world.para()
    world.say(f"{helper.id} squinted up and said that a crooked thing can throw a whole town into a riot of noise.")
    world.say(f"So {hero.id} fetched {fix_tool.label} and used it to {tool.method}.")
    magic_obj.crooked = False
    magic_obj.fixed = True
    world.say(f"That made the {magic_obj.label} {tool.steady}.")
    propagate(world)
    world.para()
    world.say(f"Then {hero.id} tried again, and this time the magic came out {tool.result}.")
    world.say(f"The {place.name} quieted down, and the whole wide place looked happy to have its tall tale back.")
    world.facts["resolved"] = True
    return world


PLACES = {
    "town_square": Place(name="town square", vibe="everybody came there to swap news"),
    "schoolhouse": Place(name="schoolhouse", vibe="the floorboards kept every secret"),
    "riverbank": Place(name="riverbank", vibe="the wind loved to show off there"),
    "fairground": Place(name="fairground", vibe="the lanterns made a grand racket after dark"),
}

OBJECTS = {
    "horn": {"label": "horn", "phrase": "a crooked magic horn", "type": "instrument"},
    "fiddle": {"label": "fiddle", "phrase": "a crooked magic fiddle", "type": "instrument"},
    "lantern": {"label": "lantern", "phrase": "a crooked magic lantern", "type": "light"},
    "shovel": {"label": "shovel", "phrase": "a crooked magic shovel", "type": "tool"},
}

TOOLS = {
    "string": Tool(id="string", label="a long string", phrase="a long string", method="steady its bend", result="tidy as a whistle", steady="stopped wobbling", fits={"string"}),
    "peg": Tool(id="peg", label="a wooden peg", phrase="a wooden peg", method="brace its neck straight", result="clear and bright", steady="held straight", fits={"peg"}),
    "brace": Tool(id="brace", label="an iron brace", phrase="an iron brace", method="hold it steady", result="strong and true", steady="stood firm", fits={"brace"}),
}


GIRL_NAMES = ["Mabel", "Lottie", "Etta", "Nell", "Ruby"]
BOY_NAMES = ["Zeke", "Bert", "Cal", "Jude", "Hank"]
HELPER_NAMES = ["Aunt Sis", "Old Mose", "Mrs. Grit", "Uncle Ben", "Mayor Pruitt"]


@dataclass
class StoryShape:
    opening: str
    turn: str
    ending: str


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child about a {f["magic_obj"].label} that is crooked and causes a riot of noise.',
        f"Tell a funny frontier story where {f['hero'].id} finds {f['magic_obj'].phrase} and learns to fix its crooked magic.",
        f'Create a short magical tall tale that uses the word "crooked" and ends with the town quieting down again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    magic_obj = f["magic_obj"]
    tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} find in the {place.name}?",
            answer=f"{hero.id} found {magic_obj.phrase}, and it was crooked and magical.",
        ),
        QAItem(
            question=f"Why did the town start making such a riot of noise?",
            answer=f"The riot of noise began because the crooked magic in the {magic_obj.label} spilled everywhere when {hero.id} used it.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} calm the magic down?",
            answer=f"They used {tool.label} to {tool.method}, which made the {magic_obj.label} {tool.steady}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the {place.name} was quiet again and the magic came out {tool.result}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does crooked mean?",
            answer="Crooked means bent or not straight.",
        ),
        QAItem(
            question="What is a magical thing in a tall tale often like?",
            answer="In a tall tale, a magical thing can seem larger than life and can cause very big, funny trouble.",
        ),
        QAItem(
            question="What is a riot of noise?",
            answer="A riot of noise is a big noisy uproar where lots of things happen at once.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} crooked={e.crooked} magical={e.magical} fixed={e.fixed} "
            f"meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.supports_magic:
            lines.append(asp.fact("supports_magic", pid))
    for oid, cfg in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("label", oid, cfg["label"]))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("method", tid, tool.method))
    return "\n".join(lines)


ASP_RULES = r"""
crooked_object(O) :- object(O), crooked(O).
magical_object(O) :- object(O), magical(O).
uproar(O) :- crooked_object(O), used(O).
fixed(O) :- magical_object(O), repaired(O).
calm(O) :- fixed(O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: crooked magic and a town-sized uproar.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-kind", choices=["boy", "girl"], dest="hero_kind")
    ap.add_argument("--helper-kind", choices=["man", "woman"], dest="helper_kind")
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
    place = args.place or rng.choice(list(PLACES))
    tool = args.tool or rng.choice(list(TOOLS))
    obj = args.object_ or rng.choice(list(OBJECTS))
    hero_kind = args.hero_kind or rng.choice(["boy", "girl"])
    hero_name = args.name or rng.choice(BOY_NAMES if hero_kind == "boy" else GIRL_NAMES)
    helper_kind = args.helper_kind or rng.choice(["man", "woman"])
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, tool=tool, object=obj, hero_name=hero_name, hero_kind=hero_kind, helper_name=helper_name, helper_kind=helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="town_square", tool="string", object="horn", hero_name="Zeke", hero_kind="boy", helper_name="Old Mose", helper_kind="man"),
    StoryParams(place="schoolhouse", tool="peg", object="fiddle", hero_name="Mabel", hero_kind="girl", helper_name="Aunt Sis", helper_kind="woman"),
    StoryParams(place="fairground", tool="brace", object="lantern", hero_name="Hank", hero_kind="boy", helper_name="Mayor Pruitt", helper_kind="woman"),
]


def valid_combo(params: StoryParams) -> bool:
    return params.tool in TOOLS and params.object in OBJECTS and params.place in PLACES


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
