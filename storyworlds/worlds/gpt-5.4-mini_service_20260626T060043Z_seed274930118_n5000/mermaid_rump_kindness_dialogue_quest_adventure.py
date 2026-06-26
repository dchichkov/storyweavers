#!/usr/bin/env python3
"""
storyworlds/worlds/mermaid_rump_kindness_dialogue_quest_adventure.py
====================================================================

A small storyworld about a mermaid on a kindness-filled quest, told in an
adventure style with dialogue and a gentle turn toward help.

Premise:
- A young mermaid wants to finish a quest in a bright sea setting.
- Something awkward or embarrassing about her rump makes the journey hard.

Tension:
- The mermaid worries about getting stuck, splashed, or laughed at.
- A companion or helpful sea creature speaks kindly and offers a better plan.

Turn:
- Kind words and a practical choice help the mermaid keep going.

Resolution:
- The quest succeeds, and the ending image proves the change in state:
  courage up, worry down, progress made, and the rump no longer the focus.

This file is self-contained and follows the Storyweavers world contract.
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

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mermaid"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the coral cove"
    style: str = "Adventure"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    gerund: str
    obstacle: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    keeps: set[str]
    offer: str
    tail: str


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "coral_cove": Setting(place="the coral cove", style="Adventure", affords={"quest_swim", "search"}),
    "star_shelf": Setting(place="the star shelf", style="Adventure", affords={"quest_swim", "search"}),
    "moon_grotto": Setting(place="the moon grotto", style="Adventure", affords={"quest_swim", "search"}),
}

QUESTS = {
    "pearl_map": Quest(
        id="pearl_map",
        goal="find the pearl map",
        gerund="following the pearl map trail",
        obstacle="a snag of kelp and a sharp rock",
        risk="scraping her rump on the rock",
        keyword="quest",
        tags={"quest", "map", "pearl"},
    ),
    "lost_shell_bell": Quest(
        id="lost_shell_bell",
        goal="bring back the lost shell bell",
        gerund="searching for the shell bell",
        obstacle="a narrow tunnel and a fussy tide",
        risk="bumping her rump on the tunnel wall",
        keyword="quest",
        tags={"quest", "shell", "bell"},
    ),
    "glimmer_key": Quest(
        id="glimmer_key",
        goal="recover the glimmer key",
        gerund="diving for the glimmer key",
        obstacle="a whirl of bubbles and a tangled net",
        risk="getting her rump caught in the net",
        keyword="quest",
        tags={"quest", "key", "glimmer"},
    ),
}

AIDS = [
    Aid(
        id="soft_shell",
        label="a soft shell cushion",
        phrase="a soft shell cushion",
        helps={"scratch", "hit"},
        keeps={"rump"},
        offer="slip onto a soft shell cushion first",
        tail="swam on with the soft shell cushion tucked safely behind her",
    ),
    Aid(
        id="wide_tail_sash",
        label="a wide tail sash",
        phrase="a wide tail sash",
        helps={"net", "kelp"},
        keeps={"rump"},
        offer="wrap a wide tail sash around the lower waves",
        tail="glided ahead with the wide tail sash making room for her",
    ),
    Aid(
        id="brave_shell_boots",
        label="brave shell boots",
        phrase="brave shell boots",
        helps={"rock", "tunnel"},
        keeps={"feet", "tail"},
        offer="put on brave shell boots before the climb",
        tail="kept going with brave shell boots flashing in the water",
    ),
]

MERMAID_NAMES = ["Nerina", "Mira", "Coral", "Luna", "Ariel", "Nessa", "Maris", "Pearl"]
HELPERS = ["dolphin", "turtle", "seahorse", "crab", "octopus"]
TRAITS = ["brave", "curious", "gentle", "lively", "steady", "cheerful"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def quest_at_risk(quest: Quest) -> bool:
    return True


def select_aid(quest: Quest) -> Optional[Aid]:
    if "rock" in quest.obstacle or "tunnel" in quest.obstacle:
        return AIDS[2]
    if "net" in quest.obstacle:
        return AIDS[1]
    return AIDS[0]


def explain_rejection() -> str:
    return "(No story: the chosen quest does not create a clear enough danger and kindness turn.)"


def build_story_name(name: str, helper: str, trait: str) -> str:
    return f"{trait.capitalize()} {name} and the {helper}"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def run_world(setting: Setting, quest: Quest, hero_name: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="mermaid", traits=["young", trait]))
    helper = world.add(Entity(id=helper_kind, kind="character", type=helper_kind))
    prize = world.add(Entity(
        id="quest_item",
        kind="thing",
        type="thing",
        label=quest.goal,
        phrase=quest.goal,
        owner=hero.id,
        caretaker=hero.id,
        location=setting.place,
    ))

    hero.memes["hope"] = 1
    hero.memes["worry"] = 0
    helper.memes["kindness"] = 1

    world.say(f"{hero.id} was a {trait} mermaid who loved adventure beneath the waves.")
    world.say(f"She had a big {quest.keyword} to {quest.goal}, and the sea shimmered like a promise.")
    world.say(f"At {setting.place}, {hero.id} looked at the water and knew the day would matter.")

    world.para()
    hero.memes["desire"] = 1
    world.say(f"{hero.id} wanted to {quest.gerund}, but {quest.obstacle} waited ahead.")
    world.say(f"If she rushed too fast, {quest.risk}.")
    hero.memes["worry"] = 1
    world.say(f"She pressed a hand to her fin and whispered, 'I can do this, but I need a little help.'")

    aid = select_aid(quest)
    if aid is None:
        raise StoryError(explain_rejection())

    world.para()
    world.say(f"A {helper_kind} drifted near and said, 'I know a kinder way.'")
    world.say(f"'{aid.offer},' the {helper_kind} said, and {hero.id} listened.")
    world.say(f"{hero.id} smiled at the gentle plan, because kindness made the path feel wider.")
    hero.memes["kindness"] = 1
    hero.memes["worry"] = 0
    hero.memes["courage"] = 1
    world.add(Entity(id="aid", kind="thing", type="aid", label=aid.label, phrase=aid.phrase, worn_by=hero.id))

    world.para()
    world.say(f"{hero.id} took the safer route and kept moving toward the prize.")
    world.say(f"{aid.tail}.")
    world.say(f"At last, she reached the place where the {quest.goal} waited, bright as a starfish.")
    world.say(f"{hero.id} held it high, and the water around her seemed to cheer.")
    world.say(f"The little worry about her rump was gone now, replaced by brave, happy swimming.")

    world.facts.update(
        hero=hero,
        helper=helper,
        quest=quest,
        aid=aid,
        setting=setting,
        prize=prize,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "mermaid": [
        ("What is a mermaid?", "A mermaid is a magical sea creature with a human upper body and a fish tail."),
    ],
    "quest": [
        ("What is a quest?", "A quest is a journey where someone tries to find something, solve a problem, or do a brave task."),
    ],
    "kindness": [
        ("What is kindness?", "Kindness means being gentle, helpful, and caring to someone else."),
    ],
    "dialogue": [
        ("What is dialogue?", "Dialogue is when characters talk to each other in a story."),
    ],
    "adventure": [
        ("What makes an adventure exciting?", "An adventure feels exciting when a character travels, faces a challenge, and keeps going with courage."),
    ],
    "rump": [
        ("What is a rump?", "A rump is the back part of an animal or person, near the bottom."),
    ],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Adventure story for a child about a mermaid and a {f["quest"].keyword} that includes kind dialogue.',
        f"Tell a gentle sea adventure where {f['hero'].id} wants to {f['quest'].goal} but needs help with her rump.",
        f'Write a story set at {f["setting"].place} where a mermaid hears a kind voice and keeps going on her quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    aid = f["aid"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a young mermaid who goes on an adventure at {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.goal} on her quest.",
        ),
        QAItem(
            question=f"Why did {hero.id} need help?",
            answer=f"She needed help because the path had {quest.obstacle}, and she did not want to hurt her rump.",
        ),
        QAItem(
            question=f"Who spoke kindly to {hero.id}?",
            answer=f"The {helper.type} spoke kindly to her and offered {aid.phrase}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} succeeding on the quest and feeling brave and happy instead of worried.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    tags.add("mermaid")
    tags.add("kindness")
    tags.add("dialogue")
    tags.add("adventure")
    tags.add("rump")
    out: list[QAItem] = []
    for tag, qas in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in qas)
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_ready(H,Q) :- hero(H), quest(Q), obstacle(Q,O), risk(Q,R), O != "", R != "".
kind_turn(H,Q) :- hero(H), quest(Q), help(A), helpful(A,Q).
story_ok(H,Q) :- quest_ready(H,Q), kind_turn(H,Q).
#show story_ok/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
        lines.append(asp.fact("obstacle", qid, q.obstacle))
        lines.append(asp.fact("risk", qid, q.risk))
    for aid in AIDS:
        lines.append(asp.fact("help", aid.id))
        for tag in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, tag))
        lines.append(asp.fact("helpful", aid.id, "pearl_map"))
        lines.append(asp.fact("helpful", aid.id, "lost_shell_bell"))
        lines.append(asp.fact("helpful", aid.id, "glimmer_key"))
    lines.append(asp.fact("hero", "mermaid"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = {("mermaid", qid) for qid in QUESTS}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python reasonableness ({len(asp_set)} quests).")
        return 0
    print("MISMATCH between clingo and Python:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mermaid adventure about kindness, dialogue, and questing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", choices=MERMAID_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    name = args.name or rng.choice(MERMAID_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = run_world(SETTINGS[params.setting], QUESTS[params.quest], params.name, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        pairs = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(pairs)} compatible story cores:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for quest in QUESTS:
                p = StoryParams(setting=setting, quest=quest, name="Nerina", helper="dolphin", trait="brave")
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
