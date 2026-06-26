#!/usr/bin/env python3
"""
storyworlds/worlds/preserve_reconciliation_dialogue_twist_fable.py
===================================================================

A small fable-like storyworld about keeping something safe, a misunderstanding,
a dialogue, a twist, and a reconciliation.

Premise:
- A careful animal wants to preserve a shared stash.
- A second animal misunderstands and thinks the stash is being hidden or hoarded.
- They argue in dialogue.
- A twist reveals the second animal had a good reason.
- They reconcile by making a new plan that truly preserves the stash for both.

The world is deliberately small and classical: a few characters, a few objects,
and a stateful emotional/physical simulation that drives the prose.
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


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "hen", "owl", "goat", "squirrel", "rabbit"}
        male = {"fox", "wolf", "raven", "badger", "deer", "bear"}
        # fable default: use neutral if uncertain; names don't need biological precision.
        if self.type in {"squirrel", "hen", "owl", "rabbit"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"wolf", "raven", "badger", "deer", "bear"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    stash: str
    hero: str
    twist: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hill": Place(name="the hill", affords={"bury", "guard", "share"}),
    "grove": Place(name="the grove", affords={"bury", "hide", "share"}),
    "barn": Place(name="the old barn", affords={"store", "guard", "share"}),
}

HEROES = {
    "squirrel": {"type": "squirrel", "label": "squirrel", "trait": "careful"},
    "rabbit": {"type": "rabbit", "label": "rabbit", "trait": "busy"},
    "hen": {"type": "hen", "label": "hen", "trait": "practical"},
}

VISITORS = {
    "raven": {"type": "raven", "label": "raven", "trait": "sharp-eyed"},
    "fox": {"type": "fox", "label": "fox", "trait": "clever"},
    "owl": {"type": "owl", "label": "owl", "trait": "quiet"},
}

STASHES = {
    "acorns": {
        "label": "acorns",
        "phrase": "a bowl of acorns",
        "kind": "food",
        "plural": True,
        "preserve_verb": "preserve",
        "preserve_gerund": "preserving",
    },
    "jam": {
        "label": "jam",
        "phrase": "a jar of berry jam",
        "kind": "food",
        "plural": False,
        "preserve_verb": "preserve",
        "preserve_gerund": "preserving",
    },
    "seeds": {
        "label": "seeds",
        "phrase": "a little sack of seeds",
        "kind": "food",
        "plural": True,
        "preserve_verb": "keep safe",
        "preserve_gerund": "keeping safe",
    },
}

TWISTS = {
    "winter": "The visitor was not greedy at all; she was saving food for the long winter.",
    "nest": "The visitor wanted the stash for a nest, not to take it away forever.",
    "gift": "The visitor had brought a hidden gift and needed a fair place to leave it.",
}

# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _r_scattered(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "thing":
            continue
        if e.meters.get("scattered", 0.0) < THRESHOLD:
            continue
        sig = ("scattered", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["at_risk"] = 1.0
        out.append(f"The stash looked in danger of being lost to weather and time.")
    return out


def _r_reconcile(world: World) -> list[str]:
    hero = world.entities.get("hero")
    visitor = world.entities.get("visitor")
    stash = world.entities.get("stash")
    if not hero or not visitor or not stash:
        return []
    if hero.memes.get("grudge", 0.0) < THRESHOLD:
        return []
    if visitor.memes.get("truth", 0.0) < THRESHOLD:
        return []
    sig = ("reconcile", hero.id, visitor.id, stash.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["grudge"] = 0.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    visitor.memes["trust"] = visitor.memes.get("trust", 0.0) + 1.0
    stash.meters["secure"] = 1.0
    return ["__reconcile__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_scattered, _r_reconcile):
            items = rule(world)
            if items:
                changed = True
                produced.extend(x for x in items if x != "__reconcile__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_state(world: World) -> bool:
    stash = world.get("stash")
    return stash.meters.get("at_risk", 0.0) >= THRESHOLD


def predict_path(world: World, method: str) -> bool:
    sim = world.copy()
    sim.get("stash").meters["scattered"] = 1.0 if method in {"bury", "store"} else 0.0
    propagate(sim, narrate=False)
    return bool(sim.get("stash").meters.get("at_risk", 0.0) >= THRESHOLD)


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, stash: Entity) -> None:
    world.say(
        f"Once, a careful {hero.label} lived near {world.place.name} and kept "
        f"{stash.phrase} close."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved to {world.facts['preserve_verb']} "
        f"{stash.it()} because the little food could matter later."
    )


def arrival_and_misread(world: World, hero: Entity, visitor: Entity, stash: Entity) -> None:
    world.para()
    world.say(
        f"One day, a {visitor.label} came to {world.place.name} and saw the hidden stash."
    )
    world.say(
        f'"Why are you hiding {stash.it()}?" {visitor.pronoun("subject").capitalize()} asked.'
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["grudge"] = 1.0
    visitor.memes["curiosity"] = visitor.memes.get("curiosity", 0.0) + 1.0
    visitor.memes["uncertainty"] = 1.0


def dialogue_tension(world: World, hero: Entity, visitor: Entity, stash: Entity) -> None:
    world.say(
        f'"I am not hiding {stash.it()}," said the {hero.label}. '
        f'"I am trying to {world.facts["preserve_verb"]} {stash.it()} so it will last."'
    )
    world.say(
        f'"Last for whom?" asked the {visitor.label}, still frowning.'
    )
    world.say(
        f'"For the days when food is scarce," said the {hero.label}. '
        f'"A small treasure is safer when it is cared for."'
    )


def twist_reveal(world: World, hero: Entity, visitor: Entity, stash: Entity) -> None:
    world.para()
    truth = world.facts["twist_text"]
    visitor.memes["truth"] = 1.0
    world.say(f"Then came the twist: {truth}")
    world.say(
        f'The {visitor.label} lowered {visitor.pronoun("possessive")} ears. '
        f'"I thought you meant to keep it all for yourself," {visitor.pronoun("subject")} said.'
    )
    world.say(
        f'"I only wanted to protect it," said the {hero.label}. '
        f'"I was afraid it would spoil, scatter, or be lost."'
    )


def reconciliation(world: World, hero: Entity, visitor: Entity, stash: Entity) -> None:
    world.para()
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    visitor.memes["trust"] = visitor.memes.get("trust", 0.0) + 1.0
    stash.meters["secure"] = 1.0
    world.say(
        f'The {visitor.label} nodded. "Then let us preserve it together," {visitor.pronoun("subject")} said.'
    )
    world.say(
        f'They found a dry corner, shared the work, and made a safer place for {stash.it()}. '
        f"By dusk, the stash was tucked away well, and neither friend had to guard it alone."
    )


# ---------------------------------------------------------------------------
# Story builder
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero_cfg = HEROES[params.hero]
    visitor_name = next(k for k in VISITORS if k != params.twist)  # twist key not same domain
    visitor_cfg = VISITORS[visitor_name]
    stash_cfg = STASHES[params.stash]
    twist_text = TWISTS[params.twist]

    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg["type"], label=hero_cfg["label"]))
    visitor = world.add(Entity(id="visitor", kind="character", type=visitor_cfg["type"], label=visitor_cfg["label"]))
    stash = world.add(Entity(
        id="stash",
        kind="thing",
        type=stash_cfg["kind"],
        label=stash_cfg["label"],
        phrase=stash_cfg["phrase"],
        plural=stash_cfg["plural"],
        owner=hero.id,
        caretaker=hero.id,
    ))

    world.facts.update(
        preserve_verb=stash_cfg["preserve_verb"],
        preserve_gerund=stash_cfg["preserve_gerund"],
        twist_text=twist_text,
        hero=hero,
        visitor=visitor,
        stash=stash,
    )

    intro(world, hero, stash)
    arrival_and_misread(world, hero, visitor, stash)
    dialogue_tension(world, hero, visitor, stash)
    twist_reveal(world, hero, visitor, stash)
    reconciliation(world, hero, visitor, stash)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a {f["hero"].label} who wants to {f["preserve_verb"]} {f["stash"].it()} and must explain the plan in dialogue.',
        f"Tell a child-friendly story with a twist where a {f['visitor'].label} first suspects the {f['hero'].label} is hiding food, but the two animals reconcile.",
        f'Write a simple fable that includes the words "{f["preserve_gerund"]}" and "twist" and ends with two friends sharing responsibility.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    visitor = f["visitor"]
    stash = f["stash"]
    qa = [
        QAItem(
            question=f"What was the {hero.label} trying to do with the {stash.label}?",
            answer=f"The {hero.label} was trying to {f['preserve_verb']} the {stash.label} so it would last longer.",
        ),
        QAItem(
            question=f"Why did the {visitor.label} first sound upset?",
            answer=f"The {visitor.label} thought the {hero.label} might be hiding the {stash.label} for itself, so it asked sharp questions.",
        ),
        QAItem(
            question="What changed after the twist?",
            answer=f"After the twist, the {visitor.label} understood the true reason and joined the {hero.label} in protecting the stash.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The two animals reconciled, shared the work, and made the stash safe together.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "preserve": [
        QAItem(
            question="What does it mean to preserve something?",
            answer="To preserve something means to keep it safe, fresh, or unchanged for later.",
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising new fact that changes how you understand what was happening.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing, understand each other, and become friendly again.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in a story.",
        )
    ],
    "fable": [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("preserve", "dialogue", "twist", "reconciliation", "fable") for item in WORLD_KNOWLEDGE[key]]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
preserve_goal(H, S) :- hero(H), stash(S).
misread(V, H, S) :- visitor(V), hero(H), stash(S), sees(V, S), not understands(V, H, S).
twist_reveals(V, H, S) :- misread(V, H, S), truth(V).
reconcile(H, V, S) :- preserve_goal(H, S), twist_reveals(V, H, S).
valid_story(P, H, S, V, T) :- place(P), hero(H), stash(S), visitor(V), twist(T),
                              located_at(S, P), preserve_goal(H, S).
#show valid_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
    for sid in STASHES:
        lines.append(asp.fact("stash", sid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for pid in PLACES:
        lines.append(asp.fact("located_at", "acorns", pid))
        lines.append(asp.fact("located_at", "jam", pid))
        lines.append(asp.fact("located_at", "seeds", pid))
    for vid in VISITORS:
        lines.append(asp.fact("sees", vid, "acorns"))
        lines.append(asp.fact("sees", vid, "jam"))
        lines.append(asp.fact("sees", vid, "seeds"))
    for vid in VISITORS:
        lines.append(asp.fact("truth", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if not asp_valid_stories():
        print("MISMATCH: no ASP valid_story/5 atoms found.")
        return 1
    print(f"OK: ASP produced {len(asp_valid_stories())} valid story tuples.")
    return 0


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about preserving, dialogue, twist, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--stash", choices=STASHES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--twist", choices=TWISTS)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for p in PLACES:
        for h in HEROES:
            for s in STASHES:
                for t in TWISTS:
                    combos.append((p, h, s, t))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              if True else c]
    combos = [c for c in combos if args.hero is None or c[1] == args.hero]
    combos = [c for c in combos if args.stash is None or c[2] == args.stash]
    combos = [c for c in combos if args.twist is None or c[3] == args.twist]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, hero, stash, twist = rng.choice(sorted(combos))
    return StoryParams(place=place, hero=hero, stash=stash, twist=twist)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"location={e.location or world.place.name}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} compatible stories:")
        for row in models[:50]:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(place="hill", hero="squirrel", stash="acorns", twist="winter"),
            StoryParams(place="grove", hero="hen", stash="jam", twist="nest"),
            StoryParams(place="barn", hero="rabbit", stash="seeds", twist="gift"),
        ]
        samples = [generate(p) for p in cur]
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
