#!/usr/bin/env python3
"""
A standalone storyworld for a small Adventure-style tale about a hose,
a curious child, and a kind compromise.

Premise:
- A child is curious about a drying patch of sticky glittery slime in a garden.
- They want to use a hose to rinse it clean, but the hose stream could dilute
  a treasured mixture or soak something delicate.
- Kindness enters as a helper who suggests using a gentler nozzle and a bucket
  so the cleaning can happen without ruining the treasure.

This world keeps the simulation small:
- physical meters: wetness, dilutedness, sparkle, worry, helpfulness
- emotional memes: curiosity, kindness, caution, joy, relief, conflict

The narrative is driven by the simulated state, not by a frozen paragraph.
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

NAMES = ["Mina", "Nico", "Tess", "Owen", "Luna", "Pip", "Ari", "Jo", "Mila", "Finn"]
HELPERS = ["grandparent", "neighbor", "older sibling", "friend"]
PLACES = ["the garden", "the backyard", "the little path", "the strawberry patch"]
TREASURES = [
    ("jar of berry paint", "a jar of berry paint", "jar"),
    ("cup of seed tea", "a cup of seed tea", "cup"),
    ("bowl of soap bubbles", "a bowl of soap bubbles", "bowl"),
]
NOZZLES = [
    ("wide spray nozzle", "a wide spray nozzle"),
    ("soft mist nozzle", "a soft mist nozzle"),
    ("gentle sprinkler cap", "a gentle sprinkler cap"),
]


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
    protective: bool = False
    notes: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["wet", "dilute", "sparkle", "worry", "helpfulness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "kindness", "caution", "joy", "relief", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


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
    id: str
    label: str
    phrase: str
    vulnerable_to: set[str]
    diluted_by: set[str]
    owner_role: str = "child"


@dataclass
class Gear:
    id: str
    label: str
    purpose: str
    guards: set[str]
    reduces: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w

    def characters(self):
        return [e for e in self.entities.values() if e.kind == "character"]


def act_hose(world: World, actor: Entity, activity: Activity, prize: Entity) -> None:
    actor.meters["wet"] += 1
    actor.memes["curiosity"] += 1
    world.say(
        f"{actor.id} found a hose by the path and wondered what would happen if "
        f"{actor.pronoun('subject')} turned it on."
    )
    world.say(
        f"{actor.pronoun('subject').capitalize()} loved the feeling of adventure and wanted to {activity.verb}."
    )
    if prize.meters["dilute"] >= THRESHOLD:
        world.say(f"The {prize.label} looked fragile, like it could be ruined if the water came too fast.")


def predict(world: World, actor: Entity, activity: Activity, prize: Entity, gear: Optional[Gear] = None) -> dict:
    sim = world.copy()
    a = sim.get(actor.id)
    p = sim.get(prize.id)
    a.meters["wet"] += 1
    if gear is None:
        p.meters["dilute"] += 1
    else:
        p.meters["dilute"] += 0.2
    return {"ruined": p.meters["dilute"] >= THRESHOLD}


def warn(world: World, helper: Entity, actor: Entity, prize: Entity, activity: Activity) -> None:
    actor.memes["caution"] += 1
    world.say(
        f'{helper.id} smiled kindly and said, "If you blast the {prize.label}, it may dilute and spread everywhere."'
    )
    world.say(
        f'"Let\'s use a gentler way, so the {prize.label} stays just right," {helper.pronoun("subject")} said.'
    )


def compromise(world: World, helper: Entity, actor: Entity, prize: Entity, activity: Activity) -> Gear:
    gear_id, gear_label = rng_choice(world.facts["gear_options"])
    gear = Gear(
        id=gear_id,
        label=gear_label,
        purpose="gentle water control",
        guards={"dilute"},
        reduces={"dilute"},
    )
    world.facts["gear"] = gear
    actor.memes["kindness"] += 1
    world.say(
        f"{helper.id} brought out {gear.label} and showed {actor.id} how to turn the hose into a soft stream."
    )
    return gear


def resolve(world: World, actor: Entity, helper: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    actor.memes["joy"] += 1
    actor.memes["relief"] += 1
    actor.memes["conflict"] = 0.0
    prize.meters["dilute"] += 0.2
    prize.meters["sparkle"] += 1
    world.say(
        f"{actor.id} listened, adjusted the nozzle, and gave the {prize.label} a careful rinse."
    )
    world.say(
        f"The water stayed gentle, the {prize.label} did not dissolve into a mess, and the garden looked bright again."
    )
    world.say(
        f"At the end, {actor.id} and {helper.id} smiled at the fresh path, glad that kindness and curiosity had worked together."
    )


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES)


def rng_choice(seq):
    return random.choice(seq)


SETTINGS = {
    "garden": Setting(place="the garden", affords={"hose"}),
    "backyard": Setting(place="the backyard", affords={"hose"}),
    "path": Setting(place="the little path", affords={"hose"}),
    "strawberries": Setting(place="the strawberry patch", affords={"hose"}),
}

ACTIVITIES = {
    "hose": Activity(
        id="hose",
        verb="spray the dusty stones clean",
        gerund="spraying the stones clean",
        rush="turn the hose on full blast",
        mess="wet",
        soil="soaked and splashed",
        keyword="hose",
        tags={"hose", "water", "adventure"},
    )
}

PRIZES = {
    "berrypaint": Prize(
        id="berrypaint",
        label="berry paint",
        phrase="a jar of berry paint",
        vulnerable_to={"wet"},
        diluted_by={"wet"},
    ),
    "seedtea": Prize(
        id="seedtea",
        label="seed tea",
        phrase="a cup of seed tea",
        vulnerable_to={"wet"},
        diluted_by={"wet"},
    ),
    "soapbubbles": Prize(
        id="soapbubbles",
        label="soap bubbles",
        phrase="a bowl of soap bubbles",
        vulnerable_to={"wet"},
        diluted_by={"wet"},
    ),
}

GEAR = {
    "softnozzle": Gear(
        id="softnozzle",
        label="a soft mist nozzle",
        purpose="gentle water control",
        guards={"wet"},
        reduces={"dilute"},
    ),
    "sprinklercap": Gear(
        id="sprinklercap",
        label="a gentle sprinkler cap",
        purpose="gentle water control",
        guards={"wet"},
        reduces={"dilute"},
    ),
}

KNOWLEDGE = {
    "hose": [
        (
            "What is a hose?",
            "A hose is a long tube that carries water from a tap so you can spray or water things outdoors.",
        )
    ],
    "dilute": [
        (
            "What does dilute mean?",
            "To dilute something is to make it weaker by mixing in more water or another liquid.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help, be gentle, and care about how someone else feels.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to look, ask, and learn about new things.",
        )
    ],
    "adventure": [
        (
            "What is an adventure?",
            "An adventure is an exciting trip or activity where someone explores and discovers something new.",
        )
    ],
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about a hose, curiosity, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos():
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                out.append((place, act, prize))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    rng = random.Random(params.seed)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper.title(), kind="character", type="woman" if params.gender == "girl" else "man"))
    prize = world.add(Entity(
        id=params.prize,
        kind="thing",
        type="treasure",
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=child.id,
        caretaker=helper.id,
    ))
    prize.meters["dilute"] = 0.2
    world.facts["gear_options"] = list(GEAR.items())

    activity = ACTIVITIES[params.activity]

    world.say(
        f"{child.id} was a curious child who loved small adventures in {world.setting.place}."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} noticed {prize.phrase} and wanted to {activity.verb}."
    )
    world.say(
        f"{helper.id} was kind and always watched carefully when water was nearby."
    )

    world.para()
    act_hose(world, child, activity, prize)
    pred = predict(world, child, activity, prize)
    if pred["ruined"]:
        warn(world, helper, child, prize, activity)
        world.say(
            f"{child.id} frowned for a moment, because {child.pronoun('subject')} did not want to ruin anything."
        )
        gear = compromise(world, helper, child, prize, activity)
        world.para()
        resolve(world, child, helper, prize, activity, gear)
    else:
        world.say(f"The water stayed harmless, and the day went on with easy laughter.")

    world.facts.update(
        child=child,
        helper=helper,
        prize=prize,
        activity=activity,
        params=params,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    act = f["activity"]
    return [
        f'Write a short adventure story for a young child that uses the word "{act.keyword}" and includes kindness.',
        f"Tell a story where {child.id} wants to use a hose near {prize.phrase}, but a kind helper suggests a gentler plan.",
        f"Write a child-friendly tale about curiosity, a hose, and keeping {prize.label} from getting diluted.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the hose?",
            answer=f"{child.id} wanted to {act.verb} in {world.setting.place} because {child.pronoun('subject')} was curious about what the hose could do.",
        ),
        QAItem(
            question=f"Why did {helper.id} speak kindly to {child.id}?",
            answer=f"{helper.id} was worried that the water might dilute {prize.phrase}, so {helper.pronoun('subject')} suggested a gentler way.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {child.id} used the hose carefully, {prize.label} stayed safe, and {child.id} felt happy and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["hose", "dilute", "kindness", "curiosity", "adventure"]:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,R) :- place(P), activity(A), prize(R), affords(P,A), at_risk(A,R), has_gentle_fix(A,R).
at_risk(hose, berrypaint).
at_risk(hose, seedtea).
at_risk(hose, soapbubbles).
has_gentle_fix(hose, berrypaint).
has_gentle_fix(hose, seedtea).
has_gentle_fix(hose, soapbubbles).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for act in setting.affords:
            lines.append(asp.fact("affords", place, act))
    for act in ACTIVITIES:
        lines.append(asp.fact("activity", act))
    for prize in PRIZES:
        lines.append(asp.fact("prize", prize))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="garden", activity="hose", prize="berrypaint", name="Mina", gender="girl", helper="grandparent"),
    StoryParams(place="backyard", activity="hose", prize="seedtea", name="Nico", gender="boy", helper="neighbor"),
    StoryParams(place="path", activity="hose", prize="soapbubbles", name="Tess", gender="girl", helper="friend"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
