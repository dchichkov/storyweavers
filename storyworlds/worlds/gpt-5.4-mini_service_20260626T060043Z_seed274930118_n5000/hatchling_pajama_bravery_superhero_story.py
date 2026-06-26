#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hatchling_pajama_bravery_superhero_story.py
===============================================================================================================

A tiny superhero-style story world about a hatchling, a pajama, and bravery.

Premise:
- A small hatchling loves pretending to be a hero.
- It has a favorite pajama cape.
- A bigger worry appears, and the hatchling must decide whether to hide or be brave.
- A gentle helper and a simple act of courage turn the worry into a proud ending.

The world is intentionally small and constraint-checked: the same simulated
state drives both prose and Q&A.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hatchling"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    atmosphere: str


@dataclass
class Threat:
    id: str
    name: str
    verb: str
    scene: str
    risk: str
    fear: str
    resolve: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    help_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    threat: str
    gear: str
    name: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        nw = World(self.setting)
        nw.entities = copy.deepcopy(self.entities)
        nw.paragraphs = [[]]
        nw.facts = dict(self.facts)
        nw.fired = set(self.fired)
        return nw


SETTINGS = {
    "rooftop": Setting("the rooftop", False, "The moonlit roof felt like a secret stage."),
    "hallway": Setting("the hallway", True, "The hall was quiet, with long shadows and soft floorboards."),
    "garage": Setting("the garage", True, "The garage smelled like dust, rain, and old cardboard."),
}

THREATS = {
    "storm": Threat(
        id="storm",
        name="a thunderstorm",
        verb="face the thunderstorm",
        scene="dark clouds rolled in and the wind rattled the windows",
        risk="the little cape would get soaked and flap away",
        fear="the hatchling might hide under the bed",
        resolve="stand tall and keep going",
        tags={"storm", "rain", "brave"},
    ),
    "dark": Threat(
        id="dark",
        name="the dark hallway",
        verb="walk through the dark hallway",
        scene="the lights flickered and the hallway looked very long",
        risk="the pajama sleeves would shake as the hatchling froze",
        fear="the hatchling might say no and stay put",
        resolve="take one careful step after another",
        tags={"dark", "brave"},
    ),
    "noise": Threat(
        id="noise",
        name="a loud bang",
        verb="check the loud bang",
        scene="a clatter burst from the next room",
        risk="the soft pajama could tangle if the hatchling rushed",
        fear="the hatchling might squeak and run away",
        resolve="use a brave voice and look anyway",
        tags={"noise", "brave"},
    ),
}

GEAR = {
    "pajama": Gear(
        id="pajama",
        label="pajamas",
        phrase="a cozy pajama set",
        help_text="the pajamas felt snug like a tiny hero suit",
        tags={"pajama", "soft", "hero"},
    ),
    "cape": Gear(
        id="cape",
        label="a red blanket cape",
        phrase="a red blanket cape",
        help_text="the cape made the hatchling feel extra heroic",
        tags={"cape", "hero", "brave"},
    ),
    "lantern": Gear(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern",
        help_text="the lantern made the dark feel smaller",
        tags={"light", "brave"},
    ),
}

NAMES = ["Pip", "Milo", "Nina", "Toby", "Luna", "Bea"]
TRAITS = ["small", "curious", "gentle", "bouncy", "sleepy", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for threat_id, threat in THREATS.items():
            for gear_id, gear in GEAR.items():
                if threat_id == "storm" and gear_id in {"cape", "pajama"}:
                    combos.append((place, threat_id, gear_id))
                elif threat_id == "dark" and gear_id in {"lantern", "cape"}:
                    combos.append((place, threat_id, gear_id))
                elif threat_id == "noise" and gear_id in {"cape", "pajama"}:
                    combos.append((place, threat_id, gear_id))
    return combos


def reasonableness_gate(place: str, threat_id: str, gear_id: str) -> bool:
    return (place, threat_id, gear_id) in valid_combos()


def explain_rejection(place: str, threat_id: str, gear_id: str) -> str:
    return (
        f"(No story: {GEAR[gear_id].label} does not make sense for {THREATS[threat_id].name} "
        f"at {SETTINGS[place].place}. The brave fix has to match the danger.)"
    )


def tell(setting: Setting, threat: Threat, gear: Gear, name: str, caretaker: str, trait: str) -> World:
    world = World(setting)
    hatchling = world.add(Entity(
        id=name,
        kind="character",
        type="hatchling",
        traits=[trait, "brave"],
        memes={"bravery": 0.0, "fear": 0.0, "joy": 0.0},
    ))
    adult = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker,
        label=f"the {caretaker}",
        memes={"care": 0.0},
    ))
    costume = world.add(Entity(
        id="Pajama",
        type="pajama",
        label="pajamas",
        phrase=gear.phrase,
        owner=hatchling.id,
        caretaker=adult.id,
        worn_by=hatchling.id,
    ))
    helper = world.add(Entity(
        id=gear.id,
        type=gear.id,
        label=gear.label,
        phrase=gear.phrase,
        owner=hatchling.id,
        caretaker=adult.id,
        protective=True,
    ))
    helper.worn_by = hatchling.id

    world.say(f"{hatchling.id} was a little {trait} hatchling who loved pretending to be a superhero.")
    world.say(f"{hatchling.id} wore {costume.label} and liked how {gear.help_text}.")
    world.say(f"Every night, {hatchling.id} listened for chances to be brave.")

    world.para()
    world.say(f"Then {threat.scene}.")
    hatchling.memes["fear"] += 1
    hatchling.memes["bravery"] += 1
    world.say(f"{hatchling.id} wanted to {threat.verb}, but {threat.fear}.")

    if threat.id == "storm":
        world.say(f'The {caretaker} said, "{threat.resolve}, and I will stay with you."')
    elif threat.id == "dark":
        world.say(f'The {caretaker} said, "We can turn on a light and go together."')
    else:
        world.say(f'The {caretaker} said, "We can check it together. Being brave does not mean being alone."')

    world.para()
    hatchling.memes["fear"] = 0.0
    hatchling.memes["joy"] += 1
    adult.memes["care"] += 1
    world.say(f"{hatchling.id} took a deep breath, held on to {helper.label}, and chose to be brave.")
    world.say(f"{hatchling.id} {threat.resolve} while {gear.help_text}.")
    world.say(f"At the end, {hatchling.id} smiled in {costume.label}, and the scary moment felt smaller than a tiny feather.")

    world.facts = {
        "hero": hatchling,
        "adult": adult,
        "threat": threat,
        "gear": gear,
        "setting": setting,
        "costume": costume,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    threat = f["threat"]
    gear = f["gear"]
    return [
        "Write a short superhero story for a preschooler about a tiny hero who finds bravery.",
        f"Tell a gentle story about {hero.id}, a hatchling in pajamas, who learns to {threat.verb}.",
        f"Write a child-friendly superhero story where {gear.label} helps a hatchling stay brave.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    threat = f["threat"]
    gear = f["gear"]
    setting = f["setting"]
    costume = f["costume"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little hatchling who likes superhero adventures.",
        ),
        QAItem(
            question=f"What did {hero.id} wear?",
            answer=f"{hero.id} wore {costume.label} and also held onto {gear.label} like a tiny hero.",
        ),
        QAItem(
            question=f"What scary thing happened at {setting.place}?",
            answer=f"{threat.scene}, and {hero.id} had to decide whether to hide or be brave.",
        ),
        QAItem(
            question=f"How did the adult help {hero.id}?",
            answer=f"{adult.label.capitalize()} stayed close, gave a calm answer, and helped {hero.id} keep going.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {hero.id} felt brave, and the scary moment felt much smaller.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are pajamas for?",
            answer="Pajamas are soft clothes people wear for sleep and cozy rest.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing to do something scary even when your heart feels shaky.",
        ),
        QAItem(
            question="What does a cape do in a superhero game?",
            answer="A cape helps a pretend superhero feel bold and ready for an adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.protective:
            bits.append("protective=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append("  story beats:")
    lines.extend(f"    - {t}" for t in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Threat, Gear) :- place(Place), threat(Threat), gear(Gear), compatible(Place, Threat, Gear).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in THREATS:
        lines.append(asp.fact("threat", t))
    for g in GEAR:
        lines.append(asp.fact("gear", g))
    for p, t, g in valid_combos():
        lines.append(asp.fact("compatible", p, t, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if py == clingo_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in asp:", sorted(clingo_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: a hatchling, pajamas, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["mother", "father", "aunt", "uncle"], default=None)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place or args.threat or args.gear:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.threat is None or c[1] == args.threat)
            and (args.gear is None or c[2] == args.gear)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, threat, gear = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        threat=threat,
        gear=gear,
        name=args.name or rng.choice(NAMES),
        caretaker=args.caretaker or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(TRAITS),
    )


CURATED = [
    StoryParams(place="rooftop", threat="storm", gear="cape", name="Pip", caretaker="mother", trait="bright"),
    StoryParams(place="hallway", threat="dark", gear="lantern", name="Luna", caretaker="father", trait="curious"),
    StoryParams(place="garage", threat="noise", gear="pajama", name="Milo", caretaker="mother", trait="small"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], THREATS[params.threat], GEAR[params.gear], params.name, params.caretaker, params.trait)
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
        stories = asp_valid_stories()
        print(f"{len(stories)} valid superhero story combos:\n")
        for p, t, g in stories:
            print(f"  {p:8} {t:8} {g:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.threat} at {p.place} ({p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
