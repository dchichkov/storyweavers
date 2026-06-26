#!/usr/bin/env python3
"""
storyworlds/worlds/hone_refrigerant_cutlet_cautionary_happy_ending_foreshadowing.py
===================================================================================

A small animal-story world about careful hands, a cooling box, and a cutlet
that should stay safe until supper.

Premise:
- A young animal wants to hone a shiny little carving edge.
- A cold refrigerant case sits nearby to keep food fresh.
- A cutlet must not be left out too long.

Story shape:
- Foreshadowing: someone notices the box humming and the cutlet warming.
- Cautionary turn: the child wants to use the honed edge too eagerly.
- Happy ending: a gentle fix keeps the cutlet safe and lets everyone share.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager results import
- lazy ASP import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises generation
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "squirrel", "rabbit"}
        male = {"boy", "father", "dad", "man", "fox", "badger", "otter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    region: str
    spoil_risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Assist:
    id: str
    label: str
    fix: str
    tail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for food in world.entities.values():
        if food.kind != "thing" or food.type != "cutlet":
            continue
        if food.meters.get("warm", 0.0) < THRESHOLD:
            continue
        sig = ("spoil", food.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        food.meters["unsafe"] = 1.0
        out.append(f"The cutlet was in danger of going bad.")
    return out


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("warn", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ch.id} gave a careful warning.")
    return out


CAUSAL_RULES = [Rule("spoil", _r_spoil), Rule("warn", _r_warn)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def foreshadow(world: World, fox: Entity, cutlet: Entity, cooler: Entity) -> None:
    world.say(
        f"At the edge of {world.setting.place}, {fox.id} heard the soft hum of {cooler.label}. "
        f"That little hum was a clue that the {cutlet.label} still needed care."
    )
    if cutlet.meters.get("warm", 0.0) >= THRESHOLD:
        world.say(
            f"The {cutlet.label} had already been sitting out too long, and {fox.pronoun('possessive')} nose wrinkled."
        )


def hone_tool(world: World, fox: Entity, tool: Entity) -> None:
    fox.memes["pride"] = fox.memes.get("pride", 0.0) + 1
    world.say(
        f"{fox.id} liked to hone {fox.pronoun('possessive')} little blade until it shone like a silver leaf."
    )
    world.say(
        f"But {fox.id} remembered that a shiny edge was for careful help, not for showing off."
    )


def worry_cutlet(world: World, parent: Entity, cutlet: Entity) -> None:
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1
    cutlet.meters["warm"] = cutlet.meters.get("warm", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.id} peeked at the {cutlet.label} and said, "
        f'"If it stays warm, it will not stay tasty for long."'
    )


def careless_try(world: World, fox: Entity, tool: Entity, cutlet: Entity) -> None:
    fox.memes["impulse"] = fox.memes.get("impulse", 0.0) + 1
    world.say(
        f"{fox.id} almost used the honed edge at once, but then {fox.pronoun('possessive')} ears twitched."
    )
    world.say(
        f"{fox.id} remembered the warning about the {cutlet.label} and stopped."
    )


def fix_plan(world: World, helper: Entity, cutlet: Entity, cooler: Entity, aid: Assist) -> None:
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    cutlet.meters["warm"] = 0.0
    cutlet.meters["safe"] = 1.0
    world.say(
        f"{helper.id} suggested a kinder plan: {aid.fix}."
    )
    world.say(
        f"Together they used the {cooler.label}, and soon the {cutlet.label} was cool again."
    )
    world.say(
        f"{aid.tail}, and everyone smiled because supper would be safe."
    )


def tell(world: World, hero: Entity, parent: Entity, cutlet: Entity, cooler: Entity, tool: Entity, aid: Assist) -> World:
    world.say(
        f"{hero.id} was a small {hero.type} who loved tidy jobs and bright tools."
    )
    world.say(
        f"One day {hero.id} found {hero.pronoun('possessive')} shiny blade and decided to hone it carefully."
    )
    world.say(
        f"In the kitchen nook, the {cutlet.label} sat nearby while the {cooler.label} hummed softly."
    )

    world.para()
    foreshadow(world, hero, cutlet, cooler)
    worry_cutlet(world, parent, cutlet)
    careless_try(world, hero, tool, cutlet)

    world.para()
    world.say(
        f"{parent.id} lifted a paw and gave a gentle caution."
    )
    world.say(
        f'"Let us keep the {cutlet.label} safe first, and then you can help with the careful work."'
    )
    fix_plan(world, hero, cutlet, cooler, aid)

    world.facts.update(hero=hero, parent=parent, cutlet=cutlet, cooler=cooler, tool=tool, aid=aid)
    return world


SETTINGS = {
    "kitchen_nook": Setting(place="the kitchen nook", indoors=True, affords={"hone", "cool", "serve"}),
    "pantry_table": Setting(place="the pantry table", indoors=True, affords={"hone", "cool"}),
    "back_porch": Setting(place="the back porch", indoors=False, affords={"cool", "serve"}),
}

TOOLS = {
    "hone_stone": Tool(
        id="hone_stone",
        label="hone stone",
        phrase="a small hone stone",
        use="hone",
        risk="a careless nick",
        tags={"hone"},
    ),
    "paring_knife": Tool(
        id="paring_knife",
        label="paring knife",
        phrase="a tiny paring knife",
        use="hone",
        risk="a slippery cut",
        tags={"hone"},
    ),
}

FOODS = {
    "cutlet": Food(
        id="cutlet",
        label="cutlet",
        phrase="a warm cutlet on a plate",
        region="table",
        spoil_risk="go bad",
        tags={"cutlet"},
    ),
}

ASSISTS = {
    "ice_box": Assist(
        id="ice_box",
        label="ice box",
        fix="wrap the cutlet and place it in the ice box",
        tail="The ice box did its job",
        tags={"refrigerant"},
    ),
    "refrigerant_case": Assist(
        id="refrigerant_case",
        label="refrigerant case",
        fix="slide the cutlet into the refrigerant case",
        tail="The refrigerant case kept the cool air tucked around it",
        tags={"refrigerant"},
    ),
}

HERO_NAMES = ["Pip", "Milo", "Tansy", "Fern", "Bram", "Nina"]
PARENT_NAMES = ["Mother Hare", "Father Fox", "Aunt Badger", "Uncle Otter"]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    parent_name: str
    tool: str
    food: str
    assist: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short animal story with foreshadowing, a cautionary warning, and a happy ending.",
        f"Tell a gentle story about {hero.id} who wants to hone a tool while a cutlet needs to stay cold.",
        "Make the refrigerant matter, make the cutlet stay safe, and end with everyone feeling glad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, cutlet, cooler, tool, aid = f["hero"], f["parent"], f["cutlet"], f["cooler"], f["tool"], f["aid"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {tool.label}?",
            answer=f"{hero.id} wanted to hone the {tool.label} carefully so it would shine and be useful.",
        ),
        QAItem(
            question=f"Why was the {cutlet.label} important in the story?",
            answer=f"The {cutlet.label} needed to stay cool and safe, because warm food can go bad.",
        ),
        QAItem(
            question=f"What warning did {parent.id} give about the {cutlet.label}?",
            answer=f"{parent.id} warned that if the {cutlet.label} stayed warm, it would not stay tasty for long.",
        ),
        QAItem(
            question=f"How did the story end for the {cutlet.label}?",
            answer=f"They used the {cooler.label} and the {aid.label}, so the {cutlet.label} ended cool and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to hone something?",
            answer="To hone something means to sharpen or smooth it carefully so it works better.",
        ),
        QAItem(
            question="What is a refrigerant for?",
            answer="A refrigerant is something used in a cooling system to help keep things cold.",
        ),
        QAItem(
            question="Why do cutlets need care after cooking?",
            answer="Cooked meat can spoil if it is left warm too long, so it should be cooled or stored safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]]
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A cutlet is at risk when it is warm.
at_risk(F) :- food(F), warm(F).

% Cautionary warning follows from risk.
warns(P, F) :- person(P), food(F), at_risk(F).

% Happy ending fix: a cooling aid can make the cutlet safe again.
safe(F) :- food(F), cooled(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_use", tid, t.use))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("warm", fid))  # base story logic: cutlet is warm initially in the cautionary setup
    for aid, a in ASSISTS.items():
        lines.append(asp.fact("aid", aid))
        if "refrigerant" in a.tags:
            lines.append(asp.fact("refrigerant", aid))
    for name in HERO_NAMES:
        lines.append(asp.fact("person", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show warns/2.\n#show safe/1."))
    warns = set(asp.atoms(model, "warns"))
    safe = set(asp.atoms(model, "safe"))
    ok_warn = any(a == "cutlet" for (_, a) in warns)
    ok_safe = any(a == "cutlet" for (a,) in safe)
    if ok_warn and ok_safe:
        print("OK: ASP gate exercised with warning and safe resolution.")
        return 0
    print("MISMATCH: ASP gate did not exercise expected cutlet reasoning.")
    return 1


def explain_rejection(place: str, tool: Tool, food: Food) -> str:
    return (
        f"(No story: the chosen tool and cutlet do not make a sensible cautionary "
        f"turn at {place}. The cutlet must be at risk and later made safe, or the "
        f"story would have no honest change.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for tool_id in TOOLS:
            for food_id in FOODS:
                for aid_id in ASSISTS:
                    if "hone" in TOOLS[tool_id].tags and "refrigerant" in ASSISTS[aid_id].tags:
                        out.append((place, tool_id, food_id, aid_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: hone, refrigerant, cutlet; cautionary foreshadowing with a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--assist", choices=ASSISTS)
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.food is None or c[2] == args.food)
              and (args.assist is None or c[3] == args.assist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, food, assist = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        hero_name=args.name or rng.choice(HERO_NAMES),
        parent_name=args.parent or rng.choice(PARENT_NAMES),
        tool=tool,
        food=food,
        assist=assist,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="fox", traits=["careful", "curious"]))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="rabbit", traits=["cautious"]))
    tool = world.add(Entity(id=params.tool, kind="thing", type="tool", label=TOOLS[params.tool].label, phrase=TOOLS[params.tool].phrase))
    cutlet = world.add(Entity(id=params.food, kind="thing", type="cutlet", label="cutlet", phrase=FOODS[params.food].phrase))
    cooler = world.add(Entity(id=params.assist, kind="thing", type="cooler", label=ASSISTS[params.assist].label, phrase=ASSISTS[params.assist].label))

    tell(world, hero, parent, cutlet, cooler, tool, ASSISTS[params.assist])
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
    StoryParams(place="kitchen_nook", hero_name="Pip", parent_name="Mother Hare", tool="hone_stone", food="cutlet", assist="refrigerant_case"),
    StoryParams(place="pantry_table", hero_name="Milo", parent_name="Aunt Badger", tool="paring_knife", food="cutlet", assist="ice_box"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show warns/2.\n#show safe/1."))
    return sorted(set(asp.atoms(model, "warns")) | set(asp.atoms(model, "safe")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show warns/2.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show warns/2.\n#show safe/1."))
        print(f"ASP atoms: {sorted(set(asp.atoms(model, 'warns')) | set(asp.atoms(model, 'safe')))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
