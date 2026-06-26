#!/usr/bin/env python3
"""
Standalone storyworld: field / grim admission / surprise superhero story.

A child-friendly superhero tale about a brave kid hero, a wide field, a grim
admission, and a surprise that changes the ending.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "hero"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the field"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    keyword: str


@dataclass
class Surprise:
    id: str
    reveal: str
    help_text: str
    result_text: str


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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0


def _inc(d: dict[str, float], key: str, amt: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amt


def _hero_name(kind: str) -> str:
    return kind.capitalize()


def _article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


def _maybe_cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "field": Setting(place="the field", affords={"fly", "race", "signal"}),
}

ACTIONS = {
    "fly": Action(
        id="fly",
        verb="fly low over the field",
        gerund="flying low over the field",
        rush="dash up into the air",
        effect="the wind tugged at everything loose",
        keyword="field",
    ),
    "race": Action(
        id="race",
        verb="race across the field",
        gerund="racing across the field",
        rush="sprint toward the far line",
        effect="the grass flashed under fast boots",
        keyword="field",
    ),
    "signal": Action(
        id="signal",
        verb="send a signal from the field",
        gerund="sending a signal from the field",
        rush="wave the lantern hard",
        effect="the signal could guide the team",
        keyword="signal",
    ),
}

SURPRISES = {
    "helper": Surprise(
        id="helper",
        reveal="a little helper drone popped out of the tall grass",
        help_text="It had a tiny lamp and a speaker for sharing quick messages.",
        result_text="The drone shone a bright path and carried the warning to the team.",
    ),
    "badge": Surprise(
        id="badge",
        reveal="the grim old badge was not broken at all",
        help_text="It only needed a quick wipe, and a hidden button made it sparkle.",
        result_text="The badge flashed like a star and made the whole team cheer.",
    ),
    "signal": Surprise(
        id="signal",
        reveal="the surprise was that the field itself carried the message",
        help_text="A row of bright markers had been waiting in the grass all along.",
        result_text="The markers lit up in order, and the hero's signal reached everyone.",
    ),
}

HEROES = [
    ("Nova", "girl"),
    ("Max", "boy"),
    ("Riley", "girl"),
    ("Theo", "boy"),
    ("Zuri", "girl"),
]

TRAITS = ["brave", "quick", "kind", "bold", "clever"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting affords the chosen action.
valid_story(S, A, R) :- setting(S), affords(S, A), surprise(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for rid in SURPRISES:
        lines.append(asp.fact("surprise", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(setting: Setting, action: Action, surprise: Surprise, hero_name: str, hero_type: str,
         trait: str, sidekick_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name.lower(),
        traits=[trait, "stubborn"],
        meters={"speed": 0.0, "damage": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "hope": 0.0, "surprise": 0.0},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type="hero",
        label=sidekick_name.lower(),
        traits=["helpful"],
        meters={"speed": 0.0},
        memes={"loyalty": 1.0},
    ))
    badge = world.add(Entity(
        id="badge",
        kind="thing",
        type="badge",
        label="badge",
        phrase="the silver badge on the hero belt",
        owner=hero.id,
        caretaker=hero.id,
        worn_by=hero.id,
        meters={"dust": 1.0},
        memes={"value": 1.0},
    ))

    # Act 1: setup
    world.say(
        f"{_hero_name(hero.type)} {hero.id} was a {trait} superhero who watched over {setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved to {action.gerund} because {action.effect}."
    )
    world.say(
        f"On {hero.pronoun('possessive')} belt, {hero.pronoun('possessive')} badge shone like a small moon."
    )

    # Act 2: trouble
    world.para()
    _inc(hero.memes, "worry", 1.0)
    _inc(hero.meters, "speed", 1.0)
    world.say(
        f"One evening, {hero.id} reached the middle of the field and wanted to {action.verb}."
    )
    world.say(
        f"Then {hero.pronoun('possessive')} radio crackled, and {hero.id} heard that something grim had happened."
    )
    world.say(
        f"{hero.id} made a grim admission: the badge had slipped in the grass earlier, and now no one could see it."
    )
    _inc(badge.meters, "dust", 1.0)
    _inc(hero.memes, "shame", 1.0)
    world.say(
        f"That made {hero.id} feel small for a moment, because a superhero is supposed to keep a careful watch."
    )

    # Surprise turn
    world.para()
    _inc(hero.memes, "surprise", 1.0)
    world.say(f"Then came a surprise: {surprise.reveal}.")
    world.say(surprise.help_text)
    world.say(
        f"{sidekick.id} ran up beside {hero.id} and said, \"We can fix this together.\""
    )

    # Resolution
    _inc(hero.memes, "hope", 2.0)
    hero.memes["worry"] = 0.0
    badge.meters["dust"] = 0.0
    world.say(
        f"Together they searched the grass, and the little helper found the lost badge in a bright patch of clover."
    )
    world.say(
        f"{surprise.result_text} Soon {hero.id} could {action.verb} again, and {hero.pronoun('possessive')} badge gleamed clean and safe."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        badge=badge,
        action=action,
        surprise=surprise,
        setting=setting,
        hero_type=hero_type,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    surprise = f["surprise"]
    return [
        f'Write a short superhero story for a young child that takes place in {world.setting.place} and includes the word "field".',
        f"Tell a gentle superhero story where {hero.id} makes a grim admission and then a surprise helps fix the problem.",
        f'Write a child-friendly adventure about {hero.id} who wants to {action.verb} and learns a surprising lesson in the field.',
        f"Make the story feel like a classic superhero story with a brave hero, a worry, and a helpful surprise: {surprise.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    badge = f["badge"]
    action = f["action"]
    surprise = f["surprise"]
    trait = next((t for t in hero.traits if t != "stubborn"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, a {trait} {hero.type} who watches over the field.",
        ),
        QAItem(
            question=f"What grim admission did {hero.id} make?",
            answer=f"{hero.id} admitted that the badge had slipped into the grass and gone missing for a while.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the field?",
            answer=f"{hero.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} after the surprise?",
            answer=f"{sidekick.id} helped, and together they found the lost badge.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The badge was found, the worry faded, and {hero.id} could {action.verb} again.",
        ),
    ]
    if badge.meters.get("dust", 0.0) == 0.0:
        qa.append(QAItem(
            question="Why did the badge matter at the end?",
            answer="It mattered because it was part of the hero's suit, and finding it made the hero feel ready and proud again.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a field?",
            answer="A field is a wide open place with grass where people can run, play, and look far across the ground.",
        ),
        QAItem(
            question="What does grim mean?",
            answer="Grim means serious and worried, like a face that knows something is wrong.",
        ),
        QAItem(
            question="What is an admission?",
            answer="An admission is when someone tells the truth about something, even if it is hard to say.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly changes what is happening.",
        ),
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Contract interface
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    surprise: str
    name: str
    sidekick: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="field", action="signal", surprise="helper", name="Nova", sidekick="Pip", gender="girl", trait="brave"),
    StoryParams(place="field", action="fly", surprise="badge", name="Max", sidekick="Zip", gender="boy", trait="clever"),
    StoryParams(place="field", action="race", surprise="signal", name="Riley", sidekick="Moss", gender="girl", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld in a field.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or "field"
    action = args.action or rng.choice(sorted(SETTINGS[place].affords))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice([n for n, g in HEROES if g == gender])
    sidekick = args.sidekick or rng.choice(["Pip", "Zip", "Moss", "Beam"])
    trait = args.trait or rng.choice(TRAITS)
    if place not in SETTINGS:
        raise StoryError("That place is not available in this storyworld.")
    if action not in SETTINGS[place].affords:
        raise StoryError("That action does not fit the field setting.")
    return StoryParams(place=place, action=action, surprise=surprise, name=name, sidekick=sidekick, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        SURPRISES[params.surprise],
        params.name,
        params.gender,
        params.trait,
        params.sidekick,
    )
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


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = {(p, a, r) for p in SETTINGS for a in SETTINGS[p].affords for r in SURPRISES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
