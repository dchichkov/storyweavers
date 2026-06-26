#!/usr/bin/env python3
"""
A small Storyweavers storyworld: a child in a dentist office, a spacey mishap,
and a surprising Twist that turns a scary visit into a game of peekaboo.

The world premise is simple:
- A child comes to a dentist office.
- They bring a snack lunch with ratatouille.
- They do an antic of playing peekaboo with a shiny helmet visor / dental lamp shadows.
- The dentist worries about cleanliness and the exam.
- Twist: the office has a special space-themed mirror trick, and the child helps
  the dentist with a cheerful peekaboo routine that calms the room.
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
    place: str = "the dentist office"
    affords: set[str] = field(default_factory=lambda: {"peekaboo", "antic", "twist"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects_from: set[str] = field(default_factory=set)


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


SETTING = Setting()

ACTIVITIES = {
    "peekaboo": Activity(
        id="peekaboo",
        verb="play peekaboo",
        gerund="playing peekaboo",
        rush="pop out from behind the chair",
        mess="noise",
        soil="a little too loud",
        keyword="peekaboo",
        tags={"peekaboo"},
    ),
    "antic": Activity(
        id="antic",
        verb="do an antic",
        gerund="doing silly antics",
        rush="spin around the lamp stand",
        mess="noise",
        soil="full of giggles",
        keyword="antic",
        tags={"antic"},
    ),
    "twist": Activity(
        id="twist",
        verb="do a Twist",
        gerund="twisting and turning",
        rush="twirl like a tiny comet",
        mess="noise",
        soil="extra bouncy",
        keyword="Twist",
        tags={"twist", "space"},
    ),
}

PRIZES = {
    "ratatouille": Prize(
        label="ratatouille",
        phrase="a warm lunchbox of ratatouille",
        type="lunchbox",
        region="hands",
        plural=False,
    ),
    "helmet": Prize(
        label="helmet",
        phrase="a shiny little space helmet",
        type="helmet",
        region="head",
        plural=False,
    ),
    "jacket": Prize(
        label="jacket",
        phrase="a bright jacket with silver stars",
        type="jacket",
        region="torso",
        plural=False,
    ),
}

GEAR = {
    "napkin": Gear(
        id="napkin",
        label="a big napkin",
        prep="put on a big napkin",
        tail="tucked the napkin into place",
        protects_from={"mess"},
    ),
    "mirror": Gear(
        id="mirror",
        label="the dentist mirror",
        prep="hold up the tiny mirror",
        tail="flashed the mirror like a little sun",
        protects_from={"noise"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nova", "Piper", "Ada", "Zoe"]
BOY_NAMES = ["Leo", "Max", "Finn", "Toby", "Noah", "Eli"]
TRAITS = ["curious", "brave", "playful", "sparkly", "bouncy", "cheerful"]


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def _predicted_problem(activity: Activity, prize: Prize) -> bool:
    return activity.keyword in {"peekaboo", "antic", "Twist"} and prize.label == "ratatouille"


def tell(activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         parent_type: str, trait: str) -> World:
    world = World(SETTING)

    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        memes={"joy": 0.0, "worry": 0.0, "delight": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
        memes={"worry": 0.0, "calm": 0.0},
    ))
    dentist = world.add(Entity(
        id="Dentist",
        kind="character",
        type="woman",
        label="the dentist",
        memes={"worry": 0.0, "calm": 0.0},
    ))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))

    # Act 1
    world.say(
        f"{hero_name} was a little {trait} {hero_type} who came to {world.setting.place} with "
        f"{child.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"{hero_name} loved {activity.gerund}, and {child.pronoun()} also loved "
        f"the spacey stickers on the wall."
    )

    world.para()

    # Act 2
    world.say(
        f"Inside the office, the bright lamp shone like a tiny moon, and {hero_name} wanted to "
        f"{activity.verb} right away."
    )
    if _predicted_problem(activity, prize_cfg):
        parent.memes["worry"] += 1
        dentist.memes["worry"] += 1
        world.say(
            f'The {parent_type} smiled, but said, "{hero_name}, be careful with that {prize.label}. '
            f'We do not want it to get messy during the checkup."'
        )
        world.say(
            f"{hero_name} heard that, but {child.pronoun('possessive')} feet still wanted to "
            f"{activity.rush}."
        )
        child.memes["defiance"] = 1.0
    else:
        world.say(f"{hero_name} paused and watched the lamp glow.")
    world.say(
        f"Then the {dentist.label} raised the mirror and made a tiny face appear and disappear."
    )
    child.memes["surprise"] = 1.0
    world.say(
        f"{hero_name} laughed, because it looked like a little starship hiding in clouds."
    )

    world.para()

    # Twist resolution
    gear = GEAR["mirror"] if activity.id in {"peekaboo", "twist"} else GEAR["napkin"]
    world.say(
        f'That was the Twist: the {dentist.label} said, "{gear.prep}, and we can make '
        f'peekaboo into the game."'
    )
    child.memes["joy"] += 1
    parent.memes["calm"] += 1
    dentist.memes["calm"] += 1
    if prize_cfg.label == "ratatouille":
        world.say(
            f"{hero_name} held {child.pronoun('possessive')} lunchbox close, then waited while the "
            f"mirror flashed and hid again."
        )
        world.say(
            f"Soon {hero_name} was {activity.gerund}, and the ratatouille stayed safe and neat "
            f"for after the appointment."
        )
    else:
        world.say(
            f"{hero_name} did the {activity.keyword} with a big grin, and the office felt lighter."
        )
    world.say(
        f'The {parent_type} laughed too, and the checkup ended with a happy "{gear.tail}".'
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short child-friendly story set in a dentist office with a space-adventure feel.',
        f"Tell a story where {f['name']} does {f['activity'].verb}, but a dentist office visit becomes a cheerful Twist.",
        f'Use the words "{f["activity"].keyword}", "peekaboo", and "ratatouille" in a gentle story with a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where does {f['name']} go in the story?",
            answer=f"{f['name']} goes to the dentist office with {f['parent']} for a checkup.",
        ),
        QAItem(
            question=f"What food did {f['name']} bring?",
            answer=f"{f['name']} brought ratatouille in a lunchbox, and it stayed safe for after the visit.",
        ),
        QAItem(
            question="What was the Twist?",
            answer="The Twist was that the dentist turned the scary moment into a peekaboo game with the mirror, so everyone relaxed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dentist office for?",
            answer="A dentist office is a place where a dentist checks teeth and helps keep them healthy.",
        ),
        QAItem(
            question="What is peekaboo?",
            answer="Peekaboo is a game where someone hides and pops back out, which can make little kids laugh.",
        ),
        QAItem(
            question="What is ratatouille?",
            answer="Ratatouille is a warm vegetable dish made by cooking soft pieces of vegetables together.",
        ),
        QAItem(
            question="What does a twist mean in a story?",
            answer="A twist is a surprising turn that changes what you expected to happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or "ratatouille"
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    if prize != "ratatouille":
        raise StoryError("This storyworld is centered on ratatouille as the child's lunch.")
    if activity not in ACTIVITIES:
        raise StoryError("Invalid activity.")
    return StoryParams(activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
    world.facts = {
        "name": params.name,
        "activity": ACTIVITIES[params.activity],
        "parent": params.parent,
        "prize": PRIZES[params.prize],
    }
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small dentist-office space-adventure storyworld.")
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait")
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


ASP_RULES = r"""
activity(A) :- act(A).
prize(P) :- pr(P).
bad_combo(A,P) :- act(A), pr(P), P = ratatouille.
compatible(A,P) :- activity(A), prize(P), not bad_combo(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ACTIVITIES:
        lines.append(asp.fact("act", a))
    for p in PRIZES:
        lines.append(asp.fact("pr", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("dentist_office", a, "ratatouille") for a in ACTIVITIES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set((x[1], x[2]) for x in valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, act in enumerate(ACTIVITIES):
            params = StoryParams(
                activity=act,
                prize="ratatouille",
                name=GIRL_NAMES[i % len(GIRL_NAMES)],
                gender="girl",
                parent="mother",
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
