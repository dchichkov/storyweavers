#!/usr/bin/env python3
"""
A small heartwarming storyworld about an usher, a bit of goop, and a little magic.

The story premise:
- A friendly usher helps visitors at a cozy place.
- A magical spill of goop makes one task harder.
- The usher and the visitor solve the problem together, ending in warmth and gratitude.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- StoryParams, registries, parser, resolve_params, generate, emit, main
- Python reasonableness gate and inline ASP twin
- optional verification and trace output
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "usher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)
    keyword: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class MagicTool:
    id: str
    label: str
    description: str
    fix: str
    blessing: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lobby": Setting(place="the theater lobby", indoor=True, affords={"magic"}),
    "gallery": Setting(place="the glowing gallery", indoor=True, affords={"magic"}),
    "station": Setting(place="the station hall", indoor=True, affords={"magic"}),
}

ACTIVITIES = {
    "magic": Activity(
        id="magic",
        verb="practice a little magic",
        gerund="practicing little magic tricks",
        rush="wave the wand too fast",
        mess="goopy",
        soil="spattered with goop",
        tags={"magic", "goop"},
        keyword="magic",
    ),
    "sparkles": Activity(
        id="sparkles",
        verb="make sparkles",
        gerund="making sparkles",
        rush="spin the wand in a hurry",
        mess="dusty",
        soil="dusty and sticky",
        tags={"magic"},
        keyword="sparkles",
    ),
}

PRIZES = {
    "vest": Prize(label="vest", phrase="a neat red usher vest", region="torso"),
    "gloves": Prize(label="gloves", phrase="soft white gloves", region="hands", plural=True),
    "namebadge": Prize(label="badge", phrase="a shiny name badge", region="torso"),
}

MAGIC = [
    MagicTool(
        id="wand",
        label="a tiny wand",
        description="a little wand with a star on top",
        fix="tap the goop into a neat little mound",
        blessing="the wand could turn a mess into something gentle and tidy",
    ),
    MagicTool(
        id="cloth",
        label="a mooncloth towel",
        description="a soft towel that hummed when it touched a spill",
        fix="soak up the goop without hurting anything",
        blessing="the mooncloth could drink up magic spills like a thirsty cloud",
    ),
]

USHER_NAMES = ["Mina", "Noor", "Lena", "Sana", "Ivy", "Rosa"]
VISITOR_NAMES = ["Pip", "Jojo", "Milo", "Tia", "Hugo", "Ada"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    usher_name: str
    visitor_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.mess == "goopy" and prize.region in {"torso", "hands"}


def select_magic(activity: Activity, prize: Prize) -> Optional[MagicTool]:
    if activity.id == "magic" and prize.region in {"torso", "hands"}:
        return MAGIC[0]
    if activity.id == "sparkles":
        return MAGIC[1]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            if aid not in setting.affords:
                continue
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_magic(act, prize):
                    out.append((place, aid, pid))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), mess_of(A, goopy), worn_on(P, torso).
prize_at_risk(A,P) :- activity(A), prize(P), mess_of(A, goopy), worn_on(P, hands).

has_fix(A,P) :- prize_at_risk(A,P), magic_fix(A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for mt in MAGIC:
        lines.append(asp.fact("magic_tool", mt.id))
    for place, aid, pid in valid_combos():
        if select_magic(ACTIVITIES[aid], PRIZES[pid]):
            lines.append(asp.fact("magic_fix", aid, pid))
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
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------
def setting_line(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was warm and bright."
    return f"{setting.place.capitalize()} felt calm and welcoming."


def generate_story(world: World, hero: Entity, visitor: Entity, prize: Entity, activity: Activity, tool: MagicTool) -> None:
    world.say(f"{hero.id} was an usher who loved making people feel at home.")
    world.say(f"{visitor.id} was a small visitor with a shy smile, and {visitor.pronoun('possessive')} {prize.label} was neat and bright.")
    world.say(f"At {world.setting.place}, {setting_line(world.setting)}")
    world.para()
    world.say(f"One evening, {visitor.id} wanted to {activity.verb}, because the little magic in the room made everything seem possible.")
    world.say(f"But when {visitor.id} tried to {activity.rush}, a blob of {activity.mess} landed on {visitor.pronoun('possessive')} {prize.label}.")
    world.say(f"{hero.id} saw the spill and smiled kindly. “That can be fixed,” {hero.pronoun()} said.")
    world.para()
    world.say(f"{hero.id} brought out {tool.label}, {tool.description}, and asked {visitor.id} to hold still.")
    world.say(f"Together they {tool.fix}, and the {prize.label} came out clean again.")
    world.say(f"{tool.blessing} helped turn the mistake into a tiny, gentle moment.")
    world.para()
    world.say(f"{visitor.id} laughed in relief and hugged {hero.id}.")
    world.say(f"By the end, {visitor.id} was still {activity.gerund}, only now with a calmer heart and a clean {prize.label}.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    visitor = f["visitor"]
    prize = f["prize"]
    act = f["activity"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who helped {visitor.id} after the goop landed on {visitor.pronoun('possessive')} {prize.label}?",
            answer=f"{hero.id} the usher helped right away, and {hero.id} stayed kind the whole time.",
        ),
        QAItem(
            question=f"What happened when {visitor.id} tried to {act.rush}?",
            answer=f"A blob of {act.mess} landed on {visitor.pronoun('possessive')} {prize.label}, which made the moment messy.",
        ),
        QAItem(
            question=f"What did {hero.id} use to make the mess better?",
            answer=f"{hero.id} used {tool.label} to {tool.fix}.",
        ),
        QAItem(
            question=f"How did the story end for {visitor.id} and {hero.id}?",
            answer=f"They ended with a clean {prize.label}, a happy hug, and a warmer feeling between them.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an usher do?",
            answer="An usher helps visitors find their way, stay comfortable, and feel welcome in a place like a theater or hall.",
        ),
        QAItem(
            question="What is goop?",
            answer="Goop is a thick, sticky mess. It can drip, smear, and cling to things.",
        ),
        QAItem(
            question="What can magic do in a gentle story?",
            answer="Magic can help solve a problem in a surprising but kind way, like tidying a spill or making a hard moment feel softer.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a warm, child-friendly story about an usher, a little bit of goop, and a kind magical fix.',
        f"Tell a heartwarming story set at {world.setting.place} where {f['visitor'].id} makes a messy mistake and {f['hero'].id} helps gently.",
        'Write a short magical story that ends with a hug, a clean prize, and a calmer heart.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_magic(act, pr)):
            raise StoryError("(No valid combination matches the given options.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        usher_name=args.usher_name or rng.choice(USHER_NAMES),
        visitor_name=args.visitor_name or rng.choice(VISITOR_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    tool = select_magic(activity, prize)
    if tool is None:
        raise StoryError("No reasonable magical fix exists for this combination.")

    world = World(setting)
    hero = world.add(Entity(id=params.usher_name, kind="character", type="usher"))
    visitor = world.add(Entity(id=params.visitor_name, kind="character", type="child"))
    prize_ent = world.add(Entity(id="prize", type=prize.label, label=prize.label, phrase=prize.phrase, caretaker=hero.id))

    world.facts.update(hero=hero, visitor=visitor, prize=prize_ent, activity=activity, tool=tool)
    generate_story(world, hero, visitor, prize_ent, activity, tool)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: an usher, goop, magic, and a heartwarming fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--usher-name")
    ap.add_argument("--visitor-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(place="lobby", activity="magic", prize="vest", usher_name="Mina", visitor_name="Pip"),
    StoryParams(place="gallery", activity="magic", prize="namebadge", usher_name="Noor", visitor_name="Ada"),
    StoryParams(place="station", activity="sparkles", prize="gloves", usher_name="Lena", visitor_name="Milo"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
