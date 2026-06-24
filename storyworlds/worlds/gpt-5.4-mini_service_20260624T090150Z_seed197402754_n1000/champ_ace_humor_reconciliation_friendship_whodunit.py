#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/champ_ace_humor_reconciliation_friendship_whodunit.py
================================================================================================

A small whodunit storyworld about a puzzling missing thing, two friends named
Champ and Ace, and a cheerful solution that ends in reconciliation.

Seed inspiration:
- A child-friendly mystery with a clear clue trail.
- Humor to keep the tension light.
- Friendship and reconciliation at the end.
- "champ" and "ace" as core seed words.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

WORLD_ID = "whodunit_champ_ace"
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
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue: str
    smudge: str
    hide_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    habit: str
    truth: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    suspect: str
    name: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "clubhouse": Setting(
        place="the clubhouse",
        detail="The clubhouse had a round table, a coat rack, and one tiny window.",
        afford={"cookie", "lantern", "ribbon"},
    ),
    "kitchen": Setting(
        place="the kitchen",
        detail="The kitchen had a warm lamp, a low shelf, and a chair with a squeaky leg.",
        afford={"cookie", "lantern", "ribbon"},
    ),
}

MYSTERIES = {
    "cookie_tin": Mystery(
        id="cookie_tin",
        label="cookie tin",
        phrase="a shiny cookie tin",
        clue="crumbs",
        smudge="crumb",
        hide_spot="the story shelf",
        tags={"cookie", "funny", "friendship"},
    ),
    "lantern": Mystery(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        clue="soot",
        smudge="soot",
        hide_spot="the back shelf",
        tags={"lantern", "light", "funny"},
    ),
    "ribbon_box": Mystery(
        id="ribbon_box",
        label="ribbon box",
        phrase="a box of bright ribbons",
        clue="sparkles",
        smudge="glitter",
        hide_spot="the art shelf",
        tags={"ribbon", "funny", "friendship"},
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the cat",
        type="thing",
        alibi="It had been napping on the rug.",
        habit="like to curl up in warm places",
        truth="The cat only brushed past the shelf and did not take anything.",
    ),
    "pigeon": Suspect(
        id="pigeon",
        label="the pigeon",
        type="thing",
        alibi="It had been pecking crumbs outside the open door.",
        habit="like to stare at shiny things",
        truth="The pigeon saw the shiny thing but never carried it off.",
    ),
    "little_sibling": Suspect(
        id="little sibling",
        label="little sibling",
        type="boy",
        alibi="He had been building a block tower near the window.",
        habit="like to hide things as a joke",
        truth="He hid the item for a prank, then felt sorry and brought it back.",
    ),
}

GAMES = [
    "A tiny mystery needed a careful look.",
    "The room looked ordinary, which made the puzzle feel stranger.",
    "Everybody wanted the truth, even if the truth was a little silly.",
]

NAMES = ["Champ", "Ace", "Mina", "Toby", "Lila", "Nico", "Pia", "Juno"]
FRIEND_NAMES = ["Ace", "Champ", "Maya", "Ben", "Rae", "Finn", "Ivy", "Zed"]
FRIENDSHIP = ["kind", "loyal", "bright", "patient", "helpful"]
HUMOR = ["funny", "quick-witted", "playful", "cheerful", "mischievous"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id, mystery in MYSTERIES.items():
            if mystery.id not in setting.afford and mystery.id != "ribbon_box":
                continue
            for suspect_id in SUSPECTS:
                combos.append((setting_id, mystery_id, suspect_id))
    return combos


@dataclass
class ASPConfig:
    setting: str
    mystery: str
    suspect: str


ASP_RULES = r"""
% A story combo is valid if the setting can host the mystery and the suspect exists.
valid(Setting, Mystery, Suspect) :- setting(Setting), mystery(Mystery), suspect(Suspect),
                                    affords(Setting, Mystery).

% The ribbon box is always reasonable in either setting because it is a small,
% portable object that can be hidden on any shelf.
valid(Setting, ribbon_box, Suspect) :- setting(Setting), suspect(Suspect).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for obj in sorted(setting.afford):
            lines.append(asp.fact("affords", sid, obj))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def reasonability_gate(args: argparse.Namespace) -> None:
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.setting and args.mystery:
        if (args.setting, args.mystery, args.suspect or "cat") not in valid_combos():
            raise StoryError("That mystery does not fit the chosen setting.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonability_gate(args)
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, mystery, suspect = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if friend == name:
        friend = "Ace" if name != "Ace" else "Champ"
    return StoryParams(setting=setting, mystery=mystery, suspect=suspect, name=name, friend=friend)


def _mood(world: World, key: str, delta: float) -> None:
    for ent in world.entities.values():
        ent.memes[key] = ent.memes.get(key, 0.0) + delta


def generate_mystery_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    suspect = SUSPECTS[params.suspect]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Champ", "Toby", "Nico"} else "girl", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy" if params.friend in {"Champ", "Toby", "Nico", "Ace", "Ben", "Finn", "Zed"} else "girl", label=params.friend))
    culprit = world.add(Entity(id=suspect.id, kind="character", type=suspect.type, label=suspect.label))
    item = world.add(Entity(id=mystery.id, kind="thing", type=mystery.id, label=mystery.label, phrase=mystery.phrase, owner=hero.id))

    hero.memes["curiosity"] = 1
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    suspect_actor = culprit

    world.say(f"{hero.id} and {friend.id} came to {setting.place}.")
    world.say(setting.detail)
    world.say(f"Then {hero.id} noticed that {item.phrase} was missing from its usual spot.")
    world.say(f"{item.label.capitalize()} mystery! {hero.id} and {friend.id} traded a look and started asking careful questions.")

    world.para()
    world.say(f"They checked the {mystery.hide_spot} first.")
    world.say(f"There was no {item.label} there, only {mystery.clue}.")
    item.meters["clue"] = 1
    hero.memes["worry"] = 1
    friend.memes["humor"] = 1
    world.say(f"{friend.id} whispered, 'That clue is almost as small as a mouse's sneeze.' {hero.id} almost laughed, which helped.")

    world.para()
    world.say(f"They asked {suspect.label}.")
    world.say(suspect.alibi)
    if suspect.id == "little_sibling":
        world.say("He tried to look innocent, but the guilty kind of smile kept wiggling on his face.")
        culprit.memes["guilt"] = 1
        hero.memes["suspicion"] = 1
    else:
        world.say(suspect.truth)
        culprit.memes["calm"] = 1

    world.para()
    if suspect.id == "little_sibling":
        world.say(f"{hero.id} pointed to the {mystery.clue}.")
        world.say(f"That clue matched the snack crumbs on {suspect.label}'s sleeves.")
        world.say(f"{suspect.label} sighed and admitted he had hidden the {item.label} for a prank.")
        world.say(f"He brought it back at once and said sorry.")
        culprit.memes["guilt"] = 0
        culprit.memes["reconciliation"] = 1
        hero.memes["reconciliation"] = 1
        friend.memes["humor"] = 2
        world.say(f"{hero.id} laughed a little, because the whole mystery had been a silly prank instead of a real theft.")
        world.say(f"Then {hero.id}, {friend.id}, and {suspect.label} set the {item.label} back in place and shared a smile.")
    else:
        world.say(f"{hero.id} noticed the clue on the floor and followed it to the {mystery.hide_spot}.")
        world.say(f"The {item.label} had slipped behind a stack of books.")
        world.say(f"{friend.id} grinned and said, 'We solved it without even needing detective capes.'")
        world.say(f"{hero.id} and {friend.id} put the {item.label} back where it belonged.")
        world.say(f"{suspect.label} gave a sheepish nod, and everyone agreed the mystery was over.")

    world.facts.update(
        hero=hero,
        friend=friend,
        culprit=culprit,
        item=item,
        mystery=mystery,
        suspect_cfg=suspect,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child that includes the words "champ" and "ace".',
        f"Tell a gentle mystery about {f['hero'].id} and {f['friend'].id} at {f['setting'].place}.",
        f"Write a funny detective story where a missing {f['item'].label} leads to a friendly apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    culprit = f["culprit"]
    item = f["item"]
    mystery = f["mystery"]

    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} trying to solve at {f['setting'].place}?",
            answer=f"They were trying to solve the mystery of the missing {item.label}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} notice the truth?",
            answer=f"The clue was {mystery.clue}, and it helped {hero.id} follow the trail.",
        ),
        QAItem(
            question=f"Who finally admitted what happened to the {item.label}?",
            answer=f"{culprit.label} admitted it and brought the {item.label} back.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}, {friend.id}, and {culprit.label}?",
            answer=f"They smiled, fixed the problem, and ended as friends again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions so they can learn what people saw and solve the mystery.",
        ),
        QAItem(
            question=f"Why can {mystery.label} be a useful clue?",
            answer=f"Because {mystery.clue} can show where the {mystery.label} was handled or hidden.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, say sorry if needed, and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.hidden:
            bits.append("hidden=True")
        lines.append(f"  {ent.id:12} ({ent.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_mystery_world(params)
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


def explain_rejection(args: argparse.Namespace) -> str:
    return "That combination does not make a reasonable little whodunit."


CURATED = [
    StoryParams(setting="clubhouse", mystery="cookie_tin", suspect="little_sibling", name="Champ", friend="Ace"),
    StoryParams(setting="kitchen", mystery="lantern", suspect="cat", name="Ace", friend="Champ"),
    StoryParams(setting="clubhouse", mystery="ribbon_box", suspect="pigeon", name="Mina", friend="Champ"),
]


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError(explain_rejection(args))
    setting, mystery, suspect = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if friend == name:
        friend = "Ace" if name != "Ace" else "Champ"
    return StoryParams(setting=setting, mystery=mystery, suspect=suspect, name=name, friend=friend)


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
                params = resolve_args(args, random.Random(seed))
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
            header = f"### {p.name} and {p.friend}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
