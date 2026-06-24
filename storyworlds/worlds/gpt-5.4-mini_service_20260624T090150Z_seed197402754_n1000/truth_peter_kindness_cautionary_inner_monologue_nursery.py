#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about Peter, truth, kindness, and a cautious
little inner monologue.

Seed tale:
- Peter is a small child in a cozy nursery kitchen.
- He makes a messy mistake.
- A cautious inner monologue warns him not to hide the truth.
- He tells the truth, and kindness helps him fix the mess together.

The world is intentionally tiny: one setting, a handful of objects, and one
clear emotional turn from worry to relief.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    cozy: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mistake: str
    risk: str
    worry_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str


@dataclass
class Fix:
    id: str
    label: str
    help_line: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


def _truth_rule(world: World) -> list[str]:
    out: list[str] = []
    peter = world.get("peter")
    if peter.memes.get("truth", 0) >= THRESHOLD and peter.memes.get("fear", 0) >= THRESHOLD:
        sig = ("truth_relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            peter.memes["relief"] = peter.memes.get("relief", 0) + 1
            peter.memes["fear"] = 0
            out.append("__truth_relief__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_truth_rule,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__truth_relief__")
    if narrate:
        for s in produced:
            world.say(s)


def tell(world: World, activity: Activity, prize: Prize, fix: Fix) -> World:
    peter = world.add(Entity(id="peter", kind="character", type="boy"))
    caregiver = world.add(Entity(id="mama", kind="character", type="mother", label="Mama"))
    messy = world.add(Entity(
        id=prize.id,
        type="thing",
        label=prize.label,
        phrase=prize.phrase,
        caretaker=caregiver.id,
    ))

    world.say("Peter sat by the nursery window, as still as still could be.")
    world.say("He loved the cozy room, with its books and its blue tick-tock tree.")
    world.say(f"He reached for the {activity.verb}, and then, oh dear, the {activity.mistake}.")
    peter.meters["mess"] = 1
    peter.memes["worry"] = 1

    world.para()
    world.say(
        f"In Peter's little inner monologue, a cautious whisper said, "
        f'"Telling the truth is braver than hiding a thing that shows."'
    )
    peter.memes["fear"] = 1
    peter.memes["caution"] = 1
    peter.memes["truth"] = 1

    world.say(
        f"Peter looked at the {prize.label} and felt his cheeks go hot like jam on a spoon."
    )
    world.say(
        f'{activity.worry_line} "If I tell a lie," thought Peter, '
        f'"the mess may only grow."'
    )

    world.para()
    world.say('So Peter took a breath and said, "Mama, I must tell the truth."')
    world.say(
        f'He pointed to the {prize.label} and owned the spill with a brave, small "scoot."'
    )
    propagate(world, narrate=False)

    world.say(
        f"Mama gave a smile so warm it seemed to turn the kitchen gold."
    )
    world.say(
        f'"Thank you for telling the truth, my dear," she said, "that was honest and bold."'
    )
    world.say(
        f"Then her kindness made the room feel safe; it was soft as a lullaby tune."
    )

    world.para()
    world.say(f"{fix.help_line} Peter fetched {fix.label}, and they cleaned in a careful row.")
    messy.meters["dirty"] = 1
    caregiver.memes["kindness"] = 1
    peter.memes["relief"] = peter.memes.get("relief", 0) + 1
    peter.memes["joy"] = peter.memes.get("joy", 0) + 1

    world.say(
        f"At last the {prize.label} was clean again, and Peter felt light as a feather in June."
    )
    world.say(
        f"He tucked the lesson in his pocket: truth is small, but it helps hearts bloom."
    )

    world.facts.update(
        peter=peter,
        caregiver=caregiver,
        prize=messy,
        activity=activity,
        fix=fix,
    )
    return world


SETTINGS = {
    "nursery_kitchen": Setting(place="the nursery kitchen", cozy=True),
}

ACTIVITIES = {
    "spill": Activity(
        id="spill",
        verb="reach for the jam",
        gerund="reaching for the jam",
        mistake="the jam spilled onto the cloth",
        risk="a sticky stain on the table",
        worry_line="He knew the cloth would be sticky and the table would need a wash.",
        tags={"truth", "jam", "mess"},
    ),
    "crumbs": Activity(
        id="crumbs",
        verb="nibble the biscuit",
        gerund="nibbling the biscuit",
        mistake="crumbs tumbled all over the bench",
        risk="crumbs on the seat",
        worry_line="He knew the crumbs would show as plain as day.",
        tags={"truth", "crumbs", "mess"},
    ),
}

PRIZES = {
    "cloth": Prize(id="cloth", label="table cloth", phrase="the table cloth", region="table"),
    "apron": Prize(id="apron", label="apron", phrase="Mama's apron", region="torso"),
}

FIXES = {
    "sponge": Fix(
        id="sponge",
        label="a soft sponge",
        help_line="Kindness made room for a fix, so Mama passed him",
        tail="Then Peter wiped and wiped, until the shine came back.",
    ),
    "rag": Fix(
        id="rag",
        label="a clean rag",
        help_line="With kindness in the air, Mama handed him",
        tail="Soon the little room looked bright and neat again.",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    fix: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "truth": [
        ("What is the truth?",
         "The truth is saying what really happened, even if it feels a little hard."),
    ],
    "kindness": [
        ("What is kindness?",
         "Kindness means being gentle and helpful to someone else."),
    ],
    "cautionary": [
        ("What does caution mean?",
         "Caution means taking care and pausing before you do something that might cause trouble."),
    ],
    "inner_monologue": [
        ("What is an inner monologue?",
         "An inner monologue is the quiet voice inside your head that you use to think."),
    ],
    "peter": [
        ("Who is Peter?",
         "Peter is a common story name for a little boy in a nursery rhyme style tale."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story for a young child about truth, kindness, and a cautious inner monologue.',
        f"Tell a gentle story about Peter in {world.setting.place} who makes a small mistake and then tells the truth.",
        f"Write a cozy story where Peter uses his inner monologue to choose kindness and fix a mess.",
        f"Make the ending warm and rhythmic, with Peter learning that the truth helps more than hiding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    act: Activity = f["activity"]
    prize: Prize = f["prize"]
    fix: Fix = f["fix"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Peter, a little boy who makes a small mistake and then tells the truth.",
        ),
        QAItem(
            question="What did Peter do that caused trouble?",
            answer=f"Peter {act.verb}, and {act.mistake}.",
        ),
        QAItem(
            question="What did Peter's cautious inner monologue tell him?",
            answer="It told him that hiding the mistake would not help, and that telling the truth would be braver.",
        ),
        QAItem(
            question="How did kindness help at the end?",
            answer=f"Mama answered with kindness and gave Peter {fix.label} so they could clean up together.",
        ),
        QAItem(
            question="What was clean again at the end?",
            answer=f"The {prize.label} was clean again, and the room felt neat and calm.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["truth", "kindness", "cautionary", "inner_monologue", "peter"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
truthful(peter) :- says_truth(peter), cautious_inner_voice(peter).
kind_fix(peter) :- truthful(peter), kindness_from(mama,peter).
safe_story(peter) :- kind_fix(peter).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("says_truth", "peter"))
    lines.append(asp.fact("cautious_inner_voice", "peter"))
    lines.append(asp.fact("kindness_from", "mama", "peter"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_safe() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/1."))
    atoms = set(asp.atoms(model, "safe_story"))
    python_ok = {("peter",)} if asp_safe() else set()
    if atoms == python_ok:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python reasonableness gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python_ok))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about Peter, truth, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or rng.choice(list(PRIZES))
    fix = args.fix or rng.choice(list(FIXES))
    return StoryParams(place=place, activity=activity, prize=prize, fix=fix)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    act = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    fix = FIXES[params.fix]
    world = tell(world, act, prize, fix)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="nursery_kitchen", activity="spill", prize="cloth", fix="sponge"),
    StoryParams(place="nursery_kitchen", activity="crumbs", prize="apron", fix="rag"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern:")
        print("  peter + truth + kindness + cautionary inner monologue")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
