#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tubby_inspection_bravery_cautionary_comedy.py
==============================================================================

A standalone storyworld for a small comedy domain about a brave child, a
cautionary helper, a very muddy pet, and a last-minute tubby before an
inspection.

Seed words:
- tubby
- inspection

Style:
- Comedy

Features:
- Bravery
- Cautionary

The world is intentionally tiny: one problem, one cautious warning, one comic
attempt at cleanup, and one ending image that proves the room and the pet changed.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    inspection_word: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    splash: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pet:
    id: str
    label: str
    type: str = "pet"
    muddy: bool = True
    comic_sound: str = "splish"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CleanupPlan:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    pet = world.get("pet")
    bath = world.get("bath")
    if pet.meters["wet"] >= THRESHOLD and pet.meters["sudsy"] >= THRESHOLD:
        sig = ("splash", pet.id)
        if sig not in world.fired:
            world.fired.add(sig)
            bath.meters["mess"] += 1
            out.append("__splash__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["bravery"] >= THRESHOLD and hero.memes["worry"] < THRESHOLD:
            sig = ("brave", hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            hero.memes["confidence"] += 1
            out.append(f"{hero.id} took a deep breath and kept going.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("splash", "physical", _r_splash),
    Rule("bravery", "social", _r_bravery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(setting: Setting, activity: Activity, pet: Pet, tool: Tool) -> bool:
    return activity.id in setting.afford and pet.muddy and tool.id == "brush"


def cleanup_ok(plan: CleanupPlan, pet: Pet, delay: int) -> bool:
    return plan.power >= 1 + delay


SETTINGS = {
    "bathroom": Setting(
        "bathroom",
        "the bathroom",
        "the tiny bathroom with a squeaky tub",
        "inspection",
        afford={"tubby"},
    ),
    "mudroom": Setting(
        "mudroom",
        "the mudroom",
        "the little mudroom by the back door",
        "inspection",
        afford={"tubby"},
    ),
}

ACTIVITIES = {
    "tubby": Activity(
        "tubby",
        "give the puppy a tubby",
        "giving the puppy a tubby",
        "wet",
        "drip",
        {"feet", "torso"},
        "tubby",
        tags={"water", "pet", "clean"},
    )
}

PETS = {
    "mudpie": Pet("mudpie", "Muddy", comic_sound="splorf", tags={"pet", "mud"}),
    "flop": Pet("flop", "Flop", comic_sound="splish", tags={"pet", "mud"}),
}

TOOLS = {
    "brush": Tool("brush", "a scruffy brush", "a scruffy brush", "scrub", tags={"clean"}),
    "towel": Tool("towel", "a big towel", "a big towel", "dry", tags={"clean"}),
}

PLANS = {
    "gentle": CleanupPlan(
        "gentle", 3, 3,
        "scrubbed the puppy with warm water, shampoo, and a steady hand until the mud slid away",
        "tried to scrub too fast, but the muddy wiggles beat the plan",
        "washed the puppy carefully until {pet} was clean",
        tags={"clean", "water"},
    ),
    "quick": CleanupPlan(
        "quick", 2, 2,
        "rubbed the puppy dry and did a fast second rinse until the suds were gone",
        "rushed the job and only made more suds",
        "dried the puppy and made the bath sparkle",
        tags={"clean"},
    ),
}

NAMES = ["Mina", "Toby", "Ava", "Ben", "Nora", "Leo", "June", "Milo"]
TRAITS = ["brave", "careful", "curious", "sensible"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    pet: str
    tool: str
    plan: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            for pid, pet in PETS.items():
                for tid, tool in TOOLS.items():
                    if reasonableness_ok(setting, act, pet, tool):
                        combos.append((sid, aid, pid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: tubby, inspection, bravery, cautionary comedy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PETS:
        lines.append(asp.fact("pet", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,P,T) :- setting(S), activity(A), pet(P), tool(T), S = S, A = A, P = P, T = T.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def tell(setting: Setting, activity: Activity, pet: Pet, tool: Tool, plan: CleanupPlan,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         parent_type: str, trait: str, delay: int) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["cautionary"]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    bath = world.add(Entity(id="bath", type="bath", label="the tub"))
    pet_e = world.add(Entity(id="pet", type="pet", label=pet.label))
    pet_e.meters["mud"] = 1
    hero.memes["bravery"] = 1
    helper.memes["worry"] = 1

    world.say(f"On a busy afternoon, {hero.id} and {helper.id} peered at the tub and planned a tubby for {pet.label}.")
    world.say(f"The bathroom was ready for an inspection, which made everyone stand a little straighter than usual.")
    world.say(f"{helper.id} sniffed. \"That puppy is so muddy it could stamp its own footprints,\" {helper.pronoun()} said.")

    world.para()
    world.say(f"{hero.id} grinned with bravery. \"A tubby will fix it!\" {hero.pronoun().capitalize()} said.")
    world.say(f"{helper.id} lifted one cautionary finger. \"Yes, but slowly. Slippery floors make comedy for the floor and trouble for ankles.\"")
    if delay:
        world.say(f"Even the rubber duck looked worried for a moment.")

    world.para()
    pet_e.meters["wet"] += 1
    pet_e.meters["sudsy"] += 1
    pet_e.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(f"They began the tubby anyway, and {pet.label} went {pet.comic_sound}! as the soap bubbles climbed like tiny clouds.")
    world.say(f"{helper.id} kept the {tool.label} ready and reminded {hero.id} to stay brave, not reckless.")

    world.para()
    if cleanup_ok(plan, pet, delay):
        world.say(f"Then {helper.id} helped {hero.id} use {plan.text}.")
        pet_e.meters["mud"] = 0
        pet_e.meters["wet"] = 0
        pet_e.meters["sudsy"] = 0
        bath.meters["mess"] = 0
        parent.memes["pleased"] += 1
        world.say(f"When the inspection came, {parent.label_word} found a clean puppy, a dry floor, and one very proud child.")
        world.say(f"{hero.id} held up {pet.label}, all clean and fluffy, while the duck floated like a tiny parade leader.")
        outcome = "clean"
    else:
        world.say(f"{helper.id} tried to help, but the plan was too quick for all that mud.")
        bath.meters["mess"] += 1
        pet_e.meters["sudsy"] += 1
        world.say(f"The room became one long slide of bubbles, paws, and surprised giggles, and everybody had to start over.")
        outcome = "messy"

    world.facts.update(
        hero=hero, helper=helper, parent=parent, pet=pet_e, bath=bath, tool=tool,
        activity=activity, plan=plan, outcome=outcome
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a small child that includes the words "tubby" and "inspection".',
        f"Tell a story where {f['hero'].id} shows bravery, {f['helper'].id} is cautionary, and a muddy pet gets a tubby before an inspection.",
        f"Write a gentle funny story about a child, a muddy pet, and a careful cleanup plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    pet = f["pet"]
    qa = [
        QAItem("What was the child trying to do?", f"{hero.id} was trying to give {pet.label} a tubby before the inspection."),
        QAItem("Why did the helper warn them?", f"{helper.id} warned them because the puppy was muddy and the bathroom could get slippery. The helper wanted the cleanup to stay funny and safe instead of turning into a slip-and-splash show."),
        QAItem("How did the story end?", f"It ended with a clean puppy and a dry floor, so the inspection went well. The brave child listened to the cautionary helper and the whole room looked ready on purpose."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a tubby?", "A tubby is a kid-friendly word for a bath. It is usually warm, bubbly, and used to get clean."),
        QAItem("What is an inspection?", "An inspection is when someone checks something carefully to see if it is clean, safe, or done the right way."),
        QAItem("Why can a wet floor be dangerous?", "A wet floor can be slippery, so feet can slide by surprise. That is why careful people dry the floor before walking around."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combos.")
    filtered = [c for c in combos
                if (args.setting is None or c[0] == args.setting)
                and (args.activity is None or c[1] == args.activity)
                and (args.pet is None or c[2] == args.pet)
                and (args.tool is None or c[3] == args.tool)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    sid, aid, pid, tid = rng.choice(sorted(filtered))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if hero_gender == "boy" else "boy"
    hero = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    plan = args.plan or rng.choice(sorted(PLANS))
    trait = rng.choice(TRAITS)
    return StoryParams(sid, aid, pid, tid, plan, hero, hero_gender, helper, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], ACTIVITIES[params.activity], PETS[params.pet],
        TOOLS[params.tool], PLANS[params.plan], params.hero, params.hero_gender,
        params.helper, params.helper_gender, params.parent, params.trait, params.delay
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


def asp_verify() -> int:
    clingo = set(asp_valid_combos())
    py = set(valid_combos())
    if clingo == py:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH: ASP gate differs from Python.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: generate smoke test crashed: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("bathroom", "tubby", "mudpie", "brush", "gentle", "Mina", "girl", "Toby", "boy", "mother", "brave"),
            StoryParams("mudroom", "tubby", "flop", "brush", "quick", "Ben", "boy", "Ava", "girl", "father", "careful"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero} and {p.helper}: {p.setting}, {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
