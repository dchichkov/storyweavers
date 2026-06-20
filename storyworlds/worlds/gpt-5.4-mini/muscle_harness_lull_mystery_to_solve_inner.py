#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/muscle_harness_lull_mystery_to_solve_inner.py
===============================================================================

A standalone storyworld for a small animal-story domain with:
- a mystery to solve
- inner monologue
- the seed words: muscle, harness, lull

The world centers on a young animal helper, a missing harness, and a quiet lull
in the barnyard that makes tiny clues easy to miss. The model uses stateful
characters, physical meters, and emotional memes; the story is driven by a
simple causal world model rather than by post-hoc paraphrase.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "lost": 0.0, "found": 0.0, "wet": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "focus": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "sister", "mare", "doe"}
        male = {"boy", "father", "brother", "stallion", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    quiet: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    spot: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Harness:
    id: str
    label: str
    phrase: str
    has_lead: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    action: str
    success: str
    fail: str
    tags: set[str] = field(default_factory=set)


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if x)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").meters["lost"] >= THRESHOLD and ("worry", "hero") not in world.fired:
        world.fired.add(("worry", "hero"))
        world.get("hero").memes["worry"] += 1
        out.append("")
    return out


def _r_focus(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes["focus"] >= THRESHOLD and ("focus", "clue") not in world.fired:
        world.fired.add(("focus", "clue"))
        world.get("hero").memes["hope"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("focus", _r_focus)]


def quiet_lull(world: World, place: Place) -> None:
    if place.quiet:
        world.say(f"At {place.label}, the afternoon had a soft lull, and even the leaves seemed to whisper.")
    else:
        world.say(f"At {place.label}, the air was busy, but one calm lull opened between the sounds.")


def introduce(world: World, hero: Entity, buddy: Entity, place: Place, harness: Harness) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} was a little {hero.type} with quick eyes and strong little muscle for pulling."
        f" {buddy.id} stayed close, tail twitching with curiosity."
    )
    world.say(
        f"They had {harness.phrase} ready for the morning job, because the harness made the work safe and neat."
    )


def mystery_starts(world: World, hero: Entity, clue: Clue, harness: Harness) -> None:
    hero.meters["lost"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But when {hero.id} looked for the {harness.label}, it was gone."
    )
    world.say(
        f"{hero.id} stared at the empty hook by the wall. 'Where could it be?' "
        f"{hero.id} thought. 'I put it down only a moment ago.'"
    )
    world.say(
        f"Then {clue.phrase} caught {hero.pronoun('possessive')} eye."
    )


def inner_monologue(world: World, hero: Entity, clue: Clue, harness: Harness, place: Place) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"'{hero.id}, think,' {hero.pronoun()} told {hero.pronoun('object')} in a tiny inner voice."
    )
    world.say(
        f"'If the harness is missing, maybe it did not vanish. Maybe it got moved during the lull.'"
    )
    world.say(
        f"{hero.id} peered toward {clue.spot}. The quiet made small things easier to notice."
    )


def follow_clue(world: World, hero: Entity, clue: Clue, harness: Harness) -> None:
    if clue.kind == "wind":
        hero.memes["hope"] += 1
        world.say(
            f"{hero.id} sniffed the air and followed the clue to {clue.spot}."
        )
        world.say(
            f"The harness did not hide in the dark at all. It had been snagged there when the wind tugged the strap."
        )
    else:
        world.say(f"{hero.id} followed {clue.label} to {clue.spot}.")


def solve(world: World, hero: Entity, buddy: Entity, harness: Harness, rescue: Rescue) -> None:
    hero.meters["found"] += 1
    hero.memes["relief"] += 1
    buddy.memes["relief"] += 1
    world.say(
        f"{hero.id} lifted the {harness.label} free and gave it a careful shake."
    )
    world.say(
        f"Then {hero.id} and {buddy.id} used {rescue.action}, and the day felt tidy again."
    )


def ending(world: World, hero: Entity, buddy: Entity, harness: Harness, place: Place) -> None:
    world.say(
        f"By the end, the harness hung ready on the hook again, and {hero.id} felt proud for solving the mystery."
    )
    world.say(
        f"The barn settled back into its gentle quiet, with {buddy.id} beside {hero.id} and the lull turning peaceful instead of puzzling."
    )


def tell(place: Place, clue: Clue, harness: Harness, rescue: Rescue,
         hero_name: str = "Milo", hero_type: str = "foal",
         buddy_name: str = "Pip", buddy_type: str = "kitten") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, role="solver"))
    buddy = world.add(Entity(id=buddy_name, kind="character", type=buddy_type, label=buddy_name, role="helper"))
    world.add(Entity(id="hook", label="the hook"))
    world.facts.update(place=place, clue=clue, harness=harness, rescue=rescue, hero=hero, buddy=buddy)

    quiet_lull(world, place)
    introduce(world, hero, buddy, place, harness)
    world.para()
    mystery_starts(world, hero, clue, harness)
    inner_monologue(world, hero, clue, harness, place)
    follow_clue(world, hero, clue, harness)
    world.para()
    solve(world, hero, buddy, harness, rescue)
    ending(world, hero, buddy, harness, place)
    propagate(world, narrate=False)
    world.facts["solved"] = hero.meters["found"] >= THRESHOLD
    return world


PLACES = {
    "barn": Place("barn", "the barn", quiet=True, tags={"barn", "quiet"}),
    "orchard": Place("orchard", "the orchard", quiet=True, tags={"orchard", "quiet"}),
    "yard": Place("yard", "the yard", quiet=False, tags={"yard"}),
}

CLUES = {
    "wind": Clue("wind", "a loose strap", "A loose strap on the fence fluttered once", "the fence post", "wind", tags={"wind", "strap"}),
    "mud": Clue("mud", "a muddy print", "A muddy print near the gate pointed the way", "the gate", "mud", tags={"mud"}),
    "hay": Clue("hay", "a hay crumb", "A hay crumb on the floor shone pale in the light", "the feed bin", "hay", tags={"hay"}),
}

HARNESS = {
    "work": Harness("work", "harness", "a sturdy harness", has_lead=True, tags={"harness"}),
    "bright": Harness("bright", "red harness", "a bright red harness", has_lead=True, tags={"harness", "red"}),
}

RESCUES = {
    "pull": Rescue("pull", "tug gently", "a careful tug", "pulled the strap free", "could not free the strap", tags={"pull"}),
    "lift": Rescue("lift", "lift it off", "a careful lift", "lifted it down", "could not lift it down", tags={"lift"}),
}

CURATED = [
    ("barn", "wind", "work", "pull", "Milo", "foal", "Pip", "kitten"),
    ("orchard", "hay", "bright", "lift", "Poppy", "colt", "Moss", "puppy"),
    ("yard", "mud", "work", "pull", "Nell", "foal", "Toby", "kitten"),
]


@dataclass
class StoryParams:
    place: str
    clue: str
    harness: str
    rescue: str
    hero_name: str
    hero_type: str
    buddy_name: str
    buddy_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a tiny mystery and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--harness", choices=HARNESS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--name")
    ap.add_argument("--buddy")
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
    combos = []
    for p in PLACES:
        for c in CLUES:
            for h in HARNESS:
                for r in RESCUES:
                    combos.append((p, c, h, r))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.harness is None or c[2] == args.harness)
              and (args.rescue is None or c[3] == args.rescue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, harness, rescue = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(["Milo", "Poppy", "Nell", "Sunny", "Tansy"])
    buddy_name = args.buddy or rng.choice(["Pip", "Moss", "Dot", "Bramble", "Twig"])
    hero_type = rng.choice(["foal", "colt", "kid goat", "lamb"])
    buddy_type = rng.choice(["kitten", "puppy", "duckling", "chick"])
    return StoryParams(place, clue, harness, rescue, hero_name, hero_type, buddy_name, buddy_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], HARNESS[params.harness], RESCUES[params.rescue],
                 params.hero_name, params.hero_type, params.buddy_name, params.buddy_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story for a young child that includes the words muscle, harness, and lull.",
        f"Tell a gentle mystery about {f['hero'].id} and a missing harness during a quiet lull.",
        f"Write a story with inner monologue where {f['hero'].id} solves the harness mystery by following a clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, buddy, place, clue, harness = f["hero"], f["buddy"], f["place"], f["clue"], f["harness"]
    return [
        QAItem(f"What kind of story is this?", "It is an animal story with a small mystery to solve. The main character thinks through the clues in an inner voice."),
        QAItem(f"What was missing?", f"The {harness.label} was missing at first, so {hero.id} had to search for it. That is what started the mystery."),
        QAItem(f"How did {hero.id} solve the mystery?", f"{hero.id} followed the clue to {clue.spot} and found the {harness.label} there. The clue was enough to explain where it had gone."),
        QAItem(f"How did the story end?", f"It ended with the {harness.label} back on the hook and the work ready to begin again. {hero.id} felt proud and calm at the end."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a harness?", "A harness is a strap or set of straps that helps guide or hold an animal safely. People use it for work or for leading an animal."),
        QAItem("What does lull mean?", "A lull is a quiet pause when things get calm for a little while. It can make a place feel peaceful."),
        QAItem("What does a muscle do?", "A muscle helps an animal move, stretch, and pull. Strong muscles make hard work easier."),
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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,H,R) :- place(P), clue(C), harness(H), rescue(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for h in HARNESS:
        lines.append(asp.fact("harness", h))
    for r in RESCUES:
        lines.append(asp.fact("rescue", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, harness=None, rescue=None, name=None, buddy=None), random.Random(7)))
        _ = sample.story
        _ = format_qa(sample)
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
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
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
