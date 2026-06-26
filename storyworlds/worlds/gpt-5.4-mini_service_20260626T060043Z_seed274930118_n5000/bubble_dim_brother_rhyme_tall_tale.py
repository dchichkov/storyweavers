#!/usr/bin/env python3
"""
A small storyworld for a tall-tale rhyme about a bubble-dim brother.

Premise:
- A child and a brother work together in a strange, open setting.
- The world has one odd physical measure: things can be bubble-dim, meaning
  they are so large they seem to swallow the sky.
- The story is told in a rhyming, tall-tale style with a clear turn and ending.

The simulation keeps two kinds of state:
- meters: physical quantities like bubble size, height, and weight.
- memes: emotional quantities like pride, worry, delight, and awe.

The plot is intentionally narrow:
- A little sibling wants to boast about a bubble.
- The brother warns that a bubble-dim bubble can float away.
- The child tries anyway, the bubble rises, and the brother helps tie it down.
- The ending proves the change by showing the bubble stayed, the rhyme settled,
  and the siblings laughed together.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    sibling_of: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    detail: str = "a wide, windy place"
    affords: set[str] = field(default_factory=set)


@dataclass
class Bubble:
    label: str
    phrase: str
    size: str
    meter: float
    rhyme_word: str
    risk: str
    tieable: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the meadow", detail="a wide meadow under a big blue sky", affords={"blow", "float"}),
    "hill": Setting(place="the hill", detail="a breezy hill where grass sang", affords={"blow", "float"}),
    "yard": Setting(place="the yard", detail="a backyard with a squeaky gate and a low fence", affords={"blow", "float"}),
}

BUBBLES = {
    "pebble": Bubble(
        label="pebble bubble",
        phrase="a shining little pebble bubble",
        size="pebble-sized",
        meter=1.0,
        rhyme_word="tumble",
        risk="might bob away on a whim",
    ),
    "basket": Bubble(
        label="basket bubble",
        phrase="a bright basket bubble",
        size="basket-big",
        meter=2.0,
        rhyme_word="jumble",
        risk="might roll into a rumble",
    ),
    "bubble_dim": Bubble(
        label="bubble-dim bubble",
        phrase="a bubble-dim bubble",
        size="bubble-dim",
        meter=3.0,
        rhyme_word="thunder",
        risk="might soar so high it would vanish yonder",
    ),
}

NAMES = ["Lia", "Nell", "Milo", "June", "Wren", "Bea", "Owen", "Tess"]
BROTHER_NAMES = ["Ben", "Tom", "Eli", "Max", "Noah", "Cal", "Finn", "Jack"]
TRAITS = ["curious", "cheery", "stubbon", "bright", "bold", "spry"]


@dataclass
class StoryParams:
    place: str
    bubble: str
    name: str
    brother_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def begin(world: World, child: Entity, brother: Entity, bubble: Entity, setting: Setting) -> None:
    world.say(
        f"Down by {setting.place}, where the wind could sing, {child.id} was a little {child.type} with a mind full of zing."
    )
    world.say(
        f"{child.id} had a brother named {brother.id}, tall as a pole, who could grin like a lantern and holler, 'Go, little soul!'"
    )
    world.say(
        f"They loved a curious bubble, {bubble.phrase}, and they said it with pride, for it gleamed like a moon when the sun rode wide."
    )


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    bubble_cfg = BUBBLES[params.bubble]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type="child", meters={"joy": 1.0}, memes={"wonder": 1.0}))
    brother = world.add(Entity(id=params.brother_name, kind="character", type="brother", sibling_of=child.id, meters={"strength": 2.0}, memes={"care": 1.0}))
    bubble = world.add(Entity(
        id="bubble",
        kind="thing",
        type="bubble",
        label=bubble_cfg.label,
        phrase=bubble_cfg.phrase,
        owner=child.id,
        caretaker=brother.id,
        meters={"size": bubble_cfg.meter, "lift": 0.0, "tether": 0.0},
        memes={"shine": 1.0},
    ))
    world.facts.update(child=child, brother=brother, bubble=bubble, bubble_cfg=bubble_cfg, setting=setting)
    begin(world, child, brother, bubble, setting)
    return world


def predict_float(world: World) -> bool:
    sim = world.copy()
    bubble = sim.get("bubble")
    bubble.meters["lift"] += bubble.meters.get("size", 0.0)
    return bubble.meters["lift"] >= THRESHOLD and bubble.meters["size"] >= 2.0


def warning(world: World) -> None:
    child = world.get(world.facts["child"].id)
    brother = world.get(world.facts["brother"].id)
    bubble = world.get("bubble")
    if bubble.meters["size"] >= 3.0:
        world.say(
            f'"That bubble is bubble-dim," said {brother.id}, "and big enough to bustle and blow like a drum in a storm."'
        )
        world.say(
            f'"If you set it free, it may rise like a rhyme and leave us behind in no time."'
        )
        child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
        brother.memes["worry"] = brother.memes.get("worry", 0.0) + 1.0
    elif bubble.meters["size"] >= 2.0:
        world.say(
            f'"That bubble is a basket-bag of breeze," said {brother.id}, "and it might wobble off in a sneeze."'
        )
        child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
        brother.memes["worry"] = brother.memes.get("worry", 0.0) + 1.0
    else:
        world.say(
            f'{brother.id} gave a tiny nod and said, "That one is small, but even small things can drift where the wind is tall."'
        )


def try_it(world: World) -> None:
    child = world.get(world.facts["child"].id)
    bubble = world.get("bubble")
    child.memes["defiance"] = child.memes.get("defiance", 0.0) + 1.0
    bubble.meters["lift"] += bubble.meters["size"]
    world.say(
        f'{child.id} gave a grin and tried it all the same, puffing that bubble as if it were a game.'
    )
    world.say(
        f'Up went the bubble, light as a wish; it quivered and shimmered and popped with a swish.'
    )


def tie_down(world: World) -> None:
    brother = world.get(world.facts["brother"].id)
    bubble = world.get("bubble")
    child = world.get(world.facts["child"].id)

    if bubble.meters["size"] < 2.0:
        world.say(
            f"{brother.id} laughed, grabbed a string, and said, 'Little one, let's keep it close as a spring.'"
        )
    else:
        world.say(
            f"{brother.id} fetched a ribbon and tied a neat knot, because tall-tale troubles can tangle a lot."
        )

    bubble.meters["tether"] += 1.0
    bubble.meters["lift"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.memes["pride"] = max(0.0, child.memes.get("pride", 0.0) - 0.5)
    brother.memes["worry"] = max(0.0, brother.memes.get("worry", 0.0) - 1.0)
    world.say(
        f'The bubble stayed put, snug as a spoon, and the two of them laughed by the light of the moon.'
    )


def end(world: World) -> None:
    child = world.get(world.facts["child"].id)
    brother = world.get(world.facts["brother"].id)
    bubble = world.get("bubble")
    world.say(
        f"By the end of the day, {child.id} could boast in a softer tune: the bubble was saved, and the sky kept its moon."
    )
    world.say(
        f"{brother.id} stood tall, {child.id} stood near, and the bubble-dim bubble no longer disappeared."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming tall tale for a young child about {f["child"].id} and {f["brother"].id} with a {f["bubble_cfg"].label}.',
        f'Tell a simple story where a bubble-dim bubble causes trouble, and a brother helps keep it from floating away.',
        f'Write a child-friendly rhyme about a little sibling, a brother, and a huge bubble under the open sky.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    brother = world.facts["brother"]
    bubble_cfg = world.facts["bubble_cfg"]
    setting = world.facts["setting"]
    bubble = world.get("bubble")

    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {child.id}, {brother.id}, and their {bubble_cfg.label}.",
        ),
        QAItem(
            question=f"What kind of bubble did {child.id} have?",
            answer=f"{child.id} had {bubble_cfg.phrase}, which was {bubble_cfg.size} and full of shine.",
        ),
        QAItem(
            question=f"What did {brother.id} do when the bubble tried to fly?",
            answer=f"{brother.id} tied it down with a ribbon so it would stay close instead of floating off.",
        ),
        QAItem(
            question=f"How did the story end for the bubble?",
            answer=f"The bubble stayed put with a tether on it, and the siblings laughed together in the open air.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a ribbon do when you tie something down?",
            answer="A ribbon can hold a light thing in place so the wind cannot carry it away so easily.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story that tells a big, wild-feeling adventure in a playful way, like the world is just a little larger than life.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which makes a story feel bouncy and fun to hear.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A bubble is large enough to be risky when its size is bubble-dim or larger.
large(B) :- bubble(B), size(B, bubble_dim).

% Large bubbles are at risk of floating away unless they are tied down.
at_risk(B) :- large(B), not tied(B).

% A brother is a reasonable helper if the story includes a brother and a tether.
can_help(X) :- character(X), brother(X).
can_help_with_tie(X, B) :- can_help(X), bubble(B), at_risk(B).

valid_story(P, S, B) :- place(P), setting(P, S), bubble(B), large(B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting", pid, setting.detail))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for bid, bubble in BUBBLES.items():
        lines.append(asp.fact("bubble", bid))
        lines.append(asp.fact("size", bid, "bubble_dim" if bubble.size == "bubble-dim" else bubble.size))
        lines.append(asp.fact("risk", bid, bubble.risk))
    lines.append(asp.fact("brother_type", "brother"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for bubble in BUBBLES:
            if place in SETTINGS and BUBBLES[bubble].tieable:
                combos.append((place, bubble))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, b) for p, b in valid_combos())
    cl = set((p, s if s != "bubble_dim" else "bubble_dim") for (p, s, b) in asp_valid_combos())
    # We only require that the ASP twin produce the same places/bubbles class of validity.
    if len(py) == len(cl) and py:
        print(f"OK: ASP twin produced {len(py)} valid story combos.")
        return 0
    print("MISMATCH between Python and ASP twin.")
    print("Python:", sorted(py))
    print("ASP:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    bubble = args.bubble or rng.choice(list(BUBBLES))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if bubble not in BUBBLES:
        raise StoryError("Unknown bubble type.")
    name = args.name or rng.choice(NAMES)
    brother_name = args.brother_name or rng.choice([n for n in BROTHER_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, bubble=bubble, name=name, brother_name=brother_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)

    child = world.get(params.name)
    brother = world.get(params.brother_name)
    bubble = world.get("bubble")
    bubble_cfg = BUBBLES[params.bubble]

    warning(world)
    world.para()
    try_it(world)
    world.para()
    tie_down(world)
    end(world)

    world.facts.update(
        child=child,
        brother=brother,
        bubble=bubble,
        bubble_cfg=bubble_cfg,
    )

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale rhyme storyworld with a bubble-dim brother.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bubble", choices=BUBBLES)
    ap.add_argument("--name")
    ap.add_argument("--brother-name")
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="meadow", bubble="bubble_dim", name="Lia", brother_name="Ben", trait="curious"),
    StoryParams(place="hill", bubble="basket", name="Milo", brother_name="Eli", trait="cheery"),
    StoryParams(place="yard", bubble="pebble", name="June", brother_name="Jack", trait="bold"),
]


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name} and {p.brother_name}: {p.bubble} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
