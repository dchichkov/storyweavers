#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a hoarse mystery to solve.

Premise:
A child or helper in a tiny kingdom hears a strange sound at night.
Their voice has gone hoarse from asking questions and calling for help.
They follow clues, speak with neighbors, and solve the mystery through
dialogue and sound effects.

The domain is intentionally small and constraint-checked:
- one mystery object is hidden in one place
- one sound clue points to the culprit
- one helper gives the final hint
- the ending resolves with a recovered item and a quieter voice
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


# ---------------------------------------------------------------------------
# Entities and world
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: str = ""
    found: bool = False
    heard: bool = False
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "witch", "woman"}
        male = {"boy", "father", "king", "man", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    sound: str
    can_hide: set[str] = field(default_factory=set)
    clue_kind: str = ""
    description: str = ""


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    hidden_at: str
    sound: str
    clue: str
    culprit: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, mystery: Mystery):
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        w = World(self.place, self.mystery)
        w.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "tower": Place(
        id="tower",
        label="the old tower",
        sound="hollow whoosh",
        can_hide={"key", "crown", "lantern"},
        clue_kind="echo",
        description="The tower was tall, round, and full of echoing corners.",
    ),
    "forest": Place(
        id="forest",
        label="the moonlit forest",
        sound="rustle rustle",
        can_hide={"key", "cloak", "bell"},
        clue_kind="rustle",
        description="The forest was thick with leaves and whispering branches.",
    ),
    "kitchen": Place(
        id="kitchen",
        label="the warm kitchen",
        sound="clink clink",
        can_hide={"spoon", "ring", "bowl"},
        clue_kind="clink",
        description="The kitchen smelled of bread, butter, and morning tea.",
    ),
    "garden": Place(
        id="garden",
        label="the sleeping garden",
        sound="shh shh",
        can_hide={"key", "seed", "glove"},
        clue_kind="shiver",
        description="The garden kept its roses curled up like little secrets.",
    ),
}

MYSTERIES = {
    "key": Mystery(
        id="key",
        label="a silver key",
        phrase="a little silver key with a heart-shaped bow",
        hidden_at="tower",
        sound="jing-jing",
        clue="echo",
        culprit="owl",
    ),
    "crown": Mystery(
        id="crown",
        label="a tiny crown",
        phrase="a tiny crown with one blue stone",
        hidden_at="garden",
        sound="ting-ting",
        clue="rustle",
        culprit="wind",
    ),
    "lantern": Mystery(
        id="lantern",
        label="a small lantern",
        phrase="a small lantern with a bright glass belly",
        hidden_at="forest",
        sound="tink-tink",
        clue="clink",
        culprit="hedgehog",
    ),
    "bell": Mystery(
        id="bell",
        label="a brass bell",
        phrase="a brass bell with a ribbon knot",
        hidden_at="kitchen",
        sound="ding-ding",
        clue="shiver",
        culprit="cat",
    ),
}

HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "queen", "king", "guard"]
HERO_NAMES = ["Lina", "Milo", "Nia", "Tomas", "Elsa", "Pip", "Ruby", "Otto"]
HELPER_NAMES = ["Mother Rose", "Father Oak", "Queen Mira", "King Alder", "Guard June"]

TRAITS = ["curious", "brave", "gentle", "quiet", "bright", "earnest"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_valid_combo(place: Place, mystery: Mystery) -> bool:
    return place.id == mystery.hidden_at and mystery.culprit in {"owl", "wind", "hedgehog", "cat"}


def explain_rejection(place: Place, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.label} does not belong in {place.label} in this little fairy tale.)"
    )


def choose_helper_name(helper_type: str) -> str:
    mapping = {
        "mother": "Mother Rose",
        "father": "Father Oak",
        "queen": "Queen Mira",
        "king": "King Alder",
        "guard": "Guard June",
    }
    return mapping[helper_type]


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place, mystery)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        role="hero",
        meters={"voice": 1.0},
        memes={"curiosity": 1.0, "worry": 1.0, "hope": 0.0},
    ))
    helper = world.add(Entity(
        id=choose_helper_name(params.helper_type),
        kind="character",
        type=params.helper_type,
        role="helper",
        meters={},
        memes={"kindness": 1.0},
    ))
    item = world.add(Entity(
        id=mystery.id,
        kind="thing",
        type="thing",
        label=mystery.label,
        phrase=mystery.phrase,
        hidden_in=place.id,
        found=False,
    ))

    world.facts.update(hero=hero, helper=helper, item=item, place=place, mystery=mystery)
    return world


def speak(world: World, line: str) -> None:
    world.say(f'"{line}"')


def investigate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    place: Place = world.facts["place"]
    mystery: Mystery = world.facts["mystery"]
    item: Entity = world.facts["item"]

    world.say(
        f"Once upon a time, {hero.id} wandered into {place.label}. "
        f"{place.description}"
    )
    world.say(
        f"{hero.id} had a hoarse little voice from calling, "
        f"and every word came out scratchy and thin."
    )

    world.para()
    speak(world, f"Did you hear that {place.sound}?")
    speak(world, f"I did,")

    world.say(
        f"said {helper.id}, listening carefully. "
        f"The strange sound went {mystery.sound}, then stopped, then went {mystery.sound} again."
    )
    world.say(
        f"{hero.id} looked under stones and behind doors, but the mystery stayed hidden."
    )

    world.para()
    speak(world, f"If the sound is {mystery.sound}, where should we look?")
    speak(world, f"Listen for the clue,")

    clue_line = {
        "echo": "the tower answered with an echoing knock from above.",
        "rustle": "the leaves rustled like a secret being carried by the wind.",
        "clink": "the shelves gave a tiny clink, as if something hard had tapped wood.",
        "shiver": "the garden shivered softly, and a little jingle came from the vines.",
    }[mystery.clue]
    world.say(f"{helper.id} pointed and said that {clue_line}")

    # Resolution: the clue matches the hidden place and reveals the culprit.
    if item.hidden_in != place.id:
        raise StoryError("The mystery is hidden in the wrong place for this storyworld.")

    item.found = True
    hero.memes["hope"] += 1.0
    hero.meters["voice"] = 0.4  # less strain after help
    world.facts["solved"] = True

    world.para()
    world.say(
        f"At last, {hero.id} found {item.phrase} tucked where the clue had pointed."
    )
    world.say(
        f"Near it was a sign of the culprit too: {mystery.culprit} feathers, "
        f"fur, or tracks, depending on the old fairy tale trick of the night."
    )
    speak(world, f"We solved it!")
    speak(world, f"We solved it together.")

    world.say(
        f"{hero.id}'s voice was still hoarse, but now it sounded happy instead of worried."
    )
    world.say(
        f"And in the soft ending light, {helper.id} smiled while {hero.id} held the found treasure close."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    return [
        f'Write a short fairy-tale mystery story about {hero.id}, a hoarse voice, and {mystery.label} at {place.label}.',
        f"Tell a gentle story where {hero.id} asks questions, {helper.id} helps, and the clue sound is '{mystery.sound}'.",
        f'Write a child-facing story with dialogue and sound effects that ends when the mystery of {mystery.phrase} is solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"Who was trying to solve the mystery in {place.label}?",
            answer=f"{hero.id} was trying to solve it, with help from {helper.id}.",
        ),
        QAItem(
            question=f"What made {hero.id}'s voice sound different?",
            answer=f"{hero.id} had gone hoarse from asking questions and calling for help.",
        ),
        QAItem(
            question=f"What was the hidden object?",
            answer=f"The hidden object was {item.phrase}.",
        ),
        QAItem(
            question=f"What sound clue helped them look in the right place?",
            answer=f"The clue sound was {mystery.sound}, which matched the mystery and led them onward.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} found the missing thing, and the mystery was solved with {helper.id}'s help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]
    return [
        QAItem(
            question="What does it mean for a voice to be hoarse?",
            answer="A hoarse voice sounds scratchy, rough, or tired, often after much talking or shouting.",
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues help people figure out what happened by giving useful hints about where to look.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help readers hear the noises in the scene, like jing-jing or rustle-rustle.",
        ),
        QAItem(
            question=f"What kind of sound does {place.label} make in this fairy tale?",
            answer=f"In this storyworld, {place.label} is associated with the sound {place.sound}.",
        ),
        QAItem(
            question="Why do helpers speak gently in fairy tales?",
            answer="Gentle helpers make the story feel safe and kind while the mystery is being solved.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.found:
            bits.append("found=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:18} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  place={world.place.id} mystery={world.mystery.id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
mystery(M) :- mystery_fact(M).
valid(P, M) :- place_fact(P), mystery_fact(M), hidden_at(M, P).
solved(P, M) :- valid(P, M), clue_matches(M), has_helper(P).

#show valid/2.
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        lines.append(asp.fact("sound", pid, p.sound))
        lines.append(asp.fact("clue_kind", pid, p.clue_kind))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        lines.append(asp.fact("hidden_at", mid, m.hidden_at))
        lines.append(asp.fact("mystery_sound", mid, m.sound))
        lines.append(asp.fact("clue_matches", mid))
        lines.append(asp.fact("culprit", mid, m.culprit))
    for ht in HELPER_TYPES:
        lines.append(asp.fact("has_helper", ht))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p.id, m.id) for p in PLACES.values() for m in MYSTERIES.values() if is_valid_combo(p, m))
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale mystery world with hoarse dialogue and sound effects.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    valid = [(p.id, m.id) for p in PLACES.values() for m in MYSTERIES.values() if is_valid_combo(p, m)]
    filtered = [
        (p, m) for p, m in valid
        if (args.place is None or p == args.place)
        and (args.mystery is None or m == args.mystery)
    ]
    if not filtered:
        raise StoryError("(No valid fairy-tale mystery matches the given options.)")
    place, mystery = rng.choice(filtered)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or choose_helper_name(helper_type)
    if args.helper is None:
        helper = choose_helper_name(helper_type)
    return StoryParams(
        place=place,
        mystery=mystery,
        hero=hero,
        hero_type=hero_type,
        helper_type=helper_type,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    investigate(world)
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
    StoryParams(place="tower", mystery="key", hero="Lina", hero_type="girl", helper_type="queen", helper="Queen Mira"),
    StoryParams(place="forest", mystery="lantern", hero="Milo", hero_type="boy", helper_type="guard", helper="Guard June"),
    StoryParams(place="garden", mystery="crown", hero="Nia", hero_type="girl", helper_type="mother", helper="Mother Rose"),
    StoryParams(place="kitchen", mystery="bell", hero="Otto", hero_type="boy", helper_type="father", helper="Father Oak"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2.\n#show solved/2."))
        print("valid combos:", sorted(set(asp.atoms(model, "valid"))))
        print("solved combos:", sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
            header = f"### {p.hero} at {p.place} solving {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
