#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/wag_inner_monologue_moral_value_transformation_pirate.py
====================================================================================================================================

A small standalone storyworld in a pirate-tale style.

Premise:
- A young pirate wants to use a noisy, unsafe shortcut during a dockside hunt.
- A companion notices the risk, speaks up, and the hero thinks through the choice.
- The hero changes from impatient to careful, choosing a safer tool and ending
  with a vivid physical image that shows the change.

Features used:
- Inner Monologue
- Moral Value
- Transformation

The story domain stays small on purpose: a few places, a few actions, and a few
compatible safety choices. The prose is generated from simulated state, not from
a frozen template with swapped nouns.
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    id: str
    label: str
    sound: str
    afford: set[str] = field(default_factory=set)
    risky: set[str] = field(default_factory=set)


@dataclass
class Hunt:
    id: str
    verb: str
    inner_thought: str
    rush: str
    mess: str
    risk: str
    zone: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    harbor: str = ""
    hunt: str = ""
    prize: str = ""
    tool: str = ""
    name: str = ""
    gender: str = ""
    parent: str = ""
    companion: str = ""
    seed: Optional[int] = None


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.noisy: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.harbor)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.noisy = self.noisy
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["bold"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["messy"] += 1
            actor.meters["trouble"] += 1
            out.append(f"{actor.label}'s {item.label} got splashed and messy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["messy"] < THRESHOLD or not item.attrs.get("caretaker"):
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.attrs["caretaker"])
        carer.meters["work"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_signal(world: World) -> list[str]:
    for actor in world.characters():
        if actor.meters["fear"] < THRESHOLD:
            continue
        sig = ("signal", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.noisy = True
        return ["__signal__"]
    return []


CAUSAL_RULES = [
    Rule("mess", "physical", _r_mess),
    Rule("worry", "physical", _r_worry),
    Rule("signal", "social", _r_signal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def prize_at_risk(hunt: Hunt, prize: Prize) -> bool:
    return prize.region in hunt.zone


def select_tool(hunt: Hunt, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS.values():
        if hunt.mess in tool.guards and prize.region in tool.covers:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for harbor_id, harbor in HARBORS.items():
        for hunt_id in harbor.afford:
            hunt = HUNTS[hunt_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(hunt, prize) and select_tool(hunt, prize):
                    combos.append((harbor_id, hunt_id, prize_id))
    return combos


def predict(world: World, hero: Entity, hunt: Hunt, prize: Prize) -> dict:
    sim = world.copy()
    _do_hunt(sim, sim.get(hero.id), hunt, narrate=False)
    pr = sim.get("prize")
    return {"messy": pr.meters["messy"] >= THRESHOLD, "work": sim.get("caretaker").meters["work"]}


def _do_hunt(world: World, hero: Entity, hunt: Hunt, narrate: bool = True) -> None:
    world.zone = set(hunt.zone)
    hero.meters["bold"] += 1
    hero.meters["restless"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"At {world.harbor.label}, {hero.label} and {companion.label} listened to the gulls and the creak of ropes."
    )
    world.say(
        f"{hero.label} was a little pirate who liked {world.facts['hunt'].verb}; inside {hero.pronoun('possessive')} head, {world.facts['hunt'].inner_thought}."
    )


def setup(world: World, hero: Entity, companion: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.label}'s {world.facts['parent'].label} had given {hero.pronoun('object')} {prize.phrase} before the ship set out."
    )
    prize.worn_by = hero.id
    world.say(f"{hero.label} loved {prize.it()} and wore {prize.it()} like treasure.")


def arrive(world: World) -> None:
    world.say(
        f"One {world.facts['time']} the harbor sounded busy, and {world.harbor.sound}."
    )


def want(world: World, hero: Entity, companion: Entity, hunt: Hunt, prize: Entity) -> None:
    hero.meters["want"] += 1
    world.say(
        f"{hero.label} wanted to {hunt.verb} right away, but {hero.pronoun('possessive')} {world.facts['parent'].label} frowned at {prize.label}."
    )


def warn(world: World, companion: Entity, hero: Entity, hunt: Hunt, prize: Entity) -> None:
    pred = predict(world, hero, hunt, prize)
    world.facts["predicted"] = pred
    world.say(
        f'{companion.label} said, "{prize.label} could get {hunt.risk}, and then there would be trouble."'
    )


def inner_turn(world: World, hero: Entity, hunt: Hunt) -> None:
    world.say(
        f"Inside {hero.label}'s head, another thought answered: maybe a real pirate was not the one who rushed first."
    )
    hero.meters["thinking"] += 1
    hero.memes["moral_value"] += 1


def choose_change(world: World, hero: Entity, companion: Entity, hunt: Hunt, prize: Prize, tool: Tool) -> None:
    hero.memes["calm"] += 1
    hero.memes["change"] += 1
    world.say(
        f"{hero.label} took a breath, nodded, and chose {tool.phrase} instead."
    )
    tool.id in world.entities or world.add(Entity(id=tool.id, type="tool", label=tool.label, protective=True, covers=set(tool.covers)))
    t = world.get(tool.id)
    t.worn_by = hero.id
    world.say(
        f"With {tool.label}, {hero.label} could still {hunt.verb}, and {prize.label} stayed safe."
    )


def finish(world: World, hero: Entity, companion: Entity, prize: Entity, hunt: Hunt) -> None:
    hero.meters["bold"] = 0
    hero.memes["moral_value"] += 1
    world.say(
        f"By the end, {hero.label} was no longer the pirate who wanted the quickest way; {hero.pronoun().capitalize()} was the pirate who chose the safer one."
    )
    world.say(
        f"{companion.label} wagged {companion.pronoun('possessive')} tail beside the dock, and {hero.label}'s {prize.label} stayed bright and dry in the sea wind."
    )


def tell(harbor: Harbor, hunt: Hunt, prize_cfg: Prize, tool_def: Tool,
         name: str, gender: str, parent: str, companion: str) -> World:
    world = World(harbor)
    world.facts["time"] = "afternoon"
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, traits=["little", "pirate"]))
    comp = world.add(Entity(id=companion, kind="character", type="dog", label=companion, role="companion"))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=parent, label=parent))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, attrs={"caretaker": caretaker.id}, region=prize_cfg.region, plural=prize_cfg.plural))
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label, protective=True, covers=set(tool_def.covers)))

    world.facts.update(hero=hero, companion=comp, parent=caretaker, prize=prize, hunt=hunt, tool=tool, harbor=harbor)

    intro(world, hero, comp)
    setup(world, hero, comp, prize)
    world.para()
    arrive(world)
    want(world, hero, comp, hunt, prize)
    warn(world, comp, hero, hunt, prize)
    inner_turn(world, hero, hunt)
    world.para()
    choose_change(world, hero, comp, hunt, prize, tool)
    finish(world, hero, comp, prize, hunt)
    return world


HARBORS = {
    "cove": Harbor(id="cove", label="the little cove", sound="the waves slapped the pilings", afford={"map", "lantern", "rope"}, risky={"water"}),
    "dock": Harbor(id="dock", label="the moonlit dock", sound="the ropes tapped the posts", afford={"map", "lantern", "rope"}, risky={"water"}),
    "ship": Harbor(id="ship", label="the deck of the ship", sound="the mast hummed in the wind", afford={"map", "lantern", "rope", "sail"}, risky={"water"}),
}

HUNTS = {
    "map": Hunt(id="map", verb="follow the map", inner_thought="the treasure might be close if {hero} hurried", rush="dash to the chest", mess="wet", risk="soaked", zone={"feet", "legs"}, tags={"water", "wet"}),
    "lantern": Hunt(id="lantern", verb="search by lantern light", inner_thought="the dark corner looked spooky and tempting", rush="grab the nearest flame", mess="smoky", risk="smoky", zone={"torso"}, tags={"dark", "light"}),
    "rope": Hunt(id="rope", verb="climb the rope ladder", inner_thought="the tallest mast would make the best lookout", rush="scramble up fast", mess="muddy", risk="muddy", zone={"feet", "legs"}, tags={"climb"}),
    "sail": Hunt(id="sail", verb="pull the sail loose", inner_thought="the ship would seem bigger if {hero} could help", rush="jerk the rope hard", mess="sandy", risk="tangled", zone={"torso"}, tags={"wind"}),
}

PRIZES = {
    "boots": Prize(id="boots", label="sea boots", phrase="shiny sea boots", region="feet", plural=True),
    "shirt": Prize(id="shirt", label="stripe shirt", phrase="a stripe shirt", region="torso"),
    "cloak": Prize(id="cloak", label="captain's cloak", phrase="a captain's cloak", region="torso"),
    "sash": Prize(id="sash", label="red sash", phrase="a red sash", region="legs"),
}

TOOLS = {
    "wrap": Tool(id="wrap", label="dry wrap", phrase="a dry wrap", guards={"wet", "muddy", "sandy"}, covers={"feet", "legs"}),
    "coat": Tool(id="coat", label="oilskin coat", phrase="an oilskin coat", guards={"wet", "smoky"}, covers={"torso"}),
    "boots": Tool(id="boots", label="rain boots", phrase="rain boots", guards={"wet", "muddy"}, covers={"feet"}),
    "gloves": Tool(id="gloves", label="work gloves", phrase="work gloves", guards={"rope", "sandy"}, covers={"hands"}),
}

def _make_valid_tool() -> Tool:
    return next(iter(TOOLS.values()))


@dataclass
class StoryChoice:
    harbor: str
    hunt: str
    prize: str
    tool: str


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nina"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]
DOG_NAMES = ["Pip", "Wag", "Moss", "Skiff"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate storyworld with inner monologue, moral value, and transformation.")
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--hunt", choices=HUNTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--companion")
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
              if (args.harbor is None or c[0] == args.harbor)
              and (args.hunt is None or c[1] == args.hunt)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    harbor, hunt, prize = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(t.id for t in TOOLS.values() if HUNTS[hunt].mess in t.guards and PRIZES[prize].region in t.covers))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    companion = args.companion or rng.choice(DOG_NAMES)
    return StoryParams(harbor=harbor, hunt=hunt, prize=prize, tool=tool, name=name, gender=gender, parent=parent, companion=companion)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate story for a young child that includes the word "wag" and shows a character thinking to itself before choosing a safer way.',
        f"Tell a short pirate tale where {f['hero'].label} wants to {f['hunt'].verb} at {f['harbor'].label}, but chooses {f['tool'].label} after listening to a friend.",
        f'Write a story with inner monologue, moral value, and transformation where a pirate learns that patience is braver than rushing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, comp, prize, hunt, tool = f["hero"], f["companion"], f["prize"], f["hunt"], f["tool"]
    parent = f["parent"]
    qa = [
        QAItem(
            question=f"What did {hero.label} want to do at {f['harbor'].label} before thinking twice?",
            answer=f"{hero.label} wanted to {hunt.verb}. At first {hero.pronoun()} felt hurried, but the sight of {prize.label} made the choice feel risky.",
        ),
        QAItem(
            question=f"What did the companion warn {hero.label} about?",
            answer=f"{comp.label} warned that {prize.label} could get {hunt.risk}. That warning mattered because the prize was being worn right where the danger could reach it.",
        ),
        QAItem(
            question=f"How did {hero.label}'s thoughts change during the story?",
            answer=f"At first {hero.label} only wanted the quickest way. Then {hero.pronoun()} decided that a smart pirate listens, stays calm, and picks the safer tool.",
        ),
        QAItem(
            question=f"How did the story show a moral change at the end?",
            answer=f"{hero.label} changed from rushing forward to choosing {tool.label}. The ending proves the change because the prize stayed safe and the pirate acted with care.",
        ),
    ]
    if world.facts["predicted"]["messy"]:
        qa.append(QAItem(
            question=f"Why would rushing have been a problem for {prize.label}?",
            answer=f"Rushing would have splashed {prize.label} and made it messy. The story says that clearly, because the risk was tied to where the prize was worn and the unsafe rush reached that spot.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does wag mean?", "Wag means to move back and forth, often the way a happy dog moves its tail."),
        QAItem("What is a moral value?", "A moral value is a kind of good habit, like caring, honesty, patience, or kindness."),
        QAItem("What is a transformation in a story?", "A transformation is when a character changes in an important way, like becoming braver or wiser."),
        QAItem("What is a pirate tale?", "A pirate tale is an adventure story about ships, docks, treasure, and daring choices on the sea."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict((k,v) for k,v in e.meters.items() if v)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict((k,v) for k,v in e.memes.items() if v)}")
        if e.kind == "character":
            bits.append(f"role={e.role or 'n/a'}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(out)


def tell(harbor: Harbor, hunt: Hunt, prize_cfg: Prize, tool_def: Tool, name: str, gender: str, parent_type: str, companion_name: str) -> World:
    world = World(harbor)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, role="hero", traits=["pirate", "restless"]))
    comp = world.add(Entity(id=companion_name, kind="character", type="dog", label=companion_name, role="companion"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, region=prize_cfg.region, plural=prize_cfg.plural, attrs={"caretaker": parent.id}))
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label, protective=True, covers=set(tool_def.covers)))
    world.facts.update(hero=hero, companion=comp, parent=parent, prize=prize, hunt=hunt, tool=tool, harbor=harbor)

    world.say(f"At {harbor.label}, the tide sang against the boards and {comp.label} gave a cheerful wag of the tail.")
    world.say(f"{hero.label} was a little pirate with a busy heart, and inside {hero.pronoun('possessive')} head {hunt.inner_thought}.")
    world.say(f"{parent.label} had given {hero.pronoun('object')} {prize.phrase} before the adventure began.")
    world.say(f"{hero.label} liked the shine of {prize.label}, and {prize.label} bobbed lightly as {hero.label} moved.")
    world.para()
    world.say(f"One afternoon the harbor was loud with ropes and gulls.")
    world.say(f"{hero.label} wanted to {hunt.verb}, but {parent.label} warned that {prize.label} could get {hunt.risk}.")
    world.say(f"{comp.label} added, \"Careful now. The quick way can spoil a good thing.\"")
    world.say(f"Inside, {hero.label} wondered if a real pirate had to rush at everything.")
    hero.memes["moral_value"] += 1
    hero.memes["tension"] += 1
    world.para()
    world.say(f"Then {hero.label} took a breath and chose {tool.phrase} instead.")
    tool.worn_by = hero.id
    hero.memes["calm"] += 1
    hero.memes["transformation"] += 1
    hero.meters["changed"] += 1
    world.say(f"With {tool.label}, {hero.label} could still {hunt.verb}, and {prize.label} stayed clean and bright.")
    world.say(f"{comp.label} wagged {comp.label}'s tail beside the dock while {hero.label} smiled at the safer plan.")
    return world


ASP_RULES = r"""
risk(A,P) :- hunt(A), prize(P), zone(A,Z), region(P,R), covers_hazard(Z,R).
valid(H, A, P) :- harbor(H), hunt(A), prize(P), risk(A,P), has_tool(A,P).
has_tool(A,P) :- tool(T), guards(T,M), hunt_mess(A,M), tool_covers(T,R), region(P,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HARBORS:
        lines.append(asp.fact("harbor", hid))
    for aid, a in HUNTS.items():
        lines.append(asp.fact("hunt", aid))
        lines.append(asp.fact("hunt_mess", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("tool_covers", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    sample = generate(resolve_params(argparse.Namespace(harbor=None, hunt=None, prize=None, tool=None, name=None, gender=None, parent=None, companion=None), random.Random(7)))
    if not sample.story:
        print("Smoke test failed: empty story.")
        return 1
    print(f"OK: ASP parity and story smoke test passed ({len(valid_combos())} combos).")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.harbor not in HARBORS or params.hunt not in HUNTS or params.prize not in PRIZES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    harbor = HARBORS[params.harbor]
    hunt = HUNTS[params.hunt]
    prize = PRIZES[params.prize]
    tool = TOOLS[params.tool]
    if not (prize_at_risk(hunt, prize) and hunt.mess in tool.guards and prize.region in tool.covers):
        raise StoryError("This combination is not a valid pirate story.")
    world = tell(harbor, hunt, prize, tool, params.name, params.gender, params.parent, params.companion)
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
    StoryParams(harbor="cove", hunt="map", prize="boots", tool="wrap", name="Lily", gender="girl", parent="mother", companion="Wag"),
    StoryParams(harbor="dock", hunt="rope", prize="sash", tool="gloves", name="Tom", gender="boy", parent="father", companion="Pip"),
    StoryParams(harbor="ship", hunt="sail", prize="cloak", tool="coat", name="Mia", gender="girl", parent="mother", companion="Moss"),
    StoryParams(harbor="dock", hunt="map", prize="boots", tool="wrap", name="Finn", gender="boy", parent="father", companion="Skiff"),
]

def _resolve_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            sample = generate(p)
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
