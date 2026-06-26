#!/usr/bin/env python3
"""
Storyworld: Candid Transformation Quest Rhyme Whodunit

A small whodunit-style domain where a candid detective follows a quest to find
a missing rhyming charm, and the solution is a transformation: someone changes
from suspect to helper when the truth is openly admitted.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "guard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    phrase: str
    risk: str
    transformation: str
    rhyme_key: str
    quest_key: str


@dataclass
class Puzzle:
    mystery: str
    reveal: str
    suspect_hint: str
    rhyme_line: str


@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    detective_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Candid whodunit with a quest, rhyme, and transformation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
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


SETTINGS = {
    "museum": Setting(place="the museum hall", mood="quiet", affords={"search", "listen"}),
    "library": Setting(place="the old library", mood="hushed", affords={"search", "listen"}),
    "garden": Setting(place="the moonlit garden", mood="still", affords={"search", "listen"}),
}

CLUES = {
    "bell": Clue(
        label="silver bell",
        phrase="a tiny silver bell",
        risk="rang too loudly",
        transformation="turned from hidden to heard",
        rhyme_key="bell",
        quest_key="search",
    ),
    "pebble": Clue(
        label="blue pebble",
        phrase="a smooth blue pebble",
        risk="slipped from a pocket",
        transformation="went from dull stone to proof",
        rhyme_key="stone",
        quest_key="search",
    ),
    "ribbon": Clue(
        label="red ribbon",
        phrase="a bright red ribbon",
        risk="looked like an ordinary scrap",
        transformation="became a sign of honesty",
        rhyme_key="glow",
        quest_key="search",
    ),
}

SUSPECTS = {
    "mila": {"type": "girl", "label": "Mila", "hint": "kept looking at the floor"},
    "tom": {"type": "boy", "label": "Tom", "hint": "spoke too quickly"},
    "nora": {"type": "girl", "label": "Nora", "hint": "held a careful little secret"},
}

NAMES = ["Cora", "June", "Iris", "Pip", "Mabel", "Rowan", "Theo", "Luna"]
HELPERS = ["Ava", "Ben", "Finn", "Mina", "Owen", "Zara"]
TRAITS = ["candid", "curious", "brave", "patient"]


def reasonableness_gate(place: str, clue: str, suspect: str) -> bool:
    return place in SETTINGS and clue in CLUES and suspect in SUSPECTS


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("rhyme_key", cid, c.rhyme_key))
        lines.append(asp.fact("quest_key", cid, c.quest_key))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("suspect_type", sid, s["type"]))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,S) :- place(P), clue(C), suspect(S), affords(P,search), rhyme_key(C,_), quest_key(C,search), suspect_type(S,_).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(p, c, s) for p in SETTINGS for c in CLUES for s in SUSPECTS if reasonableness_gate(p, c, s)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    combos = [
        (p, c, s) for p in SETTINGS for c in CLUES for s in SUSPECTS
        if (args.place is None or p == args.place)
        and (args.clue is None or c == args.clue)
        and (args.suspect is None or s == args.suspect)
        and reasonableness_gate(p, c, s)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, clue, suspect = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        clue=clue,
        suspect=suspect,
        detective_name=args.detective_name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
    )


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity]:
    clue = CLUES[params.clue]
    suspect_spec = SUSPECTS[params.suspect]
    detective = world.add(Entity(id=params.detective_name, kind="character", type="detective", label=params.detective_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="helper", label=params.helper_name))
    suspect = world.add(Entity(id=suspect_spec["label"], kind="character", type=suspect_spec["type"], label=suspect_spec["label"]))
    object_ = world.add(Entity(id=clue.label, type="clue", label=clue.label, phrase=clue.phrase, owner=suspect.id))
    object_.worn_by = suspect.id
    return detective, helper, suspect, object_


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    detective, helper, suspect, clue = _setup(world, params)
    clue_def = CLUES[params.clue]
    suspect_hint = SUSPECTS[params.suspect]["hint"]

    world.say(
        f"In {setting.place}, {detective.label} was a candid little detective who liked clear answers."
    )
    world.say(
        f"One night, {detective.label} began a quest to find {clue.phrase}, because the room's silence felt wrong."
    )
    world.para()
    world.say(
        f"{helper.label} whispered that {suspect.label} {suspect_hint}, and the trail began to rhyme like a nursery song."
    )
    world.say(
        f"{detective.label} searched shelves and shadows, following every clue with a steady step."
    )
    world.para()

    world.facts.update(
        detective=detective, helper=helper, suspect=suspect, clue=clue, clue_def=clue_def, setting=setting
    )

    # state-driven turn: the suspect reveals the object and changes from guarded to honest
    suspect.memes["nervous"] = 1.0
    suspect.memes["truth"] = 0.0
    world.say(
        f"At last, {detective.label} asked one more honest question, and {suspect.label} answered candidly."
    )
    world.say(
        f"{suspect.label} admitted that {clue_def.risk}, so {clue.phrase} had been hidden in plain sight."
    )
    world.say(
        f"The answer was a transformation: what looked like a mystery turned into a shared laugh."
    )
    world.para()
    suspect.memes["truth"] = 1.0
    suspect.memes["relief"] = 1.0
    detective.memes["satisfaction"] = 1.0
    helper.memes["joy"] = 1.0

    world.say(
        f"By the end, the clue had {clue_def.transformation}, and the little quest was complete."
    )
    world.say(
        f"{detective.label} and {helper.label} walked home with the rescued {clue.label}, while {suspect.label} smiled at the truth."
    )

    world.facts.update(
        clue=clue,
        transformed=True,
        solved=True,
        suspect_hint=suspect_hint,
        clue_rhyme=clue_def.rhyme_key,
    )

    prompts = [
        f'Write a short whodunit for a child that includes the word "candid" and a small quest.',
        f"Tell a gentle mystery where {detective.label} searches for {clue.phrase} in {setting.place}.",
        f"Write a rhyme-tinged detective story about a missing clue and a truthful ending.",
    ]

    story_qa = [
        QAItem(
            question=f"What was {detective.label} trying to find in {setting.place}?",
            answer=f"{detective.label} was trying to find {clue.phrase}. It was the missing clue in the mystery.",
        ),
        QAItem(
            question=f"Why did the answer feel like a transformation instead of a simple discovery?",
            answer=(
                f"It felt like a transformation because {suspect.label} changed from hiding things to speaking candidly. "
                f"That honest change turned the mystery into a shared solution."
            ),
        ),
        QAItem(
            question=f"How was the story a quest?",
            answer=(
                f"It was a quest because {detective.label} kept searching from place to place, following clues until the truth was found."
            ),
        ),
        QAItem(
            question=f"What made the story feel like a rhyme?",
            answer=(
                f"The clue and the ending were linked by a rhyming, song-like trail of hints, so the mystery sounded playful and neat."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What does candid mean?",
            answer="Candid means honest and open, like telling the truth clearly instead of hiding it.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, where someone keeps going until they reach the goal.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bell and spell.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader follows clues to find out who did something.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:14} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", clue="bell", suspect="mila", detective_name="Cora", helper_name="Ben"),
    StoryParams(place="library", clue="pebble", suspect="tom", detective_name="Iris", helper_name="Mina"),
    StoryParams(place="garden", clue="ribbon", suspect="nora", detective_name="Pip", helper_name="Zara"),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible (place, clue, suspect) combos:")
        for p, c, s in combos:
            print(f"  {p:10} {c:8} {s:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.detective_name}: {p.clue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
