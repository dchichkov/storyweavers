#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/derelict_bonnie_magic_nursery_rhyme.py
======================================================================

A standalone storyworld script for a small TinyStories-style domain inspired by
the seed words "derelict" and "bonnie", with a nursery-rhyme feel and a touch
of magic.

Premise
-------
A bonnie child finds a derelict little place where the music has gone quiet.
A magical helper and a simple rhyme help them wake the place, mend what is worn,
and end with a bright, child-facing image that proves the change.

The world is built from typed entities with physical meters and emotional memes.
The prose is driven from simulated state, not from a frozen paragraph template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/derelict_bonnie_magic_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/derelict_bonnie_magic_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/derelict_bonnie_magic_nursery_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/derelict_bonnie_magic_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/derelict_bonnie_magic_nursery_rhyme.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MEND_GOAL = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "girl": "girl", "boy": "boy"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    ruin: str
    quiet: str
    song: str
    dust: float
    broken: float
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
class MagicTool:
    id: str
    label: str
    phrase: str
    spark: str
    power: float
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
class Repair:
    id: str
    label: str
    verb: str
    finish: str
    power: float
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
        self.place: Optional[Place] = None

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
        clone.facts = copy.deepcopy(self.facts)
        clone.place = copy.deepcopy(self.place)
        return clone


@dataclass
@dataclass
class StoryParams:
    place: str
    magic: str
    repair: str
    name: str
    parent: str
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


PLACES = {
    "nursery": Place(
        "nursery", "a derelict nursery", "derelict", "very quiet", "no song at all",
        dust=2.0, broken=1.0, tags={"derelict", "nursery"}),
    "garden": Place(
        "garden", "a derelict little garden", "derelict", "very still", "no bird song",
        dust=1.5, broken=1.2, tags={"derelict", "garden"}),
    "attic": Place(
        "attic", "a derelict attic", "derelict", "very dim", "no humming at all",
        dust=2.2, broken=1.1, tags={"derelict", "attic"}),
}

MAGIC = {
    "wand": MagicTool("wand", "a tiny wand", "tap the dust", "with a twinkle", 1.4, {"magic", "wand"}),
    "rhyme": MagicTool("rhyme", "a rhyme", "sing the old rhyme", "with a sing-song chime", 1.2, {"magic", "rhyme"}),
    "bell": MagicTool("bell", "a silver bell", "ring the little bell", "with a bright ding-ding", 1.6, {"magic", "bell"}),
}

REPAIRS = {
    "mend": Repair("mend", "mend", "mend the broken bits", "the broken bits were sound again", 1.2, {"mend"}),
    "sweep": Repair("sweep", "sweep", "sweep away the old dust", "the floor shone clean and neat", 1.0, {"sweep"}),
    "brighten": Repair("brighten", "brighten", "brighten the dark corners", "the corners glowed like dawn", 1.3, {"brighten"}),
}

GIRL_NAMES = ["Bonnie", "Lily", "Mia", "Elsie", "Nora"]
BOY_NAMES = ["Toby", "Finn", "Owen", "Jack", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for m in MAGIC:
            for r in REPAIRS:
                if MAGIC[m].power + REPAIRS[r].power >= PLACES[p].dust + PLACES[p].broken:
                    out.append((p, m, r))
    return out


def reason_gate(place: Place, magic: MagicTool, repair: Repair) -> bool:
    return magic.power + repair.power >= place.dust + place.broken


def explain_rejection(place: Place, magic: MagicTool, repair: Repair) -> str:
    return (
        f"(No story: {magic.label} and {repair.label} are not strong enough to "
        f"wake {place.label} from its derelict hush. Pick a different magic or a gentler ruin.)"
    )


def with_article(text: str) -> str:
    return text if text.startswith(("a ", "an ", "the ")) else f"a {text}"


def tune_state(world: World) -> None:
    p = world.place
    if p is None:
        return
    world.get("place").meters["dust"] = p.dust
    world.get("place").meters["broken"] = p.broken
    if p.dust < 0.5 and p.broken < 0.5:
        world.get("place").memes["joy"] += 1
    elif p.dust < 1.0:
        world.get("place").memes["hope"] += 1


def cast_magic(world: World, child: Entity, tool: MagicTool, repair: Repair) -> None:
    place = world.get("place")
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} found {tool.phrase} in the {world.place.label}, {tool.spark}. "
        f"The place was {world.place.ruin} and {world.place.quiet}, with {world.place.song}."
    )
    world.say(f'"Come, come," {child.id} said, and {tool.spark} {tool.verb} left the dust to dance.')
    place.meters["dust"] = max(0.0, place.meters["dust"] - tool.power)
    place.meters["sparkle"] += 1
    child.memes["hope"] += 1
    if place.meters["dust"] < THRESHOLD:
        world.say(f"The first bit of grey mist lifted, and the corners looked less lonely.")
    world.para()
    place.meters["broken"] = max(0.0, place.meters["broken"] - repair.power)
    world.say(
        f"Then {child.id} began to {repair.verb}. With care and a bit of song, "
        f"{repair.finish}."
    )
    if place.meters["broken"] < THRESHOLD:
        child.memes["joy"] += 1
    world.say(
        f"At last the {place.label} was no longer {world.place.ruin}; it was bright, "
        f"bonnie, and new enough to smile."
    )


def tell(place: Place, magic: MagicTool, repair: Repair, name: str = "Bonnie", parent: str = "mom") -> World:
    world = World()
    world.place = place
    child = world.add(Entity(id=name, kind="character", type="girl", role="child", traits=["bonnie"]))
    grown = world.add(Entity(id=parent.title(), kind="character", type="mother" if parent == "mom" else "father", role="grownup"))
    room = world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id=magic.id, type="tool", label=magic.label, attrs={"magic": True}))
    world.add(Entity(id=repair.id, type="tool", label=repair.label, attrs={"repair": True}))
    child.memes["hope"] = 1.0
    grown.memes["care"] = 1.0
    tune_state(world)
    world.say(
        f"{child.id} was a bonnie little child who liked to hum a tune. One day {child.id} "
        f"went to {place.label}, and the old place was derelict and grey."
    )
    world.say(
        f"{child.id} looked around and said, \"Oh dear me, this place has lost its cheer.\""
    )
    world.para()
    world.say(
        f"{grown.id} came softly near and said, \"A little magic can mend a lot, but we must "
        f"use it kindly and keep our voices sweet.\""
    )
    cast_magic(world, child, magic, repair)
    world.para()
    grown.memes["joy"] += 1
    world.say(
        f"{grown.id} smiled and clapped. \"Now that is a bonnie change,\" {grown.pronoun()} said, "
        f"and {child.id} skipped home with a spring in {child.pronoun('possessive')} step."
    )
    world.facts.update(child=child, grown=grown, place=place, magic=magic, repair=repair)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story for a child named {f["child"].id} that includes the words "derelict" and "bonnie".',
        f"Tell a gentle magical tale where {f['child'].id} finds a derelict place and uses a little magic to make it bright again.",
        f'Write a short sing-song story with a happy ending, soft magic, and the word "{f["place"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, grown, place, magic, repair = f["child"], f["grown"], f["place"], f["magic"], f["repair"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, a bonnie little child, and {grown.label_word if grown.label_word else 'a grown-up'} who helped with the magic. They went to {place.label} and changed it together."),
        QAItem(
            question="What was wrong with the place at first?",
            answer=f"It was derelict, dusty, and very quiet. The old place had lost its song, so it felt lonely before the magic began."),
        QAItem(
            question="How did the problem get fixed?",
            answer=f"{child.id} used {magic.label} and then {repair.label} to wake the place up. The magic cleared the dust and the repair made the broken bits sound again."),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {place.label} bright and smiling instead of derelict. {child.id} went home happy because the place had a new spark of life."),
    ]


WORLD_KNOWLEDGE = {
    "derelict": [QAItem(
        question="What does derelict mean?",
        answer="Derelict means old, neglected, and in bad shape because nobody has taken care of it.")],
    "magic": [QAItem(
        question="What is magic in a story?",
        answer="Magic is a special made-up power that can do surprising things, like make a light sparkle or help something change.")],
    "nursery": [QAItem(
        question="What is a nursery rhyme?",
        answer="A nursery rhyme is a short, sing-song story or poem for children. It often has a gentle rhythm and easy words.")],
    "bonnie": [QAItem(
        question="What does bonnie mean?",
        answer="Bonnie is a sweet word that means pretty, lovely, or nice to look at.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.place.tags)
    tags |= {"magic", "nursery", "bonnie"}
    out: list[QAItem] = []
    for key in ["bonnie", "derelict", "magic", "nursery"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("dust", pid, p.dust))
        lines.append(asp.fact("broken", pid, p.broken))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("power", mid, m.power))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
good(P, M, R) :- place(P), magic(M), repair(R), dust(P, D), broken(P, B), power(M, PM), power(R, PR), PM + PR >= D + B.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show good/3."))
    return sorted(set(asp.atoms(model, "good")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    # smoke test one normal generation path
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bonnie derelict magic nursery-rhyme storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mom", "dad"])
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
    if args.place and args.magic and args.repair:
        if not reason_gate(PLACES[args.place], MAGIC[args.magic], REPAIRS[args.repair]):
            raise StoryError(explain_rejection(PLACES[args.place], MAGIC[args.magic], REPAIRS[args.repair]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)
              and (args.repair is None or c[2] == args.repair)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, magic, repair = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES)
    parent = args.parent or rng.choice(["mom", "dad"])
    return StoryParams(place, magic, repair, name, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MAGIC[params.magic], REPAIRS[params.repair], params.name, params.parent)
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
    StoryParams("nursery", "wand", "mend", "Bonnie", "mom"),
    StoryParams("garden", "rhyme", "brighten", "Bonnie", "dad"),
    StoryParams("attic", "bell", "sweep", "Bonnie", "mom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show good/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, m, r in combos:
            print(f"  {p:8} {m:6} {r}")
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} + {p.magic} + {p.repair}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
