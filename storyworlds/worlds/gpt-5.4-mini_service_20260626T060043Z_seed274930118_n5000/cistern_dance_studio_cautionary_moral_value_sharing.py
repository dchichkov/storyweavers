#!/usr/bin/env python3
"""
A small bedtime-story world set in a dance studio with a quiet cistern in the
corner. The story leans on caution, moral value, and sharing: a child wants to
poke too close to the cistern, a grown-up warns them, and the ending turns on a
kind share that helps everyone dance safely.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("wet", "slip", "dirty", "danger", "tidy"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "caution", "sharing", "calm", "curiosity", "bond"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dance studio"
    indoor: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    caution: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str = "cistern"
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
    "dance_studio": Setting(place="the dance studio", indoor=True),
}

ACTIVITIES = {
    "approach_cistern": Activity(
        id="approach_cistern",
        verb="tiptoe toward the cistern",
        gerund="tiptoeing toward the cistern",
        caution="A cistern lid should stay closed, and the floor near it can be slippery.",
        risk="slipping near the water",
        mess="wet",
        zone={"feet"},
        keyword="cistern",
        tags={"cistern", "wet", "caution"},
    ),
    "dance_circle": Activity(
        id="dance_circle",
        verb="dance in a wide circle",
        gerund="dancing in a wide circle",
        caution="Keeping a safe circle leaves room for everyone.",
        risk="bumping elbows",
        mess="tidy",
        zone={"feet", "arms"},
        keyword="sharing",
        tags={"sharing", "moral"},
    ),
}

PRIZES = {
    "blue_ribbon": Prize(
        label="blue ribbon",
        phrase="a bright blue ribbon",
        type="ribbon",
        region="waist",
    ),
    "soft_slippers": Prize(
        label="soft slippers",
        phrase="soft pink slippers",
        type="slippers",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="mats",
        label="foam mats",
        covers={"feet"},
        guards={"wet"},
        prep="unroll the foam mats and dance on the dry spots",
        tail="unrolled the foam mats and kept dancing on the dry spots",
        plural=True,
    ),
    Gear(
        id="shared_ribbons",
        label="a basket of extra ribbons",
        covers={"waist"},
        guards={"tidy"},
        prep="set out a basket of extra ribbons for everyone to share",
        tail="set out the basket and handed ribbons around with smiles",
    ),
]

GIRL_NAMES = ["Maya", "Nina", "Lina", "Sora", "Ava"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Milo", "Ben"]
TRAITS = ["gentle", "curious", "careful", "spirited", "sweet"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "dance_studio"
    activity: str = "approach_cistern"
    prize: str = "soft_slippers"
    name: str = "Maya"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id == "approach_cistern":
        actor.memes["curiosity"] += 1
        actor.memes["caution"] += 1
        actor.meters["danger"] += 1
        world.trace.append("The child moved too close to the cistern.")
    elif activity.id == "dance_circle":
        actor.memes["joy"] += 1
        actor.memes["sharing"] += 1
        actor.memes["calm"] += 1
        world.trace.append("The child danced in a safe circle.")
    if narrate:
        world.say(f"{actor.id} was {activity.gerund}.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str,
         trait: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    parent = world.add(Entity(id="grownup", kind="character", type=parent_type, label="the grown-up", meters={}, memes={}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={},
        memes={},
    ))

    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    prize.worn_by = child.id

    world.say(f"{name} was a {trait} little {gender} who loved the quiet hum of {setting.place}.")
    world.say(f"{name} liked {activity.gerund} and twirling to the soft music under the studio lights.")
    world.say(f"One evening, {name}'s {parent.label} gave {child.pronoun('object')} {prize.phrase}.")
    world.say(f"{name} loved {prize.phrase} and wore {prize.it()} like a ribbon from a happy dream.")

    world.para()
    world.say(f"In a back corner of {setting.place}, there was a round cistern with a heavy lid.")
    world.say(f"{activity.caution} {name} still wanted to peek closer and closer.")
    _do_activity(world, child, activity, narrate=True)

    if activity.id == "approach_cistern":
        child.memes["worry"] += 1
        prize.meters["wet"] += 1
        world.say(f"The floor near the cistern looked shiny, and {name} felt a tiny wobble in {child.pronoun('possessive')} knees.")
        world.say(f"The grown-up said, \"Careful now. The cistern is not a toy, and slippery floors can make a tumble.\"")
        world.say(f"{name} stopped and listened, because the warning sounded wise and warm.")
        world.para()
        world.say(f"Then the grown-up set out {GEAR[1].label} for everyone to share.")
        world.say(f"{name} placed the extra ribbons in a neat line, and the other dancers each chose one kindly.")
        child.memes["sharing"] += 1
        child.memes["calm"] += 1
        child.memes["joy"] += 1
        prize.meters["tidy"] += 1
        world.say(f"After that, {name} kept a safe distance from the cistern and joined the group in a wide circle.")
        world.say(f"They danced softly together, and the room felt bright, safe, and full of sharing.")
    else:
        child.memes["sharing"] += 1
        child.memes["calm"] += 1
        world.say(f"The grown-up smiled and asked everyone to share the open space.")
        world.say(f"{name} helped hand out extra ribbons, and the dancers all took turns in the middle.")
        world.say(f"No one crowded the cistern, and the little dance circle stayed tidy and peaceful.")

    world.facts.update(
        child=child,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        trait=trait,
        resolved=True,
        caution=True,
        sharing=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    return [
        'Write a bedtime story for a small child set in a dance studio with a cistern in the corner.',
        f"Tell a gentle cautionary story where {child.id} is tempted to {activity.verb} but learns a safer choice.",
        "Write a story about sharing ribbons, listening to a warning, and ending with a calm dance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Why did {child.id} stop getting so close to the cistern?",
            answer=f"{child.id} stopped because the grown-up warned that the cistern was not a toy and the floor nearby could be slippery.",
        ),
        QAItem(
            question=f"What did {child.id} share with the other dancers?",
            answer=f"{child.id} helped share the extra ribbons so everyone could take turns and feel included.",
        ),
        QAItem(
            question=f"What stayed safe by the end of the story?",
            answer=f"The studio stayed calm, the cistern stayed closed, and {child.id} kept {prize.it()} neat while dancing safely.",
        ),
        QAItem(
            question=f"What did {child.id} learn from the grown-up's caution?",
            answer=f"{child.id} learned that it is wiser to listen, keep a safe distance from the cistern, and choose a kinder way to play.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cistern?",
            answer="A cistern is a container for holding water. It is usually something people keep closed or covered.",
        ),
        QAItem(
            question="Why should a child be careful near a slippery floor?",
            answer="A slippery floor can make feet slide, and a child might fall or bump into something hard.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something or take turns with it so everyone gets a fair chance.",
        ),
        QAItem(
            question="Why do dancers sometimes practice in a circle?",
            answer="A circle gives everyone room to move without bumping into each other, so the dancing stays safe and smooth.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.extend(f"  {t}" for t in world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(dance_studio).
activity(approach_cistern).
activity(dance_circle).
prize(blue_ribbon).
prize(soft_slippers).

cautionary(approach_cistern).
moral_value(dance_circle).
sharing(dance_circle).
sharing(blue_ribbon).
sharing(soft_slippers).

reasonably_valid(dance_studio, approach_cistern, soft_slippers).
reasonably_valid(dance_studio, dance_circle, blue_ribbon).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(a.tags):
            lines.append(asp.fact(tag, aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.plural:
            lines.append(asp.fact("plural", pid))
        lines.append(asp.fact("wears_on", pid, p.region))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/3."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def python_valid() -> list[tuple]:
    return [("dance_studio", "approach_cistern", "soft_slippers"), ("dance_studio", "dance_circle", "blue_ribbon")]


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP and Python gates match ({len(a)} valid story shapes).")
        return 0
    print("MISMATCH:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Generation API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: dance studio, cistern, caution, and sharing.")
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
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    place = args.place or "dance_studio"
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PRIZES[prize].genders:
        raise StoryError("This story only supports the chosen child/prize pairing.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.trait, params.parent)
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
        print(asp_program("#show reasonably_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid story shapes:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(name="Maya", gender="girl", parent="mother", trait="curious", activity="approach_cistern", prize="soft_slippers")),
            generate(StoryParams(name="Noah", gender="boy", parent="father", trait="gentle", activity="dance_circle", prize="blue_ribbon")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
