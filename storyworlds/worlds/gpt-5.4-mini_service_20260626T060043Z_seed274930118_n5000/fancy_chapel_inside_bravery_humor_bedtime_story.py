#!/usr/bin/env python3
"""
A bedtime-style story world set inside a fancy chapel, where a child finds
bravery with a little humor.
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
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the fancy chapel"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"bell", "choir", "candle"})

    @property
    def bedside_name(self) -> str:
        return "inside"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Aid:
    id: str
    label: str
    action: str
    tail: str


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


SETTINGS = {
    "chapel": Setting(),
}

ACTIVITIES = {
    "bell": Activity(
        id="bell",
        verb="ring the little bell",
        gerund="ringing the little bell",
        rush="hurry to the bell",
        risk="the echo might feel too loud",
        keyword="bell",
        tags={"bell", "echo"},
    ),
    "choir": Activity(
        id="choir",
        verb="sing a tiny hymn",
        gerund="singing a tiny hymn",
        rush="step into the choir loft",
        risk="the high voices might wobble",
        keyword="choir",
        tags={"choir", "music"},
    ),
}

PRIZES = {
    "cloak": Prize(
        label="cloak",
        phrase="a fancy blue cloak with shiny buttons",
        type="cloak",
        region="torso",
    ),
    "shoes": Prize(
        label="shoes",
        phrase="a pair of neat black shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
    "book": Prize(
        label="prayer book",
        phrase="a little prayer book with a gold ribbon",
        type="book",
        region="hands",
    ),
}

AIDS = {
    "joke": Aid(
        id="joke",
        label="a silly joke",
        action="tell a silly joke",
        tail="smiled and made the chapel feel warm again",
    ),
    "breath": Aid(
        id="breath",
        label="slow brave breaths",
        action="take slow brave breaths",
        tail="stood tall and calm",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "June", "Ada", "Ivy"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Ben", "Noah", "Arlo"]
TRAITS = ["gentle", "curious", "sleepy", "spirited", "small"]


@dataclass
class StoryParams:
    place: str = "chapel"
    activity: str = "bell"
    prize: str = "book"
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "gentle"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("chapel", "bell", "book"), ("chapel", "choir", "book")]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} is not a good match for a {prize.label} "
        f"in this little chapel scene.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok} for {PRIZES[prize_id].label}.)"


def select_aid(activity: Activity) -> Aid:
    return AIDS["joke"] if activity.id == "bell" else AIDS["breath"]


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
        meters={"distance": 0.0},
        memes={"worry": 0.0, "bravery": 0.0, "humor": 0.0, "calm": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        meters={"distance": 0.0},
        memes={"warmth": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=prize_cfg.plural,
    ))

    aid = select_aid(activity)

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved quiet places.")
    world.say(f"{hero.id} liked the fancy chapel inside because the candles glowed like small stars.")
    world.say(f"One evening, {hero.id} wore {hero.pronoun('possessive')} {prize.label} and walked beside {hero.pronoun('possessive')} {parent.label}.")
    world.para()
    world.say(f"At the chapel, {hero.id} wanted to {activity.verb}.")
    world.say(f"But {activity.risk}.")
    hero.memes["worry"] += 1.0
    world.say(f"{hero.id} held still and looked at the long aisle, feeling a tiny flutter in {hero.pronoun('possessive')} chest.")
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} gave {hero.id} {aid.label} and said, \"You can be brave in a small way first.\"")
    hero.memes["humor"] += 1.0
    world.say(f"{hero.id} giggled at the joke, because even the echo seemed to grin back.")
    world.para()
    hero.memes["bravery"] += 1.0
    hero.meters["distance"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["calm"] += 1.0
    world.say(f"With one brave breath, {hero.id} walked forward and {activity.verb}.")
    world.say(f"The little sound rang out, soft and bright, and {hero.id} smiled when the chapel answered with a gentle echo.")
    world.say(f"{hero.pronoun('subject').capitalize()} {aid.tail}, and {hero.id} tucked {hero.pronoun('possessive')} {prize.label} close for the walk home.")
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, aid=aid, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        'Write a bedtime story about a child inside a fancy chapel who finds bravery with a small joke.',
        f"Tell a gentle bedtime story where {hero.id} wants to {act.verb} inside a fancy chapel.",
        f"Write a short bedtime-style story that includes a chapel, humor, and bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Where was {hero.id} in the story?",
            answer=f"{hero.id} was inside a fancy chapel with {hero.pronoun('possessive')} parent.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel braver?",
            answer=f"{aid.label} helped {hero.id} feel braver, and the joke made {hero.id} laugh first.",
        ),
        QAItem(
            question=f"What was special about {hero.id}'s {prize.label}?",
            answer=f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} while walking through the chapel, and it stayed neat.",
        ),
        QAItem(
            question=f"How did {hero.id} act at the end?",
            answer=f"{hero.id} acted bravely, smiled at the echo, and went home calm.",
        ),
    ]


KNOWLEDGE = {
    "bell": [(
        "What is a bell for?",
        "A bell is often used to make a clear ringing sound that people can hear from far away."
    )],
    "choir": [(
        "What is a choir?",
        "A choir is a group of people who sing together."
    )],
    "echo": [(
        "What is an echo?",
        "An echo is a sound that bounces back after it hits a wall or a big space."
    )],
    "music": [(
        "Why do people sing together?",
        "People sing together to make music that sounds warm and full."
    )],
    "humor": [(
        "What is humor?",
        "Humor is something funny that makes people smile or laugh."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery means doing something scary or hard even when you feel nervous."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.update({"humor", "bravery"})
    out: list[QAItem] = []
    for tag in ["bravery", "humor", "bell", "choir", "echo", "music"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(chapel).
indoor(chapel).

activity(bell).
activity(choir).

prize(book).
prize(cloak).
prize(shoes).

valid(chapel,bell,book).
valid(chapel,choir,book).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("place", name))
        if setting.indoor:
            lines.append(asp.fact("indoor", name))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", name, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a fancy chapel inside, with bravery and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if args.prize != "book" or args.activity not in {"bell", "choir"}:
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="chapel", activity="bell", prize="book", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="chapel", activity="choir", prize="book", name="Theo", gender="boy", parent="father", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
