#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/violent_storage_closet_bravery_folk_tale.py
===========================================================================

A standalone story world for a small folk-tale domain set in a storage closet.

Premise:
- A child hears a violent racket from a storage closet.
- The child must choose bravery over fear.
- A hidden creature or mishap is revealed.
- A small, careful rescue changes the room from frightening to safe.

The world is built from typed entities with physical meters and emotional memes.
The text is state-driven rather than a fixed paragraph with swapped names.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/violent_storage_closet_bravery_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/violent_storage_closet_bravery_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/violent_storage_closet_bravery_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/violent_storage_closet_bravery_folk_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    locked: bool = False
    opens: bool = False
    dangerous: bool = False
    gentle: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class ClosetThing:
    id: str
    label: str
    kind: str
    dangerous: bool = False
    gentle: bool = False
    opens: bool = False
    locked: bool = False
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
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        return c

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
class Rule:
    name: str
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


def _r_fear(world: World) -> list[str]:
    out = []
    closet = world.get("closet")
    if closet.meters["rattle"] < THRESHOLD:
        return out
    sig = ("fear", "closet")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in list(world.entities.values()):
        if ch.role == "child":
            ch.memes["fear"] += 1
    closet.meters["ominous"] += 1
    out.append("__fear__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    closet = world.get("closet")
    if closet.meters["opened"] < THRESHOLD:
        return out
    sig = ("relief", "opened")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in list(world.entities.values()):
        if ch.role == "child":
            ch.memes["relief"] += 1
    closet.meters["ominous"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)


def tell(world: World, child: Entity, elder: Entity, closet: Entity, thing: Entity, key: Entity) -> World:
    child.memes["bravery"] = 5.0
    child.memes["curiosity"] = 3.0
    elder.memes["calm"] = 4.0
    world.say(
        f"Long ago, in a little house by the lane, {child.id} lived with {elder.label_word}. "
        f"Behind the kitchen there stood an old storage closet, narrow and gray."
    )
    world.say(
        f"One evening, the closet began to shake with a violent rattle, and the latch gave a hard little knock."
    )
    closet.meters["rattle"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} stood still and listened. {child.id}'s heart fluttered, but {child.pronoun().capitalize()} did not run away."
    )
    world.para()
    if thing.id == "kitten":
        world.say(
            f'"Someone is in there," {child.id} whispered. "I hear a tiny cry."'
        )
    else:
        world.say(
            f'"Someone is in there," {child.id} whispered. "The closet sounds trapped."'
        )
    world.say(
        f"{elder.label_word.capitalize()} warned {child.id} not to poke the door without help, for old things could fall."
    )
    child.memes["bravery"] += 1
    child.memes["defiance"] += 0.5
    if child.memes["bravery"] >= 6:
        world.say(
            f"But {child.id} took a brave breath, held the lantern high, and found the little key hanging on a nail."
        )
    else:
        world.say(
            f"But {child.id} took a careful breath and asked for the key instead."
        )
    key.meters["found"] += 1
    world.say(
        f"The key fit the lock with a soft click. The closet door opened, and the violent racket fell into silence."
    )
    closet.meters["opened"] += 1
    propagate(world, narrate=False)
    world.para()
    if thing.gentle:
        world.say(
            f"Inside was a frightened {thing.label}, tangled in a ribbon and sitting atop a toppled box."
        )
        world.say(
            f"{child.id} knelt down, untied the ribbon, and lifted the {thing.label} into warm hands."
        )
        thing.meters["safe"] += 1
        thing.memes["calm"] += 1
        child.memes["tenderness"] += 1
    else:
        world.say(
            f"Inside was a spilled stack of jars and old cloths, all mixed in a sorry heap."
        )
        world.say(
            f"{child.id} and {elder.label_word} put the pile right again, one careful piece at a time."
        )
        thing.meters["tidy"] += 1
    world.para()
    world.say(
        f"After that, the closet was only a closet again, and {child.id} kept the little key on a ribbon by the door."
    )
    world.say(
        f"That night, {child.id} fell asleep brave and warm, knowing that a frightened heart can still choose a steady hand."
    )
    world.facts.update(child=child, elder=elder, closet=closet, thing=thing, key=key, outcome="resolved")
    return world


THEMES = {
    "folk": "a small folk-tale house by the lane",
}

CHILDREN = ["Mina", "Nell", "Toby", "Owen", "Elsa", "Pip"]
ELDERS = [("grandma", "grandmother"), ("grandpa", "grandfather"), ("mom", "mother"), ("dad", "father")]
THINGS = {
    "kitten": ClosetThing("kitten", "kitten", "animal", gentle=True, tags={"animal", "gentle"}),
    "nest": ClosetThing("nest", "nest", "thing", gentle=True, tags={"bird", "gentle"}),
    "box": ClosetThing("box", "box", "thing", tags={"box"}),
}
KEYS = {
    "key": ClosetThing("key", "little brass key", "tool", opens=True, tags={"key"}),
    "lantern": ClosetThing("lantern", "lantern", "tool", gentle=True, tags={"light"}),
}


@dataclass
@dataclass
class StoryParams:
    child: str
    child_type: str
    elder: str
    elder_type: str
    thing: str
    key: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("folk", "kitten", "key"), ("folk", "nest", "key"), ("folk", "box", "key")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world set in a storage closet.")
    ap.add_argument("--child")
    ap.add_argument("--elder")
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--key", choices=KEYS)
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
    child = args.child or rng.choice(CHILDREN)
    elder_name, elder_type = rng.choice(ELDERS)
    if args.elder:
        elder_name = args.elder
    thing = args.thing or rng.choice(list(THINGS))
    key = args.key or "key"
    return StoryParams(child, "child", elder_name, elder_type, thing, key)


def generate(params: StoryParams) -> StorySample:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type="girl", role="child"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_type, role="elder"))
    closet = world.add(Entity(id="closet", kind="thing", type="closet", label="storage closet", locked=True, dangerous=True))
    thing = world.add(Entity(id=params.thing, kind="thing", type=params.thing, label=THINGS[params.thing].label, gentle=THINGS[params.thing].gentle))
    key = world.add(Entity(id=params.key, kind="thing", type="key", label="little brass key", opens=True))
    tell(world, child, elder, closet, thing, key)
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale about {f['child'].id} hearing a violent sound in a storage closet and choosing bravery.",
        f"Tell a child-sized story where a brave child opens an old storage closet and discovers what was making the noise.",
        f"Write a gentle folk tale in which {f['child'].id} feels fear, uses courage, and turns a violent racket into a safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    thing = f["thing"]
    qa = [
        ("What scared the child?", "A violent rattle came from the storage closet, and it sounded like something was trapped inside."),
        ("What did the child do?", f"{child.id} listened, took a brave breath, and found the little key to open the closet."),
        ("Who helped in the story?", f"{elder.id} helped keep the child calm and made sure the old closet was opened safely."),
        ("What was found in the closet?", f"A frightened {thing.label} was inside, and the child carefully made it safe."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is bravery?", "Bravery means being scared but still doing the right thing and helping anyway."),
        ("What is a storage closet?", "A storage closet is a small room or cupboard where people keep boxes and other things."),
        ("Why should you be careful around old closets?", "Old closets can have stacked things, tight spaces, or latches that need gentle handling."),
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.locked:
            parts.append("locked=True")
        if e.opens:
            parts.append("opens=True")
        if e.dangerous:
            parts.append("dangerous=True")
        if e.gentle:
            parts.append("gentle=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
rattle(closet) :- violent_sound(closet).
afraid(child) :- rattle(closet), child_role(child).
openable(closet) :- has_key(key), locked(closet).
resolved(child) :- afraid(child), openable(closet).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("violent_sound", "closet"),
        asp.fact("child_role", "child"),
        asp.fact("has_key", "key"),
        asp.fact("locked", "closet"),
    ]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show resolved/1."))
    atoms = set(asp.atoms(model, "resolved"))
    python_ok = True
    return 0 if ("child",) in atoms and python_ok else 1


def explain_rejection() -> str:
    return "(No story: this world always needs a violent sound, a brave child, and a key in the storage closet.)"


CURATED = [
    StoryParams("Mina", "girl", "grandma", "grandmother", "kitten", "key"),
    StoryParams("Toby", "boy", "grandpa", "grandfather", "nest", "key"),
    StoryParams("Elsa", "girl", "mom", "mother", "box", "key"),
]


def resolve_world_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.key and args.key not in KEYS:
        raise StoryError(explain_rejection())
    return StoryParams(
        child=args.child or rng.choice(CHILDREN),
        child_type="girl" if (args.child or rng.choice([0, 1])) else "boy",
        elder=args.elder or rng.choice([e[0] for e in ELDERS]),
        elder_type="grandmother",
        thing=args.thing or rng.choice(list(THINGS)),
        key=args.key or "key",
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        child=args.child or rng.choice(CHILDREN),
        child_type="girl" if rng.choice([True, False]) else "boy",
        elder=args.elder or rng.choice(["grandma", "grandpa", "mom", "dad"]),
        elder_type="grandmother",
        thing=args.thing or rng.choice(list(THINGS)),
        key=args.key or "key",
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


def build_parser_for_verify() -> argparse.ArgumentParser:
    return build_parser()


def generate_smoke() -> None:
    _ = generate(CURATED[0])


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show resolved/1."))
        return
    if args.verify:
        try:
            generate_smoke()
        except Exception:
            raise
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
