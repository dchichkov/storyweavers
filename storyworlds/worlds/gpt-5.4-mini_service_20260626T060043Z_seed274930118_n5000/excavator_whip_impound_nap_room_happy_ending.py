#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/excavator_whip_impound_nap_room_happy_ending.py
===============================================================================================================

A tiny nursery-rhyme storyworld about a nap room, a toy excavator, a toy whip,
and a gentle impound basket that keeps the room quiet.

Seed tale, imagined from the prompt:
---
In a nap room with soft mats and sleepy bears, a child loves a toy excavator.
One day the child also finds a shiny toy whip and makes loud clip-clop sounds.
The caregiver worries the noise will wake the resting babies and impounds the
whip in a quiet basket.
The child feels grumbly at first, then uses the excavator to build a pillow
nest instead.
The nap room stays hush-hush, and everyone ends with a happy ending.

This script turns that premise into a small causal simulation:
- meters track physical state such as sound, tidiness, and tucked-in comfort;
- memes track feelings such as delight, worry, and calm;
- the story is driven by state changes rather than by a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

NARRATIVE_STYLE = "nursery"
SETTING_NAME = "the nap room"

SOUND_WORDS = {
    "excavator": "whirr-whirr",
    "whip": "whip-whip",
    "impound": "shhh",
    "nap": "hush-hush",
    "happy": "tra-la-la",
}

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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = SETTING_NAME
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    sound: str
    mess: str
    affects_sound: float
    affects_tidy: float
    keyword: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    caregiver: str
    seed: Optional[int] = None


SETTINGS = {
    "nap_room": Setting(place=SETTING_NAME, affords={"quiet_play", "impound", "nap"}),
}

ACTIONS = {
    "excavator": Action(
        id="excavator",
        verb="push the toy excavator along the mat",
        gerund="pushing the toy excavator",
        sound="whirr-whirr",
        mess="tiny-tracks",
        affects_sound=0.2,
        affects_tidy=0.1,
        keyword="excavator",
    ),
    "whip": Action(
        id="whip",
        verb="crack the whip and click it loud",
        gerund="cracking the whip",
        sound="whip-whip",
        mess="noise",
        affects_sound=1.2,
        affects_tidy=0.0,
        keyword="whip",
    ),
    "impound": Action(
        id="impound",
        verb="put the noisy toy in the impound basket",
        gerund="impounding the toy",
        sound="shhh",
        mess="quiet",
        affects_sound=-0.8,
        affects_tidy=0.2,
        keyword="impound",
    ),
    "nap": Action(
        id="nap",
        verb="curl up for a nap",
        gerund="napping",
        sound="hush-hush",
        mess="calm",
        affects_sound=-0.3,
        affects_tidy=0.0,
        keyword="nap",
    ),
}

CHILD_NAMES = ["Maya", "Noah", "Luna", "Theo", "Ivy", "Finn"]
CAREGIVERS = ["mother", "father", "nurse", "helper"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["sound"] >= THRESHOLD and ("noise",) not in world.fired:
        world.fired.add(("noise",))
        child.memes["worry"] += 1
        out.append("The nap room felt loud and lumpy with noise.")
    return out


def _r_impound(world: World) -> list[str]:
    out: list[str] = []
    whip = world.get("whip")
    basket = world.get("basket")
    caregiver = world.get("caregiver")
    child = world.get("child")
    if child.meters["sound"] >= THRESHOLD and whip.worn_by == child.id and ("impound",) not in world.fired:
        world.fired.add(("impound",))
        whip.worn_by = None
        basket.meters["held"] += 1
        caregiver.memes["calm"] += 1
        child.memes["grumble"] += 1
        out.append(f'{caregiver.id.capitalize()} said, "{SOUND_WORDS["impound"]}, the whip goes to the impound basket now."')
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    excavator = world.get("excavator")
    caregiver = world.get("caregiver")
    if child.meters["sound"] < THRESHOLD and child.memes["worry"] >= THRESHOLD and ("happy",) not in world.fired:
        world.fired.add(("happy",))
        child.memes["happy"] += 2
        child.memes["grumble"] = 0
        excavator.meters["tracks"] += 1
        out.append(
            f'{child.id.capitalize()} pushed the excavator softly: "{SOUND_WORDS["excavator"]}, whirr-whirr, under the blanket hill."'
        )
        out.append(
            f'The little hill became a pillow nest, and {caregiver.id} smiled beside {child.pronoun("object")}.'
        )
    return out


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("impound", _r_impound), Rule("happy", _r_happy)]


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


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["nap_room"])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, label=params.child_name))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.caregiver, label=f"the {params.caregiver}"))
    excavator = world.add(Entity(id="excavator", type="toy", label="toy excavator", owner=child.id))
    whip = world.add(Entity(id="whip", type="toy", label="toy whip", owner=child.id))
    basket = world.add(Entity(id="basket", type="thing", label="impound basket", protective=True, caretaker=caregiver.id))

    excavator.worn_by = child.id
    whip.worn_by = child.id

    # Act 1
    world.say(f"In {SETTING_NAME}, {child.id} loved the {excavator.label} best of all.")
    world.say(f'{child.id.capitalize()} rolled it slow and low: "{SOUND_WORDS["excavator"]}, whirr-whirr!"')
    world.say(f"But the shiny {whip.label} made a louder call: "{SOUND_WORDS["whip"]}, whip-whip!"')
    world.para()

    # Act 2
    child.meters["sound"] += 1.3
    whip.meters["noise"] += 1.0
    child.memes["delight"] += 1
    world.say(
        f"The little whip went snap-snap, and the nap room gave a sleepy sigh."
    )
    world.say(
        f"{caregiver.id.capitalize()} looked up and worried the babies would wake."
    )
    propagate(world, narrate=True)
    world.para()

    # Act 3
    if whip.worn_by == child.id:
        world.say(
            f'{child.id.capitalize()} pouted, then listened to the soft hush in the room.'
        )
        world.say(
            f'At last {child.id} tucked the whip in the impound basket and whispered, "{SOUND_WORDS["impound"]}."'
        )
        whip.worn_by = None
        child.meters["sound"] = 0.0
    propagate(world, narrate=True)
    world.say(
        f"Then the excavator dug a nest of pillows, and the nap room turned cozy and bright."
    )
    world.say(
        f"{child.id} curled up for a nap, {SOUND_WORDS['nap']}, and the happy ending shone like a moon lamp."
    )

    world.facts.update(
        child=child,
        caregiver=caregiver,
        excavator=excavator,
        whip=whip,
        basket=basket,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short nursery-rhyme story about {child.id}, a toy excavator, and a toy whip in a nap room.',
        f'Write a gentle story where {child.id} makes noise with a whip, the caregiver impounds it, and the excavator helps with a happy ending.',
        f'Write a child-friendly story with sound effects like "whirr-whirr" and "whip-whip" that ends in a quiet nap room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    return [
        QAItem(
            question=f"What did {child.id} love most in the nap room?",
            answer=f"{child.id} loved the toy excavator most, because it could move slowly and make a soft {SOUND_WORDS['excavator']} sound.",
        ),
        QAItem(
            question=f"Why did {caregiver.id} put the whip in the impound basket?",
            answer=f"{caregiver.id} put the whip in the impound basket because the whip was making loud {SOUND_WORDS['whip']} sounds and the nap room needed to stay quiet.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The ending was happy because the child listened, the whip stayed in the impound basket, and the excavator helped build a cozy pillow nest for nap time.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an excavator?",
            answer="An excavator is a machine or toy with a digging arm that can scoop, push, and move things around.",
        ),
        QAItem(
            question="What does impound mean?",
            answer="To impound something means to take it to a holding place for a while, usually so it can be kept safe or handled later.",
        ),
        QAItem(
            question="Why are sound effects used in stories?",
            answer="Sound effects help a story feel lively and fun, and they let readers hear the action in their minds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("setting", "nap_room"))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    lines.append(asp.fact("allowed", "nap_room", "excavator"))
    lines.append(asp.fact("allowed", "nap_room", "whip"))
    lines.append(asp.fact("allowed", "nap_room", "impound"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(nap_room, excavator, whip) :- setting(nap_room), action(excavator), action(whip), allowed(nap_room, excavator), allowed(nap_room, whip).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("nap_room", "excavator", "whip")}
    cl = set(asp_valid_combos())
    if cl == py:
        print("OK: ASP matches Python gate (1 combo).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a nap room, an excavator, and a whip.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    return StoryParams(child_name=name, child_gender=gender, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(child_name="Maya", child_gender="girl", caregiver="mother"),
    StoryParams(child_name="Noah", child_gender="boy", caregiver="father"),
    StoryParams(child_name="Luna", child_gender="girl", caregiver="helper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combo(s).")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
