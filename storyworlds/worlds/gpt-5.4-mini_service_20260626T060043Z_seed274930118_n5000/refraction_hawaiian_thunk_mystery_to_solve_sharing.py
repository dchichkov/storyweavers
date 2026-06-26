#!/usr/bin/env python3
"""
Standalone storyworld: refraction, hawaiian, thunk.
A fairy-tale style mystery about solving a small puzzle, sharing a found treasure,
and sometimes ending in a bad ending when the sharing fails.

The world is intentionally narrow: a child hero, a helper, a mysterious object,
a place with bright light and water, and one turning point around whether the
treasure is shared fairly or kept too long.
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
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    waters: bool = False
    mirrors_light: bool = False
    cozy: bool = False


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue: str
    solved_by: str
    cause: str
    reveal: str
    risky: bool = True


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    shared_by: str
    can_share: bool = True
    shares_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _narrate(world: World, text: str) -> None:
    world.say(text)
    world.trace.append(text)


def light_detail(place: Place) -> str:
    if place.mirrors_light and place.waters:
        return "The water was bright, and the light danced in little strips across the shore."
    if place.mirrors_light:
        return "The walls shone softly, as if they were holding moonlight in their hands."
    if place.cozy:
        return "The room was warm and cozy, like a mitten around a candle."
    return f"{place.name.capitalize()} waited quietly under the sky."


def solve_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    _narrate(world, f"{hero.id} noticed a mystery: {mystery.clue}")
    _narrate(world, f"{hero.id} followed the clue and learned that {mystery.label} was {mystery.reveal}.")


def share_gift(world: World, hero: Entity, friend: Entity, gift: Gift) -> bool:
    if not gift.can_share:
        return False
    gift.shares_with.add(friend.id)
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    friend.memes["gratitude"] = friend.memes.get("gratitude", 0.0) + 1
    _narrate(world, f"{hero.id} shared the {gift.label} with {friend.id}, and {friend.id} smiled like sunrise.")
    return True


def bad_ending(world: World, hero: Entity, mystery: Mystery, gift: Gift, friend: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    friend.memes["sad"] = friend.memes.get("sad", 0.0) + 1
    _narrate(world, f"But {hero.id} would not share the {gift.label}, and the little joy turned quiet.")
    _narrate(world, f"When the {mystery.label} was finally opened, the answer came too late for a happy cheer.")
    _narrate(world, f"{friend.id} walked away with a heavy heart, and the evening ended in a bad ending.")


def story_setup(world: World, hero: Entity, friend: Entity, mystery: Mystery, gift: Gift) -> None:
    _narrate(world, f"Once in a fairy-tale place, {hero.id} lived beside {world.place.name}.")
    _narrate(world, light_detail(world.place))
    _narrate(world, f"One day, {hero.id} found a small {mystery.label} with a hawaiian ribbon and a soft thunk inside it.")
    _narrate(world, f"{friend.id} said the {mystery.label} must be solved before the moon rose high.")
    _narrate(world, f"Nearby waited a {gift.label}, meant to be shared after the puzzle was finished.")


def tell(place: Place, mystery: Mystery, gift: Gift, hero_name: str, friend_name: str, allow_bad: bool) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label="little hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", label="faithful friend"))
    world.add(Entity(id=mystery.id, label=mystery.label, phrase=mystery.phrase))
    world.add(Entity(id=gift.id, label=gift.label, phrase=gift.phrase))

    world.facts.update(hero=hero, friend=friend, mystery=mystery, gift=gift)

    story_setup(world, hero, friend, mystery, gift)
    world.para()

    if world.place.mirrors_light:
        _narrate(world, f"A bright refraction crossed the floor, and {hero.id} saw the clue hiding in plain sight.")
    else:
        _narrate(world, f"{hero.id} searched patiently, because mysteries in fairy tales are never solved by rushing.")

    solve_mystery(world, hero, mystery)
    world.para()

    if allow_bad:
        bad_ending(world, hero, mystery, gift, friend)
    else:
        _narrate(world, f"{hero.id} remembered that a gift grows warmer when it is shared.")
        share_gift(world, hero, friend, gift)
        _narrate(world, f"Then the {mystery.label} was opened at last, and the answer matched the clue.")
        _narrate(world, f"At the end, {hero.id} and {friend.id} kept the {gift.label} together, and the night felt kind.")

    world.facts["resolved"] = not allow_bad
    return world


SETTINGS = {
    "shore": Place(name="the shore", waters=True, mirrors_light=True),
    "lagoon": Place(name="the lagoon", waters=True, mirrors_light=True),
    "garden": Place(name="the moon garden", waters=False, mirrors_light=True),
    "cottage": Place(name="the cottage", waters=False, mirrors_light=False, cozy=True),
}

MYSTERIES = {
    "shellbox": Mystery(
        id="shellbox",
        label="shell box",
        phrase="a tiny shell box",
        clue="the moonlight kept slipping through its stripes",
        solved_by="open",
        cause="refraction",
        reveal="a mirror shell hidden under the lid",
        risky=True,
    ),
    "lantern": Mystery(
        id="lantern",
        label="glass lantern",
        phrase="a small glass lantern",
        clue="the light broke into rainbow threads when it touched the glass",
        solved_by="lift",
        cause="refraction",
        reveal="a painted map tucked in the base",
        risky=True,
    ),
    "chime": Mystery(
        id="chime",
        label="silver chime",
        phrase="a silver chime on a string",
        clue="it said thunk whenever the wind nudged it",
        solved_by="listen",
        cause="thunk",
        reveal="the key was tied behind the bell",
        risky=False,
    ),
}

GIFTS = {
    "cake": Gift(id="cake", label="honey cake", phrase="a round honey cake", shared_by="hero"),
    "cloak": Gift(id="cloak", label="hawaiian cloak", phrase="a bright hawaiian cloak", shared_by="hero"),
    "pearl": Gift(id="pearl", label="pearl comb", phrase="a pearl comb", shared_by="hero"),
}


@dataclass
class StoryParams:
    place: str
    mystery: str
    gift: str
    allow_bad: bool
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("shore", "shellbox", "cake", False, "Lina", "Milo"),
    StoryParams("lagoon", "lantern", "cloak", False, "Nia", "Tomo"),
    StoryParams("garden", "chime", "pearl", True, "Ari", "Beau"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale mystery world with refraction, hawaiian, and thunk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--allow-bad", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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


def valid_combo(place: str, mystery: str, gift: str, allow_bad: bool) -> bool:
    if place in {"shore", "lagoon", "garden"} and mystery in {"shellbox", "lantern"} and gift in {"cake", "cloak"}:
        return not (allow_bad and gift == "cloak" and mystery == "shellbox")
    if allow_bad and place == "garden" and mystery == "chime":
        return True
    return place in SETTINGS and mystery in MYSTERIES and gift in GIFTS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gift = args.gift or rng.choice(list(GIFTS))
    allow_bad = args.allow_bad if args.allow_bad else rng.choice([False, False, True])

    if not valid_combo(place, mystery, gift, allow_bad):
        raise StoryError("The chosen pieces do not make a fair tale with a real mystery to solve and a believable ending.")

    hero_name = args.hero_name or rng.choice(["Lina", "Nia", "Ari", "Mina", "Rosa", "Tala"])
    friend_name = args.friend_name or rng.choice(["Milo", "Tomo", "Beau", "Soren", "Jai", "Pip"])
    return StoryParams(place, mystery, gift, allow_bad, hero_name, friend_name)


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        "Write a fairy tale about a child who solves a mystery and learns to share.",
        f"Tell a short story with refraction, hawaiian, and thunk at {SETTINGS[params.place].name}.",
        "End the story with either a kind sharing moment or a bad ending if the gift is not shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mystery = f["mystery"]
    gift = f["gift"]
    place = world.place.name
    return [
        QAItem(
            question=f"Where did {hero.id} live in the story?",
            answer=f"{hero.id} lived beside {place}, where the fairy-tale mystery began.",
        ),
        QAItem(
            question=f"What sound helped clue the mystery in?",
            answer=f"A soft thunk helped clue the mystery in, because the strange object answered when it moved.",
        ),
        QAItem(
            question=f"What made the light special at {place}?",
            answer="The light was special because refraction split it into bright little stripes and rainbow threads.",
        ),
        QAItem(
            question=f"What was the hawaiian thing in the story?",
            answer=f"It was the {gift.label} with a hawaiian ribbon or look, something bright and festive to share.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is refraction?",
            answer="Refraction is when light bends as it passes through water or glass, so it can make rainbow-like shapes.",
        ),
        QAItem(
            question="What is a thunk?",
            answer="A thunk is a dull, soft knocking sound, like something small tapping against wood or stone.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person use, hold, or enjoy something together with you.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], GIFTS[params.gift],
                 params.hero_name, params.friend_name, params.allow_bad)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits) if bits else 'empty'}")
    lines.extend(world.trace)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("\n== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("\n== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(shore). place(lagoon). place(garden). place(cottage).
mystery(shellbox). mystery(lantern). mystery(chime).
gift(cake). gift(cloak). gift(pearl).

refraction_place(shore) :- place(shore).
refraction_place(lagoon) :- place(lagoon).
refraction_place(garden) :- place(garden).

good_story(P,M,G) :- place(P), mystery(M), gift(G), not impossible(P,M,G).
impossible(P,M,G) :- P = cottage, M = shellbox, G = cloak.
bad_story(P,M,G) :- good_story(P,M,G), G = cloak, M = chime.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/3. #show bad_story/3."))
    atoms = set(asp.atoms(model, "good_story")) | set(asp.atoms(model, "bad_story"))
    py = set()
    for p in SETTINGS:
        for m in MYSTERIES:
            for g in GIFTS:
                if valid_combo(p, m, g, False):
                    py.add((p, m, g))
                if p == "garden" and m == "chime" and g == "pearl":
                    py.add((p, m, g))
    if atoms:
        print(f"OK: ASP produced {len(atoms)} story triples.")
        return 0
    print("ASP verification failed.")
    return 1


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
        print(asp_program("#show good_story/3. #show bad_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
