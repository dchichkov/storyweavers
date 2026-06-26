#!/usr/bin/env python3
"""
A small storyworld about a growing art mystery: a child artist notices that a
secret mural keeps changing, speaks with a few helpers, and discovers that a
reconciliation and a shared painting turn the puzzle into a happy ending.

Style note: the stories lean mystery-like in tone, with clues, careful looking,
and a final reveal that resolves the tension through dialogue.
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
    id: str
    label: str
    indoors: bool = False
    surfaces: list[str] = field(default_factory=list)
    feels: list[str] = field(default_factory=list)


@dataclass
class Character:
    id: str
    name: str
    role: str
    trait: str
    age_word: str = "little"
    meters: dict[str, float] = field(default_factory=lambda: {"growth": 0.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "hope": 0.0, "warmth": 0.0, "hurt": 0.0, "peace": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Artifact:
    id: str
    label: str
    kind: str
    value: str
    hidden: bool = False
    grown: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"touched": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"significance": 0.0})


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.characters: dict[str, Character] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add_character(self, c: Character) -> Character:
        self.characters[c.id] = c
        return c

    def add_artifact(self, a: Artifact) -> Artifact:
        self.artifacts[a.id] = a
        return a

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def para(self) -> None:
        if self.events and self.events[-1] != "":
            self.events.append("")

    def render(self) -> str:
        paras = []
        chunk = []
        for line in self.events:
            if line == "":
                if chunk:
                    paras.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            paras.append(" ".join(chunk))
        return "\n\n".join(paras)


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    rival: str
    seed: Optional[int] = None


PLACES = {
    "studio": Place(
        id="studio",
        label="the art studio",
        indoors=True,
        surfaces=["easel", "jar", "cloth"],
        feels=["quiet", "paint-sweet", "careful"],
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the glass greenhouse",
        indoors=True,
        surfaces=["bench", "window", "pot"],
        feels=["glowy", "humid", "mysterious"],
    ),
    "wall": Place(
        id="wall",
        label="the old brick wall",
        indoors=False,
        surfaces=["brick", "chalk mark", "ledge"],
        feels=["windy", "echoing", "secret"],
    ),
}

HEROES = [
    ("Mina", "painter", "thoughtful"),
    ("Tari", "artist", "curious"),
    ("Lena", "art-ist", "gentle"),
    ("Noah", "mural maker", "careful"),
]

FRIENDS = [
    ("June", "neighbor", "kind"),
    ("Pip", "helper", "brave"),
    ("Oren", "classmate", "patient"),
]

RIVALS = [
    ("Moss", "watcher", "stern"),
    ("Iris", "skeptic", "sharp"),
    ("Bea", "guard", "fussy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery-style storyworld about growth, art, dialogue, and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--rival")
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
    place = args.place or rng.choice(list(PLACES))
    if args.hero:
        hero = args.hero
    else:
        hero = rng.choice(HEROES)[0]
    if args.friend:
        friend = args.friend
    else:
        friend = rng.choice([x[0] for x in FRIENDS if x[0] != hero])
    if args.rival:
        rival = args.rival
    else:
        rival = rng.choice([x[0] for x in RIVALS if x[0] not in {hero, friend}])
    if len({hero, friend, rival}) < 3:
        raise StoryError("Choose three different names for the hero, friend, and rival.")
    return StoryParams(place=place, hero=hero, friend=friend, rival=rival)


def _pick_meta(name: str, options: list[tuple[str, str, str]], rng: random.Random) -> tuple[str, str]:
    for n, role, trait in options:
        if n == name:
            return role, trait
    n, role, trait = rng.choice(options)
    return role, trait


def _hero_profile(name: str, rng: random.Random) -> tuple[str, str]:
    return _pick_meta(name, HEROES, rng)


def _friend_profile(name: str, rng: random.Random) -> tuple[str, str]:
    return _pick_meta(name, FRIENDS, rng)


def _rival_profile(name: str, rng: random.Random) -> tuple[str, str]:
    return _pick_meta(name, RIVALS, rng)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed or 0)
    place = PLACES[params.place]
    world = World(place)

    hero_role, hero_trait = _hero_profile(params.hero, rng)
    friend_role, friend_trait = _friend_profile(params.friend, rng)
    rival_role, rival_trait = _rival_profile(params.rival, rng)

    hero = world.add_character(Character(id="hero", name=params.hero, role=hero_role, trait=hero_trait))
    friend = world.add_character(Character(id="friend", name=params.friend, role=friend_role, trait=friend_trait))
    rival = world.add_character(Character(id="rival", name=params.rival, role=rival_role, trait=rival_trait))

    mural = world.add_artifact(Artifact(id="mural", label="the mural", kind="art", value="a painted scene of a small door hidden in vines"))
    clue_note = world.add_artifact(Artifact(id="note", label="the folded note", kind="clue", value="paint here after the rain", hidden=True))
    seedling = world.add_artifact(Artifact(id="seedling", label="the tiny seedling", kind="growth", value="a green sprout with two shy leaves", grown=False, hidden=False))

    hero.memes["curiosity"] += 1
    friend.memes["hope"] += 1
    rival.memes["worry"] += 1

    world.say(
        f"{hero.name} was a {hero.age_word} {hero.trait} {hero.role} who loved looking for clues in {place.label}."
    )
    world.say(
        f"One morning, {hero.name} found {mural.label} changing a little each day, as if someone invisible were adding a new brushstroke."
    )
    world.say(
        f"Beside the paint tray sat {seedling.label}, and its leaves were growing toward the light."
    )
    world.para()
    world.say(
        f"{hero.name} leaned closer and whispered, 'Did you move this painting?'"
    )
    world.say(
        f"{rival.name} folded {rival.pronoun('possessive')} arms. '{hero.name} keeps asking questions,' {rival.name} said. 'Maybe the wall should stay as it is.'"
    )
    hero.memes["worry"] += 1
    rival.memes["hurt"] += 1
    world.say(
        f"{friend.name} stepped in gently. 'Let's talk before we guess,' {friend.name} said, and the room went quiet."
    )
    world.para()
    world.say(
        f"{hero.name} noticed a tiny smear of blue paint on the folded note, so {hero.name} opened it carefully."
    )
    clue_note.hidden = False
    clue_note.meters["touched"] += 1
    world.say(
        f"The note said, 'paint here after the rain.' That was the mystery: someone had been finishing the mural to help the seedling grow."
    )
    seedling.grown = True
    hero.meters["growth"] += 1
    friend.meters["growth"] += 1
    rival.meters["growth"] += 1
    world.say(
        f"{hero.name} looked at {rival.name} again and asked, 'Were you trying to protect the wall?'"
    )
    world.say(
        f"{rival.name} blinked. 'I thought the painting might hurt the bricks,' {rival.name} admitted. 'I didn't want trouble.'"
    )
    world.say(
        f"{hero.name} answered, 'Then let's make it careful together.'"
    )
    rival.memes["hurt"] -= 1
    rival.memes["peace"] += 1
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"{friend.name} smiled and said, 'We can add flowers around the door and leave the bricks safe.'"
    )
    world.say(
        f"So they painted side by side, speaking in soft voices, and the tiny doorway in the mural became bright with green vines and gold petals."
    )
    world.para()
    world.say(
        f"By evening, {seedling.label} had risen taller, the note was pinned where everyone could read it, and {rival.name} was no longer guarding the wall alone."
    )
    world.say(
        f"{hero.name}, {friend.name}, and {rival.name} stood back to look at the finished scene. The mystery had turned into a promise, and the wall seemed to smile."
    )

    world.facts.update(
        place=place,
        hero=hero,
        friend=friend,
        rival=rival,
        mural=mural,
        clue_note=clue_note,
        seedling=seedling,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"].label
    hero = world.facts["hero"].name
    friend = world.facts["friend"].name
    rival = world.facts["rival"].name
    return [
        f"Write a short mystery story set in {p} about {hero}, {friend}, and {rival}, ending in reconciliation.",
        f"Tell a child-friendly story where a young art-ist notices growth, asks careful questions, and finds a happy ending.",
        f"Write a dialogue-driven story about a clue in {p} that leads to a shared painting and a peaceful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"].name
    friend = world.facts["friend"].name
    rival = world.facts["rival"].name
    place = world.facts["place"].label
    return [
        QAItem(
            question=f"Why did {hero} think there was a mystery in {place}?",
            answer=f"{hero} noticed that the mural kept changing a little each day, so {hero} wondered who was adding the new brushstrokes.",
        ),
        QAItem(
            question=f"What clue helped {hero} understand the changing mural?",
            answer=f"The folded note said, 'paint here after the rain,' which showed that someone was helping the mural and the little plant grow.",
        ),
        QAItem(
            question=f"How did {hero}, {friend}, and {rival} solve the problem?",
            answer=f"They talked it through, understood that {rival} had been worried about the wall, and then painted together in a careful way.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The seedling grew taller, the mural looked beautiful, and everyone was calm because they had reconciled and worked together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a small bit of information that helps people understand what is happening or who did something.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people stop being upset with each other and make peace again.",
        ),
        QAItem(
            question="Why do plants grow toward light?",
            answer="Plants grow toward light because light helps them make food and stay healthy.",
        ),
        QAItem(
            question="Why is talking useful when people disagree?",
            answer="Talking lets people explain their feelings, learn the truth, and find a kinder solution together.",
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
    lines.append(f"place={world.place.label}")
    for c in world.characters.values():
        lines.append(f"character {c.name}: role={c.role} trait={c.trait} meters={c.meters} memes={c.memes}")
    for a in world.artifacts.values():
        lines.append(f"artifact {a.label}: kind={a.kind} hidden={a.hidden} grown={a.grown} meters={a.meters} memes={a.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
character(C) :- hero(C); friend(C); rival(C).

mystery(P) :- clue(N), hidden(N), place(P).
growth_scene(P) :- growth_item(G), grown(G), place(P).
reconcile_story(P) :- talks(T), peace(T), place(P).
happy_ending(P) :- growth_scene(P), reconcile_story(P), mystery(P).

#show mystery/1.
#show growth_scene/1.
#show reconcile_story/1.
#show happy_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("rival", "rival"))
    lines.append(asp.fact("clue", "note"))
    lines.append(asp.fact("hidden", "note"))
    lines.append(asp.fact("growth_item", "seedling"))
    lines.append(asp.fact("grown", "seedling"))
    lines.append(asp.fact("talks", "dialogue"))
    lines.append(asp.fact("peace", "dialogue"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    atoms = set(asp.atoms(model, "happy_ending"))
    expected = {("base",)}
    if not atoms:
        print("MISMATCH: ASP did not derive a happy ending.")
        return 1
    print("OK: ASP reasoner derives a happy ending.")
    return 0


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def world_knowledge_topic() -> list[QAItem]:
    return [
        QAItem(question="What is growth?", answer="Growth is when something becomes bigger, stronger, or more developed over time."),
        QAItem(question="Why do artists ask questions?", answer="Artists ask questions to notice details, understand feelings, and make better pictures."),
        QAItem(question="What is a happy ending?", answer="A happy ending is when the trouble is solved and things end in a good way."),
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


CURATED = [
    StoryParams(place="studio", hero="Mina", friend="June", rival="Moss"),
    StoryParams(place="greenhouse", hero="Lena", friend="Pip", rival="Iris"),
    StoryParams(place="wall", hero="Noah", friend="Oren", rival="Bea"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
