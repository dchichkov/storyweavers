#!/usr/bin/env python3
"""
storyworlds/worlds/republic_quest_surprise_folk_tale.py
======================================================

A small storyworld about a folk-tale republic, a quest, and a surprise.

A child-facing seed story:
---
In a little republic of hill villages, the people kept a lantern on the town
square so everyone could read the voting stone and share news at dusk.

One spring, the lantern went missing before the market song. Mira, a young
goatherd, promised the elders she would find it before the council bell. She
followed a trail of berry crumbs, crossed a moss bridge, and asked the river
her first riddle. At the old willow, a fox gave her a surprise: the lantern had
not been stolen at all. The mayor had hidden it in a carved box so the children
could learn the republic's secret path to the moon well.

Mira laughed, carried the lantern home, and lit the square in time for the song.

Causal state updates:
---
    quest progress -> seeker.meters["progress"] += 1
    quest step solved honestly -> seeker.memes["hope"] += 1
    surprise revealed -> seeker.memes["wonder"] += 1 ; community.memes["trust"] += 1
    lantern returned -> square.meters["light"] += 1 ; community.meters["order"] += 1

Style:
---
A folk tale voice with a clear quest, a surprise turn, and a bright ending image.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "elderwoman"}
        male = {"boy", "man", "father", "king", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    name: str
    place: str
    signal: str
    people: str


@dataclass
class Quest:
    id: str
    task: str
    track: str
    clue: str
    return_word: str
    risk_word: str
    keyword: str = "quest"


@dataclass
class Surprise:
    id: str
    reveal: str
    twist: str
    wonder: str
    end_image: str
    keyword: str = "surprise"


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "hill_republic": Setting(
        name="hill republic",
        place="a round square between green hills",
        signal="the council bell",
        people="the folk",
    ),
    "river_republic": Setting(
        name="river republic",
        place="a stone quay beside the river",
        signal="the bell at the water gate",
        people="the neighbors",
    ),
    "orchard_republic": Setting(
        name="orchard republic",
        place="an apple square under tall trees",
        signal="the market horn",
        people="the villagers",
    ),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        task="find the missing lantern",
        track="follow berry crumbs and kindly signs",
        clue="a carved box",
        return_word="returned",
        risk_word="dark",
        keyword="quest",
    ),
    "ring": Quest(
        id="ring",
        task="bring back the silver town ring",
        track="ask each helper in turn",
        clue="the mayor's bread basket",
        return_word="brought back",
        risk_word="empty",
        keyword="quest",
    ),
    "key": Quest(
        id="key",
        task="recover the brass gate key",
        track="listen to the old willow and the brook",
        clue="a bird nest",
        return_word="carried home",
        risk_word="locked",
        keyword="quest",
    ),
}

SURPRISES = {
    "fox_box": Surprise(
        id="fox_box",
        reveal="the fox had not stolen anything",
        twist="the fox was guarding the secret instead",
        wonder="a bright mystery",
        end_image="the lantern glowing in the square like a small sun",
        keyword="surprise",
    ),
    "grandmother": Surprise(
        id="grandmother",
        reveal="the grandmother had hidden the treasure",
        twist="she wanted the children to learn the old path first",
        wonder="a warm family secret",
        end_image="the treasure wrapped in a blue cloth by the hearth",
        keyword="surprise",
    ),
    "mayor_note": Surprise(
        id="mayor_note",
        reveal="the mayor had written a note and tucked it in the basket",
        twist="the note led the seeker to a lesson about sharing",
        wonder="a clever little trick",
        end_image="the note shining on the table beside the prize",
        keyword="surprise",
    ),
}

HERO_NAMES = ["Mira", "Toma", "Lena", "Jori", "Sana", "Niko", "Pia", "Elio"]
COMMUNITY_LABELS = ["the elders", "the people", "the folk", "the neighbors"]
TRAITS = ["brave", "curious", "kind", "patient", "steady", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for q in QUESTS:
            for su in SURPRISES:
                combos.append((s, q, su))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    surprise: str
    hero: str
    trait: str
    community: str = "the folk"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a folk-tale republic, a quest, and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--community", choices=COMMUNITY_LABELS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, surprise = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    community = args.community or rng.choice(COMMUNITY_LABELS)
    return StoryParams(setting=setting, quest=quest, surprise=surprise, hero=hero, trait=trait, community=community)


def _world_from_params(p: StoryParams) -> World:
    if p.setting not in SETTINGS or p.quest not in QUESTS or p.surprise not in SURPRISES:
        raise StoryError("Invalid story parameters.")
    world = World(SETTINGS[p.setting])
    hero = world.add(Entity(id=p.hero, kind="character", type="girl", role="seeker"))
    elder = world.add(Entity(id="Elder", kind="character", type="elderwoman", label="the elder"))
    square = world.add(Entity(id="Square", kind="place", type="place", label="the square"))
    prize = world.add(Entity(id="Prize", kind="thing", type="thing", label=QUESTS[p.quest].task))
    quest = QUESTS[p.quest]
    surprise = SURPRISES[p.surprise]
    hero.meters["progress"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["wonder"] = 0.0
    elder.memes["trust"] = 0.0
    square.meters["light"] = 0.0
    square.meters["order"] = 0.0
    world.facts.update(hero=hero, elder=elder, square=square, prize=prize, quest=quest, surprise=surprise, params=p)
    return world


def _do_progress(world: World, hero: Entity) -> None:
    hero.meters["progress"] += 1
    hero.memes["hope"] += 1


def _do_surprise(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["wonder"] += 1
    elder.memes["trust"] += 1


def tell(world: World) -> None:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    quest = world.facts["quest"]
    surprise = world.facts["surprise"]
    p: StoryParams = world.facts["params"]
    setting = world.setting

    world.say(
        f"In the {setting.name}, {p.hero} was a {p.trait} little seeker who loved the sound of old stories."
    )
    world.say(
        f"Each dusk, {setting.people} gathered at {setting.place} to hear the republic's bell and share news."
    )
    world.say(
        f"One day the people found that {quest.task} was gone, and {p.hero} promised to {quest.task} before {setting.signal} rang."
    )
    _do_progress(world, hero)

    world.para()
    world.say(
        f"{p.hero} set out on the {quest.keyword} and chose to {quest.track}, with only a small basket and a brave heart."
    )
    world.say(
        f"The trail led past the willow, where the path felt {quest.risk_word} and the air smelled of rain and berries."
    )
    _do_progress(world, hero)

    world.para()
    world.say(
        f"At last came the {surprise.keyword}: {surprise.reveal}, and {surprise.twist}."
    )
    _do_surprise(world, hero, elder)
    world.say(
        f"{p.hero} laughed, because the answer was kinder than a stolen story. That was the republic's way: listen well, and the truth will find you."
    )

    world.para()
    world.say(
        f"Together they carried the prize home, and by evening {setting.place} held {surprise.end_image}."
    )
    world.say(
        f"The {p.community} smiled under the lantern light, and {p.hero} knew the quest had made the whole republic feel closer."
    )
    world.facts["done"] = True


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    q: Quest = world.facts["quest"]
    s: Surprise = world.facts["surprise"]
    return [
        f"Write a folk tale about a republic where {p.hero} must {q.task} and finds {s.keyword}.",
        f"Tell a short story for children in a republic, with a quest, a surprise turn, and a bright ending.",
        f"Write a gentle tale that uses the word republic and ends with {p.hero} learning a surprise about the missing prize.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    q: Quest = world.facts["quest"]
    s: Surprise = world.facts["surprise"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    qa = [
        QAItem(
            question=f"What was {p.hero} trying to do in the republic?",
            answer=f"{p.hero} was trying to {q.task}. {p.hero} promised to do it before the town bell rang, so the story had a clear quest from the start.",
        ),
        QAItem(
            question=f"How did {p.hero} search for the missing prize?",
            answer=f"{p.hero} followed {q.track}. The journey moved through the folk-tale world step by step, so the search felt like a real quest instead of a quick guess.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was that {s.reveal}. It changed the story from worry to wonder and showed that the answer had been hidden in a kind way.",
        ),
        QAItem(
            question=f"How did {p.hero} feel when the surprise was revealed?",
            answer=f"{p.hero} felt hope and wonder. The search had paid off, and the elder's trust helped turn the quest into a happy ending.",
        ),
    ]
    if hero.meters["progress"] >= THRESHOLD:
        qa.append(QAItem(
            question=f"Did {p.hero} really make progress on the quest?",
            answer=f"Yes. {p.hero} moved forward twice in the story, once by starting the search and again by following the clues. That progress is why the ending feels earned.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    q: Quest = world.facts["quest"]
    s: Surprise = world.facts["surprise"]
    out = [
        QAItem(
            question="What is a republic?",
            answer="A republic is a place where people share the rules and choose leaders in a peaceful way. Folk tales often use a republic to show a community working together.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or solve a hard problem. In stories, a quest gives the hero a goal and a reason to keep going.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something the reader or character did not expect. It can change the meaning of the journey and make the ending feel new.",
        ),
    ]
    return out


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
progressed(H) :- hero(H).
wondered(H) :- hero(H).
trusted(E) :- elder(E).
story_good :- hero(H), progressed(H), wondered(H), trusted(E).
valid(S,Q,Su) :- setting(S), quest(Q), surprise(Su).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for su in SURPRISES:
        lines.append(asp.fact("surprise", su))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("elder", "elder"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between ASP and Python gate.")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))
        return 1
    # smoke test normal generation
    sample = generate(StoryParams(setting="hill_republic", quest="lantern", surprise="fox_box", hero="Mira", trait="curious"))
    if not sample.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    print(f"OK: ASP gate matches Python ({len(cl)} combos) and generation works.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = _world_from_params(params)
    tell(world)
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
    StoryParams(setting="hill_republic", quest="lantern", surprise="fox_box", hero="Mira", trait="curious", community="the folk"),
    StoryParams(setting="river_republic", quest="ring", surprise="grandmother", hero="Toma", trait="kind", community="the neighbors"),
    StoryParams(setting="orchard_republic", quest="key", surprise="mayor_note", hero="Lena", trait="brave", community="the villagers"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, surprise = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    community = args.community or rng.choice(COMMUNITY_LABELS)
    return StoryParams(setting=setting, quest=quest, surprise=surprise, hero=hero, trait=trait, community=community)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, quest, surprise) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.quest} / {p.surprise} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
