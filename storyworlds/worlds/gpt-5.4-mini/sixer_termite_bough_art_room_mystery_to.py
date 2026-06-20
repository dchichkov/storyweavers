#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sixer_termite_bough_art_room_mystery_to.py
===========================================================================

A standalone story world for a small superhero mystery in an art room.

Seed-inspired premise:
- A kid hero and a helper investigate a strange mess in the art room.
- Clues include the seed words: sixer, termite, bough.
- The mystery resolves through observation, a clever reveal, and a fix that
  changes the room state in a way the ending image can prove.

The world is intentionally small and classical:
- typed entities with meters and memes,
- a forward-chained rule engine,
- a reasonableness gate,
- an inline ASP twin,
- and three Q&A sets grounded in simulated state.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    label: str
    details: str
    mystery_spots: list[str] = field(default_factory=list)

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
    phrase: str
    kind: str
    suspicious: bool = False
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
    helps: str
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
class Reasoning:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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
        if e.meters["mystery"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "hero" in world.entities:
            world.get("hero").memes["focus"] += 1
        out.append("__worry__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("found_termite") and "hero" in world.entities:
        sig = ("clue", "termite")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["certainty"] += 1
            out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("clue", "social", _r_clue)]


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


def sensible_reasonings() -> list[Reasoning]:
    return [r for r in REASONINGS.values() if r.sense >= SENSE_MIN]


def valid_combo(setting: Setting, clue: Clue, tool: Tool) -> bool:
    return setting.id == "art_room" and clue.suspicious and clue.kind in tool.helps


def needs_hypothesis(clue: Clue, tool: Tool) -> bool:
    return clue.suspicious and clue.kind in tool.helps


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _inspect_clue(sim, sim.get(clue_id), narrate=False)
    return {
        "mystery": sim.get(clue_id).meters["mystery"],
        "found": sim.facts.get("found_termite", False),
    }


def _inspect_clue(world: World, clue: Entity, narrate: bool = True) -> None:
    clue.meters["mystery"] += 0
    world.facts["found_termite"] = clue.attrs.get("termite", False)
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["bravery"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In the art room, {hero.id} and {helper.id} looked at the bright tables, "
        f"the paint cups, and the paper wall. {setting.details}"
    )
    world.say(
        f'{hero.id} wore a tiny cape and said, "We solve mysteries here." '
        f"{helper.id} nodded, ready to help."
    )


def trouble(world: World, clue: Entity, hero: Entity) -> None:
    hero.meters["mystery"] += 1
    clue.meters["mystery"] += 1
    world.say(
        f"Then they found {clue.phrase}. It looked odd among the paints and glue. "
        f"{clue.label_word.capitalize()} did not belong in the art room."
    )


def ask_about_clue(world: World, hero: Entity, helper: Entity, clue: Entity, tool: Tool) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["focus"] += 1
    world.say(
        f'"{clue.label_word.capitalize()}," said {hero.id}, pointing with a gloved hand. '
        f'"And that little hole near the shelves. It feels like a clue."'
    )
    world.say(
        f'{helper.id} squinted. "It might be tiny trouble, and {tool.phrase} could help us look."'
    )


def reveal(world: World, hero: Entity, clue: Entity) -> None:
    hero.memes["certainty"] += 1
    if clue.attrs.get("termite"):
        world.facts["found_termite"] = True
        world.say(
            f"{hero.id} crouched low and followed the crumb trail. Behind the bough-shaped "
            f"mobile, a small termite tunnel showed in the wood."
        )
        world.say(
            f'"A termite!" {hero.id} cried. "That is why the bough was crumbling."'
        )
    else:
        world.say(
            f"{hero.id} checked the mark twice and found that the clue was only a smudge."
        )


def fix(world: World, hero: Entity, helper: Entity, tool: Tool, clue: Clue) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    clue.meters["mystery"] = 0.0
    world.get("room").meters["safe"] = 1.0
    world.say(
        f"{helper.id} brought {tool.phrase}, and {hero.id} used it to mark the damaged spot. "
        f"Then they called a grown-up to move the art away from the weak bough."
    )
    world.say(
        f"The room felt calm again. The strange mark was no longer a mystery, and the art table "
        f"stood tidy under the painted lights."
    )


def ending_image(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"By the end, {hero.id}'s cape hung straight, {helper.id} smiled, and the art room was "
        f"quiet except for the soft tap of brushes drying in a cup."
    )


def tell(setting: Setting, clue: Clue, tool: Tool,
         hero_name: str = "Nova", helper_name: str = "Scout",
         hero_type: str = "girl", helper_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    room = world.add(Entity(id="room", type="room", label="the art room"))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label, attrs={"termite": clue.id == "termite"}))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label))

    setup(world, hero, helper, setting)
    world.para()
    trouble(world, clue_ent, hero)
    ask_about_clue(world, hero, helper, clue_ent, tool)
    reveal(world, hero, clue_ent)
    world.para()
    fix(world, hero, helper, tool, clue_ent)
    ending_image(world, hero, helper)

    world.facts.update(
        hero=hero, helper=helper, room=room, clue_cfg=clue, clue=clue_ent, tool_cfg=tool,
        tool=tool_ent, setting=setting, found_termite=bool(clue_ent.attrs.get("termite")),
        resolved=True, ending="solved",
    )
    return world


SETTINGS = {
    "art_room": Setting(
        "art_room",
        "the art room",
        "The sunlight made the paint jars sparkle, and the big paper wall glowed like a poster.",
        mystery_spots=["behind the bough-shaped mobile", "under the easel", "by the shelf of clay"],
    ),
}

CLUES = {
    "termite": Clue(
        "termite",
        "termite tunnel",
        "a tiny termite tunnel in the wood",
        kind="wood",
        suspicious=True,
        tags={"termite", "wood", "mystery"},
    ),
    "bough": Clue(
        "bough",
        "bough",
        "a brittle bough from a prop tree",
        kind="wood",
        suspicious=True,
        tags={"bough", "wood", "mystery"},
    ),
    "sixer": Clue(
        "sixer",
        "sixer badge",
        "a sixer badge left on the table",
        kind="paper",
        suspicious=False,
        tags={"sixer", "paper"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        "magnifier",
        "magnifier",
        "a small magnifier",
        helps="wood",
        tags={"magnifier", "inspect"},
    ),
    "ruler": Tool(
        "ruler",
        "ruler",
        "a long ruler",
        helps="wood",
        tags={"ruler", "measure"},
    ),
    "flashlight": Tool(
        "flashlight",
        "flashlight",
        "a flashlight",
        helps="wood",
        tags={"flashlight", "inspect"},
    ),
}

REASONINGS = {
    "inspect": Reasoning(
        "inspect",
        3,
        3,
        "looked closely with the magnifier and found the hidden damage",
        "looked, but the clue was too small and nothing useful was found",
        "looked closely and found the hidden damage",
        tags={"inspect", "wood"},
    ),
    "measure": Reasoning(
        "measure",
        2,
        2,
        "measured the crack and marked the weak spot",
        "measured it, but the mark was too fuzzy to help",
        "measured the crack and marked the weak spot",
        tags={"measure", "wood"},
    ),
    "shield": Reasoning(
        "shield",
        2,
        2,
        "covered the art with paper so the rest of the room stayed safe",
        "tried to cover it, but the paper did not fit",
        "covered the art so the room stayed safe",
        tags={"shield"},
    ),
}

GAMES = [
    ("art_room", "termite", "magnifier"),
    ("art_room", "bough", "ruler"),
    ("art_room", "termite", "flashlight"),
]

GIRL_NAMES = ["Nova", "Mira", "Luna", "Ada", "Ivy", "Zoe"]
BOY_NAMES = ["Scout", "Pip", "Finn", "Jace", "Theo", "Leo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
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
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for tid, tool in TOOLS.items():
                if valid_combo(setting, clue, tool):
                    out.append((sid, cid, tid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero art-room mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
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


def explain_rejection(clue: Clue, tool: Tool) -> str:
    return f"(No story: {tool.label} does not help solve a {clue.label} mystery in the art room.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.tool:
        if not valid_combo(SETTINGS[args.setting or "art_room"], CLUES[args.clue], TOOLS[args.tool]):
            raise StoryError(explain_rejection(CLUES[args.clue], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, tool = rng.choice(sorted(combos))
    hero_type = rng.choice(["girl", "boy"])
    helper_type = "boy" if hero_type == "girl" else "girl"
    hero = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = rng.choice([n for n in (BOY_NAMES if helper_type == "boy" else GIRL_NAMES) if n != hero])
    return StoryParams(setting, clue, tool, hero, hero_type, helper, helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a superhero-style art room mystery for a child that includes the words "sixer", "termite", and "bough".',
        f"Tell a bright mystery story where {f['hero'].id} and {f['helper'].id} investigate a strange clue in the art room and discover what damaged the bough.",
        "Write a short superhero mystery with a child hero, a careful helper, and an ending that shows the art room became safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, clue = f["hero"], f["helper"], f["clue_cfg"]
    qa = [
        ("Who solved the mystery?",
         f"{hero.id} and {helper.id} solved it together in the art room."),
        ("What strange thing did they find?",
         f"They found {clue.phrase}, which looked out of place among the paints and paper."),
        ("What did they learn was causing the trouble?",
         "They learned a termite had made a tunnel in the wood, which is why the bough was weakening."),
        ("How did the story end?",
         "The mystery was solved, the damage was marked, and the art room was safe and calm again."),
    ]
    if f.get("found_termite"):
        qa.append((
            "Why was the clue important?",
            f"It pointed them to a termite problem, and that explained why the bough was getting brittle. "
            f"Without that clue, they would have guessed wrong."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue_cfg"].tags) | set(world.facts["tool_cfg"].tags)
    out = []
    if "termite" in tags:
        out.append(("What is a termite?", "A termite is a tiny insect that can chew wood and make holes inside it."))
    if "bough" in tags:
        out.append(("What is a bough?", "A bough is a large tree branch. It can bend, break, or get weak if something eats into it."))
    if "sixer" in tags or True:
        out.append(("What is a sixer badge?", "In this story, a sixer badge is a little paper badge. It is part of the art room game, not the mystery itself."))
    out.append(("What does a magnifier do?", "A magnifier makes small things look bigger so you can inspect them more carefully."))
    return out


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
        if e.attrs:
            bits.append(f"attrs={ {k: v for k, v in e.attrs.items() if v} }")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
suspicious(C) :- clue(C), suspicious_clue(C).
valid(S, C, T) :- setting(S), clue(C), tool(T), suspicious(C), helps(T, wood), art_room(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if sid == "art_room":
            lines.append(asp.fact("art_room", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.suspicious:
            lines.append(asp.fact("suspicious_clue", cid))
        lines.append(asp.fact("kind", cid, c.kind))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps", tid, t.helps))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, tool=None), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], TOOLS[params.tool], params.hero, params.helper, params.hero_type, params.helper_type)
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
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, c, t, "Nova", "girl", "Scout", "boy")) for s, c, t in GAMES]
    else:
        seen: set[str] = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
