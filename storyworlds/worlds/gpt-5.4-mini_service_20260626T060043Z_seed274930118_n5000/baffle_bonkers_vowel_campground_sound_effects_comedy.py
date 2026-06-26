#!/usr/bin/env python3
"""
A standalone story world for a campground comedy about baffling, bonkers
sound effects and a vowel puzzle.

The seed premise:
- At a campground, a child is baffled by a bonkers sound effect game.
- The game depends on vowels and silly camp noises.
- A small misunderstanding turns into a playful fix and a joke ending.

This file follows the Storyweavers world contract:
- stdlib-only prose engine
- typed entities with meters and memes
- inline ASP twin and Python reasonableness gate
- story + prompts + story QA + world QA
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all
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

VOWELS = {"a", "e", "i", "o", "u"}


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

    def __post_init__(self) -> None:
        for k in ["noise", "mess", "laugh", "confusion", "embarrassment", "relief", "joy"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Campground:
    name: str = "the campground"
    places: list[str] = field(default_factory=lambda: ["the pine loop", "the fire ring", "the picnic table"])
    has_fire: bool = True


@dataclass
class Trick:
    id: str
    title: str
    goal: str
    clue: str
    sound: str
    requires_vowel: bool
    funny_result: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    plural: bool = False


@dataclass
class World:
    campground: Campground
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    campground: str
    trick: str
    prop: str
    name: str
    parent: str
    seed: Optional[int] = None


CAMPGROUNDS = {
    "campground": Campground(name="the campground"),
}

TRICKS = {
    "vowel_call": Trick(
        id="vowel_call",
        title="the vowel call-and-response game",
        goal="call out a vowel in a silly camp voice",
        clue="The leader made a clue sound first, and everyone had to answer with a vowel.",
        sound="Aaa! Eee! Iii!",
        requires_vowel=True,
        funny_result="the answer sounded so goofy that even the raccoons seemed impressed",
    ),
    "bonkers_echo": Trick(
        id="bonkers_echo",
        title="the bonkers echo game",
        goal="repeat a funny sound effect without laughing",
        clue="The first person had to make a sound effect and the next person had to copy it.",
        sound="Boing! Honk! Bloop!",
        requires_vowel=False,
        funny_result="every copy got sillier until the whole loop sounded like a comic book",
    ),
    "baffle_buzz": Trick(
        id="baffle_buzz",
        title="the baffling buzz game",
        goal="guess which camp thing made the buzzing sound",
        clue="One sound came from the tent zipper, one from the snack box, and one from the lantern.",
        sound="Bzzzt!",
        requires_vowel=False,
        funny_result="the clues were so mixed up that everyone laughed before they guessed anything",
    ),
}

PROPS = {
    "whistle": Prop(
        id="whistle",
        label="a bright whistle",
        phrase="a bright whistle with a red cord",
    ),
    "flashlight": Prop(
        id="flashlight",
        label="a flashlight",
        phrase="a small flashlight for night games",
    ),
    "marshmallows": Prop(
        id="marshmallows",
        label="marshmallows",
        phrase="a bag of marshmallows",
        plural=True,
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ella", "Ruby", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Owen", "Jack"]
PARENTS = ["mother", "father"]


class WorldModel(World):
    pass


def _sounds_like_vowel(text: str) -> bool:
    return text[:1].lower() in VOWELS


def reasonableness_gate(trick: Trick, prop: Prop) -> bool:
    if trick.requires_vowel and prop.id == "marshmallows":
        return False
    return True


ASP_RULES = r"""
trick(vowel_call).
trick(bonkers_echo).
trick(baffle_buzz).

prop(whistle).
prop(flashlight).
prop(marshmallows).

requires_vowel(vowel_call).
makes_sound(whistle, "Eee").
makes_sound(flashlight, "Bzzzt").
makes_sound(marshmallows, "Mmm").

reasonable(T,P) :- trick(T), prop(P), not bad_pair(T,P).
bad_pair(vowel_call, marshmallows).
valid(T,P) :- trick(T), prop(P), reasonable(T,P).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in TRICKS.values():
        lines.append(asp.fact("trick", t.id))
        if t.requires_vowel:
            lines.append(asp.fact("requires_vowel", t.id))
    for p in PROPS.values():
        lines.append(asp.fact("prop", p.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for t in TRICKS:
        for p in PROPS:
            if reasonableness_gate(TRICKS[t], PROPS[p]):
                pairs.append((t, p))
    return sorted(pairs)


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_pairs())
    asp_pairs = set(asp_valid_pairs())
    if py == asp_pairs:
        print(f"OK: ASP matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - asp_pairs:
        print("  only in python:", sorted(py - asp_pairs))
    if asp_pairs - py:
        print("  only in ASP:", sorted(asp_pairs - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground comedy story world with vowels and sound effects.")
    ap.add_argument("--campground", choices=CAMPGROUNDS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    pairs = [pair for pair in valid_pairs()
             if (args.trick is None or pair[0] == args.trick)
             and (args.prop is None or pair[1] == args.prop)]
    if not pairs:
        raise StoryError("(No valid campground comedy combination matches the given options.)")
    if args.trick and args.prop and not reasonableness_gate(TRICKS[args.trick], PROPS[args.prop]):
        raise StoryError("That prop does not make a reasonable partner for the chosen trick.")
    trick_id, prop_id = rng.choice(pairs)
    trick = TRICKS[trick_id]
    prop = PROPS[prop_id]
    gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(campground="campground", trick=trick.id, prop=prop.id, name=name, parent=parent)


def build_world(params: StoryParams) -> WorldModel:
    world = WorldModel(campground=CAMPGROUNDS[params.campground])
    trick = TRICKS[params.trick]
    prop = PROPS[params.prop]

    gender = "girl" if params.name in GIRL_NAMES else "boy"
    child = world.add(Entity(id=params.name, kind="character", type=gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(id=prop.id, type=prop.id, label=prop.label, phrase=prop.phrase, owner=child.id, caretaker=parent.id, plural=prop.plural))
    item.worn_by = child.id

    child.memes["baffled"] = 1
    child.memes["curious"] = 1
    parent.memes["playful"] = 1

    world.say(f"{child.id} loved the campground because every trail and tent seemed ready for a joke.")
    world.say(f"One evening, {child.id} brought {item.phrase} to {world.campground.name} and hoped for a big laugh.")
    world.para()
    world.say(f"The game was called {trick.title}, and its clue went like this: {trick.clue}")
    world.say(f"{child.id} listened, then made a face as if a mosquito had told a riddle. {trick.sound}")
    child.meters["confusion"] += 1
    child.memes["baffled"] += 1

    if trick.requires_vowel and prop.id != "marshmallows":
        world.say(f"{params.parent.capitalize()} raised an eyebrow and said, 'Not quite—that sound starts with a vowel, not a wrinkle.'")
        world.say(f"{child.id} giggled anyway, because the whole rule sounded bonkers in the best way.")
        child.memes["embarrassment"] += 1
        parent.memes["joy"] += 1
    elif trick.requires_vowel:
        world.say(f"{params.parent.capitalize()} pointed to the snack bag and said, 'Oops, {item.label} do not begin with a vowel, but this game needs one.'")
        child.meters["confusion"] += 1
        child.memes["baffled"] += 1
    else:
        world.say(f"{params.parent.capitalize()} copied the noise with a flourish, and the campground rang with {trick.sound.lower()}")
        child.meters["laugh"] += 1
        child.memes["joy"] += 1

    world.para()
    if trick.requires_vowel:
        world.say(f"Then {params.parent} turned the moment into a joke and said, 'Let's use a real vowel answer and keep the fun going.'")
        world.say(f"{child.id} shouted, 'Aaa!' so loudly that a nearby zipper seemed to agree.")
        child.meters["noise"] += 1
        child.memes["joy"] += 1
        child.memes["baffled"] = 0
        world.say(f"Everybody laughed when the answer bounced around the pines, and {trick.funny_result}.")
    else:
        world.say(f"{params.parent} changed the game by whispering a new rule: every sound had to be extra silly, but no one could burst out laughing too soon.")
        world.say(f"{child.id} tried a {trick.sound} that sounded so bonkers it almost became a sneeze.")
        child.meters["laugh"] += 1
        child.memes["joy"] += 1
        child.memes["baffled"] = 0
        world.say(f"By the end, the whole campsite was trading sound effects, and {trick.funny_result}.")

    world.facts.update(child=child, parent=parent, prop=item, trick=trick, campground=world.campground)
    return world


def generation_prompts(world: WorldModel) -> list[str]:
    f = world.facts
    child = f["child"]
    trick = f["trick"]
    prop = f["prop"]
    return [
        'Write a short comedy story for a young child set at a campground, with a bonkers sound effect and a vowel joke.',
        f"Tell a funny campground story where {child.id} tries {trick.title} and learns what makes a vowel answer sound right.",
        f"Write a gentle comic story that includes the words baffle, bonkers, and vowel, and ends with everybody laughing at camp.",
        f"Make a simple story about a child, {prop.label}, and a sound effect game at the campground.",
    ]


def story_qa(world: WorldModel) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    trick = f["trick"]
    prop = f["prop"]
    return [
        QAItem(
            question=f"What was {child.id} trying to play at the campground?",
            answer=f"{child.id} was trying to play {trick.title}, a silly campground game with sound effects.",
        ),
        QAItem(
            question=f"Why did {child.id} feel baffled at first?",
            answer=f"{child.id} felt baffled because the clue was bonkers and the game needed a vowel answer, which did not match at first.",
        ),
        QAItem(
            question=f"What helped the story turn funny instead of frustrating?",
            answer=f"{parent.label} turned it into a joke, helped choose a real vowel answer, and kept the game playful.",
        ),
        QAItem(
            question=f"What camp item was part of the scene with {child.id}?",
            answer=f"{child.id} brought {prop.phrase} to the campground, which made the silly game feel extra campy.",
        ),
    ]


def world_knowledge_qa(world: WorldModel) -> list[QAItem]:
    return [
        QAItem(question="What is a vowel?", answer="A vowel is one of the letters a, e, i, o, or u."),
        QAItem(question="What is a sound effect?", answer="A sound effect is a special sound used to make a story or game feel lively and funny."),
        QAItem(question="What is a campground?", answer="A campground is a place where people stay outdoors, often with tents, trees, and a fire ring."),
        QAItem(question="What does bonkers mean?", answer="Bonkers means silly, wild, or a little bit crazy in a funny way."),
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


def dump_trace(world: WorldModel) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def valid_story_params() -> list[StoryParams]:
    out = []
    for trick, prop in valid_pairs():
        out.append(StoryParams(campground="campground", trick=trick, prop=prop, name="Mia", parent="mother"))
    return out


CURATED = [
    StoryParams(campground="campground", trick="vowel_call", prop="whistle", name="Mia", parent="mother"),
    StoryParams(campground="campground", trick="bonkers_echo", prop="flashlight", name="Leo", parent="father"),
    StoryParams(campground="campground", trick="baffle_buzz", prop="marshmallows", name="Nora", parent="mother"),
]


def asp_verify_story() -> int:
    return asp_verify()


def build_asp_show_program() -> str:
    return asp_program("#show valid/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible pairs:")
        for t, p in pairs:
            print(f"  {t:12} {p}")
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
            header = f"### {p.name}: {p.trick} with {p.prop} at {p.campground}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
