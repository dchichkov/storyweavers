#!/usr/bin/env python3
"""
storyworlds/worlds/seesaw_curiosity_tall_tale.py
=================================================

A tiny storyworld in a Tall Tale mode: a curious child, a seesaw, a wobble,
and a clever balance that turns a scary lean into a delighted ride.

The world is constraint-checked. It only tells stories when the seesaw setup
is believable: curiosity must lead to a risky lean, then a reasonable helper,
weight, or adjustment must restore balance.
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
    plural: bool = False
    owner: Optional[str] = None
    seated_on: Optional[str] = None
    side: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the schoolyard"
    indoors: bool = False


@dataclass
class Scene:
    seat: str
    hero_side: str
    helper_side: str
    length: str
    twist: str
    keyword: str = "seesaw"


@dataclass
class Helper:
    id: str
    label: str
    type: str
    kind: str = "character"
    weight: int = 1
    lift: str = "hop on the other end"
    balance_hint: str = "steady"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_balance(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    if not hero or not helper:
        return out
    a = world.get(hero.id)
    b = world.get(helper.id)
    if a.seated_on != "seesaw" or b.seated_on != "seesaw":
        return out
    lean = abs(a.meters.get("down_force", 0.0) - b.meters.get("down_force", 0.0))
    if lean >= THRESHOLD and ("balance", a.id, b.id) not in world.fired:
        world.fired.add(("balance", a.id, b.id))
        if a.meters.get("down_force", 0.0) > b.meters.get("down_force", 0.0):
            out.append(f"The seesaw dipped low on one side.")
        else:
            out.append(f"The seesaw tipped the other way with a wild little squeak.")
    return out


def _r_resolve(world: World) -> list[str]:
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    if not hero or not helper:
        return []
    a = world.get(hero.id)
    b = world.get(helper.id)
    key = ("resolve", a.id, b.id)
    if key in world.fired:
        return []
    if abs(a.meters.get("down_force", 0.0) - b.meters.get("down_force", 0.0)) < THRESHOLD:
        world.fired.add(key)
        return [f"The seesaw found its balance and bounced like a happy grin."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_balance, _r_resolve):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(scene: Scene, helper: Helper) -> bool:
    if scene.hero_side == helper.balance_hint:
        return True
    return helper.weight == 1 and scene.length in {"long", "extra long"}


def build_world(setting: Setting, scene: Scene, hero_name: str, hero_type: str,
                helper: Helper) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"curiosity": 1.0, "down_force": 1.0},
        memes={"curiosity": 1.0, "joy": 0.0},
    ))
    buddy = world.add(Entity(
        id=helper.id,
        kind="character",
        type=helper.type,
        label=helper.label,
        meters={"down_force": float(helper.weight)},
        memes={"helpfulness": 1.0},
    ))
    world.facts["hero"] = hero
    world.facts["helper"] = buddy
    return world


def tell(setting: Setting, scene: Scene, hero_name: str = "Milo", hero_type: str = "boy",
         helper: Optional[Helper] = None) -> World:
    if helper is None:
        helper = HELPERS[0]
    if not reasonableness_gate(scene, helper):
        raise StoryError("The chosen helper does not make a believable seesaw balance for this tall tale.")

    world = build_world(setting, scene, hero_name, hero_type, helper)
    hero = world.get(hero_name)
    buddy = world.get(helper.id)

    hero.seated_on = "seesaw"
    hero.side = scene.hero_side
    hero.meters["curiosity"] += 1
    hero.memes["curiosity"] += 1

    world.say(
        f"{hero.id} was a little {hero.type} with curiosity big as a kite, and {hero.pronoun('possessive')} eyes kept drifting to the seesaw in {setting.place}."
    )
    world.say(
        f"That seesaw was so long it looked like it could hold a cloud at one end and a watermelon cart at the other."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to sit on the {scene.hero_side} end and see if the boards would sing under {hero.pronoun('object')}."
    )
    hero.meters["curiosity"] += 1
    hero.memes["joy"] += 0.5
    propagate(world)

    world.para()
    buddy.seated_on = "seesaw"
    buddy.side = scene.helper_side
    buddy.meters["down_force"] += float(helper.weight)
    world.say(
        f"Then {helper.label} came along and said, \"{helper.lift.capitalize()}!\""
    )
    world.say(
        f"{hero.id} blinked at the {scene.twist}, because the seesaw had been leaning like a sleepy tree in a windstorm."
    )
    propagate(world)

    world.para()
    world.say(
        f"But when {helper.label} hopped on the other end, the plank gave a mighty creak, shifted its shoulders, and sprang level again."
    )
    hero.memes["joy"] += 1
    buddy.memes["joy"] = buddy.memes.get("joy", 0.0) + 1
    propagate(world)

    world.para()
    world.say(
        f"Up went {hero.id}, down went {helper.label}, and back again they went, higher than a fence post and merrier than a marching band."
    )
    world.say(
        f"By the end, the seesaw was no longer a wobble machine but a great wooden grin, and {hero.id} laughed so hard the whole yard seemed to bounce."
    )

    world.facts.update(
        hero=hero,
        helper=buddy,
        scene=scene,
        setting=setting,
    )
    return world


SETTINGS = {
    "schoolyard": Setting(place="the schoolyard", indoors=False),
    "park": Setting(place="the park", indoors=False),
    "playground": Setting(place="the playground", indoors=False),
    "fair": Setting(place="the county fair", indoors=False),
}

SCENES = {
    "short": Scene(seat="seesaw", hero_side="high", helper_side="low", length="short", twist="tiny wood board"),
    "long": Scene(seat="seesaw", hero_side="high", helper_side="low", length="long", twist="long board"),
    "extra_long": Scene(seat="seesaw", hero_side="high", helper_side="low", length="extra long", twist="extra-long board"),
}

HELPERS = [
    Helper(id="Nell", label="Nell", type="girl", weight=1, lift="jump on and help me out", balance_hint="steady"),
    Helper(id="Otto", label="Otto", type="boy", weight=2, lift="climb aboard and give it a shove", balance_hint="steady"),
    Helper(id="Mabel", label="Mabel", type="girl", weight=1, lift="hop on the far end", balance_hint="steady"),
]

NAMES = ["Milo", "Nina", "Bea", "Toby", "Rory", "Lena", "Eli", "Pippa"]
TYPES = ["boy", "girl"]


@dataclass
class StoryParams:
    place: str
    scene: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("side", sid, scene.hero_side))
        lines.append(asp.fact("length", sid, scene.length))
    for hid, h in enumerate(HELPERS):
        lines.append(asp.fact("helper", h.id))
        lines.append(asp.fact("helper_weight", h.id, h.weight))
        lines.append(asp.fact("helper_hint", h.id, h.balance_hint))
    return "\n".join(lines)


ASP_RULES = r"""
valid_scene(S) :- scene(S).
valid_helper(H) :- helper(H).

compatible(S, H) :- valid_scene(S), valid_helper(H),
                    length(S, L), helper_weight(H, W),
                    helper_hint(H, steady), W >= 1, L != short.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, scene in SCENES.items():
        for h in HELPERS:
            if reasonableness_gate(scene, h):
                out.append((sid, h.id))
    return sorted(out)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} compatible scenes.")
        return 0
    print("MISMATCH:")
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    if py - cl:
        print(" only in Python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    scene = f["scene"]
    return [
        f'Write a Tall Tale for a child named {hero.id} who is curious about a seesaw at {world.setting.place}.',
        f"Tell a big-hearted story where {hero.id} and {helper.label} make the seesaw at {world.setting.place} balance again.",
        f'Write a short, lively story that includes the word "seesaw" and ends with a happy bounce.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What was {hero.id} curious about at {world.setting.place}?",
            answer=f"{hero.id} was curious about the seesaw at {world.setting.place}, and {hero.pronoun('possessive')} curiosity pulled {hero.pronoun('object')} right toward it.",
        ),
        QAItem(
            question=f"Who helped make the seesaw level again?",
            answer=f"{helper.label} helped. When {helper.label} hopped on the other end, the seesaw stopped leaning and settled back into balance.",
        ),
        QAItem(
            question=f"What did the seesaw look like after the helper joined in?",
            answer="It looked steady and happy, like a wooden grin that could bounce the day itself.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seesaw?",
            answer="A seesaw is a long board that rocks up and down on a middle support when children sit on the two ends.",
        ),
        QAItem(
            question="Why do two children have to balance a seesaw?",
            answer="They have to balance it so one side does not slam to the ground and the ride can go up and down smoothly.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.seated_on:
            bits.append(f"seated_on={e.seated_on}")
        if e.side:
            bits.append(f"side={e.side}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="schoolyard", scene="long", helper="Nell", name="Milo", gender="boy"),
    StoryParams(place="park", scene="extra_long", helper="Otto", name="Nina", gender="girl"),
    StoryParams(place="playground", scene="long", helper="Mabel", name="Bea", gender="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A Tall Tale storyworld about curiosity and a seesaw.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=TYPES)
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
    valid = []
    for sid, helper_id in valid_combos():
        if args.scene is not None and sid != args.scene:
            continue
        if args.helper is not None and helper_id != args.helper:
            continue
        valid.append((sid, helper_id))
    if not valid:
        raise StoryError("(No valid seesaw tale matches the given options.)")
    scene, helper = rng.choice(valid)
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(TYPES)
    return StoryParams(place=place, scene=scene, helper=helper, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SCENES[params.scene], params.name, params.gender, next(h for h in HELPERS if h.id == params.helper))
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible seesaw scenes:")
        for sid, hid in combos:
            print(f"  {sid:12} {hid}")
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
            header = f"### {p.name}: seesaw in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
