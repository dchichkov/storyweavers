#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snicker_before_snack_friendship_foreshadowing_curiosity_mystery.py
===================================================================================================

A tiny mystery storyworld about friends, a curious clue, a foreshadowed surprise,
and a snack that should have been enjoyed before the secret was revealed.

Premise
-------
A child hears a strange snicker, notices a clue before snack time, and follows
curiosity with a friend to solve a small mystery. The turn is that the "mystery"
is not danger at all: it is a hidden snack planned by a thoughtful friend, and
the snicker was only foreshadowing that someone was trying not to laugh.

The world model tracks:
- physical meters: hiding, found, ready, opened, scattered
- emotional memes: curiosity, trust, delight, relief, mischief

The story stays concrete and state-driven: the clue, the search, the reveal, and
the changed ending image all come from the simulated world state.
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

NAMES = ["Mia", "Lena", "Noah", "Theo", "Ava", "Eli", "Zoe", "Iris", "Milo", "Nina"]
PLACES = {
    "kitchen": "the kitchen",
    "garden": "the garden",
    "playroom": "the playroom",
    "porch": "the porch",
}
SNACKS = {
    "cookies": "a small plate of cookies",
    "apples": "apple slices in a blue bowl",
    "crackers": "a crinkly box of crackers",
    "berries": "a bowl of berries with a tiny spoon",
}
CLUES = {
    "napkin": "a napkin tucked under a book",
    "crumbs": "a few crumbs on the table",
    "note": "a folded note with a smiley face",
    "trail": "a tiny trail of sugar",
}
TRIGGERS = {
    "snicker": "snicker",
    "before": "before",
    "snack": "snack",
}


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


@dataclass
class StoryParams:
    place: str
    snack: str
    clue: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_found(world: World) -> list[str]:
    out = []
    child = world.get("child1")
    clue = world.get("clue")
    if child.memes["curiosity"] < THRESHOLD or clue.meters["found"] >= THRESHOLD:
        return out
    if world.fired and ("found",) in world.fired:
        return out
    if child.meters["searching"] >= THRESHOLD and clue.meters["hidden"] >= THRESHOLD:
        clue.meters["found"] += 1
        world.fired.add(("found",))
        child.memes["satisfaction"] += 1
        out.append("The clue finally made sense.")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    snack = world.get("snack")
    clue = world.get("clue")
    if clue.meters["found"] < THRESHOLD or snack.meters["hidden"] < THRESHOLD:
        return out
    if ("reveal",) in world.fired:
        return out
    world.fired.add(("reveal",))
    snack.meters["hidden"] = 0.0
    snack.meters["ready"] += 1
    world.get("parent").memes["mischief"] += 1
    out.append("The secret was not scary at all.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    snack = world.get("snack")
    if snack.meters["ready"] < THRESHOLD or ("relief",) in world.fired:
        return out
    world.fired.add(("relief",))
    for eid in ("child1", "child2"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["trust"] += 1
    out.append("The friends relaxed all at once.")
    return out


CAUSAL_RULES = [Rule("found", _r_found), Rule("reveal", _r_reveal), Rule("relief", _r_relief)]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for snack in SNACKS:
            for clue in CLUES:
                combos.append((place, snack, clue))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small friendship mystery with a hidden snack.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if not combos:
        raise StoryError("No valid story combinations.")
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.snack and args.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.snack is None or c[1] == args.snack)
        and (args.clue is None or c[2] == args.clue)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, snack, clue = rng.choice(sorted(filtered))
    g1 = args.child1_gender or rng.choice(["girl", "boy"])
    g2 = args.child2_gender or ("boy" if g1 == "girl" else "girl")
    child1 = args.child1 or rng.choice(NAMES)
    child2 = args.child2 or next(n for n in rng.sample(NAMES, len(NAMES)) if n != child1)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, snack=snack, clue=clue, child1=child1, child1_gender=g1, child2=child2, child2_gender=g2, parent=parent)


def tell(params: StoryParams) -> World:
    world = World()
    c1 = world.add(Entity(id="child1", kind="character", type=params.child1_gender, label=params.child1, role="curious"))
    c2 = world.add(Entity(id="child2", kind="character", type=params.child2_gender, label=params.child2, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent", role="planner"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=CLUES[params.clue]))
    snack = world.add(Entity(id="snack", kind="thing", type="snack", label=SNACKS[params.snack]))
    clue.meters["hidden"] = 1.0
    snack.meters["hidden"] = 1.0
    c1.memes["curiosity"] = 1.0
    c2.memes["trust"] = 1.0
    world.say(f"In {PLACES[params.place]}, {params.child1} heard a small {TRIGGERS['snicker']} from behind {params.parent}'s chair.")
    world.say(f"It happened {TRIGGERS['before']} {TRIGGERS['snack']} time, and that made {params.child1} lean closer.")
    world.say(f"{params.child2} noticed {CLUES[params.clue]}, which felt like a clue in a mystery.")
    world.para()
    c1.meters["searching"] = 1.0
    world.say(f"{params.child1} and {params.child2} followed the clue together, and their friendship made the search feel brave.")
    world.say(f'The question kept poking at them: "What is hidden here, and why did someone snicker?"')
    propagate(world, narrate=False)
    world.para()
    if snack.meters["ready"] >= THRESHOLD:
        world.say(f"They found {SNACKS[params.snack]} tucked away, and {params.parent} laughed softly.")
        world.say(f'The snicker was only a tiny foreshadowing clue: the surprise was a snack, saved for later.')
        world.say(f"At the end, the friends sat close and shared the snack, happy that the mystery had turned kind.")
    else:
        world.say(f"They kept searching until the hidden snack appeared, and the mystery unfolded into a gentle surprise.")
        world.say(f"Their curiosity had been right, and the clue had been waiting to be understood.")
    world.facts.update(params=params, child1=c1, child2=c2, parent=parent, clue=clue, snack=snack)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a small mystery story for a young child that includes the words snicker, before, and snack.",
        f"Tell a friendship story where {p.child1} and {p.child2} follow a clue before snack time and discover why someone snickered.",
        f"Write a gentle mystery with curiosity and foreshadowing, ending with a snack shared by friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(question="What did the children hear?", answer=f"They heard a small snicker, which made {p.child1} curious right away. It was only a tiny hint that someone knew more than they were saying."),
        QAItem(question="What was the clue?", answer=f"The clue was {CLUES[p.clue]}. They followed it together because friendship made them brave enough to keep looking."),
        QAItem(question="How did the mystery end?", answer=f"It ended with {SNACKS[p.snack]} being shared as a surprise snack. The snicker turned out to be foreshadowing, not trouble."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes you want to ask questions and find out what is going on."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a small hint that tells you something important may happen later."),
        QAItem(question="What does friendship help with?", answer="Friendship helps people work together, feel brave, and solve small problems side by side."),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for snack in SNACKS:
        lines.append(asp.fact("snack", snack))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
        lines.append(asp.fact("valid", place, snack, clue) if False else "")
    for place in PLACES:
        for snack in SNACKS:
            for clue in CLUES:
                lines.append(asp.fact("valid", place, snack, clue))
    return "\n".join([x for x in lines if x])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        resolved = resolve_params(build_parser().parse_args([]), random.Random(7))
        sample = generate(resolved)
        _ = sample.story
    except Exception as e:
        print(f"FAIL: smoke test crashed: {e}")
        return 1
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity matches Python valid_combos().")
    else:
        print("MISMATCH: ASP parity does not match Python valid_combos().")
        rc = 1
    print("OK: generate smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.snack not in SNACKS or params.clue not in CLUES:
        raise StoryError("Invalid parameters.")
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
    StoryParams(place="kitchen", snack="cookies", clue="note", child1="Mia", child1_gender="girl", child2="Noah", child2_gender="boy", parent="mother"),
    StoryParams(place="garden", snack="berries", clue="crumbs", child1="Theo", child1_gender="boy", child2="Ava", child2_gender="girl", parent="father"),
    StoryParams(place="playroom", snack="crackers", clue="trail", child1="Zoe", child1_gender="girl", child2="Milo", child2_gender="boy", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story combos.")
        for t in valid_combos():
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
