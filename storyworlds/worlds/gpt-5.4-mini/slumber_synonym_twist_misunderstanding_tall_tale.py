#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slumber_synonym_twist_misunderstanding_tall_tale.py
==================================================================================

A standalone storyworld for a tall-tale bedtime misunderstanding:
a child hears the word *synonym*, thinks it is something to *catch*,
and the resulting twist turns a sleepy house into an unexpected, gentle
adventure. The story is tiny, classical, and state-driven: characters get
sleepy, a misunderstanding escalates, a grown-up clarifies the meaning, and the
ending proves the change with a calm slumber.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/slumber_synonym_twist_misunderstanding_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/slumber_synonym_twist_misunderstanding_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/slumber_synonym_twist_misunderstanding_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/slumber_synonym_twist_misunderstanding_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/slumber_synonym_twist_misunderstanding_tall_tale.py --verify
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
SENSE_MIN = 2


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
    attrs: dict = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    meaning: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    trigger: str
    misunderstanding: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sleep(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["sleepy"] >= THRESHOLD:
            sig = ("sleep", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["slumber"] += 1
            out.append(f"{e.id} yawned so hard that even the lamp seemed to blink slower.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    if world.facts.get("reveal_done"):
        for e in world.characters():
            if e.memes["worry"] >= THRESHOLD:
                sig = ("calm", e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                e.memes["worry"] = 0.0
                e.memes["relief"] += 1
                out.append(f"{e.id} felt the worry melt like butter in a warm pan.")
    return out


CAUSAL_RULES = [Rule("sleep", "physical", _r_sleep), Rule("calm", "social", _r_calm)]


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
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(item: Item, twist: Twist) -> bool:
    return "night" in item.tags and "words" in twist.tags


def predict_twist(world: World, item: Item, twist: Twist) -> dict:
    sim = world.copy()
    _do_twist(sim, sim.get("child"), item, twist, narrate=False)
    return {"confused": sim.get("child").memes["confusion"] >= THRESHOLD}


def _do_twist(world: World, child: Entity, item: Item, twist: Twist, narrate: bool = True) -> None:
    child.memes["confusion"] += 1
    child.meters["restless"] += 1
    world.facts["reveal_done"] = False
    world.say(f"{child.id} heard the word {item.label} and thought it was a thing one could fetch from under the moon.")
    world.say(f"That was the first half of the misunderstanding: {twist.misunderstanding}")


def explain(world: World, adult: Entity, child: Entity, twist: Twist, item: Item) -> None:
    adult.memes["gentleness"] += 1
    world.facts["reveal_done"] = True
    world.say(f"{adult.label_word.capitalize()} chuckled and said that {item.label} was not a rope, a stone, or a button for the sky.")
    world.say(f'"{item.label}" means "{item.meaning}," {adult.pronoun()} said, and the word itself sounded like a soft feather pillow.')


def twist_turn(world: World, child: Entity, item: Item, twist: Twist) -> None:
    child.memes["wonder"] += 1
    child.meters["restless"] += 1
    world.say(f"Then came the twist: {twist.reveal}")
    world.say(f"{child.id} laughed, because the mystery had been a word all along, and the word was a synonym for a simpler one.")


def bedtime(world: World, child: Entity, adult: Entity) -> None:
    child.meters["sleepy"] += 1
    adult.meters["sleepy"] += 1
    propagate(world, narrate=True)
    world.say(f"At last {child.id} climbed under the quilt and slipped into a deep slumber while {adult.id} counted the stars outside the window.")
    world.say("The house grew quiet, and the tall tale ended in a small, peaceful snore.")


def tell(theme: Twist, item: Item, child_name: str = "Milo", child_gender: str = "boy",
         adult_name: str = "Grandma", adult_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the grown-up"))
    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 0.0
    adult.memes["patience"] = 1.0
    world.say(f"One moonlit evening, {child.id} was full of questions and almost full of slumber.")
    world.say(f"{child.id} had heard the word {item.label} and wanted to know what it really meant.")
    world.para()
    child.memes["confusion"] += 1
    child.meters["restless"] += 1
    world.say(f"That was a tall, tangled mistake, because {theme.misunderstanding}")
    world.say(f"{adult.id} listened carefully, and the room stayed as quiet as a quilt.")
    world.para()
    explain(world, adult, child, theme, item)
    twist_turn(world, child, item, theme)
    bedtime(world, child, adult)
    world.facts.update(child=child, adult=adult, item=item, twist=theme, outcome="settled")
    return world


ITEMS = {
    "slumber": Item("slumber", "slumber", "a deep, cozy sleep", "sleep", tags={"night", "words"}),
    "synonym": Item("synonym", "synonym", "a word that means the same as another word", "same-meaning word", tags={"night", "words"}),
}

TWISTS = {
    "misunderstanding": Twist(
        "misunderstanding",
        "synonym",
        "The child thought the new word was a little creature or object that could be lost in the dark.",
        "But the grown-up showed that a synonym is only a word with a twin meaning, not a thing to chase.",
        tags={"words", "night"},
    ),
    "twist": Twist(
        "twist",
        "slumber",
        "The child thought slumber was a giant bedtime bird with feathers of moonlight.",
        "But the grown-up explained that slumber is just another word for sleep.",
        tags={"words", "night"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Maya"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Leo", "Finn"]
ADULT_NAMES = ["Grandma", "Grandpa", "Mama", "Papa"]


@dataclass
class StoryParams:
    twist: str
    item: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(t, i) for t in TWISTS for i in ITEMS if is_reasonable(ITEMS[i], TWISTS[t])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale bedtime storyworld with slumber and synonym.")
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.twist and args.item and not is_reasonable(ITEMS[args.item], TWISTS[args.twist]):
        raise StoryError("This story needs a word-like misunderstanding, so that twist would not work.")
    combos = [c for c in valid_combos()
              if (args.twist is None or c[0] == args.twist)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    twist, item = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(BOY_NAMES if child_gender == "boy" else GIRL_NAMES)
    adult_gender = args.adult_gender or rng.choice(list(ADULT_NAMES))
    adult_name = args.adult_name or adult_gender
    return StoryParams(twist, item, child_name, child_gender, adult_name, adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale bedtime story for a 3-to-5-year-old that includes "{f["item"].label}" and the word "slumber".',
        f"Tell a gentle story where {f['child'].id} misunderstands {f['item'].label}, then a grown-up explains it and the mystery turns into a bedtime laugh.",
        f'Write a story with a misunderstanding and a twist that shows how a synonym can sound big but turn out simple.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, item = f["child"], f["adult"], f["item"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {adult.id}, who stayed awake just long enough to solve a word puzzle."),
        (f"What word confused {child.id}?",
         f"{child.id} got confused by the word {item.label}, because it sounded like something that might be caught or found."),
        ("How did the misunderstanding end?",
         f"The grown-up explained the meaning, the twist made the child laugh, and the night settled into slumber."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is slumber?",
         "Slumber means sleep. It is a calm word people sometimes use in a story or a poem."),
        ("What is a synonym?",
         "A synonym is a word that means the same or almost the same as another word."),
        ("Why do stories use a twist?",
         "A twist surprises the reader and changes what we expect, which can make a story fun and memorable."),
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, I) :- twist(T), item(I), reasonable(T, I).
reasonable(T, I) :- twist(T), item(I), wordlike(I), nightlike(T).
outcome(settled) :- valid(_, _).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("wordlike", iid))
    for tid in TWISTS:
        lines.append(asp.fact("nightlike", tid))
    lines.append(asp.fact("reasonable", "misunderstanding", "synonym"))
    lines.append(asp.fact("reasonable", "twist", "slumber"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos:")
        if cl - py:
            print(" only in ASP:", sorted(cl - py))
        if py - cl:
            print(" only in Python:", sorted(py - cl))
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: default generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(TWISTS[params.twist], ITEMS[params.item], params.child_name, params.child_gender, params.adult_name, params.adult_gender)
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


CURATED = [
    StoryParams("misunderstanding", "synonym", "Milo", "boy", "Grandma", "grandmother"),
    StoryParams("twist", "slumber", "Mina", "girl", "Grandpa", "grandfather"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, i in asp_valid_combos():
            print(f"  {t:16} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
