#!/usr/bin/env python3
"""
A small rhyming storyworld about a bike ride, a false alarm, and a funny inner
monologue. The seed words guide the domain: bike, false, and a single startled
"fuck" only as a hidden internal exclamation in the world model, never in child-
facing prose.

This world keeps the simulation tiny:
- one child and one helper
- one bike with a false-sounding problem
- one repair choice that resolves the worry
- inner monologue and humor woven into the narration
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

RHYME_PAIRS = [
    ("glow", "show"),
    ("light", "bright"),
    ("mend", "friend"),
    ("wheel", "peel"),
    ("spin", "grin"),
    ("ride", "slide"),
    ("bell", "well"),
    ("track", "back"),
]

NAMES = ["Milo", "Nina", "Tess", "Owen", "Pia", "Rico", "Lena", "Benny"]
ADJECTIVES = ["spry", "brave", "happy", "curious", "bouncy", "tiny", "cheery"]
HELPERS = ["parent", "grandparent", "neighbor", "big sister", "big brother"]
PLACES = ["the sidewalk", "the park path", "the driveway", "the little lane"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    place: str
    child: Entity
    helper: Entity
    bike: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    helper: str
    place: str
    adjective: str
    seed: Optional[int] = None


def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def build_rhyme_line(a: str, b: str) -> str:
    return f"{a} / {b}"


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name:
        raise StoryError("The child needs a name.")
    if not params.place:
        raise StoryError("The story needs a place.")
    if params.helper not in HELPERS:
        raise StoryError("The helper choice is not supported.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming bike storyworld with humor and inner monologue.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--adjective", choices=ADJECTIVES)
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
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    place = args.place or rng.choice(PLACES)
    adjective = args.adjective or rng.choice(ADJECTIVES)
    params = StoryParams(name=name, helper=helper, place=place, adjective=adjective)
    reasonableness_gate(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity(id=params.name, kind="character", label=params.name, phrase=f"a {params.adjective} child")
    helper = Entity(id=params.helper, kind="character", label=params.helper, phrase=f"the {params.helper}")
    bike = Entity(id="bike", kind="thing", label="bike", phrase="a little red bike")
    bike.meters = {"tire_air": 1.0, "wheel_spin": 1.0}
    bike.memes = {"trust": 1.0, "false_alarm": 0.0, "repair_need": 0.0}
    return World(place=params.place, child=child, helper=helper, bike=bike)


def rhyme_story(world: World) -> None:
    c = world.child
    h = world.helper
    b = world.bike

    world.say(f"{c.label} had a bike with a shiny little bell,")
    world.say(f"and loved to ride it fast, with a grin that did quite well.")
    world.say(f"One day at {world.place}, the wheel gave a tiny squeal,")
    world.say(f"and {c.label} thought, in a hush, 'Oh no... that sound feels real.'")

    world.para()
    world.say(f"Inside {c.label}'s head, a funny thought began to race:")
    world.say(f"'Is the bike broken? Is this my unlucky place?'")
    world.say(f"Then came a second thought, more careful, small, and slow:")
    world.say(f"'Maybe it's just a pebble. Maybe it's a false alarm, you know.'")

    b.inc_meme("false_alarm", 1.0)
    b.inc_meme("repair_need", 0.25)
    c.inc_meme("worry", 1.0)
    c.inc_meme("humor", 1.0)

    world.para()
    world.say(f"{h.label.capitalize()} knelt down and listened with a grin,")
    world.say(f"then tapped the tire softly to hear the little spin.")
    world.say(f'"It sounds more like a pebble than a dramatic doom,"')
    world.say(f"{h.label} said, and chuckled with a tiny boom of room.")

    world.say(f"{c.label} blinked and felt the worry start to thin:")
    world.say(f"'Phew,' thought {c.label}, 'my brain was loud again.'")

    b.inc_meter("wheel_spin", 0.5)
    b.inc_meter("repair_need", 0.0)

    world.para()
    world.say(f"{h.label} plucked a pebble from the tread with care,")
    world.say(f"and {c.label} laughed, because it was stuck right there.")
    world.say(f"The bike went rolling, round and bright, just like a song,")
    world.say(f"and all the false alarm got small and then was gone.")

    c.inc_meme("joy", 1.0)
    c.inc_meme("relief", 1.0)
    b.inc_meme("trust", 0.5)

    world.facts.update(
        setting=world.place,
        child=c,
        helper=h,
        bike=b,
        false_alarm=True,
        pebble=True,
        rhyme="bike/false/light",
        inner_monologue=True,
        humor=True,
    )


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    return [
        "Write a short rhyming story for a child about a bike that makes a funny false alarm.",
        f"Tell a gentle story where {c.label} thinks the bike is broken, but the worry turns out to be false.",
        "Make the child’s inner monologue playful, and end with the bike rolling again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    place = world.facts["setting"]
    return [
        QAItem(
            question=f"What did {c.label} think was wrong with the bike at first?",
            answer="At first, the child thought the bike had a serious problem, but that worry was a false alarm.",
        ),
        QAItem(
            question=f"Who helped check the bike at {place}?",
            answer=f"The {h.label} helped check the bike and listen to the wheel.",
        ),
        QAItem(
            question="What fixed the problem?",
            answer="A small pebble caught in the tire was removed, so the bike could roll again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bike for?",
            answer="A bike is for riding, pedaling, and having fun moving along a path or road.",
        ),
        QAItem(
            question="What does false alarm mean?",
            answer="A false alarm means something seemed serious at first, but it turned out not to be a real problem.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet talking a character does inside their own head.",
        ),
        QAItem(
            question="Why can a small pebble make a bike sound strange?",
            answer="A pebble can rub or tap the tire, which can make a bike squeak or sound funny while rolling.",
        ),
    ]


ASP_RULES = r"""
false_alarm(bike) :- pebble_in_tire(bike), wheel_squeak(bike).
resolved(bike) :- false_alarm(bike), pebble_removed(bike).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("bike", "bike"),
        asp.fact("pebble_in_tire", "bike"),
        asp.fact("wheel_squeak", "bike"),
        asp.fact("helper", "helper"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show false_alarm/1.\n#show resolved/1."))
    atoms = sorted(set((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model))
    expected = [("false_alarm", ("bike",))]
    if atoms == expected:
        print("OK: ASP gate matches the Python story model.")
        return 0
    print("MISMATCH:", atoms, "!=", expected)
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.child, world.helper, world.bike]:
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    rhyme_story(world)
    story = normalize_text(world.render())
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(name="Milo", helper="parent", place="the sidewalk", adjective="bouncy"),
    StoryParams(name="Nina", helper="grandparent", place="the park path", adjective="curious"),
    StoryParams(name="Tess", helper="big sister", place="the driveway", adjective="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show false_alarm/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world uses a tiny ASP twin; use --show-asp to inspect it.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
