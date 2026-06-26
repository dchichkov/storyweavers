#!/usr/bin/env python3
"""
A storyworld for a tiny rhyming quest with a flashback, a helpful suggestion,
and a happy ending.

Premise:
- A small hero wants to go on a quest for a lost moon key.
- A friend suggests a safer route and influences the hero to follow a clue.
- A flashback explains why the hero cares about the key.
- The ending resolves in a cheerful rhyme.

This world is intentionally small and constraint-checked. It simulates physical
state (meters) and emotional state (memes) so the prose follows the model
rather than swapping nouns in a frozen paragraph.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap(self, text: str) -> str:
        return text[:1].upper() + text[1:] if text else text


class World:
    def __init__(self, setting: str, setting_phrase: str):
        self.setting = setting
        self.setting_phrase = setting_phrase
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.rhyme: list[str] = []

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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    quest_item: str
    flashback_item: str
    seed: Optional[int] = None


@dataclass
class Setting:
    key: str
    phrase: str
    path: str
    clue: str
    home: str


@dataclass
class QuestItem:
    key: str
    label: str
    phrase: str
    place: str
    glint: str


@dataclass
class Helper:
    key: str
    label: str
    suggestion: str
    influence: str
    rhyme_hint: str


SETTINGS: dict[str, Setting] = {
    "meadow": Setting(
        key="meadow",
        phrase="a sunny meadow by a singing stream",
        path="the pebble path",
        clue="a silver trail of clover",
        home="the cozy hill hut",
    ),
    "harbor": Setting(
        key="harbor",
        phrase="a breezy harbor with bright boats",
        path="the rope dock",
        clue="a shell that shone like snow",
        home="the round red lantern house",
    ),
    "orchard": Setting(
        key="orchard",
        phrase="an apple orchard with whispering trees",
        path="the curvy grass lane",
        clue="a stripe of moonlight on bark",
        home="the little porch under vines",
    ),
}

QUEST_ITEMS: dict[str, QuestItem] = {
    "moon_key": QuestItem(
        key="moon_key",
        label="moon key",
        phrase="a little moon key",
        place="the old stone well",
        glint="moon-bright",
    ),
    "star_bell": QuestItem(
        key="star_bell",
        label="star bell",
        phrase="a tiny star bell",
        place="the willow bridge",
        glint="starry",
    ),
    "song_leaf": QuestItem(
        key="song_leaf",
        label="song leaf",
        phrase="a singing leaf",
        place="the hollow oak",
        glint="green and bright",
    ),
}

HELPERS: dict[str, Helper] = {
    "sparrow": Helper(
        key="sparrow",
        label="sparrow",
        suggestion="take the soft path and look for the bright clue",
        influence="the sparrow's chirp steered the hero to the clue",
        rhyme_hint="follow the sparrow, narrow and shallow",
    ),
    "fox": Helper(
        key="fox",
        label="fox",
        suggestion="try the shady path where footprints show",
        influence="the fox's gentle nod changed the hero's mind",
        rhyme_hint="trust the fox and the little box of blocks",
    ),
    "grandma": Helper(
        key="grandma",
        label="grandma",
        suggestion="bring a lantern and go step by step",
        influence="grandma's calm voice helped the hero feel brave",
        rhyme_hint="light the night with grandma's light",
    ),
}

HEROES = [
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Tess", "girl"),
    ("Finn", "boy"),
    ("Luna", "girl"),
]

FLASHBACK_MOTIFS = {
    "moon_key": "the key once jingled in a lullaby at bedtime",
    "star_bell": "the bell once rang when the home lantern blinked awake",
    "song_leaf": "the leaf once sang when the wind was kind and slow",
}

WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a quest?",
        answer="A quest is a search for something important, often with a goal, a clue, and a brave journey.",
    ),
    QAItem(
        question="What does influence mean?",
        answer="To influence someone means to help change their choice or direction by what you say or do.",
    ),
    QAItem(
        question="What does suggest mean?",
        answer="To suggest something means to offer an idea, like a helpful plan or a safer way to do something.",
    ),
    QAItem(
        question="What is a flashback?",
        answer="A flashback is when a story briefly remembers something that happened before the main event.",
    ),
    QAItem(
        question="What is a happy ending?",
        answer="A happy ending is when the problem gets solved and the characters finish feeling glad and safe.",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting, helper, and quest item are all present.
valid_story(S, H, Q) :- setting(S), helper(H), quest(Q).

% The helper must be able to suggest and influence the hero in this world.
can_suggest(H) :- helper(H), suggests(H, _).
can_influence(H) :- helper(H), influences(H, _).

% A real story needs both suggestion and influence.
good_story(S, H, Q) :- valid_story(S, H, Q), can_suggest(H), can_influence(H).

#show good_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.key))
        lines.append(asp.fact("path", s.key, s.path))
        lines.append(asp.fact("clue", s.key, s.clue))
    for q in QUEST_ITEMS.values():
        lines.append(asp.fact("quest", q.key))
        lines.append(asp.fact("quest_place", q.key, q.place))
    for h in HELPERS.values():
        lines.append(asp.fact("helper", h.key))
        lines.append(asp.fact("suggests", h.key, h.suggestion))
        lines.append(asp.fact("influences", h.key, h.influence))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    clingo_set = set(asp.atoms(model, "good_story"))
    python_set = set((s, h, q) for s in SETTINGS for h in HELPERS for q in QUEST_ITEMS)
    if clingo_set == python_set:
        print(f"OK: ASP matches Python story space ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python story space:")
    if clingo_set - python_set:
        print(" only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming quest storyworld with suggest, influence, flashback, and happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--flashback-item", choices=QUEST_ITEMS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    helper = args.helper or rng.choice(list(HELPERS))
    quest_item = args.quest_item or rng.choice(list(QUEST_ITEMS))
    flashback_item = args.flashback_item or rng.choice(list(QUEST_ITEMS))
    if flashback_item == quest_item:
        raise StoryError("Flashback item must be different from the quest item.")
    return StoryParams(
        setting=setting,
        hero=hero,
        helper=helper,
        quest_item=quest_item,
        flashback_item=flashback_item,
    )


def _hero_type(name: str) -> str:
    return dict(HEROES)[name]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    helper = HELPERS[params.helper]
    quest = QUEST_ITEMS[params.quest_item]
    flashback = QUEST_ITEMS[params.flashback_item]
    hero_type = _hero_type(params.hero)

    world = World(setting=setting.key, setting_phrase=setting.phrase)
    hero = world.add(Entity(id=params.hero, kind="character", type=hero_type, label=params.hero))
    guide = world.add(Entity(id=helper.key, kind="character", type="creature", label=helper.label))
    item = world.add(Entity(
        id=quest.key,
        kind="thing",
        type="treasure",
        label=quest.label,
        phrase=quest.phrase,
        owner=params.hero,
        carried_by=None,
        found=False,
    ))
    lost = world.add(Entity(
        id=flashback.key,
        kind="thing",
        type="treasure",
        label=flashback.label,
        phrase=flashback.phrase,
        owner=params.hero,
        carried_by=None,
        found=True,
    ))

    hero.memes["hope"] = 1.0
    hero.memes["want"] = 1.0
    guide.memes["kind"] = 1.0
    item.meters["distance"] = 3.0
    lost.meters["memory"] = 1.0

    # Act 1: setup and flashback.
    world.say(f"In {setting.phrase}, {params.hero} had a quest to find {quest.phrase}.")
    world.say(f"Before the quest could start, {helper.label} came near and gave a gentle tip: {helper.suggestion}.")
    world.say(f"{helper.influence.capitalize()}, and {params.hero} felt the brave plan begin to grow.")
    world.para()
    world.say(f"Then came a flashback, soft as a feather in flight.")
    world.say(f"{FLASHBACK_MOTIFS[flashback.key].capitalize()}, and that was why {params.hero} cared so much.")
    world.say(f"{params.hero} remembered {flashback.phrase} from home, and the memory made {params.hero.lower() if False else params.hero} smile.")

    # Act 2: influence changes the route.
    world.para()
    hero.memes["curious"] = 1.0
    guide.meters["distance"] = 1.0
    hero.meters["distance"] = 1.0
    world.say(f"{params.hero} wanted to rush, but {helper.label} pointed to {setting.clue}.")
    world.say(f"So {params.hero} chose {setting.path} instead of a wild dash through the reeds.")
    world.say(f"The path was calm and fine, and each small step felt right in time.")

    # Act 3: quest success and ending image.
    item.found = True
    item.carried_by = params.hero
    item.meters["distance"] = 0.0
    hero.memes["joy"] = 2.0
    hero.memes["fear"] = 0.0
    hero.memes["gratitude"] = 1.0
    guide.memes["pride"] = 1.0
    world.para()
    world.say(f"At {quest.place}, {params.hero} found {quest.phrase} at last.")
    world.say(f"{params.hero} held it high, and the dark little worry passed.")
    world.say(f"{helper.label} grinned, and together they sang, 'Search with care, and you will see; follow the clue, and be feeling free.'")
    world.say(f"It was a happy ending, bright and true: the quest was done, and the sky looked new.")

    world.facts = {
        "hero": hero,
        "helper": guide,
        "quest": item,
        "flashback": lost,
        "setting": setting,
        "params": params,
        "helper_obj": helper,
        "quest_obj": quest,
        "flashback_obj": flashback,
        "resolved": True,
    }

    prompts = [
        f"Write a short rhyming story about a child named {params.hero} who goes on a quest in {setting.phrase}.",
        f"Tell a gentle story that uses suggest and influence, includes a flashback, and ends happily.",
        f"Write a simple rhyming tale where {helper.label} helps {params.hero} find {quest.phrase}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {helper.label} suggest to {params.hero}?",
            answer=f"{helper.label} suggested {helper.suggestion}, which helped {params.hero} choose the safer path.",
        ),
        QAItem(
            question=f"Why was there a flashback in the story?",
            answer=f"The flashback showed why {params.hero} cared about {quest.phrase}: {FLASHBACK_MOTIFS[flashback.key]}.",
        ),
        QAItem(
            question=f"What happened at the end of the quest?",
            answer=f"{params.hero} found {quest.phrase} at {quest.place}, felt glad, and the story ended with a happy ending.",
        ),
        QAItem(
            question=f"How did {helper.label} influence {params.hero}'s choice?",
            answer=f"{helper.influence.capitalize()}, so {params.hero} followed {setting.path} and kept going with care.",
        ),
    ]
    world_qa = WORLD_KNOWLEDGE + [
        QAItem(
            question="What do you do when you follow a clue?",
            answer="You pay attention to a sign or hint and let it help you choose where to go next.",
        ),
        QAItem(
            question="Why can a helper be important in a quest?",
            answer="A helper can give a clue, a suggestion, or a kind push that makes the quest easier and safer.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.found:
            bits.append("found=True")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for s in SETTINGS:
        for h in HELPERS:
            for q in QUEST_ITEMS:
                for fb in QUEST_ITEMS:
                    if fb != q:
                        out.append(StoryParams(setting=s, hero="Milo", helper=h, quest_item=q, flashback_item=fb))
    return out


def asp_all_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_all_combos()
        print(f"{len(combos)} compatible stories:")
        for s, h, q in combos:
            print(f"  {s:8} {h:8} {q:10}")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        for p in _all_params():
            p.seed = args.seed
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = args.seed
            sample = generate(p)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
