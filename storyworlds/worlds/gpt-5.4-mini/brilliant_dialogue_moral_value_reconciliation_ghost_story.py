#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/brilliant_dialogue_moral_value_reconciliation_ghost_story.py
=============================================================================================

A small standalone storyworld for a gentle ghost story with dialogue, a moral
value, and reconciliation.

Premise
-------
A child explores a quiet place at night, meets a lonely ghost, and learns that
the ghost is not there to frighten anyone. The child chooses honesty and kindness
instead of fear, and the ending brings a bright, reconciled calm.

The world keeps the story state-driven: fear, trust, loneliness, and restoration
change what gets narrated. It also includes a reasonableness gate and an inline
ASP twin for parity checks.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    sound: str
    mood: str
    dark_spot: str

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
class Object:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str
    moral_value: str
    bright: bool = False
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
class Encounter:
    id: str
    sense: int
    repair: int
    text: str
    fail: str
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
        clone = World(self.setting)
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["caution"] += 1
        out.append("__fear__")
    return out


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if ghost and ghost.memes["lonely"] >= THRESHOLD and ("lonely", ghost.id) not in world.fired:
        world.fired.add(("lonely", ghost.id))
        ghost.memes["sigh"] += 1
        out.append("__lonely__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("lonely", "social", _r_lonely)]


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


def reasonableness_ok(setting: Setting, obj: Object, encounter: Encounter) -> bool:
    return obj.bright and encounter.sense >= 2 and obj.moral_value in {"truth", "kindness", "reconciliation"}


def sensible_encounters() -> list[Encounter]:
    return [e for e in ENCOUNTERS.values() if e.sense >= 2]


def encounter_difficulty(obj: Object) -> int:
    return 1 if obj.fragile else 0


def can_reconcile(encounter: Encounter, obj: Object) -> bool:
    return encounter.repair >= encounter_difficulty(obj)


def predict(world: World, obj_id: str) -> dict:
    sim = world.copy()
    _touch_object(sim, sim.get("child"), sim.get("ghost"), sim.entities[obj_id], narrate=False)
    return {"fear": sim.get("child").memes["fear"], "trust": sim.get("child").memes["trust"]}


def _touch_object(world: World, child: Entity, ghost: Entity, obj: Entity, narrate: bool = True) -> None:
    child.memes["curiosity"] += 1
    obj.meters["moved"] += 1
    if obj.id == "mirror":
        ghost.memes["hope"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"On a quiet night, {child.id} crept into {setting.place}. "
        f"The air was still, and {setting.sound} drifted through the dark."
    )
    world.say(
        f"At the end of {setting.dark_spot}, something gave off a brilliant glow."
    )


def meet_ghost(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["fear"] += 1
    ghost.memes["lonely"] += 1
    world.say(
        f'"Who are you?" {child.id} whispered.'
    )
    world.say(
        f'"I am {ghost.id}," the ghost said softly. "{ghost.attrs.get("role_line", "I only wanted someone to listen.")}"'
    )


def explain_moral(world: World, ghost: Entity, child: Entity, obj: Entity) -> None:
    world.say(
        f'"I did not mean to be frightful," {ghost.id} said. '
        f'"I only wanted my {obj.label} back, and I wanted someone to tell the truth about it."'
    )
    world.say(
        f'{child.id} swallowed and looked at the bright thing again. '
        f'"I can be honest," {child.id} said. "And I can help."'
    )


def reconcile(world: World, child: Entity, ghost: Entity, obj: Entity, encounter: Encounter) -> None:
    child.memes["trust"] += 1
    child.memes["fear"] = 0
    ghost.memes["lonely"] = 0
    ghost.memes["peace"] += 1
    body = encounter.text.replace("{object}", obj.label)
    world.say(f"Then {child.id} reached out and {body}.")
    world.say(
        f"The ghost smiled, and the room felt warmer. "
        f'"Thank you," {ghost.id} said. "That was kind, and it was right."'
    )


def end_image(world: World, child: Entity, ghost: Entity, obj: Entity) -> None:
    world.say(
        f"In the end, {child.id} left the dark place with {obj.phrase} held close, "
        f"and {ghost.id} was no longer lonely at all."
    )
    world.say(
        f"The brilliant light stayed in the window, and the night seemed gentle instead of strange."
    )


def tell(setting: Setting, obj: Object, encounter: Encounter,
         child_name: str = "Mina", child_gender: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost",
                             attrs={"role_line": "I lost my old mirror, and I miss my friend."}))
    item = world.add(Entity(id=obj.id, type=obj.kind, label=obj.label, attrs={"moral": obj.moral_value}))
    child.memes["trust"] = 2.0
    ghost.memes["lonely"] = 1.0
    introduce(world, child, setting)
    world.para()
    meet_ghost(world, child, ghost)
    explain_moral(world, ghost, child, item)
    world.para()
    _touch_object(world, child, ghost, item)
    if can_reconcile(encounter, obj):
        reconcile(world, child, ghost, item, encounter)
    end_image(world, child, ghost, item)
    world.facts.update(child=child, ghost=ghost, setting=setting, obj_cfg=obj, obj=item,
                       encounter=encounter, resolved=can_reconcile(encounter, obj))
    return world


SETTINGS = {
    "attic": Setting("attic", "the attic", "a few boards whispered overhead", "dusty and old", "the far corner"),
    "hall": Setting("hall", "the old hall", "the clock ticked slowly", "dim and echoing", "the tall window"),
    "library": Setting("library", "the library", "pages sighed in the shelves", "quiet and pale", "the reading nook"),
}

OBJECTS = {
    "mirror": Object("mirror", "mirror", "an old silver mirror", "mirror", "its silver edge flashed like moonlight",
                     "truth", bright=True, fragile=True, tags={"bright", "truth"}),
    "bell": Object("bell", "bell", "a tiny brass bell", "bell", "its ring could call a friend",
                   "kindness", bright=True, fragile=False, tags={"bright", "kindness"}),
    "lantern": Object("lantern", "lantern", "a little lantern", "lantern", "its light was bright as a star",
                      "reconciliation", bright=True, fragile=False, tags={"bright", "reconciliation"}),
}

ENCOUNTERS = {
    "gentle": Encounter("gentle", 3, 2,
                        'picked up the {object} and placed it back on the shelf',
                        'reached for the {object}, but it slipped from nervous fingers',
                        tags={"reconcile"}),
    "honest": Encounter("honest", 2, 1,
                       'told the truth about the {object} and handed it back carefully',
                       'tried to hide the truth, but the story would not stay hidden',
                       tags={"truth"}),
    "kind": Encounter("kind", 4, 1,
                      'held the {object} out with both hands and smiled',
                      'held back too long and the lonely feeling grew bigger',
                      tags={"kindness"}),
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ivy", "Clara"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Eli", "Tom"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    obj: str
    encounter: str
    child_name: str
    child_gender: str
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
    for s in SETTINGS:
        for o, obj in OBJECTS.items():
            for e, enc in ENCOUNTERS.items():
                if reasonableness_ok(SETTINGS[s], obj, enc):
                    combos.append((s, o, e))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a young child that includes the word "brilliant" and a quiet conversation with a ghost.',
        f"Tell a story where {f['child'].id} meets {f['ghost'].id} in {f['setting'].place} and learns a moral lesson about {f['obj_cfg'].moral_value}.",
        f"Write a reunion story where a child and a ghost speak kindly, tell the truth, and end with reconciliation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, ghost, obj, enc = f["child"], f["ghost"], f["obj"], f["encounter"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and a lonely ghost named {ghost.id}. They meet in {f['setting'].place} and talk instead of running away."),
        ("What did the child learn?",
         f"{child.id} learned that telling the truth and being kind can help a sad problem heal. That is why the ending feels peaceful instead of scary."),
        ("How did the child and the ghost make things right?",
         f"{child.id} {enc.text.replace('{object}', obj.label)}. After that, they spoke kindly, and the ghost was no longer lonely."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a ghost story often feel like?",
         "A ghost story often feels quiet and a little mysterious, but it can still end gently if the characters speak kindly."),
        ("Why is honesty important?",
         "Honesty helps people trust each other. When someone tells the truth, it is easier to fix a problem and feel close again."),
        ("What is reconciliation?",
         "Reconciliation means making peace after a problem. People stop hurting feelings and begin to understand each other again."),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost story world with dialogue and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--encounter", choices=ENCOUNTERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.object and args.encounter:
        if not reasonableness_ok(SETTINGS[args.setting or "attic"], OBJECTS[args.object], ENCOUNTERS[args.encounter]):
            raise StoryError("This object and encounter do not make a reasonable ghost story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.encounter is None or c[2] == args.encounter)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, encounter = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting, obj, encounter, name, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.obj], ENCOUNTERS[params.encounter],
                 params.child_name, params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "mirror", "gentle", "Mina", "girl"),
    StoryParams("hall", "bell", "honest", "Theo", "boy"),
    StoryParams("library", "lantern", "kind", "Lily", "girl"),
]


def explain_response(rid: str) -> str:
    e = ENCOUNTERS[rid]
    return f"(Refusing encounter '{rid}': it is too weak or not sensible enough for a moral ghost story.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.bright:
            lines.append(asp.fact("bright", oid))
        if o.fragile:
            lines.append(asp.fact("fragile", oid))
        lines.append(asp.fact("moral", oid, o.moral_value))
    for eid, e in ENCOUNTERS.items():
        lines.append(asp.fact("encounter", eid))
        lines.append(asp.fact("sense", eid, e.sense))
        lines.append(asp.fact("repair", eid, e.repair))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,E) :- setting(S), object(O), encounter(E), bright(O), moral(O,M), sense(E,N), N >= 2, good_moral(M).
"""
# minimal twin; query is enough for parity of valid combos


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos")
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(f"{len(valid_combos())} compatible combos.")
        for s, o, e in valid_combos():
            print(s, o, e)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
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
