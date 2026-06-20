#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/suffocate_licorice_bind_mystery_to_solve_happy.py
=================================================================================

A standalone storyworld for a small pirate-tale mystery: a child crew notices a
strange licorice smell, discovers a hidden trap, and solves the mystery with
careful binding and a safe rescue. The core premise is child-facing, concrete,
and state-driven: clues accumulate, a danger is predicted, the crew acts, and a
happy ending proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/suffocate_licorice_bind_mystery_to_solve_happy.py
    python storyworlds/worlds/gpt-5.4-mini/suffocate_licorice_bind_mystery_to_solve_happy.py --all
    python storyworlds/worlds/gpt-5.4-mini/suffocate_licorice_bind_mystery_to_solve_happy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/suffocate_licorice_bind_mystery_to_solve_happy.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    scene: str
    dark_spot: str
    goal: str
    pirate_frame: str

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
class Clue:
    id: str
    text: str
    smell: str
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
class Hazard:
    id: str
    label: str
    bindable: bool
    can_suffocate: bool
    spread: int
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    haz = world.facts.get("hazard")
    if not haz:
        return out
    suspect = world.get("clue")
    if suspect.meters["suspicion"] >= THRESHOLD and ("danger",) not in world.fired:
        world.fired.add(("danger",))
        world.get("ship").meters["risk"] += 1
        world.get("crew").memes["worry"] += 1
        out.append("__danger__")
    return out


CAUSAL_RULES = [Rule("danger", "social", _r_danger)]


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


def suspect_present(clue: Clue, hazard: Hazard) -> bool:
    return clue.id in {"licorice", "salted_licorice"} and hazard.can_suffocate


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.power >= SENSE_MIN]


def hazard_severity(hazard: Hazard) -> int:
    return hazard.spread


def can_solve(tool: Tool, hazard: Hazard) -> bool:
    return tool.power >= hazard_severity(hazard)


def _do_bind(world: World, hazard_ent: Entity, tool: Tool, narrate: bool = True) -> None:
    hazard_ent.meters["bound"] += 1
    hazard_ent.meters["weakened"] += 1
    propagate(world, narrate=narrate)


def predict_world(world: World, hazard: Hazard, tool: Tool) -> dict:
    sim = world.copy()
    _do_bind(sim, sim.get("hazard"), tool, narrate=False)
    return {
        "solved": sim.get("hazard").meters["bound"] >= THRESHOLD,
        "risk": sim.get("ship").meters["risk"],
    }


def setup(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {mate.id} turned the deck into "
        f"{setting.scene}. {setting.pirate_frame}"
    )
    world.say(
        f"They called themselves {hero.id} and {mate.id}, two little pirates "
        f"searching for {setting.goal}."
    )


def mystery(world: World, hero: Entity, clue: Clue, setting: Setting) -> None:
    world.say(
        f"But a strange smell drifted over the boards -- sweet like {clue.smell}. "
        f"It floated from {setting.dark_spot}, where the light was thin."
    )
    world.say(
        f"{hero.id} leaned closer and whispered, \"Why does it smell like {clue.smell}?\""
    )


def inspect(world: World, mate: Entity, clue: Clue, hazard: Hazard) -> None:
    mate.memes["curiosity"] += 1
    world.say(
        f"{mate.id} pointed to the clue. \"This is no snack,\" {mate.pronoun()} said. "
        f"\"Something here is trying to hide. We should not let it suffocate the air.\""
    )
    world.say(
        f"They found {clue.text}, and the little pirates knew the mystery had a real danger in it."
    )
    world.facts["hazard"] = True


def warn(world: World, mate: Entity, hero: Entity, hazard: Hazard, tool: Tool) -> None:
    pred = predict_world(world, hazard, tool)
    mate.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f"{mate.id} bit {mate.pronoun('possessive')} lip. \"If we pull on that without "
        f"being careful, it could bind fast and trap the air,\" {mate.pronoun()} said. "
        f"\"Then the little ship would be in trouble.\""
    )


def choose(tool: Tool) -> str:
    return {
        "rope": "a coil of rope",
        "cloth": "a thick cloth strip",
        "hook": "a small hook and line",
    }[tool.id]


def bind(world: World, hero: Entity, mate: Entity, hazard_ent: Entity, tool: Tool, hazard: Hazard) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} nodded and grabbed {choose(tool)}. With one careful tug, "
        f"{hero.id} began to {tool.action} the hidden knot."
    )
    _do_bind(world, hazard_ent, tool)
    world.say(
        f"The thing loosened, and the smell of licorice faded from the air."
    )


def rescue(world: World, setting: Setting, hero: Entity, mate: Entity) -> None:
    world.say(
        f"Soon the pirates found the trapped hatch under {setting.dark_spot}. "
        f"Inside was a tiny bird with its wing stuck in the old net."
    )
    world.say(
        f"{hero.id} and {mate.id} freed it gently. The bird blinked, fluffed its feathers, "
        f"and flew up to the bright rigging."
    )


def happy_end(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"After that, the deck felt cheerful again. The little pirates sailed on, "
        f"and the warm wind carried only salt and sunshine."
    )
    world.say(
        f"At the end, {hero.id} and {mate.id} waved from the bow while the rescued bird "
        f"circled safely overhead."
    )


def tell(setting: Setting, clue: Clue, hazard: Hazard, tool: Tool,
         hero_name: str = "Lena", hero_gender: str = "girl",
         mate_name: str = "Milo", mate_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    ship = world.add(Entity(id="ship", type="ship", label="the little ship"))
    clue_ent = world.add(Entity(id="clue", type="thing", label="the clue"))
    hazard_ent = world.add(Entity(id="hazard", type="thing", label=hazard.label))
    world.facts.update(setting=setting, clue=clue, hazard_cfg=hazard, tool=tool,
                       hero=hero, mate=mate, parent=parent, ship=ship,
                       clue_ent=clue_ent, hazard_ent=hazard_ent)

    setup(world, hero, mate, setting)
    world.para()
    mystery(world, hero, clue, setting)
    inspect(world, mate, clue, hazard)
    warn(world, mate, hero, hazard, tool)
    world.para()
    bind(world, hero, mate, hazard_ent, tool, hazard)
    rescue(world, setting, hero, mate)
    world.para()
    happy_end(world, hero, mate, setting)
    world.facts["solved"] = True
    return world


SETTINGS = {
    "dock": Setting("dock", "the dock", "a little dockside island", "the old netting corner", "a lost bird", "The sofa was their ship, a mop became a mast, and a chalk map showed the way."),
    "cove": Setting("cove", "the cove", "a windy cove camp", "the shadow under the sailcloth", "a hidden hatch", "The blanket became their sail, a broom became a pole, and a tin cup held their treasure map."),
}

CLUES = {
    "licorice": Clue("licorice", "a knotted black ribbon", "licorice", {"licorice", "mystery"}),
    "salted_licorice": Clue("salted_licorice", "a sticky black cord", "licorice", {"licorice", "mystery"}),
}

HAZARDS = {
    "net": Hazard("net", "the net", True, True, 3, {"bind", "suffocate"}),
    "sailrope": Hazard("sailrope", "the rope knot", True, True, 2, {"bind"}),
}

TOOLS = {
    "rope": Tool("rope", "rope", "a careful loop", "tie it loose", 3, {"bind"}),
    "cloth": Tool("cloth", "cloth", "a soft wrap", "wrap and bind it gently", 2, {"bind"}),
    "hook": Tool("hook", "hook", "a little hook line", "hook and tug the knot free", 3, {"bind"}),
}

GIRL_NAMES = ["Lena", "Mira", "Nia", "Tia", "Ava", "Zoe"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Noah", "Leo", "Eli"]
TRAITS = ["careful", "curious", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CLUES:
            for hid in HAZARDS:
                for tid in TOOLS:
                    if suspect_present(CLUES[cid], HAZARDS[hid]) and can_solve(TOOLS[tid], HAZARDS[hid]):
                        combos.append((sid, cid, hid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    hazard: str
    tool: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
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


KNOWLEDGE = {
    "licorice": [("What is licorice?", "Licorice is a sweet treat that can be black or red and has a strong taste.")],
    "bind": [("What does bind mean?", "To bind something means to tie or fasten it so it stays together.")],
    "suffocate": [("What does suffocate mean?", "To suffocate means to not get enough air, which is very dangerous.")],
    "net": [("What is a net?", "A net is a piece of string with holes in it. People use it to catch or hold things.")],
    "rope": [("What is rope for?", "Rope is a strong line that can tie things, pull things, or hold things in place.")],
    "cloth": [("What is cloth?", "Cloth is fabric. It can be used to wrap, cover, or clean things.")],
    "hook": [("What is a hook?", "A hook is a curved piece that can catch or hold onto something.")],
}
KNOWLEDGE_ORDER = ["licorice", "bind", "suffocate", "net", "rope", "cloth", "hook"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-tale mystery for a 3-to-5-year-old that includes the words "licorice", "bind", and "suffocate".',
        f"Tell a happy story where {f['hero'].id} and {f['mate'].id} solve a strange smell mystery on a little ship.",
        f"Write a child-friendly pirate story where a clue smells like licorice, a hidden danger is bound safely, and the ending is happy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, clue, hazard = f["hero"], f["mate"], f["clue"], f["hazard_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {mate.id}, two little pirates who were trying to solve a mystery together."),
        ("What strange smell did they notice?",
         f"They noticed a smell like licorice drifting from the dark corner of the deck. That was the first clue that something hidden was there."),
        ("What did they do with the danger?",
         f"They used {f['tool'].label} to bind it carefully, so it could not keep causing trouble. The safe binding helped them solve the mystery without anyone getting hurt."),
        ("How did the story end?",
         f"It ended happily. They freed the trapped bird, the air felt normal again, and the little pirates sailed on with smiles."),
    ]
    if f.get("predicted_risk", 0) >= THRESHOLD:
        qa.append((
            "Why did the mate warn the hero?",
            f"{mate.id} warned {hero.id} because the hidden thing could suffocate the air if it stayed trapped. The warning mattered because the crew needed a careful way to bind it, not a rough yank."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue"].tags) | set(world.facts["hazard_cfg"].tags) | set(world.facts["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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


CURATED = [
    StoryParams("dock", "licorice", "net", "rope", "Lena", "girl", "Milo", "boy", "mother", "careful"),
    StoryParams("cove", "salted_licorice", "sailrope", "cloth", "Mira", "girl", "Finn", "boy", "father", "curious"),
]


def explain_rejection(clue: Clue, hazard: Hazard, tool: Tool) -> str:
    if not suspect_present(clue, hazard):
        return "(No story: the licorice clue does not match this hazard, so there is no mystery to solve.)"
    if not can_solve(tool, hazard):
        return "(No story: that tool is too weak to bind the hazard safely.)"
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
suspect(C) :- clue(C), licorice(C).
danger(H) :- hazard(H), can_suffocate(H).
valid(S, C, H, T) :- setting(S), clue(C), hazard(H), tool(T), suspect(C), danger(H), tool_power(T,P), hazard_spread(H,Sv), P >= Sv.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        if "licorice" in CLUES[cid].tags:
            lines.append(asp.fact("licorice", cid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.can_suffocate:
            lines.append(asp.fact("can_suffocate", hid))
        lines.append(asp.fact("hazard_spread", hid, h.spread))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_power", tid, t.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH in ASP gate")
            rc = 1
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: empty story")
            rc = 1
    except Exception:
        traceback.print_exc()
        return 1
    try:
        print(sample.story)
    except Exception:
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale mystery world with licorice clues and safe binding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--mate")
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
    if args.clue and args.hazard and not suspect_present(CLUES[args.clue], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(CLUES[args.clue], HAZARDS[args.hazard], TOOLS[args.tool] if args.tool else TOOLS["rope"]))
    if args.tool and args.hazard and not can_solve(TOOLS[args.tool], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(CLUES[args.clue] if args.clue else CLUES["licorice"], HAZARDS[args.hazard], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.hazard is None or c[2] == args.hazard)
              and (args.tool is None or c[3] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, hazard, tool = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice(BOY_NAMES if mate_gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, clue, hazard, tool, hero, hero_gender, mate, mate_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], HAZARDS[params.hazard], TOOLS[params.tool], params.hero, params.hero_gender, params.mate, params.mate_gender, params.parent)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
