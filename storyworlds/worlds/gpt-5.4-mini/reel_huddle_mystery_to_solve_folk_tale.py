#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reel_huddle_mystery_to_solve_folk_tale.py
===========================================================================

A small standalone storyworld for a folk-tale style mystery.

Seed words:
- reel
- huddle

Premise:
A village weaver loses a special reel of red thread on the morning of a feast.
A child and a grandmother huddle with the neighbors, follow small clues, and
solve where the thread went. The ending proves the mystery was solved and the
village can finish its work.

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- generates grounded Q&A from world state
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOLVE_MIN = 2


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa", "mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    kind: str
    has_tracks: bool = False
    has_water: bool = False
    has_hidey: bool = False
    has_barn: bool = False
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
class Mystery:
    id: str
    missing: str
    clue_word: str
    clue_kind: str
    reveal: str
    solution: str
    ending_image: str
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
    places: dict[str, Place] = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(places=copy.deepcopy(self.places))
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
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


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.role == "seeker" and e.memes["worry"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            out.append("__worry__")
    return out


def _r_clue(world: World) -> list[str]:
    out = []
    if world.facts.get("thread_seen") and ("clue", "thread") not in world.fired:
        world.fired.add(("clue", "thread"))
        world.facts["clue_ready"] = True
        out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("clue", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            xs = rule.apply(world)
            if xs:
                changed = True
                produced.extend(x for x in xs if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(params: "StoryParams") -> None:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.mystery == "lost_thread" and not PLACES[params.place].has_tracks:
        raise StoryError("This mystery needs a place with tracks to follow.")
    if params.mystery == "lost_eggs" and not PLACES[params.place].has_barn:
        raise StoryError("This mystery needs a barn or coop to search.")
    if params.huddle_size < 2:
        raise StoryError("A huddle needs at least two people.")


def _do_search(world: World, seeker: Entity, place: Place, mystery: Mystery) -> None:
    seeker.memes["worry"] += 1
    if place.has_tracks:
        world.facts["thread_seen"] = True
    if place.has_water:
        world.facts["water_seen"] = True


def tell(place: Place, mystery: Mystery, seeker_name: str, helper_name: str, elder_name: str,
         seeker_gender: str = "boy", helper_gender: str = "girl", elder_gender: str = "woman",
         huddle_size: int = 3, seed: Optional[int] = None) -> World:
    world = World(places={place.id: place})
    seeker = world.add(Entity(seeker_name, kind="character", type=seeker_gender, role="seeker"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    elder = world.add(Entity(elder_name, kind="character", type=elder_gender, role="elder"))
    villagers = [seeker, helper, elder]

    for v in villagers:
        v.memes["hope"] += 1

    world.say(
        f"In {place.label}, {seeker_name} noticed that the {mystery.missing} had gone missing just before the feast."
    )
    world.say(
        f"{helper_name} and {elder_name} came close, and the three of them huddled together to think."
    )
    world.say(
        f'"We will look for a {mystery.clue_word}," said {elder_name}, "for every mystery leaves a small trail."'
    )

    world.para()
    _do_search(world, seeker, place, mystery)
    if place.has_tracks:
        world.say(
            f"Near the lane, {seeker_name} found {mystery.reveal}, and the clue made the huddle lean closer."
        )
    else:
        world.say(f"They searched carefully, but the first clue stayed hidden.")

    world.para()
    if mystery.id == "lost_thread":
        world.facts["thread_seen"] = True
        world.say(
            f"At last, they followed a thin line of red thread to a mossy stump by the hedge, where a lamb had tangled it in its wool."
        )
        world.say(
            f"{elder_name} laughed softly, untwisted the reel, and carried it home."
        )
        world.say(
            f"By sunset the weaving table was busy again, and the village could finish the feast cloth."
        )
        ending = "The reel sat safely back in the basket, bright as a berry."
    elif mystery.id == "lost_bell":
        world.say(
            f"They followed the sound of tapping to the old well, where the missing bell had rolled under a wooden board."
        )
        world.say(f"{helper_name} reached in, and {seeker_name} rang it once for the whole lane to hear.")
        ending = "The bell chimed from the porch, clear as a song."
    else:
        world.say(
            f"They found the missing jar beside the herb bed, tucked under a leaf like a secret."
        )
        world.say(f"{seeker_name} grinned and placed it in the middle of the table.")
        ending = "The jar gleamed on the table beside the warm bread."

    world.say(
        f"Everyone huddled one last time by the fire, not in worry now, but in cheerful relief."
    )
    world.say(ending)

    world.facts.update(
        place=place,
        mystery=mystery,
        seeker=seeker,
        helper=helper,
        elder=elder,
        huddle_size=huddle_size,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style mystery for a young child that includes the words "reel" and "huddle".',
        f"Tell a warm village story where {f['seeker'].id}, {f['helper'].id}, and {f['elder'].id} huddle together to solve a small mystery.",
        f'Write a simple tale about a missing {f["mystery"].missing} and a clue that leads to the solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker, helper, elder = f["seeker"], f["helper"], f["elder"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was where the missing {mystery.missing} had gone. The village needed it for the feast, so the children and the elder set out to solve it."
        ),
        QAItem(
            question="How did they work together?",
            answer=f"{seeker.id}, {helper.id}, and {elder.id} huddled together and looked for small clues. The huddle helped them think calmly and notice the trail instead of panicking."
        ),
        QAItem(
            question=f"What did they find at the end in {place.label}?",
            answer=f"They found the answer to the mystery and brought the {mystery.missing} back. The ending image shows the village calm again, with the work ready to continue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reel?",
            answer="A reel is a round tool that holds thread, yarn, or string so it can be wound neatly and used little by little."
        ),
        QAItem(
            question="What does it mean to huddle?",
            answer="To huddle means to gather close together, usually to talk quietly, share warmth, or think about what to do next."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first. People solve it by looking for clues and putting the clues together."
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "village": Place("village", "the village lane", "village", has_tracks=True, tags={"tracks", "folk"}),
    "hedge": Place("hedge", "the hedge path", "path", has_tracks=True, has_hidey=True, tags={"tracks", "folk"}),
    "barn": Place("barn", "the old barn", "barn", has_tracks=True, has_barn=True, tags={"barn", "folk"}),
}

MYSTERIES = {
    "lost_thread": Mystery("lost_thread", "reel of red thread", "trail", "clue", "a thin line of red thread on a mossy stump",
                           "a lamb had tangled it in its wool", "The reel sat safely back in the basket, bright as a berry.",
                           tags={"thread", "reel"}),
    "lost_bell": Mystery("lost_bell", "brass bell", "sound", "clue", "a soft tapping near the well",
                         "the bell had rolled under a wooden board", "The bell chimed from the porch, clear as a song.",
                         tags={"bell"}),
    "lost_jar": Mystery("lost_jar", "jam jar", "trace", "clue", "a green leaf by the herb bed",
                        "the jar was tucked beside the herb bed", "The jar gleamed on the table beside the warm bread.",
                        tags={"jar"}),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    mystery: str
    seeker: str
    helper: str
    elder: str
    seeker_gender: str
    helper_gender: str
    elder_gender: str
    huddle_size: int = 3
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mys in MYSTERIES.items():
            if mid == "lost_thread" and place.has_tracks:
                combos.append((pid, mid))
            elif mid == "lost_bell" and place.has_tracks:
                combos.append((pid, mid))
            elif mid == "lost_jar" and (place.has_tracks or place.has_hidey):
                combos.append((pid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--seeker")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
    ap.add_argument("--seeker-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--elder-gender", choices=["man", "woman", "grandmother", "grandfather"])
    ap.add_argument("--huddle-size", type=int, default=3)
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
    reasonableness_gate(StoryParams(
        place=args.place or "village",
        mystery=args.mystery or "lost_thread",
        seeker=args.seeker or "Milo",
        helper=args.helper or "Nina",
        elder=args.elder or "Grandma",
        seeker_gender=args.seeker_gender or "boy",
        helper_gender=args.helper_gender or "girl",
        elder_gender=args.elder_gender or "grandmother",
        huddle_size=args.huddle_size,
    ))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    seeker_gender = args.seeker_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if seeker_gender == "boy" else "boy")
    elder_gender = args.elder_gender or rng.choice(["grandmother", "grandfather", "woman", "man"])
    seeker = args.seeker or rng.choice(["Milo", "Pip", "Lina", "Tess", "Arlo"])
    helper = args.helper or rng.choice(["Nina", "Jory", "Mae", "Wren", "Anya"])
    elder = args.elder or rng.choice(["Grandma", "Grandpa", "Old May", "Wise Ben"])
    return StoryParams(place, mystery, seeker, helper, elder, seeker_gender, helper_gender, elder_gender, args.huddle_size)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(PLACES[params.place], MYSTERIES[params.mystery],
                 params.seeker, params.helper, params.elder,
                 params.seeker_gender, params.helper_gender, params.elder_gender,
                 params.huddle_size, params.seed)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(Place, Mystery) :- place(Place), mystery(Mystery), can_solve(Place, Mystery).
can_solve(village, lost_thread).
can_solve(hedge, lost_thread).
can_solve(barn, lost_thread).
can_solve(village, lost_bell).
can_solve(hedge, lost_bell).
can_solve(barn, lost_bell).
can_solve(village, lost_jar).
can_solve(hedge, lost_jar).
can_solve(barn, lost_jar).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for pid, place in PLACES.items():
        if place.has_tracks:
            lines.append(asp.fact("has_tracks", pid))
        if place.has_barn:
            lines.append(asp.fact("has_barn", pid))
        if place.has_hidey:
            lines.append(asp.fact("has_hidey", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, mystery=None, seeker=None, helper=None, elder=None,
            seeker_gender=None, helper_gender=None, elder_gender=None,
            huddle_size=3, seed=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("village", "lost_thread", "Milo", "Nina", "Grandma", "boy", "girl", "grandmother", 3),
    StoryParams("hedge", "lost_bell", "Lina", "Pip", "Wise Ben", "girl", "boy", "man", 3),
    StoryParams("barn", "lost_jar", "Arlo", "Mae", "Grandpa", "boy", "girl", "grandfather", 3),
]


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
        print(f"{len(asp_valid_combos())} compatible (place, mystery) combos:")
        for p, m in asp_valid_combos():
            print(f"  {p:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
