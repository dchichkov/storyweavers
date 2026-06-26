#!/usr/bin/env python3
"""
storyworlds/worlds/palette_misunderstanding_folk_tale.py
=========================================================

A small folk-tale story world about a magical palette, a misunderstanding,
and a gentle clearing-up of the trouble.

The tale premise:
- A young painter finds a bright palette.
- A villager misunderstands the colors and thinks they mean something else.
- The misunderstanding spreads through the village.
- A wiser helper notices the real cause and makes a kind fix.

This world simulates both physical state (meters) and emotional state (memes),
then narrates from that state rather than swapping nouns in a fixed paragraph.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"color": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "wonder": 0.0, "worry": 0.0, "misunderstanding": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class PaletteChoice:
    colors: list[str]
    meaning: str
    glow: str
    trigger: str
    fix: str


@dataclass
class StoryParams:
    name: str
    gender: str
    elder: str
    village: str
    palette: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


PALETTES = {
    "sunrise": PaletteChoice(
        colors=["gold", "rose", "amber"],
        meaning="a promise of morning work and new bread",
        glow="bright as a kettle on the fire",
        trigger="the baker would not sell the bread",
        fix="the baker only needed to see the true sunrise sign",
    ),
    "forest": PaletteChoice(
        colors=["green", "brown", "moss"],
        meaning="a blessing for trees, roots, and safe paths",
        glow="soft as fern leaves after rain",
        trigger="the woodcutter feared the woods were angry",
        fix="the woodcutter only needed to hear the old tree song",
    ),
    "harvest": PaletteChoice(
        colors=["wheat", "red", "copper"],
        meaning="a wish for full baskets and kind neighbors",
        glow="warm as a loaf just taken from the oven",
        trigger="the miller thought the village was being warned of famine",
        fix="the miller only needed to see the basket hidden in the cart",
    ),
    "river": PaletteChoice(
        colors=["blue", "silver", "white"],
        meaning="a charm for safe crossings and clear water",
        glow="clear as moonlight on a shallow stream",
        trigger="the ferryman thought the river spirit was displeased",
        fix="the ferryman only needed to see the painted stone at the bank",
    ),
}

VILLAGES = ["Ashford", "Willowmere", "Briar Glen", "Holly Cross", "Stonebrook"]
ELDERS = ["baker", "woodcutter", "miller", "ferryman"]
GENDERS = ["girl", "boy"]
NAMES = {
    "girl": ["Mina", "Tessa", "Lina", "Suri", "Nia"],
    "boy": ["Oren", "Pavel", "Tomas", "Eli", "Marek"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about a palette misunderstanding.")
    ap.add_argument("--name", choices=sum([v for v in NAMES.values()], []))
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--palette", choices=PALETTES)
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
    palette = args.palette or rng.choice(sorted(PALETTES))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    elder = args.elder or rng.choice(ELDERS)
    village = args.village or rng.choice(VILLAGES)
    return StoryParams(name=name, gender=gender, elder=elder, village=village, palette=palette)


def _build_world(params: StoryParams) -> World:
    world = World()
    choice = PALETTES[params.palette]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=f"the {params.elder}"))
    palette = world.add(Entity(
        id="palette",
        kind="thing",
        type="palette",
        label="palette",
        phrase=f"a painted palette of {', '.join(choice.colors)}",
        owner=hero.id,
        carried_by=hero.id,
    ))
    sign = world.add(Entity(id="sign", kind="thing", type="sign", label="sign"))
    world.facts = {
        "hero": hero,
        "elder": elder,
        "palette": palette,
        "choice": choice,
        "village": params.village,
    }

    hero.memes["wonder"] += 1
    world.say(
        f"In the village of {params.village}, {hero.id} was a little {params.gender} who loved bright things and old stories."
    )
    world.say(
        f"One morning, {hero.id} found {choice.glow} a {palette.phrase} tucked beside the road."
    )
    world.say(
        f"{hero.id} held the palette close, because the colors seemed to carry {choice.meaning}."
    )

    world.para()
    hero.memes["joy"] += 1
    hero.meters["color"] += 1
    world.say(
        f"{hero.id} painted a tiny mark on a wooden sign by the lane, and the color shone like a folk charm."
    )
    world.say(
        f"Then {params.elder} saw the mark and frowned, for {choice.trigger}."
    )
    elder.memes["worry"] += 1
    elder.memes["misunderstanding"] += 1
    world.say(
        f"At once, the elder told the neighbors a worried tale, and the village grew quiet with the wrong idea."
    )

    world.para()
    hero.memes["misunderstanding"] += 1
    world.say(
        f"{hero.id} heard the whispers and felt the trouble in the air."
    )
    world.say(
        f"Still, {hero.id} came to the square with the palette held high and said, "
        f'"This is not a warning. It is only a kind sign for the harvest road."'
    )
    world.say(
        f"The elder looked again and understood that {choice.fix}."
    )
    elder.memes["relief"] += 1
    elder.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["misunderstanding"] = 0.0
    world.say(
        f"So the elder laughed, the neighbors laughed too, and the palette was hung above the lane like a bright little blessing."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    choice = f["choice"]
    village = f["village"]
    return [
        f'Write a folk-tale style story for a child in which a colorful palette causes a misunderstanding in {village}.',
        f"Tell a gentle story about {hero.id} and a magical palette, where an elder first misunderstands the colors and then learns the truth.",
        f'Write a simple village story that includes the word "palette" and ends with everyone understanding the sign correctly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    choice = f["choice"]
    village = f["village"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the palette?",
            answer=f"{hero.id} found the palette in the village of {village}, beside the road on a quiet morning.",
        ),
        QAItem(
            question=f"Why did the {elder.type} first worry about the painted sign?",
            answer=f"The {elder.type} first worried because the bright color looked like {choice.trigger}, so the elder misunderstood the sign.",
        ),
        QAItem(
            question="What happened when the truth was explained?",
            answer=f"When {hero.id} explained the palette, the elder understood that the colors meant {choice.meaning}, and everyone grew calm and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    choice = f["choice"]
    return [
        QAItem(
            question="What is a palette?",
            answer="A palette is a board or tray where colors are held together for painting.",
        ),
        QAItem(
            question="Why can colors confuse people in a folk tale?",
            answer="In a folk tale, people may not know the real meaning of a sign or color at first, so they can misunderstand it until someone explains.",
        ),
        QAItem(
            question="What does relief mean?",
            answer="Relief is the happy feeling people get when worry goes away and they know everything is safe again.",
        ),
        QAItem(
            question="What are the colors on this story's palette for?",
            answer=f"They are part of a sign of meaning and hope: {choice.meaning}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is compatible when it has a palette, an elder, and a misunderstanding
% that can be resolved by explanation.
needs_palette(P) :- palette(P).
has_misunderstanding(E) :- elder(E), misunderstanding(E).
resolves(P, E) :- needs_palette(P), has_misunderstanding(E).
valid_story(P) :- palette(P), resolves(P, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PALETTES:
        lines.append(asp.fact("palette", pid))
    for e in ELDERS:
        lines.append(asp.fact("elder", e))
        lines.append(asp.fact("misunderstanding", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p,) for p in PALETTES)
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry ({len(py_set)} palettes).")
        return 0
    print("MISMATCH between clingo and Python registries:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
    StoryParams(name="Mina", gender="girl", elder="baker", village="Ashford", palette="sunrise"),
    StoryParams(name="Oren", gender="boy", elder="woodcutter", village="Willowmere", palette="forest"),
    StoryParams(name="Lina", gender="girl", elder="miller", village="Briar Glen", palette="harvest"),
    StoryParams(name="Tomas", gender="boy", elder="ferryman", village="Stonebrook", palette="river"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world about a palette misunderstanding.")
    ap.add_argument("--name", choices=sorted({n for names in NAMES.values() for n in names}))
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--palette", choices=sorted(PALETTES))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible palettes:\n")
        for (p,) in vals:
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.palette} palette in {p.village}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
