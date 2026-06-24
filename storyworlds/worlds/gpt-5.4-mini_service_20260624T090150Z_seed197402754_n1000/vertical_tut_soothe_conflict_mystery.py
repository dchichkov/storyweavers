#!/usr/bin/env python3
"""
Storyworld: vertical_tut_soothe_conflict_mystery

A small, child-facing mystery world about a strange vertical sound, a rising
search, a brief conflict, and a soothing reveal.

Seed tale used to design the world:
---
A child and a parent hear a strange tut-tut sound from somewhere above them.
They look up a tall staircase, feel a little worried, and have a small conflict
about whether to climb. The parent soothes the child, they go up together, and
they discover the sound was just a loose weather vane tapping in the wind.
---

The world is built around:
- a vertical place with an upward path
- a mysterious "tut-tut" sound
- a conflict beat that must be soothed
- a resolution that explains the sound

The story is generated from simulated state rather than fixed prose.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    vertical: bool = True
    levels: int = 0
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    sound: str
    source: str
    clue: str
    reveal: str
    height: str
    keyword: str = "vertical"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "lighthouse": Setting(place="the lighthouse", vertical=True, levels=4, affords={"stairs", "wind"}),
    "tower": Setting(place="the old tower", vertical=True, levels=5, affords={"stairs", "wind"}),
    "museum": Setting(place="the museum staircase", vertical=True, levels=3, affords={"stairs", "wind"}),
}

MYSTERIES = {
    "weather_vane": Mystery(
        sound="tut-tut",
        source="a loose weather vane",
        clue="a tiny metal tap from the roof",
        reveal="the vane was knocking softly in the wind",
        height="up near the top",
        keyword="vertical",
    ),
    "window_shutter": Mystery(
        sound="tut-tut",
        source="a window shutter",
        clue="a light wooden tick from above",
        reveal="the shutter was bumping the wall each time the breeze rose",
        height="up on a higher landing",
        keyword="vertical",
    ),
    "hanging_sign": Mystery(
        sound="tut-tut",
        source="a hanging sign",
        clue="a little rhythm from the stair rail",
        reveal="the sign was tapping the post whenever the air moved",
        height="on the next level up",
        keyword="vertical",
    ),
}

NAMES = ["Mia", "Noah", "Lily", "Eli", "Ava", "Theo", "Maya", "Finn"]
PARENTS = ["mother", "father", "mom", "dad"]
TRAITS = ["curious", "gentle", "brave", "quiet", "careful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A vertical mystery with a soothing resolution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place in SETTINGS for mid in MYSTERIES]


CURATED = [
    StoryParams(place="lighthouse", mystery="weather_vane", name="Mia", parent="mother"),
    StoryParams(place="tower", mystery="window_shutter", name="Noah", parent="father"),
    StoryParams(place="museum", mystery="hanging_sign", name="Ava", parent="mom"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.mystery and (args.place, args.mystery) not in combos:
        raise StoryError("That place and mystery do not fit this vertical storyworld.")
    picks = [(p, m) for p, m in combos if (args.place is None or p == args.place) and (args.mystery is None or m == args.mystery)]
    if not picks:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(picks))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, mystery=mystery, name=name, parent=parent)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Mystery]:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mia", "Lily", "Ava", "Maya"} else "boy"))
    parent_type = {"mom": "mother", "dad": "father"}.get(params.parent, params.parent)
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=params.parent))
    mystery = MYSTERIES[params.mystery]
    object_ent = world.add(Entity(
        id="clue",
        type="thing",
        label=mystery.source,
        phrase=mystery.source,
        location="upstairs",
    ))
    world.facts.update(hero=hero, parent=parent, mystery=mystery, object_ent=object_ent)
    return world, hero, parent, object_ent, mystery


def _move_up(world: World, hero: Entity, parent: Entity, mystery: Mystery) -> None:
    hero.meters["up"] = hero.meters.get("up", 0) + 1
    parent.meters["up"] = parent.meters.get("up", 0) + 1
    world.say(f"They started up the stairs, one careful step at a time, because the sound seemed to float {mystery.height}.")


def _tension(world: World, hero: Entity, parent: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(f'{hero.id} heard the {mystery.sound} again and frowned. "{mystery.sound}! Something up there is making that noise."')
    world.say(f"{hero.id} wanted to rush, but {hero.pronoun('possessive')} {parent.label} asked {hero.pronoun('object')} to slow down.")


def _soothe(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["soothed"] = hero.memes.get("soothed", 0) + 1
    hero.memes["conflict"] = 0
    hero.memes["worry"] = max(0, hero.memes.get("worry", 0) - 1)
    world.say(f"{parent.label.capitalize()} spoke softly and let the hand in {hero.pronoun('possessive')} hand feel warm and safe.")
    world.say(f'"Let’s look together," {parent.label} said. "No need to be scared."')


def _reveal(world: World, hero: Entity, parent: Entity, mystery: Mystery) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(f"At the top, they found the answer: {mystery.reveal}.")
    world.say(f"The little mystery was not a problem after all. It was only {mystery.source}, and the wind kept tapping it with its tiny fingers.")
    world.say(f"{hero.id} smiled, and the stairs felt less tall now that the secret was known.")


def tell_story(params: StoryParams) -> World:
    world, hero, parent, obj, mystery = _setup_world(params)
    world.say(f"{hero.id} was a {random.choice(TRAITS)} child who lived near {world.setting.place}.")
    world.say(f"One quiet afternoon, {hero.id} heard a strange {mystery.sound} coming from somewhere above.")
    world.say(f"It sounded like a mystery tucked inside the {mystery.keyword} stairs.")

    world.para()
    _move_up(world, hero, parent, mystery)
    _tension(world, hero, parent, mystery)
    world.say(f"{hero.id} pointed toward the ceiling and whispered that the sound felt odd and a little scary.")

    world.para()
    _soothe(world, hero, parent)
    _move_up(world, hero, parent, mystery)
    _reveal(world, hero, parent, mystery)

    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    mystery = f["mystery"]
    return [
        f'Write a short mystery story for a young child about a {mystery.keyword} place and a strange "{mystery.sound}" sound.',
        f"Tell a gentle story where {hero.id} and {parent.label} hear a noisy clue, have a small conflict, and soothe it before finding the answer.",
        f"Write a child-friendly mystery that climbs upward, includes the word '{mystery.keyword}', and ends with a calm reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What strange sound did {hero.id} hear in {world.setting.place}?",
            answer=f"{hero.id} heard a {mystery.sound} sound coming from above in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried before they reached the top?",
            answer=f"{hero.id} felt worried because the {mystery.sound} sound came from somewhere above, so it seemed like a mystery.",
        ),
        QAItem(
            question=f"How did {parent.label} help {hero.id} feel better?",
            answer=f"{parent.label.capitalize()} spoke softly, held {hero.id}'s hand, and soothed the conflict so they could look together.",
        ),
        QAItem(
            question=f"What did they discover at the end?",
            answer=f"They discovered that {mystery.reveal}.",
        ),
    ]


KNOWLEDGE = {
    "vertical": [
        ("What does vertical mean?", "Vertical means going up and down, like a tall ladder or a steep staircase."),
    ],
    "tut": [
        ("What does a tut-tut sound like?", "A tut-tut sound is a tiny tapping or ticking noise, often soft and repeated."),
    ],
    "soothe": [
        ("What does it mean to soothe someone?", "To soothe someone means to make them feel calmer, safer, and less worried."),
    ],
    "conflict": [
        ("What is a conflict?", "A conflict is a moment when people want different things or feel upset for a little while."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is something you do not understand yet, so you look for clues until you find the answer."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"vertical", "tut", "soothe", "conflict", "mystery"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- clue_of(M,_).

vertical_place(P) :- setting(P).
tut_sound(M) :- sound_of(M,"tut-tut").

conflict_story(P,M) :- vertical_place(P), tut_sound(M), soothe_needed(P,M).
soothe_needed(P,M) :- vertical_place(P), sound_of(M,"tut-tut").
resolved(P,M) :- conflict_story(P,M), reveal_of(M,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.vertical:
            lines.append(asp.fact("vertical_place", pid))
        lines.append(asp.fact("levels", pid, s.levels))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("sound_of", mid, m.sound))
        lines.append(asp.fact("clue_of", mid, m.clue))
        lines.append(asp.fact("reveal_of", mid, m.reveal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show mystery/1."))
    # not used for parity in this tiny world, but kept for contract completeness
    return sorted(set(asp.atoms(model, "setting")))


def build_sample(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict_story/2. #show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world has a tiny ASP twin, but no alternate combinatorics are exposed here.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
