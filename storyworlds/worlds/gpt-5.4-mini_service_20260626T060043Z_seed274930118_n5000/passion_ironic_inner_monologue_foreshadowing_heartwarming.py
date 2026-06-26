#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/passion_ironic_inner_monologue_foreshadowing_heartwarming.py
==============================================================================================================

A small storyworld about a child with a big passion, a little ironic trouble,
and a heartwarming fix.

Seed tale idea:
- A child is passionately making a kite for a family outing.
- The kite's tail is already frayed, which foreshadows trouble.
- The child notices the weakness in an inner monologue, then the wind makes the
  weak spot matter in an ironic way: the thing they love most is the thing that
  is hardest to keep together.
- A loved one helps reinforce the kite, and the final flight becomes the
  warm, happy image that proves what changed.

This script is self-contained, uses stdlib only in the prose path, and imports
the shared result containers eagerly as required.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    traits: list[str] = field(default_factory=list)

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
    place: str
    outdoors: bool
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
    weather: str
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
class Fix:
    id: str
    label: str
    purpose: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    fix: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "yard": Setting("the backyard", True, {"kite"}),
    "hill": Setting("the windy hill", True, {"kite"}),
    "park": Setting("the park", True, {"kite"}),
}

ACTIVITIES = {
    "kite": Activity(
        id="kite",
        verb="fly the kite",
        gerund="flying the kite",
        rush="run into the wind",
        mess="torn",
        soil="frayed and loose",
        zone={"torso", "hands"},
        weather="windy",
        keyword="kite",
        tags={"wind", "string", "paper", "passion", "ironic"},
    )
}

PRIZES = {
    "kite": Prize(
        label="kite",
        phrase="a bright paper kite with a long tail",
        type="kite",
        region="hands",
    )
}

FIXES = {
    "tape": Fix(
        id="tape",
        label="tape",
        purpose="reinforce the kite",
        prep="bring out some tape and paper scraps",
        tail="carefully taped the weak places",
    ),
    "string": Fix(
        id="string",
        label="strong string",
        purpose="steady the kite",
        prep="find stronger string in the basket",
        tail="knotted the string twice so it would hold",
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Rose", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Noah", "Theo", "Ben"]
TRAITS = ["passionate", "gentle", "curious", "bright", "determined"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    if activity.id == "kite" and prize.label == "kite":
        return FIXES["tape"]
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming storyworld: a passionate child, an ironic snag, and a gentle fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} would not truly threaten {prize.label}, "
        f"so there would be no honest tension or heartwarming fix.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_fix(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, activity, prize, "tape", name, gender, helper, trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["joy"] += 1
    actor.meters[activity.mess] += 1
    if narrate:
        world.say(f"{actor.id} kept working, and the kite's weak seam started to look worse.")


def predict_damage(world: World, actor: Entity, activity: Activity, prize: Entity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return True if prize.label == "kite" else False


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
needs_fix(A,P) :- prize_at_risk(A,P), fix(F), repairs(F,A,P).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), needs_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("repairs", fid, "kite", "kite"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, fix: Fix,
         hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["passionate", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper.id,
    ))
    hero.memes["passion"] += 1
    hero.meters["anticipation"] += 1
    world.say(
        f"{hero.id} was a {trait} little {hero.type} with a big passion for {activity.gerund}."
    )
    world.say(
        f"{hero.id} had made {prize_cfg.phrase}, and {hero.pronoun('possessive')} heart fluttered every time the kite lifted."
    )
    world.say(
        f"But on the way to {setting.place}, {hero.id} noticed one tiny thing: a frayed corner on the tail."
    )
    world.say(
        f'In {hero.id}\'s head, a small inner monologue whispered, "That might matter later."'
    )

    world.para()
    world.say(
        f"At {setting.place}, the wind was lively and quick. {hero.id} thought, "
        f'"If the tail tears, my favorite kite may not stay up."'
    )
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the breeze tugged at the weak seam in an almost ironic way: "
        f"the thing {hero.id} loved most was the thing the wind could tease the easiest."
    )
    world.say(
        f"When {hero.id} tried to {activity.rush}, the tail fluttered badly and the tear grew wider."
    )

    world.para()
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} saw the problem too, because that little fray had been foreshadowing trouble all along."
    )
    world.say(
        f'"Let\'s fix it together," {helper.id} said, and {helper.id} went to {fix.prep}.'
    )
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} held the kite still while {helper.id} {fix.tail}."
    )
    world.say(
        f"{hero.id} listened to {hero.pronoun('possessive')} own thoughts again: " 
        f'"We can still make this beautiful."'
    )

    world.para()
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"At last, the kite rose on the wind, steadier than before. "
        f"{hero.id} laughed, {helper.id} laughed, and the repaired tail danced like a ribbon."
    )
    world.say(
        f"It was a heartwarming sight: the same beloved kite, now strong enough to fly, "
        f"and the same child, glowing with pride because patience had helped passion last."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        fix=fix,
        activity=activity,
        setting=setting,
        resolved=True,
        foreshadowed=True,
        ironic=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a gentle story for a young child about {hero.id}, whose passion for "{activity.keyword}" meets an ironic problem.',
        f"Tell a heartwarming story where {hero.id} notices a foreshadowed problem, thinks it through in an inner monologue, and fixes {prize.label}.",
        f'Write a short, cozy story that includes the words "passion" and "ironic" and ends with a happy shared success.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} love to do?",
            answer=f"{hero.id} loved {activity.gerund}, because {hero.pronoun('possessive')} passion for the kite was very strong.",
        ),
        QAItem(
            question=f"What small clue foreshadowed trouble?",
            answer="A frayed corner on the kite's tail foreshadowed that the wind might pull the weak spot apart.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They fixed the kite together with tape so {prize.label} could fly safely in the wind.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and happy, because {hero.pronoun('possessive')} beloved kite was still beautiful and now it could soar.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tape do?",
            answer="Tape can stick pieces together and help a torn thing stay in one piece.",
        ),
        QAItem(
            question="What is a foreshadowing clue?",
            answer="A foreshadowing clue is a little sign early in a story that hints something important may happen later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a character has in their head when they are thinking to themselves.",
        ),
        QAItem(
            question="Why can wind be helpful for a kite?",
            answer="Wind can lift a kite into the sky and help it float and dance.",
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        FIXES[params.fix],
        params.name,
        params.gender,
        params.helper,
        params.trait,
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
    StoryParams(place="hill", activity="kite", prize="kite", fix="tape", name="Mia", gender="girl", helper="mother", trait="passionate"),
    StoryParams(place="park", activity="kite", prize="kite", fix="tape", name="Leo", gender="boy", helper="father", trait="determined"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
