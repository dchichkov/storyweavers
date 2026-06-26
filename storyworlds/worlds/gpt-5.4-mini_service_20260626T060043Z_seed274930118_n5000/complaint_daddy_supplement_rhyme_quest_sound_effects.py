#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/complaint_daddy_supplement_rhyme_quest_sound_effects.py
================================================================================================

A compact storyworld in a Space Adventure style: a child and a daddy go on a
small quest for a supplement, with a complaint in the middle, a rhyme to steady
the mood, and sound effects to make the ship feel alive.

The premise is simple and child-facing:
- a small crew on a spaceship needs a supplement
- the child complains about the taste / the delay
- daddy turns it into a quest
- the quest succeeds with a playful rhyme and ship sounds

The world is intentionally small and constraint-driven so every generated story
reads like a complete miniature tale rather than a shuffled template.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "daddy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    quest_word: str
    destination: str
    obstacle: str
    sound: str
    rhyme: str
    reward: str
    keyword: str


@dataclass
class Supplement:
    id: str
    label: str
    phrase: str
    taste: str
    benefit: str
    container_sound: str
    carried_sound: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "space_station": Setting(place="the space station", indoors=True, affords={"quest"}),
    "moon_base": Setting(place="the moon base", indoors=True, affords={"quest"}),
    "cargo_ship": Setting(place="the cargo ship", indoors=True, affords={"quest"}),
}

QUESTS = {
    "medbay": Quest(
        id="medbay",
        quest_word="medbay quest",
        destination="the glowing medbay",
        obstacle="a long, humming hallway",
        sound="buzzz",
        rhyme="Through the hall and past the light, we fetch the fix and make it right.",
        reward="a helper star sticker",
        keyword="quest",
    ),
    "supply": Quest(
        id="supply",
        quest_word="supply quest",
        destination="the supply room",
        obstacle="a locked hatch that clicked and clinked",
        sound="clink-clink",
        rhyme="Step by step and side by side, we find the thing we need to ride.",
        reward="a shiny map pin",
        keyword="quest",
    ),
    "scanner": Quest(
        id="scanner",
        quest_word="scanner quest",
        destination="the scanner alcove",
        obstacle="a sleepy robot who blinked too slowly",
        sound="beep-beep",
        rhyme="When the lights go bright and neat, we keep our small brave marching beat.",
        reward="a moon ribbon",
        keyword="quest",
    ),
}

SUPPLEMENTS = {
    "vitamin": Supplement(
        id="vitamin",
        label="vitamin supplement",
        phrase="a bright vitamin supplement",
        taste="bitter at first, then sweet like berry juice",
        benefit="gives tired crews a little extra pep",
        container_sound="clack",
        carried_sound="jingle",
    ),
    "starcharge": Supplement(
        id="starcharge": "starcharge",
        label="star-charge supplement",
        phrase="a star-charge supplement",
        taste="minty and fizzy",
        benefit="helps sleepy travelers feel ready for the next stop",
        container_sound="snip",
        carried_sound="tink",
    ),
    "moonmilk": Supplement(
        id="moonmilk",
        label="moonmilk supplement",
        phrase="a moonmilk supplement",
        taste="soft and creamy with a tiny vanilla puff",
        benefit="keeps hungry space kids from getting grumbly",
        container_sound="pop",
        carried_sound="plip",
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Zoe", "Luna", "Ava"]
BOY_NAMES = ["Kai", "Finn", "Noah", "Leo", "Taj"]
TRAITS = ["curious", "brave", "bouncy", "lively", "tiny"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    supplement: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for sup in SUPPLEMENTS:
                combos.append((s, q, sup))
    return combos


def explain_rejection(setting: str, quest: str, supplement: str) -> str:
    return (
        f"(No story: the {quest} and the {supplement} do not fit the space-style "
        f"quest reasonableness gate for {setting}.)"
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    supp = SUPPLEMENTS[params.supplement]

    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    daddy = world.add(Entity(id="Daddy", kind="character", type="daddy", label="daddy"))
    item = world.add(Entity(
        id=supp.id,
        type="thing",
        label=supp.label,
        phrase=supp.phrase,
        owner=hero.id,
        carried_by=hero.id,
    ))

    world.facts.update(hero=hero, daddy=daddy, supplement=item, quest=quest, setting=setting)

    # Act 1: setup
    world.say(
        f"On {setting.place}, little {params.name} was a {params.trait} child who loved bright ship lights."
    )
    world.say(
        f"{params.name} had a {supp.phrase}, and the little bottle made a soft {supp.container_sound} in a pocket."
    )
    world.say(
        f"{params.name} knew the supplement {supp.benefit}, which made the whole crew smile when they were tired."
    )

    # Act 2: complaint and quest
    world.para()
    world.say(
        f"But {params.name} made a complaint in a grumpy little voice: "
        f"\"I do not want to wait for the {quest.quest_word}!\""
    )
    world.say(
        f"Daddy smiled and said, \"Then let us make it a quest. We will walk past {quest.obstacle} and bring it home.\""
    )
    world.say(
        f"As they started off, the corridor went {quest.sound}! {params.name} held the bottle tight, and it gave a tiny {supp.carried_sound}."
    )

    # Act 3: rhyme + resolution
    world.para()
    world.say(
        f"At {quest.destination}, a silver drawer slid open, and the needed supplement blinked like a small star."
    )
    world.say(f'Daddy said a rhyme to keep the steps light: "{quest.rhyme}"')
    world.say(
        f"{params.name} copied the rhyme, and the complaint drifted away like a puff of moon dust."
    )
    world.say(
        f"Then {params.name} tucked the supplement safely away, and the whole ship answered with a happy {quest.sound}."
    )
    world.say(
        f"By the end, {params.name} felt proud, Daddy felt proud too, and the little quest had turned into a bright space adventure."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    supp: Entity = f["supplement"]
    return [
        f'Write a short Space Adventure story for a child named {hero.id} with a complaint, a daddy, and a {supp.label}.',
        f"Tell a gentle quest story where {hero.id} and daddy travel to {quest.destination} and use a rhyme to stay brave.",
        f'Write a story that includes the sound effect "{quest.sound}" and ends with a happy space mission.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    supp: Entity = f["supplement"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who made the complaint at the start of the story?",
            answer=f"{hero.id} made the complaint because the quest felt slow at first.",
        ),
        QAItem(
            question=f"What did daddy call the trip to {quest.destination}?",
            answer=f"Daddy called it a quest, and he turned the problem into a brave little mission.",
        ),
        QAItem(
            question=f"What supplement was carried along on the adventure?",
            answer=f"They carried {supp.phrase}, which was the supplement in the story.",
        ),
        QAItem(
            question=f"What sound effect was heard in the hallway at {setting.place}?",
            answer=f"The hallway went {quest.sound}, which made the ship feel lively.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the supplement safely stored, the complaint gone, and the child feeling proud of the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest: Quest = f["quest"]
    supp: Entity = f["supplement"]
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip or mission to find something, solve a problem, or help someone.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like beep, buzz, or clink that help a story feel noisy and alive.",
        ),
        QAItem(
            question="What is a supplement?",
            answer="A supplement is something added to help the body get extra support, like a vitamin or special drink.",
        ),
        QAItem(
            question=f"Why might a supplement matter in a space story?",
            answer=f"In a space story, a supplement can help tired travelers feel better, which fits {supp.benefit}.",
        ),
        QAItem(
            question="Why do stories sometimes use rhyme?",
            answer="Stories use rhyme to sound playful, help children remember lines, and make a scene feel cheerful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
quest(Q) :- quest_fact(Q).
supplement(P) :- supplement_fact(P).

valid_story(S,Q,P) :- setting(S), quest(Q), supplement(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for q in QUESTS:
        lines.append(asp.fact("quest_fact", q))
    for p in SUPPLEMENTS:
        lines.append(asp.fact("supplement_fact", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world: complaint, daddy, supplement, rhyme, quest, sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--supplement", choices=SUPPLEMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    quest = args.quest or rng.choice(list(QUESTS))
    supplement = args.supplement or rng.choice(list(SUPPLEMENTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, supplement=supplement, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories")
        for t in asp.atoms(model, "valid_story"):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for quest in QUESTS:
                for supplement in SUPPLEMENTS:
                    p = StoryParams(
                        setting=setting,
                        quest=quest,
                        supplement=supplement,
                        name=GIRL_NAMES[0],
                        gender="girl",
                        trait=TRAITS[0],
                    )
                    samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
