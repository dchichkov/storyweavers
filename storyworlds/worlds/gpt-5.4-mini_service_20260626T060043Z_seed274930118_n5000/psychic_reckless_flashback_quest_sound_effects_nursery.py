#!/usr/bin/env python3
"""
storyworlds/worlds/psychic_reckless_flashback_quest_sound_effects_nursery.py
=============================================================================

A small nursery-rhyme story world about a psychic helper, a reckless quest,
a flashback clue, and sound effects that steer the ending.

Premise:
- A child hears a tiny psychic whisper that a lost bell is waiting in a moonlit
  meadow.
- The child starts a reckless quest, rushes ahead, and nearly misses the right
  path.
- A flashback reveals an old lesson: listen for the sound that matches the
  treasure.
- The child follows the sounds, finds the bell, and returns home with calm
  pride.

The world model tracks physical meters and emotional memes so the prose is
driven by state changes rather than a fixed template.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    glow: str
    soundscape: str


@dataclass
class Quest:
    id: str
    object_label: str
    object_phrase: str
    clue_sound: str
    risky_verb: str
    careful_verb: str
    ending_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    type: str
    label: str
    whisper: str
    flashback_line: str


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


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    quest: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_meadow": Setting(
        place="the moonlit meadow",
        glow="silver",
        soundscape="whisper",
    ),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        object_label="silver bell",
        object_phrase="a little silver bell",
        clue_sound="ding-ding",
        risky_verb="dash through the reeds",
        careful_verb="tiptoe by the reeds",
        ending_sound="ting-ting",
        tags={"sound", "flashback", "quest"},
    ),
    "kite": Quest(
        id="kite",
        object_label="star kite",
        object_phrase="a bright star kite",
        clue_sound="swish-swish",
        risky_verb="race over the hill",
        careful_verb="walk over the hill",
        ending_sound="whoosh-whoosh",
        tags={"sound", "flashback", "quest"},
    ),
}

COMPANIONS = {
    "owl": Companion(
        id="owl",
        type="owl",
        label="an old owl",
        whisper="whoo-whoo",
        flashback_line="Long ago, the owl had taught the child to listen for the softest sound.",
    ),
    "fox": Companion(
        id="fox",
        type="fox",
        label="a small fox",
        whisper="mew-mew",
        flashback_line="Once before, the fox had pointed to the right path when the child heard a tiny chime.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Milo", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for quest in QUESTS:
            for comp in COMPANIONS:
                out.append((place, quest, comp))
    return out


def reasonableness_gate(quest: Quest) -> bool:
    return "sound" in quest.tags and "quest" in quest.tags


ASP_RULES = r"""
#show valid/3.

valid(P,Q,C) :- place(P), quest(Q), companion(C), quest_tag(Q, sound), quest_tag(Q, quest).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, t))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print(" only in clingo:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme psychic quest story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    choices = valid_combos()
    if args.quest and not reasonableness_gate(QUESTS[args.quest]):
        raise StoryError("The quest is not sound-based enough for this world.")
    combos = [
        c for c in choices
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.companion is None or c[2] == args.companion)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, companion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(name=name, gender=gender, companion=companion, quest=quest)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS["moon_meadow"]
    quest = QUESTS[params.quest]
    comp = COMPANIONS[params.companion]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"feet": 0.0},
        memes={"curiosity": 0.0, "reckless": 0.0, "joy": 0.0, "relief": 0.0, "wonder": 0.0},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=comp.type,
        label=comp.label,
        memes={"care": 0.0, "memory": 0.0},
    ))
    treasure = world.add(Entity(
        id=quest.id,
        type="thing",
        label=quest.object_label,
        phrase=quest.object_phrase,
        owner=None,
        caretaker=params.name,
        meters={"hidden": 1.0, "found": 0.0},
    ))

    world.facts.update(child=child, guide=guide, treasure=treasure, quest=quest, comp=comp)

    world.say(f"{child.id} went to {setting.place}, where the air was {setting.glow} and the night hummed soft.")
    world.say(f"{comp.label.capitalize()} gave a tiny whisper, {comp.whisper}, and pointed at the grass.")
    world.say(f'"There is {quest.object_phrase} somewhere here," {comp.label} said. "That is the quest for you."')

    world.para()
    child.memes["curiosity"] += 1
    child.memes["reckless"] += 1
    world.say(f"{child.id} felt brave and a little reckless, so {child.pronoun()} began to {quest.risky_verb}.")
    world.say(f"The path went {setting.place.split()[-1] if ' ' in setting.place else 'on'} with a patter, patter, patter sound.")

    world.para()
    world.say(f"Then came a flashback, bright as a blink.")
    world.say(comp.flashback_line)
    child.memes["wonder"] += 1
    child.memes["reckless"] = 0.0
    world.say(f"{child.id} remembered the lesson: the right path would sing the same sound as the treasure.")

    world.para()
    world.say(f"So {child.id} slowed down and chose to {quest.careful_verb}.")
    world.say(f"Near the brambles, the air went {quest.clue_sound} and {quest.ending_sound}, soft-soft-soft.")
    treasure.meters["found"] = 1.0
    treasure.meters["hidden"] = 0.0
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(f"There was {quest.object_phrase}, nestled in the moss like a moonbeam toy.")
    world.say(f"{child.id} picked it up and smiled, for the quest was done.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = f["quest"]
    c: Companion = f["comp"]
    child: Entity = f["child"]
    return [
        f'Write a short nursery-rhyme story about a psychic little hero who follows the sound "{q.clue_sound}".',
        f"Tell a story where {child.id} starts a reckless quest, remembers a flashback, and finds {q.object_phrase} with help from {c.label}.",
        f'Write a gentle rhyme with sound effects like "patter, patter" and a happy ending for a lost treasure quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    quest: Quest = f["quest"]
    comp: Companion = f["comp"]
    treasure: Entity = f["treasure"]
    return [
        QAItem(
            question=f"What was {child.id} trying to find in the meadow?",
            answer=f"{child.id} was trying to find {treasure.phrase} during the quest.",
        ),
        QAItem(
            question=f"Why did {child.id} slow down after acting reckless?",
            answer=f"{child.id} remembered the flashback lesson from {comp.label} and listened for the sound that matched the treasure.",
        ),
        QAItem(
            question=f"What sound helped guide {child.id} to the treasure?",
            answer=f'The clue sound was "{quest.clue_sound}", and the ending sound was "{quest.ending_sound}".',
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} found {treasure.phrase}, picked it up, and felt glad and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment in a story that shows something from before, so the listener can remember an old lesson or event.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like patter, ding-ding, or whoosh that help you imagine the noises in the scene.",
        ),
        QAItem(
            question="What does psychic mean here?",
            answer="Psychic means the helper seems to know or sense something in a special, mysterious way, like hearing a tiny clue in the air.",
        ),
    ]


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(name="Mia", gender="girl", companion="owl", quest="bell"),
    StoryParams(name="Leo", gender="boy", companion="fox", quest="kite"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:\n")
        for p, q, c in models:
            print(f"  {p:12} {q:8} {c}")
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
            header = f"### {p.name}: quest={p.quest}, companion={p.companion}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
