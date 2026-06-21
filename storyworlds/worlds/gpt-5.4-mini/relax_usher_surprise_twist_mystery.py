#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/relax_usher_surprise_twist_mystery.py
====================================================================

A small standalone mystery-flavored storyworld about a child visiting a quiet
old place, trying to relax, being ushered along by a guide, and discovering a
surprise twist that solves the mystery in a gentle, concrete way.

Seed words:
- relax
- usher

Features:
- Surprise
- Twist

Style:
- Mystery

The domain is intentionally tiny: a child, a guide, a place, a hidden object,
and a reveal. The world model tracks physical state in meters and emotional
state in memes, and the story is rendered from simulated changes rather than
from a frozen template swap.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
class Place:
    id: str
    label: str
    mood: str
    quiet: str
    echo: str
    hiding_place: str
    secret_sign: str

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
class Guide:
    id: str
    label: str
    role_line: str
    usher_text: str
    relax_text: str

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
class HiddenThing:
    id: str
    label: str
    clue: str
    reveal: str
    twist: str
    surprise: str

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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_unease(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meter("unease") >= THRESHOLD:
            sig = ("unease", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["curiosity"] = e.memes.get("curiosity", 0) + 1
            out.append("__unease__")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    clue = world.facts.get("clue_entity")
    hidden = world.facts.get("hidden_entity")
    seeker = world.facts.get("seeker")
    if not clue or not hidden or not seeker:
        return out
    if clue.meter("noticed") >= THRESHOLD and hidden.meter("revealed") < THRESHOLD:
        sig = ("reveal", hidden.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hidden.meters["revealed"] = 1.0
        seeker.memes["relief"] = seeker.memes.get("relief", 0) + 1
        out.append("__reveal__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_unease, _r_reveal):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
@dataclass
class StoryParams:
    place: str
    guide: str
    hidden: str
    child: str
    child_gender: str
    adult: str
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
    "library": Place("library", "the old library", "quiet", "soft", "echoey", "back desk", "a faint line of dust"),
    "hall": Place("hall", "the museum hall", "quiet", "hushed", "echoey", "curtain nook", "a silver reflection"),
    "attic": Place("attic", "the dusty attic", "still", "creaky", "dim", "old trunk", "a little draft"),
}

GUIDES = {
    "librarian": Guide("librarian", "the librarian", "a kind guide", "ushered", "helped relax"),
    "caretaker": Guide("caretaker", "the caretaker", "a calm guide", "ushered", "helped relax"),
    "aunt": Guide("aunt", "Aunt May", "a patient guide", "ushered", "helped relax"),
}

HIDDENS = {
    "note": HiddenThing("note", "a folded note", "a small clue", "the note was only hiding behind a book", "the clue turned out to be the answer", "a surprise note"),
    "key": HiddenThing("key", "a tiny brass key", "a shining clue", "the key was tucked under a loose board", "the twist was that the key opened the music box", "a surprise key"),
    "badge": HiddenThing("badge", "an old badge", "a strange clue", "the badge was pinned to the back of a frame", "the twist was that it belonged to the missing map", "a surprise badge"),
}

GIRLS = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOYS = ["Ben", "Leo", "Max", "Theo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, g, h) for p in PLACES for g in GUIDES for h in HIDDENS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with relax, usher, surprise, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--hidden", choices=HIDDENS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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


def explain_rejection() -> str:
    return "(No story: the requested mystery ingredients do not form a plausible hidden-clue reveal.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.guide:
        combos = [c for c in combos if c[1] == args.guide]
    if args.hidden:
        combos = [c for c in combos if c[2] == args.hidden]
    if not combos:
        raise StoryError(explain_rejection())
    place, guide, hidden = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRLS if gender == "girl" else BOYS)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(place, guide, hidden, name, gender, adult)


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    guide = GUIDES[params.guide]
    hidden = HIDDENS[params.hidden]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="seeker"))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult, role="helper", label="the adult"))
    clue = world.add(Entity(id="clue", type="thing", label=hidden.clue))
    secret = world.add(Entity(id="secret", type="thing", label=hidden.label))
    world.facts.update(place=place, guide=guide, hidden=hidden, child=child, adult=adult, clue_entity=clue, hidden_entity=secret, seeker=child)

    child.memes["curiosity"] = 1.0
    world.say(f"{child.id} arrived at {place.label}, where the air felt {place.mood} and {place.quiet}.")
    world.say(f"{guide.label} gave {child.id} a gentle smile and {guide.usher_text} {child.pronoun('object')} toward {place.hiding_place}.")
    world.say(f'"Try to { "relax" }," {guide.label} said. "Sometimes the quiet tells a story."')
    world.para()
    child.meter("unease")
    child.meters["unease"] = 1.0
    world.say(f"But {place.secret_sign} caught {child.id}'s eye, and {child.id} could not stop staring.")
    world.say(f"{child.id} noticed {hidden.clue}, and {place.echo} felt like it might be hiding a secret.")
    clue.meters["noticed"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(f"{guide.label} leaned closer. \"Let's {guide.relax_text} and look again,\" {guide.label} said.")
    world.say(f"{child.id} breathed out, and that tiny pause became the start of the mystery.")
    if hidden.id == "key":
        world.say(f"Then came the surprise: {hidden.surprise}.")
        world.say(f"The twist was {hidden.twist}, so the key was not a random trinket at all.")
    elif hidden.id == "note":
        world.say(f"Then came the surprise: {hidden.surprise}.")
        world.say(f"The twist was {hidden.twist}, and the message on the note matched the clue perfectly.")
    else:
        world.say(f"Then came the surprise: {hidden.surprise}.")
        world.say(f"The twist was {hidden.twist}, and the badge belonged to someone everyone had been looking for.")
    child.meters["relaxed"] = 1.0
    world.say(f"In the end, {child.id} smiled at {adult.label_word} and held the clue as if it had been waiting all along.")
    world.say(f"The mystery did not stay scary; it became a small, bright answer hidden inside the quiet room.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that uses the words "relax" and "usher" and ends with a surprise twist.',
        f"Tell a quiet mystery about {f['child'].id} at {f['place'].label} where {f['guide'].label} helps {f['child'].id} relax before a hidden clue is found.",
        f"Write a simple story with a surprise and a twist, where an adult and a guide reveal that {f['hidden'].label} was the answer all along.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    hidden = f["hidden"]
    place = f["place"]
    adult = f["adult"]
    return [
        QAItem("Who is the story about?", f"It is about {child.id}, who visits {place.label} with help from {guide.label}."),
        QAItem("Why did the story feel like a mystery?", f"The room was quiet, a clue was hidden, and {child.id} had to notice little signs to understand what was happening. The surprise twist changed the clue into an answer."),
        QAItem(f"What did {guide.label} do for {child.id}?", f"{guide.label} {guide.usher_text} {child.pronoun('object')} forward and helped {child.id} relax. That made it easier to notice the hidden clue instead of getting scared."),
        QAItem("What was the surprise twist?", f"The surprise was {hidden.surprise}, and the twist was {hidden.twist}. That meant the clue was not random; it pointed straight to the answer."),
        QAItem("How did the story end?", f"It ended with {child.id} smiling at {adult.label_word} and holding the answer safely. The mystery became a gentle discovery instead of a scary one."),
    ]


KNOWLEDGE = [
    QAItem("What is a clue in a mystery?", "A clue is a little piece of information that helps you figure something out. Clues can be tiny details like a sound, a mark, or an object in the wrong place."),
    QAItem("What does it mean to relax?", "To relax means to calm your body and mind. When you relax, you breathe more slowly and feel less tense."),
    QAItem("What does usher mean?", "To usher someone means to guide them along politely. A person who ushers helps another person move to the right place."),
    QAItem("What is a surprise?", "A surprise is something you do not expect. Good stories often use surprises to make the reader wonder what will happen next."),
    QAItem("What is a twist in a story?", "A twist is a new turn that changes what you thought was happening. It can make an ordinary clue suddenly make sense."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,G,H) :- place(P), guide(G), hidden(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for g in GUIDES:
        lines.append(asp.fact("guide", g))
    for h in HIDDENS:
        lines.append(asp.fact("hidden", h))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("library", "librarian", "note", "Mia", "girl", "mother"),
            StoryParams("hall", "caretaker", "key", "Ben", "boy", "father"),
            StoryParams("attic", "aunt", "badge", "Nora", "girl", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
