#!/usr/bin/env python3
"""
A small animal-story world about a gorilla, a cauliflower, and a necessary mystery
to solve with curiosity and humor.

The world is built around a simple premise:
- A gorilla finds a cauliflower that does not belong where it was found.
- Curiosity turns the odd discovery into a mystery to solve.
- The answer to the mystery reveals a practical necessity, and the gorilla helps
  set things right in a funny, gentle way.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

WORLD_NAME = "cauliflower_gorilla_necessity_curiosity_mystery_to_solve"

SPOT_IDS = ("garden", "market", "path", "truck", "shed")
MOOD_WORDS = ("curious", "serious", "hopeful", "amused")
HUMOR_BEATS = (
    "looked like a tiny cloud with a green hat",
    "rolled like a wobbling white ball",
    "sat there as if it had dropped in from a vegetable parade",
)


@dataclass
class Thing:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    place: str = "garden"
    seed: Optional[int] = None


@dataclass
class Registry:
    story_place: str
    gorilla_name: str = "Gus"
    helper_name: str = "Mina"
    gorilla_traits: tuple[str, ...] = ("gentle", "curious")
    helper_traits: tuple[str, ...] = ("smart", "patient")
    cauliflower_label: str = "cauliflower"
    mystery_item: str = "missing lunch"


@dataclass
class World:
    params: StoryParams
    registry: Registry
    entities: dict[str, Thing] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, ent: Thing) -> Thing:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Thing:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace_lines(self) -> list[str]:
        lines = ["--- world model state ---"]
        for ent in self.entities.values():
            bits = []
            if ent.location:
                bits.append(f"location={ent.location}")
            if ent.owner:
                bits.append(f"owner={ent.owner}")
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            lines.append(f"  {ent.id:10} ({ent.kind:8}) {' '.join(bits)}")
        lines.append(f"  fired rules: {sorted(self.fired)}")
        return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: curiosity, a mystery to solve, and a necessary cauliflower."
    )
    ap.add_argument("--place", choices=SPOT_IDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(SPOT_IDS)
    return StoryParams(place=place)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", p) for p in SPOT_IDS]
    lines.append(asp.fact("animal", "gorilla"))
    lines.append(asp.fact("object", "cauliflower"))
    lines.append(asp.fact("theme", "curiosity"))
    lines.append(asp.fact("theme", "mystery_to_solve"))
    lines.append(asp.fact("theme", "humor"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
story_theme(curiosity).
story_theme(mystery_to_solve).
story_theme(humor).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    got = sorted(set(asp.atoms(model, "valid_place")))
    expected = [(p,) for p in SPOT_IDS]
    if got == expected:
        print(f"OK: clingo gate matches registry ({len(got)} places).")
        return 0
    print("MISMATCH between clingo and python registry.")
    print("  clingo:", got)
    print("  python:", expected)
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SPOT_IDS:
        raise StoryError(f"Unknown place: {params.place}")


def generate_story_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    reg = Registry(story_place=params.place)
    w = World(params=params, registry=reg)

    gorilla = w.add(Thing(
        id="gorilla",
        kind="character",
        label=reg.gorilla_name,
        meters={"strength": 3.0},
        memes={"curiosity": 1.0},
        location=params.place,
    ))
    helper = w.add(Thing(
        id="helper",
        kind="character",
        label=reg.helper_name,
        meters={"strength": 1.0},
        memes={"humor": 1.0, "patience": 1.0},
        location=params.place,
    ))
    cauliflower = w.add(Thing(
        id="cauliflower",
        kind="object",
        label="cauliflower",
        meters={"freshness": 1.0, "weight": 1.0},
        location=params.place,
        owner=None,
    ))
    crate = w.add(Thing(
        id="crate",
        kind="object",
        label="wooden crate",
        meters={"capacity": 1.0},
        location=params.place,
    ))
    w.facts.update(gorilla=gorilla, helper=helper, cauliflower=cauliflower, crate=crate)
    return w


def act_find(w: World) -> None:
    g = w.get("gorilla")
    c = w.get("cauliflower")
    g.bump_meme("curiosity", 1.0)
    c.location = w.params.place
    w.say(
        f"{g.label} the gorilla found a cauliflower in the {w.params.place}, "
        f"and it {random.choice(HUMOR_BEATS)}."
    )


def act_mystery(w: World) -> None:
    g = w.get("gorilla")
    g.bump_meme("mystery", 1.0)
    w.say(
        f"{g.label} scratched his head. Why would a cauliflower be here? "
        f"It was a mystery to solve."
    )


def act_investigate(w: World) -> None:
    g = w.get("gorilla")
    h = w.get("helper")
    c = w.get("cauliflower")
    g.bump_meme("curiosity", 1.0)
    h.bump_meme("humor", 1.0)
    w.say(
        f"{g.label} and {h.label} looked for clues. They checked the path, "
        f"the shed, and the little cart nearby."
    )
    w.say(
        f"{h.label} laughed and said, 'Maybe the cauliflower wanted a new job!' "
        f"but {g.label} kept looking."
    )
    w.facts["clues"] = ["cart", "shed", "path"]
    w.facts["cauliflower"] = c


def act_discover_necessity(w: World) -> None:
    g = w.get("gorilla")
    h = w.get("helper")
    c = w.get("cauliflower")
    g.bump_meme("understanding", 1.0)
    w.say(
        f"At last, they found the answer: the cauliflower had been taken out "
        f"so it could be washed and sent to the kitchen on time."
    )
    w.say(
        f"It was a necessity, not a trick. {g.label} nodded, and {h.label} smiled "
        f"because the mystery finally made sense."
    )
    c.owner = "kitchen"
    c.location = "basket"
    w.facts["necessity"] = True


def act_resolve(w: World) -> None:
    g = w.get("gorilla")
    h = w.get("helper")
    c = w.get("cauliflower")
    g.bump_meme("joy", 1.0)
    g.bump_meme("humor", 1.0)
    w.say(
        f"{g.label} carried the cauliflower to the basket with careful hands, "
        f"and {h.label} gave it a proud little salute."
    )
    w.say(
        f"Then they both laughed, because the cauliflower still looked like a "
        f"tiny cloud that had learned how to behave."
    )
    w.say(
        f"By the end, the cauliflower was safe, the job was done, and the gorilla "
        f"had turned a curious problem into a happy answer."
    )
    w.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    w = generate_story_world(params)
    act_find(w)
    w.para()
    act_mystery(w)
    act_investigate(w)
    w.para()
    act_discover_necessity(w)
    act_resolve(w)
    return w


def generation_prompts(world: World) -> list[str]:
    place = world.params.place
    return [
        f"Write a short animal story about a gorilla, a cauliflower, and a mystery in the {place}.",
        "Tell a gentle story where curiosity leads to a mystery to solve and the answer is a necessity.",
        "Write a humorous story about an animal who finds a cauliflower and learns why it had to be moved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = world.params.place
    g = world.get("gorilla")
    h = world.get("helper")
    return [
        QAItem(
            question=f"What did the gorilla find in the {place}?",
            answer="He found a cauliflower, and it looked very out of place.",
        ),
        QAItem(
            question="Why did the gorilla keep looking for clues?",
            answer="He was curious, and the strange cauliflower made him think it was a mystery to solve.",
        ),
        QAItem(
            question="Why was the cauliflower moved?",
            answer="It was moved because it was a necessity: it needed to be washed and sent to the kitchen on time.",
        ),
        QAItem(
            question=f"Who helped the gorilla solve the mystery?",
            answer=f"{h.label} helped by checking the clues and making a funny remark that kept the search cheerful.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The gorilla carried the cauliflower to the basket, the job was finished, and everyone laughed at the silly-looking vegetable.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cauliflower?",
            answer="A cauliflower is a vegetable with a bumpy white head and green leaves around it.",
        ),
        QAItem(
            question="What does curiosity help animals do?",
            answer="Curiosity helps them notice strange things, ask questions, and learn what is going on.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzling situation that needs clues and careful thinking.",
        ),
        QAItem(
            question="Why can humor help in a problem?",
            answer="Humor can make a problem feel less scary and help friends keep working together.",
        ),
        QAItem(
            question="What is a necessity?",
            answer="A necessity is something that must be done because it is important or needed.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join(world.trace_lines())


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_place/1."))
        places = sorted(set(asp.atoms(model, "valid_place")))
        print(f"{len(places)} places:")
        for p in places:
            print(f"  {p[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SPOT_IDS:
            params = StoryParams(place=place, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
