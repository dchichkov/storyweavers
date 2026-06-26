#!/usr/bin/env python3
"""
Standalone storyworld for a small Adventure-style tale set in a toy library.

Premise:
- A child explores a toy library.
- A folk magazine from the shelf triggers a flashback to an earlier clue.
- At o'clock time, the child uses that memory to find a missing toy and keep the magazine safe.

This world is intentionally narrow: one strong, child-facing story engine with
a concrete turn, a flashback, and a tidy resolution.
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
# Physical / emotional world model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the toy library"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    gear: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "toy_library": Setting(place="the toy library", affords={"search"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search the toy shelves",
        gerund="searching the toy shelves",
        rush="dash down the aisle",
        risk="dog-ear the magazine",
        keyword="o'clock",
        tags={"adventure", "flashback", "magazine", "folk", "o'clock"},
    ),
}

PRIZES = {
    "magazine": Prize(
        label="magazine",
        phrase="a folk magazine with bright paper drawings",
        type="magazine",
    ),
}

GEAR = {
    "sleeve": Gear(
        id="sleeve",
        label="a cardboard sleeve",
        prep="slip the magazine into a cardboard sleeve first",
        tail="slipped the magazine into the cardboard sleeve",
        protects={"magazine"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lily", "Ava", "Nora"],
    "boy": ["Theo", "Ben", "Finn", "Leo"],
}

TRAITS = ["curious", "brave", "lively", "bold"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [("toy_library", "search", "magazine")]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.type in {"magazine"} and activity.id == "search"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if prize.type in GEAR["sleeve"].protects and activity.id == "search":
        return GEAR["sleeve"]
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: this adventure works only when {prize.label} can be kept safe "
        f"with a sleeve during {activity.gerund}.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: try a different child gender for {prize_id}; {gender} was not supported.)"


def predict_mess(world: World, child: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(child.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"torn": prize.meters.get("torn", 0) >= THRESHOLD}


def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.meters["rushed"] = child.meters.get("rushed", 0) + 1
    if narrate:
        world.say(f"{child.id} loved {activity.gerund}.")
    prize = world.get("magazine")
    if prize.carried_by == child.id and "sleeve" not in world.facts.get("gear_ids", set()):
        prize.meters["torn"] = prize.meters.get("torn", 0) + 1


def trigger_flashback(world: World, child: Entity, prize: Entity) -> None:
    child.memes["memory"] = child.memes.get("memory", 0) + 1
    world.say(
        f'The folk pictures on the {prize.label} made {child.id} remember a flashback: '
        f'earlier, at {world.facts["o_clock"]} o\'clock, someone had traced the same map clue with a finger.'
    )
    world.facts["flashback"] = True


def arrive(world: World, child: Entity, companion: Entity, activity: Activity) -> None:
    world.say(
        f'At {world.facts["o_clock"]} o\'clock, {child.id} and {companion.label_word} went to {world.setting.place}.'
    )
    world.say("The toy library was full of little doors, soft rugs, and tiny shelves."


    )


def wants(world: World, child: Entity, activity: Activity) -> None:
    world.say(f"{child.id} wanted to {activity.verb} right away.")


def warn(world: World, companion: Entity, child: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f'"Careful," {companion.id} said. "If you {activity.verb}, you might {activity.risk}."'
    )


def defies(world: World, child: Entity, activity: Activity) -> None:
    child.memes["stubborn"] = child.memes.get("stubborn", 0) + 1
    world.say(f"{child.id} almost ran ahead, because the shelves looked like an adventure.")


def compromise(world: World, companion: Entity, child: Entity, prize: Entity, gear: Gear) -> None:
    world.say(
        f'{companion.id} smiled and said, "Let us {gear.prep}."'
    )
    prize.carried_by = child.id
    world.facts["gear_ids"] = {gear.id}
    world.say(f"They {gear.tail}.")


def resolve(world: World, child: Entity, companion: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"With the magazine safe, {child.id} followed the flashback clue past the puppet corner."
    )
    world.say(
        f"{child.id} found the missing toy boat tucked behind a stack of blocks, and the day felt like a real adventure."
    )
    world.say(
        f"At the end, the {prize.label} stayed smooth, and the toy library felt brighter than before."
    )
    child.memes["joy"] = child.memes.get("joy", 0) + 2
    child.memes["confidence"] = child.memes.get("confidence", 0) + 1
    world.facts["resolved"] = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, gear: Gear,
         hero_name: str, hero_type: str, companion_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_type, label="the helper"))
    prize = world.add(Entity(id="magazine", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    world.facts["o_clock"] = "six"
    world.facts["hero"] = child
    world.facts["companion"] = companion
    world.facts["prize"] = prize
    world.facts["activity"] = activity
    world.facts["gear"] = gear
    world.facts["setting"] = setting

    world.say(
        f"{child.id} was a little {random.choice(TRAITS)} {child.type} who loved surprises."
    )
    world.say(
        f"{child.id} found {prize_cfg.phrase} on a shelf, and the old folk pages felt like a secret."
    )
    world.para()
    arrive(world, child, companion, activity)
    wants(world, child, activity)
    warn(world, companion, child, prize, activity)
    defies(world, child, activity)
    trigger_flashback(world, child, prize)
    world.para()
    compromise(world, companion, child, prize, gear)
    _do_activity(world, child, activity, narrate=False)
    resolve(world, child, companion, activity, prize)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short adventure story in a toy library that includes the word "o\'clock".',
        'Tell a child-friendly story about folk magazine pages that cause a flashback and help solve a small problem.',
        f'Write a gentle adventure where {f["hero"].id} visits the toy library at {f["o_clock"]} o\'clock and keeps a magazine safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Where does {hero.id} go at {f['o_clock']} o'clock in the story?",
            answer=f"{hero.id} goes to the toy library with {companion.label_word}.",
        ),
        QAItem(
            question=f"What special thing does {hero.id} find there?",
            answer=f"{hero.id} finds {prize.phrase}, which is a folk magazine from the shelf.",
        ),
        QAItem(
            question=f"What does the folk magazine make {hero.id} remember?",
            answer="It makes the child remember a flashback to an earlier clue at o'clock time.",
        ),
        QAItem(
            question=f"How does the helper keep the magazine safe?",
            answer="The helper tells the child to slip the magazine into a cardboard sleeve first.",
        ),
        QAItem(
            question=f"What does the child find after following the flashback clue?",
            answer=f"{hero.id} finds the missing toy boat hidden behind a stack of blocks.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a magazine?",
            answer="A magazine is a thin book with pages full of pictures and stories.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What does o'clock tell you?",
            answer="O'clock tells you that a time is on the hour, like six o'clock.",
        ),
        QAItem(
            question="What is a toy library?",
            answer="A toy library is a place where children can look at, borrow, or discover toys and play things.",
        ),
        QAItem(
            question="What does a cardboard sleeve do?",
            answer="A cardboard sleeve helps protect paper pages from bending or tearing.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
valid(P,A,R) :- setting(P), activity(A), prize(R), affords(P,A), risky(A,R), fixable(A,R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for act in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in act.tags:
            lines.append(asp.fact("tag", aid, tag))
        lines.append(asp.fact("risky", aid, "magazine"))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("fixable", "search", rid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld set in a toy library.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gear", choices=GEAR.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Unsupported gender.")
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr) or select_gear(act, pr) is None:
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.prize == "magazine":
        pass
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(["mother", "father", "grandmother", "grandfather"])
    gear = args.gear or "sleeve"
    return StoryParams(place=place, activity=activity, prize=prize, gear=gear, name=name, gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        GEAR[params.gear],
        params.name,
        params.gender,
        params.companion,
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


CURATED = [
    StoryParams(place="toy_library", activity="search", prize="magazine", gear="sleeve", name="Mina", gender="girl", companion="grandmother"),
    StoryParams(place="toy_library", activity="search", prize="magazine", gear="sleeve", name="Theo", gender="boy", companion="father"),
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
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print(" ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
