#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sleaze_profession_sesame_problem_solving_space_adventure.py
===========================================================================================

A standalone story world for a small space-adventure domain with problem solving.

Seed words:
- sleaze
- profession
- sesame

Story premise:
- A space crew is in the middle of a mission.
- A sticky sleaze spill or sesame mess creates trouble.
- The crew uses different professions and tools to solve the problem.
- The ending proves the ship is clean, safe, and ready to fly on.

This script follows the Storyweavers contract:
- stdlib only
- storyworlds/results.py imported eagerly
- StoryParams, build_parser, resolve_params, generate, emit, main
- --verify, --asp, --show-asp, --trace, --qa, --json, --all, -n, --seed
- Python reasonableness gate plus inline ASP twin
- Q&A sets grounded in simulated world state, not rendered text parsing
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    profession: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Ship:
    name: str
    place: str
    crew: list[str] = field(default_factory=list)

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
class Mess:
    id: str
    label: str
    smell: str
    on: str
    sticky: bool = True
    mess_kind: str = "sleaze"
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
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
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


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


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    spill = world.facts.get("spill")
    if spill is None:
        return out
    if spill.meters["active"] < THRESHOLD:
        return out
    sig = ("sticky", spill.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("panel").meters["gummed"] += 1
    for c in world.characters():
        c.memes["worry"] += 1
    out.append("__sticky__")
    return out


def _r_slowdown(world: World) -> list[str]:
    out: list[str] = []
    if world.get("panel").meters["gummed"] < THRESHOLD:
        return out
    sig = ("slowdown",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ship").meters["delay"] += 1
    out.append("The ship could not answer quickly enough.")
    return out


CAUSAL_RULES = [
    Rule("sticky", "physical", _r_sticky),
    Rule("slowdown", "physical", _r_slowdown),
]


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


def reasonables() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def hazard_at_risk(mess: Mess, target: str) -> bool:
    return mess.sticky and target in {"panel", "sensor", "door", "lever"}


def tool_fits(tool: Tool, target: str) -> bool:
    return target in tool.tags


def predict(world: World, target: str) -> dict:
    sim = world.copy()
    spill = sim.facts["spill"]
    spill.meters["active"] += 1
    propagate(sim, narrate=False)
    return {
        "gummed": sim.get(target).meters["gummed"],
        "delay": sim.get("ship").meters["delay"],
    }


def setup(world: World, crew: list[Entity], ship: Ship, mess: Mess) -> None:
    names = " and ".join(c.id for c in crew)
    world.say(
        f"On the starship {ship.name}, {names} were traveling through a quiet "
        f"part of space. {ship.place.capitalize()} was bright with buttons, blinking "
        f"lights, and a round table for snacks."
    )
    world.say(
        f"{crew[0].id} served in the {crew[0].profession} profession, {crew[1].id} worked as "
        f"a {crew[1].profession}, and {crew[2].id} knew how to keep the little ship calm."
    )
    world.say(
        f"Near the control panel, a tray of sesame crackers tipped over, and a slick {mess.mess_kind} "
        f"spread across the floor and up the wall."
    )
    for c in crew:
        c.memes["curiosity"] += 1


def problem(world: World, hero: Entity, helper: Entity, mess: Mess, target: Entity) -> None:
    hero.memes["interest"] += 1
    world.say(
        f"{hero.id} peered at the mess and said, \"That {mess.label} is in the way.\" "
        f"{helper.id} nodded. \"It could gum up the {target.label}.\""
    )
    world.say(
        f"They wanted to keep going, but the {mess.mess_kind} on the {target.label} meant the ship might slip."
    )


def use_profession(world: World, fixer: Entity, tool: Tool, target: Entity, mess: Mess) -> None:
    fixer.memes["confidence"] += 1
    world.say(
        f"{fixer.id}, who knew the {fixer.profession} profession well, took "
        f"{tool.phrase} and {tool.action} the {target.label}."
    )
    target.meters["clean"] += 1
    mess.meters["active"] = 0.0
    world.get("panel").meters["gummed"] = 0.0
    world.get("ship").meters["delay"] = 0.0
    world.say(
        f"The sticky sleaze lifted away in a thin gray ribbon, and the {target.label} shone again."
    )


def celebrate(world: World, crew: list[Entity], target: Entity, tool: Tool) -> None:
    for c in crew:
        c.memes["relief"] += 1
        c.memes["joy"] += 1
    world.say(
        f"Then the crew smiled, because the little ship was safe again. "
        f"{crew[2].id} closed the snack tray, {crew[0].id} checked the stars, and {crew[1].id} tucked "
        f"{tool.label} back into its pouch."
    )
    world.say(
        f"By the end, the {target.label} was clean, the sesame smell was only a snack smell, "
        f"and the starship flew on through the dark with room to spare."
    )


def tell(ship: Ship, mess: Mess, tool: Tool, target_label: str,
         name1: str = "Ari", type1: str = "girl",
         name2: str = "Beck", type2: str = "boy",
         name3: str = "Jo", type3: str = "girl",
         professions: tuple[str, str, str] = ("pilot", "engineer", "cook")) -> World:
    world = World(ship)
    world.add(Entity("ship", kind="thing", type="ship", label=ship.name))
    panel = world.add(Entity("panel", kind="thing", type="panel", label=target_label))
    spill = world.add(Entity("spill", kind="thing", type="mess", label=mess.label))
    world.facts["spill"] = spill
    crew = [
        world.add(Entity(name1, kind="character", type=type1, role="hero", profession=professions[0])),
        world.add(Entity(name2, kind="character", type=type2, role="helper", profession=professions[1])),
        world.add(Entity(name3, kind="character", type=type3, role="fixer", profession=professions[2])),
    ]
    setup(world, crew, ship, mess)
    world.para()
    problem(world, crew[0], crew[1], mess, panel)
    world.para()
    spill.meters["active"] += 1
    propagate(world, narrate=True)
    use_profession(world, crew[2], tool, panel, mess)
    world.para()
    celebrate(world, crew, panel, tool)
    world.facts.update(
        crew=crew, ship=ship, mess=mess, tool=tool, panel=panel,
        outcome="fixed", spilled=True, cleaned=True
    )
    return world


SHIP_REGISTRY = {
    "orbiter": Ship("Moon Kite", "the control room"),
    "freighter": Ship("Comet Box", "the command deck"),
    "explorer": Ship("Star Nest", "the galley hallway"),
}

MESSES = {
    "sesame": Mess("sesame", "sesame crumbs", "toasty", "panel", tags={"sesame", "food"}),
    "sleaze": Mess("sleaze", "sleaze", "slippery", "panel", tags={"sleaze", "sticky"}),
}

TOOLS = {
    "cloth": Tool("cloth", "clean cloth", "a clean cloth", "wipe", 2, 3, tags={"panel"}),
    "brush": Tool("brush", "soft brush", "a soft brush", "sweep", 3, 3, tags={"panel"}),
    "spray": Tool("spray", "tiny spray bottle", "a tiny spray bottle", "sprayed", 4, 2, tags={"panel"}),
}

PROFESSIONS = ["pilot", "engineer", "cook", "navigator", "medic", "mechanic"]
NAMES_G = ["Ari", "Mina", "Zoe", "Luna", "Ivy", "Nia"]
NAMES_B = ["Beck", "Kai", "Juno", "Taj", "Milo", "Rey"]


@dataclass
@dataclass
class StoryParams:
    ship: str
    mess: str
    tool: str
    target: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    fixer: str
    fixer_type: str
    profession1: str
    profession2: str
    profession3: str
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
    out = []
    for ship in SHIP_REGISTRY:
        for mess_id, mess in MESSES.items():
            for tool_id, tool in TOOLS.items():
                if hazard_at_risk(mess, "panel") and tool_fits(tool, "panel"):
                    out.append((ship, mess_id, tool_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure problem solving storyworld.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--n", type=int, default=1)
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
    if args.mess and args.tool:
        if not (hazard_at_risk(MESSAGES[args.mess], "panel") and tool_fits(TOOLS[args.tool], "panel")):
            raise StoryError("No story: that mess does not fit that fix.")
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.mess is None or c[1] == args.mess)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, mess, tool = rng.choice(sorted(combos))
    g1 = rng.choice([True, False])
    g2 = rng.choice([True, False])
    hero = rng.choice(NAMES_G if g1 else NAMES_B)
    helper = rng.choice([n for n in (NAMES_B if g1 else NAMES_G) if n != hero])
    fixer = rng.choice([n for n in NAMES_G + NAMES_B if n not in {hero, helper}])
    return StoryParams(
        ship, mess, tool, "control panel",
        hero, "girl" if g1 else "boy",
        helper, "boy" if g2 else "girl",
        fixer, "girl" if rng.choice([True, False]) else "boy",
        rng.choice(PROFESSIONS), rng.choice(PROFESSIONS), rng.choice(PROFESSIONS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "{f["mess"].label}" and "profession".',
        f"Tell a problem-solving story on a starship where a sesame snack mess blocks the control panel and the crew fixes it calmly.",
        f'Write a child-friendly story about a ship, a sticky sleaze mess, and a clever repair that ends with the crew flying on.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew = f["crew"]
    return [
        QAItem(
            question="Who was on the starship?",
            answer=f"It was a small crew: {crew[0].id}, {crew[1].id}, and {crew[2].id}. They each had a different profession and worked together on the ship."
        ),
        QAItem(
            question="What problem did they have?",
            answer="Sesame crumbs and sticky sleaze covered the control panel area. That made the ship hard to use until they cleaned it."
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"{crew[2].id} used the {f['tool'].label} to clean the panel, and the other two crew members helped by keeping the snack tray closed and watching the controls. The sticky mess was removed, so the ship could fly on safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a pilot do?",
            answer="A pilot helps guide a ship or vehicle and watches where it goes."
        ),
        QAItem(
            question="What does an engineer do?",
            answer="An engineer fixes machines and helps them work the way they should."
        ),
        QAItem(
            question="What are sesame seeds?",
            answer="Sesame seeds are tiny seeds that can be sprinkled on food like bread or crackers."
        ),
        QAItem(
            question="Why can sticky messes be a problem on a ship?",
            answer="Sticky messes can make buttons and tools hard to use. On a spaceship, that can slow the crew down until they clean it."
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
        if e.profession:
            bits.append(f"profession={e.profession}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SHIP_REGISTRY[params.ship],
        MESSES[params.mess],
        TOOLS[params.tool],
        params.target,
        params.hero, params.hero_type,
        params.helper, params.helper_type,
        params.fixer, params.fixer_type,
        (params.profession1, params.profession2, params.profession3),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
hazard(M, T) :- sticky(M), target(T).
fit(Tool, T) :- tool(Tool), target(T), tool_target(Tool, T).
valid(Ship, M, Tool) :- ship(Ship), mess(M), tool(Tool), hazard(M, target), fit(Tool, target).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIP_REGISTRY:
        lines.append(asp.fact("ship", sid))
    for mid in MESSAGES if False else []:
        pass
    for mid, m in MESSES.items():
        lines.append(asp.fact("mess", mid))
        if m.sticky:
            lines.append(asp.fact("sticky", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_target", tid, "target"))
    lines.append(asp.fact("target", "target"))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("orbiter", "sesame", "cloth", "control panel", "Ari", "girl", "Beck", "boy", "Jo", "girl", "pilot", "engineer", "cook"),
    StoryParams("freighter", "sleaze", "brush", "control panel", "Mina", "girl", "Kai", "boy", "Taj", "boy", "navigator", "mechanic", "medic"),
]


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {exc}")
    return rc


def resolve_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def explain_response(rid: str) -> str:
    r = TOOLS[rid]
    better = ", ".join(sorted(t.id for t in reasonables()))
    return f"(Refusing tool '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
