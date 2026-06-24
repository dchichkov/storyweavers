#!/usr/bin/env python3
"""
storyworlds/worlds/license_curiosity_happy_ending_friendship_whodunit.py
========================================================================

A small whodunit-flavored story world about curious friends, a missing license,
and a happy ending.

Seed tale sketch:
---
At the community garden library, two friends were ready for story hour. But the
special painting license that let them use the art table was missing. The friends
looked under benches, asked gentle questions, and followed small clues. In the
end, they found the license tucked inside a picture book by mistake, and
everyone laughed with relief.

World model:
---
- Curiosity raises a character's drive to search.
- Friendship raises trust and makes sharing clues easier.
- The mystery resolves when enough clues are found and the lost license is
  matched to a harmless mistake.
- The ending must prove the change in state: the license is recovered, the
  blame is cleared, and the friends are happy together.

The prose is intentionally child-facing and clue-driven, with a cozy whodunit
shape: a problem, a search, a reveal, and a happy ending.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clean": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "friendship": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    hiding_spots: list[str]
    clue_spots: list[str]


@dataclass
class Mystery:
    id: str
    title: str
    lost_item: str
    item_phrase: str
    item_owner_role: str
    culprit_role: str
    culprit_reason: str
    final_place: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero: str
    friend: str
    sidekick: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(
        place="the community library",
        mood="quiet and cozy",
        hiding_spots=["behind the picture books", "under a reading bench", "inside a basket"],
        clue_spots=["between book pages", "near the return cart", "by the rug"],
    ),
    "garden": Setting(
        place="the community garden shed",
        mood="soft and sunny",
        hiding_spots=["behind a watering can", "under a bench", "in a flower crate"],
        clue_spots=["beside the seed jars", "near the chalkboard", "under a glove"],
    ),
    "museum": Setting(
        place="the little town museum",
        mood="bright and echoing",
        hiding_spots=["behind a display case", "under a stool", "inside a brochure rack"],
        clue_spots=["by the welcome desk", "near the map stand", "under a little poster"],
    ),
}

MYSTERIES = {
    "paint_license": Mystery(
        id="paint_license",
        title="the missing paint license",
        lost_item="license",
        item_phrase="the blue paint license",
        item_owner_role="art teacher",
        culprit_role="librarian",
        culprit_reason="to keep it safe inside a book while cleaning the art table",
        final_place="inside a picture book",
        tags={"license", "paint", "book"},
    ),
    "garden_license": Mystery(
        id="garden_license",
        title="the missing garden license",
        lost_item="license",
        item_phrase="the green garden license",
        item_owner_role="garden keeper",
        culprit_role="friend",
        culprit_reason="to tuck it into a note pocket during a game and forgot it there",
        final_place="inside a folded note",
        tags={"license", "garden", "note"},
    ),
    "music_license": Mystery(
        id="music_license",
        title="the missing music license",
        lost_item="license",
        item_phrase="the shiny music license",
        item_owner_role="music helper",
        culprit_role="child",
        culprit_reason="to use it as a bookmark and left it in a book",
        final_place="between the pages of a song book",
        tags={"license", "music", "book"},
    ),
}

NAMES = ["Mia", "Noah", "Lily", "Ben", "Zoe", "Theo", "Ava", "Jun"]
TRAITS = ["curious", "careful", "kind", "bright", "patient", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cozy whodunit story world about a missing license and curious friends."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--sidekick")
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


def is_reasonable(setting: Setting, mystery: Mystery) -> bool:
    return "license" in mystery.tags and bool(setting.hiding_spots) and bool(setting.clue_spots)


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.title} does not fit {setting.place}. "
        f"The story needs hiding spots and clue spots so the whodunit can unfold.)"
    )


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            if is_reasonable(SETTINGS[s], MYSTERIES[m]):
                out.append((s, m))
    return out


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in s.hiding_spots:
            lines.append(asp.fact("hides", sid, spot))
        for spot in s.clue_spots:
            lines.append(asp.fact("clue_spot", sid, spot))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("lost", mid, m.lost_item))
        lines.append(asp.fact("item_owner_role", mid, m.item_owner_role))
        lines.append(asp.fact("culprit_role", mid, m.culprit_role))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S, M) :- setting(S), mystery(M), lost(M, license), clue_spot(S, _), hides(S, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n not in {hero, friend}])
    return StoryParams(setting=setting, mystery=mystery, hero=hero, friend=friend, sidekick=sidekick)


def _char(world: World, name: str, role: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type="child", label=name, phrase=role))


def _item(world: World, mystery: Mystery) -> Entity:
    return world.add(Entity(
        id="license",
        type="license",
        label="license",
        phrase=mystery.item_phrase,
        owner="adult",
        hidden_in="",
    ))


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    hero = _char(world, params.hero, "curious friend")
    friend = _char(world, params.friend, "helpful friend")
    sidekick = _char(world, params.sidekick, "quiet helper")
    license_item = _item(world, mystery)
    culprit = world.add(Entity(id="adult", kind="character", type="adult", label=mystery.culprit_role))
    world.facts.update(
        hero=hero, friend=friend, sidekick=sidekick, culprit=culprit,
        mystery=mystery, license=license_item, setting=setting
    )
    return world


def generate_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    sidekick: Entity = f["sidekick"]
    culprit: Entity = f["culprit"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    license_item: Entity = f["license"]

    hero.memes["curiosity"] += 2
    friend.memes["friendship"] += 2
    sidekick.memes["friendship"] += 1

    world.say(
        f"At {setting.place}, {hero.id} and {friend.id} were ready for a calm day. "
        f"The place felt {setting.mood}, and {hero.id} noticed that {mystery.item_phrase} was gone."
    )
    world.say(
        f'{hero.id} frowned. "We should find the {license_item.label}," {hero.id} said, '
        f"because the room could not start the special activity without it."
    )

    world.para()
    world.say(
        f"{friend.id} nodded right away. That kind of friendship made the search feel brave instead of scary. "
        f"{sidekick.id} came along too, carrying a pencil and looking under the nearest bench."
    )

    clue_count = 0
    for spot in setting.clue_spots[:2]:
        clue_count += 1
        world.say(
            f"They found a small clue near {spot}: a tiny trail that pointed toward {mystery.final_place}."
        )
    hero.memes["curiosity"] += clue_count
    friend.memes["friendship"] += 1

    world.para()
    world.say(
        f"{hero.id} asked gentle questions, one by one, and {friend.id} listened closely. "
        f"At last, they learned that the {mystery.culprit_role} had not meant to be sneaky at all."
    )
    world.say(
        f'The {mystery.culprit_role} had only done it {mystery.culprit_reason}. '
        f'That was the whole whodunit: a mistake, not a mean trick.'
    )

    world.para()
    license_item.hidden_in = mystery.final_place
    license_item.carried_by = hero.id
    hero.memes["relief"] += 2
    friend.memes["relief"] += 2
    culprit.memes["relief"] += 1
    world.say(
        f'Together they opened {mystery.final_place}, and there was the {license_item.label} at last. '
        f'{hero.id} held it up like a tiny treasure, and everyone laughed with relief.'
    )
    world.say(
        f"The missing license was back where it belonged, the room could begin the activity, "
        f"and the friends walked home happy, side by side."
    )


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    hero: Entity = f["hero"]
    return [
        f'Write a gentle whodunit for a young child about a missing {mystery.lost_item} at {setting.place}.',
        f"Tell a story where {hero.id} uses curiosity and friendship to solve the mystery of {mystery.item_phrase}.",
        f'Write a happy-ending mystery story that includes the word "license" and ends with a small group of friends smiling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    culprit: Entity = f["culprit"]
    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at {setting.place}, which felt {setting.mood}."
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The missing thing was {mystery.item_phrase}, a license the room needed."
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"{hero.id} and {friend.id} solved it together, and their friendship helped them keep looking."
        ),
        QAItem(
            question=f"Why was the {mystery.culprit_role} involved?",
            answer=f"The {mystery.culprit_role} had moved the license only to keep it safe, so it was a harmless mistake."
        ),
        QAItem(
            question="How did the story end?",
            answer="The friends found the license, laughed with relief, and ended the day happy."
        ),
    ]


KNOWLEDGE = {
    "license": [
        (
            "What is a license?",
            "A license is a paper or card that says someone has permission to do something, like use a place or activity."
        )
    ],
    "book": [
        (
            "Why do people use bookmarks?",
            "People use bookmarks to save their place in a book so they can find the page again later."
        )
    ],
    "friendship": [
        (
            "What does friendship help people do?",
            "Friendship helps people share, listen, and solve problems together."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes someone want to ask questions and learn more."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    tags.update({"license", "friendship", "curiosity", "book"})
    out: list[QAItem] = []
    for tag in ["curiosity", "friendship", "license", "book"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.hidden_in:
            parts.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", mystery="music_license", hero="Mia", friend="Jun", sidekick="Theo"),
    StoryParams(setting="garden", mystery="garden_license", hero="Ava", friend="Noah", sidekick="Lily"),
    StoryParams(setting="museum", mystery="paint_license", hero="Ben", friend="Zoe", sidekick="Mia"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=story_text(world),
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery:
        if not is_reasonable(SETTINGS[args.setting], MYSTERIES[args.mystery]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], MYSTERIES[args.mystery]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    return StoryParams(setting=setting, mystery=mystery, hero=args.hero or rng.choice(NAMES),
                       friend=args.friend or rng.choice(NAMES), sidekick=args.sidekick or rng.choice(NAMES))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, m in combos:
            print(f"  {s:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
