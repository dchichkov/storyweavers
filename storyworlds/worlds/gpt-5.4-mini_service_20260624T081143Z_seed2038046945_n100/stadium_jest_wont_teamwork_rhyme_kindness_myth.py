#!/usr/bin/env python3
"""
storyworlds/worlds/stadium_jest_wont_teamwork_rhyme_kindness_myth.py
====================================================================

A small myth-style storyworld about a child, a stadium, a jest, and a stubborn
"won't" that softens into teamwork, rhyme, and kindness.

Seed tale:
---
At the old stadium, a young bard kept making a jest when the team could not sing
in time. The others would not join, and the chorus fell apart. Then one friend
showed a kinder way: they split the lines, shared the rhyme, and worked as one.
The jest turned gentle, the won't disappeared, and the stadium rang with a song
that everybody could carry.

The world model tracks:
- physical meters: noise, effort, balance, shine
- emotional memes: pride, hurt, kindness, teamwork, delight, stubbornness

The story is driven by state: a warning, a refusal, a turn toward shared rhyme,
and an ending image proving the change.
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
class Place:
    name: str = "the stadium"
    kind: str = "stadium"
    echo: bool = True


@dataclass
class CastRole:
    id: str
    type: str
    label: str
    vibe: str


@dataclass
class Challenge:
    kind: str
    action: str
    fear: str
    turn: str
    ending: str


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    challenger: str
    challenge: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "plural": v.plural, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        return w


HEROES = [
    CastRole("Ari", "boy", "young bard", "bright"),
    CastRole("Mira", "girl", "young bard", "bright"),
    CastRole("Nilo", "boy", "small singer", "keen"),
    CastRole("Sela", "girl", "small singer", "keen"),
]
HELPERS = [
    CastRole("Toma", "boy", "friend", "kind"),
    CastRole("Lina", "girl", "friend", "kind"),
    CastRole("Pax", "boy", "teammate", "steady"),
    CastRole("Ria", "girl", "teammate", "steady"),
]
CHALLENGERS = [
    CastRole("Crowd", "group", "crowd", "loud"),
    CastRole("Captain", "adult", "captain", "stern"),
    CastRole("Chorus", "group", "chorus", "shy"),
]
CHALLENGES = {
    "rhyme": Challenge("rhyme", "share the rhyme", "the lines would tangle", "split the lines among friends", "the stadium rang with one bright rhyme"),
    "teamwork": Challenge("teamwork", "join the team song", "the song would stay apart", "match the beat together", "the chant became one shared song"),
    "kindness": Challenge("kindness", "answer with kindness", "hurt words would sting", "offer a gentle reply", "the jest turned soft and warm"),
}
PLACES = {"stadium": Place(name="the stadium", kind="stadium", echo=True)}

KNOWLEDGE = {
    "stadium": [("What is a stadium?", "A stadium is a very large place where people gather to watch games or performances.")],
    "jest": [("What is a jest?", "A jest is a playful joke, often said to make people smile or laugh.")],
    "won't": [("What does won't mean?", "\"Won't\" is a short way to say \"will not.\" It means someone refuses or does not agree.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help one another and do a job together.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a pattern where words sound alike at the end.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring to others.")],
}
KNOWLEDGE_ORDER = ["stadium", "jest", "won't", "teamwork", "rhyme", "kindness"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("This storyworld only knows a stadium.")
    if params.challenge not in CHALLENGES:
        raise StoryError("Unknown challenge.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different characters.")


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "stadium"), asp.fact("echoes", "stadium")]
    for k in CHALLENGES:
        lines.append(asp.fact("challenge", k))
    lines.append(asp.fact("word", "jest"))
    lines.append(asp.fact("word", "wont"))
    lines.append(asp.fact("word", "teamwork"))
    lines.append(asp.fact("word", "rhyme"))
    lines.append(asp.fact("word", "kindness"))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(stadium, C) :- challenge(C).
has_story(stadium, C) :- compatible(stadium, C).
#show has_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show has_story/2."))
    return sorted(set(asp.atoms(model, "has_story")))


def asp_verify() -> int:
    py = {("stadium", c) for c in CHALLENGES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} cases).")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic stadium storyworld about jest, won't, teamwork, rhyme, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--challenger")
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
    reasonableness_gate(StoryParams(
        place=args.place or "stadium",
        hero=args.hero or HEROES[0].id,
        helper=args.helper or HELPERS[0].id,
        challenger=args.challenger or CHALLENGERS[0].id,
        challenge=args.challenge or "rhyme",
    ))
    place = args.place or "stadium"
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    hero = args.hero or rng.choice([r.id for r in HEROES])
    helper = args.helper or rng.choice([r.id for r in HELPERS if r.id != hero])
    challenger = args.challenger or rng.choice([r.id for r in CHALLENGERS])
    return StoryParams(place=place, hero=hero, helper=helper, challenger=challenger, challenge=challenge)


def _ramp(world: World, hero: Entity, helper: Entity, challenger: Entity, challenge: Challenge) -> None:
    hero.memes["stubbornness"] = hero.memes.get("stubbornness", 0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0) + 1
    world.say(f"At the old stadium, {hero.id} made a jest while {challenger.label} would not join the song.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {challenge.action}, but the other voices fell out of step.")
    world.say(f"The refusal sounded like won't: a hard little word that made the echo feel cold.")
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(f"Then {helper.id} came near with {helper.label} kindness and a hand ready for teamwork.")


def _turn(world: World, hero: Entity, helper: Entity, challenger: Entity, challenge: Challenge) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["hurt"] = max(0, hero.memes.get("hurt", 0) - 1)
    world.say(f"{helper.id} suggested they {challenge.turn}, one by one, until the whole rhyme could breathe.")
    world.say(f"{hero.id} listened, the jest grew gentler, and the won't began to loosen.")
    challenger.memes["softened"] = 1
    world.say(f"Even {challenger.label} leaned closer, because a kinder beat is hard to ignore.")


def _end(world: World, hero: Entity, helper: Entity, challenger: Entity, challenge: Challenge) -> None:
    world.say(f"In the end, they kept their promise and the {world.place.kind} glowed with shared rhyme.")
    world.say(f"{hero.id} was no longer alone in the song; {helper.id} and the others stood with {hero.pronoun('object')}.")
    world.say(f"The final image was simple: teamwork on stone seats, kindness in the air, and a jest that had learned to smile.")


def generate_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero_cfg = next(r for r in HEROES if r.id == params.hero)
    helper_cfg = next(r for r in HELPERS if r.id == params.helper)
    chal_cfg = next(r for r in CHALLENGERS if r.id == params.challenger)
    challenge = CHALLENGES[params.challenge]

    hero = world.add(Entity(hero_cfg.id, "character", hero_cfg.type, hero_cfg.label, False, {"effort": 0, "balance": 0}, {"pride": 0, "hurt": 0, "kindness": 0, "teamwork": 0}))
    helper = world.add(Entity(helper_cfg.id, "character", helper_cfg.type, helper_cfg.label, False, {"effort": 0}, {"kindness": 0, "teamwork": 0}))
    challenger = world.add(Entity(chal_cfg.id, "character", chal_cfg.type, chal_cfg.label, False, {"noise": 0}, {"sternness": 1}))

    world.facts.update(hero=hero, helper=helper, challenger=challenger, challenge=challenge)
    _ramp(world, hero, helper, challenger, challenge)
    world.say("")
    _turn(world, hero, helper, challenger, challenge)
    world.say("")
    _end(world, hero, helper, challenger, challenge)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a myth-like story set in a stadium where a jest and a stubborn won\'t become teamwork.',
        f"Tell a child-facing tale about {f['hero'].id}, {f['helper'].id}, and a shared rhyme that softens a refusal.",
        'Make the story sound ancient and kind, but keep it concrete and clear for a young child.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, challenger, challenge = f["hero"], f["helper"], f["challenger"], f["challenge"]
    return [
        QAItem(question=f"Where did {hero.id} tell the jest?", answer=f"{hero.id} told the jest at the stadium, where voices could echo and carry."),
        QAItem(question=f"What made the won't begin to loosen?", answer=f"It loosened when {helper.id} arrived with kindness and asked for teamwork."),
        QAItem(question=f"What did they share in the turn of the story?", answer=f"They shared the rhyme, splitting it up so everyone could help carry the song."),
        QAItem(question=f"Who finally leaned closer to the song?", answer=f"Even {challenger.label} leaned closer once the beat became kinder and easier to join."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        q, a = KNOWLEDGE[tag][0]
        out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- trace ---"]
    for e in world.entities.values():
        bits.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams("stadium", "Ari", "Toma", "Crowd", "rhyme"),
    StoryParams("stadium", "Mira", "Lina", "Captain", "kindness"),
    StoryParams("stadium", "Nilo", "Pax", "Chorus", "teamwork"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show has_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible cases:", asp_valid())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
