#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crawl_dim_surprise_flashback_space_adventure.py
===============================================================================

A standalone storyworld about a tiny space-adventure crawl through a dim ship,
where a child explorer expects one thing and gets a surprise, then a flashback
explains why the odd sound or object matters. The world is small, concrete, and
state-driven: meters track physical conditions like light, charge, and distance;
memes track emotions like wonder, worry, and relief.

The seed words and style guide this world:
- Words: crawl-dim
- Features: Surprise, Flashback
- Style: Space Adventure
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
LIGHT_MIN = 1.0
SURPRISE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"light": 0.0, "charge": 0.0, "distance": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "wonder": 0.0, "relief": 0.0, "surprise": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Location:
    id: str
    label: str
    dimness: float
    crawl: bool = False
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
class ShipPiece:
    id: str
    label: str
    place: str
    surprise_kind: str
    flash_kind: str
    hidden: bool = False
    revealed: bool = False
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
    glow: str
    helps_flashback: bool = False
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    location: Optional[Location] = None
    piece: Optional[ShipPiece] = None
    tool: Optional[Tool] = None
    timeline: list[str] = field(default_factory=list)

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
        clone.location = copy.deepcopy(self.location)
        clone.piece = copy.deepcopy(self.piece)
        clone.tool = copy.deepcopy(self.tool)
        clone.timeline = list(self.timeline)
        return clone

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
@dataclass
class StoryParams:
    location: str
    piece: str
    tool: str
    hero: str
    hero_gender: str
    captain: str
    captain_gender: str
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


LOCATIONS = {
    "crawl_dim": Location("crawl_dim", "the crawl-dim corridor", dimness=3.0, crawl=True, tags={"crawl-dim"}),
    "airlock": Location("airlock", "the airlock hall", dimness=2.0, crawl=True, tags={"space", "hall"}),
    "storage": Location("storage", "the storage tunnel", dimness=2.5, crawl=True, tags={"tunnel"}),
}

SHIP_PIECES = {
    "star_map": ShipPiece("star_map", "a star map tile", "under a loose panel", "surprise", "flash", hidden=True, tags={"map", "surprise"}),
    "robot": ShipPiece("robot", "a tiny repair robot", "behind a vent grate", "surprise", "whirr", hidden=True, tags={"robot", "surprise"}),
    "seedpod": ShipPiece("seedpod", "a seedpod crate", "beside a blinking pipe", "surprise", "clink", hidden=True, tags={"crate", "surprise"}),
}

TOOLS = {
    "torch": Tool("torch", "a torch", "a torch", "glowed like a tiny moon", helps_flashback=False, tags={"light"}),
    "lamp": Tool("lamp", "a pocket lamp", "a pocket lamp", "shone soft and steady", helps_flashback=False, tags={"light"}),
    "memory_bead": Tool("memory_bead", "a memory bead", "a little memory bead", "warmed with old light", helps_flashback=True, tags={"flashback"}),
}

HERO_NAMES = ["Nova", "Rio", "Mika", "Juno", "Zed", "Luna", "Tari", "Pip"]
CAPTAIN_NAMES = ["Captain Sol", "Captain Vela", "Captain Mira", "Captain Orion"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc_id, loc in LOCATIONS.items():
        if not loc.crawl:
            continue
        for piece_id in SHIP_PIECES:
            for tool_id in TOOLS:
                combos.append((loc_id, piece_id, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure crawl storyworld with surprise and flashback.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--piece", choices=SHIP_PIECES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "they"])
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy", "they"])
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
              if (args.location is None or c[0] == args.location)
              and (args.piece is None or c[1] == args.piece)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, piece, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    captain_gender = args.captain_gender or "they"
    return StoryParams(loc, piece, tool, hero, hero_gender, captain, captain_gender)


def _setup_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(params.hero, kind="character", type=params.hero_gender, role="hero"))
    cap = world.add(Entity(params.captain, kind="character", type=params.captain_gender, role="captain"))
    loc = LOCATIONS[params.location]
    piece = SHIP_PIECES[params.piece]
    tool = TOOLS[params.tool]
    world.location = copy.deepcopy(loc)
    world.piece = copy.deepcopy(piece)
    world.tool = copy.deepcopy(tool)
    world.add(Entity("corridor", type="place", label=loc.label))
    world.add(Entity("panel", type="thing", label="the loose panel"))
    world.add(Entity("hideaway", type="thing", label=piece.place))
    hero.meters["distance"] = 1.0
    cap.meters["distance"] = 2.0
    hero.memes["wonder"] = 1.0
    cap.memes["worry"] = 1.0
    world.facts.update(hero=hero, captain=cap, location=loc, piece=piece, tool=tool)
    return world


def predict_discovery(world: World) -> dict:
    sim = world.copy()
    hero = sim.get(sim.facts["hero"].id)
    piece = sim.piece
    hero.meters["distance"] += 1.0
    piece.revealed = True
    hero.memes["surprise"] += 1.0
    return {"revealed": True, "surprise": hero.memes["surprise"] >= SURPRISE_MIN}


def _move_crawl(world: World, hero: Entity) -> None:
    hero.meters["distance"] += 1.0
    hero.meters["dust"] += 1.0
    hero.memes["wonder"] += 1.0
    world.say(f"{hero.id} had to crawl-dim through the narrow corridor, where the walls felt close and cool.")


def _flashback(world: World, hero: Entity, piece: ShipPiece, tool: Tool) -> None:
    hero.memes["surprise"] += 1.0
    world.say(f"Then {hero.id} found {piece.label} in {piece.place}, and the surprise made {hero.pronoun('possessive')} eyes go wide.")
    if tool.helps_flashback:
        world.say(f"{tool.phrase} glimmered in {hero.pronoun('possessive')} hand, and that soft glow brought back a flashback.")
        world.say(f"{hero.id} remembered the day {world.facts['captain'].id} had hidden the clue there to keep it safe for later.")
    else:
        world.say(f"{tool.phrase} lit the dark so {hero.id} could remember why the clue had been left there before.")
    world.timeline.append("flashback")
    hero.memes["worry"] += 0.5


def _reveal_and_return(world: World, hero: Entity, cap: Entity, piece: ShipPiece) -> None:
    piece.revealed = True
    hero.memes["relief"] += 1.0
    cap.memes["relief"] += 1.0
    world.say(f"{cap.id} smiled when {hero.id} called out, and together they carried {piece.label} back to the bridge.")
    world.say(f"The little ship seemed brighter as soon as the secret was shared.")
    world.timeline.append("return")


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.facts["hero"]
    cap = world.facts["captain"]
    piece = world.piece
    tool = world.tool

    world.say(f"{hero.id} and {cap.id} explored {world.location.label} on a quiet starship night.")
    world.say(f"The place was dim, and the only sound was the soft hum of the ship.")

    world.para()
    _move_crawl(world, hero)
    world.say(f"{hero.id} was looking for the next hatch when {hero.pronoun()} noticed something hidden.")

    pred = predict_discovery(world)
    world.facts["predicted_surprise"] = pred["surprise"]

    world.para()
    _flashback(world, hero, piece, tool)

    world.para()
    _reveal_and_return(world, hero, cap, piece)
    world.say(f"By the end, the crawl-dim corridor no longer felt spooky; it felt like the start of a safe new mission.")

    world.facts["outcome"] = "reveal"
    world.facts["timeline"] = list(world.timeline)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the word "crawl-dim" and a surprise hidden in a ship corridor.',
        f"Tell a story where {f['hero'].id} crawls through a dim spaceship passage, finds a surprise, and then has a flashback about why it was hidden.",
        "Write a gentle space adventure with a surprise, a flashback, and a bright ending image of the ship feeling safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    cap = f["captain"]
    piece = f["piece"]
    tool = f["tool"]
    answers = [
        QAItem(
            question="Who was exploring the spaceship?",
            answer=f"{hero.id} and {cap.id} were exploring together. {hero.id} was the one crawling through the dim corridor and finding the surprise."
        ),
        QAItem(
            question="What surprise did the child find?",
            answer=f"{hero.id} found {piece.label} hidden {piece.place}. It was a small but exciting surprise because nobody expected it to be there."
        ),
        QAItem(
            question="Why did the story have a flashback?",
            answer=f"The flashback explained why the clue had been hidden in the first place. {tool.phrase} helped {hero.id} remember that {cap.id} had left it safely for later."
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does crawl-dim mean in this story?",
            answer="It means the corridor is so low and dark that a child has to crawl carefully. In a spaceship story, that makes the place feel secret and a little spooky."
        ),
        QAItem(
            question="Why is a flashlight useful in the dark?",
            answer="A flashlight gives steady light without making the whole place dangerous. It helps children see hidden things and move carefully."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something that happened earlier. It helps explain why a surprising thing makes sense now."
        ),
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  timeline: {world.timeline}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(L,P,T) :- location(L), piece(P), tool(T).
surprise_seen(H,P) :- hero(H), piece(P), hidden(P).
flashback_needed(T) :- tool(T), helps_flashback(T).
outcome(reveal) :- valid(L,P,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid in LOCATIONS:
        lines.append(asp.fact("location", lid))
    for pid in SHIP_PIECES:
        lines.append(asp.fact("piece", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if TOOLS[tid].helps_flashback:
            lines.append(asp.fact("helps_flashback", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(location=None, piece=None, tool=None, hero=None, hero_gender=None, captain=None, captain_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams("crawl_dim", "star_map", "memory_bead", "Nova", "girl", "Captain Sol", "they"),
    StoryParams("airlock", "robot", "torch", "Rio", "boy", "Captain Vela", "they"),
    StoryParams("storage", "seedpod", "lamp", "Mika", "girl", "Captain Mira", "they"),
]


def resolve_rejection(args: argparse.Namespace) -> None:
    if args.location and args.location not in LOCATIONS:
        raise StoryError("Unknown location.")
    if args.piece and args.piece not in SHIP_PIECES:
        raise StoryError("Unknown piece.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show surprise_seen/2.\n#show flashback_needed/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
