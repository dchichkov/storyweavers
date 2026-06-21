#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/weaken_nipple_whisk_sound_effects_heartwarming.py
==================================================================================

A tiny heartwarming storyworld about a child helping a caregiver keep a baby
animal fed when a bottle nipple grows weak. The story uses sound effects, a
gentle setback, and a warm repair so the ending image proves what changed.

Seed words:
- weaken
- nipple
- whisk

Style:
- Heartwarming

Feature:
- Sound effects
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
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Item:
    id: str
    label: str
    noun: str
    kind: str
    safe: bool = False
    makes_sound: bool = False
    adds_warmth: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class CareAction:
    id: str
    sense: int
    power: int
    sound: str
    fix: str
    fail: str
    happy: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_item(self, iid: str) -> Item:
        return self.items[iid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bottle = world.items["bottle"]
    if bottle.meters["leaking"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get_entity("child").memes["worry"] += 1
    world.get_entity("caregiver").memes["worry"] += 1
    world.get_item("tablecloth").meters["wet"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


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


def safe_responses() -> list[CareAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def is_reasonable(action: CareAction) -> bool:
    return action.sense >= SENSE_MIN


def would_spill(nipple_age: int) -> bool:
    return nipple_age >= 1


def predict(world: World) -> dict:
    sim = world.copy()
    _weaken_nipple(sim, narrate=False)
    return {
        "spill": sim.get_item("bottle").meters["leaking"] >= THRESHOLD,
        "wet": sim.get_item("tablecloth").meters["wet"] >= THRESHOLD,
    }


def _mix_with_whisk(world: World, caregiver: Entity, bowl: Item) -> None:
    caregiver.memes["care"] += 1
    world.say(
        f'{caregiver.id} took the whisk and went "swish, swish, swish" '
        f'while the warm milk turned smooth in the bowl.'
    )
    bowl.meters["mixed"] += 1


def _weaken_nipple(world: World, narrate: bool = True) -> None:
    bottle = world.get_item("bottle")
    bottle.meters["leaking"] += 1
    bottle.meters["weak"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, child: Entity, caregiver: Entity, baby: Entity) -> None:
    child.memes["joy"] += 1
    caregiver.memes["joy"] += 1
    baby.memes["hope"] += 1
    world.say(
        f"On a cozy afternoon, {child.id} sat beside {caregiver.id} at the little "
        f"kitchen table while {baby.id} wriggled in a blanket nest."
    )
    world.say(
        f'There was a soft bowl, a tiny bottle, and a whisk waiting nearby. '
        f'The room already felt warm and kind.'
    )


def need_help(world: World, child: Entity, caregiver: Entity, baby: Entity) -> None:
    world.say(
        f"{baby.id} gave a tiny \"mew\" and reached for dinner. "
        f'{child.id} smiled and said, "I want to help."'
    )
    world.say(
        f'{caregiver.id} nodded. "You can," {caregiver.pronoun()} said, "but be '
        f'gentle with the bottle nipple."'
    )


def leak_turn(world: World, child: Entity, bottle: Item) -> None:
    world.say(
        f'Then the old nipple went "squeak..." and began to weaken. '
        f"A little drip formed at the tip."
    )
    world.say(
        f'{child.id} pointed. "Oh no, it is getting weaker," {child.pronoun()} said.'
    )


def warn(world: World, caregiver: Entity, child: Entity, bottle: Item) -> None:
    pred = predict(world)
    if pred["spill"]:
        world.facts["predicted_spill"] = True
        world.say(
            f'"Good noticing," {caregiver.id} said softly. "If we keep using that '
            f"nipple, it will leak milk onto the cloth.""
        )


def repair(world: World, caregiver: Entity, child: Entity, action: CareAction, bowl: Item) -> None:
    caregiver.memes["relief"] += 1
    child.memes["relief"] += 1
    world.say(
        f'{caregiver.id} smiled and said, "Let\'s fix it the safe way." '
        f'With a gentle "clink," {caregiver.pronoun()} set out a fresh nipple '
        f'and handed {child.id} the whisk again.'
    )
    _mix_with_whisk(world, caregiver, bowl)
    world.say(
        f'"Now the bottle is ready," {caregiver.id} said, and the air felt '
        f'calm again.'
    )


def ending(world: World, child: Entity, caregiver: Entity, baby: Entity) -> None:
    child.memes["love"] += 1
    caregiver.memes["love"] += 1
    baby.memes["full"] += 1
    world.say(
        f'{baby.id} drank happily from the new nipple, making tiny "glup, glup" '
        f'sounds while {child.id} held the bowl steady.'
    )
    world.say(
        f'Soon there was only a warm kitchen, a clean towel, and {child.id} '
        f'smiling up at {caregiver.id} beside the sleepy baby.'
    )


def tell(action: CareAction, child_name: str = "Mia", child_gender: str = "girl",
         caregiver_name: str = "Mom", caregiver_gender: str = "mother",
         baby_name: str = "Nina", baby_gender: str = "girl") -> World:
    world = World()
    child = world.add_entity(Entity(id=child_name, kind="character", type=child_gender, role="helper"))
    caregiver = world.add_entity(Entity(id=caregiver_name, kind="character", type=caregiver_gender, role="caregiver"))
    baby = world.add_entity(Entity(id=baby_name, kind="character", type=baby_gender, role="baby"))

    bowl = world.add_item(Item(id="bowl", label="bowl", noun="bowl", kind="kitchen"))
    bottle = world.add_item(Item(id="bottle", label="bottle", noun="bottle nipple", kind="feeding"))
    towel = world.add_item(Item(id="tablecloth", label="cloth", noun="tablecloth", kind="cloth"))
    whisk = world.add_item(Item(id="whisk", label="whisk", noun="whisk", kind="tool", makes_sound=True, tags={"whisk"}))
    world.add_item(Item(id="fresh_nipple", label="fresh nipple", noun="fresh nipple", kind="feeding", safe=True, tags={"nipple"}))

    play_setup(world, child, caregiver, baby)
    world.para()
    need_help(world, child, caregiver, baby)
    leak_turn(world, child, bottle)
    warn(world, caregiver, child, bottle)
    world.para()
    if would_spill(1):
        bottle.meters["leaking"] += 1
    _weaken_nipple(world, narrate=True)
    world.say('It went "drip, drip" against the cloth.')
    world.para()
    repair(world, caregiver, child, action, bowl)
    world.para()
    ending(world, child, caregiver, baby)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        baby=baby,
        bowl=bowl,
        bottle=bottle,
        towel=towel,
        whisk=whisk,
        action=action,
        outcome="repaired",
    )
    return world


@dataclass
class StoryParams:
    action: str
    child_name: str = "Mia"
    child_gender: str = "girl"
    caregiver_name: str = "Mom"
    caregiver_gender: str = "mother"
    baby_name: str = "Nina"
    baby_gender: str = "girl"
    seed: Optional[int] = None


ACTIONS = {
    "whisk": CareAction(
        id="whisk",
        sense=3,
        power=3,
        sound="swish, swish, swish",
        fix="mix the milk with the whisk",
        fail="the milk kept dripping onto the cloth",
        happy="used the whisk to make the milk smooth again",
        tags={"whisk"},
    ),
    "gentle_swap": CareAction(
        id="gentle_swap",
        sense=3,
        power=3,
        sound="clink",
        fix="replace the weak nipple",
        fail="the drip kept getting worse",
        happy="swapped in a fresh nipple",
        tags={"nipple"},
    ),
    "towel_and_whisk": CareAction(
        id="towel_and_whisk",
        sense=2,
        power=2,
        sound="pat-pat",
        fix="wipe the cloth and whisk the milk again",
        fail="the spill was too wet to ignore",
        happy="wiped up the spill and whisked the milk again",
        tags={"whisk", "nipple"},
    ),
    "shout_only": CareAction(
        id="shout_only",
        sense=1,
        power=1,
        sound="",
        fix="shout and hope",
        fail="it did not help",
        happy="",
        tags=set(),
    ),
}

SENSE_MIN = 2

CURATED = [
    StoryParams(action="whisk", child_name="Mia", child_gender="girl", caregiver_name="Mom", caregiver_gender="mother", baby_name="Nina", baby_gender="girl"),
    StoryParams(action="gentle_swap", child_name="Theo", child_gender="boy", caregiver_name="Grandma", caregiver_gender="grandmother", baby_name="Pip", baby_gender="boy"),
    StoryParams(action="towel_and_whisk", child_name="Ava", child_gender="girl", caregiver_name="Dad", caregiver_gender="father", baby_name="Rue", baby_gender="girl"),
]


def valid_combos() -> list[tuple[str]]:
    return [(aid,) for aid, action in ACTIONS.items() if is_reasonable(action)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming bottle-and-whisk storyworld.")
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and not is_reasonable(ACTIONS[args.action]):
        raise StoryError("That action is too weak for this story.")
    choices = [a for a in ACTIONS if args.action is None or a == args.action]
    choices = [a for a in choices if is_reasonable(ACTIONS[a])]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(action=rng.choice(choices))


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming story about a child helping in the kitchen with a whisk and a weak bottle nipple.',
        'Tell a gentle story that includes the words "weaken", "nipple", and "whisk", with soft sound effects.',
        'Write a cozy child-friendly story where a small feeding problem is fixed with care and a whisking sound.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What problem happened in the story?",
         "The bottle nipple got weak and started to leak. That made the feeding setup less steady, so the grown-up needed to fix it kindly."),
        ("How did they fix it?",
         "They replaced the weak nipple and whisked the milk again. The whisking made the food smooth, and the new nipple let the baby drink safely."),
        ("How did the story end?",
         "It ended with a calm kitchen and a happy baby drinking from the fresh nipple. The child helped, and everyone felt warm and cared for."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a whisk do?",
         "A whisk helps mix food by spinning through it quickly. It can make milk or batter smooth."),
        ("What is a nipple on a baby bottle?",
         "A bottle nipple is the soft part a baby drinks from. Milk comes through it little by little."),
        ("Why is a weak bottle nipple a problem?",
         "If the nipple weakens, it can leak or fail to feed the baby well. Then the grown-up needs to replace it so feeding stays safe and neat."),
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    for i in world.items.values():
        meters = {k: v for k, v in i.meters.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if i.tags:
            bits.append(f"tags={sorted(i.tags)}")
        lines.append(f"  {i.id:10} ({i.kind:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_good(A) :- action(A), sense(A,S), sense_min(M), S >= M.
valid(A) :- action(A), reasonably_good(A).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, action.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(action=None), random.Random(0)))
        _ = sample.story
        print("OK: ordinary story generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    world = tell(ACTIONS[params.action], params.child_name, params.child_gender,
                 params.caregiver_name, params.caregiver_gender,
                 params.baby_name, params.baby_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid actions:", ", ".join(a for (a,) in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
