#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chitchat_duplicate_misunderstanding_happy_ending_conflict_slice.py
=================================================================================================

A tiny slice-of-life storyworld about a small misunderstanding during chitchat:
someone thinks a duplicate note means something is being copied or hidden, the
friends have a little conflict, then they check the facts, laugh, and end with a
happy fix.

The domain is intentionally small and state-driven:
- typed entities with physical meters and emotional memes,
- a simple forward-chained world model,
- a reasonableness gate that only allows plausible misunderstandings,
- inline ASP facts/rules mirroring the Python checks,
- three Q&A sets grounded in the simulated world, not by parsing rendered prose.

Seed words:
- chitchat
- duplicate

Features:
- Misunderstanding
- Conflict
- Happy Ending

Style:
- Slice of life
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class MisunderstandingCfg:
    id: str
    clue_word: str
    mistaken_meaning: str
    real_meaning: str
    tension_line: str
    fix_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    characters: str
    misunderstanding: str
    object: str
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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("misread", 0.0) < THRESHOLD:
            continue
        if ("conflict", ent.id) in world.fired:
            continue
        world.fired.add(("conflict", ent.id))
        ent.memes["hurt"] = ent.memes.get("hurt", 0.0) + 1
        out.append("__conflict__")
    return out


RULES = [Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in SETTINGS:
        for chars in CHARSET:
            for mid, mis in MISUNDERSTANDINGS.items():
                for obj_id, obj in OBJECTS.items():
                    if mis.id == "duplicate_note" and obj.id == "notes":
                        combos.append((setting, chars, obj_id))
                    if mis.id == "double_booking" and obj.id == "calendar":
                        combos.append((setting, chars, obj_id))
                    if mis.id == "same_mug" and obj.id == "mug":
                        combos.append((setting, chars, obj_id))
    return combos


def reasonableness_check(mis: MisunderstandingCfg, obj: ObjectCfg) -> bool:
    return (mis.id == "duplicate_note" and obj.id == "notes") or (
        mis.id == "double_booking" and obj.id == "calendar"
    ) or (mis.id == "same_mug" and obj.id == "mug")


def explain_rejection(mis: MisunderstandingCfg, obj: ObjectCfg) -> str:
    return (
        f"(No story: {mis.clue_word} and {obj.label} do not make a believable "
        f"slice-of-life misunderstanding here.)"
    )


def tell(setting: str, chars: str, mis: MisunderstandingCfg, obj: ObjectCfg) -> World:
    world = World()
    a_name, b_name = chars.split(":")
    a = world.add(Entity(id=a_name, kind="character", type="girl" if a_name in GIRL_NAMES else "boy", role="speaker"))
    b = world.add(Entity(id=b_name, kind="character", type="girl" if b_name in GIRL_NAMES else "boy", role="listener"))
    room = world.add(Entity(id="room", type="room", label=setting))
    thing = world.add(Entity(id=obj.id, type="object", label=obj.label))
    a.memes["curious"] = 1
    b.memes["curious"] = 1

    world.say(
        f"On a quiet afternoon at {setting}, {a.id} and {b.id} were having "
        f"soft little chitchat over {obj.phrase}."
    )
    world.say(
        f"{a.id} noticed a duplicate and frowned. {mis.tension_line}"
    )
    world.para()
    world.say(
        f'"Wait," {b.id} said. "That is not what it means."'
    )
    thing.meters["misread"] = 1
    propagate(world, narrate=False)
    a.memes["embarrassed"] = 1
    b.memes["patient"] = 1
    world.say(
        f"They checked the {obj.label_word} again together, and the confusion "
        f"started to shrink."
    )
    world.para()
    world.say(
        f"{mis.fix_line} Soon the two friends were laughing, and the little "
        f"mix-up felt silly instead of big."
    )
    world.say(
        f"By the end, the room felt warmer, the {obj.label_word} stayed in place, "
        f"and their chitchat turned cheerful again."
    )

    world.facts.update(
        setting=setting,
        chars=chars,
        misunderstanding=mis,
        object_cfg=obj,
        a=a,
        b=b,
        room=room,
        thing=thing,
        conflict=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mis: MisunderstandingCfg = f["misunderstanding"]
    obj: ObjectCfg = f["object_cfg"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    return [
        f'Write a slice-of-life story that includes the words "{mis.clue_word}" and "chitchat" and ends happily.',
        f"Tell a small story where {a.id} and {b.id} have a misunderstanding about {obj.label} during chitchat, then fix it kindly.",
        f"Write a child-friendly story with a little conflict, a misunderstanding, and a happy ending about {obj.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mis: MisunderstandingCfg = f["misunderstanding"]
    obj: ObjectCfg = f["object_cfg"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    return [
        ("What were the children doing?",
         f"They were having chitchat in a quiet everyday moment, just like a normal slice-of-life afternoon."),
        (f"What did {a.id} misunderstand?",
         f"{a.id} misunderstood the duplicate and thought something was wrong with {obj.label}. "
         f"{mis.tension_line}"),
        ("How did they fix the problem?",
         f"{b.id} explained the real meaning, and they checked {obj.label} together. "
         f"That careful talk cleared up the confusion and turned the conflict into a happy ending."),
        ("How did the story end?",
         f"It ended with both friends laughing and feeling close again. The misunderstanding was gone, and the room felt calm."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj: ObjectCfg = f["object_cfg"]
    items = []
    for tag in sorted(obj.tags | f["misunderstanding"].tags):
        if tag in KNOWLEDGE:
            items.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return items


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


SETTINGS = ["kitchen_table", "school_lobby", "apartment_hall"]
CHARSET = ["Mina:Jules", "Tia:Noah", "Lena:Owen"]
GIRL_NAMES = {"Mina", "Tia", "Lena"}
BOY_NAMES = {"Jules", "Noah", "Owen"}

MISUNDERSTANDINGS = {
    "duplicate_note": MisunderstandingCfg(
        id="duplicate_note",
        clue_word="duplicate",
        mistaken_meaning="a second copy that means trouble",
        real_meaning="an extra copy or note",
        tension_line="The word sounded suspicious, and {a} thought a duplicate meant someone was hiding something.",
        fix_line="It was only a spare note, not a secret trick.",
        tags={"duplicate", "note"},
    ),
    "double_booking": MisunderstandingCfg(
        id="double_booking",
        clue_word="duplicate",
        mistaken_meaning="two plans for one time",
        real_meaning="a calendar entry copied by accident",
        tension_line="The duplicated calendar line looked like two plans at once, and {a} worried their turn was lost.",
        fix_line="It was just the same event copied twice by mistake.",
        tags={"duplicate", "calendar"},
    ),
    "same_mug": MisunderstandingCfg(
        id="same_mug",
        clue_word="duplicate",
        mistaken_meaning="someone took the mug",
        real_meaning="two mugs that matched",
        tension_line="The duplicate mug made {a} think someone had swapped things around.",
        fix_line="It was only a matching mug sitting beside the first one.",
        tags={"duplicate", "mug"},
    ),
}

OBJECTS = {
    "notes": ObjectCfg(id="notes", label="notes", phrase="the little notes on the table", tags={"note", "duplicate"}),
    "calendar": ObjectCfg(id="calendar", label="calendar", phrase="the kitchen calendar", tags={"calendar", "duplicate"}),
    "mug": ObjectCfg(id="mug", label="mug", phrase="the warm mug on the counter", tags={"mug", "duplicate"}),
}

KNOWLEDGE = {
    "duplicate": [("What does duplicate mean?", "Duplicate means a copy of something, or something that appears twice.")],
    "note": [("What is a note?", "A note is a short piece of writing that helps people remember something.")],
    "calendar": [("What is a calendar for?", "A calendar helps people keep track of days, plans, and appointments.")],
    "mug": [("What is a mug?", "A mug is a cup with a handle, often used for hot drinks.")],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with chitchat and a duplicate misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--characters", choices=CHARSET)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--object", choices=OBJECTS)
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
    if args.misunderstanding and args.object:
        if not reasonableness_check(MISUNDERSTANDINGS[args.misunderstanding], OBJECTS[args.object]):
            raise StoryError(explain_rejection(MISUNDERSTANDINGS[args.misunderstanding], OBJECTS[args.object]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.characters is None or c[1] == args.characters)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, chars, obj_id = rng.choice(sorted(combos))
    if args.misunderstanding:
        mis = args.misunderstanding
    else:
        mis = rng.choice([m for m, cfg in MISUNDERSTANDINGS.items() if reasonableness_check(cfg, OBJECTS[obj_id])])
    return StoryParams(setting=setting, characters=chars, misunderstanding=mis, object=obj_id)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.characters not in CHARSET or params.misunderstanding not in MISUNDERSTANDINGS or params.object not in OBJECTS:
        raise StoryError("Invalid story parameters.")
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    obj = OBJECTS[params.object]
    if not reasonableness_check(mis, obj):
        raise StoryError(explain_rejection(mis, obj))
    world = tell(params.setting, params.characters, mis, obj)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, O) :- setting(S), chars(C), object(O), mismatch_ok(S, C, O).
mismatch_ok(S, C, O) :- setting(S), chars(C), object(O), object_tag(O, duplicate), mis_ok(O).
mis_ok(notes) :- object_tag(notes, note).
mis_ok(calendar) :- object_tag(calendar, calendar).
mis_ok(mug) :- object_tag(mug, mug).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHARSET:
        lines.append(asp.fact("chars", c))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        for t in sorted(obj.tags):
            lines.append(asp.fact("object_tag", oid, t))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        for t in sorted(mis.tags):
            lines.append(asp.fact("mis_tag", mid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, characters=None, misunderstanding=None, object=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        return 1
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


CURATED = [
    StoryParams(setting="kitchen_table", characters="Mina:Jules", misunderstanding="duplicate_note", object="notes"),
    StoryParams(setting="school_lobby", characters="Tia:Noah", misunderstanding="double_booking", object="calendar"),
    StoryParams(setting="apartment_hall", characters="Lena:Owen", misunderstanding="same_mug", object="mug"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
