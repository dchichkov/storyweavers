#!/usr/bin/env python3
"""
A small folk-tale story world about a chicken, a rhino, dusk, friendship, and a quest.

The seed image:
- A chicken and a rhino begin apart in the late light of dusk.
- A quest creates a need for help, and friendship turns into a practical, emotional change.
- The world should feel like a folk tale: concrete, gentle, and a little ceremonial.

This script simulates a tiny world where:
- the chicken and rhino each have physical meters and emotional memes,
- dusk changes the setting and raises the need for safe travel,
- a quest can only be completed if the two become friends and share the work,
- their friendship grows by helping one another through a risky crossing.

The story is generated from state changes, not from a frozen template.
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
# World data
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chicken"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"rhino"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lantern path"
    mood: str = "dusk"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    need: str
    risk: str
    route: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    action: str
    effect: str
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.quest_progress: float = 0.0
        self.shared_path: bool = False
        self.dusk_deepened: bool = False

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.quest_progress = self.quest_progress
        clone.shared_path = self.shared_path
        clone.dusk_deepened = self.dusk_deepened
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    helper: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lantern_path": Setting(place="the lantern path", mood="dusk", affords={"crossing", "listening"}),
    "old_bridge": Setting(place="the old bridge", mood="dusk", affords={"crossing", "listening"}),
    "hill_gate": Setting(place="the hill gate", mood="dusk", affords={"listening", "waiting"}),
}

QUESTS = {
    "berries": Quest(
        id="berries",
        title="the quest for moon-berries",
        need="find moon-berries before the stars wake fully",
        risk="the path grows dim and lonely",
        route="follow the narrow path past the reeds",
        reward="a bowl of bright moon-berries for the nest",
        tags={"friendship", "quest", "berries"},
    ),
    "bell": Quest(
        id="bell",
        title="the quest for the lost bell",
        need="bring back the little bell that rang in the village square",
        risk="the bell lies near a shadowed stream at dusk",
        route="walk together to the stream and listen for the sound",
        reward="the bell, shining safe and sound",
        tags={"friendship", "quest", "bell"},
    ),
    "lantern": Quest(
        id="lantern",
        title="the quest for the fallen lantern",
        need="recover the fallen lantern before the dark settles in",
        risk="the lantern sits beyond a muddy dip",
        route="cross the muddy dip one careful step at a time",
        reward="the lantern lit again",
        tags={"friendship", "quest", "lantern"},
    ),
}

HELPERS = {
    "rope": Helper(
        id="rope",
        label="a braided rope",
        action="tie a safe loop and guide the crossing",
        effect="keeps the little travelers steady",
        covers={"crossing"},
    ),
    "lantern": Helper(
        id="lantern_helper",
        label="a warm lantern",
        action="shine a bright path through the dusk",
        effect="pushes the shadows back from the trail",
        covers={"listening", "crossing"},
    ),
    "song": Helper(
        id="song",
        label="a low folk song",
        action="keep fear small and courage near",
        effect="helps the heart keep time with the steps",
        covers={"listening"},
    ),
}

NAMES = ["Mina", "Luna", "Pip", "Ada", "Nell", "June", "Tess", "Wren"]
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def protagonist_line(hero: Entity) -> str:
    return f"{hero.id} was a little {hero.type} with a bright eye and a patient heart."


def friendship_line(hero: Entity, other: Entity) -> str:
    return f"{hero.pronoun().capitalize()} liked {other.id}, even before the two of them spoke."


def quest_line(hero: Entity, quest: Quest) -> str:
    return f"One evening, {hero.id} heard of {quest.title}."


def dusk_line(setting: Setting) -> str:
    return f"The day was turning to dusk at {setting.place}, and the air grew cool and blue."


def need_line(hero: Entity, quest: Quest) -> str:
    return f"{hero.id} wanted to {quest.need}, but the way ahead asked for care."


def helper_line(helper: Helper) -> str:
    return f"Then they found {helper.label}, which could {helper.action}."


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def can_share_path(world: World, helper: Helper) -> bool:
    return "crossing" in helper.covers or "listening" in helper.covers


def predict_danger(world: World, quest: Quest) -> bool:
    sim = world.copy()
    sim.quest_progress += 0.5
    return quest.risk != ""


def begin_quest(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    friend.memes["quiet_strength"] = friend.memes.get("quiet_strength", 0.0) + 1
    world.say(protagonist_line(hero))
    world.say(friendship_line(hero, friend))
    world.say(quest_line(hero, quest))


def arrive_at_dusk(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    world.para()
    world.say(dusk_line(world.setting))
    world.say(need_line(hero, quest))
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    friend.memes["readiness"] = friend.memes.get("readiness", 0.0) + 1
    world.facts["risk"] = quest.risk


def ask_for_help(world: World, hero: Entity, friend: Entity, helper: Helper) -> None:
    if helper.id == "rope":
        world.say(f"{hero.id} looked at {friend.id} and asked for help.")
    elif helper.id == "lantern_helper":
        world.say(f"{hero.id} and {friend.id} paused until a warm lantern was lit.")
    else:
        world.say(f"{hero.id} and {friend.id} hummed a low song to gather their courage.")
    world.say(helper_line(helper))
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1


def cross_together(world: World, hero: Entity, friend: Entity, quest: Quest, helper: Helper) -> None:
    world.para()
    if not can_share_path(world, helper):
        raise StoryError("The helper does not support the kind of crossing this quest needs.")
    world.shared_path = True
    world.quest_progress += 1.0
    hero.meters["travel"] = hero.meters.get("travel", 0.0) + 1
    friend.meters["travel"] = friend.meters.get("travel", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"Together they went along {world.setting.place}, "
        f"with {helper.label} to {helper.effect}."
    )
    world.say(
        f"{hero.id} stepped first, and {friend.id} followed, and neither was left alone."
    )


def finish_quest(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    world.para()
    if world.quest_progress < THRESHOLD:
        raise StoryError("The quest has not been completed.")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.dusk_deepened = True
    world.say(
        f"At last they found {quest.reward}, and the little quest was done."
    )
    world.say(
        f"The chicken and the rhino looked at one another and smiled as if they had always been a team."
    )
    world.say(
        f"The dusk deepened, but now it seemed kind, because the path was shared and the treasure was safe."
    )


def tell(setting: Setting, quest: Quest, helper: Helper, name: str) -> World:
    world = World(setting)
    chicken = world.add(Entity(id=name, kind="character", type="chicken"))
    rhino = world.add(Entity(id="Rhino", kind="character", type="rhino"))
    world.add(Entity(id="helper", type=helper.id, label=helper.label))
    world.facts.update(hero=chicken, friend=rhino, quest=quest, helper=helper, setting=setting)

    begin_quest(world, chicken, rhino, quest)
    arrive_at_dusk(world, chicken, rhino, quest)
    ask_for_help(world, chicken, rhino, helper)
    cross_together(world, chicken, rhino, quest, helper)
    finish_quest(world, chicken, rhino, quest)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle folk tale about a chicken and a rhino who become friends at dusk.",
        f"Tell a short story where {f['hero'].id} and the rhino work together on {f['quest'].title}.",
        f"Write a child-friendly quest story set at {f['setting'].place} with friendship, dusk, and a helpful tool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    quest: Quest = f["quest"]
    helper: Helper = f["helper"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little chicken, and the rhino who became {hero.pronoun('possessive')} friend.",
        ),
        QAItem(
            question=f"What kind of tale was it?",
            answer=f"It was a folk tale about friendship and a quest at {setting.place} during dusk.",
        ),
        QAItem(
            question=f"What was the quest?",
            answer=f"The quest was to {quest.need}, and the answer came when they worked together.",
        ),
        QAItem(
            question=f"What helped them on the way?",
            answer=f"{helper.label.capitalize()} helped them because it could {helper.action}.",
        ),
        QAItem(
            question=f"How did the chicken and the rhino end the story?",
            answer=f"They finished the quest together and ended as close friends, with the path safe under the deepening dusk.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dusk?",
            answer="Dusk is the time when day is ending and the light grows soft and dim before night.",
        ),
        QAItem(
            question="Why do friends help each other on a quest?",
            answer="Friends help each other so the hard parts feel smaller and the journey can be done safely.",
        ),
        QAItem(
            question="Why is a lantern useful at dusk?",
            answer="A lantern gives a warm light that helps people see the path when the sun is gone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  quest_progress={world.quest_progress}")
    lines.append(f"  shared_path={world.shared_path}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- place(S).
character(chicken).
character(rhino).

quest_q(Q) :- quest(Q).

dusk_place(S) :- setting(S), dusk(S).

friendship_story(S, Q) :- setting(S), quest_q(Q), needs_friendship(Q).
successful(Q) :- friendship_story(_, Q), quest_q(Q).

#show valid/2.
valid(S, Q) :- setting(S), quest_q(Q), needs_friendship(Q).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting", pid))
        if SETTINGS[pid].mood == "dusk":
            lines.append(asp.fact("dusk", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs_friendship", qid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_pairs = {(p, q) for p in SETTINGS for q in QUESTS}
    asp_pairs = set(asp_valid_pairs())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches Python registry ({len(asp_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    if asp_pairs - python_pairs:
        print(" only in clingo:", sorted(asp_pairs - python_pairs))
    if python_pairs - asp_pairs:
        print(" only in python:", sorted(python_pairs - asp_pairs))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: chicken, dusk, rhino, friendship, and quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, quest=quest, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], HELPERS[params.helper], params.name)
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
    StoryParams(place="lantern_path", quest="berries", helper="lantern", name="Mina"),
    StoryParams(place="old_bridge", quest="bell", helper="rope", name="Pip"),
    StoryParams(place="hill_gate", quest="lantern", helper="song", name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (setting, quest) pairs:")
        for s, q in pairs:
            print(f"  {s:12} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.quest} at {p.place} via {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
