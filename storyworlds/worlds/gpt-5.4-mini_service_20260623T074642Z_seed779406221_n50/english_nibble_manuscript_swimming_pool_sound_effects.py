#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/english_nibble_manuscript_swimming_pool_sound_effects.py
===============================================================================================================================

A small bedtime-story world set at a swimming pool.

Seed-inspired ingredients:
- english
- nibble
- manuscript

Narrative instruments:
- Sound Effects
- Cautionary
- Repetition

The domain centers on a child, a tiny swimming pool mishap, a caution, and a
gentle fix that helps the child keep something precious dry and safe.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"wet": 0.0, "dirty": 0.0, "nibble": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "caution": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    gender: str
    parent: str
    trait: str
    item: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str = "the swimming pool"


@dataclass
class StoryWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
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


ITEMS = {
    "manuscript": {"label": "manuscript", "phrase": "an old manuscript with neat English words", "region": "hands"},
    "book": {"label": "book", "phrase": "a little English storybook", "region": "hands"},
    "papers": {"label": "papers", "phrase": "a bundle of English practice papers", "region": "hands", "plural": True},
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Noah", "Finn", "Leo", "Eli", "Theo", "Ben", "Max"]
TRAITS = ["curious", "gentle", "cheerful", "sleepy", "careful", "brave"]

ASP_RULES = r"""
at_risk(I) :- item(I), worn_on(I, hands).
protects(G, I) :- gear(G), item(I), guards(G, wet), covers(G, hands).
has_fix(I) :- protects(_, I).
valid(I) :- at_risk(I), has_fix(I).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "swimming_pool")]
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("worn_on", iid, item["region"]))
    lines.append(asp.fact("gear", "towel_bag"))
    lines.append(asp.fact("guards", "towel_bag", "wet"))
    lines.append(asp.fact("covers", "towel_bag", "hands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    clingo = set(asp.atoms(model, "valid"))
    py = {("manuscript",)}
    if clingo == py:
        print("OK: clingo gate matches Python gate (1 valid item).")
        return 0
    print("MISMATCH:", sorted(clingo), sorted(py))
    return 1


def reasonableness_gate(item_id: str) -> bool:
    return item_id in ITEMS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world set at a swimming pool.")
    ap.add_argument("--place", choices=["swimming_pool"], default="swimming_pool")
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    item = args.item or "manuscript"
    if not reasonableness_gate(item):
        raise StoryError("That item does not belong in this story.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="swimming_pool", hero_name=name, gender=gender, parent=parent, trait=trait, item=item)


def _sound(word: str) -> str:
    return {"water": "splash-splash", "warning": "plink!", "cover": "swish", "paper": "rustle-rustle"}.get(word, word)


def generate(params: StoryParams) -> StorySample:
    world = StoryWorld(Setting())
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.gender, mem es={"joy": 0.0, "worry": 0.0, "caution": 0.0, "comfort": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id="item",
        type="thing",
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        owner=hero.id,
        caretaker=parent.id,
        region=item_cfg["region"],
        plural=item_cfg.get("plural", False),
    ))

    world.say(f"At {world.setting.place}, little {params.trait} {params.hero_name} loved the quiet English words in {item.phrase}.")
    world.say(f"The pages felt like a tiny bedtime song, and {params.hero_name} liked to nibble a corner of the thought of the story, just a little, not for real.")
    world.say(f"\"Remember,\" said {parent.label}, \"water says {_sound('warning')}, and {_sound('water')} can find anything left too close to the pool.\"")
    world.para()
    world.say(f"{params.hero_name} wanted to read beside the water, and read, and read again.")
    world.say(f"But when the towel slipped, {_sound('water')} went at the edge of the bench and the manuscript began to worry.")
    item.meters["wet"] += 1
    hero.memes["worry"] += 1
    world.say(f"\"Not on the manuscript,\" said {parent.label}. \"Not on the manuscript. Not on the manuscript.\"")
    world.say(f"{params.hero_name} nodded, because caution can be soft like a blanket.")
    world.para()
    world.say(f"So they moved back under the shade, {_sound('cover')} went the towel over the papers, and {_sound('paper')} stayed inside.")
    item.protective = True
    item.memes["comfort"] += 1
    hero.memes["joy"] += 1
    world.say(f"{params.hero_name} read one English line, then another, and the little manuscript stayed dry and safe.")
    world.say(f"At the swimming pool, the water still shimmered, but the story did not get wet at all.")

    world.facts = {"hero": hero, "parent": parent, "item": item, "params": params}
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: StoryWorld) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a bedtime story set at a swimming pool that includes the words "english", "nibble", and "manuscript".',
        f"Tell a gentle story where {p.hero_name} wants to read {p.item} near the pool, but a parent gives a careful warning.",
        "Write a short story with sound effects, repetition, and a safe ending by the water.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    p = world.facts["params"]
    parent = world.facts["parent"]
    item = world.facts["item"]
    return [
        QAItem(
            question=f"What did {p.hero_name} want to do beside the swimming pool?",
            answer=f"{p.hero_name} wanted to read the {item.label} and listen to the English words inside it.",
        ),
        QAItem(
            question=f"Why did {parent.label} give a cautionary warning?",
            answer=f"{parent.label} knew the pool water could splash over the {item.label} and make the pages wet.",
        ),
        QAItem(
            question=f"How did the story end for the {item.label}?",
            answer=f"The {item.label} was covered with a towel and stayed dry and safe.",
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(question="What does English mean here?", answer="English is the language of the words in the little storybook or manuscript."),
        QAItem(question="What does nibble mean?", answer="To nibble means to take tiny little bites or to make a small, careful bite."),
        QAItem(question="What is a manuscript?", answer="A manuscript is a text written by hand or an old written copy of a story."),
    ]


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for item in sorted(ITEMS):
            params = StoryParams(place="swimming_pool", hero_name="Mia", gender="girl", parent="mother", trait="careful", item=item)
            params.seed = base_seed
            samples.append(generate(params))
    else:
        for i in range(max(args.n, 1)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
