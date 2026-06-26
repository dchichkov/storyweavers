#!/usr/bin/env python3
"""
A standalone storyworld for a tiny camp detective tale with moral values and dialogue.

Premise:
- At camp, a child detective notices a small problem: something important is missing.
- The search is driven by clues, questions, and honest dialogue.
- The moral turn comes from a value choice: telling the truth, sharing, apologizing, or helping.
- The ending proves what changed in the world: the item is found, trust rises, and the camp feels better.

This script follows the Storyweavers storyworld contract:
- stdlib-only core
- shared results containers imported eagerly
- lazy ASP helper import inside ASP helpers
- typed world entities with meters and memes
- state-driven prose, QA, trace, JSON, ASP, verify, show-asp support
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
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class CampSetting:
    place: str
    clue_place: str
    moral_topic: str
    affords: set[str]


@dataclass(frozen=True)
class Mystery:
    id: str
    missing_item: str
    item_phrase: str
    item_type: str
    hide_place: str
    clue: str
    action: str
    dialogue_prompt: str
    moral_value: str
    turn_reason: str
    resolution_line: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: CampSetting) -> None:
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


def _r_trust(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes.get("truth", 0) >= THRESHOLD and not e.found:
            sig = ("truth_trust", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["trust"] = e.memes.get("trust", 0) + 1
            out.append(f"That made the camp trust {e.id} a little more.")
    return out


CAUSAL_RULES = [("trust", _r_trust)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_setting_registry() -> dict[str, CampSetting]:
    return {
        "pine": CampSetting(
            place="Pine Camp",
            clue_place="the canoe dock",
            moral_topic="honesty",
            affords={"lost_compass", "lost_whistle", "missing_map"},
        ),
        "lake": CampSetting(
            place="Lake Camp",
            clue_place="the snack table",
            moral_topic="kindness",
            affords={"lost_compass", "missing_map"},
        ),
        "trail": CampSetting(
            place="Trail Camp",
            clue_place="the message board",
            moral_topic="helping",
            affords={"lost_whistle", "missing_map"},
        ),
    }


def build_mystery_registry() -> dict[str, Mystery]:
    return {
        "lost_compass": Mystery(
            id="lost_compass",
            missing_item="compass",
            item_phrase="a small brass compass",
            item_type="compass",
            hide_place="a pine stump near the canoe dock",
            clue="a muddy boot print pointed toward the docks",
            action="search the dock path",
            dialogue_prompt="where the compass might have rolled",
            moral_value="honesty",
            turn_reason="someone admitted they borrowed it for a map game",
            resolution_line="The compass was back in the pouch, and everyone could read north again.",
        ),
        "lost_whistle": Mystery(
            id="lost_whistle",
            missing_item="whistle",
            item_phrase="a bright red whistle",
            item_type="whistle",
            hide_place="under the snack blanket",
            clue="a crumb trail led under the table",
            action="check the snack area",
            dialogue_prompt="who had been near the snacks",
            moral_value="kindness",
            turn_reason="a younger camper confessed he hid it to keep it safe and was worried to speak up",
            resolution_line="The whistle hung on its string again, and the younger camper felt relieved.",
        ),
        "missing_map": Mystery(
            id="missing_map",
            missing_item="map",
            item_phrase="the camp map with blue crayon trails",
            item_type="map",
            hide_place="pinned behind the message board",
            clue="a corner of blue crayon showed near the board",
            action="look at the notice wall",
            dialogue_prompt="who had tried to help",
            moral_value="helping",
            turn_reason="a friend explained they moved it so rain would not soak it",
            resolution_line="The map dried flat in the cabin, and the campers knew the trail again.",
        ),
    }


SETTINGS = build_setting_registry()
MYSTERIES = build_mystery_registry()

GIRL_NAMES = ["Maya", "Lina", "Sofia", "Nora", "Ivy", "Ruby", "Leah"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Owen", "Theo", "Ben", "Jude"]
TRAITS = ["curious", "careful", "brave", "quiet", "sharp-eyed", "steady"]
MENTORS = ["counselor", "camp leader", "guide"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for m_id in setting.affords:
            combos.append((s_id, m_id))
    return combos


def reasonableness_gate(setting: CampSetting, mystery: Mystery) -> bool:
    return mystery.id in setting.affords


def explain_rejection(setting: CampSetting, mystery: Mystery) -> str:
    return (
        f"(No story: {setting.place} does not support this mystery. "
        f"The clue, action, and resolution would not fit the camp layout.)"
    )


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def introduce(world: World, detective: Entity, mentor: Entity, mystery: Mystery) -> None:
    world.say(
        f"At {world.setting.place}, {detective.id} was known as a little {next(t for t in detective.memes if t == 'trait')} detective?"
    )


def tell_story(world: World, detective: Entity, mentor: Entity, clue_item: Entity, mystery: Mystery) -> None:
    world.say(
        f"At {world.setting.place}, {detective.id} was a sharp-eyed little detective who noticed small things first."
    )
    world.say(
        f"{detective.pronoun().capitalize()} loved camp mornings, when the air smelled like pine and the path felt full of secrets."
    )
    world.say(
        f"One day, {detective.id}'s {mentor.type} said, \"We need to find {clue_item.phrase}.\""
    )
    world.say(
        f"{detective.id} said, \"I'll look. I know how to follow clues.\""
    )

    world.para()
    world.say(
        f"{detective.id} walked to {world.setting.clue_place}, because the first clue said {mystery.clue}."
    )
    world.say(
        f"{detective.id} asked, \"Did anyone see {clue_item.label}?\""
    )
    world.say(
        f"A small voice answered, \"I saw something near {mystery.hide_place}.\""
    )
    world.say(
        f"{detective.id} looked again and said, \"That clue is right. We should ask the truth.\""
    )

    world.para()
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    detective.memes["doubt"] = detective.memes.get("doubt", 0) + 1
    world.say(
        f"Then {detective.id} found a friend who looked worried and asked, \"Was it you?\""
    )
    world.say(
        f"The friend whispered, \"Yes. I moved it {mystery.turn_reason}.\""
    )
    detective.memes["truth"] = detective.memes.get("truth", 0) + 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{detective.id} said, \"Thank you for telling me.\""
    )
    world.say(
        f"{mentor.id} nodded and said, \"A brave truth helps more than a hidden worry.\""
    )
    world.say(mystery.resolution_line)
    detective.memes["pride"] = detective.memes.get("pride", 0) + 1
    detective.meters["found"] = detective.meters.get("found", 0) + 1
    clue_item.found = True


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait": 1.0},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=params.mentor,
        label=f"the {params.mentor}",
    ))
    clue_item = world.add(Entity(
        id="MissingItem",
        type=mystery.item_type,
        label=mystery.missing_item,
        phrase=mystery.item_phrase,
        hidden=True,
    ))
    world.facts.update(
        detective=detective,
        mentor=mentor,
        clue_item=clue_item,
        mystery=mystery,
        setting=setting,
    )
    tell_story(world, detective, mentor, clue_item, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short camp detective story with dialogue and a moral about {f["mystery"].moral_value}.',
        f"Tell a child-friendly mystery at {f['setting'].place} where {f['detective'].id} follows clues and learns something honest.",
        f'Write a simple detective tale that includes camp, a missing item, and a kind conversation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    mentor: Entity = f["mentor"]
    mystery: Mystery = f["mystery"]
    setting: CampSetting = f["setting"]
    return [
        QAItem(
            question=f"Where does the detective story happen?",
            answer=f"It happens at {setting.place}, a camp place with clues and quiet paths.",
        ),
        QAItem(
            question=f"What item was missing in the story?",
            answer=f"The missing item was {mystery.item_phrase}.",
        ),
        QAItem(
            question=f"What clue helped {detective.id} start solving the mystery?",
            answer=f"The clue was that {mystery.clue}.",
        ),
        QAItem(
            question=f"What did {detective.id} ask before finding out the truth?",
            answer=f"{detective.id} asked who had seen the missing item and listened carefully for the answer.",
        ),
        QAItem(
            question=f"How did the mentor respond after the truth came out?",
            answer=f"The {mentor.type} said that a brave truth helps more than a hidden worry.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The missing item was found, the truth was shared, and the camp felt calmer and safer.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "honesty": (
        "What is honesty?",
        "Honesty means telling the truth, even when it feels a little hard.",
    ),
    "kindness": (
        "What is kindness?",
        "Kindness means caring about others and trying to help them feel better.",
    ),
    "helping": (
        "What does it mean to help someone?",
        "Helping means doing something useful so another person can finish a job or feel supported.",
    ),
    "camp": (
        "What is a camp?",
        "A camp is a place where people stay, play, learn, and spend time together outdoors.",
    ),
    "clue": (
        "What is a clue?",
        "A clue is a little piece of information that helps you solve a mystery.",
    ),
    "dialogue": (
        "What is dialogue?",
        "Dialogue is when characters talk to each other in a story.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    keys = {"camp", "clue", "dialogue", f["mystery"].moral_value}
    return [QAItem(question=WORLD_KNOWLEDGE[k][0], answer=WORLD_KNOWLEDGE[k][1]) for k in WORLD_KNOWLEDGE if k in keys]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
setting_valid(S,M) :- setting(S), mystery(M), affords(S,M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, m))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting_valid/2."))
    return sorted(set(asp.atoms(model, "setting_valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Camp detective storyworld with moral dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["counselor", "camp leader", "guide"])
    ap.add_argument("--trait", choices=TRAITS if "TRAITS" in globals() else ["curious", "careful", "brave", "quiet", "sharp-eyed", "steady"])
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


TRAITS = ["curious", "careful", "brave", "quiet", "sharp-eyed", "steady"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.mystery:
        s = SETTINGS[args.setting]
        m = MYSTERIES[args.mystery]
        if not reasonableness_gate(s, m):
            raise StoryError(explain_rejection(s, m))
    filtered = [
        (s, m) for s, m in combos
        if (args.setting is None or s == args.setting)
        and (args.mystery is None or m == args.mystery)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(filtered)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    mentor = args.mentor or rng.choice(MENTORS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        name=name,
        gender=gender,
        mentor=mentor,
        trait=trait,
    )


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
    StoryParams(setting="pine", mystery="lost_compass", name="Maya", gender="girl", mentor="counselor", trait="sharp-eyed"),
    StoryParams(setting="lake", mystery="lost_compass", name="Eli", gender="boy", mentor="camp leader", trait="curious"),
    StoryParams(setting="trail", mystery="lost_whistle", name="Nora", gender="girl", mentor="guide", trait="steady"),
    StoryParams(setting="lake", mystery="missing_map", name="Finn", gender="boy", mentor="counselor", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_valid_combos()
        print(f"{len(items)} valid setting/mystery pairs:\n")
        for s, m in items:
            print(f"  {s:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
