#!/usr/bin/env python3
"""
A small folk-tale storyworld about a child, a promise, a reminder, and a pucker
of disagreement that turns into a happy ending.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    item: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


@dataclass
class ItemDef:
    label: str
    phrase: str
    type: str


@dataclass
class StoryWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
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

    def copy(self) -> "StoryWorld":
        import copy
        clone = StoryWorld(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


REMINDERS = {
    "bread": "the bread was for the widow and her hungry child",
    "honey": "the honey was meant for the winter tea",
    "seed": "the seed bag was to be planted before the moon changed",
    "cloak": "the cloak belonged to the little traveler for the cold road",
}

SETTINGS = {
    "cottage": Setting(place="the cottage hearth", vibe="warm", affords={"bread", "honey", "cloak", "seed"}),
    "forest": Setting(place="the forest path", vibe="green", affords={"seed", "cloak"}),
    "market": Setting(place="the village market", vibe="busy", affords={"bread", "honey"}),
}

ITEMS = {
    "bread": ItemDef(label="bread loaf", phrase="a round loaf of fresh bread", type="bread"),
    "honey": ItemDef(label="honey jar", phrase="a small jar of golden honey", type="honey"),
    "seed": ItemDef(label="seed bag", phrase="a little bag of pumpkin seeds", type="seed"),
    "cloak": ItemDef(label="cloak", phrase="a wool cloak with a red clasp", type="cloak"),
}

HERO_NAMES = ["Mira", "Tobin", "Anya", "Pavel", "Lina", "Niko"]
ELDER_NAMES = ["Grandma Willow", "Old Marek", "Aunt Sova", "Grandfather Bram"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("The setting must be one of the known folk-tale places.")
    if params.item not in ITEMS:
        raise StoryError("The chosen item is not part of this storyworld.")
    if params.item not in SETTINGS[params.setting].affords:
        raise StoryError("That item does not belong in that setting for this tale.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, item))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,I) :- affords(S,I), setting(S), item(I).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for item in setting.affords:
            out.append((s, item))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_pairs())
    if a == b:
        print(f"OK: clingo gate matches valid_pairs() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    if a - b:
        print("only in clingo:", sorted(a - b))
    if b - a:
        print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: remind, pucker, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
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
    pairs = valid_pairs()
    if args.setting and args.item and (args.setting, args.item) not in pairs:
        raise StoryError("That setting and item cannot make a good folk-tale conflict.")
    choices = [p for p in pairs if (args.setting is None or p[0] == args.setting) and (args.item is None or p[1] == args.item)]
    if not choices:
        raise StoryError("No valid story matches the given options.")
    setting, item = rng.choice(choices)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    name = args.name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(setting=setting, item=item, hero_name=name, hero_type=hero_type, elder_name=elder, elder_type=elder_type)


def tell(params: StoryParams) -> StoryWorld:
    reasonableness_gate(params)
    world = StoryWorld(SETTINGS[params.setting])

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_type, label=params.elder_name))
    item_def = ITEMS[params.item]
    item = world.add(Entity(id="item", type=item_def.type, label=item_def.label, phrase=item_def.phrase, owner=hero.id, caretaker=elder.id))
    world.facts.update(hero=hero, elder=elder, item=item, params=params)

    world.say(f"Once in {world.setting.place}, there lived a little {hero.type} named {hero.id}.")
    world.say(f"{hero.id} loved the taste and smell of {item.phrase}, and {hero.pronoun('possessive')} heart felt bright when {hero.pronoun()} held {item.it()}.")
    world.say(f"Every evening, {elder.label} would smile and say, 'Remember, dear one, {REMINDERS[params.item]}.'")

    world.para()
    world.say(f"One day at {world.setting.place}, {hero.id} wanted to keep {item.label} all to {hero.pronoun('object')}.")
    world.say(f"{elder.label} gently reminded {hero.id} that the bread, honey, seed, or cloak was meant for another good task.")
    world.say(f"That made {hero.id} pucker {hero.pronoun('possessive')} lips with a small, stubborn frown.")

    world.para()
    world.say(f"{hero.id} said, 'But I want {item.it()} now!' and the little voice sounded like a storm in a teacup.")
    world.say(f"{elder.label} stayed calm and reminded {hero.id} again, because folk tales love a kind reminder more than a sharp scold.")
    world.say(f"Then {hero.id} looked at the waiting path and the waiting people, and the pucker in {hero.pronoun('possessive')} face slowly softened.")

    world.para()
    world.say(f"At last, {hero.id} carried {item.it()} where it belonged.")
    world.say(f"The neighbors thanked {hero.id}, {elder.label} laughed softly, and the evening felt like a song with the last note found.")
    world.say(f"That was the happy ending: {hero.id} kept {item.it()} with a kind heart, and everyone went home feeling warmer.")
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short folk tale for a child about {p.hero_name}, a reminder, and a pucker of upset that ends well.',
        f"Tell a gentle story where {p.hero_name} wants to keep the {p.item} but {p.elder_name} reminds them of the promise.",
        f"Write a folk-tale-style happy ending about a child who pucker-frowns, listens, and chooses kindly.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.hero_name}, a little {hero.type}, and {elder.label}, who keeps reminding {p.hero_name} to do the right thing.",
        ),
        QAItem(
            question=f"What did {elder.label} keep telling {p.hero_name}?",
            answer=f"{elder.label} kept reminding {p.hero_name} that {REMINDERS[p.item]}.",
        ),
        QAItem(
            question=f"Why did {p.hero_name} pucker {hero.pronoun('possessive')} lips?",
            answer=f"{p.hero_name} pucker-frowned because {hero.pronoun()} wanted to keep {item.it()} instead of sharing or carrying it where it belonged.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {p.hero_name} listened, carried {item.it()} to the right place, and everyone felt warm and glad.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to remind someone?", answer="To remind someone is to say something again so they do not forget it."),
        QAItem(question="What does pucker mean?", answer="To pucker means to draw the lips or face into a small tight shape, often when someone feels upset or thoughtful."),
        QAItem(question="What is a folk tale?", answer="A folk tale is an old story told from person to person, often with a lesson, a challenge, and a happy ending."),
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
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} kind={e.kind} label={e.label!r} owner={e.owner} caretaker={e.caretaker}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(setting="cottage", item="bread", hero_name="Mira", hero_type="girl", elder_name="Grandma Willow", elder_type="grandmother"),
    StoryParams(setting="forest", item="seed", hero_name="Tobin", hero_type="boy", elder_name="Old Marek", elder_type="grandfather"),
    StoryParams(setting="market", item="honey", hero_name="Anya", hero_type="girl", elder_name="Aunt Sova", elder_type="grandmother"),
    StoryParams(setting="cottage", item="cloak", hero_name="Pavel", hero_type="boy", elder_name="Grandfather Bram", elder_type="grandfather"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible setting/item pairs:\n")
        for s, i in vals:
            print(f"  {s:10} {i}")
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
            header = f"### {p.hero_name}: {p.setting} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
