#!/usr/bin/env python3
"""
A tiny mythic storyworld about a slippery skid, a problem to solve, and a moral choice.

A seed tale idea:
A child or young helper travels a sacred hill path. The path is so slick that
a basket, a runner, or a small cart keeps skidding. Someone warns that rushing
will only cause trouble. The helper listens, finds a simple fix using a mat,
rope, or sand, and the group reaches the shrine safely. The story should feel
like a little myth: clear danger, wise pause, clever solution, and a moral
ending about helping others and choosing care over pride.
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

SKID_WORD = "skid"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"slick": 0.0, "mended": 0.0, "carry": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "pride": 0.0, "wisdom": 0.0, "kindness": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "queen"}
        male = {"boy", "father", "man", "brother", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the stone hill road"
    top: str = "the shrine"
    affords: set[str] = field(default_factory=set)


@dataclass
class Situation:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    zone: str
    keyword: str = "skid"
    moral: str = "care"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = self.zone
        return clone


def truthy(x: float) -> bool:
    return x >= 1.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic skid storyworld with a wise solution and a moral ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--situation", choices=SITUATIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "sister", "brother"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


SETTINGS = {
    "hill": Setting(place="the stone hill road", top="the shrine of dawn", affords={"skid"}),
    "bridge": Setting(place="the old bridge", top="the gate of reeds", affords={"skid"}),
    "courtyard": Setting(place="the temple courtyard", top="the hall of bells", affords={"skid"}),
}

SITUATIONS = {
    "skid": Situation(
        id="skid",
        verb="guide the slipping load",
        gerund="guiding a skidding load",
        rush="rush downhill",
        danger="skid",
        zone="path",
        keyword="skid",
        moral="care",
        tags={"skid", "slippery", "problem"},
    )
}

PRIZES = {
    "basket": Prize(label="basket", phrase="a reed basket of bread", type="basket", region="path", plural=False),
    "lamp": Prize(label="lamp", phrase="a small bronze lamp", type="lamp", region="path", plural=False),
    "cart": Prize(label="cart", phrase="a little wooden cart", type="cart", region="path", plural=False),
}

GEAR = [
    Gear(
        id="mat",
        label="a woven mat",
        covers={"path"},
        guards={"skid"},
        prep="lay down a woven mat first",
        tail="laid down the woven mat and walked the load across it",
    ),
    Gear(
        id="sand",
        label="a pouch of dry sand",
        covers={"path"},
        guards={"skid"},
        prep="scatter dry sand over the slick stones",
        tail="scattered dry sand over the slick stones and made the road safe",
    ),
    Gear(
        id="rope",
        label="a strong rope",
        covers={"path"},
        guards={"skid"},
        prep="tie a strong rope to steady the load",
        tail="tied a strong rope to steady the load",
    ),
]

GIRL_NAMES = ["Asha", "Mira", "Nia", "Lina", "Rosa", "Tala"]
BOY_NAMES = ["Arin", "Kiran", "Soren", "Ivo", "Ravi", "Darin"]


def problem_is_real(sit: Situation, prize: Prize) -> bool:
    return sit.zone == prize.region or sit.id == "skid"


def select_gear(sit: Situation, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if sit.keyword in g.guards and prize.region in g.covers:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for sit_id in setting.affords:
            sit = SITUATIONS[sit_id]
            for prize_id, prize in PRIZES.items():
                if problem_is_real(sit, prize) and select_gear(sit, prize):
                    combos.append((place, sit_id, prize_id))
    return combos


def explain_rejection(sit: Situation, prize: Prize) -> str:
    return (
        f"(No story: this danger does not fit the chosen prize. The {prize.label} must be at risk from a skid "
        f"and there must be a believable tool to make things safe again.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that {PRIZES[prize_id].label} is not a typical {gender}'s item here; try {ok}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SITUATIONS.items():
        lines.append(asp.fact("situation", sid))
        lines.append(asp.fact("danger", sid, s.keyword))
        lines.append(asp.fact("zone", sid, s.zone))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
    return "\n".join(lines)


ASP_RULES = r"""
real_problem(S, P) :- situation(S), prize(P), danger(S, skid), region(P, path).
fix(G, S, P) :- gear(G), real_problem(S, P), guards(G, skid), covers(G, path).
valid(Place, S, P) :- affords(Place, S), real_problem(S, P), fix(_, S, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.situation and args.prize:
        sit, pr = SITUATIONS[args.situation], PRIZES[args.prize]
        if not (problem_is_real(sit, pr) and select_gear(sit, pr)):
            raise StoryError(explain_rejection(sit, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.situation is None or c[1] == args.situation)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, situation, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "sister", "brother"])
    return StoryParams(place=place, situation=situation, prize=prize_id, name=name, gender=gender, helper=helper)


@dataclass
class StoryParams:
    place: str
    situation: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    sit = SITUATIONS[params.situation]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    gear = select_gear(sit, prize_cfg)

    hero.memes["pride"] += 1
    hero.memes["worry"] += 0
    world.say(f"In the old stories, {hero.id} was a small {params.gender} who lived near {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} knew the {SKID_WORD} of the stones could trouble even the brave.")
    world.say(f"One day, {hero.id} carried {prize.phrase} toward {setting.top}.")
    world.say(f"{hero.id} loved the task, because helping others felt like a bright torch in the dark.")

    world.para()
    world.say(f"But the path was slick, and the load began to {SKID_WORD} from side to side.")
    hero.memes["worry"] += 1
    world.say(f"{hero.id} wanted to {sit.rush}, yet the stones warned of trouble.")
    world.say(f"{helper.id} raised a hand and said, \"Do not hurry; a wise heart sees the danger first.\"")
    world.say(f"The warning was true, for the load could {SKID_WORD} down the hill and spill everything.")

    world.para()
    hero.memes["wisdom"] += 1
    helper.memes["kindness"] += 1
    world.say(f"{hero.id} paused, looked at the road, and thought of a kinder way.")
    if gear:
        world.say(f"Then {hero.id} and {helper.id} chose {gear.label}.")
        world.say(f"They {gear.prep}, and the stones no longer made the burden {SKID_WORD}.")
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(f"{gear.tail}, and the offering stayed safe on the way to {setting.top}.")
    world.say(f"When they arrived, the shrine shone quietly, and the people smiled at their care.")
    world.say(f"The old lesson stayed clear: a problem solved with patience can become a blessing for all.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        situation=sit,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, sit, prize = f["hero"], f["helper"], f["situation"], f["prize_cfg"]
    return [
        f'Write a short myth for a child where the word "{SKID_WORD}" appears and a problem is solved with care.',
        f"Tell a gentle myth about {hero.id} and {helper.id} who must keep {prize.phrase} from a {sit.keyword}.",
        f"Write a small story with a wise warning, a careful fix, and a moral about helping others instead of rushing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, sit = f["hero"], f["helper"], f["prize"], f["situation"]
    return [
        QAItem(
            question=f"Who had to solve the problem on the stone road?",
            answer=f"{hero.id} had to solve it with help from {helper.id}.",
        ),
        QAItem(
            question=f"What was the danger that made the load start to {SKID_WORD}?",
            answer=f"The stones were slick, so the load could {SKID_WORD} and spill the offering.",
        ),
        QAItem(
            question=f"How did they keep {prize.label} safe?",
            answer=f"They used {f['gear'].label} so the path became safe and the offering could reach the shrine.",
        ),
        QAItem(
            question="What moral did the story teach?",
            answer="It taught that patience, kindness, and wise problem solving can help everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that often explains a lesson, a custom, or a brave deed.",
        ),
        QAItem(
            question="Why should people be careful on a slippery road?",
            answer="People should be careful because slippery ground can make feet or loads slide and cause a fall.",
        ),
        QAItem(
            question="What does kindness help with in a problem?",
            answer="Kindness helps people work together, listen, and find a solution that keeps everyone safe.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", situation="skid", prize="basket", name="Asha", gender="girl", helper="mother"),
    StoryParams(place="bridge", situation="skid", prize="lamp", name="Ravi", gender="boy", helper="father"),
    StoryParams(place="courtyard", situation="skid", prize="cart", name="Mira", gender="girl", helper="brother"),
]


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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, situation, prize) combos:\n")
        for place, sit, prize in combos:
            print(f"  {place:10} {sit:8} {prize:8}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.situation} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.situation and args.prize:
        sit, pr = SITUATIONS[args.situation], PRIZES[args.prize]
        if not (problem_is_real(sit, pr) and select_gear(sit, pr)):
            raise StoryError(explain_rejection(sit, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.situation is None or c[1] == args.situation)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, situation, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "sister", "brother"])
    return StoryParams(place=place, situation=situation, prize=prize_id, name=name, gender=gender, helper=helper)


if __name__ == "__main__":
    main()
