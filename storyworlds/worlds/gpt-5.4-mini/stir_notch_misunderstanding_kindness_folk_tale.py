#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stir_notch_misunderstanding_kindness_folk_tale.py
=================================================================================

A small folk-tale storyworld about a village helper, a misunderstood stir, and a
kind ending. A child or young helper sees a spoon with a notch, thinks the stir
means something unkind, and a gentle elder explains the truth. The world model
tracks physical state with meters and emotional state with memes, so the story
turns from misunderstanding to kindness through actual events.

The seed words are woven into the prose:
- stir
- notch

The central features are:
- Misunderstanding
- Kindness

The tone aims for a simple folk tale: a village task, a wrong guess, a patient
explanation, and a warm ending image.
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
SENSE_MIN = 2


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
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    detail: str


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    has_notch: bool = False
    misreadable: bool = False
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Action:
    id: str
    verb: str
    ritual: str
    explanation: str
    kindness: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: ObjectThing) -> ObjectThing:
        self.items[item.id] = item
        return item

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
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["misunderstanding"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["kindness_received"] < THRESHOLD:
            continue
        sig = ("kind", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["peace"] += 1
        out.append("__peace__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("kindness", "social", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable(action: Action, setting: Setting) -> bool:
    return action.sense >= SENSE_MIN and setting.id in SETTINGS


def _do_stir(world: World, helper: Entity, spoon: ObjectThing) -> None:
    helper.meters["work"] += 1
    spoon.meters["used"] += 1


def predict_kindness(world: World, helper: Entity, action: Action) -> bool:
    sim = world.copy()
    _do_stir(sim, sim.get(helper.id), sim.items["spoon"])
    sim.get("child").memes["misunderstanding"] += 1
    return sim.get("child").memes["peace"] >= THRESHOLD


def begin(world: World, child: Entity, elder: Entity, setting: Setting, item: ObjectThing) -> None:
    child.memes["curiosity"] += 1
    elder.memes["calm"] += 1
    world.say(f"Long ago in {setting.place}, {child.id} and {elder.id} worked where {setting.opening}.")
    world.say(f"{setting.detail} There was a wooden spoon there, and its little notch caught the light.")


def misunderstanding(world: World, child: Entity, elder: Entity, item: ObjectThing, action: Action) -> None:
    child.memes["misunderstanding"] += 1
    world.say(f"{child.id} peered at the spoon and frowned. That notch looked like a mark left by anger.")
    world.say(f'"Why are you stirring so hard?" {child.id} asked softly, thinking the stir meant trouble.')


def explain(world: World, elder: Entity, child: Entity, action: Action, item: ObjectThing) -> None:
    elder.memes["kindness_shared"] += 1
    world.say(f'{elder.id} smiled and lifted the spoon. "This notch is from years of use," {elder.pronoun()} said.')
    world.say(f'"I stir the porridge so it will not stick. The stir is work, not a warning."')


def resolve(world: World, elder: Entity, child: Entity, action: Action, item: ObjectThing) -> None:
    child.memes["misunderstanding"] = 0
    child.memes["kindness_received"] += 1
    child.memes["joy"] += 1
    _do_stir(world, elder, world.items["spoon"])
    propagate(world, narrate=False)
    world.say(f"{elder.id} let {child.pronoun('object')} stir once, gently, until the porridge turned smooth.")
    world.say(f'The pot bubbled kindly, and the little notch in the spoon looked like a smile instead of a scar.')
    world.say(f'{child.id} laughed, relieved at the gentleness of it all.')


def tell(setting: Setting, action: Action, child_name: str, child_gender: str,
         elder_name: str, elder_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    pot = world.add_item(ObjectThing(id="pot", label="porridge pot", phrase="a heavy pot of porridge", kind="kitchen", helpful=True))
    spoon = world.add_item(ObjectThing(id="spoon", label="wooden spoon", phrase="a wooden spoon with a notch in its handle", kind="tool", has_notch=True, misreadable=True))
    world.facts.update(child=child, elder=elder, setting=setting, action=action, pot=pot, spoon=spoon)

    begin(world, child, elder, setting, spoon)
    world.para()
    misunderstanding(world, child, elder, spoon, action)
    explain(world, elder, child, action, spoon)
    world.para()
    resolve(world, elder, child, action, spoon)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "hearth": Setting("hearth", "the village hearth", "the elders had set a pot by the fire", "Steam curled from the black pot, and the room smelled of oats and milk."),
    "cottage": Setting("cottage", "the cottage kitchen", "the morning work was quiet and warm", "Sunlight rested on the table, and the wooden floor shone soft as honey."),
    "mill": Setting("mill", "the mill house", "the miller kept soup simmering after the flour was ground", "The old beams creaked, and a cat slept by the hearthstone."),
}

ACTIONS = {
    "stir": Action("stir", "stir", "stir the pot", "to keep the porridge from sticking", "gentle kindness", 3, 2, {"stir", "kindness"}),
    "taste": Action("taste", "taste", "taste the soup", "to check the salt", "gentle kindness", 2, 1, {"taste"}),
}

CHILD_NAMES = ["Mira", "Tobin", "Lena", "Jory", "Nia", "Pippa", "Rowan", "Soren"]
ELDER_NAMES = ["Grandma", "Grandpa", "Aunt May", "Uncle Bram"]
GENDERS = {"girl": "girl", "boy": "boy", "woman": "woman", "man": "man"}


@dataclass
class StoryParams:
    setting: str
    action: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, aid) for sid in SETTINGS for aid in ACTIONS if reasonable(ACTIONS[aid], SETTINGS[sid]) and aid == "stir"]


KNOWLEDGE = {
    "stir": [("What does it mean to stir?", "To stir is to move a spoon around in a pot or bowl so the food mixes and does not stick.")],
    "notch": [("What is a notch?", "A notch is a small cut or dent in something, like a tiny bite taken from wood.")],
    "kindness": [("What is kindness?", "Kindness is when someone is gentle, helpful, and caring to others.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when someone thinks something means one thing, but it really means something else.")],
    "porridge": [("What is porridge?", "Porridge is a warm food made by cooking oats or grains in water or milk until it is soft.")],
}
KNOWLEDGE_ORDER = ["stir", "notch", "kindness", "misunderstanding", "porridge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story that includes the words "stir" and "notch" and ends with kindness.',
        f"Tell a small village story where {f['child'].id} mistakes a notch in a spoon for something unfriendly, but {f['elder'].id} explains the truth kindly.",
        f"Write a gentle tale about misunderstanding and kindness in a kitchen, with a spoon that has a notch and a pot that gets stirred.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, elder, setting = f["child"], f["elder"], f["setting"]
    action = f["action"]
    return [
        ("Where does the story happen?", f"It happens at {setting.place}. The kitchen work there makes the little misunderstanding feel like part of a village tale."),
        ("Why was the child worried?", f"{child.id} thought the notch in the spoon meant something unkind. That guess was a misunderstanding, because the mark only came from years of stirring."),
        ("How did the elder help?", f"{elder.id} answered gently and explained what the spoon was for. Then {elder.id} let {child.id} stir, so kindness could replace the worry."),
        ("How does the story end?", f"It ends with smooth porridge, a calm heart, and a spoon that looks friendly again. The child learns that a kind explanation can fix a misunderstanding."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["action"].tags) | {"stir", "notch", "kindness", "misunderstanding"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for it in world.items.values():
        bits = []
        if it.has_notch:
            bits.append("has_notch=True")
        if it.helpful:
            bits.append("helpful=True")
        if it.misreadable:
            bits.append("misreadable=True")
        if it.meters:
            bits.append(f"meters={dict(it.meters)}")
        lines.append(f"  {it.id:8} (item   ) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hearth", "stir", "Mira", "girl", "Grandma", "woman"),
    StoryParams("cottage", "stir", "Tobin", "boy", "Aunt May", "woman"),
    StoryParams("mill", "stir", "Lena", "girl", "Grandpa", "man"),
]


def explain_rejection() -> str:
    return "(No story: this little folk tale is built around a stir and a notch. Use the stir action.)"


def asp_facts() -> str:
    import asp
    parts = []
    for sid in SETTINGS:
        parts.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        parts.append(asp.fact("action", aid))
        parts.append(asp.fact("sense", aid, a.sense))
        parts.append(asp.fact("power", aid, a.power))
    parts.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(parts)


ASP_RULES = r"""
valid(S, A) :- setting(S), action(A), sense(A, V), sense_min(M), V >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate does not match valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, action=None, child=None, child_gender=None, elder=None, elder_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale storyworld of misunderstanding and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    if args.action and args.action != "stir":
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or "stir"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(setting, action, child, child_gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], params.child, params.child_gender, params.elder, params.elder_gender)
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
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid setting/action combos:")
        for s, a in asp_valid_combos():
            print(f"  {s:10} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
