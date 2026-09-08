#!/usr/bin/env python3
"""
mechanism_friendship_cautionary_twist_mystery.py
=================================================

A small mystery world about a friend group, a curious mechanism, a cautious
investigation, and a twist that changes what everyone thinks is happening.

Seed tale:
---
At the old clock shop, a tiny mechanism began clicking at midnight. Mara and Jo
thought a hidden burglar was inside the walls, but the clicks came from the
shop's friendly music box, which had fallen behind a shelf and was trying to
wind itself by rocking on a loose spring. The friends used caution, worked
together, and learned that strange noises can have gentle explanations.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    linked_to: Optional[str] = None
    movable: bool = True
    noisy: bool = False
    safe: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None
    opening: int = 0
    sound: int = 0
    warning: int = 0
    clue: int = 0
    twist: int = 0
    ending: int = 0


SETTINGS = {
    "clockshop": Setting(place="the old clock shop", indoor=True, affords={"music_box", "clock", "spring"}),
    "attic": Setting(place="the dusty attic", indoor=True, affords={"music_box", "clock", "spring"}),
    "workshop": Setting(place="the back workshop", indoor=True, affords={"music_box", "clock", "spring"}),
}

HERO_NAMES = ["Mara", "Jo", "Nell", "Toby", "Iris", "Ben"]
FRIEND_NAMES = ["Jo", "Mara", "Pip", "Tess", "Otis", "June"]

OPENINGS = [
    "Late at night, {hero} and {friend} stood outside {place}, where the door had a thin silver crack of light.",
    "The bells above {place} were silent when {hero} and {friend} entered with one small lantern.",
    "At {place}, {hero} had promised {friend} a quick look at the strange noise before bedtime.",
    "When the street grew quiet, {hero} and {friend} tiptoed into {place} to solve a mystery.",
    "The windows of {place} glowed faintly while {hero} and {friend} counted their careful steps.",
    "A hush settled over {place}, and {hero} whispered to {friend} that tonight's clue would be small but important.",
    "On a windy evening, {hero} and {friend} opened the door to {place} and heard a faint click inside.",
    "Before the shopkeeper returned, {hero} and {friend} went into {place} to find the source of the midnight sound.",
]

SOUNDS = [
    "tick... clink... tick...",
    "click-click, then a tiny whirring hum",
    "a soft tap, pause, and another soft tap",
    "scrape, scrape, followed by a quick springy bounce",
    "a nervous little rattle from behind the shelf",
    "tap-tap-tap, as if someone were knocking from inside a box",
    "a metal chirp that came and went with the wind",
    "one lonely clunk, then a whisper of gears",
]

WARNINGS = [
    '"Don\'t touch anything yet," {hero} said. "Mysteries need careful eyes first."',
    '"Let\'s listen before we reach," {hero} whispered to {friend}.',
    '"If we rush, we might break the clue," {hero} warned.',
    '"Stay by the lantern," {hero} said. "We solve this one step at a time."',
    '"A strange sound is not a reason to grab," {hero} told {friend}.',
    '"We can be brave and cautious at the same time," {hero} said softly.',
    '"First we look, then we ask," {hero} reminded {friend}.',
    '"No poking until we know what we are poking," {hero} said with a small nod.',
]

CLUES = [
    "the dust on the floor was brushed in one little trail toward the music shelf",
    "the sound got louder whenever the old music box leaned against the wall",
    "a round brass key lay nearby, but it had not been wound all the way",
    "the shelf legs were uneven, and one corner of the box kept bumping wood",
    "tiny fresh scratches marked the back of the shelf at the height of the box",
    "the clicks matched the shape of the music box's spring, not a person's footsteps",
    "the lantern light showed a loose spring hook hanging out of the box",
    "a ribbon of dust led from the music box to a gap behind the shelf",
]

TWISTS = [
    "The shopkeeper had not left a burglar in the walls at all; the noise came from a friendly music box that had slipped behind the shelf.",
    "The scary sound was not danger, but a broken little mechanism trying to finish a song all by itself.",
    "What sounded like secret footsteps was only the music box rocking on a loose spring whenever the floorboard trembled.",
    "The mystery twist was simple: the whole shop had been listening to a trapped toy, not a hidden thief.",
    "The midnight clicking did not belong to a stranger; it belonged to the shop's old music box and its stubborn spring.",
    "The strange rattle came from a clockwork toy that had tumbled behind the shelf during the day.",
    "Instead of a burglar, the friends found a box that was trying very hard to wind itself and sing again.",
    "The clue led to a tiny mechanism that was harmless, lonely, and bent out of place behind the shelf.",
]

ENDINGS = [
    "After the box was lifted back onto the table, its song turned into a gentle lullaby, and the shop felt friendly again.",
    "By the time the lantern burned low, the music box was safe on the counter, and the only sound left was a calm tick of the wall clock.",
    "The repaired little mechanism hummed once, then rested, while the friends smiled at the quiet shelves.",
    "Soon the music box played a soft tune, and the old shop looked warm instead of spooky.",
    "When the shelf was fixed and the box was wound, the mystery ended with a sweet little melody.",
    "The last click became a song, and the shopkeeper later found two brave friends and one happy music box.",
    "With the box returned to its place, the midnight noise vanished, leaving only dust, moonlight, and relief.",
    "In the end, the mechanism was only asking for help, and the friends were glad they had listened carefully.",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_place/1.
#show valid_story/2.

setting(clockshop). setting(attic). setting(workshop).
indoor(clockshop). indoor(attic). indoor(workshop).
affords(clockshop,music_box). affords(clockshop,clock). affords(clockshop,spring).
affords(attic,music_box). affords(attic,clock). affords(attic,spring).
affords(workshop,music_box). affords(workshop,clock). affords(workshop,spring).

valid_place(P) :- setting(P), affords(P,music_box), indoor(P).
valid_story(P, friendship) :- valid_place(P).
valid_story(P, cautionary) :- valid_place(P).
valid_story(P, twist) :- valid_place(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_python_valid() -> list[tuple]:
    return sorted((p,) for p, s in SETTINGS.items() if s.indoor and "music_box" in s.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(asp_python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} places).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.place]
    world = StoryState(setting=setting)
    place_name = setting.place

    hero = world.add(Entity(id=params.hero_name, kind="character", type="child", traits=["curious", "brave"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="child", traits=["careful", "loyal"]))
    shopkeeper = world.add(Entity(id="Shopkeeper", kind="character", type="adult", traits=["gentle", "busy"]))

    music_box = world.add(Entity(
        id="music_box",
        kind="thing",
        type="music_box",
        label="music box",
        phrase="a small music box",
        owner=shopkeeper.id,
        caretaker=shopkeeper.id,
        linked_to="spring",
        movable=True,
        noisy=True,
        safe=True,
        meters={"height": 0.12, "width": 0.18},
        memes={"mystery": 0.9},
    ))
    spring = world.add(Entity(
        id="spring",
        kind="thing",
        type="spring",
        label="spring",
        phrase="a loose spring",
        movable=False,
        noisy=False,
        safe=True,
        meters={"length": 0.08},
        memes={"tension": 0.7},
    ))

    opening = OPENINGS[params.opening % len(OPENINGS)].format(hero=hero.id, friend=friend.id, place=place_name)
    sound = SOUNDS[params.sound % len(SOUNDS)]
    warning = WARNINGS[params.warning % len(WARNINGS)].format(hero=hero.id, friend=friend.id)
    clue = CLUES[params.clue % len(CLUES)]
    twist = TWISTS[params.twist % len(TWISTS)]
    ending = ENDINGS[params.ending % len(ENDINGS)]

    world.say(opening)
    world.say(f"From somewhere inside, they heard {sound}.")
    world.say(f'"It sounds like a hidden thief," {friend.id} whispered. "{hero.id}, do you hear it too?"')
    world.say(f'"I hear it," {hero.id} said. "But we should not jump to a guess."')

    world.para()
    world.say(warning)
    world.say(f"Their lantern made a small circle of light, and {clue}.")
    world.say(f'{friend.id} pointed. "{That if False else ""}"')
    # Replace the accidental placeholder-like structure with story text driven by world facts.
    world.paragraphs[-1][-1] = f'{friend.id} pointed. "That clue leads to the shelf, not the street."'
    world.say(f'{hero.id} knelt without touching the box. "Let\'s listen one more time."')
    world.say(f'"Yes," said {friend.id}, "slowly is safer than sorry."')

    world.para()
    world.say(twist)
    world.say(f"The friends looked behind the shelf and found the music box wedged near {spring.phrase}.")
    world.say(f'"No burglar," {hero.id} breathed. "{friend.id}, it was only this tiny mechanism."')
    world.say(f'"A noisy one," {friend.id} said, "but not a bad one."')

    world.para()
    world.say(f"Together, they asked the shopkeeper for help. {shopkeeper.id} smiled and said, \"You did the right thing by waiting.\"")
    world.say("They used a wooden spoon to slide the box out gently, then wound it only a little so it would not strain the spring.")
    world.say(f'The shopkeeper added, "When a mystery has a small mechanism inside it, careful hands make the best answer."')
    world.say(ending)
    world.say(f'{hero.id} and {friend.id} left hand in hand, proud that friendship and caution had solved the riddle.')

    world.facts.update(
        hero=hero,
        friend=friend,
        shopkeeper=shopkeeper,
        music_box=music_box,
        spring=spring,
        place=place_name,
        opening=opening,
        sound=sound,
        warning=warning,
        clue=clue,
        twist=twist,
        ending=ending,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly mystery set in {f['place']} with a strange mechanism and a friendly twist.",
        f"Tell a friendship story where {f['hero'].id} and {f['friend'].id} solve a cautious midnight mystery.",
        "Include dialogue, careful listening, and an ending that reveals the sound was harmless.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who solved the mystery together?",
            answer=f"{f['hero'].id} and {f['friend'].id} solved it together by listening carefully and staying friends.",
        ),
        QAItem(
            question="What made the sound in the shop?",
            answer=f"The sound came from {f['music_box'].phrase}, which was trapped near {f['spring'].phrase}.",
        ),
        QAItem(
            question="Why did they act cautiously?",
            answer="They acted cautiously because the noise sounded strange, and they wanted to avoid breaking the clue or making a mistake.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that there was no burglar at all; the mystery was just {f['music_box'].phrase} moving on a loose spring.",
        ),
        QAItem(
            question="How did the ending show the problem was solved?",
            answer=f"{f['ending']} That ending proves the shop was calm again.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, click, or function.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and avoiding unnecessary risk.",
        ),
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story where characters notice clues, ask questions, and find an answer to something puzzling.",
        ),
    ]


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


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.linked_to:
            bits.append(f"linked_to={e.linked_to}")
        if e.noisy:
            bits.append("noisy=True")
        if e.safe:
            bits.append("safe=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        friend_name=friend_name,
        opening=rng.randrange(len(OPENINGS)),
        sound=rng.randrange(len(SOUNDS)),
        warning=rng.randrange(len(WARNINGS)),
        clue=rng.randrange(len(CLUES)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with friendship, caution, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid()
        print(f"{len(model)} valid combinations:\n")
        for item in model:
            print("  ", item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, hero_name="Mara", friend_name="Jo")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
