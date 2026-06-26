#!/usr/bin/env python3
"""
A standalone storyworld for a tiny rhyming tale about yoghurt, letters, and
playful sound effects.

Seed idea:
- A child has a yogurt snack and some alphabet letters.
- They want to sort, spell, and sing with the letters.
- The yogurt makes a little mess, but an easy fix keeps the rhyme going.

This world keeps the state small and concrete:
- a child
- a bowl of yoghurt
- letter tiles
- optional spoon / napkin / tray
- emotional state: delight, frustration, pride
- physical state: yogurt spills, letters arranged, snack finished

The story always has:
1) a beginning with a sweet, alphabetic setup
2) a small problem caused by a spill or jumble
3) a rhythmic turn with sound effects and a simple fix
4) an ending image showing the changed state
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class ItemDef:
    id: str
    label: str
    phrase: str
    mess_on_spill: str
    sound: str
    rhyme: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child_type: str
    name: str
    adult_type: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting("the kitchen", indoors=True),
    "playroom": Setting("the playroom", indoors=True),
    "table": Setting("the little table", indoors=True),
}

ITEMS = {
    "letters": ItemDef(
        id="letters",
        label="alphabet tiles",
        phrase="bright alphabet tiles",
        mess_on_spill="sticky",
        sound="clack-clack",
        rhyme="A, B, C",
        fix="lined them up in a neat row",
        tags={"alphabetic", "letters", "rhyme"},
    ),
    "yoghurt": ItemDef(
        id="yoghurt",
        label="yoghurt",
        phrase="a cup of yoghurt",
        mess_on_spill="splatty",
        sound="splish-splash",
        rhyme="slurp and chirp",
        fix="wiped the drip with a napkin",
        tags={"yoghurt", "snack"},
    ),
}

GENDERED = {
    "girl": ["Mia", "Lily", "Zoe", "Ava", "Nina"],
    "boy": ["Leo", "Noah", "Max", "Finn", "Owen"],
}

ADULTS = {"mother": "mom", "father": "dad"}

TRAITS = ["cheerful", "curious", "bouncy", "gentle", "bright"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about yoghurt and alphabetic fun.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--item", choices=ITEMS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, item) for place in SETTINGS for item in ITEMS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.place:
        if (args.place, args.item) not in valid_combos():
            raise StoryError("That place and item do not make a sensible rhyming story.")
    place = args.place or rng.choice(list(SETTINGS))
    item = args.item or rng.choice(list(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDERED[gender])
    adult = args.adult or rng.choice(list(ADULTS))
    return StoryParams(place=place, child_type=gender, name=name, adult_type=adult, item=item)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b} in a merry little spree."


def sound_line(sound: str) -> str:
    return f"{sound}! went the snack, with a soft little smack."


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.child_type))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult_type, label=ADULTS[params.adult_type]))
    item = ITEMS[params.item]
    yoghurt = world.add(Entity(id="yoghurt", label="yoghurt", phrase=item.phrase, owner=child.id))
    letters = world.add(Entity(id="letters", label="letters", phrase="alphabet tiles", owner=child.id))
    napkin = world.add(Entity(id="napkin", label="napkin", phrase="a soft napkin", owner=adult.id))
    tray = world.add(Entity(id="tray", label="tray", phrase="a little tray", owner=adult.id))

    child.memes["delight"] = 1
    letters.meters["order"] = 0
    yoghurt.meters["full"] = 1
    yoghurt.meters["spill"] = 0

    world.say(f"{child.id} sat at {world.setting.place} with {item.phrase}.")
    world.say(f"{sound_line(item.sound)} {child.id} grinned at the alphabetic scene.")
    world.say(f"{child.id} tapped the tiles and sang, \"{item.rhyme}, let's all go free!\"")

    world.para()
    child.memes["curiosity"] = 1
    world.say(f"{child.id} wanted to spell a tiny word, but the cup wobbled with a sly little sway.")
    world.say(f"Tip-tip, plip-plip — the yoghurt made a tiny {item.sound} as it slid from the tray.")
    yoghurt.meters["spill"] = 1
    yoghurt.memes["messy"] = 1
    letters.meters["order"] = 0.2
    child.memes["frustration"] = 1
    world.say(f"The letters got sticky, and the neat row turned jumbly and gray.")

    world.para()
    world.say(f"{adult.label.capitalize()} came close and smiled, not stern but sweet.")
    world.say(f"\"A napkin for the drips, and a tray for the trip,\" {adult.label} said, with a rhyming beat.")
    world.say(f"{napkin.label.capitalize()} wiped the splash; {tray.label} caught the rest.")
    yoghurt.meters["spill"] = 0
    yoghurt.memes["messy"] = 0
    letters.meters["order"] = 1
    child.memes["frustration"] = 0
    child.memes["pride"] = 1
    world.say(f"Then {child.id} lined the letters up again, click-clack, nice and neat.")

    world.para()
    world.say(f"{child.id} spelled a tiny word and clapped in glee.")
    world.say(f"The yoghurt stayed quiet, the tiles stood bright, and the whole room felt like a song to see.")
    world.say(f"{child.id} and {adult.label} smiled side by side, and the alphabet ended happily.")

    world.facts.update(
        child=child,
        adult=adult,
        yoghurt=yoghurt,
        letters=letters,
        napkin=napkin,
        tray=tray,
        item=item,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    item = f["item"]
    return [
        f'Write a short rhyming story for a young child about {child.id}, {item.label}, and alphabet letters.',
        f"Tell a gentle story where {child.id} enjoys {item.phrase} but needs help when the snack gets messy.",
        f'Write a simple story with sound effects like "{item.sound}" and a happy ending about letters and yoghurt.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    item = f["item"]
    return [
        QAItem(
            question=f"What did {child.id} have at the start of the story?",
            answer=f"{child.id} had {item.phrase} and alphabet tiles at {world.setting.place}.",
        ),
        QAItem(
            question=f"What sound did the yoghurt story make when the snack wobbled?",
            answer=f"It made a little {item.sound} sound, like a playful snacky splash.",
        ),
        QAItem(
            question=f"Who helped when the letters got sticky?",
            answer=f"{adult.label.capitalize()} helped with a napkin and a tray, so the mess could be cleaned up kindly.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The letters were lined up neatly again, the yoghurt spill was gone, and the child felt proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is yoghurt?",
            answer="Yoghurt is a soft, creamy food that can be eaten with a spoon.",
        ),
        QAItem(
            question="What are alphabet letters for?",
            answer="Alphabet letters help us read, spell words, and play word games.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like jam and ham.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are playful words that help readers hear the action, like clack-clack or splish-splash.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(kitchen).
place(playroom).
place(table).

item(yoghurt).
item(letters).

compatible(P, I) :- place(P), item(I).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for item in ITEMS:
                p = StoryParams(
                    place=place,
                    child_type="girl",
                    name="Mia",
                    adult_type="mother",
                    item=item,
                )
                samples.append(generate(p))
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
