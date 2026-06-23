#!/usr/bin/env python3
"""
storyworlds/worlds/vault_quest_humor_magic_folk_tale.py
=======================================================

A small folk-tale storyworld about a quest to open a village vault with humor
and a little magic. The world tracks physical meters and emotional memes, and
the story emerges from state changes: a clever plan, a comic setback, a magical
turn, and a final image proving the vault opened safely.

Seed tale:
---
A village kept its winter honey, seed bread, and moon coins inside a stone
vault under the elder's hall. One morning, the latch jammed, and the villagers
could not open it. A child set off on a quest to ask the old fox-sage for help.
The fox gave a riddle, a singing key, and a warning: "Laugh kindly, and the
door will listen." After a few silly tries, the child discovered that the vault
opened only when the family sang together and turned the key with a smile.
The vault opened, everyone shared the food, and the village cheered.

This script turns that premise into a constraint-checked, story-driven world.
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
    owner: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "fox-sage"}
        male = {"boy", "father", "man", "fox-sage"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    echoes: str = ""
    has_vault: bool = True
    vault_type: str = "stone"
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    mischief: str
    turns: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    place: str
    quest: str
    magic: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "elder_hall": Place(id="elder_hall", label="the elder's hall", echoes="soft and wooden", tags={"hall", "vault"}),
    "orchard": Place(id="orchard", label="the orchard", echoes="bright with bees", tags={"orchard"}),
    "lane": Place(id="lane", label="the lane", echoes="small and windy", tags={"lane"}),
}

QUESTS = {
    "honey_latch": Quest(id="honey_latch", goal="open the vault", clue="listen for the latch's little song",
                         mischief="the latch kept sulking", turns=["quest", "humor", "magic"], tags={"vault", "quest"}),
    "moon_coins": Quest(id="moon_coins", goal="open the vault", clue="find the key that rings like a spoon",
                        mischief="the lock had a stubborn cough", turns=["quest", "humor", "magic"], tags={"vault", "quest"}),
}

MAGIC = {
    "singing_key": MagicTool(id="singing_key", label="a singing key", phrase="a singing key",
                             effect="it chimed when the right words were spoken",
                             sound="tink-tink-tin", tags={"magic", "key"}),
    "fox_riddle": MagicTool(id="fox_riddle", label="a fox riddle", phrase="a fox riddle",
                            effect="it made the latch think harder than before",
                            sound="hmm-hah", tags={"magic", "riddle"}),
    "laughing_salt": MagicTool(id="laughing_salt", label="laughing salt", phrase="a pinch of laughing salt",
                               effect="it tickled the lock awake",
                               sound="hee-hee", tags={"magic", "humor"}),
}

TREASURE = Treasure(id="treasure", label="winter honey, seed bread, and moon coins",
                    phrase="winter honey, seed bread, and moon coins", plural=True,
                    tags={"food", "vault"})


class StoryWorld:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS:
            for m in MAGIC:
                combos.append((p, q, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale vault quest with humor and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["boy", "girl"], dest="hero_type")
    ap.add_argument("--helper-type", choices=["boy", "girl", "fox-sage"], dest="helper_type")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, magic = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "fox-sage"])
    hero_name = args.name or rng.choice(["Nia", "Toby", "Mira", "Pip", "Lina", "Jory"])
    helper_name = args.helper or (rng.choice(["Aunt May", "Old Fox", "Gran Bell"]) if helper_type == "fox-sage" else rng.choice(["Moss", "Wren", "Bram", "Suri"]))
    return StoryParams(place=place, quest=quest, magic=magic, hero_name=hero_name,
                       hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def _setup_world(params: StoryParams) -> tuple[StoryWorld, Entity, Entity, Entity, Quest, MagicTool, Treasure]:
    place = PLACES.get(params.place)
    quest = QUESTS.get(params.quest)
    magic = MAGIC.get(params.magic)
    if not place or not quest or not magic:
        raise StoryError("Invalid params.")
    world = StoryWorld(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name,
                            meters={"travel": 0.0}, memes={"hope": 0.0, "joy": 0.0, "worry": 0.0},
                            attrs={"role": "hero"}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name,
                              meters={"travel": 0.0}, memes={"hope": 0.0, "joy": 0.0, "worry": 0.0},
                              attrs={"role": "helper"}))
    vault = world.add(Entity(id="vault", kind="thing", type="vault", label="the vault", plural=False,
                             meters={"stuck": 1.0, "opened": 0.0}, memes={"grump": 1.0}, attrs={"place": place.id}))
    treasure = world.add(Entity(id="treasure", kind="thing", type="treasure", label=TREASURE.label, plural=True,
                                meters={"safe": 1.0}, memes={"need": 0.0}))
    tool = world.add(Entity(id="magic", kind="thing", type="magic", label=magic.label, plural=False,
                            meters={"glow": 1.0}, memes={"cheer": 1.0}, attrs={"effect": magic.effect}))
    return world, hero, helper, vault, quest, magic, TREASURE


def tell(world: StoryWorld, hero: Entity, helper: Entity, vault: Entity, quest: Quest, magic: MagicTool, treasure: Treasure) -> None:
    hero.memes["hope"] += 1
    hero.meters["travel"] += 1
    world.say(f"{hero.label} of {world.place.label} heard that the vault would not open.")
    world.say(f"The old folk sighed because the vault held {treasure.phrase}, and supper was growing late.")
    world.say(f"So {hero.label} set out on a quest to {quest.goal}, carrying nothing but courage and a grin.")
    world.para()
    helper.memes["joy"] += 1
    helper.memes["worry"] += 1
    world.say(f"At the lane, {helper.label} met {hero.label} and offered {magic.phrase}.")
    world.say(f'"{magic.sound}," {helper.label} said. "{quest.clue}."')
    world.say(f"{quest.mischief.capitalize()}, so the pair had to try the key twice and laugh once.")
    world.para()
    vault.meters["stuck"] = 0.0
    vault.meters["opened"] = 1.0
    vault.memes["grump"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{hero.label} sang a small tune, {helper.label} turned the lock, and {magic.effect}.")
    world.say(f"The vault clicked open at last, and inside lay {treasure.phrase}, shining like a feast in a cradle.")
    world.say(f"The village shared the food, and {hero.label} went home smiling, with the vault standing easy and open behind {hero.pronoun('object')}.")


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale about a child who sets out on a quest to open a vault using {f['magic'].label}.",
        f"Tell a gentle story with humor and magic where {f['hero'].label} helps the village get the food from the vault.",
        f"Create a short folk tale that includes the word 'vault' and ends with the vault opening after a clever song.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    magic = f["magic"]
    return [
        QAItem(
            question=f"Why did {hero.label} go on a quest?",
            answer=f"{hero.label} went because the vault would not open, and the village needed the food inside. The quest gave the child a chance to ask for magical help instead of giving up."
        ),
        QAItem(
            question=f"What did {helper.label} give {hero.label}?",
            answer=f"{helper.label} gave {hero.label} {magic.phrase}. It helped because the tool made the lock wake up and listen."
        ),
        QAItem(
            question="How did the story end?",
            answer="The vault opened, the village shared the food, and everyone went home laughing. The ending proves the problem was fixed, not just mentioned."
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vault?",
            answer="A vault is a strong place that keeps important things safe. People use a vault when they want a door that is hard to open without the right key or trick."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find, fix, or win something important. In folk tales, the traveler often meets a helper or a challenge along the way."
        ),
        QAItem(
            question="What makes a story funny?",
            answer="A funny story often includes a surprise, a silly mistake, or a playful twist. The humor makes the tale feel warm instead of scary."
        ),
        QAItem(
            question="What does magic do in a folk tale?",
            answer="Magic can reveal hidden answers, open stubborn doors, or help a brave character try again. It often works best when someone is kind or clever, too."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"- {p}" for p in sample.prompts)
    parts.append("")
    parts.append("== story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world, hero, helper, vault, quest, magic, treasure = _setup_world(params)
    tell(world, hero, helper, vault, quest, magic, treasure)
    world.facts.update(hero=hero, helper=helper, vault=vault, quest=quest, magic=magic, treasure=treasure)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
vault_opened :- stuck(vault,1), magic(magic), helper(helper).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.has_vault:
            lines.append(asp.fact("has_vault", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for mid in MAGIC:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show place/1."))
    return sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    ok = set(asp_valid_combos()) == set((p,) for p in PLACES)
    if not ok:
        print("MISMATCH: ASP facts do not match place registry.")
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, magic=None, name=None, helper=None, hero_type=None, helper_type=None), random.Random(777)))
    if not sample.story or "vault" not in sample.story.lower():
        print("MISMATCH: generated story smoke test failed.")
        return 1
    print("OK: ASP parity and story smoke test passed.")
    return 0


CURATED = [
    StoryParams(place="elder_hall", quest="honey_latch", magic="singing_key", hero_name="Nia", hero_type="girl", helper_name="Old Fox", helper_type="fox-sage"),
    StoryParams(place="orchard", quest="moon_coins", magic="fox_riddle", hero_name="Pip", hero_type="boy", helper_name="Moss", helper_type="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, magic = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "fox-sage"])
    hero_name = args.name or rng.choice(["Nia", "Pip", "Mira", "Toby", "Lina", "Jory"])
    helper_name = args.helper or (rng.choice(["Old Fox", "Aunt Brin", "Gran Moss"]) if helper_type == "fox-sage" else rng.choice(["Moss", "Bram", "Suri", "Wren"]))
    return StoryParams(place=place, quest=quest, magic=magic, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible places:", ", ".join(pid for pid in PLACES))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(json.dumps([s.to_dict() for s in samples] if len(samples) != 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and the {p.magic} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
