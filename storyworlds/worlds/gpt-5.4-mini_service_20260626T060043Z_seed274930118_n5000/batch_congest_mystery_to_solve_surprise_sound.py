#!/usr/bin/env python3
"""
A small slice-of-life story world about a noisy home mystery:
a surprising sound turns out to come from a congested drain, and a child helps
solve it during a busy batch of baking and tidy-up.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    sound: str
    surprise: str
    mess: str
    congestion: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    activity: str
    object: str
    name: str
    gender: str
    helper: str
    trait: str
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

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_mystery_noise(world: World) -> list[str]:
    out: list[str] = []
    sink = world.entities.get("sink")
    if not sink:
        return out
    if sink.meters.get("congested", 0.0) < THRESHOLD:
        return out
    sig = ("noise", "sink")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sink.memes["mystery"] = 1.0
    out.append("The sink made a funny gurgle-gloop sound.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    sink = world.entities.get("sink")
    if not sink:
        return out
    if sink.meters.get("congested", 0.0) < THRESHOLD:
        return out
    if sink.meters.get("cleared", 0.0) < THRESHOLD:
        return out
    sig = ("relief", "sink")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("Then the water hurried away with a cheerful whoosh.")
    return out


CAUSAL_RULES = [
    _r_mystery_noise,
    _r_relief,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_noise(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    sink = sim.entities.get("sink")
    return bool(sink and sink.memes.get("mystery", 0.0) >= THRESHOLD)


def tell(setting: Setting, activity: Activity, obj_cfg: ObjectCfg,
         name: str = "Mina", gender: str = "girl",
         helper: str = "mother", trait: str = "curious") -> World:
    world = World(setting)

    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=helper, label=f"the {helper}"))
    sink = world.add(Entity(id="sink", type="sink", label="sink", phrase="the kitchen sink"))
    bowl = world.add(Entity(
        id="bowl",
        type=obj_cfg.label,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=child.id,
    ))

    child.memes["curiosity"] = 1.0
    child.memes["calm"] = 1.0

    world.say(
        f"{name} was a little {trait} {gender} who liked quiet jobs in {setting.place}."
    )
    world.say(
        f"{name} and {parent.label} were making a big batch of snacks together, "
        f"and the kitchen smelled sweet and warm."
    )
    world.say(
        f"{name} loved stirring the bowl, because the batter made soft plip-plop sounds."
    )
    world.para()

    sink.meters["congested"] = 1.0
    world.say(
        f"Just then, a strange gurgle-gloop came from the sink."
    )
    if predict_noise(world):
        world.say(
            f"{name} tilted {name.lower()} head. \"What is making that sound?\" {name} asked."
        )
        world.say(
            f"{parent.label} frowned a little. \"The drain looks congested,\" {parent.label} said. "
            f"\"Something is stuck in it.\""
        )
    world.para()

    world.say(
        f"{name} peeked into the sink, then found a tiny wad of paper and some crumbs near the drain."
    )
    world.say(
        f"With {parent.pronoun('possessive')} help, {name} picked them out and ran water gently."
    )
    sink.meters["cleared"] = 1.0
    propagate(world, narrate=True)
    world.say(
        f"The noisy mystery was solved, and the kitchen felt calm again."
    )
    world.say(
        f"{name} went back to the batch of snacks, smiling when the bowl gave one last soft plop."
    )

    world.facts.update(
        child=child,
        parent=parent,
        sink=sink,
        bowl=bowl,
        activity=activity,
        obj_cfg=obj_cfg,
        setting=setting,
        mystery=predict_noise(world),
        solved=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"batch"}),
    "laundry": Setting(place="the laundry room", affords={"batch"}),
    "backyard": Setting(place="the backyard", affords={"batch"}),
}

ACTIVITIES = {
    "batch": Activity(
        id="batch",
        verb="make a batch",
        gerund="making a batch",
        sound="plip-plop",
        surprise="a funny gurgle-gloop",
        mess="crumbs",
        congestion="congested",
        keyword="batch",
        tags={"batch", "sound"},
    ),
    "snack": Activity(
        id="snack",
        verb="make snacks",
        gerund="making snacks",
        sound="tap-tap",
        surprise="a surprise drip",
        mess="crumbs",
        congestion="congested",
        keyword="snack",
        tags={"batch", "sound"},
    ),
}

OBJECTS = {
    "bowl": ObjectCfg(label="bowl", phrase="a big mixing bowl", region="hands"),
    "cup": ObjectCfg(label="cup", phrase="a small measuring cup", region="hands"),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Finn", "Noah"]
TRAITS = ["curious", "careful", "cheerful", "quiet", "thoughtful"]


KNOWLEDGE = {
    "batch": [
        ("What is a batch?",
         "A batch is a group of things made or done together at one time, like a batch of cookies."),
    ],
    "sound": [
        ("What are sound effects?",
         "Sound effects are little noises that help you imagine what is happening, like a whoosh, a tap, or a gurgle."),
    ],
    "congested": [
        ("What does congested mean for a drain?",
         "A congested drain is blocked or partly blocked, so water cannot move through it easily."),
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for aname in setting.affords:
            for oname in OBJECTS:
                combos.append((sname, aname, oname))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about a child and a surprising sound in {f["setting"].place}.',
        f'Write a gentle mystery story where {f["child"].id} hears a gurgle from a congested sink while helping with a batch of snacks.',
        f"Tell a child-friendly story that includes a surprise sound effect and ends with the mystery being solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    sink: Entity = f["sink"]
    activity: Activity = f["activity"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What kind of problem did {child.id} notice in {place}?",
            answer=f"{child.id} noticed a mystery sound from the sink, and the drain was congested.",
        ),
        QAItem(
            question=f"What sound effect did the sink make before the problem was solved?",
            answer=f"The sink made a funny gurgle-gloop sound before the water could move again.",
        ),
        QAItem(
            question=f"How did {child.id} help {parent.label} with the mystery?",
            answer=f"{child.id} looked into the sink, found what was blocking it, and helped clear the drain gently.",
        ),
        QAItem(
            question=f"What was {child.id} doing before the mystery sound started?",
            answer=f"{child.id} was helping make a batch of snacks in {place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, qa in KNOWLEDGE.items():
        if tag in tags:
            for q, a in qa:
                out.append(QAItem(question=q, answer=a))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show noisy/1.
#show solved/1.

noisy(sink) :- congested(sink).
solved(sink) :- congested(sink), cleared(sink).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show noisy/1.\n#show solved/1."))
    noisy = set(asp.atoms(model, "noisy"))
    solved = set(asp.atoms(model, "solved"))
    ok = ("sink",) in noisy and ("sink",) in solved
    if ok:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life mystery storyworld about a congested sink and a solved surprise sound.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--name")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        OBJECTS[params.object],
        name=params.name,
        gender=params.gender,
        helper=params.helper,
        trait=params.trait,
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


CURATED = [
    StoryParams(setting="kitchen", activity="batch", object="bowl", name="Mina", gender="girl", helper="mother", trait="curious"),
    StoryParams(setting="kitchen", activity="batch", object="cup", name="Theo", gender="boy", helper="father", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show noisy/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show noisy/1.\n#show solved/1."))
        print("noisy:", sorted(set(asp.atoms(model, "noisy"))))
        print("solved:", sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.activity} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
