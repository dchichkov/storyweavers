#!/usr/bin/env python3
"""
storyworlds/worlds/prayer_repetition_fable.py
==============================================

A small fable-like story world about prayer, repetition, patience, and a gentle
change of heart.

The seed premise:
- A young animal wants something quickly.
- An elder advises a repeated prayer before action.
- Repetition steadies the hero, and the ending shows a calmer choice.

The world model tracks physical meters and emotional memes:
- meters: tiredness, hunger, distance, neatness
- memes: restlessness, patience, gratitude, faith, worry, joy

The narration is state-driven: repeated prayer lowers worry and raises patience,
which changes the hero's choice and the ending image.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "owl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "fox", "rabbit", "sparrow"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str = "field"
    affords: set[str] = field(default_factory=set)


@dataclass
class Prayer:
    id: str
    line: str
    repeated_line: str
    calm_gain: float
    worry_loss: float
    faith_gain: float
    keyword: str = "prayer"


@dataclass
class Want:
    id: str
    goal: str
    hurry: str
    risk: str
    gain: str
    keyword: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    elder: str
    want: str
    prayer: str
    seed: Optional[int] = None


PLACES = {
    "field": Place(name="the field", kind="field", affords={"gather", "rest", "walk"}),
    "path": Place(name="the path", kind="path", affords={"walk", "gather"}),
    "hill": Place(name="the hill", kind="hill", affords={"watch", "rest", "walk"}),
}

WANTS = {
    "gather": Want(
        id="gather",
        goal="gather berries",
        hurry="rush to the bushes",
        risk="they might drop the berries and come home empty-pawed",
        gain="a basket of sweet berries",
        keyword="berries",
    ),
    "walk": Want(
        id="walk",
        goal="reach the pond",
        hurry="run down the hill",
        risk="they might stumble and turn the walk into a sore one",
        gain="a calm path and an easy step",
        keyword="pond",
    ),
    "rest": Want(
        id="rest",
        goal="find a soft nest",
        hurry="dash toward the reeds",
        risk="they might miss the quiet place and grow more tired",
        gain="a warm nest and a rested heart",
        keyword="nest",
    ),
    "watch": Want(
        id="watch",
        goal="see the sunrise",
        hurry="climb too fast",
        risk="they might grow winded and miss the first gold light",
        gain="the sunrise and a still breath",
        keyword="sunrise",
    ),
}

PRAYERS = {
    "simple": Prayer(
        id="simple",
        line="the little prayer said once can quiet a busy heart",
        repeated_line="the little prayer said again and again can make a busy heart steady",
        calm_gain=2.0,
        worry_loss=2.0,
        faith_gain=1.0,
    ),
    "thankful": Prayer(
        id="thankful",
        line="we thank the sky, the path, and the hands that help us",
        repeated_line="we thank the sky, the path, and the hands that help us, one quiet breath at a time",
        calm_gain=1.5,
        worry_loss=1.0,
        faith_gain=1.5,
    ),
}

HERO_TYPES = ["rabbit", "mouse", "sparrow", "fox"]
ELDER_TYPES = ["owl", "tortoise", "goat"]


def _m(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _e(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _do_prayer(world: World, hero: Entity, prayer: Prayer, times: int) -> None:
    for i in range(times):
        sig = ("prayer", prayer.id, i)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(hero, "faith", prayer.faith_gain)
        _add_meme(hero, "patience", prayer.calm_gain)
        _add_meme(hero, "worry", -prayer.worry_loss)
        _add_meter(hero, "stillness", 1.0)


def predict_outcome(world: World, hero: Entity, want: Want, prayer: Prayer) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    _add_meme(h, "restlessness", 1.0)
    _add_meter(h, "distance", 1.0)
    _do_prayer(sim, h, prayer, 3)
    return {
        "calm": _e(h, "patience") >= 3.0 and _e(h, "worry") <= 0.0,
        "risk": want.risk,
    }


def tell_story(place: Place, hero_type: str, elder_type: str, want: Want, prayer: Prayer) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="Hero",
        kind="character",
        type=hero_type,
        label=f"the young {hero_type}",
        meters={"distance": 0.0, "tiredness": 0.0, "stillness": 0.0},
        memes={"restlessness": 1.0, "patience": 0.0, "worry": 1.0, "gratitude": 0.0, "faith": 0.0, "joy": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label=f"the old {elder_type}",
        meters={"distance": 0.0},
        memes={"calm": 1.0, "grace": 1.0},
    ))

    world.say(f"Once, a {hero_type} lived near {place.name}, and the little one wanted to {want.goal}.")
    world.say(f"Each morning, {hero.pronoun('subject').capitalize()} felt eager and a little jumpy, for the goal seemed close and very sweet.")
    world.say(f"The old {elder_type} saw this and said, \"{prayer.line.capitalize()}.\"")
    world.para()

    world.say(f"The {hero_type} tried to {want.hurry}, but the wish to hurry made {hero.pronoun('possessive')} paws unsteady.")
    _add_meme(hero, "restlessness", 1.0)
    _add_meter(hero, "distance", 1.0)
    _add_meme(hero, "worry", 1.0)
    world.say(f"{hero.pronoun('subject').capitalize()} almost forgot the elder's words, and that was the trouble.")

    world.para()
    world.say(f"Then the {elder_type} asked for repetition: \"{prayer.repeated_line.capitalize()}.\"")
    _do_prayer(world, hero, prayer, 3)
    world.say(f"So the {hero_type} repeated the prayer three times, softly and carefully, until {hero.pronoun('possessive')} chest felt quieter.")
    world.say(f"With each repeat, hurry slipped away, and patience stood up in its place.")

    calm = _e(hero, "patience")
    worry = _e(hero, "worry")
    if calm >= 3.0 and worry <= 0.0:
        _add_meme(hero, "joy", 2.0)
        _add_meme(hero, "gratitude", 1.0)
        world.say(f"At last, the {hero_type} moved again, but now {hero.pronoun('subject')} walked instead of rushing.")
        world.say(f"{hero.pronoun('subject').capitalize()} found {want.gain}, and it came at the right time because {hero.pronoun('subject')} had become steady enough to notice it.")
        world.say(f"The old {elder_type} smiled, and the little one learned that a prayer said with repetition can make a small heart strong.")
    else:
        world.say(f"The {hero_type} still felt too busy inside, so the elder asked for another round of prayer before any more steps were taken.")
        world.say(f"That gentler waiting was also part of the lesson.")

    world.facts.update(hero=hero, elder=elder, want=want, prayer=prayer, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, want, prayer = f["hero"], f["elder"], f["want"], f["prayer"]
    return [
        f'Write a short fable for children about a {hero.type} who wants to {want.goal}, and an {elder.type} who teaches prayer through repetition.',
        f"Tell a gentle fable where the young {hero.type} hurries, the old {elder.type} suggests a repeated prayer, and calm comes before the next step.",
        f'Write a small animal fable that includes the word "prayer" and shows how saying it again and again can change a rushed heart.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, want, prayer = f["hero"], f["elder"], f["want"], f["prayer"]
    return [
        QAItem(
            question=f"What did the young {hero.type} want in the story?",
            answer=f"The young {hero.type} wanted to {want.goal}.",
        ),
        QAItem(
            question=f"Who taught the {hero.type} to pray by repeating the words?",
            answer=f"The old {elder.type} taught the lesson and told the young {hero.type} to repeat the prayer.",
        ),
        QAItem(
            question="What changed after the prayer was repeated three times?",
            answer="The little heart became steadier, the hurry faded, and the animal chose to walk instead of rushing.",
        ),
        QAItem(
            question=f"Why was the repeated prayer helpful to the {hero.type}?",
            answer=f"It helped because repetition lowered worry and raised patience, so the {hero.type} could think clearly before moving.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prayer?",
            answer="A prayer is words spoken with care to ask, thank, or praise.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying something again and again.",
        ),
        QAItem(
            question="Why can repeating something help a child learn it?",
            answer="Repeating something helps because the mind hears it many times, so it becomes easier to remember and use.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    hero = args.hero or rng.choice(HERO_TYPES)
    elder = args.elder or rng.choice(ELDER_TYPES)
    want_id = args.want or rng.choice(sorted(PLACES[place].affords))
    prayer_id = args.prayer or rng.choice(sorted(PRAYERS))
    if want_id not in WANTS:
        raise StoryError("Unknown want.")
    if prayer_id not in PRAYERS:
        raise StoryError("Unknown prayer.")
    if want_id not in PLACES[place].affords:
        raise StoryError(f"(No story: {PLACES[place].name} does not fit the want to {WANTS[want_id].goal}.)")
    return StoryParams(place=place, hero=hero, elder=elder, want=want_id, prayer=prayer_id)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(PLACES[params.place], params.hero, params.elder, WANTS[params.want], PRAYERS[params.prayer])
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


ASP_RULES = r"""
% A prayer becomes stronger when repeated.
strong_prayer(P) :- prayer(P).

% Repetition reduces worry and increases patience.
calm(H) :- repeated(H, P, N), N >= 3, strong_prayer(P).

% A calm hero avoids rushing.
not_rushing(H) :- calm(H).

% The good ending exists when the hero is calm and not rushing.
good_end(H) :- calm(H), not_rushing(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PRAYERS.items():
        lines.append(asp.fact("prayer", pid))
    for wid, w in WANTS.items():
        lines.append(asp.fact("want", wid))
    for pl in PLACES:
        lines.append(asp.fact("place", pl))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about prayer and repetition.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HERO_TYPES))
    ap.add_argument("--elder", choices=sorted(ELDER_TYPES))
    ap.add_argument("--want", choices=sorted(WANTS))
    ap.add_argument("--prayer", choices=sorted(PRAYERS))
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for want_id in place.affords:
            for prayer_id in PRAYERS:
                for hero in HERO_TYPES:
                    for elder in ELDER_TYPES:
                        combos.append((place_id, hero, elder, want_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    program = asp_program("#show prayer/1.\n#show want/1.\n#show place/1.")
    model = asp.one_model(program)
    return sorted(set(asp.atoms(model, "prayer")))


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    print("OK: ASP twin is present.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show prayer/1.\n#show want/1.\n#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show prayer/1.\n#show want/1.\n#show place/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place_id in sorted(PLACES):
            for want_id in sorted(PLACES[place_id].affords):
                params = StoryParams(
                    place=place_id,
                    hero="rabbit",
                    elder="owl",
                    want=want_id,
                    prayer="simple",
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
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
