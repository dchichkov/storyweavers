#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/pattern_minus_van_cautionary_misunderstanding_tall_tale.py
======================================================================================================

A small standalone story world in a tall-tale voice:
- cautionary tension around a van in a narrow lane
- a misunderstanding about the word "minus"
- a pattern at risk, then saved by a sensible move

Seed words woven into the world:
- pattern
- minus
- van

The world is intentionally tiny and constraint-checked: a child, a caregiver,
a van, and a patterned prize. The story grows from world state changes rather
than from a fixed paragraph template.
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

# Physical threshold for state changes to become narratively meaningful.
THRESHOLD = 1.0


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
    worn_by: Optional[str] = None
    ridden_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    narrow_lane: bool = False
    affords: set[str] = field(default_factory=set)


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
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    help_text: str
    tail: str
    covers: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "lane": Setting(place="the narrow lane", narrow_lane=True, affords={"wheel", "watch"}),
    "yard": Setting(place="the yard", narrow_lane=False, affords={"watch", "wheel"}),
    "market": Setting(place="the market road", narrow_lane=True, affords={"watch"}),
}

ACTIVITIES = {
    "watch": Activity(
        id="watch",
        verb="watch the van roll in",
        gerund="watching the van roll in",
        rush="run to the lane",
        risk="be in the way of the van",
        keyword="van",
        tags={"van", "cautionary"},
    ),
    "wheel": Activity(
        id="wheel",
        verb="wheel the pattern cart",
        gerund="wheeling the pattern cart",
        rush="push the cart ahead",
        risk="bump the pattern into the van",
        keyword="pattern",
        tags={"pattern", "van"},
    ),
}

PRIZES = {
    "banner": Prize(
        label="banner",
        phrase="a bright pattern banner",
        type="banner",
        location="wall",
    ),
    "blanket": Prize(
        label="blanket",
        phrase="a striped pattern blanket",
        type="blanket",
        location="ground",
    ),
    "cart": Prize(
        label="cart",
        phrase="a little pattern cart",
        type="cart",
        location="ground",
    ),
}

GEAR = [
    Gear(
        id="rope",
        label="a rope line",
        help_text="stretch a rope line to mark the safe spot",
        tail="stayed behind the rope line",
        covers={"lane"},
    ),
    Gear(
        id="porch",
        label="the porch step",
        help_text="move the pattern up onto the porch step",
        tail="rolled the pattern up onto the porch step",
        covers={"porch"},
    ),
]

GIRL_NAMES = ["Mira", "Nina", "Ruby", "Lena", "Ada", "Poppy"]
BOY_NAMES = ["Bennett", "Toby", "Cal", "Jasper", "Milo", "Eli"]
TRAITS = ["bold", "curious", "cheery", "sturdy", "spirited"]


def prize_at_risk(activity: Activity, prize: Prize, setting: Setting) -> bool:
    return setting.narrow_lane and activity.keyword == "van" and prize.location in {"ground", "wall"}


def select_gear(activity: Activity, prize: Prize, setting: Setting) -> Optional[Gear]:
    if prize.location == "ground":
        return GEAR[0]
    if prize.location == "wall":
        return GEAR[1]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            if act_id not in setting.affords:
                continue
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize, setting) and select_gear(act, prize, setting):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize, setting: Setting) -> str:
    return (
        f"(No story: {activity.gerund} does not create a real caution for "
        f"{prize.label} in {setting.place}. The tale needs a pattern in the lane, "
        f"a van, and a sensible fix.)"
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, caregiver_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        meters={}, memes={"wonder": 1.0, "curiosity": 1.0},
    ))
    caregiver = world.add(Entity(
        id="Caregiver", kind="character", type=caregiver_type, label="the elder",
        meters={}, memes={"care": 1.0},
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=caregiver.id,
    ))
    van = world.add(Entity(
        id="Van", kind="thing", type="van", label="the van",
        phrase="a big delivery van", meters={"near": 0.0}, memes={"looming": 0.0},
    ))

    # Act 1
    world.say(
        f"{hero.id} was a {trait} {hero.type} who loved every bright pattern under the sun."
    )
    world.say(
        f"{hero.pronoun().capitalize()} treasured {hero.pronoun('possessive')} {prize.label} "
        f"with its bold little pattern."
    )
    world.say(
        f"That morning, the elder said a great wagon of a van was coming down the road."
    )

    # Act 2
    world.para()
    world.say(
        f"At the narrow lane, {hero.id} wanted to {activity.verb} beside {hero.pronoun('possessive')} "
        f"{prize.label}."
    )
    world.say(
        f"The elder warned, \"Keep that pattern out of the lane; that van is too big to dance around."
        f"\""
    )
    hero.memes["desire"] = 1.0
    hero.memes["confusion"] = 1.0
    van.meters["near"] = 1.0
    van.memes["looming"] = 1.0

    world.say(
        f"{hero.id} misunderstood the warning and thought \"minus\" meant the pattern had to be taken "
        f"away from the whole day, not just from the road."
    )
    world.say(
        f"So {hero.id} tried to drag {hero.pronoun('possessive')} {prize.label} toward the van, "
        f"which was a taller idea than a barn cat and twice as tricky."
    )
    hero.memes["alarm"] = 1.0
    prize.meters["at_risk"] = 1.0
    prize.memes = {"jitters": 1.0}  # type: ignore[attr-defined]

    # Act 3
    world.para()
    gear = select_gear(activity, prize, setting)
    if gear is None:
        raise StoryError(explain_rejection(activity, prize, setting))

    if prize.location == "ground":
        world.say(
            f"The elder pointed to a rope line and said, \"Minus means move the pattern from the lane, "
            f"not from the world.\""
        )
        world.say(
            f"{hero.id}'s eyes opened wide. {hero.pronoun().capitalize()} hopped the pattern cart back "
            f"behind the rope line."
        )
        world.say(
            f"Then the van rolled through with its bells clanking like a tin thundercloud, and nothing got bumped."
        )
        world.say(
            f"{hero.id} felt proud, because the pattern stayed bright and the lane stayed clear."
        )
        prize.meters["safe"] = 1.0
        hero.memes["confusion"] = 0.0
        hero.memes["relief"] = 1.0
    else:
        world.say(
            f"The elder said, \"Minus means take the pattern up to the porch step, where the van cannot reach.\""
        )
        world.say(
            f"{hero.id} understood at last and carried the banner to the porch, while the van rumbled by below."
        )
        world.say(
            f"The banner hung safe and high, as proud as a courthouse flag, and the road kept its distance."
        )
        prize.meters["safe"] = 1.0
        hero.memes["confusion"] = 0.0
        hero.memes["relief"] = 1.0

    world.facts.update(
        hero=hero,
        caregiver=caregiver,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        van=van,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    return [
        f'Write a short tall-tale story for a young child that includes the words "pattern", "minus", and "van".',
        f"Tell a cautionary story where {hero.id} misunderstands what 'minus' means while trying to keep {prize.label} safe from a van.",
        f"Write a gentle, funny story about a big van, a bright pattern, and a child learning to stay out of the lane.",
        f"Tell a story that starts with curiosity, turns on a misunderstanding, and ends with a safe plan for {act.keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caregiver = f["caregiver"]
    prize = f["prize"]
    act = f["activity"]
    setting = f["setting"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a {hero.type} who loved a bright pattern and learned a careful lesson.",
        ),
        QAItem(
            question=f"Why did the elder warn {hero.id} about the lane?",
            answer=f"The elder warned {hero.id} because a big van was coming through {setting.place}, and the lane was too narrow for a child and a pattern to linger there.",
        ),
        QAItem(
            question=f"What did {hero.id} misunderstand about the word 'minus'?",
            answer=f"{hero.id} misunderstood it and thought 'minus' meant taking the pattern away from everything, instead of just moving it out of the van's path.",
        ),
        QAItem(
            question=f"How did {gear.label} help in the end?",
            answer=f"{gear.help_text}, so the {prize.label} could stay safe while the van rolled by.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, {hero.id} was relieved, the pattern stayed safe, and the van passed without bumping anything.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a van?",
            answer="A van is a big vehicle that can carry people or things, and it needs plenty of room to move safely.",
        ),
        QAItem(
            question="What does minus mean?",
            answer="Minus means take away or remove one part from a group, or keep something out of a place where it does not belong.",
        ),
        QAItem(
            question="What is a pattern?",
            answer="A pattern is a repeated design, like stripes, dots, or shapes that show up again and again.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), setting(S), narrow_lane(S),
                       keyword(A, van), location(P, ground).
prize_at_risk(A, P) :- activity(A), prize(P), setting(S), narrow_lane(S),
                       keyword(A, van), location(P, wall).

has_fix(A, P) :- prize_at_risk(A, P), gear(G), helps(G, A, P).
valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.narrow_lane:
            lines.append(asp.fact("narrow_lane", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("location", pid, p.location))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("helps", g.id, "watch", "banner"))
        lines.append(asp.fact("helps", g.id, "wheel", "cart"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    import storyworlds.asp as asp
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in clingo:", sorted(clingo_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale cautionary storyworld about a pattern, a minus misunderstanding, and a van."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if False else True]
    # Manual filter to keep the code clear and robust.
    combos = []
    for place, act, prize in valid_combos():
        if args.place and place != args.place:
            continue
        if args.activity and act != args.activity:
            continue
        if args.prize and prize != args.prize:
            continue
        combos.append((place, act, prize))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, caregiver=caregiver, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.caregiver, params.trait)
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
    StoryParams(place="lane", activity="watch", prize="banner", name="Mira", gender="girl", caregiver="grandmother", trait="curious"),
    StoryParams(place="yard", activity="watch", prize="blanket", name="Toby", gender="boy", caregiver="grandfather", trait="cheery"),
    StoryParams(place="lane", activity="wheel", prize="cart", name="Ruby", gender="girl", caregiver="mother", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print(" ", t)
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
