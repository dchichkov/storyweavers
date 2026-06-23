#!/usr/bin/env python3
"""
storyworlds/worlds/front_pl_dim_cycle_mystic_friendship_conflict.py
===================================================================

A small ghost-story storyworld about two friends, a dim front porch, and a
mystic cycle that stirs up a conflict before the friends learn to share.

The story world is built around a short, child-facing premise:
two children find a strange bicycle on a front porch at dusk, a soft ghostly
presence points them toward a safer choice, and a tense moment turns into a
friendship-saving compromise.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared results eagerly
- imports shared asp lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    front: bool = False
    cycle: bool = False
    mystic: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    place: str
    dim: bool
    tags: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False
    mystic: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    object_id: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    porch = world.entities.get("porch")
    obj = world.entities.get("object")
    if not porch or not obj:
        return out
    if porch.meters.get("dim", 0.0) < THRESHOLD or not obj.mystic:
        return out
    sig = ("cold", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.memes["mystery"] = obj.memes.get("mystery", 0.0) + 1
    out.append("A faint hush seemed to settle over the bicycle.")
    return out


def _r_conflict(world: World) -> list[str]:
    a = world.entities.get("A")
    b = world.entities.get("B")
    obj = world.entities.get("object")
    if not a or not b or not obj:
        return []
    if a.memes.get("want", 0.0) < THRESHOLD or b.memes.get("worry", 0.0) < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] = a.memes.get("conflict", 0.0) + 1
    b.memes["conflict"] = b.memes.get("conflict", 0.0) + 1
    return ["__conflict__"]


def _r_share(world: World) -> list[str]:
    a = world.entities.get("A")
    b = world.entities.get("B")
    obj = world.entities.get("object")
    if not a or not b or not obj:
        return []
    if a.memes.get("share", 0.0) < THRESHOLD:
        return []
    sig = ("share",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["joy"] = a.memes.get("joy", 0.0) + 1
    b.memes["joy"] = b.memes.get("joy", 0.0) + 1
    return ["__share__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_cold, _r_conflict, _r_share):
            out = fn(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for obj_id in OBJECTS:
            if setting.dim and OBJECTS[obj_id].mystic:
                combos.append((setting_id, obj_id))
    return combos


def _pron(name: str, gender: str, case: str = "subject") -> str:
    e = Entity(id=name, type=gender)
    return e.pronoun(case)


def tell(setting: Setting, obj_spec: ObjectSpec, name_a: str, gender_a: str,
         name_b: str, gender_b: str) -> World:
    world = World(setting)
    world.add(Entity(id="A", kind="character", type=gender_a, label=name_a,
                     traits=["friend"], meters={"at_porch": 1.0}, memes={"want": 0.0}))
    world.add(Entity(id="B", kind="character", type=gender_b, label=name_b,
                     traits=["friend"], meters={"at_porch": 1.0}, memes={"worry": 0.0}))
    world.add(Entity(id="porch", type="place", label="front porch", front=True,
                     meters={"dim": 1.0 if setting.dim else 0.0}))
    world.add(Entity(id="object", type=obj_spec.type, label=obj_spec.label,
                     phrase=obj_spec.phrase, mystic=obj_spec.mystic, plural=obj_spec.plural,
                     meters={}, memes={}))

    a = world.get("A")
    b = world.get("B")
    obj = world.get("object")

    world.say(
        f"At the {setting.place}, {name_a} and {name_b} found {obj.phrase} near the front door."
    )
    world.say(
        f"The air felt quiet and front-pl-dim, and the little light on the porch made the {obj.label} seem mystic."
    )
    a.memes["want"] += 1
    b.memes["worry"] += 1
    world.para()
    world.say(
        f"{name_a} wanted to ride {obj.it()} right away, but {name_b} hesitated and held back a careful hand."
    )
    propagate(world, narrate=True)
    a.memes["share"] += 1
    world.para()
    world.say(
        f"Then {name_b} reminded {name_a} that friends could take turns, and the two of them agreed on a shared cycle of one slow lap each."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"In the end, {name_a} and {name_b} rolled the {obj.label} together down the porch steps, laughing softly while the dusk stayed calm around them."
    )

    world.facts.update(setting=setting, object=obj_spec, a=a, b=b)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obj = f["object"]
    setting = f["setting"]
    a = f["a"]
    b = f["b"]
    return [
        f'Write a short ghost story for a young child about two friends on a dim porch who find a {obj.label} and must choose how to share it.',
        f"Tell a child-friendly story where {a.label} and {b.label} face a small conflict over a {obj.label} at {setting.place}, and the ending feels gentle and mysterious.",
        f'Write a simple story that uses the words "front-pl-dim", "cycle", and "mystic" while two friends solve a porch-time argument kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj = f["object"]
    a = f["a"]
    b = f["b"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=f"The story is about {a.label} and {b.label}, two friends who find a {obj.label} on a dim porch and have to handle a small conflict together.",
        ),
        QAItem(
            question=f"Why did {a.label} and {b.label} argue about the {obj.label}?",
            answer=f"{a.label} wanted to ride the {obj.label} first, while {b.label} worried about the strange feeling around it. That worry turned the moment into a small conflict until they chose to share.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"They decided to take turns and move the {obj.label} together. That choice let their friendship stay strong, and the porch felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj = f["object"]
    out = [
        QAItem(
            question="What does mystic mean in a story?",
            answer="Mystic means strange, magical, or full of a quiet mysterious feeling. It makes an ordinary thing seem like it belongs to a ghost story.",
        ),
        QAItem(
            question="What is a cycle?",
            answer="A cycle is something that goes around again and again, like a repeated path or a bicycle wheel turning in circles.",
        ),
    ]
    if obj.mystic:
        out.append(QAItem(
            question=f"Why might a {obj.label} feel mystic on a porch at dusk?",
            answer=f"A {obj.label} can feel mystic when it sits in dim light and seems unusual or old. The quiet porch makes it look as if it has a secret story of its own.",
        ))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.front:
            bits.append("front=True")
        if e.cycle:
            bits.append("cycle=True")
        if e.mystic:
            bits.append("mystic=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "porch": Setting(place="the front porch", dim=True, tags={"front", "dim"}),
    "steps": Setting(place="the front steps", dim=True, tags={"front", "dim"}),
    "yard": Setting(place="the front yard", dim=False, tags={"front"}),
}

OBJECTS = {
    "cycle": ObjectSpec(id="cycle", label="cycle", phrase="a mystic cycle", type="cycle", mystic=True, tags={"cycle", "mystic"}),
    "bike": ObjectSpec(id="bike", label="bike", phrase="an old bike", type="cycle", mystic=False, tags={"cycle"}),
    "bell": ObjectSpec(id="bell", label="bell", phrase="a small brass bell", type="thing", mystic=True, tags={"mystic"}),
}

CURATED = [
    StoryParams(setting="porch", object_id="cycle", name_a="Mina", gender_a="girl", name_b="Owen", gender_b="boy", seed=11),
    StoryParams(setting="steps", object_id="cycle", name_a="Iris", gender_a="girl", name_b="Leo", gender_b="boy", seed=17),
]


def explain_rejection(setting: Setting, obj: ObjectSpec) -> str:
    return f"(No story: {obj.label} needs a dim, haunted-feeling place, and {setting.place} is not the right match.)"


ASP_RULES = r"""
dim_place(P) :- setting(P), dim(P).
mystic_object(O) :- object(O), mystic(O).
valid(S,O) :- dim_place(S), mystic_object(O).
conflict :- want(A), worry(B).
share :- take_turns.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dim:
            lines.append(asp.fact("dim", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.mystic:
            lines.append(asp.fact("mystic", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    smoke = True
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object_id=None, name_a=None, gender_a=None, name_b=None, gender_b=None, seed=1), random.Random(1)))
        smoke = bool(sample.story)
    except Exception:
        smoke = False
    if ok and smoke:
        print("OK: ASP parity and story smoke test passed.")
        return 0
    print("FAIL: verification did not pass.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: friendship, conflict, and a mystic cycle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
              and (args.object_id is None or c[1] == args.object_id)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, object_id = rng.choice(sorted(combos))
    na = args.name_a or rng.choice(["Mina", "Iris", "Nora", "Owen", "Leo", "Finn"])
    nb = args.name_b or rng.choice([n for n in ["Mina", "Iris", "Nora", "Owen", "Leo", "Finn"] if n != na])
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or rng.choice(["girl", "boy"])
    return StoryParams(setting=setting, object_id=object_id, name_a=na, gender_a=ga, name_b=nb, gender_b=gb)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.object_id not in OBJECTS:
        raise StoryError("Invalid params.")
    if (params.setting, params.object_id) not in valid_combos():
        raise StoryError(explain_rejection(SETTINGS[params.setting], OBJECTS[params.object_id]))
    world = tell(SETTINGS[params.setting], OBJECTS[params.object_id],
                 params.name_a, params.gender_a, params.name_b, params.gender_b)
    return StorySample(params=params, story=world.render(),
                       prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
