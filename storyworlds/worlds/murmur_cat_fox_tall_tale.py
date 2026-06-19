#!/usr/bin/env python3
"""
storyworlds/worlds/murmur_cat_fox_tall_tale.py
==============================================

Seed prompt used:
    Write a story that includes the following words and narrative instruments.
    Words: murmur, wondrous cat, shiny fox
    Features: Suspense, Foreshadowing
    Style: Tall Tale

Source tale written from the seed:
    In Brambleton, the moon could be polished and the creek could whisper your
    name. One evening, Pip heard a murmur under the old mill. His wondrous cat
    Whiskerbell arched her back, and a shiny fox flashed past with silver dust on
    its paws. Everyone wanted to chase the fox, but the cat listened first. She
    knew the sound was a loose mill wheel, not a trickster's laugh. Pip wedged the
    wheel before it cracked loose. The twist was that the shiny fox had been
    running for help, carrying the clue on its paws.

This storyworld keeps that logic in state. A murmur means a real local problem;
the shiny fox looks suspicious, but only the wondrous cat can turn its clue into
the correct source. A story is refused unless the clue points to the source and
the chosen tool actually fixes it.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    tall_detail: str
    affords: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class MurmurSource:
    id: str
    label: str
    sound: str
    risk: str
    danger_line: str
    fixed_image: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    fox_mark: str
    points_to: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    action: str
    fixes: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place, source: MurmurSource) -> None:
        self.place = place
        self.source = source
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.active_clue: Optional[Clue] = None
        self.active_tool: Optional[Tool] = None
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def role(self, role: str) -> Entity:
        for ent in self.entities.values():
            if ent.role == role:
                return ent
        raise KeyError(role)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place, self.source)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.active_clue = self.active_clue
        clone.active_tool = self.active_tool
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def clue_points(clue: Clue, source: MurmurSource) -> bool:
    return source.id in clue.points_to


def tool_fixes(tool: Tool, source: MurmurSource) -> bool:
    return source.id in tool.fixes


def _r_murmur_worry(world: World) -> list[str]:
    source = world.get("source")
    town = world.get("town")
    if source.meters["murmuring"] < THRESHOLD:
        return []
    sig = ("murmur_worry", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    town.memes["unease"] += 1
    return []


def _r_false_suspicion(world: World) -> list[str]:
    fox = world.role("messenger")
    hero = world.role("hero")
    town = world.get("town")
    if fox.memes["seen"] < THRESHOLD or town.memes["unease"] < THRESHOLD:
        return []
    if world.active_clue and clue_points(world.active_clue, world.source):
        return []
    sig = ("false_suspicion", fox.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspicion"] += 1
    town.memes["suspicion"] += 1
    return ["For one long blink, everybody thought the shiny fox had made the murmur."]


def _r_cat_insight(world: World) -> list[str]:
    cat = world.role("helper")
    hero = world.role("hero")
    if cat.memes["listening"] < THRESHOLD or not world.active_clue:
        return []
    if not clue_points(world.active_clue, world.source):
        return []
    sig = ("cat_insight", world.active_clue.id, world.source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cat.memes["insight"] += 1
    hero.memes["trust_cat"] += 1
    hero.memes["suspicion"] = 0.0
    return []


def _r_repair(world: World) -> list[str]:
    source = world.get("source")
    fox = world.role("messenger")
    town = world.get("town")
    if not world.active_tool or source.meters["murmuring"] < THRESHOLD:
        return []
    if not tool_fixes(world.active_tool, world.source):
        return []
    sig = ("repair", world.active_tool.id, world.source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["murmuring"] = 0.0
    source.meters["safe"] += 1
    fox.memes["trusted"] += 1
    town.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule("murmur_worry", _r_murmur_worry),
    Rule("false_suspicion", _r_false_suspicion),
    Rule("cat_insight", _r_cat_insight),
    Rule("repair", _r_repair),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def start_murmur(world: World) -> None:
    world.get("source").meters["murmuring"] += 1
    propagate(world, narrate=False)


def predict_chase(world: World) -> dict:
    sim = world.copy()
    sim.role("messenger").memes["chased"] += 1
    sim.get("source").meters["danger"] += 1
    sim.get("town").memes["confusion"] += 1
    return {
        "danger": sim.get("source").meters["danger"],
        "risk": world.source.risk,
    }


def introduce(world: World, hero: Entity, cat: Entity) -> None:
    hero.memes["wonder"] += 1
    cat.memes["wonder"] += 1
    world.say(
        f"In {world.place.label}, {world.place.tall_detail}. "
        f"{hero.id} lived there with a wondrous cat named {cat.id}, "
        f"whose whiskers could hear around corners."
    )


def foreshadow(world: World, source: MurmurSource) -> None:
    cat = world.role("helper")
    start_murmur(world)
    world.say(
        f"One peach-purple evening, a murmur slipped from {source.label}: "
        f"{source.sound}."
    )
    world.say(
        "The chickens stopped counting clouds, the porch boards held their breath, "
        f"and {cat.id}'s tail made a question mark."
    )


def fox_appears(world: World, clue: Clue) -> None:
    fox = world.role("messenger")
    fox.memes["seen"] += 1
    fox.memes["carrying_clue"] += 1
    world.say(
        f"Then a shiny fox flashed by the fence, bright as a spoon in moonlight, "
        f"with {clue.fox_mark}."
    )
    propagate(world, narrate=True)


def cat_warns(world: World, hero: Entity, cat: Entity, clue: Clue) -> None:
    pred = predict_chase(world)
    cat.memes["listening"] += 1
    world.active_clue = clue
    propagate(world, narrate=False)
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{cat.id} pressed one ear to the ground. "Do not chase the shine," '
        f"the wondrous cat seemed to say. If they chased the fox, "
        f"{world.source.danger_line}."
    )
    world.say(
        f"{hero.id} looked again at {clue.label}, and the clue pointed away "
        f"from blame and toward {world.source.label}."
    )


def choose_tool(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["resolve"] += 1
    world.active_tool = tool
    world.say(
        f"So {hero.id} grabbed {tool.label} and ran where the murmur was thickest. "
        f"{tool.action}."
    )
    propagate(world, narrate=False)


def reveal(world: World, hero: Entity, cat: Entity, tool: Tool) -> None:
    source = world.get("source")
    fox = world.role("messenger")
    if source.meters["safe"] >= THRESHOLD:
        world.say(
            f"The murmur folded down to a purr. {world.source.fixed_image}"
        )
        world.say(
            f"And then came the twist, tall as a weather vane: the shiny fox "
            f"had not caused the trouble at all. It had carried the clue to "
            f"{hero.id} and {cat.id}."
        )
        world.say(
            f"{fox.id} bowed so low its tail dusted the road, and {cat.id} "
            f"blinked like a queen. From that day on, when {world.place.label} "
            f"heard a murmur, it listened before it blamed."
        )
    else:
        world.say(
            f"{tool.label.capitalize()} did not quiet the murmur, so the fox "
            f"vanished with the clue and everyone had to begin again."
        )


def tell(place: Place, source: MurmurSource, clue: Clue, tool: Tool,
         name: str = "Pip", gender: str = "boy", cat_name: str = "Whiskerbell",
         fox_name: str = "Gleam", trait: str = "curious") -> World:
    world = World(place, source)
    hero = world.add(Entity(name, kind="character", type=gender, label=name,
                            role="hero", traits=[trait]))
    cat = world.add(Entity(cat_name, kind="character", type="cat", label="wondrous cat",
                           role="helper", traits=["wondrous"]))
    world.add(Entity(fox_name, kind="character", type="fox", label="shiny fox",
                     role="messenger", traits=["shiny"]))
    world.add(Entity("town", type="town", label=place.label))
    world.add(Entity("source", type="source", label=source.label))

    introduce(world, hero, cat)
    foreshadow(world, source)
    world.para()
    fox_appears(world, clue)
    cat_warns(world, hero, cat, clue)
    world.para()
    choose_tool(world, hero, tool)
    reveal(world, hero, cat, tool)
    world.facts.update(hero=hero, cat=cat, fox=world.role("messenger"),
                       place=place, source=source, clue=clue, tool=tool,
                       resolved=world.get("source").meters["safe"] >= THRESHOLD)
    return world


PLACES = {
    "brambleton": Place("brambleton", "Brambleton",
                        "the moon could be polished and the creek could whisper your name",
                        {"mill_wheel", "stream_gate", "bee_box"},
                        tags={"village"}),
    "thistle_fair": Place("thistle_fair", "Thistle Fair",
                          "pies cooled on windowsills as tall as haystacks",
                          {"bee_box", "bell_rope", "stream_gate"},
                          tags={"fair"}),
    "copper_hollow": Place("copper_hollow", "Copper Hollow",
                           "every roof rang softly when the evening star came out",
                           {"mill_wheel", "bell_rope"},
                           tags={"hollow"}),
}

SOURCES = {
    "mill_wheel": MurmurSource("mill_wheel", "the old mill wheel",
                               "rub-rub-rumble, like a giant clearing its throat",
                               "the wheel would crack loose",
                               "the wheel might shake free before anyone fixed it",
                               "The old mill wheel turned round and true, dipping silver water without a wobble.",
                               tags={"mill", "repair"}),
    "stream_gate": MurmurSource("stream_gate", "the stream gate",
                                "glug-glug-mmm, like a jug trying to sing",
                                "the lane would flood",
                                "the gate might spill the creek into the lane",
                                "The stream slid back into its channel and stopped nibbling at the road.",
                                tags={"water", "flood"}),
    "bee_box": MurmurSource("bee_box", "the bee box",
                            "bzz-mmm-bzz, like a secret wrapped in wings",
                            "the bees would swarm",
                            "the bees might pour out in a frightened cloud",
                            "The bees settled into a golden hush around their box.",
                            tags={"bees", "care"}),
    "bell_rope": MurmurSource("bell_rope", "the tower bell rope",
                              "hum-hum-hong, like thunder in a teacup",
                              "the bell would crash down",
                              "the loose rope might yank the bell from its hook",
                              "The bell hung steady and rang one tiny thank-you note.",
                              tags={"bell", "repair"}),
}

CLUES = {
    "silver_sawdust": Clue("silver_sawdust", "silver sawdust on the fox's paws",
                           "silver sawdust glittering on its paws",
                           {"mill_wheel"}, tags={"wood", "fox"}),
    "wet_pawprints": Clue("wet_pawprints", "wet pawprints shining behind the fox",
                          "wet pawprints sparkling behind it",
                          {"stream_gate"}, tags={"water", "fox"}),
    "pollen_tail": Clue("pollen_tail", "gold pollen trembling on the fox's tail",
                        "gold pollen trembling on its tail",
                        {"bee_box"}, tags={"bees", "fox"}),
    "copper_thread": Clue("copper_thread", "a copper thread caught in the fox's fur",
                          "a copper thread caught in its fur",
                          {"bell_rope"}, tags={"bell", "fox"}),
}

TOOLS = {
    "wooden_wedge": Tool("wooden_wedge", "a wooden wedge",
                         "The wedge held the loose axle until the wheel stopped shuddering",
                         {"mill_wheel"}, tags={"repair", "wood"}),
    "sandbag": Tool("sandbag", "a sandbag",
                    "The sandbag pressed against the stream gate and sealed the hungry gap",
                    {"stream_gate"}, tags={"water", "flood"}),
    "spare_hive": Tool("spare_hive", "a spare hive box",
                       "The spare hive box gave the bees room to calm down",
                       {"bee_box"}, tags={"bees", "care"}),
    "new_knot": Tool("new_knot", "a new bell knot",
                     "The new knot held tight, and the rope stopped humming against the hook",
                     {"bell_rope"}, tags={"bell", "repair"}),
}

GIRL_NAMES = ["Mira", "Lila", "Nell", "Ava", "Rose"]
BOY_NAMES = ["Pip", "Theo", "Finn", "Jory", "Sam"]
CAT_NAMES = ["Whiskerbell", "Marmalade", "Moonbutton", "Velvet"]
FOX_NAMES = ["Gleam", "Silverstep", "Brightbrush", "Sparks"]
TRAITS = ["curious", "careful", "brave", "sharp-eyed", "kind"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if source_id not in place.affords:
                continue
            for clue_id, clue in CLUES.items():
                if not clue_points(clue, source):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_fixes(tool, source):
                        combos.append((place_id, source_id, clue_id, tool_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    source: str
    clue: str
    tool: str
    name: str
    gender: str
    cat: str
    fox: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "fox": [("What is a fox?",
             "A fox is a small wild animal with a pointed nose and a bushy tail. In stories, foxes are often clever, but this one is helpful.")],
    "mill": [("What does a mill wheel do?",
              "A mill wheel turns with water or wind and helps run a mill. If it gets loose, it can break or be dangerous.")],
    "water": [("Why can a small leak become a flood?",
               "Water keeps flowing through any gap it finds. If the gap grows, more water can spill out and flood a path.")],
    "bees": [("Why should bees be handled gently?",
              "Bees can get frightened if their home is crowded or bumped. Gentle care helps them settle and keeps everyone safer.")],
    "bell": [("Why does a bell rope need to be tied well?",
              "A bell rope helps move a heavy bell. If it is loose, the bell can swing the wrong way or even fall.")],
    "repair": [("Why is it smart to fix small problems early?",
                "Small problems are easier to fix before they grow. Listening early can keep everyone safe.")],
}
KNOWLEDGE_ORDER = ["fox", "mill", "water", "bees", "bell", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a suspenseful tall tale using the words "murmur", "wondrous cat", and "shiny fox" with foreshadowing.',
        f"Tell a story where {f['hero'].id} hears a murmur, suspects a shiny fox, "
        f"but trusts a wondrous cat and fixes {f['source'].label}.",
        f"Write a tall tale where the fox seems guilty at first, but the twist reveals it was carrying a clue: {f['clue'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, cat, fox = f["hero"], f["cat"], f["fox"]
    source, clue, tool = f["source"], f["clue"], f["tool"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, the wondrous cat {cat.id}, and the shiny fox {fox.id}."),
        ("What created the suspense?",
         f"A murmur came from {source.label}, and then the shiny fox flashed by with {clue.fox_mark}. For a moment, it looked as if the fox might be causing the trouble."),
        ("Why did the cat stop the chase?",
         f"The cat listened before blaming the fox. The world model predicted that chasing the fox would let the real problem grow until {source.risk}."),
        ("What did the clue mean?",
         f"The clue, {clue.label}, pointed to {source.label}. It made the fox a messenger instead of the culprit."),
        ("How was the problem solved?",
         f"{hero.id} used {tool.label}. {tool.action}, so the murmur quieted and {source.fixed_image.lower()}"),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source"].tags) | set(world.facts["clue"].tags) | set(world.facts["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  clue: {world.active_clue.id if world.active_clue else 'none'}")
    lines.append(f"  tool: {world.active_tool.id if world.active_tool else 'none'}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("brambleton", "mill_wheel", "silver_sawdust", "wooden_wedge",
                "Pip", "boy", "Whiskerbell", "Gleam", "curious"),
    StoryParams("brambleton", "stream_gate", "wet_pawprints", "sandbag",
                "Mira", "girl", "Moonbutton", "Silverstep", "careful"),
    StoryParams("thistle_fair", "bee_box", "pollen_tail", "spare_hive",
                "Nell", "girl", "Marmalade", "Brightbrush", "kind"),
    StoryParams("copper_hollow", "bell_rope", "copper_thread", "new_knot",
                "Theo", "boy", "Velvet", "Sparks", "sharp-eyed"),
]


def explain_rejection(source: MurmurSource, clue: Optional[Clue], tool: Optional[Tool]) -> str:
    if clue and not clue_points(clue, source):
        return (
            f"(No story: {clue.label} does not point to {source.label}. "
            "The fox's clue must identify the real source of the murmur.)"
        )
    if tool and not tool_fixes(tool, source):
        return (
            f"(No story: {tool.label} does not fix {source.label}. "
            "The ending must repair the problem that made the murmur.)"
        )
    return "(No story: the requested place, clue, and tool do not make one reasonable mystery.)"


ASP_RULES = r"""
true_clue(C,S) :- clue(C), source(S), points_to(C,S).
right_tool(T,S) :- tool(T), source(S), fixes(T,S).
valid(P,S,C,T) :- place(P), source(S), clue(C), tool(T),
                  affords(P,S), true_clue(C,S), right_tool(T,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, source_id))
    for source_id in SOURCES:
        lines.append(asp.fact("source", source_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for source_id in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, source_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for source_id in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tool_id, source_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a suspenseful tall tale with a wondrous cat and shiny fox.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--cat")
    ap.add_argument("--fox")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and (args.clue or args.tool):
        source = SOURCES[args.source]
        clue = CLUES[args.clue] if args.clue else None
        tool = TOOLS[args.tool] if args.tool else None
        if (clue and not clue_points(clue, source)) or (tool and not tool_fixes(tool, source)):
            raise StoryError(explain_rejection(source, clue, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.clue is None or combo[2] == args.clue)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, source, clue, tool = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    cat = args.cat or rng.choice(CAT_NAMES)
    fox = args.fox or rng.choice(FOX_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place, source, clue, tool, name, gender, cat, fox, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SOURCES[params.source], CLUES[params.clue],
                 TOOLS[params.tool], params.name, params.gender,
                 params.cat, params.fox, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, clue, tool) combos:\n")
        for place, source, clue, tool in combos:
            print(f"  {place:14} {source:12} {clue:16} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.source} solved with {p.tool} ({p.place})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
