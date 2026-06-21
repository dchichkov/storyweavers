#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chocolate_romp_churn_twist_comedy.py
=====================================================================

A compact, child-facing storyworld about a kitchen romp that goes comic, gets
churned into trouble, and turns with a surprise twist: the mess becomes a sweet
shared treat instead of a disaster.

Seed words:
- chocolate
- romp
- churn

Style:
- comedy

Instrument:
- twist

The world is built as a small state machine with typed entities, physical meters,
emotional memes, a reasonableness gate, an ASP twin, and three QA sets grounded
in the simulated state.
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    churn_kind: str
    can_spill: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Space:
    id: str
    scene: str
    twist_spot: str
    spill_hint: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class TwistTool:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["churned"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["sticky"] += 1
        for kid in list(world.entities.values()):
            if kid.role in {"romper", "helper"}:
                kid.memes["alarm"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for space_id, space in SPACES.items():
        for treat_id, treat in TREATS.items():
            for tool_id, tool in TOOLS.items():
                for repair_id, repair in REPAIRS.items():
                    if treat.can_spill and tool.sense >= SENSE_MIN and repair.sense >= SENSE_MIN:
                        combos.append((space_id, treat_id, tool_id, repair_id))
    return combos


def sensible_tools() -> list[str]:
    return [k for k, v in TOOLS.items() if v.sense >= SENSE_MIN]


def fire_churn_amount(tool: TwistTool, treat: Treat) -> int:
    return 1 if tool.power >= 1 and treat.can_spill else 0


def can_fix(repair: Repair, churn_amount: int) -> bool:
    return repair.power >= churn_amount


def _do_churn(world: World, treat_ent: Entity, tool: TwistTool, treat: Treat, narrate: bool = True) -> None:
    treat_ent.meters["churned"] += fire_churn_amount(tool, treat)
    propagate(world, narrate=narrate)


def predict(world: World, treat_id: str, tool_id: str) -> dict:
    sim = world.copy()
    treat_ent = sim.get(treat_id)
    _do_churn(sim, treat_ent, TOOLS[tool_id], TREATS[treat_id], narrate=False)
    return {"spill": sim.get("floor").meters["sticky"] >= THRESHOLD}


def start(world: World, kid: Entity, helper: Entity, space: Space) -> None:
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {kid.id} and {helper.id} turned {space.scene} into a romp. "
        f"{space.spill_hint}"
    )
    world.say(f'They kept giggling, because every good romp feels a little too big for the room.')


def want_chocolate(world: World, kid: Entity, treat: Treat) -> None:
    kid.memes["desire"] += 1
    world.say(
        f'{kid.id} spotted {treat.phrase}. "{treat.label.capitalize()}!" {kid.id} said. '
        f'"We can use it for a funny snack parade!"'
    )


def warn(world: World, helper: Entity, kid: Entity, treat: Treat, space: Space) -> None:
    pred = predict(world, treat.id, "twister")
    helper.memes["caution"] += 1
    if pred["spill"]:
        world.say(
            f'{helper.id} laughed, then wrinkled {helper.pronoun("possessive")} nose. '
            f'"If you churn that {treat.label} too hard, it will splat all over {space.twist_spot}. '
            f'We will be wiping it off for ages."'
        )
    else:
        world.say(f'"Maybe a tiny twist only," {helper.id} said, trying not to grin.')


def twist(world: World, kid: Entity, helper: Entity, treat_ent: Entity, treat: Treat, tool: TwistTool) -> None:
    kid.memes["determination"] += 1
    world.say(
        f'{kid.id} grabbed {tool.phrase} and gave the {treat.label} a grand {tool.action}. '
        f'For one second it looked impressive. Then the chocolate started to churn.'
    )
    _do_churn(world, treat_ent, tool, treat)
    world.say(
        f"The chocolate zigged, zagged, and flopped. One thick splat landed on the floor, "
        f"and another landed on {helper.id}'s sleeve."
    )


def twist_tension(world: World, kid: Entity, helper: Entity, treat: Treat) -> None:
    if world.get("floor").meters["sticky"] >= THRESHOLD:
        world.say(
            f'{helper.id} blinked at the sticky spot and said, "Well, that is a very committed chocolate."'
        )
    kid.memes["embarrassment"] += 1


def repair_scene(world: World, parent: Entity, repair: Repair, treat: Treat) -> None:
    world.get("floor").meters["sticky"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} came in with {repair.phrase}. In a quick, calm move, '
        f'{parent.pronoun()} used it to fix the mess before it spread any farther.'
    )
    world.say(
        f"The room smelled like chocolate instead of trouble, and the silly spill turned into a clean joke."
    )


def twist_ending(world: World, parent: Entity, kid: Entity, helper: Entity, treat: Treat, space: Space) -> None:
    for e in (kid, helper):
        e.memes["joy"] += 1
        e.memes["relief"] += 1
    world.say(
        f'Then {parent.label_word.capitalize()} had a twist: {parent.pronoun()} scraped the chocolate into a bowl, '
        f"added milk, and called it a lucky treat."
    )
    world.say(
        f'{kid.id} stared, then laughed. "We made dessert!" {kid.id} said. '
        f"{helper.id} tasted it and nearly snorted from giggling."
    )
    world.say(
        f'By bedtime, the floor was shiny again, and the only thing left from the romp was a little bowl of chocolate.'
    )


def narrate_story(world: World, kid: Entity, helper: Entity, parent: Entity, space: Space,
                  treat: Treat, tool: TwistTool, repair: Repair) -> None:
    start(world, kid, helper, space)
    world.para()
    want_chocolate(world, kid, treat)
    warn(world, helper, kid, treat, space)
    world.para()
    twist(world, kid, helper, world.get("treat"), treat, tool)
    twist_tension(world, kid, helper, treat)
    world.para()
    repair_scene(world, parent, repair, treat)
    twist_ending(world, parent, kid, helper, treat, space)


@dataclass
class StoryParams:
    space: str
    treat: str
    tool: str
    repair: str
    kid_name: str
    kid_gender: str
    helper_name: str
    helper_gender: str
    parent_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SPACES = {
    "kitchen": Space(id="kitchen", scene="the kitchen floor into a silly romp", twist_spot="the tiles", spill_hint="The table was set for snacks, and the spoon was already doing its own dance."),
    "picnic": Space(id="picnic", scene="a picnic blanket into a comedy stage", twist_spot="the blanket", spill_hint="The lemonade trembled beside the basket as if it knew jokes were coming."),
    "bakery": Space(id="bakery", scene="the bakery counter into a romp", twist_spot="the counter", spill_hint="The sweet smell of sugar made everything feel one sneeze away from chaos."),
}

TREATS = {
    "chocolate": Treat(id="chocolate", label="chocolate", phrase="a glossy bowl of chocolate", churn_kind="melty", can_spill=True, tags={"chocolate", "sweet"}),
    "pudding": Treat(id="pudding", label="pudding", phrase="a wobbly cup of pudding", churn_kind="wobbly", can_spill=True, tags={"sweet"}),
    "sauce": Treat(id="sauce", label="sauce", phrase="a spoonful of chocolate sauce", churn_kind="drippy", can_spill=True, tags={"chocolate", "sauce"}),
}

TOOLS = {
    "twister": TwistTool(id="twister", label="twister", phrase="a whisk-shaped twister", action="whisk-twirl", power=1, sense=2, tags={"twist"}),
    "spoon": TwistTool(id="spoon", label="spoon", phrase="a giant spoon", action="stir-spin", power=1, sense=2, tags={"twist"}),
    "fan": TwistTool(id="fan", label="fan", phrase="a tiny hand fan", action="fan-flutter", power=1, sense=2, tags={"twist"}),
}

REPAIRS = {
    "napkins": Repair(id="napkins", label="napkins", phrase="a stack of napkins", power=1, sense=2, tags={"cleanup"}),
    "towel": Repair(id="towel", label="towel", phrase="a big kitchen towel", power=1, sense=2, tags={"cleanup"}),
    "bowl": Repair(id="bowl", label="bowl", phrase="a spare mixing bowl", power=1, sense=2, tags={"cleanup", "dessert"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Max", "Sam"]


def explain_rejection(space: Space, treat: Treat, tool: TwistTool, repair: Repair) -> str:
    return "(No story: the chosen pieces do not make a sensible comedy twist.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy storyworld about chocolate, a romp, and a twist.")
    ap.add_argument("--space", choices=SPACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.space or args.treat or args.tool or args.repair:
        combos = [c for c in combos if
                  (args.space is None or c[0] == args.space) and
                  (args.treat is None or c[1] == args.treat) and
                  (args.tool is None or c[2] == args.tool) and
                  (args.repair is None or c[3] == args.repair)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    space, treat, tool, repair = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    kid_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(space=space, treat=treat, tool=tool, repair=repair,
                       kid_name=kid_name, kid_gender=gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("space", SPACES), ("treat", TREATS), ("tool", TOOLS), ("repair", REPAIRS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = World()
    kid = world.add(Entity(id=params.kid_name, kind="character", type=params.kid_gender, role="romper"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent", label="the parent"))
    floor = world.add(Entity(id="floor", type="floor", label="the floor"))
    treat_ent = world.add(Entity(id="treat", type="treat", label=TREATS[params.treat].label))
    narrate_story(world, kid, helper, parent, SPACES[params.space], TREATS[params.treat], TOOLS[params.tool], REPAIRS[params.repair])
    world.facts.update(kid=kid, helper=helper, parent=parent, space=SPACES[params.space], treat_cfg=TREATS[params.treat], tool=TOOLS[params.tool], repair=REPAIRS[params.repair], treat=treat_ent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=[QAItem(q, a) for q, a in story_qa(world)], world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a preschooler that includes the words "chocolate", "romp", and "twist".',
        f"Tell a comic story where {f['kid'].id} and {f['helper'].id} make a romp out of {f['space'].scene} and a chocolate spill turns into a surprise.",
        f"Write a short, playful story with a twist ending where chocolate becomes part of the joke instead of a problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, helper, parent = f["kid"], f["helper"], f["parent"]
    treat_cfg, space = f["treat_cfg"], f["space"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id}, {helper.id}, and {parent.label_word}. They are the three people at the center of the chocolate romp."),
        ("What did the children want to do?",
         f"They wanted a romp with {treat_cfg.label}. That choice made the kitchen feel funny before the twist changed the mood."),
        ("Why did the helper warn them?",
         f"{helper.id} warned them because a hard churn would make chocolate spill onto {space.twist_spot}. The helper could already picture the mess in the world state."),
        ("How did the story end?",
         f"It ended as a joke and a treat. The mess was turned into something sweet, so the ending felt silly instead of upsetting."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is chocolate?",
         "Chocolate is a sweet food made from cocoa. It can melt and make a sticky mess if it gets warm."),
        ("What does churn mean?",
         "To churn means to mix or turn something around and around. If you churn something soft too much, it can splash or spill."),
        ("What is a twist in a story?",
         "A twist is a surprise change. It makes the story go in a new direction the listener did not expect."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(space="kitchen", treat="chocolate", tool="twister", repair="bowl", kid_name="Mia", kid_gender="girl", helper_name="Ben", helper_gender="boy", parent_type="mother"),
    StoryParams(space="picnic", treat="pudding", tool="spoon", repair="napkins", kid_name="Leo", kid_gender="boy", helper_name="Nora", helper_gender="girl", parent_type="father"),
    StoryParams(space="bakery", treat="sauce", tool="fan", repair="towel", kid_name="Zoe", kid_gender="girl", helper_name="Sam", helper_gender="boy", parent_type="mother"),
]


ASP_RULES = r"""
valid(S,T,U,R) :- space(S), treat(T), tool(U), repair(R), sense_tool(U), sense_repair(R).
spill(T) :- treat(T), can_spill(T).
twist(T,U) :- spill(T), tool(U).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SPACES:
        lines.append(asp.fact("space", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.can_spill:
            lines.append(asp.fact("can_spill", tid))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        lines.append(asp.fact("sense_tool", uid))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense_repair", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(asp_program("", "#show valid/4."))
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
