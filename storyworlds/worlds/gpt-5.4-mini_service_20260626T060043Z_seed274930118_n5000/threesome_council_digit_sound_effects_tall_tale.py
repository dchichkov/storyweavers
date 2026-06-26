#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Tall Tale about a threesome council, a digit,
and sound effects that help the day turn right.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.id.endswith("a"):
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.kind == "character":
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "it", "object": "it", "possessive": "its"}
        return table[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Story params and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    trio: str
    digit: str
    effect: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "riverbend": "the wide riverbend",
    "prairie": "the golden prairie",
    "crossroads": "the windy crossroads",
    "canyon": "the red canyon",
}

TRIOS = {
    "ranchers": ("Old Mose", "June Bell", "Pip"),
    "railfolk": ("Hattie", "Barlow", "Nell"),
    "trailkeepers": ("Mina", "Thorn", "Lark"),
}

DIGITS = {
    "0": "a round zero carved on a gatepost",
    "1": "a lean one painted on a wagon wheel",
    "2": "a curly two stamped on a lantern box",
    "3": "a bright three chalked on a barn door",
    "4": "a sturdy four stitched into a saddle blanket",
    "5": "a quick five tied to a fence rail",
    "6": "a six like a curled-up rope loop",
    "7": "a crooked seven cut into a signboard",
    "8": "an eight like two little moons touching",
    "9": "a proud nine shining on a tin cup",
}

SOUND_EFFECTS = {
    "boing": "boing-boing",
    "clatter": "clatter-clang",
    "whoosh": "whoooosh",
    "whistle": "fweeet",
    "thump": "thump-thump",
    "jingle": "jing-a-ling",
}

NAMES = ["Ruby", "Clem", "Wren", "Mabel", "Otis", "Silas", "Tilda", "Jeb"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(riverbend). place(prairie). place(crossroads). place(canyon).
digit(0..9).

need_council(P) :- place(P).
sound_help(E) :- effect(E).
story_ok(P,D,E) :- need_council(P), digit(D), sound_help(E).
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for d in DIGITS:
        lines.append(asp.fact("digit", int(d)))
    for e in SOUND_EFFECTS:
        lines.append(asp.fact("effect", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = set((p, d, e) for p in PLACES for d in DIGITS for e in SOUND_EFFECTS)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    trio_names = TRIOS[params.trio]
    hero = world.add(Entity(id=params.name, kind="character", label=params.name, traits=["tall-tale"]))
    council = [world.add(Entity(id=n, kind="character", label=n, traits=["council"])) for n in trio_names]
    digit = world.add(Entity(id=f"digit_{params.digit}", kind="thing", label=params.digit, phrase=DIGITS[params.digit]))
    effect = world.add(Entity(id=params.effect, kind="thing", label=SOUND_EFFECTS[params.effect], phrase=params.effect))

    world.facts.update(hero=hero, council=council, digit=digit, effect=effect, params=params)
    return world


def tell_story(world: World) -> World:
    f = world.facts
    hero: Entity = f["hero"]
    council: list[Entity] = f["council"]
    digit: Entity = f["digit"]
    effect: Entity = f["effect"]

    world.say(
        f"{hero.label} came riding into {world.place} where three old hands had formed a council "
        f"under the sky as broad as a barn roof."
    )
    world.say(
        f"They were {council[0].label}, {council[1].label}, and {council[2].label}, and every one of them "
        f"could smell trouble before supper."
    )
    world.say(
        f"On the gatepost sat {digit.phrase}, and every time the wind touched it, it made a lonely "
        f"{effect.phrase} sound, as if the whole country had tucked a tin fiddle inside its coat."
    )

    world.para()
    world.say(
        f"The council scratched their hats, squinted at the mark, and said it was no ordinary digit; "
        f"it was a clue with dust on its boots."
    )
    world.say(
        f"{council[0].label} tapped the post. {effect.label} went {effect.phrase}! "
        f"{council[1].label} stamped a boot. It answered with another {effect.phrase}!"
    )
    world.say(
        f"That told them the digit was stuck fast because a loose latch had jammed the trail box shut."
    )

    world.para()
    world.say(
        f"So the threesome made a plan. {council[2].label} hummed low and slow, "
        f"{council[1].label} lifted the latch, and {council[0].label} called out, "
        f'"Now, one, two, three!"'
    )
    world.say(
        f"At the third word the whole place shook with a grand {effect.phrase}, "
        f"and the box sprang open like a jackrabbit at dawn."
    )
    world.say(
        f"Out rolled the digit at last, bright as a new coin, and the council laughed so hard "
        f"that even the wind sounded cheerful."
    )

    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall-tale story about a threesome council that hears a {f['digit'].label} and uses a sound effect to solve a problem.",
        f"Tell a big-hearted frontier story where {f['hero'].label} joins a council at {world.place} and the sound {f['effect'].phrase} matters.",
        f"Write a short tale with three helpers, a digit, and a noisy clue that leads to a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    council: list[Entity] = f["council"]
    digit: Entity = f["digit"]
    effect: Entity = f["effect"]

    return [
        QAItem(
            question=f"Who came to {world.place} and met the council?",
            answer=f"{hero.label} came to {world.place} and met the threesome council made of {council[0].label}, {council[1].label}, and {council[2].label}."
        ),
        QAItem(
            question=f"What digit was causing trouble in the story?",
            answer=f"The trouble came from {digit.phrase}."
        ),
        QAItem(
            question=f"What sound effect helped the council figure out the clue?",
            answer=f"The council listened to {effect.phrase}, and that sound helped them solve the problem."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The stuck clue was opened, the digit was found, and the council ended up laughing together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a council?",
            answer="A council is a group of people who talk together and make a plan."
        ),
        QAItem(
            question="What is a digit?",
            answer="A digit is one of the numbers from 0 to 9."
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a noise that helps tell a story or makes a moment feel lively."
        ),
    ]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} phrase={e.phrase}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Contract entry points
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale storyworld: a threesome council, a digit, and a sound effect.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--trio", choices=TRIOS.keys())
    ap.add_argument("--digit", choices=DIGITS.keys())
    ap.add_argument("--effect", choices=SOUND_EFFECTS.keys())
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    trio = args.trio or rng.choice(list(TRIOS))
    digit = args.digit or rng.choice(list(DIGITS))
    effect = args.effect or rng.choice(list(SOUND_EFFECTS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, trio=trio, digit=digit, effect=effect, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combinations:")
        for t in triples[:50]:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for trio in TRIOS:
                for digit in DIGITS:
                    for effect in SOUND_EFFECTS:
                        params = StoryParams(place=place, trio=trio, digit=digit, effect=effect, name=NAMES[0])
                        samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
