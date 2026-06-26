#!/usr/bin/env python3
"""
storyworlds/worlds/creamery_distract_quest_ghost_story.py
=========================================================

A small storyworld: a child at a creamery, a distracting ghost, and a quest to
recover a lost little favor before the frozen treats melt.

The world is built from a simple premise:
- A child arrives at a creamery with a quest.
- A ghostly distraction threatens the quest.
- The child uses a kind, concrete method to stay focused.
- The ending proves the quest changed the world state.

The prose aims for a gentle ghost-story feel: chilly air, soft creaks, silver
light, and a small brave turn without real danger.
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
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the creamery"
    afford_quest: bool = True


@dataclass
class Quest:
    id: str
    object_label: str
    object_phrase: str
    aim: str
    clue: str
    reward: str


@dataclass
class Ghost:
    id: str
    label: str
    distraction: str
    method: str
    tell: str


@dataclass
class StoryParams:
    place: str
    quest: str
    ghost: str
    name: str
    gender: str
    helper: str
    trait: str
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


QUESTS = {
    "key": Quest(
        id="key",
        object_label="silver key",
        object_phrase="a tiny silver key with a star on it",
        aim="find the hidden door",
        clue="the key would open a little cabinet behind the freezer",
        reward="the quest could end",
    ),
    "receipt": Quest(
        id="receipt",
        object_label="old receipt",
        object_phrase="an old receipt folded into a square",
        aim="prove the order was paid for",
        clue="the receipt was tucked behind the scoop stand",
        reward="the promise could be kept",
    ),
}

GHOSTS = {
    "whisper": Ghost(
        id="whisper",
        label="a whispery ghost",
        distraction="kept calling the child to the frosty window",
        method="look at the sparkly trail and then back at the quest",
        tell="its voice sounded like wind through a spoon drawer",
    ),
    "bell": Ghost(
        id="bell",
        label="a bell-ringing ghost",
        distraction="made the ice-cream bell ring again and again",
        method="count three breaths and hold the map tight",
        tell="every chime made the spoons tremble",
    ),
}

SETTINGS = {
    "creamery": Setting(place="the creamery", afford_quest=True),
}

TRAITS = ["curious", "brave", "gentle", "quiet", "cheerful"]
NAMES_GIRL = ["Mina", "Lily", "Ivy", "Nora", "June"]
NAMES_BOY = ["Theo", "Finn", "Eli", "Owen", "Milo"]


def first_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def story_intro(hero: Entity, helper: Entity, quest: Quest, setting: Setting) -> str:
    return (
        f"{hero.id} was a little {hero.type} who loved night lights, warm cocoa, and quiet errands. "
        f"One chilly evening, {hero.id} and {helper.label} went to {setting.place} for a small quest: "
        f"to {quest.aim}."
    )


def ghost_arrival(hero: Entity, ghost: Ghost) -> str:
    return (
        f"But when they stepped inside, {ghost.label} drifted from the freezer door. "
        f"It {ghost.distraction}, and {ghost.tell}."
    )


def quest_pressure(hero: Entity, quest: Quest) -> str:
    return (
        f"{hero.id} held the map with both hands, because {quest.clue}. "
        f"The little paper felt important, and the room seemed colder around it."
    )


def focus_turn(hero: Entity, helper: Entity, ghost: Ghost, quest: Quest) -> str:
    return (
        f"{helper.label} leaned close and said, \"We can keep going.\" "
        f"{hero.id} took a slow breath, chose to {ghost.method}, and walked past the humming freezer."
    )


def resolution(hero: Entity, helper: Entity, quest: Quest) -> str:
    return (
        f"At the back cabinet, {hero.id} found {quest.object_phrase}. "
        f"{hero.id} opened the little latch, the quest was finished, and the creamery lights looked softer than before."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", type="parent", label=f"the {params.helper}"))
    quest = QUESTS[params.quest]
    ghost = GHOSTS[params.ghost]

    world.facts.update(hero=hero, helper=helper, quest=quest, ghost=ghost, setting=setting)

    hero.memes["determination"] = 1.0
    hero.memes["worry"] = 0.0
    ghost_ent = world.add(Entity(id=ghost.id, kind="character", type="ghost", label=ghost.label))
    ghost_ent.memes["mischief"] = 1.0

    world.say(story_intro(hero, helper, quest, setting))
    world.say(
        f"{hero.id} carried {first_article(quest.object_label)} {quest.object_label} card in {hero.pronoun('possessive')} pocket."
    )

    world.para()
    world.say(ghost_arrival(hero, ghost))
    hero.memes["worry"] += 1.0
    world.say(quest_pressure(hero, quest))

    world.para()
    world.say(f"{hero.id} almost forgot the quest when the ghost danced by the mint case.")
    world.say(f"Then {helper.label} pointed to the map and gave {hero.pronoun('object')} a small nod.")
    world.say(focus_turn(hero, helper, ghost, quest))
    hero.memes["worry"] = 0.0
    hero.memes["focus"] = 1.0

    world.para()
    world.say(resolution(hero, helper, quest))
    hero.memes["joy"] = 1.0
    hero.meters["quest_done"] = 1.0
    ghost_ent.meters["distracted"] = 0.0
    world.say(f"{hero.id} smiled, because the ghost had only wanted attention, and the quest was safely done.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    ghost: Ghost = f["ghost"]  # type: ignore[assignment]
    return [
        f'Write a gentle ghost story set at {world.setting.place} about {hero.id} and a small quest.',
        f'Tell a child-facing story where {ghost.label} distracts {hero.id}, but {hero.id} stays focused and finishes a quest.',
        f'Write a short story that includes "{quest.object_label}" and ends with a completed quest at the creamery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    ghost: Ghost = f["ghost"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.id} go to do the quest?",
            answer=f"{hero.id} went to {world.setting.place} with {helper.label} to finish the quest.",
        ),
        QAItem(
            question=f"What kept trying to distract {hero.id}?",
            answer=f"{ghost.label} kept trying to distract {hero.id}, but {hero.id} stayed focused on the quest.",
        ),
        QAItem(
            question=f"What did {hero.id} find at the end?",
            answer=f"{hero.id} found {quest.object_phrase} and completed the quest.",
        ),
        QAItem(
            question=f"How did {hero.id} avoid getting tricked by the ghost?",
            answer=f"{hero.id} listened to {helper.label}, took a slow breath, and followed the map instead of the distraction.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a creamery?",
            answer="A creamery is a place where people make and sell dairy treats like ice cream.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small mission or search for something important.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character that can be mysterious, but in gentle stories it can be harmless.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = [asp.fact("place", "creamery")]
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
        lines.append(asp.fact("quest_object", q.id, q.object_label))
    for g in GHOSTS.values():
        lines.append(asp.fact("ghost", g.id))
        lines.append(asp.fact("distracts", g.id))
    lines.append(asp.fact("setting_supports", "creamery", "quest"))
    return "\n".join(lines)


ASP_RULES = r"""
supported_story(P) :- place(P), setting_supports(P, quest).
has_distraction(G) :- ghost(G), distracts(G).
reasonable_story(P) :- supported_story(P), has_distraction(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    import asp

    model = asp.one_model(asp_program("#show reasonable_story/1."))
    return bool(asp.atoms(model, "reasonable_story"))


def asp_verify() -> int:
    py = SETTINGS["creamery"].afford_quest and bool(GHOSTS)
    asp_ok = asp_reasonable()
    if py == asp_ok:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print(f"MISMATCH: python={py} asp={asp_ok}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle creamery ghost story with a small quest.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="creamery")
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--ghost", choices=GHOSTS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.place != "creamery":
        raise StoryError("This storyworld only supports the creamery setting.")
    quest = args.quest or rng.choice(list(QUESTS))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=args.place,
        quest=quest,
        ghost=ghost,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_params() -> list[StoryParams]:
    out = []
    for q in QUESTS:
        for g in GHOSTS:
            for gender in ["girl", "boy"]:
                out.append(
                    StoryParams(
                        place="creamery",
                        quest=q,
                        ghost=g,
                        name="Mina" if gender == "girl" else "Theo",
                        gender=gender,
                        helper="mother",
                        trait="curious",
                    )
                )
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show reasonable_story/1."))
        atoms = asp.atoms(model, "reasonable_story")
        print(f"{len(atoms)} reasonable story shape(s)")
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in valid_params()]
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
