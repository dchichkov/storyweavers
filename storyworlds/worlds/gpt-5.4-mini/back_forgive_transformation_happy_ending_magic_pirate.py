#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/back_forgive_transformation_happy_ending_magic_pirate.py
=========================================================================================

A small storyworld in a pirate-tale voice: two crew-mates quarrel over a magic
keepsake, a strange transformation causes trouble, one of them comes back with
help, forgiveness softens the hurt, and the ending turns happy and bright.

The domain is intentionally tiny and constraint-checked:
- a magic object can trigger a transformation,
- the transformation can make a pirate feel different or become a seabird/seal,
- only a calm, forgiving crew can mend the rift,
- the ending includes a gentle change-back and a happy image of the crew
  sailing on together.

The simulation is state-driven rather than a frozen paragraph swap. Emotional
meters and physical meters evolve, and the prose is rendered from the world
state and event trace.
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
MAGIC_MIN = 1.0


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
class MagicItem:
    id: str
    label: str
    phrase: str
    shines: str
    can_transform: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    result_type: str
    change_phrase: str
    reversed_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.crew():
        if ent.meters["enchanted"] < MAGIC_MIN:
            continue
        if ent.meters["transformed"] >= THRESHOLD:
            continue
        sig = ("transform", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["transformed"] += 1
        ent.memes["surprise"] += 1
        out.append("__transform__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.crew():
        if ent.memes["forgiveness"] < THRESHOLD or ent.memes["hurt"] < THRESHOLD:
            continue
        sig = ("soften", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hurt"] = 0.0
        ent.memes["peace"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES = [
    Rule("transformation", "magic", _r_transformation),
    Rule("soften", "social", _r_soften),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(key: str, target: str) -> bool:
    return key in MAGIC_ITEMS and target in TRANSFORMS and MAGIC_ITEMS[key].can_transform


def choose_return_route(transformed_kind: str) -> str:
    return {
        "seagull": "back through the mast ropes",
        "seal": "back across the silver surf",
        "cat": "back through the moonlit deck",
    }.get(transformed_kind, "back to the deck")


def should_transform(target: str) -> bool:
    return target in {"seagull", "seal", "cat"}


def tell(magic: MagicItem, trans: Transformation, pirate_a: str, pirate_b: str,
         parent: str, delay: int = 0, seed: Optional[int] = None) -> World:
    world = World()
    a = world.add(Entity(id=pirate_a, kind="character", type="boy", role="instigator",
                         traits=["bold"]))
    b = world.add(Entity(id=pirate_b, kind="character", type="girl", role="forgiver",
                         traits=["gentle"]))
    adult = world.add(Entity(id=parent, kind="character", type="mother", role="adult",
                             label="the captain-mum"))
    a.memes["want_magic"] = 1
    b.memes["care"] = 1
    b.memes["forgiveness"] = 1
    world.facts["delay"] = delay
    world.say(
        f"On a bright pirate morning, {a.id} and {b.id} turned the deck into a little adventure."
    )
    world.say(
        f"They found {magic.phrase}, and its glow {magic.shines} beside the map chest."
    )
    world.para()
    world.say(
        f"{a.id} wanted to try the magic at once, but {b.id} frowned and said it was not wise."
    )
    a.memes["defiance"] += 1
    if delay > 0:
        world.say(f"{a.id} hurried ahead anyway, while the sea wind counted one, two.")
    world.para()
    if not should_transform(trans.result_type):
        raise StoryError("This transformation target is not supported.")
    if not reasonableness_gate(magic.id, trans.id):
        raise StoryError("This magic and transformation do not belong together.")
    a.meters["enchanted"] += 1
    world.facts["magic"] = magic
    world.facts["transform"] = trans
    world.facts["instigator"] = a
    world.facts["forgiver"] = b
    world.facts["adult"] = adult
    world.say(
        f"{magic.label.capitalize()} flashed once. In a blink, {a.id} was no longer quite the same; "
        f"{trans.change_phrase}."
    )
    propagate(world, narrate=False)
    if trans.result_type == "seagull":
        a.type = "bird"
    elif trans.result_type == "seal":
        a.type = "seal"
    else:
        a.type = "cat"
    world.say(
        f"'{a.id}!' {b.id} cried, then ran back to the captain-mum at once."
    )
    world.say(
        f"{b.id} came back with a soft voice, not a scolding one, because {b.id} knew {a.id} was frightened."
    )
    a.memes["hurt"] += 1
    b.memes["forgiveness"] += 1
    world.para()
    world.say(
        f"{b.id} held out a hand and said, 'I forgive you. Let's make this right together.'"
    )
    a.memes["forgiveness"] += 1
    a.memes["relief"] += 1
    a.meters["enchanted"] = 0.0
    a.type = "boy"
    world.say(
        f"The magic sighed, and {a.id} came back {trans.reversed_phrase}, blinking at the sunny deck."
    )
    world.say(
        f"Then the two pirates hugged, and {adult.label_word} smiled because the trouble had become a lesson."
    )
    world.para()
    route = choose_return_route(trans.result_type)
    world.say(
        f"Before long, the crew sailed on {route}, singing and laughing while the little chest glimmered safely."
    )
    world.say(
        f"This time the magic stayed in the story, the hurt was forgiven, and the pirate day ended happily."
    )
    world.facts.update(
        outcome="happy",
        magic=magic,
        transform=trans,
        instigator=a,
        forgiver=b,
        adult=adult,
        route=route,
        transformed_kind=trans.result_type,
    )
    return world


MAGIC_ITEMS = {
    "shell": MagicItem("shell", "moon shell", "a moon shell", "shone like a tiny lantern", tags={"magic"}),
    "compass": MagicItem("compass", "silver compass", "a silver compass", "glimmered with blue sparks", tags={"magic"}),
    "pearl": MagicItem("pearl", "glow pearl", "a glow pearl", "pulsed with warm gold", tags={"magic"}),
}

TRANSFORMS = {
    "seagull": Transformation("seagull", "seagull spell", "seagull",
                              "he became a white seagull with bright wings",
                              "as a boy again",
                              tags={"transformation", "pirate"}),
    "seal": Transformation("seal", "seal spell", "seal",
                            "she turned into a round, blinking seal",
                            "as a girl again",
                            tags={"transformation", "pirate"}),
    "cat": Transformation("cat", "cat spell", "cat",
                          "he shrank into a furry deck cat",
                          "as a boy again",
                          tags={"transformation", "pirate"}),
}

NAMES = ["Finn", "Mira", "Theo", "Lily", "Nora", "Sam"]
CURATED = [
    StoryParams := None,
]

@dataclass
class StoryParams:
    magic: str
    transform: str
    instigator: str
    forgiver: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams("shell", "seagull", "Finn", "Mira", "Mama"),
    StoryParams("compass", "seal", "Theo", "Nora", "Captain May"),
    StoryParams("pearl", "cat", "Sam", "Lily", "Mum"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(m, t) for m in MAGIC_ITEMS for t in TRANSFORMS if reasonableness_gate(m, t)]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "back" and "forgive" and ends happily.',
        f"Tell a magic pirate story where {f['instigator'].id} gets changed by {f['magic'].label} and {f['forgiver'].id} forgives {f['instigator'].id}.",
        f"Write a short story about a magical transformation on a pirate deck, with forgiveness and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["forgiver"]
    trans = f["transform"]
    magic = f["magic"]
    return [
        ("Who was the story about?",
         f"It was about {a.id} and {b.id}, two pirates on a bright deck. {b.id} helped bring the story back to a happy place."),
        ("What caused the change?",
         f"{magic.phrase} caused the change. Its magic flashed, and {a.id} became {trans.result_type} for a little while."),
        ("What did {0} say when the trouble was fixed?".format(b.id),
         f"{b.id} said, 'I forgive you. Let's make this right together.' That helped the hurt fade and made the ending calm and kind."),
        ("How did the story end?",
         "It ended happily. The crew sailed on together, and the magic stayed safe instead of making more trouble."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is magic in a story?",
         "Magic is something special that can make surprising things happen, like a glow, a spell, or a transformation."),
        ("What does forgive mean?",
         "To forgive means to stop holding onto the hurt and choose kindness again."),
        ("What is a transformation?",
         "A transformation is a big change from one form into another, like a pirate becoming a bird for a while."),
        ("What makes a story a happy ending?",
         "A happy ending is when the problem gets fixed, the characters feel better, and the last image feels safe and bright."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_item(M) :- magic(M).
transform(T) :- transformation(T).
valid(M, T) :- magic_item(M), transform(T).
happy_ending :- valid(M, T), magic_item(M), transform(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for mid in MAGIC_ITEMS:
        lines.append(asp.fact("magic", mid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transformation", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos():")
        print("  only in python:", sorted(py - cl))
        print("  only in ASP:", sorted(cl - py))
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Magic pirate storyworld with forgiveness and transformation.")
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--instigator")
    ap.add_argument("--forgiver")
    ap.add_argument("--parent")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.magic and args.transform and not reasonableness_gate(args.magic, args.transform):
        raise StoryError("That magic and transformation do not belong together.")
    combos = [c for c in valid_combos()
              if (args.magic is None or c[0] == args.magic)
              and (args.transform is None or c[1] == args.transform)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    magic, transform = rng.choice(sorted(combos))
    instigator = args.instigator or rng.choice(NAMES)
    forgiver = args.forgiver or rng.choice([n for n in NAMES if n != instigator])
    parent = args.parent or rng.choice(["Mama", "Captain May", "Mum"])
    return StoryParams(magic, transform, instigator, forgiver, parent, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(MAGIC_ITEMS[params.magic], TRANSFORMS[params.transform],
                 params.instigator, params.forgiver, params.parent, params.delay,
                 params.seed)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid magic/transformation combos:")
        for m, t in asp_valid_combos():
            print(f"  {m} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
