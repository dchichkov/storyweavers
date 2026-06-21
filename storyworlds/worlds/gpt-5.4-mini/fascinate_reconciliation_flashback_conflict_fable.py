#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fascinate_reconciliation_flashback_conflict_fable.py
====================================================================================

A standalone storyworld for a small fable-like domain: a bright object fascinates
one animal, that fascination causes a conflict, a remembered flashback explains
the hurt, and a reconciliation ends the tale with a wiser rule.

The domain is intentionally tiny:
- a child-facing woodland setting
- two talking animals
- one shining object that can fascinate
- a simple conflict over ownership or attention
- a flashback that reveals why one character is upset
- a reconciliation that changes the ending image

The story is generated from world state, not from a frozen paragraph template.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox", "owl", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class ObjectSpec:
    id: str
    label: str
    shine: str
    place: str
    value: str
    touch: str
    topic: str
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
class AnimalSpec:
    id: str
    type: str
    label: str
    home: str
    quality: str
    topic: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]

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
    def __init__(self) -> None:
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


def _r_fascinate(world: World) -> list[str]:
    out: list[str] = []
    shiny = world.facts.get("object")
    if not shiny:
        return out
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.memes["fascination"] < THRESHOLD:
            continue
        sig = ("fascinate", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fascinated_by_object"] += 1
        out.append("__fascinated__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.memes["hurt"] < THRESHOLD or ent.memes["resentment"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    Rule("fascinate", "social", _r_fascinate),
    Rule("conflict", "social", _r_conflict),
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


def old_hurt_before(newcomer: str, owner: str) -> bool:
    return newcomer != owner


def flashback_reason(world: World, seeker: Entity, owner: Entity, obj: ObjectSpec) -> bool:
    return seeker.memes["curiosity"] >= 1 and owner.memes["hurt"] >= THRESHOLD


def can_reconcile(world: World) -> bool:
    return True


def _spark(world: World, seeker: Entity, obj: Entity) -> None:
    seeker.memes["fascination"] += 1
    seeker.memes["curiosity"] += 1
    obj.meters["glow"] += 1
    propagate(world, narrate=False)


def _take(world: World, seeker: Entity, obj: Entity) -> None:
    seeker.meters["held"] += 1
    obj.meters["missing"] += 1
    seeker.memes["greed"] += 1


def _return(world: World, seeker: Entity, owner: Entity, obj: Entity) -> None:
    seeker.meters["held"] = 0.0
    obj.meters["missing"] = 0.0
    owner.meters["held"] += 1
    owner.memes["relief"] += 1


def tell(obj_spec: ObjectSpec, seeker_spec: AnimalSpec, owner_spec: AnimalSpec) -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_spec.id, kind="character", type=seeker_spec.type, label=seeker_spec.label, role="seeker", traits=[seeker_spec.quality]))
    owner = world.add(Entity(id=owner_spec.id, kind="character", type=owner_spec.type, label=owner_spec.label, role="owner", traits=[owner_spec.quality]))
    glint = world.add(Entity(id="object", kind="thing", type="thing", label=obj_spec.label))
    world.facts["object"] = obj_spec
    world.facts["seeker"] = seeker
    world.facts["owner"] = owner

    owner.memes["hurt"] = 1.0
    owner.memes["resentment"] = 1.0
    seeker.memes["curiosity"] = 1.0

    world.say(
        f"In the old wood, {seeker.id} and {owner.id} lived by a small path and a soft stream. "
        f"One morning they found {obj_spec.label}, and it {obj_spec.shine} beside {obj_spec.place}."
    )
    world.say(
        f"{seeker.id} could not look away. {obj_spec.label_word if hasattr(obj_spec, 'label_word') else obj_spec.label} seemed to {obj_spec.topic}, "
        f"and {seeker.id} reached for it at once."
    )

    world.para()
    _spark(world, seeker, glint)
    world.say(
        f'"{seeker.id}, that belongs to the hills," said {owner.id}. '
        f'But {seeker.id} was so fascinated that {seeker.pronoun()} still tried to keep it close.'
    )
    _take(world, seeker, glint)

    if flashback_reason(world, seeker, owner, obj_spec):
        world.para()
        owner.memes["memory"] += 1
        world.say(
            f"Then {owner.id} paused and remembered the day a little thorn had scratched {owner.pronoun('object')} by the stream. "
            f"That old hurt was why {owner.id} had sounded sharp."
        )
        world.say(
            f"{seeker.id} saw the hurt in {owner.id}'s face and looked down at {obj_spec.label} in shame."
        )

    world.para()
    if can_reconcile(world):
        seeker.memes["shame"] += 1
        seeker.memes["kindness"] += 1
        owner.memes["forgiveness"] += 1
        _return(world, seeker, owner, glint)
        world.say(
            f"{seeker.id} handed {obj_spec.label} back and said sorry. {owner.id} softened at once. "
            f"The two of them sat together, and {owner.id} shared the shiny thing so they could admire it side by side."
        )
        world.say(
            f"By sunset, they had learned the fable's lesson: a thing may fascinate the eyes, but friendship is better than taking."
        )
    world.facts.update(
        object=obj_spec,
        seeker=seeker,
        owner=owner,
        reconciled=True,
        flashback=bool(owner.memes["memory"] >= THRESHOLD),
    )
    return world


OBJECTS = {
    "mirror_coin": ObjectSpec(
        "mirror_coin",
        "mirror-bright coin",
        "shone like a little sun",
        "a stone root",
        "could fascinate any passing eye",
        "to flash and glitter",
        "shimmer",
        {"bright", "shiny"},
    ),
    "glass_pebble": ObjectSpec(
        "glass_pebble",
        "glass pebble",
        "sparkled in the grass",
        "the riverbank",
        "could fascinate a careful heart",
        "to wink blue and green",
        "gleam",
        {"bright", "shiny"},
    ),
    "golden_leaf": ObjectSpec(
        "golden_leaf",
        "golden leaf",
        "glowed in the sunlight",
        "the old stump",
        "could fascinate a hungry mind",
        "to glow like treasure",
        "glow",
        {"bright", "shiny"},
    ),
}

ANIMALS = {
    "fox": AnimalSpec("Fenn", "fox", "fox", "a hollow tree", "curious", "fable", {"clever"}),
    "rabbit": AnimalSpec("Roo", "rabbit", "rabbit", "a burrow", "gentle", "fable", {"gentle"}),
    "crow": AnimalSpec("Cora", "crow", "crow", "a tall pine", "watchful", "fable", {"watchful"}),
    "mouse": AnimalSpec("Milo", "mouse", "mouse", "a little nest", "small", "fable", {"small"}),
    "owl": AnimalSpec("Oren", "owl", "owl", "an elm branch", "wise", "fable", {"wise"}),
}


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam"]


@dataclass
class StoryParams:
    object: str
    seeker: str
    owner: str
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

CURATED = [
    ("mirror_coin", "fox", "owl"),
    ("glass_pebble", "crow", "rabbit"),
    ("golden_leaf", "mouse", "fox"),
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny fable world about fascination, conflict, flashback, and reconciliation.")
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--seeker", choices=ANIMALS)
    ap.add_argument("--owner", choices=ANIMALS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for oid in OBJECTS:
        for seeker in ANIMALS:
            for owner in ANIMALS:
                if seeker != owner:
                    combos.append((oid, seeker, owner))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.seeker and args.owner and args.seeker == args.owner:
        raise StoryError("Seeker and owner must be different characters.")
    combos = [c for c in valid_combos()
              if (args.object is None or c[0] == args.object)
              and (args.seeker is None or c[1] == args.seeker)
              and (args.owner is None or c[2] == args.owner)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    oid, seeker, owner = rng.choice(sorted(combos))
    return StoryParams(oid, seeker, owner)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obj = f["object"].label
    seeker = f["seeker"].id
    owner = f["owner"].id
    return [
        f'Write a short fable for a child that includes the word "fascinate" and features {obj}.',
        f"Tell a story where {seeker} is fascinated by {obj}, then a conflict happens, then there is reconciliation.",
        f"Write a simple fable in which {owner} remembers an old hurt in a flashback and then makes peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj, seeker, owner = f["object"], f["seeker"], f["owner"]
    qa = [
        QAItem(
            question=f"Why did {seeker.id} want the shiny object?",
            answer=f"{seeker.id} was fascinated by {obj.label}, because it {obj.shine}. The bright sight pulled {seeker.pronoun()} closer and closer."
        ),
        QAItem(
            question=f"Why was there a conflict between {seeker.id} and {owner.id}?",
            answer=f"{owner.id} thought the object belonged to the hills, but {seeker.id} wanted to keep it. That disagreement made both of them tense until they talked again."
        ),
        QAItem(
            question="What changed after the flashback?",
            answer=f"{owner.id} remembered an old hurt by the stream, so the sharp words made more sense. After that, {seeker.id} understood the feeling behind the anger."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation. {seeker.id} gave the object back, said sorry, and the two shared it kindly instead of fighting over it."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj = world.facts["object"]
    owner = world.facts["owner"]
    return [
        QAItem(
            question="What does it mean to fascinate someone?",
            answer="To fascinate someone means to grab their attention so strongly that they keep looking or thinking about it."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened earlier. It helps explain why a character feels upset or careful now."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after a conflict. The characters stop being upset and choose kindness again."
        ),
        QAItem(
            question=f"Why can a bright object like {obj.label} be important in a fable?",
            answer="In a fable, a bright object can tempt a character, start a problem, and then teach a lesson about choices and friendship."
        ),
        QAItem(
            question=f"What kind of character is {owner.id} in this story?",
            answer=f"{owner.id} is the owner of the shiny object and the one who is hurt first. That role gives the story its conflict and its chance for reconciliation."
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(OBJECTS[params.object], ANIMALS[params.seeker], ANIMALS[params.owner])
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
different(A,B) :- animal(A), animal(B), A != B.
fascinated(S) :- seeker(S), sees_shiny(S).
conflict :- fascinated(S), owner(O), seeker(S), S != O.
flashback :- conflict, hurt_before(O), owner(O).
reconcile :- flashback.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("  only in python:", sorted(py - clingo))
        print("  only in clingo:", sorted(clingo - py))
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(CURATED[0] if isinstance(CURATED[0], StoryParams) else StoryParams(*CURATED[0]))
        assert sample.story.strip()
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: the requested combination is too small or invalid for this fable.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for oid, seeker, owner in asp_valid_combos():
            print(f"  {oid:14} {seeker:8} {owner:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated_params = [StoryParams(*t) for t in CURATED]
        samples = [generate(p) for p in curated_params]
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
            header = f"### {p.seeker} & {p.owner}: {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
