#!/usr/bin/env python3
"""
storyworlds/worlds/ninetieth_habit_weirdo_laundromat_sound_effects_twist.py
============================================================================

A small story world in a laundromat, shaped like a folk tale: a harmless weirdo,
a long-standing habit, a chain of sound effects, and a twist that lands in humor.

Seed tale premise:
---
In a laundromat beside the sleepy market lane, there was a cheerful little weirdo
named Pip who loved the sounds of washing machines. Every time a washer went
"whirr-whirr" or a dryer went "thump-thump," Pip grinned and tried to echo it
with spoons, buttons, and a tiny drum.

On the ninetieth wash day of Pip's favorite habit, one machine made a strange
"clank-clink-ploof!" sound that did not match any ordinary laundry tune. Pip
followed the noise through the steam and discovered a twist: the "broken" machine
was not broken at all. A clever mouse had climbed inside an empty sock and was
beating it like a little drum.

Pip laughed, the mouse bowed, and the laundromat became a concert hall of soft
squeaks, spinning shirts, and happy chuckles.

State model:
---
- Physical meters track sound, clutter, steam, and tidy order.
- Emotional memes track curiosity, delight, surprise, embarrassment, and fondness.
- The story is driven by the simulated discovery of the true noise source.
- The ending must prove the twist changed the world: the laundromat is calmer,
  and the hero's habit has become a new, shared game.

ASP twin:
---
The inline ASP rules mirror the Python reasonableness gate:
- a twist is valid only if the laundromat has a machine, a sound cue, and a
  hidden source for the odd noise;
- a helpful reveal is valid only if it lowers confusion and raises delight.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the laundromat"
    indoor: bool = True
    affords: set[str] = field(default_factory=lambda: {"wash", "dry"})


@dataclass
class Twist:
    odd_noise: str
    reveal: str
    hidden_source: str
    sound_word: str
    humor_tag: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    habit: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


def sound_of(setting: Setting) -> str:
    return "whirr-whirr, ching-ching" if setting.indoor else "drip-drip, whirr-whirr"


SETTING = Setting()

TWISTS = {
    "mouse_sock_drum": Twist(
        odd_noise="clank-clink-ploof",
        reveal="a mouse had climbed inside an empty sock and was drumming on it like a tiny kettle drum",
        hidden_source="mouse",
        sound_word="clank-clink-ploof",
        humor_tag="sock drum",
    ),
    "coin_in_pocket": Twist(
        odd_noise="jingle-jangle-bonk",
        reveal="an old coin had slipped into a coat pocket and was dancing against the metal washer door",
        hidden_source="coin",
        sound_word="jingle-jangle-bonk",
        humor_tag="pocket bell",
    ),
    "spinning_button": Twist(
        odd_noise="bip-bip-brrr",
        reveal="a bright button had fallen into the dryer and was making a merry little click with every spin",
        hidden_source="button",
        sound_word="bip-bip-brrr",
        humor_tag="button ping",
    ),
}


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"sound": 0.0},
        memes={"curiosity": 1.0, "delight": 0.0, "surprise": 0.0, "fondness": 0.0, "embarrassment": 0.0},
    ))
    washer = world.add(Entity(id="washer", label="the washer", type="machine", meters={"sound": 0.0}))
    dryer = world.add(Entity(id="dryer", label="the dryer", type="machine", meters={"sound": 0.0}))
    sock = world.add(Entity(id="sock", label="an empty sock", type="sock", plural=False, meters={"clutched": 0.0}))
    mouse = world.add(Entity(id="mouse", label="a clever mouse", type="mouse", meters={"hidden": 1.0}, memes={"cheer": 1.0}))

    twist = TWISTS[params.twist]
    world.facts.update(hero=hero, washer=washer, dryer=dryer, sock=sock, mouse=mouse, twist=twist, params=params)

    # Act 1
    world.say(
        f"In {world.setting.place}, there lived a little weirdo named {hero.id}, "
        f"and {hero.pronoun('possessive')} favorite habit was to listen for the old laundry sounds."
    )
    world.say(
        f"{hero.id} loved the {sound_of(world.setting)} of spinning wheels and swishing shirts, "
        f"and {hero.pronoun()} kept time with {hero.pronoun('possessive')} fingers like a merry clock."
    )
    world.say(
        f"Every wash day, {hero.id} visited the laundromat and whispered the names of the sounds "
        f"as if they were friends."
    )

    # Act 2
    world.para()
    hero.meters["sound"] += 1.0
    washer.meters["sound"] += 1.0
    dryer.meters["sound"] += 1.0
    hero.memes["surprise"] += 1.0

    world.say(
        f"On the ninetieth day of this habit, one machine made a strange {twist.sound_word} "
        f"that did not fit the usual tune."
    )
    world.say(
        f"{hero.id} leaned close, followed the little racket through the steam, and heard it again: "
        f"{twist.odd_noise}."
    )
    world.say(
        f"That sound was so odd that even the buttons seemed to hold their breath."
    )

    # Act 3
    world.para()
    hero.memes["curiosity"] += 1.0
    hero.memes["delight"] += 1.0
    hero.memes["embarrassment"] += 0.5
    mouse.memes["cheer"] += 1.0
    sock.meters["clutched"] += 1.0

    world.say(
        f"Then came the twist: {twist.reveal}."
    )
    world.say(
        f"{hero.id} burst out laughing, because the great mystery was only a tiny musician in a sock."
    )
    world.say(
        f"{hero.id} offered the mouse a safe perch on a warm basket, and together they made a better tune: "
        f"{sound_of(world.setting)} and a soft little squeak-squeak chorus."
    )
    world.say(
        f"By evening, the laundromat was calm again, but now everyone smiled when they heard "
        f"{twist.sound_word}, because it meant a new song had begun."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    twist: Twist = world.facts["twist"]
    return [
        f'Write a folk tale for young children set in a laundromat about a little weirdo with a {params.habit}.',
        f'Tell a humorous story where the ninetieth time becomes special and a strange "{twist.sound_word}" leads to a twist.',
        f'Write a gentle story with sound effects, a hidden surprise, and a happy ending in the laundromat.',
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    twist: Twist = world.facts["twist"]
    hero: Entity = world.facts["hero"]
    return [
        QAItem(
            question=f"Where is the story set?",
            answer="The story is set in a laundromat, where washing machines and dryers make their own music.",
        ),
        QAItem(
            question=f"What was {params.hero_name}'s habit?",
            answer=(
                f"{params.hero_name}'s habit was to listen carefully to the sounds of the laundromat "
                f"and echo them with little rhythmic motions."
            ),
        ),
        QAItem(
            question="Why was the ninetieth day special?",
            answer=(
                "The ninetieth day was special because the familiar laundry sounds were interrupted "
                f"by a strange {twist.sound_word}, which led to the mystery."
            ),
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=(
                f"The twist was that the odd noise was not a broken machine at all; it was {twist.reveal}."
            ),
        ),
        QAItem(
            question=f"How did {params.hero_name} feel at the end?",
            answer=(
                f"{params.hero_name} felt delighted and amused, because the mystery turned into a friendly joke "
                "and the laundromat became a place for a tiny concert."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laundromat?",
            answer="A laundromat is a place where people go to wash and dry clothes in large machines.",
        ),
        QAItem(
            question="Why do machines in a laundromat make sounds?",
            answer="Washing machines and dryers make sounds because they spin, swish, tumble, and move the clothes around.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the listener expects.",
        ),
        QAItem(
            question="Why can humor make a story fun?",
            answer="Humor makes a story fun because it helps people laugh when something surprising or silly happens.",
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this laundromat tale needs a real odd sound, a hidden cause, and a cheerful twist.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "laundromat":
        raise StoryError("(No story: this world is fixed in a laundromat.)")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("(No story: unknown twist.)")
    hero_name = args.name or rng.choice(["Pip", "Moss", "Tilly", "Bram", "Nell"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    habit = args.habit or rng.choice(["counting the chimes", "tapping the baskets", "mimicking the spins"])
    twist = args.twist or rng.choice(list(TWISTS))
    return StoryParams(place="laundromat", hero_name=hero_name, hero_type=hero_type, habit=habit, twist=twist)


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


ASP_RULES = r"""
valid_twist(T) :- twist(T), has_noise(T), has_reveal(T), humorous(T).
good_story(T) :- valid_twist(T), laundromat(laundromat), setting_sound(laundromat).
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("laundromat", "laundromat"))
    lines.append(asp.fact("setting_sound", "laundromat"))
    for k, t in TWISTS.items():
        lines.append(asp.fact("twist", k))
        lines.append(asp.fact("has_noise", k))
        lines.append(asp.fact("has_reveal", k))
        lines.append(asp.fact("humorous", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_twist/1."))
    clingo_set = set(asp.atoms(model, "valid_twist"))
    python_set = {(k,) for k in TWISTS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python twist registry ({len(clingo_set)} twists).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A laundromat folk tale with sound effects, a twist, and humor.")
    ap.add_argument("--place", choices=["laundromat"])
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--habit")
    ap.add_argument("--twist", choices=list(TWISTS))
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


CURATED = [
    StoryParams(place="laundromat", hero_name="Pip", hero_type="boy", habit="counting the chimes", twist="mouse_sock_drum"),
    StoryParams(place="laundromat", hero_name="Tilly", hero_type="girl", habit="tapping the baskets", twist="coin_in_pocket"),
    StoryParams(place="laundromat", hero_name="Bram", hero_type="boy", habit="mimicking the spins", twist="spinning_button"),
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
        print(asp_program("#show valid_twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_twist/1."))
        rows = sorted(set(asp.atoms(model, "valid_twist")))
        print(f"{len(rows)} twists:")
        for (tw,) in rows:
            print(f"  {tw}")
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.habit} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
