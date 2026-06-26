#!/usr/bin/env python3
"""
Standalone Storyworld: granpa quest twist pirate tale.

A tiny pirate-style simulation where a child and granpa set out on a quest,
face a twist, and finish with a clear changed ending image.
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather", "granpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    cause: str
    fix: str
    turns: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    risky_for: set[str] = field(default_factory=set)  # quest ids
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.weather: str = ""
        self.twist_hit: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# World content
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting("the harbor", {"quest", "twist"}),
    "island": Setting("the island", {"quest", "twist"}),
    "cove": Setting("the cove", {"quest", "twist"}),
    "ship": Setting("the little ship", {"quest", "twist"}),
}

QUESTS = {
    "treasure": Quest(
        id="treasure",
        goal="find the buried treasure chest",
        verb="find the treasure chest",
        gerund="searching for the treasure chest",
        rush="rush toward the old oak",
        keyword="treasure",
        tags={"treasure", "gold", "map"},
    ),
    "shell": Quest(
        id="shell",
        goal="bring home a shining shell from the shore",
        verb="find the shining shell",
        gerund="gathering shells",
        rush="dash to the waterline",
        keyword="shell",
        tags={"shell", "beach"},
    ),
    "flag": Quest(
        id="flag",
        goal="raise the missing pirate flag",
        verb="raise the pirate flag",
        gerund="hoisting the pirate flag",
        rush="climb the mast",
        keyword="flag",
        tags={"flag", "mast", "rope"},
    ),
}

TWISTS = {
    "storm": Twist(
        id="storm",
        label="a storm twist",
        cause="a dark cloud rolled in and the sea began to splash hard",
        fix="a lantern and a stout rope",
        turns={"wet", "dark", "wind"},
    ),
    "fog": Twist(
        id="fog",
        label="a fog twist",
        cause="a pale fog slid over the water and made the path hard to see",
        fix="a compass and a bright lantern",
        turns={"dark", "lost", "mist"},
    ),
    "sneaky": Twist(
        id="sneaky",
        label="a sneaky twist",
        cause="the map fluttered loose and the wind tried to steal it away",
        fix="a clamp and a careful hand",
        turns={"lost", "wind", "paper"},
    ),
}

ARTIFACTS = {
    "map": Artifact("map", "map", "a creased map with a blue X", "torso", {"treasure"}),
    "boots": Artifact("boots", "boots", "sturdy boots", "feet", {"storm", "fog"}, plural=True),
    "cloak": Artifact("cloak", "cloak", "a dark cloak", "torso", {"fog"}),
    "lantern": Artifact("lantern", "lantern", "a bright lantern", "hand", {"storm", "fog", "sneaky"}),
    "rope": Artifact("rope", "rope", "a coil of rope", "hand", {"storm", "sneaky"}, plural=False),
    "compass": Artifact("compass", "compass", "a small compass", "hand", {"fog"}),
    "clamp": Artifact("clamp", "clamp", "a brass clamp", "hand", {"sneaky"}),
}

GRENADES = ["grandfather", "granpa"]  # keep granpa in the script vocabulary
NAMES = ["Nina", "Lio", "Milo", "Tia", "Pip", "Arlo", "Mara", "Jace"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def quest_at_risk(quest: Quest, twist: Twist) -> bool:
    return bool(quest.tags & twist.turns)


def select_fix(quest: Quest, twist: Twist) -> Optional[list[Artifact]]:
    picks: list[Artifact] = []
    if twist.id == "storm" and quest.id == "treasure":
        picks = [ARTIFACTS["boots"], ARTIFACTS["lantern"], ARTIFACTS["rope"]]
    elif twist.id == "fog" and quest.id in {"treasure", "flag"}:
        picks = [ARTIFACTS["compass"], ARTIFACTS["lantern"]]
    elif twist.id == "sneaky" and quest.id == "treasure":
        picks = [ARTIFACTS["clamp"], ARTIFACTS["map"]]
    return picks or None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            if qid not in setting.affords:
                continue
            for tid, twist in TWISTS.items():
                if quest_at_risk(quest, twist) and select_fix(quest, twist):
                    out.append((place, qid, tid))
    return out


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(place: str, quest_id: str, twist_id: str, name: str, seed: Optional[int] = None) -> World:
    setting = SETTINGS[place]
    quest = QUESTS[quest_id]
    twist = TWISTS[twist_id]
    world = World(setting)
    world.weather = twist.id

    child = world.add(Entity(id=name, kind="character", type="boy", label=name))
    granpa = world.add(Entity(id="Granpa", kind="character", type="granpa", label="Granpa"))
    map_item = world.add(Entity(id="Map", type="map", label="map", phrase=ARTIFACTS["map"].phrase,
                                owner=child.id, caretaker=granpa.id))
    world.add(Entity(id="QuestGear", type="gear", label="gear"))

    # Setup
    world.say(f"{child.id} was a small pirate who loved {quest.gerund}.")
    world.say(f"Granpa smiled beside {child.id} and brought out {map_item.phrase}.")
    world.say(f"They had a quest to {quest.goal} at {setting.place}.")

    # Middle turn
    world.say(f"One day, they sailed to {setting.place}.")
    world.say(f"{child.id} wanted to {quest.verb} right away.")
    world.say(f"But then {twist.cause}.")

    # World-state effects
    child.memes["eager"] = child.memes.get("eager", 0) + 1
    child.memes["concern"] = child.memes.get("concern", 0) + 1
    child.meters["distance"] = child.meters.get("distance", 0) + 1
    world.twist_hit = True
    world.facts["quest"] = quest
    world.facts["twist"] = twist
    world.facts["child"] = child
    world.facts["granpa"] = granpa
    world.facts["map"] = map_item
    world.facts["seed"] = seed
    world.facts["place"] = place

    fix = select_fix(quest, twist)
    if not fix:
        raise StoryError("No reasonable fix exists for this quest and twist.")

    if twist.id == "storm":
        world.say(f"Granpa tied the {fix[2].label} and lit the {fix[1].label}.")
        world.say(f"The {fix[0].label} kept {child.id}'s feet dry while they kept going.")
    elif twist.id == "fog":
        world.say(f"Granpa held up the {fix[1].label} and checked the {fix[0].label}.")
        world.say(f"The bright beam and the little needle pointed them toward the shore.")
    else:  # sneaky
        world.say(f"Granpa snapped the {fix[0].label} onto the {map_item.label}.")
        world.say(f"The map stayed put, and the wind could not steal their clue.")

    child.memes["joy"] = child.memes.get("joy", 0) + 1
    granpa.memes["pride"] = granpa.memes.get("pride", 0) + 1

    # Resolution
    world.say(f"They followed the clue until the treasure, shell, or flag was found at last.")
    if quest.id == "treasure":
        world.say(f"At the end, {child.id} lifted a tiny chest from the sand, and Granpa laughed softly beside the waves.")
    elif quest.id == "shell":
        world.say(f"At the end, {child.id} found a shining shell in the foam, and Granpa tucked it safely into his pocket.")
    else:
        world.say(f"At the end, {child.id} raised the pirate flag high, and it snapped bright in the wind.")

    world.say(f"The trip started as a quest, changed with a twist, and ended with {child.id} and Granpa smiling like real shipmates.")
    world.facts["fix"] = fix
    return world


# ---------------------------------------------------------------------------
# Parameterization
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    twist: str
    name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="harbor", quest="treasure", twist="storm", name="Milo"),
    StoryParams(place="island", quest="treasure", twist="fog", name="Pip"),
    StoryParams(place="cove", quest="treasure", twist="sneaky", name="Nina"),
]


def explain_rejection(quest: Quest, twist: Twist) -> str:
    return (
        f"(No story: this quest and twist do not make a reasonable pirate tale. "
        f"Try a quest whose clues can truly be helped by the twist's fix.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.twist:
        q, t = QUESTS[args.quest], TWISTS[args.twist]
        if not (quest_at_risk(q, t) and select_fix(q, t)):
            raise StoryError(explain_rejection(q, t))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest, twist = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, quest=quest, twist=twist, name=name, seed=args.seed)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    t = world.facts["twist"]
    child = world.facts["child"]
    return [
        f'Write a short pirate tale for a young child about {child.id}, Granpa, a quest, and {t.label}.',
        f"Tell a child-friendly pirate story where someone tries to {q.verb} but a twist changes the plan.",
        f'Write a tiny adventure story that uses the word "{q.keyword}" and ends with Granpa helping the crew finish the quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    t = world.facts["twist"]
    child = world.facts["child"]
    granpa = world.facts["granpa"]
    fix = world.facts["fix"]
    out = [
        QAItem(
            question=f"Who went on the pirate quest with {child.id}?",
            answer=f"{child.id} went with Granpa, and they sailed together like a tiny pirate crew.",
        ),
        QAItem(
            question=f"What was the quest they wanted to finish at {world.setting.place}?",
            answer=f"They wanted to {q.verb} after sailing to {world.setting.place}.",
        ),
        QAItem(
            question=f"What twist changed the plan during the trip?",
            answer=f"{t.cause.capitalize()}. That was the twist that made the quest harder for a moment.",
        ),
        QAItem(
            question=f"How did Granpa help once the twist appeared?",
            answer=f"Granpa used {', '.join(a.label for a in fix)} so they could keep going and finish the quest safely.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate map for?",
            answer="A pirate map shows where to look for something hidden, like treasure or a secret place.",
        ),
        QAItem(
            question="Why do sailors tie things down when the wind is strong?",
            answer="They tie things down so the wind cannot blow them away from the boat or the deck.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_at_risk(Q,T) :- quest(Q), twist(T), quest_tag(Q,K), twist_turn(T,K).
compatible(Q,T) :- quest_at_risk(Q,T), fix(Q,T).
valid(Place,Q,T) :- affords(Place,Q), compatible(Q,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for tag in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, tag))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        for turn in sorted(t.turns):
            lines.append(asp.fact("twist_turn", tid, turn))
        if select_fix(QUESTS["treasure"], t) is not None:
            lines.append(asp.fact("fix", "treasure", tid))
        if select_fix(QUESTS["flag"], t) is not None:
            lines.append(asp.fact("fix", "flag", tid))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with granpa, quest, and twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--twist", choices=TWISTS)
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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params.place, params.quest, params.twist, params.name, params.seed)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  place={world.setting.place}")
    lines.append(f"  twist_hit={world.twist_hit}")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible (place, quest, twist) combos:")
        for x in models:
            print(" ", x)
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
            header = f"### {p.name}: {p.quest} at {p.place} with {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
