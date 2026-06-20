#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/basil_planet_damp_humor_folk_tale.py
====================================================================

A standalone story world for a tiny folk tale with humor, centered on basil,
a little planet, and damp weather.

Premise
-------
On a tiny planet, a child gardener wants to help a basil plant stand tall, but
the planet is damp after a misty day. The basil droops, a silly trouble grows,
and a clever helper uses a warm, sensible fix. The ending proves the garden
changed: the basil perks up, the damp patch is managed, and the folk-tale
voice lands on a cheerful laugh.

The world is intentionally small:
- one child gardener
- one basil plant
- one damp patch / puddle / misty problem
- one helper or elder
- one practical remedy that fits the problem

The style aims for:
- Folk Tale cadence
- child-facing concrete prose
- a humorous, slightly playful tone
- a clear state-driven turn and resolution
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
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    vibe: str
    damp_image: str


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    need: str
    root_zone: str
    leaf_zone: str
    thirsty: bool = False
    damp_loving: bool = False


@dataclass
class DampProblem:
    id: str
    label: str
    phrase: str
    source: str
    effect: str
    level: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    tool: str
    action: str
    qa_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dampen_basil(world: World) -> list[str]:
    out: list[str] = []
    basil = world.entities.get("basil")
    damp = world.entities.get("damp")
    if not basil or not damp:
        return out
    if basil.meters["trimmed"] >= THRESHOLD:
        sig = ("perk", basil.id)
        if sig not in world.fired:
            world.fired.add(sig)
            basil.memes["hope"] += 1
            out.append("__perk__")
    return out


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    humor = world.entities.get("child")
    basil = world.entities.get("basil")
    if not humor or not basil:
        return out
    if basil.memes["hope"] >= THRESHOLD and humor.memes["delight"] < 2:
        sig = ("laugh", humor.id)
        if sig not in world.fired:
            world.fired.add(sig)
            humor.memes["delight"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("perk", "plant", _r_dampen_basil), Rule("humor", "social", _r_humor)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, plant: Plant, problem: DampProblem, remedy: Remedy) -> bool:
    return problem.level >= 1 and remedy.power >= 1 and plant.damp_loving is False


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, plant in PLANTS.items():
            for hid, problem in PROBLEMS.items():
                for rid, remedy in REMEDIES.items():
                    if reasonableness_gate(setting, plant, problem, remedy):
                        combos.append((sid, pid, hid))
    return combos


@dataclass
class StoryParams:
    setting: str
    plant: str
    problem: str
    remedy: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def setup(world: World, setting: Setting, plant: Plant, problem: DampProblem, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> tuple[Entity, Entity, Entity, Entity]:
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["bright", "patient"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["wise", "wry"]))
    basil = world.add(Entity(id="basil", kind="plant", type="plant", label=plant.label, role="plant"))
    damp = world.add(Entity(id="damp", kind="thing", type="thing", label=problem.label, role="problem"))
    child.memes["curiosity"] += 1
    helper.memes["goodwill"] += 1
    basil.meters["wilt"] += 1
    damp.meters["wet"] += 1
    world.facts["setting"] = setting
    world.facts["plant_cfg"] = plant
    world.facts["problem_cfg"] = problem
    return child, helper, basil, damp


def tell(setting: Setting, plant: Plant, problem: DampProblem, remedy: Remedy, child_name: str = "Mina", child_gender: str = "girl", helper_name: str = "Uncle Reed", helper_gender: str = "man") -> World:
    world = World()
    child, helper, basil, damp = setup(world, setting, plant, problem, child_name, child_gender, helper_name, helper_gender)

    world.say(
        f"On a tiny planet, in {setting.place}, {child.id} tended a little basil patch while the air stayed {setting.vibe}. "
        f"{setting.damp_image}"
    )
    world.say(
        f"{child.id} stroked the leaves and said, 'Sweet basil, don't droop on me now.' "
        f"The plant gave a tiny, dramatic slump, as if it had heard a joke and was trying not to giggle."
    )

    world.para()
    world.say(
        f"But the ground was {problem.label}, and that made the basil's roots unhappy. "
        f"{child.id} wanted to help at once, though the damp patch kept shining like a puddle with opinions."
    )
    world.say(
        f'"We need {remedy.tool}," {helper.id} said, smelling the air like a soup tester. '
        f'"No wizardry, just the sensible sort."'
    )

    world.para()
    if remedy.id == "warm_stones":
        world.say(
            f"{child.id} gathered warm stones from the sunny path, laid them around the basil, and let the damp breath out slowly. "
            f"The little planet did not object; it only blinked in the sun."
        )
        basil.meters["trimmed"] += 1
        basil.meters["dry"] += 1
        damp.meters["wet"] = 0
        basil.memes["relief"] += 1
        child.memes["pride"] += 1
        propagate(world, narrate=True)
        world.say(
            f"Before long, the basil stood straighter, its leaves curled like green ribbons, and {child.id} laughed because the plant looked almost smug."
        )
        world.say(
            f'"If I had known basil liked warm stones," {child.id} said, "I would have dressed the planet in a blanket!" '
            f'{helper.id} laughed so hard {helper.pronoun()} nearly dropped {helper.pronoun("possessive")} spoon.'
        )
    elif remedy.id == "sponge":
        world.say(
            f"{helper.id} brought a sponge and softly blotted the damp soil, as careful as a mouse carrying a crumb. "
            f"The basil stopped sulking when the water stopped pooling around its roots."
        )
        basil.meters["trimmed"] += 1
        basil.meters["dry"] += 1
        damp.meters["wet"] = 0
        basil.memes["relief"] += 1
        child.memes["pride"] += 1
        propagate(world, narrate=True)
        world.say(
            f"{child.id} peered at the tidy pot and said, 'I see the trick now: a thirsty plant likes water, but not a bathtub.' "
            f"That made both of them grin."
        )
    else:
        world.say(
            f"{helper.id} tried {remedy.action}, but the damp patch kept on winking and the basil stayed wobbly. "
            f"Even the planet seemed to shrug with one muddy shoulder."
        )
        damp.meters["wet"] += 1
        basil.meters["wilt"] += 1
        child.memes["worry"] += 1
        world.say(
            f"So {child.id} and {helper.id} fetched a new plan, because folk tales are kind to people who laugh, think again, and try the right thing."
        )

    world.para()
    world.say(
        f"In the end, the basil smelled bright and peppery, the damp patch was tamed, and {child.id} left the garden smiling at the tiny planet as if it had told a joke back."
    )

    world.facts.update(
        child=child,
        helper=helper,
        basil=basil,
        damp=damp,
        remedy=remedy,
        setting=setting,
        outcome="fixed" if damp.meters["wet"] == 0 else "unfixed",
    )
    return world


SETTINGS = {
    "moon_plot": Setting("moon_plot", "the moon garden", "damp and glittery", "A silver mist sat on the pebbles like spilled milk."),
    "hill_patch": Setting("hill_patch", "the hilltop patch", "cool and damp", "Fog draped the little planet, and every leaf wore a bead of water."),
    "courtyard": Setting("courtyard", "the old courtyard", "misty and damp", "A shallow sheen on the stones made the whole place look freshly washed."),
}

PLANTS = {
    "sweet_basil": Plant("sweet_basil", "basil", "a small pot of basil", "dry soil with a little sun", "roots", "leaves"),
    "king_basil": Plant("king_basil", "basil", "a proud basil crown", "dry soil and warm air", "roots", "leaves"),
}

PROBLEMS = {
    "mist": DampProblem("mist", "damp", "a damp patch", "the night mist", "keeps roots soggy", 1, {"damp"}),
    "puddle": DampProblem("puddle", "damp", "a little puddle", "a leaky pebble seam", "makes soil too wet", 1, {"damp"}),
}

REMEDIES = {
    "warm_stones": Remedy("warm_stones", 3, 3, "warm stones", "set warm stones around the pot", "set warm stones around the basil", "tried to warm the basil, but the damp patch stayed stubborn", {"warm", "dry"}),
    "sponge": Remedy("sponge", 2, 2, "a sponge", "blot the damp soil", "blotted the damp soil", "blotted at the soil, but it was still too wet", {"dry"}),
}

CHILD_NAMES = ["Mina", "Pip", "Luna", "Tobi", "Suri", "Nell", "Oren"]
HELPER_NAMES = ["Uncle Reed", "Aunt Clover", "Old Mara", "Baker Joss"]
GENDERS = ["girl", "boy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, plant, problem, remedy = f["setting"], f["plant_cfg"], f["problem_cfg"], f["remedy"]
    return [
        f'Write a humorous folk tale for a child about {plant.label} on a tiny planet where the garden is {problem.label}.',
        f"Tell a short story in a folk-tale voice where {f['child'].id} tries to help basil on {setting.place} with {remedy.tool}.",
        f'Write a gentle funny story that includes the words "basil", "planet", and "damp", and ends with the basil looking better.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, basil, damp = f["child"], f["helper"], f["basil"], f["damp"]
    remedy = f["remedy"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, who cared for basil on {setting.place}, and {helper.id}, who helped with the fix."),
        ("Why did the basil droop?", f"The basil drooped because the ground was too {damp.label}. Damp soil makes roots unhappy, so the plant looked sulky."),
        ("What did they use to help the basil?", f"They used {remedy.tool}. That was the sensible answer for this tiny garden problem."),
    ]
    if f["outcome"] == "fixed":
        qa.append((
            "How did the story end?",
            f"The basil stood up straighter and looked healthy again. The damp patch was managed, and everyone laughed at how serious the plant had seemed."
        ))
        qa.append((
            f"Why was {helper.id} amused?",
            f"{helper.id} was amused because {child.id} said the planet ought to wear a blanket. It was a funny line, and the joke matched the folk-tale mood."
        ))
    else:
        qa.append((
            "What happened when they tried the first plan?",
            f"The first plan did not solve the damp problem, so the basil stayed wobbly. Then they had to think again and choose a better way."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem_cfg"].tags) | set(world.facts["remedy"].tags) | {"basil"}
    out: list[tuple[str, str]] = []
    if "basil" in tags:
        out.append(("What is basil?", "Basil is a green herb with a bright smell. People often use its leaves in food, and it grows best when its roots are not too wet."))
    if "damp" in tags:
        out.append(("What does damp mean?", "Damp means a little wet or moist. A place can be damp after mist, rain, or a spill."))
    if "warm" in tags:
        out.append(("Why can warmth help plants after damp weather?", "A little warmth can help extra water dry out. If the soil is not soaked, the plant's roots can breathe more easily."))
    if "planet" in tags:
        out.append(("What is a planet?", "A planet is a round world in space that moves around a star. In stories, a planet can feel tiny and friendly like a little village in the sky."))
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_for(params: StoryParams) -> bool:
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = args.setting or rng.choice(list(SETTINGS))
    plant = args.plant or rng.choice(list(PLANTS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    child_gender = args.child_gender or rng.choice(GENDERS)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting, plant, problem, remedy, child, child_gender, helper, helper_gender)


def _verify_smoke() -> None:
    p = StoryParams("courtyard", "sweet_basil", "mist", "warm_stones", "Mina", "girl", "Old Mara", "woman")
    sample = generate(p)
    if not sample.story or "basil" not in sample.story.lower():
        raise StoryError("Smoke test failed: story generation did not produce basil text.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: basil, planet, damp, humor, folk tale.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PLANTS[params.plant],
        PROBLEMS[params.problem],
        REMEDIES[params.remedy],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PLANTS:
        lines.append(asp.fact("plant", p))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,H) :- setting(S), plant(P), problem(H), remedy(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        _verify_smoke()
        print("OK: smoke test story generation succeeded.")
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("courtyard", "sweet_basil", "mist", "warm_stones", "Mina", "girl", "Old Mara", "woman"),
    StoryParams("moon_plot", "king_basil", "puddle", "sponge", "Pip", "boy", "Uncle Reed", "man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
