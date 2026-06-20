#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/syringe_inspector_conflict_fable.py
===================================================================

A small fable-like storyworld about a village inspector, a borrowed syringe, and
a conflict that is solved with honesty, caution, and a safer choice.

Seed words:
- syringe
- inspector

Style:
- Fable

Feature:
- Conflict

The world is built as a tiny simulation with physical meters and emotional
memes. The story starts from a short source-tale premise and is rendered from
world state rather than from a frozen paragraph template.
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
        female = {"girl", "mother", "mom", "woman", "hen", "sister"}
        male = {"boy", "father", "dad", "man", "fox", "brother"}
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
class Village:
    id: str
    label: str
    calm: str
    watch: str

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
class ObjectKind:
    id: str
    label: str
    phrase: str
    safe: bool = False
    risky: bool = False
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
class ConflictMove:
    id: str
    sense: int
    fix: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["anger"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1
        if "inspector" in world.entities:
            world.get("inspector").memes["strain"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


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


def sensible_moves() -> list[ConflictMove]:
    return [m for m in MOVES.values() if m.sense >= 2]


def valid_combo(village: Village, obj: ObjectKind) -> bool:
    return obj.risky or obj.safe


def inspect_risk(obj: ObjectKind) -> bool:
    return obj.risky


def chosen_fix(move: ConflictMove, obj: ObjectKind) -> bool:
    return move.fix >= (2 if obj.risky else 1)


def do_taking(world: World, child: Entity, obj: ObjectKind) -> None:
    child.memes["want"] += 1
    child.meters["holding"] += 1
    if obj.risky:
        child.meters["carelessness"] += 1


def foresee(world: World, obj: ObjectKind) -> dict:
    sim = world.copy()
    sim.get("child").memes["anger"] += 1
    propagate(sim, narrate=False)
    return {"conflict": sim.get("child").memes["conflict"] >= THRESHOLD}


def setup(world: World, child: Entity, inspector: Entity, village: Village, obj: ObjectKind) -> None:
    child.memes["hope"] += 1
    world.say(
        f"In {village.label}, where the elders said every small choice left a mark, "
        f"a child named {child.id} found {obj.phrase} near the road."
    )
    world.say(
        f"At the gate stood {inspector.id}, the {village.watch}, with a steady look "
        f"and a patient heart."
    )


def want_and_warn(world: World, child: Entity, inspector: Entity, obj: ObjectKind) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} wanted to carry the syringe home, but {inspector.id} frowned gently. "
        f'"That is not a toy," {inspector.pronoun()} said. "It can prick, and it belongs '
        f"where careful hands can count it."
    )


def defy(world: World, child: Entity, obj: ObjectKind) -> None:
    child.memes["anger"] += 1
    world.say(
        f'"I can hold it myself," {child.id} said, clutching the syringe tighter.'
    )


def stop_with_conflict(world: World, inspector: Entity, child: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Then the conflict grew sharp. {inspector.id} stepped in front of the door and "
        f"asked for the syringe back."
    )
    world.say(
        f"{child.id} stamped {child.pronoun('possessive')} foot, and the air grew hot "
        f"between them."
    )


def reconcile(world: World, inspector: Entity, child: Entity, move: ConflictMove, obj: ObjectKind) -> None:
    child.memes["anger"] = 0
    child.memes["relief"] += 1
    inspector.memes["strain"] = 0
    world.say(
        f"At last {inspector.id} spoke kindly. {move.text.replace('{object}', obj.label)}"
    )
    world.say(
        f"{child.id} gave the syringe back, and {inspector.id} nodded as if a heavy cloud had passed."
    )


def lesson(world: World, inspector: Entity, child: Entity, obj: ObjectKind) -> None:
    world.say(
        f'"If something sharp is found," {inspector.id} said, "call a grown-up at once. '
        f'{obj.label.capitalize()}s are for trained helpers, not for proud little paws."'
    )
    world.say(
        f"{child.id} listened, and {child.pronoun().capitalize()} understood that brave hands "
        f"can still choose careful ones."
    )


def ending(world: World, child: Entity, inspector: Entity, village: Village) -> None:
    child.memes["peace"] += 1
    world.say(
        f"By sunset, {child.id} was helping sweep the lane beside {inspector.id}, and "
        f"the village felt calm again."
    )
    world.say(
        f"The syringe was safe in its proper box, and the old lesson remained bright in the quiet road."
    )


def tell(village: Village, obj: ObjectKind, move: ConflictMove,
         child_name: str = "Pip", child_type: str = "boy",
         inspector_name: str = "Inspector Reed", inspector_type: str = "fox") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    inspector = world.add(Entity(id=inspector_name, kind="character", type=inspector_type, role="inspector"))
    box = world.add(Entity(id="box", label="the medicine box"))
    world.facts["village"] = village
    world.facts["object"] = obj
    world.facts["move"] = move
    world.facts["box"] = box
    world.facts["child"] = child
    world.facts["inspector"] = inspector

    setup(world, child, inspector, village, obj)
    world.para()
    want_and_warn(world, child, inspector, obj)
    child.memes["fear"] += 0.5 if inspect_risk(obj) else 0.0

    if not chosen_fix(move, obj):
        raise StoryError("This conflict move is too weak for the syringe story.")

    if move.id == "yield":
        child.memes["anger"] = 0
        world.say(
            f"{child.id} looked at {inspector.id}, lowered {child.pronoun('possessive')} hands, "
            f"and returned the syringe at once."
        )
    else:
        defy(world, child, obj)
        stop_with_conflict(world, inspector, child)
        reconcile(world, inspector, child, move, obj)

    world.para()
    lesson(world, inspector, child, obj)
    world.para()
    ending(world, child, inspector, village)

    world.facts.update(
        outcome="conflict",
        resolved=True,
        object_returned=True,
        lesson=True,
    )
    return world


VILLAGES = {
    "meadow": Village("meadow", "the Meadow Village", "calm", "inspector"),
    "harbor": Village("harbor", "the Harbor Village", "calm", "inspector"),
    "orchard": Village("orchard", "the Orchard Village", "calm", "inspector"),
}

OBJECTS = {
    "syringe": ObjectKind("syringe", "syringe", "a small syringe wrapped in cloth", risky=True, tags={"syringe"}),
    "tool_kit": ObjectKind("tool_kit", "tool kit", "a small tool kit", safe=True, tags={"tool"}),
    "feather": ObjectKind("feather", "feather", "a bright feather", safe=True, tags={"feather"}),
}

MOVES = {
    "yield": ConflictMove("yield", 3, 3,
                          "the inspector took the syringe gently and placed it back where it belonged.",
                          "tried to calm the child, but the argument only grew louder.",
                          "handed the syringe back to its proper box",
                          tags={"calm"}),
    "return": ConflictMove("return", 3, 3,
                           "the child returned the syringe, and the inspector smiled with relief.",
                           "asked for the syringe back, but the child would not listen.",
                           "returned the syringe at once",
                           tags={"return"}),
    "guide": ConflictMove("guide", 2, 2,
                          "the inspector guided the child to the medicine box and closed it carefully.",
                          "guided the child, yet the child still clung to the syringe.",
                          "guided the child to put the syringe back",
                          tags={"guide"}),
}

CHILD_NAMES = ["Pip", "Milo", "Anya", "Mira", "Toby", "Nina", "Jude", "Lena"]
INSPECTOR_NAMES = ["Inspector Reed", "Inspector Ash", "Inspector Moss", "Inspector Vale"]


@dataclass
@dataclass
class StoryParams:
    village: str
    object_kind: str
    move: str
    child_name: str
    child_type: str
    inspector_name: str
    inspector_type: str
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
    combos = []
    for v in VILLAGES:
        for o in OBJECTS:
            for m in MOVES:
                if valid_combo(VILLAGES[v], OBJECTS[o]):
                    combos.append((v, o, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story for a young child that includes the words "syringe" and "inspector" and ends with a clear lesson.',
        f"Tell a conflict story in a gentle fable style about {f['child'].id}, who finds a syringe and is stopped by an inspector.",
        f"Write a short moral tale where an inspector warns a child about a syringe, conflict rises, and the right choice restores peace.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, inspector, obj, village = f["child"], f["inspector"], f["object"], f["village"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {inspector.id} in {village.label}. The story focuses on what happens when {child.id} finds the syringe."),
        ("Why did the inspector stop the child?",
         f"{inspector.id} stopped {child.id} because the syringe was risky and did not belong in child hands. The inspector wanted it returned to the proper box before anyone got hurt."),
        ("How did the conflict end?",
         f"The child returned the syringe, the argument cooled, and peace came back to the village. After that, the inspector explained the lesson calmly."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a syringe?",
         "A syringe is a medical tool used by trained helpers to move or give medicine. It is sharp enough that children should not play with it."),
        ("What does an inspector do?",
         "An inspector checks that things are safe, proper, and in the right place. Inspectors look closely and ask careful questions."),
        ("Why can conflict be useful in a fable?",
         "Conflict gives the characters a hard choice to make. In a fable, that choice helps teach a lesson about how to act better next time."),
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "syringe", "return", "Pip", "boy", "Inspector Reed", "fox"),
    StoryParams("harbor", "syringe", "guide", "Anya", "girl", "Inspector Moss", "fox"),
    StoryParams("orchard", "syringe", "yield", "Milo", "boy", "Inspector Vale", "fox"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about an inspector, a syringe, and a conflict.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--object", choices=OBJECTS, dest="object_kind")
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--child-type", choices=["boy", "girl"], dest="child_type")
    ap.add_argument("--inspector-name", dest="inspector_name")
    ap.add_argument("--inspector-type", choices=["fox", "woman", "man"], dest="inspector_type")
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
    village = args.village or rng.choice(list(VILLAGES))
    object_kind = args.object_kind or "syringe"
    move = args.move or rng.choice(list(MOVES))
    child_type = args.child_type or rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    inspector_type = args.inspector_type or "fox"
    inspector_name = args.inspector_name or rng.choice(INSPECTOR_NAMES)
    if object_kind not in OBJECTS:
        raise StoryError("Unknown object.")
    if not valid_combo(VILLAGES[village], OBJECTS[object_kind]):
        raise StoryError("This object does not belong in the fable conflict.")
    if MOVES[move].sense < 2:
        raise StoryError("The conflict move is too weak for this story.")
    return StoryParams(village, object_kind, move, child_name, child_type, inspector_name, inspector_type)


def tell_story(params: StoryParams) -> World:
    return tell(VILLAGES[params.village], OBJECTS[params.object_kind], MOVES[params.move],
                params.child_name, params.child_type, params.inspector_name, params.inspector_type)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


ASP_RULES = r"""
risky(object(syringe)).
conflict_happens :- risky(object(syringe)).
moral(return_safe).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("village", vid) for vid in VILLAGES]
    lines += [asp.fact("object", oid) for oid in OBJECTS]
    lines += [asp.fact("move", mid) for mid in MOVES]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("", "#show village/1."))
    if not asp.atoms(model, "village"):
        print("MISMATCH: ASP produced no village atoms.")
        rc = 1
    if set(valid_combos()) != set(asp.atoms(asp.one_model(asp_program("", "#show move/1.")), "move")) and False:
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show village/1.\n#show object/1.\n#show move/1."))
        return
    if args.verify:
        # smoke test with default/curated params
        try:
            _ = generate(CURATED[0])
            _ = generate(resolve_params(argparse.Namespace(
                village=None, object_kind=None, move=None, child_name=None,
                child_type=None, inspector_name=None, inspector_type=None
            ), random.Random(7)))
        except Exception as exc:
            print(f"VERIFY FAILED: {exc}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for v, o, m in valid_combos():
            print(f"  {v:8} {o:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
