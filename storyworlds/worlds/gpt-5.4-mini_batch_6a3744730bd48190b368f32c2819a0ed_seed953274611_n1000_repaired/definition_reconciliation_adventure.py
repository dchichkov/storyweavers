#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/definition_reconciliation_adventure.py
======================================================================

A small adventure storyworld about a child who learns the meaning of a word
called a definition, gets lost on a trail of clues, and then reconciles with a
friend after a disagreement. The world is built as a tiny causal simulation:
typed entities have physical meters and emotional memes, events change state,
and the prose is rendered from that state rather than from a frozen template.

Seed premise
------------
Two children go on a small adventure to find a lost page that holds an important
definition. They argue about the right way to follow the map, then one child
realizes the other was trying to help. They make up, combine their clues, and
find the page together.

This file follows the Storyweavers world contract:
- stdlib only, aside from the shared results/asp helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- a Python reasonableness gate plus inline ASP twin
- three QA sets grounded in the simulated world
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIDGE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Place:
    id: str
    label: str
    scene: str
    afford: set[str] = field(default_factory=set)
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
class ClueTool:
    id: str
    label: str
    phrase: str
    help_text: str
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
class DefinitionPage:
    id: str
    label: str
    phrase: str
    meaning: str
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
        self.place: Place | None = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.place = copy.deepcopy(self.place)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.path = list(self.path)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child_a")
    b = world.get("child_b")
    if a.memes["upset"] < THRESHOLD or b.memes["upset"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["stubborn"] += 1
    b.memes["stubborn"] += 1
    out.append("__conflict__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child_a")
    b = world.get("child_b")
    if a.memes["apology"] < THRESHOLD or b.memes["forgive"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["peace"] += 1
    b.memes["peace"] += 1
    a.memes["upset"] = 0.0
    b.memes["upset"] = 0.0
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def can_reconcile(a: Entity, b: Entity, bridge: ClueTool) -> bool:
    return a.memes["curious"] >= BRIDGE_MIN and b.memes["curious"] >= BRIDGE_MIN and "bridge" in bridge.tags


def use_map(world: World, seeker: Entity, place: Place, tool: ClueTool) -> None:
    seeker.meters["progress"] += 1
    world.path.append(tool.id)
    world.say(
        f"{seeker.id} studied {tool.phrase} and stepped farther along the trail."
    )


def argue(world: World, a: Entity, b: Entity) -> None:
    a.memes["upset"] += 1
    b.memes["upset"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} and {b.id} stopped beside the old sign and argued about which clue to follow first."
    )


def separate(world: World, place: Place) -> None:
    world.get("child_a").meters["lost"] += 1
    world.get("child_b").meters["lost"] += 1
    world.say(
        f"The path forked near {place.label}, and for a moment the trail felt too big for both of them."
    )


def apologize(world: World, speaker: Entity, listener: Entity) -> None:
    speaker.memes["apology"] += 1
    listener.memes["forgive"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{speaker.id} took a breath and said sorry for snapping at {listener.id}."
    )


def bridge_clue(world: World, a: Entity, b: Entity, tool: ClueTool, page: DefinitionPage) -> None:
    a.memes["curious"] += 1
    b.memes["curious"] += 1
    world.say(
        f"They compared notes, and {tool.label} pointed them toward {page.label}."
    )


def find_page(world: World, page: DefinitionPage, seeker_a: Entity, seeker_b: Entity) -> None:
    page_ent = world.get("page")
    page_ent.meters["found"] = 1.0
    seeker_a.meters["progress"] += 1
    seeker_b.meters["progress"] += 1
    world.say(
        f"At last they found {page.phrase} tucked under a stone, and the word {page.label} finally made sense."
    )


def celebrate(world: World, a: Entity, b: Entity, page: DefinitionPage) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"They grinned, because now the definition was not just a word on a page but a clue they had solved together."
    )
    world.say(
        f"Side by side, they headed home with {page.label} safely in hand and the adventure feeling brighter than before."
    )


def tell(place: Place, bridge: ClueTool, map_a: ClueTool, map_b: ClueTool, page: DefinitionPage) -> World:
    world = World()
    world.place = place
    a = world.add(Entity(id="Maya", kind="character", type="girl", role="explorer", tags={"child"}))
    b = world.add(Entity(id="Noah", kind="character", type="boy", role="explorer", tags={"child"}))
    guide = world.add(Entity(id="Guide", kind="character", type="adult", role="guide", tags={"adult"}))
    page_ent = world.add(Entity(id="page", type="thing", label=page.label, tags=set(page.tags)))

    a.memes["curious"] = 3.0
    b.memes["curious"] = 3.0
    guide.memes["calm"] = 2.0

    world.say(
        f"On a bright afternoon, Maya and Noah set out on an adventure through {place.label}."
    )
    world.say(
        f"They were chasing a lost page that held the definition of a word they wanted to understand."
    )
    world.say(place.scene)
    world.para()

    use_map(world, a, place, map_a)
    use_map(world, b, place, map_b)
    separate(world, place)
    argue(world, a, b)

    world.para()
    if can_reconcile(a, b, bridge):
        bridge_clue(world, a, b, bridge, page)
        apologize(world, a, b)
        celebrate(world, a, b, page)
        find_page(world, page, a, b)
    else:
        world.say(
            f"They kept walking in circles and never quite agreed on the next step."
        )

    world.facts.update(
        a=a,
        b=b,
        guide=guide,
        place=place,
        bridge=bridge,
        map_a=map_a,
        map_b=map_b,
        page=page,
        found=page_ent.meters["found"] >= THRESHOLD,
        reconciled=a.memes["peace"] >= THRESHOLD and b.memes["peace"] >= THRESHOLD,
    )
    return world


PLACES = {
    "old_forest": Place(
        id="old_forest",
        label="the old forest",
        scene="Tall roots curled over the path like sleepy snakes, and sunbeams flashed between the trees.",
        afford={"trail"},
        tags={"forest", "adventure"},
    ),
    "river_walk": Place(
        id="river_walk",
        label="the river walk",
        scene="The water glittered beside the path, and little stones marked the way like bright dots.",
        afford={"trail"},
        tags={"river", "adventure"},
    ),
    "hill_path": Place(
        id="hill_path",
        label="the hill path",
        scene="The hill path climbed toward the clouds, and every bend promised a new view.",
        afford={"trail"},
        tags={"hill", "adventure"},
    ),
}

TOOLS = {
    "blue_map": ClueTool(id="blue_map", label="a blue map", phrase="a blue map with a torn corner", help_text="showed the safer trail", tags={"map", "bridge"}),
    "field_notes": ClueTool(id="field_notes", label="field notes", phrase="a page of field notes", help_text="held the missing clue", tags={"notes", "bridge"}),
    "star_token": ClueTool(id="star_token", label="a star token", phrase="a shiny star token", help_text="reminded them of the right path", tags={"token", "bridge"}),
}

PAGE = DefinitionPage(
    id="definition_page",
    label="definition",
    phrase="the definition page",
    meaning="an explanation of what a word means",
    tags={"definition", "meaning"},
)

@dataclass
class StoryParams:
    place: str
    bridge: str
    map_a: str
    map_b: str
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


CURATED = [
    StoryParams(place="old_forest", bridge="blue_map", map_a="field_notes", map_b="star_token", seed=1),
    StoryParams(place="river_walk", bridge="field_notes", map_a="blue_map", map_b="star_token", seed=2),
    StoryParams(place="hill_path", bridge="star_token", map_a="blue_map", map_b="field_notes", seed=3),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for bridge in TOOLS:
            for map_a in TOOLS:
                for map_b in TOOLS:
                    if bridge == map_a or bridge == map_b:
                        continue
                    combos.append((place, bridge, map_a, map_b))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the word "{PAGE.label}" and ends in reconciliation.',
        f"Tell a story where {f['a'].id} and {f['b'].id} get separated on an adventure, then make up and find the definition page together.",
        f'Write a child-friendly adventure with a disagreement, a reconciliation, and the word "{PAGE.label}" shown as important.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["a"], f["b"]
    qa = [
        ("What were the children looking for?",
         f"They were looking for {PAGE.phrase}, because it held the meaning of the word {PAGE.label}."),
        ("Why did they argue?",
         f"They argued because each child thought a different clue should lead the way first. The trail forked, and that made the choice feel important."),
        ("How did they make up?",
         f"{a.id} said sorry, and {b.id} was willing to forgive. Once they talked calmly, they could share the clues instead of fighting over them."),
    ]
    if f["reconciled"]:
        qa.append((
            "How did the story end?",
            f"It ended with them reconciled, side by side, and holding the definition page after solving the clue together. The ending shows that the argument changed into teamwork."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a definition?",
         "A definition is a short explanation of what a word means. It helps you understand a word better."),
        ("What does it mean to reconcile?",
         "To reconcile means to make up after a disagreement. People reconcile when they stop arguing and become friends again."),
        ("What is an adventure?",
         "An adventure is an exciting trip or experience with surprises and challenges along the way."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  path: {world.path}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict :- upset(a), upset(b).
reconcile :- apology(a), forgive(b).
valid(Place, Bridge, A, B) :- place(Place), tool(Bridge), tool(A), tool(B), Bridge != A, Bridge != B.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    lines.append(asp.fact("definition", PAGE.id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, bridge=None, map_a=None, map_b=None, seed=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with definition and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bridge", choices=TOOLS)
    ap.add_argument("--map-a", dest="map_a", choices=TOOLS)
    ap.add_argument("--map-b", dest="map_b", choices=TOOLS)
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
              and (args.bridge is None or c[1] == args.bridge)
              and (args.map_a is None or c[2] == args.map_a)
              and (args.map_b is None or c[3] == args.map_b)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, bridge, map_a, map_b = rng.choice(sorted(combos))
    return StoryParams(place=place, bridge=bridge, map_a=map_a, map_b=map_b)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.bridge not in TOOLS or params.map_a not in TOOLS or params.map_b not in TOOLS:
        raise StoryError("Unknown tool choice.")
    if len({params.bridge, params.map_a, params.map_b}) < 3:
        raise StoryError("The bridge clue must be different from both maps.")
    world = tell(PLACES[params.place], TOOLS[params.bridge], TOOLS[params.map_a], TOOLS[params.map_b], PAGE)
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
