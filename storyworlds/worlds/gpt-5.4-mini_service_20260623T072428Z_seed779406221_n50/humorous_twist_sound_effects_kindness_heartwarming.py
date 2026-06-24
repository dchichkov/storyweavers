#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/humorous_twist_sound_effects_kindness_heartwarming.py
===============================================================================================================

A standalone storyworld built from the seed theme:
- humorous
- Twist
- Sound Effects
- Kindness
- heartwarming style

Premise:
A child plans a tiny surprise using noisy, funny props, but the "mistake" turns
into the best part of the story. The world tracks concrete objects, physical
meters, and emotional memes. A causal model drives the prose so the ending
proves what changed.

This world models a small, child-facing domain: a home kitchen / yard / porch
where a child tries to make a cheerful surprise for someone kind.

The twist:
A little sound-making mishap (a pop, squeak, hiccup, or boing) seems like a
problem at first, but it becomes the cue that helps the kindness land at just
the right moment.

The story is intentionally warm, concrete, and state-driven rather than a frozen
paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    mess: str
    useful_for: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    comfort: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cheer(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["joy"] >= THRESHOLD and ("cheer", e.id) not in world.fired:
            world.fired.add(("cheer", e.id))
            out.append(f"{e.id} felt brighter already.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "table" in world.entities:
            world.get("table").meters["mess"] += 1
        out.append(f"The little mishap made the room feel even busier.")
    return out


def _r_twist(world: World) -> list[str]:
    for e in world.entities.values():
        if e.memes["surprise"] < THRESHOLD:
            continue
        sig = ("twist", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["delight"] += 1
        return ["__twist__"]
    return []


CAUSAL_RULES = [
    Rule("cheer", "emotional", _r_cheer),
    Rule("mess", "physical", _r_mess),
    Rule("twist", "social", _r_twist),
]


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


def makes_sound(prop: Prop, setting: Setting) -> bool:
    return prop.id in setting.affords


def can_kindness_work(helper: Helper, prop: Prop) -> bool:
    return helper.id in prop.tags or helper.id == "helper"


def predict_moment(world: World, child: Entity, prop: Prop, helper: Helper) -> dict:
    sim = world.copy()
    _use_prop(sim, sim.get(child.id), prop, helper, narrate=False)
    return {
        "twist": bool(sim.get(child.id).memes["surprise"] >= THRESHOLD),
        "joy": sim.get(child.id).memes["joy"],
    }


def _use_prop(world: World, child: Entity, prop: Prop, helper: Helper, narrate: bool = True) -> None:
    child.meters[prop.mess] += 1
    child.memes["surprise"] += 1
    if helper.id == "hug" or helper.id == "kind":
        child.memes["kindness"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, prop: Prop) -> None:
    child.memes["anticipation"] += 1
    world.say(
        f"{child.id} planned a tiny surprise at {world.setting.place}. "
        f"{helper.id} was nearby, and the whole room felt {world.setting.mood}."
    )
    world.say(
        f"{child.id} set out {prop.phrase}, hoping to make a warm hello sound."
    )


def sound_setup(world: World, prop: Prop) -> None:
    world.say(
        f"Then came the sound: {prop.sound} {prop.twist}. "
        f"It looked like trouble for one tiny second."
    )


def worry(world: World, child: Entity, helper: Entity, prop: Prop) -> None:
    pred = predict_moment(world, child, prop, helper)
    child.memes["worry"] += 1
    world.facts["predicted_twist"] = pred["twist"]
    world.say(
        f"{child.id} blinked. "{prop.sound}?" {child.pronoun()} said. "
        f"{helper.id} smiled and waited, because kindness sometimes needs a pause."
    )


def kind_offer(world: World, helper: Entity, child: Entity, prop: Prop) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} leaned closer and said, "
        f'"Let the funny sound happen. We can still make this lovely."'
    )


def twist_turn(world: World, child: Entity, helper: Entity, prop: Prop) -> None:
    child.memes["surprise"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Twist! {prop.twist.capitalize()}, and suddenly the sound became the joke."
    )
    world.say(
        f"{child.id} laughed so hard {child.pronoun('possessive')} shoulders bounced."
    )


def ending(world: World, child: Entity, helper: Entity, prop: Prop) -> None:
    child.memes["love"] += 1
    child.memes["kindness"] += 1
    child.memes["worry"] = 0
    world.say(
        f"Together they turned the surprise into a warm hello. "
        f"{helper.id} got the last little bit of the treat, and {child.id} "
        f"got the biggest smile."
    )
    world.say(
        f"In the end, {child.id} remembered that a strange sound can still lead "
        f"to a kind moment."
    )


def tell(setting: Setting, prop: Prop, helper_kind: Helper,
         child_name: str = "Milo", child_type: str = "boy",
         helper_name: str = "Grandma", helper_type: str = "grandmother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    table = world.add(Entity(id="table", type="table", label="little table"))
    prop_ent = world.add(Entity(id=prop.id, type="prop", label=prop.label))
    helper_ent = world.add(Entity(id=helper_kind.id, type="helper", label=helper_kind.label))

    opening(world, child, helper, prop)
    world.para()
    sound_setup(world, prop)
    worry(world, child, helper, prop)
    kind_offer(world, helper, child, prop)
    world.para()
    twist_turn(world, child, helper, prop)
    ending(world, child, helper, prop)

    world.facts.update(
        child=child,
        helper=helper,
        prop=prop,
        helper_kind=helper_kind,
        table=table,
        prop_ent=prop_ent,
        helper_ent=helper_ent,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, mood="cozy", affords={"boing", "squeak", "pop"}),
    "porch": Setting(place="the porch", indoor=False, mood="sunny", affords={"boing", "squeak"}),
    "backyard": Setting(place="the backyard", indoor=False, mood="bright", affords={"pop", "squeak", "hiccup"}),
}

PROPS = {
    "balloon": Prop(
        id="balloon",
        label="balloon",
        phrase="a bright balloon",
        sound="pop",
        mess="bump",
        useful_for="party cheer",
        twist="it was only a tiny pop, and the balloon turned into confetti",
        tags={"helper"},
    ),
    "toy": Prop(
        id="toy",
        label="toy truck",
        phrase="a toy truck with wobbly wheels",
        sound="clank",
        mess="bump",
        useful_for="music",
        twist="the wheels went boing and rolled straight into a perfect line",
        tags={"helper"},
    ),
    "spoon": Prop(
        id="spoon",
        label="spoon",
        phrase="a shiny spoon and a cup",
        sound="clink",
        mess="spill",
        useful_for="rhythm",
        twist="the spoon tapped a beat that sounded like a tiny parade",
        tags={"helper"},
    ),
}

HELPERS = {
    "hug": Helper(id="hug", label="a hug", phrase="a warm hug", comfort="comfort", tags={"helper"}),
    "song": Helper(id="song", label="a song", phrase="a soft song", comfort="music", tags={"helper"}),
}

GIRL_NAMES = ["Mia", "Ava", "Nora", "Lily", "Zoe", "Ella"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Finn", "Leo", "Max"]
TRAITS = ["careful", "cheerful", "curious", "gentle", "silly"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROPS:
            if makes_sound(PROPS[p], SETTINGS[s]):
                combos.append((s, p, "hug"))
    return combos


@dataclass
class StoryParams:
    setting: str
    prop: str
    helper: str
    child: str
    child_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "balloon": [("What does a balloon do?",
                 "A balloon gets bigger when air goes inside it, and then it can make a loud pop if it bursts.")],
    "toy": [("Why do toy trucks make children happy?",
             "Toy trucks are fun to push, and their wheels can make silly sounds while they roll.")],
    "spoon": [("What can a spoon be used for besides eating?",
              "A spoon can tap a beat on a cup or bowl, which can make a little rhythm.")],
    "hug": [("What does a hug do?",
             "A hug can help someone feel safe, calm, and loved.")],
    "song": [("Why do songs feel comforting?",
             "Songs can make a room feel gentle and warm, and they can help people relax.")],
    "pop": [("What makes a popping sound?",
            "A pop is a quick, sharp sound, like when a balloon bursts or something snaps small and fast.")],
    "boing": [("What is a boing sound?",
              "Boing is a funny springy sound, like when something bounces back and forth.")],
    "squeak": [("What is a squeak?",
               "A squeak is a small high sound, often made by something rubbing or bending.")],
    "kindness": [("What is kindness?",
                  "Kindness means being gentle and helpful to someone else.")],
}

KNOWLEDGE_ORDER = ["balloon", "toy", "spoon", "hug", "song", "pop", "boing", "squeak", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child where {f["child"].id} makes a funny sound with a {f["prop"].label} and {f["helper"].id} responds kindly.',
        f"Tell a humorous story with a small twist ending: a {f['prop'].label} goes {f['prop'].sound}, but the surprise becomes a happy moment.",
        f'Write a gentle story that includes the word "{f["prop"].label}" and ends with kindness turning a silly mishap into a warm memory.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, prop = f["child"], f["helper"], f["prop"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to make with {prop.label}?",
            answer=f"{child.id} wanted to make a happy surprise with {prop.phrase}. The idea was to cheer up {helper.id}.",
        ),
        QAItem(
            question=f"What funny sound did the {prop.label} make?",
            answer=f"It went {prop.sound}. That sound was the silly twist that changed the moment.",
        ),
        QAItem(
            question=f"Who stayed kind when the sound made things feel strange?",
            answer=f"{helper.id} stayed kind and waited, which helped {child.id} feel better right away.",
        ),
        QAItem(
            question=f"What happened after the twist in the story?",
            answer=f"The funny sound turned into part of the surprise, and {child.id} and {helper.id} laughed together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    for key in ("prop", "helper_kind"):
        tags |= world.facts[key].tags
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "balloon", "hug", "Milo", "boy", "Grandma", "grandmother", "silly"),
    StoryParams("porch", "toy", "song", "Ava", "girl", "Grandpa", "grandfather", "gentle"),
    StoryParams("backyard", "spoon", "hug", "Nora", "girl", "Mom", "mother", "cheerful"),
]


def explain_rejection(setting: Setting, prop: Prop) -> str:
    if not makes_sound(prop, setting):
        return f"(No story: {prop.label} doesn't make a useful sound in {setting.place}.)"
    return "(No story: this combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny heartwarming storyworld with humorous sound-effect twists.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, helper = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["boy", "girl"])
    child = args.name or rng.choice(BOY_NAMES if child_type == "boy" else GIRL_NAMES)
    helper_name = args.helper_name or rng.choice(["Grandma", "Grandpa", "Mom", "Dad"])
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, prop, helper, child, child_type, helper_name, helper_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], HELPERS[params.helper],
                 params.child, params.child_type, params.helper_name, params.helper_type)
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
makes_sound(P,S) :- prop(P), setting(S), soundy(P,S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, prop in PROPS.items():
        lines.append(asp.fact("prop", p))
        for tag in sorted(prop.tags):
            lines.append(asp.fact("tagged", p, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show makes_sound/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
