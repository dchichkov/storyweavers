#!/usr/bin/env python3
"""
storyworlds/worlds/hobble_widow_foreshadowing_ghost_story.py
=============================================================

A small storyworld for a ghost-story seed with foreshadowing.

Domain sketch:
- A widow keeps a candlelit house and a hobbling old hallway.
- Strange clues foreshadow a helpful ghost.
- A frightened child or neighbor follows the clues, learns the truth, and
  ends with a changed room and a calmer heart.

The simulation uses typed entities with physical meters and emotional memes,
a tiny forward-chaining rule, and an inline ASP twin for parity checks.
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
    phrase: str = ""
    role: str = ""
    location: str = ""
    owner: Optional[str] = None
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "widow"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    widow_name: str
    child_name: str
    child_type: str
    place: str
    omen: str
    ghost_kind: str
    seed: Optional[int] = None


@dataclass
class PlaceCfg:
    id: str
    label: str
    darkness: str
    sounds: str
    tags: set[str] = field(default_factory=set)


@dataclass
class OmenCfg:
    id: str
    clue: str
    foreshadow: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostCfg:
    id: str
    label: str
    reveal: str
    help: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: PlaceCfg):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue")
    if clue is None:
        return out
    if clue.meters["seen"] < THRESHOLD:
        return out
    sig = ("unease", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["unease"] += 1
    out.append("__unease__")
    return out


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


CAUSAL_RULES = [Rule("unease", _r_unease)]


PLACES = {
    "hall": PlaceCfg("hall", "the old hall", "dark and long", "the floorboard ticked", {"hall", "dark"}),
    "attic": PlaceCfg("attic", "the attic", "dusty and narrow", "the rafters sighed", {"attic", "dark"}),
    "garden": PlaceCfg("garden", "the back garden", "foggy and cold", "the gate tapped", {"garden", "dark"}),
}

OMENS = {
    "footstep": OmenCfg("footstep", "a slow footstep", "the slow footstep foreshadowed someone nearby", "a hidden visitor", {"sound", "foreshadow"}),
    "candle": OmenCfg("candle", "a candle that flickered blue", "the blue flicker foreshadowed a ghostly hand", "a secret message", {"light", "foreshadow"}),
    "window": OmenCfg("window", "a window that rattled once", "the rattle foreshadowed the wind or a warning", "a warning in the dark", {"wind", "foreshadow"}),
}

GHOSTS = {
    "widow_ghost": GhostCfg("widow_ghost", "the widow's late husband", "a pale face in the mirror", "he had come back to help her remember the key", {"ghost", "widow"}),
    "lantern_ghost": GhostCfg("lantern_ghost", "the lantern ghost", "a small glow under the stairs", "it had been guiding them to a lost lantern", {"ghost", "light"}),
    "cat_ghost": GhostCfg("cat_ghost", "the house cat ghost", "a soft tail by the door", "it had been leading them away from danger", {"ghost", "cat"}),
}

WIDOW_NAMES = ["Mrs. Vale", "Mrs. Reed", "Mrs. Bell", "Mrs. Grey"]
CHILD_NAMES = ["Mina", "Ned", "Tess", "Pip"]
CHILD_TYPES = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for omen in OMENS:
            for ghost in GHOSTS:
                combos.append((place, omen, ghost))
    return combos


def explain_rejection() -> str:
    return "(No story: invalid haunted-house combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--widow")
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
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
              and (args.omen is None or c[1] == args.omen)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, omen, ghost = rng.choice(sorted(combos))
    widow = args.widow or rng.choice(WIDOW_NAMES)
    child = args.child or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    return StoryParams(
        widow_name=widow,
        child_name=child,
        child_type=child_type,
        place=place,
        omen=omen,
        ghost_kind=ghost,
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    omen = OMENS[params.omen]
    ghost = GHOSTS[params.ghost_kind]
    world = World(place)
    widow = world.add(Entity(id="widow", kind="character", type="widow", label=params.widow_name, role="widow"))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name, role="child"))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label=omen.clue, phrase=omen.clue, location=place.label, tags=set(omen.tags)))
    candle = world.add(Entity(id="candle", kind="thing", type="thing", label="a small candle", phrase="a small candle", location=place.label))
    key = world.add(Entity(id="key", kind="thing", type="thing", label="an old key", phrase="an old key", location=place.label))
    world.facts.update(widow=widow, child=child, clue=clue, candle=candle, key=key, omen=omen, ghost=ghost, place=place)
    child.memes["curiosity"] += 1
    widow.memes["worry"] += 1
    world.say(f"{params.widow_name} lived in {place.label}.")
    world.say(f"{params.child_name} came to visit, and {place.darkness} made the rooms feel too quiet.")
    world.say(f"Then {omen.foreshadow}.")
    world.para()
    child.meters["heard"] += 1
    clue.meters["seen"] += 1
    propagate(world)
    world.say(f"{params.child_name} looked at the clue and felt a small chill.")
    world.say(f"{omen.risk.capitalize()}, but {params.widow_name} only said, 'Stay close.'")
    world.para()
    ghost.meters["present"] += 1
    widow.memes["fear"] += 1
    child.memes["fear"] += 1
    world.say(f"At last, {ghost.reveal}.")
    world.say(f"It was not there to scare them. {ghost.help.capitalize()}.")
    widow.memes["relief"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(f"{params.child_name} found {key.label} where the clue had pointed, and {params.widow_name} laughed softly.")
    world.say(f"In the end, the old hall felt less haunted and more like a room that had been waiting to speak.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that uses the words "{f["place"].label}" and "{f["widow"].label}".',
        f"Tell a quiet haunted-house story where {f['child'].label} notices {f['clue'].label} before the ghost appears.",
        f"Write a foreshadowing story in a dark house where a widow and a child discover a helpful ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    widow = f["widow"]
    child = f["child"]
    clue = f["clue"]
    ghost = f["ghost"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who lived in {place.label}?",
            answer=f"{widow.label} lived in {place.label}, and the house belonged to the widow in the story.",
        ),
        QAItem(
            question=f"What clue did {child.label} notice before the ghost appeared?",
            answer=f"{child.label} noticed {clue.label}. It foreshadowed that something strange and important was nearby.",
        ),
        QAItem(
            question=f"What was the ghost really doing in the end?",
            answer=f"The ghost was helping, not hurting. It revealed {ghost.help.lower()}, so the scary sign made sense after the truth came out.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is foreshadowing?", "Foreshadowing is a clue that hints at something important before it happens."),
        QAItem("Why can an old house sound spooky at night?", "Old houses can creak, whisper, and rattle in the dark, which can feel spooky even when nothing bad is happening."),
        QAItem("What is a widow?", "A widow is a woman whose husband has died."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if s:
            bits.append(f"memes={dict(s)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.location:
            bits.append(f"location={e.location}")
        out.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
seen_clue(C) :- clue(C), seen(C).
uneasy_child :- seen_clue(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for o in OMENS.values():
        lines.append(asp.fact("clue", o.id))
        lines.append(asp.fact("seen", o.id))
    for g in GHOSTS.values():
        lines.append(asp.fact("ghost", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_gate() -> int:
    import asp
    model = asp.one_model(asp_program("#show seen_clue/1."))
    seen = set(asp.atoms(model, "seen_clue"))
    py = set((o.id,) for o in OMENS.values())
    return 0 if seen == py else 1


CURATED = [
    StoryParams(widow_name="Mrs. Vale", child_name="Mina", child_type="girl", place="hall", omen="footstep", ghost_kind="widow_ghost"),
    StoryParams(widow_name="Mrs. Reed", child_name="Ned", child_type="boy", place="attic", omen="candle", ghost_kind="lantern_ghost"),
    StoryParams(widow_name="Mrs. Grey", child_name="Tess", child_type="girl", place="garden", omen="window", ghost_kind="cat_ghost"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.omen not in OMENS or params.ghost_kind not in GHOSTS:
        raise StoryError("Invalid story parameters.")
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


def valid_story_count() -> int:
    return len(valid_combos())


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show seen_clue/1."))
        return
    if args.verify:
        rc = 0
        try:
            # ASP parity
            rc |= asp_verify_gate()
            # smoke test default generation
            s0 = generate(resolve_params(argparse.Namespace(place=None, omen=None, ghost=None, widow=None, child=None, child_type=None), random.Random(0)))
            if not s0.story.strip():
                raise RuntimeError("empty story")
            # multiple seeds
            for seed in (1, 7, 777):
                p = resolve_params(args, random.Random(seed))
                s = generate(p)
                if not s.story.strip():
                    raise RuntimeError("empty story")
            # qa/json/all smoke
            for p in CURATED[:3]:
                sm = generate(p)
                if len(sm.story_qa) < 1:
                    raise RuntimeError("empty qa")
            _ = generate(resolve_params(argparse.Namespace(place=None, omen=None, ghost=None, widow=None, child=None, child_type=None), random.Random(777))).to_json()
            _ = [generate(p) for p in CURATED]
            print("OK: verify smoke tests passed.")
        except Exception as e:
            print(f"VERIFY FAILED: {e}")
            rc = 1
        sys.exit(rc)
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
