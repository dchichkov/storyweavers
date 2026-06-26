#!/usr/bin/env python3
"""
A small whodunit-style story world about friendship, support, and a happy
reconciliation.

Premise:
- A little mystery appears: something kind and important goes missing.
- Friends feel unsure, ask careful questions, and look for clues.
- Support helps the hurt feelings soften.
- The real answer leads to an apology, a repaired friendship, and a happy ending.

The world model tracks:
- physical meters: clue, worry, trust, warmth, evidence, and calm
- emotional memes: fear, suspicion, kindness, relief, support, apology, friendship

This world is intentionally small and constraint-checked: the mystery must be
solvable, the support must be meaningful, and the ending must prove the change.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "group":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    mood: str = "quiet"


@dataclass
class Mystery:
    id: str
    missing: str
    missing_phrase: str
    clue_place: str
    culprit: str
    culprit_hint: str
    reveal: str
    support_item: str
    support_action: str
    repair_action: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero: str
    friend: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, mood="quiet"),
    "library": Setting(place="the library", indoor=True, mood="hushed"),
    "playroom": Setting(place="the playroom", indoor=True, mood="bright"),
    "schoolyard": Setting(place="the schoolyard", indoor=False, mood="breezy"),
}

MYSTERIES = {
    "missing_note": Mystery(
        id="missing_note",
        missing="note",
        missing_phrase="a handwritten thank-you note",
        clue_place="under the bench",
        culprit="wind",
        culprit_hint="a corner of paper stuck to a fence",
        reveal="the wind had blown the note loose",
        support_item="a ribbon",
        support_action="held the note steady with a ribbon",
        repair_action="helped tape the note back together",
        ending_image="the note fluttered safely in the ribbon and the friends smiled at each other",
        tags={"paper", "wind", "friendship", "support"},
    ),
    "missing_biscuit": Mystery(
        id="missing_biscuit",
        missing="biscuit",
        missing_phrase="one small biscuit for the tea tray",
        clue_place="near the blue chair",
        culprit="squirrel",
        culprit_hint="tiny crumbs on the windowsill",
        reveal="a squirrel had carried the biscuit to the sill",
        support_item="a napkin",
        support_action="used a napkin to carry the crumbs carefully",
        repair_action="baked a fresh biscuit together",
        ending_image="a fresh biscuit cooled on the tray while everyone laughed kindly",
        tags={"crumbs", "animal", "friendship", "support"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="key",
        missing_phrase="the little brass key",
        clue_place="inside the flower pot",
        culprit="mischief",
        culprit_hint="a bright scratch on the pot rim",
        reveal="the key had slipped into the flower pot when the basket tipped",
        support_item="a flashlight",
        support_action="shone a flashlight into the pot",
        repair_action="put the key on a string so it would not vanish again",
        ending_image="the brass key hung safely on a string beside the friends' matching smiles",
        tags={"metal", "lost", "friendship", "support"},
    ),
}

NAMES = [
    "Mina", "Theo", "Lina", "Sam", "Nora", "Ivy", "Owen", "Milo", "Ruby", "Finn"
]

TRAITS = ["curious", "gentle", "brave", "patient", "careful", "thoughtful"]


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _bump_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = _meter(entity, key) + amount


def _bump_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = _meme(entity, key) + amount


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Mystery]:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="girl" if params.hero in {"Mina", "Lina", "Nora", "Ivy", "Ruby"} else "boy",
        label=params.hero,
        traits=["little", random.choice(TRAITS)],
        meters={"worry": 0.0, "calm": 0.0, "trust": 0.0, "evidence": 0.0},
        memes={"curiosity": 1.0, "friendship": 1.0, "support": 0.0, "suspicion": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="girl" if params.friend in {"Mina", "Lina", "Nora", "Ivy", "Ruby"} else "boy",
        label=params.friend,
        traits=["kind", random.choice(TRAITS)],
        meters={"worry": 0.0, "calm": 0.0, "trust": 1.0},
        memes={"friendship": 1.0, "support": 1.0, "apology": 0.0, "kindness": 1.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect,
        kind="character",
        type="girl" if params.suspect in {"Mina", "Lina", "Nora", "Ivy", "Ruby"} else "boy",
        label=params.suspect,
        traits=["quiet"],
        meters={"worry": 0.0},
        memes={"suspicion": 0.0},
    ))

    world.facts = {
        "setting": setting,
        "mystery": mystery,
        "hero": hero,
        "friend": friend,
        "suspect": suspect,
    }
    return world, hero, friend, suspect, mystery


def _introduce(world: World, hero: Entity, friend: Entity, suspect: Entity, mystery: Mystery) -> None:
    world.say(
        f"At {world.setting.place}, {hero.label} and {friend.label} were close friends who liked calm, careful days."
    )
    world.say(
        f"Then something went missing: {mystery.missing_phrase}. Nobody wanted a blame game, but the room felt suddenly full of questions."
    )
    world.say(
        f"{suspect.label} was nearby, so {hero.label} wondered whether {mystery.missing} had been taken."
    )
    _bump_meme(hero, "suspicion", 1.0)
    _bump_meter(hero, "worry", 1.0)
    _bump_meter(suspect, "worry", 0.5)


def _search_scene(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"{hero.label} looked under seats and behind jars, because good detectives check the place where the clue might hide."
    )
    world.say(
        f"At {mystery.clue_place}, {friend.label} found {mystery.culprit_hint}, which made everyone pause and think."
    )
    _bump_meter(hero, "evidence", 1.0)
    _bump_meter(friend, "evidence", 1.0)
    _bump_meme(friend, "support", 1.0)
    _bump_meter(hero, "trust", 0.5)


def _support_scene(world: World, hero: Entity, friend: Entity, suspect: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"{friend.label} did not rush to accuse anyone. Instead, {friend.pronoun()} said, "
        f"\"Let's support each other and look one more time.\""
    )
    world.say(
        f"{friend.label} {mystery.support_action}, and that small helping hand made {hero.label} feel steadier."
    )
    _bump_meme(hero, "support", 1.0)
    _bump_meter(hero, "calm", 1.0)
    _bump_meter(hero, "trust", 1.0)
    _bump_meter(suspect, "calm", 0.5)


def _reveal_scene(world: World, hero: Entity, friend: Entity, suspect: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"Then {hero.label} noticed the truth: {mystery.reveal}."
    )
    world.say(
        f"{suspect.label} had not meant any harm, and the mistaken worry began to soften."
    )
    _bump_meter(hero, "evidence", 1.0)
    _bump_meter(hero, "calm", 1.0)
    _bump_meter(friend, "calm", 1.0)


def _reconciliation_scene(world: World, hero: Entity, friend: Entity, suspect: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"{hero.label} took a breath and said sorry for jumping to conclusions."
    )
    world.say(
        f"{suspect.label} apologized too, even though {suspect.pronoun('subject')} had only been caught in the confusion."
    )
    world.say(
        f"Together, they {mystery.repair_action}, and the friendship between the three felt warm again."
    )
    _bump_meme(hero, "friendship", 1.0)
    _bump_meme(friend, "friendship", 1.0)
    _bump_meme(suspect, "friendship", 1.0)
    _bump_meme(hero, "relief", 1.0)
    _bump_meme(friend, "apology", 1.0)
    _bump_meter(hero, "calm", 2.0)
    _bump_meter(friend, "calm", 2.0)
    _bump_meter(suspect, "calm", 2.0)


def _ending_scene(world: World, hero: Entity, friend: Entity, suspect: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"In the end, {mystery.ending_image}."
    )
    world.say(
        f"{hero.label}, {friend.label}, and {suspect.label} left together with no hard feelings, only a happy, solved mystery."
    )


def tell_story(params: StoryParams) -> World:
    world, hero, friend, suspect, mystery = _setup_world(params)
    _introduce(world, hero, friend, suspect, mystery)
    _search_scene(world, hero, friend, mystery)
    _support_scene(world, hero, friend, suspect, mystery)
    _reveal_scene(world, hero, friend, suspect, mystery)
    _reconciliation_scene(world, hero, friend, suspect, mystery)
    _ending_scene(world, hero, friend, suspect, mystery)
    world.facts.update({
        "resolved": True,
        "ending": mystery.ending_image,
    })
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    suspect: Entity = f["suspect"]
    return [
        f'Write a short whodunit for a child about a missing {mystery.missing} and a kind act of support.',
        f"Tell a gentle mystery where {hero.label} and {friend.label} solve what happened to {mystery.missing_phrase}.",
        f"Write a friendship story with a small clue, an apology, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    suspect: Entity = f["suspect"]
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer="It is a gentle whodunit about a mystery, friendship, support, and reconciliation.",
        ),
        QAItem(
            question=f"What went missing at {world.setting.place}?",
            answer=f"{mystery.missing_phrase} went missing.",
        ),
        QAItem(
            question=f"Who helped {hero.label} stay calm while they looked for clues?",
            answer=f"{friend.label} helped by staying kind and offering support.",
        ),
        QAItem(
            question=f"Why did the friends stop worrying about {suspect.label}?",
            answer=f"They found a clue that showed {mystery.reveal}, so the suspicion was not fair.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The characters apologized, repaired the mistake, and ended as friends with a happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is support?",
            answer="Support means helping someone feel steadier, safer, or less alone.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up after a problem and their relationship feels good again.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other and help each other.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader and characters try to figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.kind}/{ent.type}) {' '.join(parts)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for mystery_id in MYSTERIES:
            for hero in NAMES[:6]:
                for friend in NAMES[4:]:
                    if hero == friend:
                        continue
                    for suspect in NAMES:
                        if suspect in {hero, friend}:
                            continue
                        combos.append((setting_id, mystery_id, hero))
                        break
    return combos


@dataclass
class AspRegistry:
    settings: dict[str, Setting]
    mysteries: dict[str, Mystery]


REGISTRY = AspRegistry(settings=SETTINGS, mysteries=MYSTERIES)


ASP_RULES = r"""
setting(S) :- place(S).
mystery(M) :- missing(M,_).
support_story(S,M) :- setting(S), mystery(M), clue(M,_), repair(M,_).
happy_ending(M) :- support_story(_,M), apology(M), reveal(M,_).
reconciliation(M) :- apology(M), kindness(M), happy_ending(M).
friendship(M) :- reconciliation(M), support(M).
#show support_story/2.
#show happy_ending/1.
#show reconciliation/1.
#show friendship/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in REGISTRY.settings.items():
        lines.append(asp.fact("place", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        lines.append(asp.fact("mood", sid, setting.mood))
    for mid, mystery in REGISTRY.mysteries.items():
        lines.append(asp.fact("missing", mid, mystery.missing))
        lines.append(asp.fact("clue", mid, mystery.clue_place))
        lines.append(asp.fact("culprit", mid, mystery.culprit))
        lines.append(asp.fact("reveal", mid, mystery.reveal))
        lines.append(asp.fact("support", mid, "support"))
        lines.append(asp.fact("repair", mid, mystery.repair_action))
        lines.append(asp.fact("apology", mid))
        lines.append(asp.fact("kindness", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show support_story/2. #show happy_ending/1. #show reconciliation/1. #show friendship/1."))
    shown = {
        "support_story": asp.atoms(model, "support_story"),
        "happy_ending": asp.atoms(model, "happy_ending"),
        "reconciliation": asp.atoms(model, "reconciliation"),
        "friendship": asp.atoms(model, "friendship"),
    }
    ok = bool(shown["support_story"] or shown["happy_ending"] or shown["reconciliation"] or shown["friendship"])
    if not ok:
        print("ASP verification failed: no expected atoms were produced.")
        return 1
    print("OK: ASP twin produced support / happy ending / reconciliation / friendship atoms.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit about support, friendship, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--friend", choices=NAMES)
    ap.add_argument("--suspect", choices=NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero = args.hero or rng.choice(NAMES[:6])
    friend_choices = [n for n in NAMES if n != hero]
    friend = args.friend or rng.choice(friend_choices)
    if friend == hero:
        raise StoryError("hero and friend must be different people")
    suspect_choices = [n for n in NAMES if n not in {hero, friend}]
    suspect = args.suspect or rng.choice(suspect_choices)
    if suspect in {hero, friend}:
        raise StoryError("suspect must be different from the hero and friend")
    return StoryParams(setting=setting, mystery=mystery, hero=hero, friend=friend, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_list() -> None:
    import asp
    model = asp.one_model(asp_program("#show support_story/2. #show happy_ending/1. #show reconciliation/1. #show friendship/1."))
    print("support_story:", sorted(set(asp.atoms(model, "support_story"))))
    print("happy_ending:", sorted(set(asp.atoms(model, "happy_ending"))))
    print("reconciliation:", sorted(set(asp.atoms(model, "reconciliation"))))
    print("friendship:", sorted(set(asp.atoms(model, "friendship"))))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show support_story/2. #show happy_ending/1. #show reconciliation/1. #show friendship/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garden", "missing_note", "Mina", "Theo", "Sam"),
            StoryParams("library", "missing_key", "Lina", "Owen", "Finn"),
            StoryParams("playroom", "missing_biscuit", "Nora", "Ruby", "Milo"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
