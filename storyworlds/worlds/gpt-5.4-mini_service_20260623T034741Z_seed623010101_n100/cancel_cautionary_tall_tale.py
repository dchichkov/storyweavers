#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/cancel_cautionary_tall_tale.py
===========================================================================================================

A standalone story world for a cautionary tall-tale about a runaway contraption,
a brave warning, and a big stop-word: cancel.

The tiny domain:
- A sky-high kite cart rolls through a prairie fair.
- A child wants the cart to keep going for fun.
- A careful helper spots danger and says "cancel".
- A grown-up uses a real stop action to end the trouble before it grows.

The story is tall-tale flavored: oversized objects, sweeping sky imagery,
and a clear cautionary turn that teaches why stopping early matters.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Contraption:
    id: str
    label: str
    phrase: str
    verb: str
    danger: str
    area: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StopAction:
    id: str
    label: str
    method: str
    power: int
    sense: int
    text: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    if not cart or cart.meters["running"] < THRESHOLD:
        return out
    sig = ("spook", "cart")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["fear"] += 1
    if "dust" in world.entities:
        world.get("dust").meters["swirl"] += 1
    out.append("The ground shook like a drum.")
    return out


CAUSAL_RULES = [Rule("spook", "physical", _r_spook)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(c: Contraption) -> bool:
    return c.area in {"road", "bridge", "fence"} and "runaway" in c.tags


def sensible_actions() -> list[StopAction]:
    return [a for a in STOP_ACTIONS.values() if a.sense >= SENSE_MIN]


def can_stop(action: StopAction, contraption: Contraption) -> bool:
    return action.power >= 2 and hazard_at_risk(contraption)


def predict_run(world: World) -> dict:
    sim = world.copy()
    sim.get("cart").meters["running"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sum(k.memes["fear"] for k in sim.characters()),
        "running": sim.get("cart").meters["running"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, setting: Setting, contraption: Contraption) -> None:
    world.say(
        f"In the broad prairie fair, {child.id} found a cart so big it seemed to have borrowed wheels from a thundercloud."
    )
    world.say(
        f"It was a {contraption.phrase}, all tall ropes and squeaky boards, and the wind kept tapping it like a drum."
    )
    world.say(
        f"{child.id} loved how it looked ready to {contraption.verb}, while {helper.id} watched the sky and the fence posts."
    )


def want_more(world: World, child: Entity, contraption: Contraption) -> None:
    child.memes["want"] += 1
    world.say(
        f'"Let it keep going," {child.id} said. "It feels like the whole sky is pushing us along."'
    )
    world.say(
        f"The cart rolled faster, and its {contraption.area} trail began to rattle behind it."
    )


def warn(world: World, helper: Entity, child: Entity, contraption: Contraption) -> None:
    pred = predict_run(world)
    helper.memes["caution"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{helper.id} pointed at the wobble. "If that thing keeps running, it will scare the horses and scatter the hats," {helper.pronoun()} said.'
    )
    world.say(
        f'"Cancel," {helper.id} called, and the word landed like a flag on a fence post.'
    )


def defy(world: World, child: Entity, contraption: Contraption) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} laughed and tried to keep the cart on its wild path anyway.'
    )


def release_brake(world: World, adult: Entity, contraption: Contraption) -> None:
    cart = world.get("cart")
    cart.meters["running"] = 0.0
    cart.meters["stopped"] = 1.0
    world.say(
        f'Then {adult.id} pulled the brake rope, and the giant cart settled down with a long wooden sigh.'
    )
    world.say(
        f"The wheels quit their clatter, the dust stopped its dance, and the prairie got its quiet back."
    )


def ending(world: World, child: Entity, helper: Entity, contraption: Contraption) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} blinked at the still cart and nodded."
    )
    world.say(
        f'"Next time," {child.id} said, "when the wind says run, we will listen to the one who says cancel first."'
    )
    world.say(
        f"And so the fair went on under the wide sky, with the big cart parked safe and sound, like a horse finally tied to a post."
    )


def tell(setting: Setting, contraption: Contraption, stop_action: StopAction,
         child_name: str, child_type: str, helper_name: str, helper_type: str,
         adult_name: str, adult_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type, role="adult"))
    world.add(Entity(id="cart", kind="thing", type="cart", label=contraption.label))
    world.add(Entity(id="dust", kind="thing", type="dust", label="dust"))
    world.facts.update(
        child=child, helper=helper, adult=adult, setting=setting,
        contraption=contraption, stop_action=stop_action
    )

    introduce(world, child, helper, setting, contraption)
    world.para()
    want_more(world, child, contraption)
    warn(world, helper, child, contraption)
    if stop_action.id == "cancel":
        defy(world, child, contraption)
        world.para()
        release_brake(world, adult, contraption)
        ending(world, child, helper, contraption)
    else:
        release_brake(world, adult, contraption)
        ending(world, child, helper, contraption)

    world.facts["stopped"] = True
    return world


SETTINGS = {
    "fair": Setting(place="the prairie fair", sky="wide blue sky", affords={"runaway"}),
    "ridge": Setting(place="the windy ridge", sky="high windy sky", affords={"runaway"}),
    "road": Setting(place="the country road", sky="long open sky", affords={"runaway"}),
}

CONTRAPTIONS = {
    "kitecart": Contraption(
        id="kitecart",
        label="kite cart",
        phrase="kite cart with sailcloth sails",
        verb="rush across the field",
        danger="runaway",
        area="road",
        tags={"runaway", "wind"},
    ),
    "windwagon": Contraption(
        id="windwagon",
        label="wind wagon",
        phrase="wind wagon with a giant painted wheel",
        verb="dash toward the gate",
        danger="runaway",
        area="bridge",
        tags={"runaway", "wind"},
    ),
    "bannerbarge": Contraption(
        id="bannerbarge",
        label="banner barge",
        phrase="banner barge with ribbon sails",
        verb="roll toward the fence",
        danger="runaway",
        area="fence",
        tags={"runaway", "wind"},
    ),
}

STOP_ACTIONS = {
    "cancel": StopAction(
        id="cancel",
        label="cancel",
        method="call off the ride",
        power=2,
        sense=3,
        text="canceled the ride before it could hurt anyone",
        tags={"cancel", "stop"},
    ),
    "brake": StopAction(
        id="brake",
        label="brake rope",
        method="pull the brake rope",
        power=3,
        sense=3,
        text="pulled the brake rope and stopped the cart",
        tags={"stop", "brake"},
    ),
    "chalk": StopAction(
        id="chalk",
        label="chalk mark",
        method="draw a chalk mark to stop the wheels",
        power=1,
        sense=1,
        text="tried a chalk mark, but it was too small to stop the cart",
        tags={"stop", "chalk"},
    ),
}

GIRL_NAMES = ["Ada", "Mina", "Ruby", "June", "Lia", "Wren", "Nora", "Ivy"]
BOY_NAMES = ["Otis", "Ned", "Jasper", "Abe", "Finn", "Theo", "Milo", "Cal"]
TRAITS = ["careful", "curious", "steady", "sharp-eyed"]


@dataclass
class StoryParams:
    setting: str = "fair"
    contraption: str = "kitecart"
    action: str = "cancel"
    child: str = "Ada"
    child_type: str = "girl"
    helper: str = "Milo"
    helper_type: str = "boy"
    adult: str = "Aunt May"
    adult_type: str = "woman"
    trait: str = "careful"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CONTRAPTIONS:
            for a in STOP_ACTIONS:
                if hazard_at_risk(CONTRAPTIONS[c]) and a in {"cancel", "brake"}:
                    combos.append((s, c, a))
    return combos


KNOWLEDGE = {
    "cancel": [("What does it mean to cancel something?",
                "To cancel something means to stop it before it goes on, or to say that it will not happen.")],
    "wind": [("What can strong wind do?",
              "Strong wind can push, toss, and tip things over if they are not tied down well.")],
    "brake": [("What does a brake do?",
               "A brake helps something slow down or stop moving.")],
    "runaway": [("What is a runaway cart?",
                  "A runaway cart is a cart that keeps moving when nobody can easily control it.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale cautionary story for a young child about a runaway {f["contraption"].label} and the word "cancel".',
        f"Tell a windy prairie story where {f['child'].id} wants to keep the {f['contraption'].label} going, but {f['helper'].id} warns to cancel it before trouble grows.",
        f'Write a big-sky story that teaches why it is wise to stop a runaway thing early, using the word "cancel".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, adult = f["child"], f["helper"], f["adult"]
    c = f["contraption"]
    return [
        QAItem(
            question=f"Who is the story about when {child.id} sees the {c.label} at the fair?",
            answer=f"It is about {child.id}, {helper.id}, and {adult.id}, all standing under the wide prairie sky. The big {c.label} is the thing that starts the trouble.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {child.id} to cancel the {c.label}?",
            answer=f"{helper.id} saw that the {c.label} was getting too wild and could scare people or animals. {helper.id} wanted to stop it early so the trouble would not grow taller than a barn.",
        ),
        QAItem(
            question=f"What did {adult.id} do after the warning?",
            answer=f"{adult.id} pulled the brake rope and stopped the cart. That turned the warning into a safe ending before the wheels could run any farther.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved and learned a lesson. The cart was quiet at last, so the child could see that stopping early was safer than chasing a bigger and bigger problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["contraption"].tags) | set(world.facts["stop_action"].tags)
    out: list[QAItem] = []
    for key in ["cancel", "wind", "brake", "runaway"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="fair", contraption="kitecart", action="cancel", child="Ada", child_type="girl", helper="Milo", helper_type="boy", adult="Aunt May", adult_type="woman", trait="careful"),
    StoryParams(setting="ridge", contraption="windwagon", action="cancel", child="Theo", child_type="boy", helper="Nora", helper_type="girl", adult="Uncle Ben", adult_type="man", trait="sharp-eyed"),
    StoryParams(setting="road", contraption="bannerbarge", action="brake", child="Ruby", child_type="girl", helper="Cal", helper_type="boy", adult="Dad", adult_type="man", trait="steady"),
]


def explain_rejection(action: StopAction) -> str:
    return f"(No story: the action '{action.id}' is not sensible enough for this cautionary tall tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale cautionary storyworld about a runaway contraption and the word cancel.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--contraption", choices=CONTRAPTIONS)
    ap.add_argument("--action", choices=STOP_ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["woman", "man"])
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
    if args.action and STOP_ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError(explain_rejection(STOP_ACTIONS[args.action]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.contraption is None or c[1] == args.contraption)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, contraption, action = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    adult = args.adult or ("Aunt May" if helper_type == "boy" else "Dad")
    adult_type = args.adult_type or ("woman" if "Aunt" in adult or "May" in adult else "man")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, contraption=contraption, action=action,
                       child=child, child_type=child_type, helper=helper, helper_type=helper_type,
                       adult=adult, adult_type=adult_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    contraption = CONTRAPTIONS.get(params.contraption)
    action = STOP_ACTIONS.get(params.action)
    if setting is None:
        raise StoryError("Unknown setting.")
    if contraption is None:
        raise StoryError("Unknown contraption.")
    if action is None:
        raise StoryError("Unknown action.")
    if not hazard_at_risk(contraption):
        raise StoryError("This contraption never becomes dangerous enough for a cautionary tale.")
    if action.sense < SENSE_MIN:
        raise StoryError(explain_rejection(action))
    world = tell(setting, contraption, action, params.child, params.child_type, params.helper, params.helper_type, params.adult, params.adult_type)
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


ASP_RULES = r"""
hazard(C) :- contraption(C), runaway(C).
valid(S,C,A) :- setting(S), contraption(C), action(A), hazard(C), sensible(A).
sensible(A) :- stop_action(A), sense(A,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c, obj in CONTRAPTIONS.items():
        lines.append(asp.fact("contraption", c))
        if "runaway" in obj.tags:
            lines.append(asp.fact("runaway", c))
    for a, obj in STOP_ACTIONS.items():
        lines.append(asp.fact("stop_action", a))
        lines.append(asp.fact("sense", a, obj.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    gate = set(asp_valid_combos())
    py = set(valid_combos())
    ok = gate == py
    if not ok:
        print("MISMATCH between ASP and Python valid_combos")
        print("only in asp:", sorted(gate - py))
        print("only in py:", sorted(py - gate))
        return 1
    print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, contraption=None, action=None, child=None, child_type=None, helper=None, helper_type=None, adult=None, adult_type=None, trait=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED generate() smoke test: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, c, a in asp_valid_combos():
            print(f"  {s:6} {c:12} {a}")
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
            header = f"### {p.child}: {p.contraption} / {p.action}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
