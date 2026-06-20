#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/calm_sharing_kindness_tall_tale.py
===================================================================

A standalone storyworld for a calm, kind, sharing tall tale.

Premise:
- Two small folks carry one useful thing.
- A problem appears because one of them has too little or too much, or a task is too big.
- Calm kindness and sharing solve it.
- The ending proves what changed in the world.

The world is built as a tiny simulation with meters (physical) and memes (emotional),
plus a small ASP twin for parity checking.
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

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    sky: str
    tall_tale: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    phrase: str
    useful_for: str
    shareable: bool = True
    fragile: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Need:
    id: str
    label: str
    reason: str
    requires: str
    urgent: int = 1

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_need(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.meters["need_help"] < THRESHOLD:
            continue
        sig = ("need", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["worry"] += 1
        out.append("__need__")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    giver = world.entities.get("giver")
    receiver = world.entities.get("receiver")
    thing = world.entities.get("thing")
    if not giver or not receiver or not thing:
        return out
    if giver.memes["sharing"] < THRESHOLD:
        return out
    if thing.meters["shared"] >= THRESHOLD:
        return out
    sig = ("share", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    thing.meters["shared"] += 1
    thing.meters["usefulness"] += 1
    receiver.meters["need_help"] = 0.0
    giver.memes["calm"] += 1
    receiver.memes["calm"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("need", "social", _r_need), Rule("share", "social", _r_sharing)]


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


def reasonable_combo(setting: Setting, need: Need, thing: Thing) -> bool:
    return thing.shareable and need.requires == thing.kind


def predict_help(world: World, thing_id: str) -> dict:
    sim = world.copy()
    _share(sim, narrate=False)
    receiver = sim.get("receiver")
    thing = sim.get(thing_id)
    return {"calm": receiver.memes["calm"], "shared": thing.meters["shared"]}


def _share(world: World, narrate: bool = True) -> None:
    giver = world.get("giver")
    receiver = world.get("receiver")
    thing = world.get("thing")
    giver.memes["sharing"] += 1
    world.say(
        f"{giver.id} looked at {receiver.id} with a calm face and said, "
        f'"Let us share what we have."'
    )
    propagate(world, narrate=narrate)
    if thing.meters["shared"] >= THRESHOLD and narrate:
        world.say(
            f"{giver.id} split the {thing.label} in two wise ways, so both could use it."
        )


def introduce(world: World, a: Entity, b: Entity, setting: Setting, thing: Thing, need: Need) -> None:
    world.say(
        f"Once, in {setting.place}, under {setting.sky}, {a.id} and {b.id} made a little camp."
    )
    world.say(setting.tall_tale)
    world.say(
        f"They had one {thing.label}, and {b.id} needed it because {need.reason}."
    )


def trouble(world: World, a: Entity, b: Entity, thing: Thing, need: Need) -> None:
    a.meters["need_help"] += 0.0
    b.meters["need_help"] += 1.0
    a.memes["calm"] += 1
    b.memes["worry"] += 1
    world.say(
        f"But the task grew tall as a cottonwood tree. {b.id} blinked and said, "
        f'"I need that {thing.label}, but I cannot use it alone."'
    )
    world.say(f"{a.id} stayed calm. {a.id} could see the trouble plain as day.")


def kindness(world: World, a: Entity, b: Entity, thing: Thing) -> None:
    a.memes["kindness"] += 1
    a.memes["sharing"] += 1
    world.say(
        f"{a.id} was kind enough to help. {a.id} put the {thing.label} between them "
        f"and offered half."
    )
    _share(world)


def ending(world: World, a: Entity, b: Entity, thing: Thing) -> None:
    world.say(
        f"In no time, {a.id} and {b.id} were using the shared {thing.label} together."
    )
    world.say(
        f"Their little camp felt twice as grand, and the calm stayed in the air like evening rain."
    )
    world.say(
        f"By the end, {thing.label} was shared, the work was done, and both hearts were light."
    )


def tell(setting: Setting, thing: Thing, need: Need, a_name: str = "Mara", a_type: str = "girl",
         b_name: str = "Jo", b_type: str = "boy", parent_type: str = "mother") -> World:
    world = World(setting)
    giver = world.add(Entity(id=a_name, kind="character", type=a_type, role="giver"))
    receiver = world.add(Entity(id=b_name, kind="character", type=b_type, role="receiver"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item = world.add(Entity(id="thing", kind="thing", type=thing.kind, label=thing.label))
    world.add(Entity(id="need", kind="thing", type="need", label=need.label))
    world.facts.update(giver=giver, receiver=receiver, parent=parent, thing=item, setting=setting, need=need)

    introduce(world, giver, receiver, setting, thing, need)
    world.para()
    trouble(world, giver, receiver, thing, need)
    kindness(world, giver, receiver, thing)
    world.para()
    ending(world, giver, receiver, thing)

    world.facts["resolved"] = item.meters["shared"] >= THRESHOLD
    return world


SETTINGS = {
    "riverbank": Setting(
        "riverbank",
        "the riverbank",
        "a sky full of patient blue",
        "The river rolled by like an old silver road, and the reeds bowed politely to the wind.",
    ),
    "prairie": Setting(
        "prairie",
        "the prairie",
        "a sky as wide as a quilt",
        "The grass leaned in soft waves, and even the clouds seemed to tip their hats.",
    ),
    "harbor": Setting(
        "harbor",
        "the harbor",
        "a sky washed clean by dawn",
        "The boats bobbed like kittens in a cradle, and the water winked at the shore.",
    ),
}

THINGS = {
    "lantern": Thing("lantern", "lantern", "tool", "a brass lantern", "light", tags={"light"}),
    "rope": Thing("rope", "rope", "tool", "a long rope", "help", tags={"rope"}),
    "bucket": Thing("bucket", "bucket", "tool", "a sturdy bucket", "carry water", tags={"water"}),
}

NEEDS = {
    "light": Need("light", "light", "the work had to be done after sunset", "tool"),
    "carry": Need("carry", "carry water", "the path was long and the well was far", "tool"),
    "pull": Need("pull", "pull the boat free", "the little boat was stuck in mud", "tool"),
}

GIRL_NAMES = ["Mara", "Nell", "Luna", "Ivy", "Ada", "Rose", "Annie"]
BOY_NAMES = ["Jo", "Otis", "Ben", "Theo", "Pip", "Finn", "Cal"]
TRAITS = ["calm", "kind", "gentle", "patient", "brave", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for nid, need in NEEDS.items():
            for tid, thing in THINGS.items():
                if reasonable_combo(setting, need, thing):
                    combos.append((sid, nid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    need: str
    thing: str
    giver: str
    giver_gender: str
    receiver: str
    receiver_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a calm tall tale for a child about sharing and kindness in {f["setting"].place}. Include the word "calm".',
        f"Tell a story where {f['giver'].id} and {f['receiver'].id} face a tall job, but one kind act lets them share a {f['thing'].label}.",
        f"Write a gentle, old-time-feeling story about a shared {f['thing'].label} and a problem that gets solved without any fuss.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    giver, receiver, thing, need = f["giver"], f["receiver"], f["thing"], f["need"]
    return [
        QAItem(
            question="Who were the story about?",
            answer=f"The story was about {giver.id} and {receiver.id}, who were trying to handle a big task together."
        ),
        QAItem(
            question=f"Why did {receiver.id} need the {thing.label}?",
            answer=f"{receiver.id} needed the {thing.label} because {need.reason}. It was the one useful thing they had, so sharing it mattered."
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"{giver.id} stayed calm, showed kindness, and shared the {thing.label}. That let both of them keep working without anyone being left out."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    thing = f["thing"]
    return [
        QAItem(
            question="What does calm mean?",
            answer="Calm means peaceful and steady, like a quiet pond that does not splash."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use something with you. It is a kind way to make sure nobody is left out."
        ),
        QAItem(
            question="Why is kindness important?",
            answer="Kindness helps people trust one another and solve problems together. It can turn a hard moment into a gentle one."
        ),
        QAItem(
            question=f"What is a {thing.label} for?",
            answer=f"A {thing.label} is used for {thing.useful_for}. In this world, it could help more than one person when it was shared."
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("riverbank", "light", "lantern", "Mara", "girl", "Jo", "boy", "mother", "calm"),
    StoryParams("prairie", "carry", "rope", "Ada", "girl", "Cal", "boy", "father", "kind"),
    StoryParams("harbor", "pull", "bucket", "Nell", "girl", "Finn", "boy", "mother", "steady"),
]


def explain_rejection(setting: Setting, need: Need, thing: Thing) -> str:
    return (
        f"(No story: a {thing.label} does not fit the need to {need.label} in {setting.place}. "
        f"Pick a thing whose purpose matches the task so sharing can truly help.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("requires", nid, need.requires))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("kind", tid, thing.kind))
        if thing.shareable:
            lines.append(asp.fact("shareable", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, N, T) :- setting(S), need(N), thing(T), shareable(T), requires(N, K), kind(T, K).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A calm, kind, sharing tall-tale story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--giver")
    ap.add_argument("--giver-gender", choices=["girl", "boy"])
    ap.add_argument("--receiver")
    ap.add_argument("--receiver-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.need is None or c[1] == args.need)
              and (args.thing is None or c[2] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, need, thing = rng.choice(sorted(combos))
    giver_gender = args.giver_gender or rng.choice(["girl", "boy"])
    receiver_gender = args.receiver_gender or ("boy" if giver_gender == "girl" else "girl")
    giver = args.giver or rng.choice(GIRL_NAMES if giver_gender == "girl" else BOY_NAMES)
    receiver = args.receiver or rng.choice([n for n in (GIRL_NAMES if receiver_gender == "girl" else BOY_NAMES) if n != giver])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, need, thing, giver, giver_gender, receiver, receiver_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    need = NEEDS[params.need]
    thing = THINGS[params.thing]
    world = World(setting)
    giver = world.add(Entity(id=params.giver, kind="character", type=params.giver_gender, role="giver"))
    receiver = world.add(Entity(id=params.receiver, kind="character", type=params.receiver_gender, role="receiver"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    item = world.add(Entity(id="thing", kind="thing", type=thing.kind, label=thing.label))
    world.facts.update(giver=giver, receiver=receiver, parent=parent, thing=item, need=need, setting=setting)

    world.say(f"Once, in {setting.place}, under {setting.sky}, {giver.id} and {receiver.id} set out together.")
    world.say(setting.tall_tale)
    world.say(f"They had only one {thing.label}, and {receiver.id} needed it because {need.reason}.")
    world.para()
    world.say(f"But the job rose tall as a barn roof. {receiver.id} looked worried, yet {giver.id} stayed calm.")
    world.say(f'"We can share," {giver.id} said, and kindness sat bright in {giver.id}\'s voice.')
    giver.memes["calm"] += 1
    giver.memes["kindness"] += 1
    giver.memes["sharing"] += 1
    receiver.meters["need_help"] += 1.0
    propagate(world, narrate=False)
    world.para()
    _share(world, narrate=True)
    world.say(f"Before long, both children were using the shared {thing.label}.")
    world.say("The work was done, the calm held steady, and the sky looked even wider.")
    world.facts["resolved"] = item.meters["shared"] >= THRESHOLD
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in world_knowledge_qa(world)]],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, need, thing) combos:")
        for s, n, t in combos:
            print(f"  {s:10} {n:8} {t}")
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
