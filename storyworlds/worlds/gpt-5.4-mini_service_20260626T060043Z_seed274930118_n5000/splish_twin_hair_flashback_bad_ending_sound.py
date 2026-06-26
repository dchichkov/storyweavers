#!/usr/bin/env python3
"""
A small nursery-rhyme-style storyworld about twin children, splishy puddles,
hair ribbons, a remembered flashback, sound effects, and a bad ending.

The domain is intentionally tiny and constraint-checked:
- twin siblings love a splish-splosh game
- their hair is part of the risk state
- rain and puddles make their hair wet and messy
- the story always includes a flashback beat and sound effects
- the ending is a bad ending: no rescue, no fix, just a rainy little regret
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
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
    keyword: str = ""


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
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name1: str
    name2: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("splish", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["tangled"] = item.meters.get("tangled", 0.0) + 1
            out.append(f"The {item.label} went wet and tangled.")
    return out


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("splish", 0.0) < THRESHOLD:
            continue
        sig = ("sound", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["sound"] = True
        out.append("Splish, splosh, swish!")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soak, _r_sound):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "yard": Setting(place="the little yard", indoor=False, affords={"splish"}),
    "garden": Setting(place="the garden path", indoor=False, affords={"splish"}),
    "porch": Setting(place="the porch", indoor=False, affords={"splish"}),
}

ACTIVITIES = {
    "splish": Activity(
        id="splish",
        verb="splish in the puddles",
        gerund="splishing in puddles",
        rush="run to the puddles",
        mess="wet",
        soil="wet and floppy",
        zone={"head"},
        weather="rainy",
        keyword="splish",
    ),
}

PRIZES = {
    "hair": Prize(
        label="hair",
        phrase="their shiny hair",
        type="hair",
        region="head",
    ),
    "ribbons": Prize(
        label="hair ribbons",
        phrase="bright hair ribbons",
        type="ribbons",
        region="head",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="bonnets",
        label="little bonnets",
        covers={"head"},
        guards={"wet"},
        prep="put on little bonnets first",
        tail="put on their little bonnets and came back",
        plural=True,
    )
]

GIRL_NAMES = ["Mimi", "Nina", "Tilly", "Pia", "Lulu", "Rina"]
BOY_NAMES = ["Toby", "Milo", "Ned", "Pip", "Ollie", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act, prize_id))
    return combos


def flashback(world: World, twin1: Entity, twin2: Entity, prize: Entity) -> None:
    world.say(
        f"Flashback: earlier, {twin1.id} and {twin2.id} had brushed {prize.pronoun('possessive')} "
        f"{prize.label} until it looked neat as a kite string."
    )


def introduce(world: World, twin1: Entity, twin2: Entity) -> None:
    world.say(
        f"Once there were twin children, {twin1.id} and {twin2.id}, who liked to bounce in a nursery-rhyme way."
    )


def setup(world: World, twin1: Entity, twin2: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"They loved to {activity.verb}, and {prize.phrase} was the proudest part of their morning."
    )
    world.say(
        f"When they skipped, they sang, 'Clippity-clap, clippity-clow, we like to play in the rain somehow!'"
    )


def arrive(world: World, twin1: Entity, twin2: Entity, activity: Activity) -> None:
    world.para()
    world.say(f"One rainy day, the twins went to {world.setting.place}.")
    world.say("The path winked with tiny puddles.")
    world.say(f"'{activity.keyword.capitalize()}, {activity.keyword.capitalize()}' went the air.")
    world.say("Splish, splosh, swish!")


def risk_and_turn(world: World, twin1: Entity, twin2: Entity, prize: Entity, activity: Activity) -> None:
    twin1.meters["splish"] = 1.0
    twin2.meters["splish"] = 1.0
    world.zone = set(activity.zone)
    propagate(world, narrate=True)
    world.say(
        f"But the water climbed to {prize.pronoun('possessive')} head, and {prize.label} became wet and floppy."
    )
    world.say(
        f"{twin1.id} paused, and {twin2.id} frowned, for the neat morning was turning to a soggy one."
    )


def bad_ending(world: World, twin1: Entity, twin2: Entity, prize: Entity) -> None:
    world.para()
    world.say(
        f"The twins looked for a fix, but no little bonnets were hanging by the door."
    )
    world.say(
        f"So they trotted home with droopy hair, and the rain kept whispering, 'Drip, drop, flop.'"
    )
    world.say(
        f"By bedtime, {prize.label} was still wet, and the nursery song ended with a sigh instead of a cheer."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name1: str, name2: str, parent: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    twin1 = world.add(Entity(id=name1, kind="character", type="girl" if name1 in GIRL_NAMES else "boy"))
    twin2 = world.add(Entity(id=name2, kind="character", type="girl" if name2 in GIRL_NAMES else "boy"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=f"{name1}+{name2}",
        caretaker=parent,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.add(Entity(id="parent", kind="character", type=parent, label=parent))

    introduce(world, twin1, twin2)
    setup(world, twin1, twin2, prize, activity)
    flashback(world, twin1, twin2, prize)
    arrive(world, twin1, twin2, activity)
    risk_and_turn(world, twin1, twin2, prize, activity)
    bad_ending(world, twin1, twin2, prize)

    world.facts.update(
        twin1=twin1,
        twin2=twin2,
        prize=prize,
        activity=activity,
        setting=setting,
        bad_ending=True,
        soiled=prize.meters.get("wet", 0.0) >= THRESHOLD,
        sound=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t1 = f["twin1"]
    t2 = f["twin2"]
    a = f["activity"]
    p = f["prize"]
    return [
        f"Write a nursery-rhyme-style story about twins named {t1.id} and {t2.id} who make a splish sound in the rain.",
        f"Tell a short child story with flashback, sound effects, and a bad ending where {p.label} gets wet.",
        f"Make a tiny rhyme about twin children at {world.setting.place} who want to {a.verb} but end with a rainy sigh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t1 = f["twin1"]
    t2 = f["twin2"]
    p = f["prize"]
    a = f["activity"]
    return [
        QAItem(
            question=f"Who were the twins in the story?",
            answer=f"The twins were {t1.id} and {t2.id}. They liked to play together in the rain.",
        ),
        QAItem(
            question=f"What did the flashback remember before the puddle play?",
            answer=f"The flashback remembered {t1.id} and {t2.id} brushing {p.pronoun('possessive')} {p.label} until it looked neat.",
        ),
        QAItem(
            question=f"What sound did the story repeat when the twins splished?",
            answer="It repeated, 'Splish, splosh, swish!' to sound like little feet in water.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {p.label} got wet and floppy, and the twins went home without a fix.",
        ),
        QAItem(
            question=f"What did the twins want to do at {world.setting.place}?",
            answer=f"They wanted to {a.verb}, which was fun but messy for {p.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that goes back to something that happened earlier.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you hear what is happening, like splish or swish.",
        ),
        QAItem(
            question="What does it mean when hair is wet?",
            answer="Wet hair feels damp and floppy instead of neat and dry.",
        ),
        QAItem(
            question="What is a twin?",
            answer="Twins are two children who are born at the same time and often look very alike.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
soiled(P) :- prize_at_risk(A,P), splish(A).
sound(A) :- splish(A).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about twins, splish, hair, flashback, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    place, activity, prize = rng.choice(combos)
    if args.place:
        place = args.place
    if args.activity:
        activity = args.activity
    if args.prize:
        prize = args.prize
    if (place, activity, prize) not in combos:
        raise StoryError("The requested options do not make a reasonable story.")
    name1 = args.name1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    name2 = args.name2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name1=name1, name2=name2, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name1, params.name2, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t in combos:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        cur = [
            StoryParams(place="yard", activity="splish", prize="hair", name1="Mimi", name2="Toby", parent="mother"),
            StoryParams(place="garden", activity="splish", prize="ribbons", name1="Nina", name2="Pip", parent="father"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
