#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a child, a missing license, a sendaway
conflict, and a brave little quest to set things right.

The tale shape is simple:
- A child longs for a small quest.
- A gatekeeper sends the child away because a needed license is missing.
- The child shows bravery, finds the license, and returns.
- The ending proves the change: no more sendaway, quest accepted, conflict eased.

This world is intentionally tiny and constraint-checked so every generated story
stays close to the same grounded premise while still varying in names, places,
and the exact license/quest details.
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
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    place: str
    vibe: str
    affords: set[str]


@dataclass(frozen=True)
class Quest:
    id: str
    noun: str
    verb: str
    place_verb: str
    reward: str
    risk: str
    needs_license: bool = True


@dataclass(frozen=True)
class License:
    id: str
    label: str
    phrase: str
    protects: set[str]


@dataclass(frozen=True)
class Guide:
    id: str
    label: str
    sendaway: str
    return_line: str
    accepts: set[str]


SETTINGS = {
    "nursery": Setting(place="the nursery", vibe="soft and bright", affords={"peek", "parade", "play"}),
    "garden": Setting(place="the garden gate", vibe="green and breezy", affords={"peek", "find", "parade"}),
    "lantern_hall": Setting(place="the lantern hall", vibe="warm and low", affords={"sing", "parade", "find"}),
}

QUESTS = {
    "peek": Quest(
        id="peek",
        noun="peek",
        verb="peek at the prize",
        place_verb="peeked at the prize",
        reward="a tiny smile from the crowd",
        risk="the gatekeeper might send the child away",
    ),
    "parade": Quest(
        id="parade",
        noun="parade",
        verb="join the little parade",
        place_verb="joined the little parade",
        reward="a bright ribbon at the end",
        risk="the line would be too strict without a license",
    ),
    "find": Quest(
        id="find",
        noun="find",
        verb="find the lost star",
        place_verb="found the lost star",
        reward="a shiny star token",
        risk="the keeper would not open the door",
    ),
}

LICENSES = {
    "paper_pass": License(
        id="paper_pass",
        label="paper pass",
        phrase="a little paper pass with a gold stamp",
        protects={"peek", "parade"},
    ),
    "moon_license": License(
        id="moon_license",
        label="moon license",
        phrase="a moon license tied with blue string",
        protects={"find", "parade"},
    ),
    "song_card": License(
        id="song_card",
        label="song card",
        phrase="a song card folded small in a pocket",
        protects={"peek", "find"},
    ),
}

GUIDES = {
    "gatekeeper": Guide(
        id="gatekeeper",
        label="the gatekeeper",
        sendaway="send away",
        return_line="welcome back",
        accepts={"paper_pass", "moon_license", "song_card"},
    ),
    "librarian": Guide(
        id="librarian",
        label="the librarian",
        sendaway="shoo away",
        return_line="step right in",
        accepts={"song_card", "paper_pass"},
    ),
    "star_warden": Guide(
        id="star_warden",
        label="the star warden",
        sendaway="turn away",
        return_line="come on through",
        accepts={"moon_license"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Noah", "Theo", "Max"]
TRAITS = ["brave", "gentle", "tiny", "cheery", "bold"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    license: str
    guide: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _pronoun(type_: str, case: str) -> str:
    return Entity(id="_", type=type_).pronoun(case)


def pick_license_for(quest: Quest, allowed: Optional[str] = None) -> list[str]:
    vals = []
    for lid, lic in LICENSES.items():
        if quest.id in lic.protects and (allowed is None or lid == allowed):
            vals.append(lid)
    return vals


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for quest_id, quest in QUESTS.items():
            for license_id, lic in LICENSES.items():
                if quest.id in lic.protects:
                    for guide_id, guide in GUIDES.items():
                        if license_id in guide.accepts:
                            combos.append((setting_id, quest_id, license_id, guide_id))
    return combos


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def tell(setting: Setting, quest: Quest, lic: License, guide: Guide,
         name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={"hope": 1.0}, memes={"bravery": 0.0, "conflict": 0.0}))
    keeper = world.add(Entity(id=guide.id, kind="character", type="adult", label=guide.label, meters={"duty": 1.0}))
    item = world.add(Entity(id=lic.id, type="license", label=lic.label, phrase=lic.phrase, owner=hero.id, keeper=keeper.id))

    world.facts.update(hero=hero, keeper=keeper, item=item, quest=quest, license=lic, guide=guide, setting=setting)

    # Opening
    world.say(f"In {setting.place}, with its {setting.vibe}, there lived a little {trait} {gender} named {name}.")
    world.say(f"{_pronoun(gender, 'subject').capitalize()} loved a small quest: to {quest.verb}.")
    world.say(f"But to do that, {name} needed {lic.phrase}.")
    world.para()

    # Conflict
    world.say(f"One day {name} went to {setting.place} and tried to {quest.verb}.")
    world.say(f"The {guide.label} looked at the empty hands and said, \"No {lic.label}, no turn for you.\"")
    world.say(f"Then the {guide.sendaway} words came down: {name} was sent away at once.")
    hero.memes["conflict"] += 1.0
    hero.meters["distance"] = 1.0
    world.para()

    # Bravery + quest
    world.say(f"But {name} was {trait} and {trait} enough to try again.")
    world.say(f"{_pronoun(gender, 'subject').capitalize()} went on a little quest to find the missing {lic.label}.")
    world.say(f"{_pronoun(gender, 'subject').capitalize()} searched a basket, a bench, and a blue cloth.")
    hero.memes["bravery"] += 1.0
    hero.meters["search_steps"] = 3.0

    # Resolution
    world.say(f"At last, {name} found {item.phrase} tucked where the moonlight could touch it.")
    world.say(f"{_pronoun(gender, 'subject').capitalize()} hurried back to {guide.label} and held it up high.")
    world.say(f'The {guide.label} smiled and said, "{guide.return_line}."')
    world.say(f"So {name} could {quest.place_verb}, and the sendaway was gone like a puff of dust.")
    hero.memes["conflict"] = 0.0
    hero.meters["distance"] = 0.0
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    lic = f["license"]
    setting = f["setting"]
    return [
        f'Write a nursery-rhyme style story about a little child who wants to {quest.verb} but needs {lic.label}.',
        f"Tell a gentle story in {setting.place} where {hero.id} is sent away, then shows bravery on a quest to find a license.",
        f'Write a small rhyming tale with the words "license" and "sendaway" and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    quest = f["quest"]
    lic = f["license"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Why was {hero.id} sent away from {setting.place}?",
            answer=f"{hero.id} was sent away because the {keeper.label} would not let {hero.pronoun('object')} {quest.verb} without {lic.label}.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do after the sendaway?",
            answer=f"{hero.id} went on a small quest to find {lic.phrase}, and that was the brave part.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {hero.id} came back with {lic.label}, and the {keeper.label} let {hero.pronoun('object')} {quest.place_verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} want all along?",
            answer=f"{hero.id} wanted to {quest.verb} from the beginning, and the whole story followed that wish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a license in this storyworld?",
            answer="A license is a little permission token that lets a child join a special thing safely or fairly.",
        ),
        QAItem(
            question="What does sendaway mean?",
            answer="Sendaway means being told to leave for now and come back later, usually until the rules are met.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the hard or scary thing anyway, even when the first answer is no.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small search or journey to find something important or to make something right.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(nursery; garden; lantern_hall).

quest(peek; parade; find).
license(paper_pass; moon_license; song_card).
guide(gatekeeper; librarian; star_warden).

affords(nursery, peek).
affords(nursery, parade).
affords(nursery, play).
affords(garden, peek).
affords(garden, find).
affords(garden, parade).
affords(lantern_hall, sing).
affords(lantern_hall, parade).
affords(lantern_hall, find).

protects(paper_pass, peek).
protects(paper_pass, parade).
protects(moon_license, find).
protects(moon_license, parade).
protects(song_card, peek).
protects(song_card, find).

accepts(gatekeeper, paper_pass).
accepts(gatekeeper, moon_license).
accepts(gatekeeper, song_card).
accepts(librarian, paper_pass).
accepts(librarian, song_card).
accepts(star_warden, moon_license).

valid(S, Q, L, G) :- setting(S), quest(Q), license(L), guide(G),
                     protects(L, Q), accepts(G, L), affords(S, Q).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for lid in LICENSES:
        lines.append(asp.fact("license", lid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    for sid, s in SETTINGS.items():
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        for lid, lic in LICENSES.items():
            if qid in lic.protects:
                lines.append(asp.fact("protects", lid, qid))
    for gid, g in GUIDES.items():
        for lid in sorted(g.accepts):
            lines.append(asp.fact("accepts", gid, lid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def explain_rejection(setting: Setting, quest: Quest, lic: License, guide: Guide) -> str:
    return (
        f"(No story: in {setting.place}, {guide.label} would not let a child {quest.verb} "
        f"with {lic.label}, so the premise has no honest sendaway conflict to resolve.)"
    )


def valid_story_combo(setting_id: str, quest_id: str, license_id: str, guide_id: str) -> bool:
    quest = QUESTS[quest_id]
    lic = LICENSES[license_id]
    guide = GUIDES[guide_id]
    return quest.id in lic.protects and license_id in guide.accepts and quest.id in SETTINGS[setting_id].affords


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about license, sendaway, conflict, bravery, and quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--license", dest="license_", choices=LICENSES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting or args.quest or args.license_ or args.guide:
        filtered = [c for c in combos
                    if (args.setting is None or c[0] == args.setting)
                    and (args.quest is None or c[1] == args.quest)
                    and (args.license_ is None or c[2] == args.license_)
                    and (args.guide is None or c[3] == args.guide)]
        if not filtered:
            raise StoryError("(No valid story matches the given options.)")
        setting_id, quest_id, license_id, guide_id = rng.choice(sorted(filtered))
    else:
        setting_id, quest_id, license_id, guide_id = rng.choice(sorted(combos))

    setting = SETTINGS[setting_id]
    quest = QUESTS[quest_id]
    lic = LICENSES[license_id]
    guide = GUIDES[guide_id]

    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        quest=quest_id,
        license=license_id,
        guide=guide_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        LICENSES[params.license],
        GUIDES[params.guide],
        params.name,
        params.gender,
        params.trait,
    )
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="nursery", quest="peek", license="paper_pass", guide="gatekeeper", name="Mia", gender="girl", trait="brave"),
    StoryParams(setting="garden", quest="find", license="moon_license", guide="star_warden", name="Leo", gender="boy", trait="bold"),
    StoryParams(setting="lantern_hall", quest="parade", license="song_card", guide="librarian", name="Nora", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.quest} at {p.setting} with {p.license}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
