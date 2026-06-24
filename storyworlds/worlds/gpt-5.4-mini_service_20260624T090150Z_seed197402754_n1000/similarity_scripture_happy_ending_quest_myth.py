#!/usr/bin/env python3
"""
storyworlds/worlds/similarity_scripture_happy_ending_quest_myth.py
===================================================================

A small mythic storyworld about a quest, a scripture, and a useful similarity.

Seed-tale shape:
- A young seeker hears of a sacred scripture.
- A guide sends them on a quest to find a sign that matches the scripture's image.
- The seeker notices a real-world similarity, proves the teaching, and returns home
  with a happy ending.

This world keeps the prose close to myth: humble travelers, wise guides,
symbolic places, and a clear end image showing what changed.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    sign: str
    affordance: str


@dataclass
class Scripture:
    id: str
    title: str
    line: str
    image: str
    theme: str


@dataclass
class Quest:
    id: str
    objective: str
    destination: str
    clue: str
    proof_word: str
    reward: str


@dataclass
class StoryParams:
    setting: str
    scripture: str
    quest: str
    name: str
    role: str
    guide: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "mountain_temple": Setting(
        place="the mountain temple",
        mood="high and quiet",
        sign="a single white stair that catches the dawn",
        affordance="clear sight",
    ),
    "river_shrine": Setting(
        place="the river shrine",
        mood="bright and moving",
        sign="a curve of water around a stone",
        affordance="flowing reflections",
    ),
    "forest_altar": Setting(
        place="the forest altar",
        mood="green and still",
        sign="two trees leaning like old friends",
        affordance="living echoes",
    ),
}

SCRIPTURES = {
    "scroll_of_resemblance": Scripture(
        id="scroll_of_resemblance",
        title="the Scroll of Resemblance",
        line="When the small mirror meets the wide sky, the path becomes clear.",
        image="a small mirror meeting the wide sky",
        theme="similarity",
    ),
    "hymn_of_kindred_paths": Scripture(
        id="hymn_of_kindred_paths",
        title="the Hymn of Kindred Paths",
        line="Look for the same shape in the stone and in the heart, and you will not be lost.",
        image="the same shape in the stone and in the heart",
        theme="scripture",
    ),
}

QUESTS = {
    "find_the_match": Quest(
        id="find_the_match",
        objective="find the thing that matches the scripture's image",
        destination="the old path",
        clue="a mark that looked like the scripture's picture",
        proof_word="match",
        reward="hope",
    ),
    "bring_back_the_sign": Quest(
        id="bring_back_the_sign",
        objective="bring back the sign foretold by the scripture",
        destination="the far hill",
        clue="a pattern that repeated itself in the world",
        proof_word="sign",
        reward="joy",
    ),
}

GIRL_NAMES = ["Mira", "Ayla", "Nora", "Lina", "Tara", "Iris"]
BOY_NAMES = ["Arin", "Theo", "Soren", "Pax", "Ezra", "Milo"]
ROLES = ["young seeker", "brave child", "small pilgrim", "earnest wanderer"]
GUIDES = ["the elder", "the priest", "the grandmother", "the keeper"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def introduction(world: World, hero: Entity, guide: Entity, scripture: Scripture) -> None:
    world.say(
        f"Once, in {world.setting.place}, there lived {hero.phrase} who longed to learn what the old words meant."
    )
    world.say(
        f"{guide.label.capitalize()} kept {scripture.title}, and said it was a scripture worth carrying carefully."
    )
    world.say(
        f"On its first page, it said: “{scripture.line}”"
    )


def quest_call(world: World, hero: Entity, guide: Entity, scripture: Scripture, quest: Quest) -> None:
    world.para()
    hero.memes["longing"] = hero.memes.get("longing", 0) + 1
    world.say(
        f"{guide.label.capitalize()} sent {hero.pronoun('object')} on a quest to {quest.objective}."
    )
    world.say(
        f"The guide warned that the answer would not come from speed, but from noticing a true similarity."
    )
    world.say(
        f"So {hero.id} went {quest.destination}, carrying the scripture in {hero.pronoun('possessive')} mind."
    )


def discovery(world: World, hero: Entity, scripture: Scripture, quest: Quest) -> None:
    world.para()
    hero.meters["travel"] = hero.meters.get("travel", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"At {world.setting.place}, {hero.id} looked and listened until {hero.pronoun('subject')} noticed {world.setting.sign}."
    )
    world.say(
        f"It had the same kind of shape as {scripture.image}, and the likeness was so clear that {hero.id} smiled at once."
    )
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    world.facts["found_similarity"] = True
    world.facts["proof"] = quest.proof_word


def return_and_end(world: World, hero: Entity, guide: Entity, scripture: Scripture, quest: Quest) -> None:
    world.para()
    world.say(
        f"{hero.id} hurried home with the glad news and showed {guide.pronoun('object')} the discovered likeness."
    )
    world.say(
        f"{guide.label.capitalize()} nodded, for the scripture had not been a riddle after all; it had been a lamp."
    )
    world.say(
        f"In the end, {hero.id} knew the quest had led to {quest.reward}, and the old words felt warm instead of distant."
    )
    world.say(
        f"That night, the temple was quiet, and the scripture rested safely while {hero.id} slept with a happy heart."
    )


def tell(setting: Setting, scripture: Scripture, quest: Quest, hero_name: str, role: str, guide_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="child" if role in {"young seeker", "small pilgrim", "brave child", "earnest wanderer"} else "person",
        label=hero_name,
        phrase=f"{role} named {hero_name}",
    ))
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type="elder",
        label=guide_name,
        phrase=f"{guide_name} the guide",
    ))
    world.facts.update(hero=hero, guide=guide, scripture=scripture, quest=quest, setting=setting)

    introduction(world, hero, guide, scripture)
    quest_call(world, hero, guide, scripture, quest)
    discovery(world, hero, scripture, quest)
    return_and_end(world, hero, guide, scripture, quest)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for a child about {f["hero"].id} and a scripture that teaches about similarity.',
        f"Tell a gentle quest story where {f['hero'].id} searches at {f['setting'].place} for a sign that matches {f['scripture'].title}.",
        f"Write a happy-ending myth in which a child finds a proof-word and comes home wiser.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    scripture: Scripture = f["scripture"]
    quest: Quest = f["quest"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.phrase}, who went on a quest in {setting.place} to understand {scripture.title}.",
        ),
        QAItem(
            question=f"What did {guide.label} send {hero.id} to do?",
            answer=f"{guide.label.capitalize()} sent {hero.id} to {quest.objective}.",
        ),
        QAItem(
            question=f"What similarity did {hero.id} notice?",
            answer=f"{hero.id} noticed that {setting.sign} had the same kind of shape as {scripture.image}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {hero.id} returned with understanding, and the scripture felt like a lamp instead of a puzzle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    scripture: Scripture = f["scripture"]
    quest: Quest = f["quest"]
    return [
        QAItem(
            question="What is a scripture?",
            answer="A scripture is a sacred writing that people read carefully because they believe it can teach wisdom.",
        ),
        QAItem(
            question="What is a similarity?",
            answer="A similarity is something two things share, like a shape, color, or pattern that makes them feel alike.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important, solve a problem, or learn a truth.",
        ),
        QAItem(
            question="Why does the scripture matter in this world?",
            answer=f"It matters because it points the seeker toward {quest.reward} through a true likeness and a good answer.",
        ),
        QAItem(
            question="What does the story teach about noticing?",
            answer="It teaches that careful looking can reveal meaning, especially when a sign in the world matches words in a scripture.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- place(S,_).
scripture(S) :- scripture_id(S).
quest(Q) :- quest_id(Q).

similarity_found(S, Q) :- setting(S), quest(Q), scripture(_), affordance(S, _).
happy_ending(S, Q) :- similarity_found(S, Q).

valid_story(Place, Scripture, Quest) :- setting_id(Place), scripture_id(Scripture), quest_id(Quest).
chosen_story(Place, Scripture, Quest) :- valid_story(Place, Scripture, Quest), similarity_found(Place, Quest), happy_ending(Place, Quest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_id", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("mood", sid, s.mood))
        lines.append(asp.fact("sign", sid, s.sign))
        lines.append(asp.fact("affordance", sid, s.affordance))
    for sid, s in SCRIPTURES.items():
        lines.append(asp.fact("scripture_id", sid))
        lines.append(asp.fact("scripture_theme", sid, s.theme))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_id", qid))
        lines.append(asp.fact("quest_reward", qid, q.reward))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n#show chosen_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = set((p, s, q) for p in SETTINGS for s in SCRIPTURES for q in QUESTS)
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python story grid ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    scripture: str
    quest: str
    name: str
    role: str
    guide: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mythic quest storyworld about similarity and scripture."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scripture", choices=SCRIPTURES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--guide", choices=GUIDES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    scripture = args.scripture or rng.choice(list(SCRIPTURES))
    quest = args.quest or rng.choice(list(QUESTS))
    role = args.role or rng.choice(ROLES)
    guide = args.guide or rng.choice(GUIDES)
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, scripture=scripture, quest=quest, name=name, role=role, guide=guide)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, s, q) for p in SETTINGS for s in SCRIPTURES for q in QUESTS]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SCRIPTURES[params.scripture],
        QUESTS[params.quest],
        params.name,
        params.role,
        params.guide,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n"))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, s, q in combos:
            print(f"  {p:16} {s:26} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams(setting=p, scripture=s, quest=q, name="Mira", role="young seeker", guide="the elder")
                  for p, s, q in valid_combos()]:
            samples.append(generate(p))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
