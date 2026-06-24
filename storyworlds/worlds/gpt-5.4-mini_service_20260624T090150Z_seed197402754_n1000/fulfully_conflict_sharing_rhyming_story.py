#!/usr/bin/env python3
"""
A small storyworld for a rhyming tale about conflict and sharing.

This world builds a tiny simulated domain where two children want the same
special toy or treat. A parent or helper notices the conflict, suggests a fair
share, and the story resolves with a happy rhyme and a lasting image of
togetherness.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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


@dataclass
class Setting:
    place: str = "the sunny yard"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    type: str
    theme: str
    shared_with: str
    rhyme: str


@dataclass
class StoryParams:
    place: str
    object: str
    hero1_name: str
    hero1_gender: str
    hero2_name: str
    hero2_gender: str
    helper: str
    seed: Optional[int] = None


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def rhyme_pair(a: str, b: str) -> str:
    return f"{a}\n{b}"


SETTINGS = {
    "yard": Setting(place="the sunny yard", affords={"kite", "ball", "blanket"}),
    "porch": Setting(place="the porch", affords={"cookies", "book", "ball"}),
    "garden": Setting(place="the flower garden", affords={"berries", "kite", "blanket"}),
    "playroom": Setting(place="the playroom", affords={"blocks", "book", "ball"}),
}

OBJECTS = {
    "kite": ObjectConfig(
        id="kite",
        label="red kite",
        phrase="a bright red kite",
        type="kite",
        theme="high in the sky",
        shared_with="two string handles",
        rhyme="light",
    ),
    "ball": ObjectConfig(
        id="ball",
        label="blue ball",
        phrase="a shiny blue ball",
        type="ball",
        theme="bounce and roll",
        shared_with="turns and throws",
        rhyme="play",
    ),
    "blanket": ObjectConfig(
        id="blanket",
        label="checkered blanket",
        phrase="a warm checkered blanket",
        type="blanket",
        theme="picnic time",
        shared_with="room for two",
        rhyme="snug",
    ),
    "cookies": ObjectConfig(
        id="cookies",
        label="cookie tin",
        phrase="a small tin of sweet cookies",
        type="cookies",
        theme="sweet delight",
        shared_with="one cookie each",
        rhyme="treat",
    ),
    "book": ObjectConfig(
        id="book",
        label="storybook",
        phrase="a picture book with a smiling moon",
        type="book",
        theme="page by page",
        shared_with="one page at a time",
        rhyme="moon",
    ),
    "berries": ObjectConfig(
        id="berries",
        label="berry bowl",
        phrase="a bowl of ripe berries",
        type="berries",
        theme="juicy red",
        shared_with="small handfuls",
        rhyme="glow",
    ),
    "blocks": ObjectConfig(
        id="blocks",
        label="tower blocks",
        phrase="a pile of wooden blocks",
        type="blocks",
        theme="stack and build",
        shared_with="one block each",
        rhyme="tower",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ruby", "Ella", "Ivy"]
BOY_NAMES = ["Theo", "Leo", "Ben", "Max", "Finn", "Noah", "Owen", "Sam"]
HELPERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["cheerful", "curious", "bouncy", "gentle", "brave", "spry"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, obj) for place, s in SETTINGS.items() for obj in s.affords if obj in OBJECTS]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("hero1")
    b = world.entities.get("hero2")
    obj = world.entities.get("object")
    if not a or not b or not obj:
        return out
    if a.memes.get("claim", 0) < THRESHOLD or b.memes.get("claim", 0) < THRESHOLD:
        return out
    if a.memes.get("shared", 0) >= THRESHOLD or b.memes.get("shared", 0) >= THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["conflict"] = a.memes.get("conflict", 0) + 1
    b.memes["conflict"] = b.memes.get("conflict", 0) + 1
    out.append("__conflict__")
    return out


def _r_soothe(world: World) -> list[str]:
    helper = world.entities.get("helper")
    a = world.entities.get("hero1")
    b = world.entities.get("hero2")
    if not helper or not a or not b:
        return []
    if helper.memes.get("kind_offer", 0) < THRESHOLD:
        return []
    sig = ("soothe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["calm"] = a.memes.get("calm", 0) + 1
    b.memes["calm"] = b.memes.get("calm", 0) + 1
    return [f"{helper.id} gave a gentle plan that made the worry unwind."]


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("soothe", _r_soothe)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_claim(world: World, actor: Entity, obj: Entity) -> None:
    actor.memes["claim"] = actor.memes.get("claim", 0) + 1
    obj.meters["desired"] = obj.meters.get("desired", 0) + 1


def _do_share(world: World, a: Entity, b: Entity, obj: Entity) -> None:
    a.memes["shared"] = a.memes.get("shared", 0) + 1
    b.memes["shared"] = b.memes.get("shared", 0) + 1
    a.memes["conflict"] = 0
    b.memes["conflict"] = 0
    obj.meters["shared"] = obj.meters.get("shared", 0) + 1


def tell(setting: Setting, obj_cfg: ObjectConfig, p: StoryParams) -> World:
    world = World(setting)
    hero1 = world.add(Entity(id="hero1", kind="character", type=p.hero1_gender, label=p.hero1_name))
    hero2 = world.add(Entity(id="hero2", kind="character", type=p.hero2_gender, label=p.hero2_name))
    helper = world.add(Entity(id="helper", kind="character", type=p.helper, label=f"the {p.helper}"))
    obj = world.add(Entity(id="object", type=obj_cfg.type, label=obj_cfg.label, phrase=obj_cfg.phrase))

    world.facts.update(hero1=hero1, hero2=hero2, helper=helper, object=obj, obj_cfg=obj_cfg, setting=setting)

    world.say(
        f"In {setting.place}, {hero1.label} and {hero2.label} met with a grin, "
        f"for the day was bright and the fun could begin."
    )
    world.say(
        f"They saw {obj.phrase}, so lovely and neat, "
        f"and both cried, \"That treasure is mine to keep!\""
    )

    _do_claim(world, hero1, obj)
    _do_claim(world, hero2, obj)
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{hero1.label} reached first with a tug and a pout, "
        f"while {hero2.label} held on and would not let go out."
    )
    world.say(
        f"\"I want it now!\" said one, and \"No, my turn!\" said the other; "
        f"the air felt quite small for a sister or brother."
    )
    propagate(world)

    world.para()
    world.say(
        f"Then {helper.label} came strolling with a smile soft and wide, "
        f"and said, \"We can share it and stay side by side.\""
    )
    helper.memes["kind_offer"] = helper.memes.get("kind_offer", 0) + 1
    world.say(
        f"\"Use it fulfully,\" said {helper.label}, \"with turns and with care; "
        f"one gets the first go, then the other can share.\""
    )
    _do_share(world, hero1, hero2, obj)
    propagate(world)

    world.say(
        f"So {hero1.label} used the {obj.label}, then passed it with cheer, "
        f"and {hero2.label} laughed, \"Your turn!\" loud and clear."
    )
    world.say(
        f"In {setting.place}, they played and they shared in a row, "
        f"and the little {obj.label} shone like a bright rainbow glow."
    )

    world.facts["shared"] = True
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child about {f["hero1"].label} and {f["hero2"].label} sharing {f["obj_cfg"].phrase}.',
        f'Create a gentle rhyme where two children have a conflict over a {f["obj_cfg"].label} and a helper teaches them to share.',
        f'Write a tiny story that uses the word "fulfully" and ends with both children happy after taking turns.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1, h2, helper, obj, cfg = f["hero1"], f["hero2"], f["helper"], f["object"], f["obj_cfg"]
    return [
        QAItem(
            question=f"Who were the two children in the story?",
            answer=f"The two children were {h1.label} and {h2.label}. They both wanted {obj.phrase} at first.",
        ),
        QAItem(
            question=f"What caused the conflict in {world.setting.place}?",
            answer=f"The conflict began because both children wanted {cfg.label} and did not want to wait for a turn.",
        ),
        QAItem(
            question=f"Who helped them share?",
            answer=f"{helper.label} helped them by suggesting that they use {cfg.label} fulfully, with turns and care.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {h1.label} and {h2.label} shared happily, and the conflict turned into calm play.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    cfg: ObjectConfig = f["obj_cfg"]
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person use something too, often by taking turns or dividing it fairly.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a disagreement or a fight over what to do or who gets something first.",
        ),
        QAItem(
            question="What does fulfully mean in this story?",
            answer="Here, fulfully means doing something in a full and kind way, with care and fair turns.",
        ),
        QAItem(
            question=f"What is a {cfg.label}?",
            answer=f"A {cfg.label} is {cfg.phrase}. In stories like this, it can be the thing children want to share.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="yard", object="kite", hero1_name="Mia", hero1_gender="girl", hero2_name="Theo", hero2_gender="boy", helper="mother"),
    StoryParams(place="porch", object="cookies", hero1_name="Nora", hero1_gender="girl", hero2_name="Leo", hero2_gender="boy", helper="grandma"),
    StoryParams(place="garden", object="berries", hero1_name="Ava", hero1_gender="girl", hero2_name="Max", hero2_gender="boy", helper="father"),
    StoryParams(place="playroom", object="blocks", hero1_name="Ella", hero1_gender="girl", hero2_name="Finn", hero2_gender="boy", helper="mother"),
]


def explain_rejection(place: str, obj: str) -> str:
    return f"(No story: {place} does not fit the object {obj} in this tiny world.)"


@dataclass
class StoryParamsResolved:
    place: str
    object: str
    hero1_name: str
    hero1_gender: str
    hero2_name: str
    hero2_gender: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about conflict and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--hero1-name")
    ap.add_argument("--hero1-gender", choices=["girl", "boy"])
    ap.add_argument("--hero2-name")
    ap.add_argument("--hero2-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj = rng.choice(sorted(combos))
    hero1_gender = args.hero1_gender or rng.choice(["girl", "boy"])
    hero2_gender = args.hero2_gender or ("boy" if hero1_gender == "girl" else "girl")
    hero1_name = args.hero1_name or rng.choice(GIRL_NAMES if hero1_gender == "girl" else BOY_NAMES)
    hero2_name = args.hero2_name or rng.choice([n for n in (GIRL_NAMES if hero2_gender == "girl" else BOY_NAMES) if n != hero1_name] or (GIRL_NAMES if hero2_gender == "girl" else BOY_NAMES))
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, object=obj, hero1_name=hero1_name, hero1_gender=hero1_gender, hero2_name=hero2_name, hero2_gender=hero2_gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], params)
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
valid(Place,Object) :- setting(Place), affords(Place,Object).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for obj in sorted(s.affords):
            lines.append(asp.fact("affords", place, obj))
    for obj_id in OBJECTS:
        lines.append(asp.fact("object", obj_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero1_name} and {p.hero2_name}: sharing {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
