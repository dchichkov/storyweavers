#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hind_introduce_machinery_kindness_cautionary_moral_value.py
====================================================================================================

A standalone story world for a tall-tale style fable about a hind, an
introducing of machinery, and the lesson that kindness and caution work
better than pride or roughness.

Seed tale shape:
- A hind brings a marvelous machine to a field or clearing.
- Someone wants to rush ahead and use it carelessly.
- The hind warns them about the danger.
- Kindness turns the moment into a safer, better plan.
- The ending leaves a clear moral value image: gentle hands, safe gears,
  and everyone better off than before.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- eager shared results import
- lazy ASP import inside helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- ASP twin with facts and inline rules
- reasonableness gate and verification
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "damage": 0.0, "care": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "caution": 0.0, "pride": 0.0, "fear": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"hind", "mother", "woman", "girl"}
        male = {"buck", "father", "man", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    affords: set[str] = field(default_factory=set)
    wild: bool = False


@dataclass
class Machine:
    id: str
    label: str
    phrase: str
    activity: str
    danger: str
    safe_method: str
    use_line: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.location: str = setting.place
        self.machine_on: bool = False
        self.machine_used: bool = False

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.location = self.location
        clone.machine_on = self.machine_on
        clone.machine_used = self.machine_used
        return clone


@dataclass
class StoryParams:
    place: str
    machine: str
    aid: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the windy meadow", affords={"thresher", "pump", "bellows"}, wild=True),
    "barnyard": Setting(place="the old barnyard", affords={"thresher", "pump"}, wild=True),
    "fairground": Setting(place="the lantern fairground", affords={"music_box", "pump", "bellows"}, wild=False),
    "mill": Setting(place="the river mill", affords={"pump", "thresher"}, wild=False),
}

MACHINES = {
    "thresher": Machine(
        id="thresher",
        label="a brass thresher",
        phrase="a brass thresher with bright teeth",
        activity="thresh the grain",
        danger="its teeth can pinch a careless hoof",
        safe_method="keep paws and hooves away from the spinning teeth",
        use_line="It rumbled like a thundercloud with a work ethic.",
        moral="kind hands and careful steps make hard work safer",
        tags={"machinery", "grains", "safety"},
    ),
    "pump": Machine(
        id="pump",
        label="a tall water pump",
        phrase="a tall water pump with a long handle",
        activity="pump water",
        danger="a sudden yank can splash and slip the floor",
        safe_method="take turns and pump one gentle push at a time",
        use_line="It boomed like a friendly giant clearing its throat.",
        moral="patience keeps a crowd from tumbling",
        tags={"machinery", "water", "safety"},
    ),
    "bellows": Machine(
        id="bellows",
        label="a leather bellows",
        phrase="a leather bellows with a wide mouth",
        activity="feed the forge",
        danger="too much wind can make sparks leap like angry fireflies",
        safe_method="pump it slowly and let the firekeeper watch",
        use_line="It sighed like a sleepy dragon learning manners.",
        moral="good work listens before it roars",
        tags={"machinery", "fire", "safety"},
    ),
    "music_box": Machine(
        id="music_box",
        label="a singing music box",
        phrase="a clockwork music box with silver birds",
        activity="play a tune",
        danger="rough hands can jam the tiny gears",
        safe_method="turn the key gently and leave the lid open only a little",
        use_line="It tinkled like a rain of shiny marbles.",
        moral="gentleness keeps delicate wonders alive",
        tags={"machinery", "music", "care"},
    ),
}

AIDS = {
    "gloves": Aid(
        id="gloves",
        label="soft work gloves",
        covers={"hooves", "hands"},
        guards={"pinch", "spark", "slip", "jam"},
        prep="put on soft work gloves first",
        tail="went to fetch the soft work gloves",
        plural=True,
    ),
    "apron": Aid(
        id="apron",
        label="a sturdy apron",
        covers={"torso"},
        guards={"splash", "spark"},
        prep="tie on a sturdy apron first",
        tail="tied on the sturdy apron",
    ),
    "goggles": Aid(
        id="goggles",
        label="round goggles",
        covers={"eyes"},
        guards={"spark", "dust"},
        prep="pull on round goggles first",
        tail="pulled on the round goggles",
        plural=True,
    ),
}

TRAITS = ["kindly", "brave", "gentle", "thoughtful", "cheerful", "patient", "steady"]
GIRL_NAMES = ["Fern", "Mabel", "Luna", "Nell", "Ruby", "Ada", "Ivy", "Hazel"]
BOY_NAMES = ["Rowan", "Jasper", "Theo", "Silas", "Bram", "Otis", "Eli", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for machine_id in setting.affords:
            for aid_id in AIDS:
                if compatible(MACHINES[machine_id], AIDS[aid_id]):
                    out.append((place, machine_id, aid_id))
    return out


def compatible(machine: Machine, aid: Aid) -> bool:
    risk_map = {
        "pinch": "hooves",
        "splash": "torso",
        "spark": "eyes",
        "dust": "eyes",
        "jam": "hands",
        "slip": "hooves",
    }
    needed = {risk_map.get(k) for k in machine.danger.split() if risk_map.get(k)}
    return any(r in aid.covers for r in needed)


def reasonableness_gate(machine: Machine, aid: Aid) -> bool:
    return compatible(machine, aid)


def select_aid(machine: Machine) -> Optional[Aid]:
    for aid in AIDS.values():
        if compatible(machine, aid):
            return aid
    return None


def predict_mess(world: World, machine: Machine, hero: Entity) -> dict:
    sim = world.copy()
    apply_machine(sim, sim.get(hero.id), machine, narrate=False, safe=False)
    return {
        "risk": sim.get(hero.id).meters["risk"],
        "damage": sim.get(hero.id).meters["damage"],
    }


def introduce(world: World, hero: Entity, machine: Machine) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"In the windy meadow there lived a little {hero.type} named {hero.id}, "
        f"a {hero.traits[0]} hind with a heart as big as a wagon wheel."
    )
    world.say(
        f"{hero.pronoun().capitalize()} knew how to introduce trouble to a machine "
        f"and how to introduce a machine to a crowd without a single hard word."
    )
    world.say(f"One bright morning, {hero.id} rolled out {machine.phrase}. {machine.use_line}")


def admire(world: World, hero: Entity, machine: Machine) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} loved the grand machine, for it could {machine.activity} faster "
        f"than a flock of geese crossing a thunder road."
    )


def gather(world: World, helper: Entity, hero: Entity) -> None:
    world.say(
        f"Folks from the field gathered close, because a hind with a machine can draw "
        f"a crowd the way honey draws bears."
    )
    world.say(
        f"Young {helper.id} craned {helper.pronoun('possessive')} neck and said "
        f'{helper.pronoun().capitalize()} wanted to try it right away.'
    )


def warn(world: World, hero: Entity, helper: Entity, machine: Machine) -> None:
    hero.memes["caution"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f'{hero.id} lifted one steady hoof and said, "Easy now. {machine.danger.capitalize()}. '
        f"We will {machine.safe_method}."'
    )


def careless_reach(world: World, helper: Entity, machine: Machine) -> None:
    helper.memes["pride"] += 1
    helper.memes["fear"] += 1
    world.say(
        f"But {helper.id} was all hot eagerness and reached too near the shining gears."
    )


def offer_aid(world: World, hero: Entity, helper: Entity, machine: Machine) -> Optional[Aid]:
    aid = select_aid(machine)
    if aid is None:
        return None
    world.add(Entity(
        id=aid.id, type="aid", label=aid.label, protective=True,
        covers=set(aid.covers), plural=aid.plural, owner=hero.id,
    ))
    world.say(
        f'{hero.id} smiled a kind, slow smile and said, "First we {aid.prep}, '
        f"and then we can work as steady as a sunrise.""
    )
    return aid


def resolve(world: World, hero: Entity, helper: Entity, machine: Machine, aid: Aid) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    helper.memes["pride"] = 0.0
    world.say(
        f"{helper.id} listened, fetched the {aid.label}, and learned that caution "
        f"was not a wet blanket but a lantern."
    )
    world.say(
        f"Together they {aid.tail}, and then {hero.id} helped {helper.id} "
        f"{machine.activity} the safe way."
    )
    world.say(
        f"The machine hummed like a friendly storm, the crowd cheered, and "
        f"{machine.moral}."
    )


def apply_machine(world: World, actor: Entity, machine: Machine, narrate: bool = True, safe: bool = True) -> None:
    actor.meters["risk"] += 1
    if not safe:
        actor.meters["damage"] += 1
    world.machine_on = True
    world.machine_used = True
    if narrate:
        world.say(f"{actor.id} used {machine.label}.")


def tell(setting: Setting, machine: Machine, aid_cfg: Aid,
         hero_name: str = "Hazel", hero_type: str = "hind",
         hero_traits: Optional[list[str]] = None, helper_type: str = "fawn") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["kindly", "steady"])
    ))
    helper = world.add(Entity(id="Pip", kind="character", type=helper_type, traits=["eager", "young"]))
    world.facts.update(hero=hero, helper=helper, machine=machine, aid_cfg=aid_cfg, setting=setting)

    introduce(world, hero, machine)
    admire(world, hero, machine)

    world.para()
    gather(world, helper, hero)
    warn(world, hero, helper, machine)
    careless_reach(world, helper, machine)

    world.para()
    aid = offer_aid(world, hero, helper, machine)
    if aid is not None:
        resolve(world, hero, helper, machine, aid)

    world.facts["aid"] = aid
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, machine = f["hero"], f["helper"], f["machine"]
    return [
        f'Write a short tall-tale story for a young child about a hind named {hero.id} '
        f"who introduces {machine.label} in {world.setting.place}.",
        f"Tell a gentle cautionary story where {hero.id} keeps {helper.id} safe "
        f"around {machine.phrase} and shows the value of kindness.",
        f'Write a moral tale using the words "hind", "introduce", and "machinery" '
        f"about a brave helper learning to use a machine carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, machine = f["hero"], f["helper"], f["machine"]
    aid = f.get("aid")
    qa = [
        QAItem(
            question=f"Who is the tall-tale story about?",
            answer=f"It is about {hero.id}, a little {hero.type} who is kind, steady, and brave enough to introduce {machine.label}.",
        ),
        QAItem(
            question=f"What did {helper.id} want to do with {machine.label}?",
            answer=f"{helper.id} wanted to try the machine right away, because it looked shiny and exciting.",
        ),
        QAItem(
            question=f"Why did {hero.id} warn {helper.id} to be careful?",
            answer=f"{hero.id} warned {helper.id} because {machine.danger}, so rushing in could cause trouble.",
        ),
    ]
    if aid is not None:
        qa.append(
            QAItem(
                question=f"How did {hero.id} help make the machine safe to use?",
                answer=f"{hero.id} chose {aid.label} first, so {helper.id} could help without getting too close to the danger.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"By the end, {helper.id} listened, the work was safe, and both of them felt proud and happy instead of worried.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    machine: Machine = f["machine"]
    out = [
        QAItem(
            question="What is machinery?",
            answer="Machinery means a machine or a group of machines that use moving parts to do work for people.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle, helpful actions that care about other people.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means warning about a danger so someone can stay safe.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good lesson about how to treat others and how to choose the right thing to do.",
        ),
    ]
    if "machinery" in machine.tags:
        out.append(QAItem(
            question="Why do machines need careful handling?",
            answer="Machines need careful handling because moving parts can pinch, jam, splash, or otherwise hurt someone who is too rough.",
        ))
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", machine="thresher", aid="gloves", name="Hazel", gender="girl", helper="fawn", trait="kindly"),
    StoryParams(place="fairground", machine="music_box", aid="goggles", name="Fern", gender="girl", helper="kid", trait="gentle"),
    StoryParams(place="mill", machine="pump", aid="gloves", name="Mabel", gender="girl", helper="calf", trait="patient"),
]


KNOWLEDGE_ORDER = ["machinery", "kindness", "cautionary", "moral value"]


def explain_rejection(machine: Machine, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} does not sensibly protect the right body parts for "
        f"{machine.label}. The tale needs a real caution and a real safe fix.)"
    )


def valid_story_combo(place: str, machine_id: str, aid_id: str) -> bool:
    return machine_id in SETTINGS[place].affords and compatible(MACHINES[machine_id], AIDS[aid_id])


@dataclass
class StoryParams:
    place: str
    machine: str
    aid: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MACHINES.items():
        lines.append(asp.fact("machine", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tagged", mid, t))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for c in sorted(a.covers):
            lines.append(asp.fact("covers", aid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Machine, Aid) :- affords(Place, Machine), machine(Machine), aid(Aid),
                              tagged(Machine, machinery), compatible(Machine, Aid).
compatible(M, A) :- machine(M), aid(A), tagged(M, machinery), safe_fix(M, A).
safe_fix(M, A) :- machine(M), aid(A), good_cover(M, A).
good_cover(M, A) :- tagged(M, safety), covers(A, hooves).
good_cover(M, A) :- tagged(M, care), covers(A, eyes).
good_cover(M, A) :- tagged(M, water), covers(A, torso).
good_cover(M, A) :- tagged(M, fire), covers(A, eyes).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, m, a) for p, m, a in valid_combos()}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about hind, introduce, machinery, kindness, cautionary moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.machine is None or c[1] == args.machine)
        and (args.aid is None or c[2] == args.aid)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, machine, aid = rng.choice(sorted(filtered))
    gender = args.gender or "girl"
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["fawn", "kid", "calf", "colt"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, machine=machine, aid=aid, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MACHINES[params.machine], AIDS[params.aid], params.name, "hind", [params.trait, "tall-tale"], params.helper)
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
            header = f"### {p.name}: {p.machine} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
