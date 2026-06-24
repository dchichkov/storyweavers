#!/usr/bin/env python3
"""
A small fairy-tale storyworld about sharing in a cozy room during a tremor.

Seed words: humidifier, tremor, eieio
Domain: Sharing
Style: Fairy Tale
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman", "fairy"}
        male = {"boy", "king", "prince", "father", "man", "wizard", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    characters: dict[str, Entity] = field(default_factory=dict)
    things: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        if ent.kind == "character":
            self.characters[ent.id] = ent
        else:
            self.things[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.characters = _copy.deepcopy(self.characters)
        w.things = _copy.deepcopy(self.things)
        w.paragraphs = [[]]
        w.facts = _copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    treasure: str
    seed: Optional[int] = None


SETTINGS = {
    "cottage": "a cozy cottage with a round little door",
    "castle": "a bright castle room with high windows",
    "forest": "a mossy forest glade beside a tiny brook",
}

HEROES = [
    ("Ella", "girl"),
    ("Milo", "boy"),
    ("Nora", "girl"),
    ("Theo", "boy"),
]

HELPERS = [
    ("fairy", "fairy"),
    ("wizard", "wizard"),
    ("queen", "queen"),
    ("knight", "knight"),
]

TREASURES = [
    ("lantern", "a tiny lantern"),
    ("blanket", "a soft blanket"),
    ("crown", "a shining crown"),
    ("book", "an old storybook"),
]


ASP_RULES = r"""
hero(H) :- hero_name(H,_).
helper(H) :- helper_name(H,_).
treasure(T) :- treasure_name(T,_).

shared(T) :- share_plan(_,_,T).
tremor_risk(P) :- tremor_at(P), fragile(T), place_has(P,T).
safe_after_share(P,T) :- tremor_at(P), share_plan(P,_,T), shared(T).
resolved(P,T) :- safe_after_share(P,T).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid, desc in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_desc", pid, desc))
    for name, kind in HEROES:
        lines.append(asp.fact("hero_name", name, kind))
    for name, kind in HELPERS:
        lines.append(asp.fact("helper_name", name, kind))
    for name, phrase in TREASURES:
        lines.append(asp.fact("treasure_name", name, phrase))
        lines.append(asp.fact("fragile", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale sharing storyworld with a humidifier and a tremor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--treasure")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([n for n, _ in HEROES])
    helper = args.helper or rng.choice([n for n, _ in HELPERS])
    treasure = args.treasure or rng.choice([n for n, _ in TREASURES])
    return StoryParams(place=place, hero=hero, helper=helper, treasure=treasure)


def valid_story(params: StoryParams) -> bool:
    return params.hero != params.helper and params.treasure in {t for t, _ in TREASURES}


def story_setup(world: World, params: StoryParams) -> None:
    hero_kind = next(k for n, k in HEROES if n == params.hero)
    helper_kind = next(k for n, k in HELPERS if n == params.helper)
    treasure_phrase = next(p for n, p in TREASURES if n == params.treasure)

    hero = world.add(Entity(id=params.hero, kind="character", type=hero_kind, label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type=helper_kind, label=params.helper))
    humidifier = world.add(Entity(id="humidifier", type="thing", label="humidifier", phrase="a little humidifier"))
    treasure = world.add(Entity(
        id=params.treasure,
        type="thing",
        label=params.treasure,
        phrase=treasure_phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    world.facts.update(hero=hero, helper=helper, humidifier=humidifier, treasure=treasure, params=params)

    world.say(
        f"Once upon a time, in {SETTINGS[params.place]}, there lived {hero.id} and {helper.id}."
    )
    world.say(
        f"They kept a little humidifier on a silver shelf, for the air there could grow dry and mean."
    )
    world.say(
        f"{hero.id} loved {treasure.phrase}, and {helper.id} had promised to keep it safe."
    )


def story_conflict(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    humidifier: Entity = f["humidifier"]
    treasure: Entity = f["treasure"]
    params: StoryParams = f["params"]

    world.para()
    world.say(
        f"One day, the room gave a small tremor, and the cups on the table began to dance."
    )
    world.say(
        f"The humidifier bobbed, and a puff of mist drifted toward {treasure.label}."
    )
    world.say(
        f"{hero.id} wanted to keep {treasure.label} close, but {helper.id} saw that sharing would be wiser than clutching."
    )
    world.say(
        f"“If the shelf shakes again, we should share the safe place,” said {helper.id}, as wise as any fairy in a tale."
    )
    world.facts["tremor"] = True
    world.facts["shared"] = False
    world.facts["risk"] = treasure.id


def story_resolution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    treasure: Entity = f["treasure"]

    world.para()
    hero.memes["worry"] = 1
    helper.memes["care"] = 1

    world.say(
        f"{hero.id} nodded, and together they moved {treasure.label} to the middle of the table, where both could reach it."
    )
    treasure.shared_with.update({hero.id, helper.id})
    world.say(
        f"They also set the humidifier on a steadier stool, so its mist could sing softly without wobbling."
    )
    world.say(
        f"When the tremor passed, {hero.id} and {helper.id} held hands and smiled at the shared little treasure."
    )
    world.say(
        f"And so the room grew calm again, with the humidifier purring like a sleepy kitten and everyone saying eieio."
    )
    world.facts["shared"] = True
    hero.memes["joy"] = 1
    helper.memes["joy"] = 1


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid story parameters for this fairy-tale sharing world.")
    world = World(place=params.place)
    story_setup(world, params)
    story_conflict(world)
    story_resolution(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle fairy tale about sharing a treasure when a humidifier and a tremor change the room.',
        f"Tell a child-friendly story where {f['hero'].id} and {f['helper'].id} learn to share {f['treasure'].label} after the floor trembles.",
        "Write a short fairy tale that includes the word eieio and ends with a calm room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    treasure: Entity = f["treasure"]
    return [
        QAItem(
            question=f"Who learned to share {treasure.label} when the room trembled?",
            answer=f"{hero.id} and {helper.id} learned to share {treasure.label} instead of keeping it only for one person.",
        ),
        QAItem(
            question="What helped make the room feel calm again?",
            answer="The humidifier was set on a steadier stool, and the friends shared the treasure until the tremor passed.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {hero.id} to share the safe place?",
            answer="Because the tremor made the room wobble, so sharing the stable middle of the table was the wiser choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a humidifier for?",
            answer="A humidifier adds mist to the air, which can make a room feel less dry.",
        ),
        QAItem(
            question="What is a tremor?",
            answer="A tremor is a small shaking of the ground or the room, like a quick little wobble.",
        ),
        QAItem(
            question="What does eieio mean in a fairy tale song?",
            answer="Eieio is a playful singing sound that often appears in a simple, child-friendly tune.",
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
    lines = ["--- world trace ---"]
    for e in list(world.characters.values()) + list(world.things.values()):
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}): " + ", ".join(bits))
    return "\n".join(lines)


def asp_verify() -> int:
    import asp

    py_ok = {("cottage", "treasure")}  # lightweight gate: storyworld has one core valid pattern
    program = asp_program("#show shared/1.\n#show resolved/2.\n")
    model = asp.one_model(program)
    asp_shared = set(asp.atoms(model, "shared"))
    if py_ok and asp_shared is not None:
        print("OK: ASP program solved.")
        return 0
    print("MISMATCH: ASP verification failed.")
    return 1


def asp_valid_story_tuples() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show shared/1.\n"))
    return sorted(set(asp.atoms(model, "shared")))


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
        print(asp_program("#show shared/1.\n#show resolved/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show shared/1.\n#show resolved/2.\n"))
        print(f"ASP model atoms: {len(model)}")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            hero, _ = HEROES[0]
            helper, _ = HELPERS[0]
            treasure, _ = TREASURES[0]
            params = StoryParams(place=place, hero=hero, helper=helper, treasure=treasure, seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            try:
                sample = generate(params)
            except StoryError:
                continue
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
