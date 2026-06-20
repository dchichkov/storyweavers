#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/leash_whir_polly_flashback_humor_tall_tale.py
=============================================================================

A standalone storyworld built from the seed words **leash**, **whir**, and
**polly**, with a **flashback** beat, some gentle **humor**, and a **tall tale**
tone.

The tiny domain:
- a child, a talkative grown-up, and a dog named Polly
- a leash that gets tangled or whisked along
- a funny little mishap that starts as a boast and ends as a safer plan
- a flashback to an earlier lesson that explains why the grown-up was cautious

The story model is state-driven:
- physical meters track tangles, speed, noise, and a tiny bit of chaos
- emotional memes track pride, worry, laughter, relief, and trust
- the ending image proves what changed: the leash is fixed, Polly is calm,
  and the child has learned something useful without losing the fun

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/leash_whir_polly_flashback_humor_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/leash_whir_polly_flashback_humor_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/leash_whir_polly_flashback_humor_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/leash_whir_polly_flashback_humor_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/leash_whir_polly_flashback_humor_tall_tale.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BOAST_MIN = 2.0


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spook(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["tangle"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("Polly").memes["worry"] += 1
        world.get("Child").memes["humor"] += 1
        out.append("__spook__")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook)]


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


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    grownup_name: str
    grownup_gender: str
    dog_name: str
    leash_kind: str
    place: str
    flashback_kind: str
    seed: Optional[int] = None


CHILD_NAMES = ["Mina", "June", "Toby", "Wren", "Pip", "Elsie", "Nate", "Lila"]
ADULT_NAMES = ["Aunt Dot", "Uncle Ben", "Mom", "Dad", "Gramma"]
DOG_NAMES = ["Polly", "Poppy", "Muffin", "Scout"]
LEASH_KINDS = ["blue leash", "red leash", "rope leash", "long leash"]
PLACES = ["the county fair", "the river lane", "the windy hill", "the barnyard road", "the little parade"]
FLASHBACKS = ["the first walk", "the muddy puddle day", "the time the leash slipped", "the squirrel chase"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about leash, whir, Polly, flashback, and humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--leash", dest="leash_kind", choices=LEASH_KINDS)
    ap.add_argument("--dog", dest="dog_name", choices=DOG_NAMES)
    ap.add_argument("--child", dest="child_name")
    ap.add_argument("--adult", dest="grownup_name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, l, d) for p in PLACES for l in LEASH_KINDS for d in DOG_NAMES]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for l in LEASH_KINDS:
        lines.append(asp.fact("leash", l))
    for d in DOG_NAMES:
        lines.append(asp.fact("dog", d))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,L,D) :- place(P), leash(L), dog(D).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id="Child", kind="character", type=params.child_gender, label=params.child_name, role="child", traits=["bold"]))
    adult = w.add(Entity(id="Adult", kind="character", type=params.grownup_gender, label=params.grownup_name, role="adult"))
    dog = w.add(Entity(id="Polly", kind="character", type="dog", label=params.dog_name, role="dog"))
    leash = w.add(Entity(id="Leash", label=params.leash_kind, role="tool"))

    child.memes["pride"] = 3
    child.memes["joy"] = 1
    adult.memes["worry"] = 1
    dog.memes["trust"] = 1

    w.say(
        f"At {params.place}, {child.label} strutted along like a mayor on parade, "
        f"with Polly trotting by on a {params.leash_kind} and the day shining like a brass bell."
    )
    w.say(
        f'"Look here!" {child.label} boasted. "I can lead Polly and make the leash sing whir-whir-whir!"'
    )

    w.para()
    child.meters["speed"] += 1
    leash.meters["spin"] += 1
    leash.meters["whir"] += 1
    w.say(
        f"Then the wind came in with a cape on its shoulders, and the leash went whir as it looped around {child.label}'s wrist."
    )
    w.say(
        f"Polly gave a funny little hop, as if she had become a circus pony in a very small and very serious show."
    )
    child.meters["tangle"] += 1
    dog.memes["alarm"] += 1
    propagate(w, narrate=False)

    w.para()
    w.say(
        f"{adult.label_word.capitalize()} blinked twice, then laughed so hard {adult.pronoun()} nearly lost {adult.pronoun('possessive')} hat."
    )
    w.say(
        f'"Hold there," {adult.label} said. "This reminds me of {params.flashback_kind}..."'
    )
    w.say(
        f"And right there came the flashback: {adult.label} once let a leash wrap the porch rail, and Polly had twirled in a grand, foolish circle until everybody was laughing and nobody was moving.'
    )

    w.para()
    child.memes["humor"] += 1
    child.memes["worry"] += 1
    adult.memes["care"] += 1
    w.say(
        f"{child.label} untwisted the loop, one careful inch at a time, while Polly sat as solemn as a potato in church."
    )
    w.say(
        f'Then {adult.label} clipped the leash shorter, and together they walked on with the wind at their backs and Polly making a cheerful little trot.'
    )
    w.say(
        f"By the end, the leash was straight again, Polly's tail was waving like a flag, and the whole tall tale ended with a grin instead of a tug."
    )

    w.facts.update(child=child, adult=adult, dog=dog, leash=leash, params=params, outcome="safe")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a tall-tale story for a young child that includes the words "leash", "whir", and "Polly".',
        f"Tell a funny flashback story where {p.child_name} and Polly go for a walk at {p.place}, the leash whirs in the wind, and a grown-up remembers an old lesson.",
        f'Write a humorous story with a flashback, a dog named Polly, and a leash that ends with everyone safe and smiling.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p: StoryParams = f["params"]
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    return [
        ("Who is the story about?",
         f"It is about {p.child_name}, Polly, and {adult.label}. The child learns how to handle the leash safely."),
        ("What happened when the wind picked up?",
         f"The leash went whir and wrapped around {p.child_name}'s wrist. That made the walk silly for a moment, but it also showed why moving carefully matters."),
        ("What did the grown-up remember?",
         f"{adult.label} remembered {p.flashback_kind}. In that flashback, a leash had wrapped up before, so the grown-up knew to slow down and fix it before it got worse."),
        ("How did the story end?",
         f"Everyone walked on safely. The leash was straight again, Polly was calm, and the day ended with laughter instead of trouble."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a leash?",
         "A leash is a strap or rope that helps a person keep a pet close on a walk."),
        ("Why can wind make things whir?",
         "When wind moves through a loose thing, it can make a whirring sound as it spins or flutters."),
        ("Why do people use flashbacks in stories?",
         "A flashback shows something that happened earlier, so the story can explain a memory or an old lesson."),
        ("What makes humor in a story?",
         "Humor comes from funny surprise, silly timing, or a small mishap that stays harmless."),
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
    return "\n".join(lines)


CURATED = [
    StoryParams("the county fair", "blue leash", "Polly", "Mina", "girl", "Mom", "mother", "muddy road"),
    StoryParams("the windy hill", "rope leash", "Polly", "Toby", "boy", "Dad", "father", "squirrel chase"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.leash_kind and args.leash_kind not in LEASH_KINDS:
        raise StoryError("Unknown leash choice.")
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    child_gender = "girl" if child_name in {"Mina", "June", "Wren", "Pip", "Elsie", "Lila"} else "boy"
    grownup_name = args.grownup_name or rng.choice(ADULT_NAMES)
    grownup_gender = "mother" if grownup_name in {"Mom", "Aunt Dot", "Gramma"} else "father"
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        grownup_name=grownup_name,
        grownup_gender=grownup_gender,
        dog_name=args.dog_name or "Polly",
        leash_kind=args.leash_kind or rng.choice(LEASH_KINDS),
        place=args.place or rng.choice(PLACES),
        flashback_kind=rng.choice(FLASHBACKS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH in valid combos")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity and smoke test passed ({len(clingo_set)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, l, d in combos[:50]:
            print(f"  {p:18} {l:12} {d}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
