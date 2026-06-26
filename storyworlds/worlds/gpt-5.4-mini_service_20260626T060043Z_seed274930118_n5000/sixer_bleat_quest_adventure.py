#!/usr/bin/env python3
"""
A small adventure storyworld about a quest, a sixer, and a bleat.

The seed words are worked into the simulated domain:
- sixer: a tiny six-piece trail compass used on the quest
- bleat: the goat-call that helps the hero listen for clues
- Quest: the central premise
- Adventure: the story style

This script follows the Storyweavers storyworld contract.
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    detail: str


@dataclass
class Quest:
    id: str
    title: str
    verb: str
    goal: str
    clue: str
    obstacle: str
    resolution: str
    sound: str = "bleat"
    feature: str = "Quest"


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, quest: Quest):
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "harbor": Place("harbor", "the harbor", "Tall ropes swayed beside old wooden docks."),
    "forest": Place("forest", "the forest", "Pine trees leaned over a narrow path."),
    "ruins": Place("ruins", "the stone ruins", "Broken arches stood like a sleeping castle."),
    "meadow": Place("meadow", "the windy meadow", "Soft grass rolled under a bright sky."),
}

QUESTS = {
    "sixer": Quest(
        id="sixer",
        title="The Sixer Compass Quest",
        verb="follow",
        goal="find the hidden trail gate",
        clue="a sixer that points the right way",
        obstacle="a wrong turn at the fork",
        resolution="the sixer clicked and led the way home",
        sound="bleat",
        feature="Quest",
    ),
    "bleat": Quest(
        id="bleat",
        title="The Bleat Beacon Quest",
        verb="listen for",
        goal="reach the hill where the lantern waits",
        clue="a bleat echoing through the rocks",
        obstacle="a gust that tried to hide the sound",
        resolution="the bleat stayed steady and brought them to the hill",
        sound="bleat",
        feature="Quest",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Tara", "Jasper", "Lena", "Owen", "Pia", "Rafi"]
GUIDE_NAMES = ["Bram", "Nell", "Sora", "Pip", "Gus", "Mara"]
TRAITS = ["curious", "bold", "quick", "careful", "cheerful", "brave"]


# ---------------------------------------------------------------------------
# World construction
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    world = World(place, quest)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        memes={"hope": 1.0, "wonder": 1.0},
    ))
    guide = world.add(Entity(
        id=params.guide_name,
        kind="character",
        type=params.guide_type,
        label=params.guide_name,
        memes={"calm": 1.0},
    ))
    sixer = world.add(Entity(
        id="sixer",
        kind="thing",
        type="tool",
        label="sixer",
        phrase="a small six-piece compass with bright arrows",
        owner=hero.id,
        carried_by=hero.id,
        hidden=False,
        meters={"shine": 1.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="treasure",
        label="lantern",
        phrase="a little lantern with a gold handle",
        hidden=True,
        owner=None,
    ))

    world.facts.update(
        hero=hero,
        guide=guide,
        sixer=sixer,
        lantern=lantern,
        quest=quest,
        place=place,
    )

    world.say(f"{hero.id} was a {TRAITS[0]} little adventurer who loved a Quest.")
    world.say(
        f"One day, {guide.id} showed {hero.pronoun('object')} the {quest.title.lower()}, "
        f"and {hero.id} tucked the sixer into {hero.pronoun('possessive')} pocket."
    )
    world.say(
        f"Their goal was to {quest.goal}, and the sixer was the one thing that could "
        f"help them keep the trail straight."
    )

    world.para()
    world.say(f"They set off through {place.label}. {place.detail}")
    world.say(f"At first, everything felt lively and open, like the start of a true Adventure.")
    world.say(f"Then they heard a soft {quest.sound} from far ahead.")
    world.say(f"{hero.id} paused, because {quest.clue} sounded like the kind of clue that mattered.")

    world.para()
    world.say(
        f"But soon they met {quest.obstacle}, and the path split around a tangle of roots."
    )
    guide.memes["concern"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"{guide.id} listened closely and said the sound was still there, just hidden by the wind."
    )
    world.say(
        f"{hero.id} held the sixer up, and its tiny arrows twitched as if they knew the secret."
    )

    world.para()
    world.say(
        f"{hero.id} followed the sixer’s turn, stepped over the roots, and found the narrow path."
    )
    world.say(
        f"At the end of it, the lantern waited where the stones made a little pocket of light."
    )
    lantern.hidden = False
    hero.memes["joy"] = 2.0
    guide.memes["pride"] = 1.0
    world.say(
        f"The sixer clicked once, and {quest.resolution}."
    )
    world.say(
        f"{hero.id} smiled at {guide.id}, because the Quest had turned into a real Adventure, "
        f"and the sound of bleat felt like a friendly promise instead of a mystery."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short Adventure story about a child named {hero.id} on a Quest with a sixer and a bleat.',
        f"Tell a gentle quest story where {hero.id} uses the sixer to solve a problem on the trail.",
        f"Write a child-facing adventure that includes the word '{quest.sound}' and ends with a clear discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    quest = f["quest"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {place.label}?",
            answer=f"{hero.id} was trying to {quest.verb} the trail and {quest.goal}.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep on the right path?",
            answer=f"The sixer helped {hero.id} keep on the right path because its tiny arrows pointed the way.",
        ),
        QAItem(
            question=f"Who went with {hero.id} on the Quest?",
            answer=f"{guide.id} went with {hero.id} and listened for the bleat in the distance.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the hidden lantern was found, the sixer had led them safely, and the Quest felt like a real Adventure finished well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compass for?",
            answer="A compass helps you know which way to go so you can keep on the right path.",
        ),
        QAItem(
            question="What sound does a goat make?",
            answer="A goat can make a bleat, which is a small, airy call.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, solve something, or reach a goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(harbor). place(forest). place(ruins). place(meadow).
quest(sixer). quest(bleat).
feature(quest).

compatible(P, Q) :- place(P), quest(Q).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    lines.append(asp.fact("feature", "quest"))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def reasonableness_gate(place: str, quest: str) -> bool:
    return place in PLACES and quest in QUESTS


def asp_verify() -> int:
    py = {(p, q) for p in PLACES for q in QUESTS if reasonableness_gate(p, q)}
    asp_set = set(asp_valid_pairs())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Adventure storyworld with a Quest, a sixer, and a bleat.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
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
    quest = args.quest or rng.choice(list(QUESTS))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    guide_type = args.guide_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    guide_name = args.guide or rng.choice(GUIDE_NAMES)
    if not reasonableness_gate(place, quest):
        raise StoryError("No valid combination matches the given options.")
    if hero_name == guide_name:
        raise StoryError("Hero and guide must be different characters.")
    return StoryParams(
        place=place,
        quest=quest,
        hero_name=hero_name,
        hero_type=hero_type,
        guide_name=guide_name,
        guide_type=guide_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        for p, q in pairs:
            print(f"{p} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for quest in QUESTS:
                p = StoryParams(
                    place=place,
                    quest=quest,
                    hero_name=HERO_NAMES[list(PLACES).index(place) % len(HERO_NAMES)],
                    hero_type="girl",
                    guide_name=GUIDE_NAMES[list(QUESTS).index(quest) % len(GUIDE_NAMES)],
                    guide_type="boy",
                )
                samples.append(generate(p))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
