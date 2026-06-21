#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/official_paper_surface_conflict_tall_tale.py
=============================================================================

A small tall-tale storyworld about an official, a paper, and a slippery surface
that turns into a conflict and then a clever resolution.

Seed words:
- official
- paper
- surface

Style:
- Tall Tale
- child-facing, concrete, state-driven, complete story with a clear turn

Domain sketch:
- A town official wants a paper sign posted on a slick surface.
- A proud helper argues with the official over where it should go.
- The paper may flutter, slide, or get splashed depending on the surface.
- A sensible fix uses a tack board, a dry board, or a porch post to settle the
  conflict and make the notice visible.

This script follows the shared Storyweavers contract:
- StoryParams dataclass with keyword construction
- build_parser, resolve_params, generate, emit, main
- QAItem/StoryError/StorySample from storyworlds/results.py
- lazy storyworlds/asp.py import in ASP helpers
- Python reasonableness gate + inline ASP_RULES twin
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

OFFICIALS = {
    "sheriff": {"label": "the sheriff", "title": "Sheriff"},
    "mayor": {"label": "the mayor", "title": "Mayor"},
    "postmaster": {"label": "the postmaster", "title": "Postmaster"},
}

HELPERS = {
    "clerk": {"label": "the clerk", "title": "Clerk"},
    "messenger": {"label": "the messenger", "title": "Messenger"},
    "dockhand": {"label": "the dockhand", "title": "Dockhand"},
}

PAPERS = {
    "notice": {
        "label": "notice paper",
        "phrase": "a notice on thick paper",
        "purpose": "post the town notice",
        "toss": "fluttered like a tiny sail",
    },
    "map": {
        "label": "map paper",
        "phrase": "a folded map on stiff paper",
        "purpose": "pin the route map",
        "toss": "curled at the corners",
    },
    "letter": {
        "label": "letter paper",
        "phrase": "a letter written on clean paper",
        "purpose": "deliver the message",
        "toss": "whipped in the wind",
    },
}

SURFACES = {
    "wet_board": {
        "label": "the wet board",
        "surface_word": "surface",
        "reason": "the rain had made the board slick",
        "slip": "slid right off",
        "type": "board",
        "stable": False,
    },
    "stone_wall": {
        "label": "the stone wall",
        "surface_word": "surface",
        "reason": "the stones were cold and rough",
        "slip": "curled at the edges",
        "type": "wall",
        "stable": False,
    },
    "dry_post": {
        "label": "the dry porch post",
        "surface_word": "surface",
        "reason": "it was dry and easy to pin to",
        "slip": "stayed put",
        "type": "post",
        "stable": True,
    },
    "cork_board": {
        "label": "the cork board",
        "surface_word": "surface",
        "reason": "it was made for tacking up papers",
        "slip": "stayed true as a North Star",
        "type": "board",
        "stable": True,
    },
}

ACTIONS = {
    "tape": {
        "label": "tape",
        "sense": 2,
        "power": 2,
        "success": "taped it up, but only after smoothing the corners dry",
        "fail": "taped it up, but the tape let go and the paper slid away",
        "qa": "taped the paper in place",
    },
    "tacks": {
        "label": "tacks",
        "sense": 3,
        "power": 4,
        "success": "pressed in a row of tacks until the paper held fast",
        "fail": "tried the tacks, but the surface was too slippery and they popped loose",
        "qa": "tacked the paper in place",
    },
    "string": {
        "label": "string",
        "sense": 3,
        "power": 3,
        "success": "tied the paper with string so it hung steady like a banner",
        "fail": "tied the string, but the paper spun and flew free in the breeze",
        "qa": "tied the paper in place",
    },
    "paste": {
        "label": "paste",
        "sense": 1,
        "power": 1,
        "success": "smeared paste on it, but the damp surface made a mess of it",
        "fail": "smeared paste on it, but the paper peeled away before long",
        "qa": "pasted the paper in place",
    },
}

GEO_NAMES = ["June", "Mabel", "Ned", "Ira", "Belle", "Cora", "Hank", "Otis", "Wren", "Piper"]

ASP_RULES = r"""
good_surface(S) :- surface(S), stable(S).
reasonable_action(A) :- action(A), sense(A, N), min_sense(M), N >= M.
valid_choice(O, P, S) :- official(O), paper(P), surface(S), good_surface(S).
outcome(success) :- chosen_action(A), action_power(A, P), surface_strength(V), P >= V.
outcome(failure) :- chosen_action(A), action_power(A, P), surface_strength(V), P < V.
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c
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


@dataclass
class StoryParams:
    official: str
    paper: str
    surface: str
    helper: str
    action: str
    name: str = "Mabel"
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for o in OFFICIALS:
        for p in PAPERS:
            for s, cfg in SURFACES.items():
                if cfg["stable"]:
                    combos.append((o, p, s))
    return combos

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: an official, paper, and a surface.")
    ap.add_argument("--official", choices=OFFICIALS)
    ap.add_argument("--paper", choices=PAPERS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
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

def reasonableness_check(params: StoryParams) -> None:
    if params.surface not in SURFACES:
        raise StoryError("Unknown surface.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if not SURFACES[params.surface]["stable"]:
        raise StoryError(f"(No story: {SURFACES[params.surface]['label']} is too slippery for a tidy notice story.)")
    if ACTIONS[params.action]["sense"] < 2:
        raise StoryError(f"(Refusing action '{params.action}': it is too flimsy for this tall-tale world.)")

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and ACTIONS[args.action]["sense"] < 2:
        raise StoryError(f"(Refusing action '{args.action}': it is too flimsy for this tall-tale world.)")
    combos = [c for c in valid_combos()
              if (args.official is None or c[0] == args.official)
              and (args.paper is None or c[1] == args.paper)
              and (args.surface is None or c[2] == args.surface)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    official, paper, surface = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    action = args.action or rng.choice(sorted(k for k, v in ACTIONS.items() if v["sense"] >= 2))
    name = args.name or rng.choice(GEO_NAMES)
    return StoryParams(official=official, paper=paper, surface=surface, helper=helper, action=action, name=name)

def _predict(world: World, params: StoryParams) -> bool:
    return SURFACES[params.surface]["stable"] and ACTIONS[params.action]["power"] >= 2

def tell(params: StoryParams) -> World:
    reasonableness_check(params)
    world = World()
    off = world.add(Entity(id="official", kind="character", type="man", label=OFFICIALS[params.official]["label"]))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=HELPERS[params.helper]["label"]))
    paper = world.add(Entity(id="paper", kind="thing", type="paper", label=PAPERS[params.paper]["label"], attrs={"phrase": PAPERS[params.paper]["phrase"]}))
    surface = world.add(Entity(id="surface", kind="thing", type="surface", label=SURFACES[params.surface]["label"], attrs=dict(SURFACES[params.surface])))
    off.memes["duty"] = 1
    helper.memes["pride"] = 1
    world.say(f"In a windy little town, {OFFICIALS[params.official]['label']} carried {PAPERS[params.paper]['phrase']} and marched toward {SURFACES[params.surface]['label']}.")
    world.say(f"{helper.label_word if False else params.name} had a heap of opinions and a heart full of thunder. \"That {SURFACES[params.surface]['label']} will not hold paper!\" {params.name} cried.")
    world.say(f"{OFFICIALS[params.official]['label'].capitalize()} frowned. \"I need the notice where every soul can see it,\" {off.pronoun()} said.")
    world.para()
    helper.memes["conflict"] = 1
    off.memes["conflict"] = 1
    world.say(f"Their words bounced back and forth like two crows over a cornfield. The paper {PAPERS[params.paper]['toss']} in the wind, and the whole matter grew as lopsided as a mule on a hill.")
    if _predict(world, params):
        world.say(f"At last, {params.name} spied a dry fix that made more sense than a rooster wearing boots.")
        world.say(f"Together they chose {ACTIONS[params.action]['label']}, and the paper stayed as true as sunrise.")
        world.say(f"{OFFICIALS[params.official]['label'].capitalize()} {ACTIONS[params.action]['success']}.")
        world.say(f"By evening, the notice was plain as day, and even the crickets could have read it.")
    else:
        world.say(f"But the plan was too weak, and the paper {SURFACES[params.surface]['slip']}.")
        world.say(f"The official had to fetch a better board and try again by lamplight.")
    world.facts.update(
        official=off,
        helper=helper,
        paper=paper,
        surface=surface,
        params=params,
        outcome="success" if SURFACES[params.surface]["stable"] else "failure",
    )
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall-tale story including the words official, paper, and surface, where {f['official'].label} and a helper argue about posting a notice.",
        f"Tell a child-friendly story about an official, a paper sign, and a tricky surface, with a conflict that ends in a clever fix.",
        f"Write a funny frontier-style story where a paper notice will not stay on a surface until the characters choose a better way.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="Who was trying to post the paper?", answer=f"{f['official'].label.capitalize()} was trying to post the paper, because the town needed the notice where everybody could see it."),
        QAItem(question="Why was there a conflict?", answer=f"The conflict started because the helper thought {f['surface'].label} was a bad place for paper, and the official wanted the sign there anyway. They both wanted the notice to work, but they disagreed about how to do it safely."),
        QAItem(question="How did the story end?", answer=f"It ended with a better choice: they used a steadier way to hold the paper, so the notice stayed up and the town could read it."),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an official?", answer="An official is a person who works for a town or group and helps make sure things are done the right way."),
        QAItem(question="What is paper?", answer="Paper is a thin material people write on, draw on, and hang up for notices or letters."),
        QAItem(question="What is a surface?", answer="A surface is the outside top part of something, like a board, a wall, or a table."),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)

def asp_facts() -> str:
    import asp
    lines = []
    for k in OFFICIALS:
        lines.append(asp.fact("official", k))
    for k in PAPERS:
        lines.append(asp.fact("paper", k))
    for k, v in SURFACES.items():
        lines.append(asp.fact("surface", k))
        if v["stable"]:
            lines.append(asp.fact("stable", k))
    for k, v in ACTIONS.items():
        lines.append(asp.fact("action", k))
        lines.append(asp.fact("sense", k, v["sense"]))
        lines.append(asp.fact("action_power", k, v["power"]))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_choice/3."))
    return sorted(set(asp.atoms(model, "valid_choice")))

def asp_reasonable_actions() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable_action/1."))
    return sorted(a for (a,) in asp.atoms(model, "reasonable_action"))

def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid choices differ from Python valid_combos().")
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos).")
    if set(asp_reasonable_actions()) != {k for k, v in ACTIONS.items() if v["sense"] >= 2}:
        rc = 1
        print("MISMATCH: ASP reasonable actions differ from Python gate.")
    else:
        print("OK: ASP matches Python action reasonableness.")
    try:
        sample = generate(StoryParams(official="sheriff", paper="notice", surface="cork_board", helper="clerk", action="tacks", name="June"))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc

def generate(params: StoryParams) -> StorySample:
    if params.official not in OFFICIALS or params.paper not in PAPERS or params.surface not in SURFACES or params.helper not in HELPERS or params.action not in ACTIONS:
        raise StoryError("Invalid story parameters.")
    if not SURFACES[params.surface]["stable"]:
        raise StoryError("The chosen surface is too unstable for this story.")
    if ACTIONS[params.action]["sense"] < 2:
        raise StoryError("The chosen action is too flimsy for this story.")
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

CURATED = [
    StoryParams(official="sheriff", paper="notice", surface="cork_board", helper="clerk", action="tacks", name="June"),
    StoryParams(official="mayor", paper="map", surface="dry_post", helper="messenger", action="string", name="Mabel"),
    StoryParams(official="postmaster", paper="letter", surface="dry_post", helper="dockhand", action="tape", name="Ned"),
]

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.official is None or c[0] == args.official)
              and (args.paper is None or c[1] == args.paper)
              and (args.surface is None or c[2] == args.surface)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    official, paper, surface = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    action = args.action or rng.choice(sorted(k for k, v in ACTIONS.items() if v["sense"] >= 2))
    name = args.name or rng.choice(GEO_NAMES)
    return StoryParams(official=official, paper=paper, surface=surface, helper=helper, action=action, name=name)

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_choice/3.\n#show reasonable_action/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations:")
        for x in asp_valid_combos():
            print(" ", x)
        return
    rng0 = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = (args.seed if args.seed is not None else random.randrange(2**31)) + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
