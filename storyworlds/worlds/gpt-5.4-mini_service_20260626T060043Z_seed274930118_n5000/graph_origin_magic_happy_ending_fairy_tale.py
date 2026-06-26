#!/usr/bin/env python3
"""
storyworlds/worlds/graph_origin_magic_happy_ending_fairy_tale.py
===============================================================

A small fairy-tale storyworld about a magical graph, an origin, and a happy
ending.

Premise:
- A child and a helper find a glowing graph-map in a fairy glen.
- The graph has an origin node, but its path is hard to read.
- Magic can reveal the true starting place and guide them home.

The simulated state tracks:
- physical meters: glow, dust, tangles, distance, neatness
- emotional memes: wonder, worry, hope, relief, delight

The story is authored from the world state, not from a frozen template:
- setup: the treasure, the wish, the warning
- turn: confusion, a magical clue, following edges
- resolution: the origin is found, the lost thing is restored, and the ending is happy
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


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

HERO_NAMES = ["Mina", "Lila", "Toby", "Nora", "Pip", "Elsie", "Rowan", "Ari"]
HELPER_NAMES = ["the fairy", "the owl", "the lantern-sprite", "the little wizard"]
TRAITS = ["curious", "gentle", "brave", "bright", "patient", "cheerful"]

LOCATIONS = {
    "glade": "a moonlit glade",
    "garden": "an old rose garden",
    "brook": "a silver brook",
    "tower": "a mossy tower room",
}

MAGICS = {
    "spark": "a spark of magic",
    "glimmer": "a glimmering spell",
    "song": "a soft song of magic",
}

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    parent: Optional[str] = None
    linked_to: Optional[str] = None
    origin: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["glow", "dust", "tangle", "distance", "neatness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["wonder", "worry", "hope", "relief", "delight", "trust"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "fairy"}
        male = {"boy", "prince", "king", "father", "wizard", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    key: str
    name: str
    affords_magic: bool = True
    has_graph: bool = True


@dataclass
class GraphSpec:
    key: str
    label: str
    phrase: str
    nodes: list[str]
    edges: list[tuple[str, str]]
    origin: str
    mystery: str
    treasure: str


@dataclass
class SpellSpec:
    key: str
    label: str
    phrase: str
    reveal: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "glade": Setting("glade", LOCATIONS["glade"]),
    "garden": Setting("garden", LOCATIONS["garden"]),
    "brook": Setting("brook", LOCATIONS["brook"]),
    "tower": Setting("tower", LOCATIONS["tower"]),
}

GRAPHS = {
    "lantern": GraphSpec(
        key="lantern",
        label="lantern graph",
        phrase="a glowing lantern graph with silver lines",
        nodes=["start", "bridge", "heart", "origin"],
        edges=[("start", "bridge"), ("bridge", "heart"), ("heart", "origin")],
        origin="origin",
        mystery="a lost path back to the cottage",
        treasure="the way home",
    ),
    "rose": GraphSpec(
        key="rose",
        label="rose graph",
        phrase="a rose-colored graph with curled petals for nodes",
        nodes=["bud", "bloom", "path", "origin"],
        edges=[("bud", "bloom"), ("bloom", "path"), ("path", "origin")],
        origin="origin",
        mystery="where the moonlit roses first began",
        treasure="the first rose",
    ),
    "brook": GraphSpec(
        key="brook",
        label="brook graph",
        phrase="a water-sparkled graph with bubbles at each corner",
        nodes=["spring", "bend", "pool", "origin"],
        edges=[("spring", "bend"), ("bend", "pool"), ("pool", "origin")],
        origin="origin",
        mystery="where the silver brook began",
        treasure="the spring of the brook",
    ),
}

SPELLS = {
    "spark": SpellSpec("spark", "spark spell", "a tiny spark spell", "the hidden origin", "shine on the path"),
    "glimmer": SpellSpec("glimmer", "glimmer spell", "a soft glimmer spell", "the first node", "show the line"),
    "song": SpellSpec("song", "song spell", "a humming song spell", "the true start", "wake the graph"),
}

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    graph: str
    spell: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def graph_has_origin(graph: GraphSpec) -> bool:
    return graph.origin in graph.nodes


def spell_reveals_origin(graph: GraphSpec, spell: SpellSpec) -> bool:
    return graph_has_origin(graph) and bool(spell.reveal)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GRAPHS:
            for sp in SPELLS:
                graph = GRAPHS[g]
                spell = SPELLS[sp]
                if graph_has_origin(graph) and spell_reveals_origin(graph, spell):
                    combos.append((s, g, sp))
    return combos


def explain_rejection(graph: GraphSpec, spell: SpellSpec) -> str:
    return (
        f"(No story: the {graph.label} must have an origin node that the spell can reveal. "
        f"This pairing would not make a clear fairy-tale turn.)"
    )


# ---------------------------------------------------------------------------
# The live world
# ---------------------------------------------------------------------------
def _gain(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _feel(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    graph = GRAPHS[params.graph]
    spell = SPELLS[params.spell]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Lila", "Nora", "Elsie"} else "boy"))
    helper_type = "fairy" if "fairy" in params.helper else "owl" if "owl" in params.helper else "wizard" if "wizard" in params.helper else "sprite"
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=params.helper))
    graph_ent = world.add(Entity(id="graph", type="graph", label=graph.label, phrase=graph.phrase, origin=True))
    origin = world.add(Entity(id="origin", type="node", label="the origin", phrase="the true starting point", linked_to="graph"))
    for node in graph.nodes:
        world.add(Entity(id=f"node_{node}", type="node", label=node, phrase=node, linked_to="graph"))
    world.facts.update(hero=hero, helper=helper, graph=graph_ent, origin=origin, graph_spec=graph, spell_spec=spell)
    return world


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def intro(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    graph = world.facts["graph_spec"]
    _feel(hero, "wonder", 1)
    _feel(helper, "trust", 1)
    world.say(
        f"Once upon a time, {hero.id} was a {random.choice(TRAITS)} little wanderer who liked to listen for secrets in quiet places."
    )
    world.say(
        f"In {world.setting.name}, {hero.id} found {graph.phrase}, and the helper called it {graph.mystery}."
    )


def trouble(world: World) -> None:
    hero = world.facts["hero"]
    graph = world.facts["graph_spec"]
    spell = world.facts["spell_spec"]
    _feel(hero, "worry", 1)
    _gain(world.facts["graph"], "dust", 1)
    world.say(
        f"But the lines were tangled with old dust, and {hero.id} could not tell where the graph began."
    )
    world.say(
        f"{hero.id} wished to know {graph.treasure}, so the helper lifted {spell.phrase} and promised it could {spell.helps}."
    )


def magic_turn(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    graph = world.facts["graph_spec"]
    spell = world.facts["spell_spec"]
    graph_ent = world.facts["graph"]
    origin = world.facts["origin"]

    _gain(graph_ent, "glow", 1)
    _gain(origin, "glow", 1)
    _feel(hero, "hope", 1)
    world.say(
        f"The spell began as a whisper, and a bright thread of light ran along the graph's edges."
    )
    world.say(
        f"One by one, the signs woke up, until the light rested on {origin.label}, the real origin node."
    )


def resolve(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    graph = world.facts["graph_spec"]
    spell = world.facts["spell_spec"]
    origin = world.facts["origin"]

    _feel(hero, "relief", 1)
    _feel(hero, "delight", 1)
    _feel(helper, "delight", 1)
    _gain(origin, "neatness", 1)
    world.say(
        f"{hero.id} smiled, because the puzzle was simple now: the path began at the origin and led home in a tidy line."
    )
    world.say(
        f"{helper.id} tucked away {spell.label}, and the little pair followed the shining route until the whole story felt safe and complete."
    )
    world.say(
        f"At the end, the graph still glowed softly, and the origin stayed bright like a lantern at the door."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    world.para()
    trouble(world)
    world.para()
    magic_turn(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    graph = world.facts["graph_spec"]
    spell = world.facts["spell_spec"]
    return [
        f"Write a fairy tale about {hero.id}, a magical graph, and the origin hidden inside it.",
        f"Tell a child-friendly story where {spell.phrase} helps reveal the start of {graph.label}.",
        f"Write a happy-ending tale set in {world.setting.name} with the words graph and origin.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    graph = world.facts["graph_spec"]
    spell = world.facts["spell_spec"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.name}?",
            answer=f"{hero.id} found {graph.phrase} in {world.setting.name}.",
        ),
        QAItem(
            question="What was hard to see at first?",
            answer="The origin was hard to see at first because the graph's lines were tangled with dust.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label.capitalize()} used {spell.phrase} to shine on the graph and reveal the origin.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the origin was clear, the path was tidy, and the ending was happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    graph = world.facts["graph_spec"]
    return [
        QAItem(
            question="What is a graph?",
            answer="A graph is a drawing of nodes connected by lines that can help show a path or a relationship.",
        ),
        QAItem(
            question="What is an origin?",
            answer="An origin is the starting place or beginning of something.",
        ),
        QAItem(
            question="What does magic do in fairy tales?",
            answer="Magic can reveal hidden things, help solve puzzles, or guide someone safely to a goal.",
        ),
        QAItem(
            question=f"Why would the origin matter for the {graph.label}?",
            answer="The origin matters because it shows where the path begins, which helps the characters understand the whole graph.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
origin_node(G,O) :- graph(G), has_origin(G,O).
valid_combo(S,G,Sp) :- setting(S), graph(G), spell(Sp), origin_node(G,O), reveals(Sp,O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, g in GRAPHS.items():
        lines.append(asp.fact("graph", gid))
        lines.append(asp.fact("has_origin", gid, g.origin))
    for spid in SPELLS:
        lines.append(asp.fact("spell", spid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parser / resolution / generation / emit / main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a magical graph and its origin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--graph", choices=GRAPHS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.graph is None or c[1] == args.graph)
        and (args.spell is None or c[2] == args.spell)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, graph, spell = rng.choice(sorted(filtered))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, graph=graph, spell=spell, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.origin:
            bits.append("origin=True")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="glade", graph="lantern", spell="spark", name="Mina", helper="the fairy", trait="curious"),
    StoryParams(setting="garden", graph="rose", spell="glimmer", name="Nora", helper="the owl", trait="gentle"),
    StoryParams(setting="brook", graph="brook", spell="song", name="Toby", helper="the little wizard", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print(" ", combo)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
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
            header = f"### {p.name}: {p.graph} in {p.setting} with {p.spell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
