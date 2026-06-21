#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wither_moral_value_heartwarming.py
===================================================================

A small heartwarming storyworld about caring for a wilted plant and learning
that kindness matters more than winning. The story includes a clear problem,
a gentle choice, and an ending image that proves the plant and the people
changed.

Theme:
- A child notices a plant beginning to wither.
- The child wants to hide the problem, but a trusted helper encourages honesty.
- They water, repair, and care for the plant together.
- The plant perks up, and the child learns a moral value: tell the truth and
  help what is fragile before it is too late.

This script follows the shared Storyworld contract:
- stdlib only
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CARE_MIN = 1
TRUTH_MIN = 1


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
class Pot:
    id: str
    label: str
    plant_name: str
    needs_water: bool = True
    withers_when_dry: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CareAction:
    id: str
    label: str
    help_text: str
    effort: int
    kindness: int
    fixes_wither: bool = False
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wither(world: World) -> list[str]:
    out: list[str] = []
    for pot in world.entities.values():
        if pot.kind != "plant" or pot.meters["dry"] < THRESHOLD:
            continue
        sig = ("wither", pot.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        pot.meters["withered"] += 1
        if "child" in world.entities:
            world.get("child").memes["worry"] += 1
        out.append("__wither__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for pot in world.entities.values():
        if pot.kind != "plant" or pot.meters["watered"] < THRESHOLD:
            continue
        sig = ("relief", pot.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if pot.meters["withered"] >= THRESHOLD:
            pot.meters["revived"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("wither", _r_wither), Rule("relief", _r_relief)]


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


def predict_wither(world: World, plant_id: str) -> dict:
    sim = world.copy()
    sim.get(plant_id).meters["dry"] += 1
    propagate(sim, narrate=False)
    plant = sim.get(plant_id)
    return {
        "withered": plant.meters["withered"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def garden_introduction(world: World, child: Entity, helper: Entity, pot: Pot) -> None:
    child.memes["love"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a warm morning, {child.id} and {helper.id} sat beside {pot.label}, "
        f"a small pot with {pot.plant_name} growing in it."
    )
    world.say(
        f"{child.id} liked how the leaves brushed the air, and {helper.id} liked "
        f"how the little garden made the porch feel bright."
    )


def trouble(world: World, child: Entity, pot: Pot) -> None:
    child.memes["notice"] += 1
    world.say(
        f"Then {child.id} saw something sad: {pot.plant_name} had started to wither, "
        f"and the leaves looked tired and soft."
    )
    world.say(f"{child.id} swallowed hard, because {child.pronoun()} did not want the plant to get worse.")


def want_hide(world: World, child: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f"At first, {child.id} wanted to hide the pot behind a chair and hope nobody noticed."
    )


def moral_warning(world: World, helper: Entity, child: Entity, pot: Pot) -> None:
    pred = predict_wither(world, "plant")
    helper.memes["truth"] += 1
    world.facts["predicted_wither"] = pred["withered"]
    world.say(
        f"{helper.id} knelt beside {child.id} and said, "
        f'"If we tell the truth now, we can help {pot.plant_name} before it withers more. '
        f'If we hide it, the plant stays hurt and we lose time."'
    )


def choose_honesty(world: World, child: Entity, helper: Entity) -> None:
    child.memes["truth"] += 1
    child.memes["brave"] += 1
    world.say(
        f"{child.id} took a deep breath and admitted what happened. "
        f"{helper.id} smiled, because being honest was the kind choice."
    )


def water_and_fix(world: World, helper: Entity, child: Entity, pot: Pot, action: CareAction) -> None:
    plant = world.get("plant")
    plant.meters["watered"] += 1
    plant.meters["dry"] = 0.0
    plant.meters["tended"] += 1
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    body = action.help_text.replace("{plant}", pot.plant_name)
    world.say(
        f"Together they {body}. "
        f"{helper.id} checked the soil, {child.id} held the watering cup, and they worked carefully."
    )
    propagate(world, narrate=False)
    if plant.meters["revived"] >= THRESHOLD:
        world.say(
            f"The next little while, the leaves lifted and turned greener, as if the plant had remembered how to smile."
        )
    else:
        world.say(
            f"The plant still looked tired, but the soil was wet again and the care had started."
        )


def ending(world: World, child: Entity, helper: Entity, pot: Pot) -> None:
    world.say(
        f"By the end of the day, {pot.plant_name} stood straighter in its pot, and {child.id} stood a little straighter too."
    )
    world.say(
        f"{child.id} learned that telling the truth early is an act of kindness, and {helper.id} taught that gentle help can bring hope back."
    )
    world.say(
        f"When the sun slid lower, the porch looked warm and quiet, and the once-withered plant had fresh leaves reaching toward the light."
    )


def tell(pot: Pot, action: CareAction, child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    plant = world.add(Entity(id="plant", kind="plant", type="plant", label=pot.label))
    garden_introduction(world, child, helper, pot)
    world.para()
    trouble(world, child, pot)
    want_hide(world, child)
    moral_warning(world, helper, child, pot)
    choose_honesty(world, child, helper)
    world.para()
    water_and_fix(world, helper, child, pot, action)
    world.para()
    ending(world, child, helper, pot)
    world.facts.update(
        child=child,
        helper=helper,
        pot=pot,
        action=action,
        plant=plant,
        outcome="revived" if plant.meters["revived"] >= THRESHOLD else "improving",
        honest=child.memes["truth"] >= THRESHOLD,
    )
    return world


POTS = {
    "sunflower": Pot(id="sunflower", label="a clay pot", plant_name="the sunflower", tags={"plant", "sunflower"}),
    "basil": Pot(id="basil", label="a blue pot", plant_name="the basil", tags={"plant", "basil"}),
    "rose": Pot(id="rose", label="a round pot", plant_name="the rose", tags={"plant", "rose"}),
}

ACTIONS = {
    "water": CareAction(
        id="water",
        label="water the plant",
        help_text="carefully water {plant} and give it a little shade",
        effort=1,
        kindness=2,
        fixes_wither=True,
        tags={"water", "care"},
    ),
    "trim": CareAction(
        id="trim",
        label="trim the plant",
        help_text="gently trim the dry parts and water {plant} after that",
        effort=1,
        kindness=2,
        fixes_wither=True,
        tags={"trim", "care"},
    ),
}

NAMES = [("Mina", "girl"), ("Ella", "girl"), ("Owen", "boy"), ("Noah", "boy"), ("Ruby", "girl"), ("Theo", "boy")]


@dataclass
class StoryParams:
    pot: str
    action: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p in POTS for a in ACTIONS if ACTIONS[a].fixes_wither]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pot = f["pot"]
    action = f["action"]
    return [
        f'Write a heartwarming story for a young child about a plant that can wither and a gentle helper who teaches a moral value.',
        f"Tell a story where {f['child'].id} notices {pot.plant_name} wither, tells the truth, and uses {action.label} to help it recover.",
        f'Write a simple story that includes the word "wither" and ends with a kind lesson about honesty and care.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, pot, action = f["child"], f["helper"], f["pot"], f["action"]
    qa = [
        QAItem(
            question="What problem did the child notice?",
            answer=f"{child.id} noticed that {pot.plant_name} had started to wither. The leaves looked tired, so the child knew it needed help soon.",
        ),
        QAItem(
            question="Why did the helper want the child to tell the truth?",
            answer=f"{helper.id} knew that hiding the problem would waste time. If they were honest right away, they could care for {pot.plant_name} before it got worse.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They worked together and {action.help_text.replace('{plant}', pot.plant_name)}. That gentle care gave the plant water and helped it perk up again.",
        ),
    ]
    if f.get("honest"):
        qa.append(
            QAItem(
                question="What moral value did the child learn?",
                answer="The child learned that telling the truth early is kind and brave. Honest words helped the adults and the plant at the same time.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for a plant to wither?",
            answer="When a plant withers, it looks sad, dry, and droopy because it is not getting enough care or water.",
        ),
        QAItem(
            question="Why do plants need water?",
            answer="Plants need water to stay healthy, grow strong, and keep their leaves from drying out.",
        ),
        QAItem(
            question="Why is honesty a good moral value?",
            answer="Honesty helps people trust each other. It also lets them solve problems sooner, which can keep small troubles from becoming big ones.",
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(pot: Pot, action: CareAction) -> str:
    return f"(No story: {action.label} cannot be applied to {pot.label} in a meaningful way.)"


ASP_RULES = r"""
withered(P) :- plant(P), dry(P), withers_when_dry(P).
revived(P) :- watered(P), withered(P), fixes_wither(P).
moral_value(honesty) :- truth_told.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in POTS.items():
        lines.append(asp.fact("plant", pid))
        if p.needs_water:
            lines.append(asp.fact("needs_water", pid))
        if p.withers_when_dry:
            lines.append(asp.fact("withers_when_dry", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if a.fixes_wither:
            lines.append(asp.fact("fixes_wither", aid))
    lines.append(asp.fact("truth_told"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import tempfile
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about a withering plant, honesty, and care.")
    ap.add_argument("--pot", choices=POTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.pot and args.action and (args.pot, args.action) not in combos:
        raise StoryError(explain_rejection(POTS[args.pot], ACTIONS[args.action]))
    pot = args.pot or rng.choice(list(POTS))
    action = args.action or rng.choice(list(ACTIONS))
    child_name, child_gender = (args.child_name, args.child_gender)
    if not child_name or not child_gender:
        child_name, child_gender = rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice(["Grandma", "Papa", "Aunt June", "Mr. Lee"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    if (pot, action) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(
        pot=pot,
        action=action,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.pot not in POTS or params.action not in ACTIONS:
        raise StoryError("Invalid story parameters.")
    world = tell(POTS[params.pot], ACTIONS[params.action], params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(f"{a}/{b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for pot, action in valid_combos():
            params = StoryParams(
                pot=pot,
                action=action,
                child_name="Mina",
                child_gender="girl",
                helper_name="Grandma",
                helper_gender="woman",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            sample = generate(params)
            sample.params.seed = seed
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
