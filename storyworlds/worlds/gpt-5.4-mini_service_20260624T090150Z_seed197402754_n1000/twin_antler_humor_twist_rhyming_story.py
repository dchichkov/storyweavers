#!/usr/bin/env python3
"""
storyworlds/worlds/twin_antler_humor_twist_rhyming_story.py
============================================================

A small storyworld about twins, a silly antler prop, and a rhyming twist.

Seed-tale idea:
---
Two twins loved to rhyme and play pretend. One day they found a pair of antlers
for a costume show. They planned a funny act, but the antlers were for the
wrong costume. After a quick twist, they turned the mix-up into a laugh and a
happy rhyme.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the fair"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------
SETTINGS = {
    "fair": Setting(place="the fair", affords={"rhymes", "play", "swap"}),
    "stage": Setting(place="the stage", affords={"rhymes", "play"}),
    "garden": Setting(place="the garden", affords={"rhymes", "play"}),
}

ACTIVITIES = {
    "rhymes": Activity(
        id="rhymes",
        verb="make up rhymes",
        gerund="making up rhymes",
        rush="dash to the stage",
        mess="splatters",
        soil="out of step",
        zone={"mouth", "hands"},
        keyword="rhyme",
        tags={"humor", "twist"},
    ),
    "play": Activity(
        id="play",
        verb="play pretend",
        gerund="playing pretend",
        rush="run to the props",
        mess="wiggles",
        soil="a noisy muddle",
        zone={"hands", "feet"},
        keyword="pretend",
        tags={"humor"},
    ),
    "swap": Activity(
        id="swap",
        verb="swap costume parts",
        gerund="swapping costume parts",
        rush="hurry to the costume box",
        mess="mixups",
        soil="all mixed up",
        zone={"hands"},
        keyword="swap",
        tags={"twist", "humor"},
    ),
}

PRIZES = {
    "bellhat": Prize(
        label="bell hat",
        phrase="a bright bell hat",
        type="hat",
        region="head",
    ),
    "shoes": Prize(
        label="shoes",
        phrase="shiny red shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a soft blue cloak",
        type="cloak",
        region="torso",
    ),
}

PROPS = {
    "antler": Prop(
        id="antler",
        label="antlers",
        phrase="a pair of cardboard antlers",
        kind="costume",
        fix="wear the antlers with the right costume",
        tags={"antler", "humor", "twist"},
    ),
    "masks": Prop(
        id="masks",
        label="masks",
        phrase="two funny masks",
        kind="costume",
        fix="use the masks for the rhyme game",
        tags={"humor"},
    ),
    "scarf": Prop(
        id="scarf",
        label="scarf",
        phrase="a long striped scarf",
        kind="costume",
        fix="wrap the scarf around the stage kit",
        tags={"twist"},
    ),
}

TWINS = [
    ("Mia", "girl", "playful"),
    ("Noa", "girl", "cheerful"),
    ("Finn", "boy", "spry"),
    ("Jude", "boy", "brave"),
]

RHYMES = {
    "humor": "They giggled and jiggled, then chuckled some more.",
    "twist": "The mix-up turned handy, not pesky or sore.",
    "antler": "The antlers looked silly, a wiggly delight.",
    "rhyme": "Their lines came in time like a ping and a chime.",
}


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    prop: str
    twin_a: str
    twin_b: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when an activity can mess the body region it sits on.
prize_at_risk(A, P) :- activity(A), prize(P), zones(A, R), worn_on(P, R).

% A prop is a compatible fix when it matches the key twist/humor slot.
compatible(A, P, G) :- prize_at_risk(A, P), prop(G), fix_for(G, A).

valid(Place, A, P, G) :- affords(Place, A), prize_at_risk(A, P), compatible(A, P, G).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zones", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for gid, g in PROPS.items():
        lines.append(asp.fact("prop", gid))
        for a in sorted({"rhymes", "play", "swap"} if "humor" in g.tags else set()):
            pass
        if gid == "antler":
            lines.append(asp.fact("fix_for", gid, "swap"))
            lines.append(asp.fact("fix_for", gid, "rhymes"))
        elif gid == "masks":
            lines.append(asp.fact("fix_for", gid, "rhymes"))
        elif gid == "scarf":
            lines.append(asp.fact("fix_for", gid, "play"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region not in act.zone and act_id != "swap":
                    continue
                for prop_id, prop in PROPS.items():
                    if prize.region in act.zone and prop_id == "antler":
                        out.append((place, act_id, prize_id, prop_id))
                    elif act_id == "rhymes" and prop_id == "masks":
                        out.append((place, act_id, prize_id, prop_id))
                    elif act_id == "play" and prop_id == "scarf":
                        out.append((place, act_id, prize_id, prop_id))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_prop(activity: Activity, prize: Prize) -> Optional[Prop]:
    if activity.id == "swap":
        return PROPS["antler"]
    if activity.id == "rhymes":
        return PROPS["masks"]
    if activity.id == "play":
        return PROPS["scarf"]
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} would not reach the {prize.region}, "
            f"so there is no real mix-up to solve.)"
        )
    return "(No story: there is no fitting prop for that mix-up.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    prize = f["prize"]
    prop = f["prop"]
    twin_a = f["twin_a"]
    return [
        f'Write a rhyming little story for a child about twins, an {prop.label}, and a funny twist.',
        f"Tell a humorous story where {twin_a} and {f['twin_b']} want to {act.verb} but worry about {prize.label}.",
        f"Write a short rhyming story with a beginning, a mix-up, and a happy ending involving {prop.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["twin_a"]
    b = f["twin_b"]
    act = f["activity"]
    prize = f["prize"]
    prop = f["prop"]
    return [
        QAItem(
            question=f"Who were the twins in the story?",
            answer=f"The twins were {a} and {b}. They liked to rhyme and play together.",
        ),
        QAItem(
            question=f"What did the twins want to do at {world.setting.place}?",
            answer=f"They wanted to {act.verb}. That made the day lively and bright.",
        ),
        QAItem(
            question=f"What item made the mix-up funny?",
            answer=f"The funny item was {prop.label}. It helped turn the problem into a silly twist.",
        ),
        QAItem(
            question=f"Why did the grown-up worry about the {prize.label}?",
            answer=(
                f"The grown-up worried because {act.gerund} could make the {prize.label} look "
                f"{act.soil}. That would have been a mess."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"The twins found a playful fix, laughed together, and kept their {prize.label} safe. "
                f"It ended with a happy rhyme."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are twins?",
            answer="Twins are two children who are born around the same time, so they are the same age.",
        ),
        QAItem(
            question="What are antlers?",
            answer="Antlers are branch-like parts that grow on the heads of some animals, like deer.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="Why can a silly mix-up be funny?",
            answer="A silly mix-up can be funny because people laugh when something unexpected turns out harmless.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    prop = PROPS[params.prop]

    world = World(setting)
    a = world.add(Entity(id=params.twin_a, kind="character", type="child"))
    b = world.add(Entity(id=params.twin_b, kind="character", type="child"))
    prize_e = world.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, plural=prize.plural))
    prop_e = world.add(Entity(id="prop", type=prop.kind, label=prop.label, phrase=prop.phrase))

    world.facts.update(
        twin_a=a,
        twin_b=b,
        activity=act,
        prize=prize_e,
        prop=prop_e,
        place=params.place,
    )
    return world


def tell(world: World, params: StoryParams) -> World:
    a = world.get(params.twin_a)
    b = world.get(params.twin_b)
    act = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    prop = PROPS[params.prop]

    world.say(f"{a.id} and {b.id} were twins with a tune in their feet,")
    world.say(f"who loved little rhymes on a sunny street.")
    world.say(f"At {world.setting.place}, they saw {prize.phrase},")
    world.say(f"and laughed at the thought of a show and a sway.")

    world.para()
    world.say(f"They wanted to {act.verb}, to wink and to spin,")
    world.say(f"but the grown-up said, \"Careful, that could make a mess begin.\"")
    world.say(f"For {act.gerund} could leave the {prize.label} in a muddle,")
    world.say(f"and nobody wanted a frowny-face huddle.")

    world.para()
    world.say(f"Then came the twist with the {prop.label} so neat:")
    world.say(f"it wasn't the right thing at first glance to meet.")
    world.say(f"But the twins saw the joke in the shiny surprise,")
    world.say(f"and turned that odd swap into laughter and skies.")

    if prop.id == "antler":
        world.say("They wore the antlers with a hop and a cheer,")
        world.say("and made up a deer-ish rhyme that drew every ear.")
    elif prop.id == "masks":
        world.say("They put on the masks and spoke in a sing-song way,")
        world.say("and the crowd clapped along at their clever little play.")
    else:
        world.say("They tied up the scarf and made it a stage-line star,")
        world.say("then bowed with a grin to the folks near and far.")

    world.para()
    world.say(f"In the end, the {prize.label} stayed safe and sound,")
    world.say(f"while the twins kept on rhyming and skipping around.")
    world.say(f"It started as worry, but ended in glee—")
    world.say(f"a twist made for two, as happy as could be.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world, params)
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
NAMES = ["Mia", "Noa", "Finn", "Jude", "Lia", "Pip", "Zoe", "Tess"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about twins and an antler twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, prize):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.prop is None or c[3] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize, prop = rng.choice(sorted(combos))
    twin_a = args.name_a or rng.choice(NAMES)
    twin_b = args.name_b or rng.choice([n for n in NAMES if n != twin_a])
    if twin_b == twin_a:
        raise StoryError("The twins need two different names.")
    return StoryParams(place=place, activity=activity, prize=prize, prop=prop, twin_a=twin_a, twin_b=twin_b)


def asp_program_text() -> str:
    return asp_program("#show valid/4.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("fair", "swap", "shoes", "antler", "Mia", "Noa"),
            StoryParams("stage", "rhymes", "bellhat", "masks", "Finn", "Jude"),
            StoryParams("garden", "play", "cloak", "scarf", "Lia", "Pip"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
