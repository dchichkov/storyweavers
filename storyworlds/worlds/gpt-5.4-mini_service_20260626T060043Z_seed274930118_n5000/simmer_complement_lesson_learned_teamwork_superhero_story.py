#!/usr/bin/env python3
"""
storyworlds/worlds/simmer_complement_lesson_learned_teamwork_superhero_story.py
===============================================================================

A small superhero storyworld about a hero, a problem that starts to simmer, and
a teammate whose power perfectly complements the first hero's power.

Premise:
- A young hero wants to stop a troublemaker from causing harm in a small city.
- One hero can freeze / shield / lift / shine, but alone the job is incomplete.
- The problem "simmers" when the villain keeps making small, annoying trouble
  that grows unless it is handled together.

Turn:
- The first hero rushes in too fast and the trouble gets worse.
- A teammate arrives whose power complements the first hero's power.
- They work together, learn a lesson, and calm the situation.

The prose is driven by a simulated world model with physical meters and emotional
memes, plus an ASP twin for the reasonableness gate and compatibility facts.
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
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "team":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Power:
    id: str
    label: str
    attack: str
    defense: str
    mess: str
    calm: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    simmer_key: str
    zone: str
    hurts: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ally:
    id: str
    label: str
    power: str
    complements: str
    helper_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    crowd: str
    afford: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "hero"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_simmer(world: World) -> list[str]:
    out: list[str] = []
    trouble = world.get("trouble")
    if trouble.meters["simmer"] < THRESHOLD:
        return out
    if trouble.meters["chaos"] >= 2:
        sig = ("escalate",)
        if sig not in world.fired:
            world.fired.add(sig)
            trouble.meters["harm"] += 1
            out.append("The trouble kept growing because nobody had slowed it down yet.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    ally = world.get("ally")
    if hero.memes.get("frustration", 0) < THRESHOLD:
        return out
    if ally.memes.get("joined", 0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    ally.memes["hope"] = ally.memes.get("hope", 0) + 1
    world.get("trouble").meters["harm"] = max(0, world.get("trouble").meters["harm"] - 1)
    out.append("Together, they made a plan that fit both powers at once.")
    return out


CAUSAL_RULES = [
    _r_simmer,
    _r_teamwork,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "city": Setting(place="Skyline City", crowd="people watching from the sidewalks", afford={"rescue", "chase"}),
    "harbor": Setting(place="Bright Harbor", crowd="dock workers and gulls", afford={"rescue", "chase"}),
    "museum": Setting(place="the glass museum", crowd="children on a field trip", afford={"rescue"}),
}


POWERS = {
    "shield": Power(
        id="shield",
        label="shield power",
        attack="raise a glowing shield",
        defense="block the flying debris",
        mess="glimmer",
        calm="steady the whole scene",
        tags={"shield", "protect"},
    ),
    "speed": Power(
        id="speed",
        label="speed power",
        attack="dash in a fast blur",
        defense="race ahead to move people out of the way",
        mess="wind",
        calm="clear a path in time",
        tags={"speed", "move"},
    ),
    "light": Power(
        id="light",
        label="light power",
        attack="flash a bright beam",
        defense="show everyone where to stand safely",
        mess="sparkle",
        calm="make the danger easy to see",
        tags={"light", "guide"},
    ),
    "water": Power(
        id="water",
        label="water power",
        attack="pour a strong stream",
        defense="cool the hot sparks",
        mess="splash",
        calm="settle the heat",
        tags={"water", "cool"},
    ),
}

TROUBLES = {
    "smoke": Trouble(
        id="smoke",
        label="smoke cloud",
        phrase="a gray smoke cloud from a broken machine",
        simmer_key="simmer",
        zone="air",
        hurts="made it hard to see",
        tags={"smoke", "heat"},
    ),
    "sparks": Trouble(
        id="sparks",
        label="spark storm",
        phrase="a shower of sparks bouncing across the street",
        simmer_key="simmer",
        zone="street",
        hurts="could sting and scare people",
        tags={"sparks", "heat"},
    ),
    "slime": Trouble(
        id="slime",
        label="sticky slime trail",
        phrase="a sticky slime trail that kept spreading",
        simmer_key="simmer",
        zone="ground",
        hurts="made people slip",
        tags={"slime", "sticky"},
    ),
}

ALLIES = {
    "partner": Ally(
        id="ally",
        label="team partner",
        power="speed",
        complements="shield",
        helper_line="Your shield stops the danger, and my speed gets everyone out first.",
        tags={"teamwork"},
    ),
    "guide": Ally(
        id="ally",
        label="team partner",
        power="light",
        complements="water",
        helper_line="Your water cools the trouble, and my light shows the safe path.",
        tags={"teamwork"},
    ),
    "helper": Ally(
        id="ally",
        label="team partner",
        power="water",
        complements="light",
        helper_line="Your light shows the problem, and my water settles it down.",
        tags={"teamwork"},
    ),
}

HERO_NAMES = ["Nova", "Atlas", "Mira", "Tessa", "Kai", "Iris", "Zane", "Luna"]
ALLY_NAMES = ["Bolt", "Comet", "Echo", "Spark", "Pip", "Vera"]
TRAITS = ["brave", "quick", "kind", "determined", "curious"]


@dataclass
class StoryParams:
    setting: str
    hero_power: str
    ally_power: str
    trouble: str
    name: str
    ally_name: str
    trait: str
    seed: Optional[int] = None


def compatible(hero_power: Power, ally_power: Power, trouble: Trouble) -> bool:
    if hero_power.id == ally_power.id:
        return False
    if trouble.simmer_key != "simmer":
        return False
    pair = {hero_power.id, ally_power.id}
    return pair in ({"shield", "speed"}, {"light", "water"})


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in POWERS:
            for a in POWERS:
                for t in TROUBLES:
                    if compatible(POWERS[h], POWERS[a], TROUBLES[t]):
                        combos.append((s, h, a))
    return combos


def choose_ally_key(hero_power: str) -> str:
    return "partner" if hero_power == "shield" else "guide" if hero_power == "light" else "helper"


def tell(setting: Setting, hero_power: Power, ally_power: Power, trouble: Trouble,
         hero_name: str, ally_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="hero", type="girl", label=hero_name,
        traits=[trait, "super"], meters={"action": 0}, memes={"confidence": 1},
    ))
    ally = world.add(Entity(
        id="ally", kind="hero", type="boy", label=ally_name,
        traits=["team"], meters={"action": 0}, memes={"joined": 0},
    ))
    tr = world.add(Entity(
        id="trouble", kind="trouble", type="thing", label=trouble.label,
        phrase=trouble.phrase, meters={"simmer": 0, "chaos": 0, "harm": 0},
        memes={"annoyance": 1},
    ))

    world.say(f"{hero_name} was a {trait} superhero who protected {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} had a {hero_power.label}, and {ally_name} had a {ally_power.label}.")
    world.say(f"One day, {trouble.phrase} began to simmer near the busy streets.")
    world.para()

    hero.meters["action"] += 1
    tr.meters["simmer"] += 1
    tr.meters["chaos"] += 1
    hero.memes["confidence"] += 1
    world.say(f"{hero_name} rushed in and tried to {hero_power.attack}, but the trouble only got more active.")
    world.say(f"That made the scene simmer even harder, because the danger kept moving.")

    if hero_power.id == "shield":
        world.say(f"{hero_name}'s shield could block harm, but it could not catch everyone fast enough.")
    elif hero_power.id == "light":
        world.say(f"{hero_name}'s light showed the danger clearly, but the trouble still spread.")
    world.para()

    hero.memes["frustration"] = 1
    ally.memes["joined"] = 1
    world.say(f"Then {ally_name} arrived and said, \"{ALLY_NAMES[0] if ally_name == ALLY_NAMES[0] else 'I can help.'}\"")
    world.say(f"{ally_name}'s power complemented {hero_name}'s power, so the two heroes could do different jobs at once.")
    world.say(f"{ALLIES[choose_ally_key(hero_power.id)].helper_line}")
    propagate(world, narrate=True)

    tr.meters["simmer"] = 0
    tr.meters["chaos"] = max(0, tr.meters["chaos"] - 1)
    hero.memes["lesson"] = 1
    ally.memes["lesson"] = 1
    hero.memes["frustration"] = 0
    world.para()
    world.say(f"With teamwork, {hero_name} used {hero_power.defense}, and {ally_name} used {ally_power.defense}.")
    world.say(f"The trouble settled down, the city was safe again, and {hero_name} learned a lesson: the best heroes do not work alone.")
    world.say(f"By the end, the danger was gone, and the two teammates stood side by side, smiling at the quiet street.")
    world.facts.update(hero=hero, ally=ally, trouble=tr, setting=setting, hero_power=hero_power, ally_power=ally_power)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    trouble = f["trouble"]
    setting = f["setting"]
    return [
        f'Write a short superhero story for a young child about teamwork and a problem that starts to simmer in {setting.place}.',
        f"Tell a story where {hero.label} and {ally.label} use powers that complement each other to stop {trouble.label}.",
        f'Write a child-friendly superhero tale that includes the words "simmer" and "complement" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    trouble = f["trouble"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a superhero in {setting.place}, and {ally.label}, who came to help with teamwork.",
        ),
        QAItem(
            question=f"What problem started to simmer in the city?",
            answer=f"{trouble.phrase} started to simmer and spread until the heroes worked together.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn at the end?",
            answer="The lesson learned was that teamwork is strongest when each hero brings a different power that complements the other.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero_power = f["hero_power"]
    ally_power = f["ally_power"]
    out: list[QAItem] = []
    if {hero_power.id, ally_power.id} == {"shield", "speed"}:
        out.append(QAItem(
            question="What does a shield power do?",
            answer="A shield power helps block danger and protect people from harm.",
        ))
        out.append(QAItem(
            question="What does speed help a superhero do?",
            answer="Speed helps a superhero move fast, reach people quickly, and get them to safety.",
        ))
    if {hero_power.id, ally_power.id} == {"light", "water"}:
        out.append(QAItem(
            question="What does light help a superhero do?",
            answer="Light helps a superhero see the problem clearly and show the safe path.",
        ))
        out.append(QAItem(
            question="What does water help a superhero do?",
            answer="Water can cool down heat and help settle a hot, dangerous situation.",
        ))
    out.append(QAItem(
        question="What is teamwork?",
        answer="Teamwork is when people help each other and use their different strengths together.",
    ))
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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="city", hero_power="shield", ally_power="speed", trouble="smoke", name="Nova", ally_name="Bolt", trait="brave"),
    StoryParams(setting="harbor", hero_power="light", ally_power="water", trouble="sparks", name="Mira", ally_name="Echo", trait="kind"),
    StoryParams(setting="museum", hero_power="shield", ally_power="speed", trouble="slime", name="Atlas", ally_name="Comet", trait="determined"),
]


@dataclass
class ASPPair:
    a: str
    b: str


ASP_RULES = r"""
valid_pair(shield,speed).
valid_pair(speed,shield).
valid_pair(light,water).
valid_pair(water,light).

compatible(S,H,A,T) :- setting(S), hero_power(H), ally_power(A), trouble(T), valid_pair(H,A), simmer_trouble(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in POWERS:
        lines.append(asp.fact("hero_power", pid))
        lines.append(asp.fact("ally_power", pid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("simmer_trouble", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with simmering trouble and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-power", choices=POWERS)
    ap.add_argument("--ally-power", choices=POWERS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--name")
    ap.add_argument("--ally-name")
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
    combos = valid_combos()
    combos = [c for c in combos
              if args.setting is None or c[0] == args.setting
              if True else True]
    combos = [c for c in combos
              if args.setting is None or c[0] == args.setting
              and (args.hero_power is None or c[1] == args.hero_power)
              and (args.ally_power is None or c[2] == args.ally_power)]
    if not combos:
        raise StoryError("(No valid superhero combination matches the given options.)")
    setting, hero_power, ally_power = rng.choice(sorted(combos))
    trouble = args.trouble or rng.choice(sorted(TROUBLES))
    name = args.name or rng.choice(HERO_NAMES)
    ally_name = args.ally_name or rng.choice(ALLY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if args.hero_power and args.ally_power and not compatible(POWERS[hero_power], POWERS[ally_power], TROUBLES[trouble]):
        raise StoryError("That hero power and ally power do not complement each other in this world.")
    return StoryParams(setting=setting, hero_power=hero_power, ally_power=ally_power,
                       trouble=trouble, name=name, ally_name=ally_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], POWERS[params.hero_power], POWERS[params.ally_power],
                 TROUBLES[params.trouble], params.name, params.ally_name, params.trait)
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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show compatible/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
            header = f"### {p.name}: {p.hero_power} + {p.ally_power} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
