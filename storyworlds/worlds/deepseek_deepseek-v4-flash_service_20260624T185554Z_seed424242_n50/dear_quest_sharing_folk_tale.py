#!/usr/bin/env python3
"""
storyworlds/worlds/dear_quest_sharing_folk_tale.py
==================================================

A Folk Tale domain: a dear hero, a quest, and the lesson of sharing.
A small simulated world where the hero must share a discovered treasure
to help a dear companion. State-driven prose with causal rules.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "queen"}
        male = {"boy", "father", "grandfather", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    type: str = "forest"   # forest, mountain, village


@dataclass
class Quest:
    id: str
    verb: str               # "find the golden acorn"
    noun_phrase: str        # "a golden acorn"
    noun_label: str         # "acorn"
    twist: str              # what makes sharing necessary: "you must give half to your friend"
    sharing_lesson: str     # moral
    food: str               # offering or reward


@dataclass
class Companion:
    type: str
    name: str
    trait: str
    need: str               # what they lack: "hungry", "thirsty", "lonely"


SETTINGS = {
    "forest": Setting(place="the ancient forest"),
    "mountain": Setting(place="the misty mountain"),
    "village": Setting(place="the little village"),
}

QUESTS = {
    "acorn": Quest(
        id="acorn",
        verb="find the golden acorn",
        noun_phrase="a golden acorn",
        noun_label="acorn",
        twist="must share half of the acorn with a hungry squirrel",
        sharing_lesson="Sharing makes the heart full and the journey sweet.",
        food="berries",
    ),
    "star": Quest(
        id="star",
        verb="catch the falling star",
        noun_phrase="a falling star",
        noun_label="star",
        twist="must share the star's light with a lost rabbit",
        sharing_lesson="A star shines brighter when it lights another's path.",
        food="carrots",
    ),
    "pearl": Quest(
        id="pearl",
        verb="fetch the moon pearl",
        noun_phrase="a moon pearl",
        noun_label="pearl",
        twist="must share the pearl's glow with a blind owl",
        sharing_lesson="The greatest treasure is the joy of giving.",
        food="mushrooms",
    ),
}

COMPANIONS = {
    "squirrel": Companion(type="squirrel", name="Squeaky", trait="hungry", need="nuts"),
    "rabbit": Companion(type="rabbit", name="Hopper", trait="lost", need="light"),
    "owl": Companion(type="owl", name="Hoot", trait="blind", need="warmth"),
}

HERO_NAMES = ["Ella", "Finn", "Nora", "Kai", "Mira", "Leo", "Zara", "Theo"]
HERO_TRAITS = ["brave", "kind", "curious", "gentle", "wise", "generous"]

# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting, quest: Quest, companion: Companion):
        self.setting = setting
        self.quest = quest
        self.companion = companion
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting, self.quest, self.companion)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal Rules
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

def _r_hero_finds(world: World) -> list[str]:
    hero = world.get("hero")
    quest = world.quest
    if hero.meters["found"] >= THRESHOLD:
        return []
    sig = ("found",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["found"] = 1
    return [f"{hero.pronoun('possessive').capitalize()} eyes grew wide. There it was – {quest.noun_phrase}."]

def _r_companion_needs(world: World) -> list[str]:
    companion = world.get("companion")
    if companion.meters["needs_help"] >= THRESHOLD:
        return []
    sig = ("needs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    companion.meters["needs_help"] = 1
    return [f"{companion.pronoun('possessive').capitalize()} belly rumbled. {companion.pronoun('subject').capitalize()} was {world.companion.need}."]

def _r_hero_offers(world: World) -> list[str]:
    hero = world.get("hero")
    companion = world.get("companion")
    if hero.memes["generosity"] >= THRESHOLD:
        return []
    sig = ("offer",)
    if sig in world.fired:
        return []
    if companion.meters["needs_help"] >= THRESHOLD and hero.meters["found"] >= THRESHOLD:
        world.fired.add(sig)
        hero.memes["generosity"] = 1
        companion.memes["grateful"] = 1
        return [f"{hero.pronoun('subject').capitalize()} smiled and offered to share."]
    return []

CAUSAL_RULES = [
    ("find", _r_hero_finds),
    ("need", _r_companion_needs),
    ("offer", _r_hero_offers),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for _, apply in CAUSAL_RULES:
            sents = apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(f"Once upon a time, in {world.setting.place}, there lived a {hero.traits[0]} {hero.type} named {hero.id}.")

def tell_quest(world: World, hero: Entity) -> None:
    world.say(f"One day, {hero.id} heard about a great treasure – {world.quest.noun_phrase}.")
    world.say(f'"I must {world.quest.verb}," said {hero.id}, and {hero.pronoun()} set off at once.')

def meet_companion(world: World, hero: Entity, companion: Entity) -> None:
    world.say(f"Along the way, {hero.id} met a little {world.companion.type} named {companion.id}.")
    world.say(f"'{companion.id} looked {world.companion.trait}.'")

def discover(world: World, hero: Entity) -> None:
    world.say(f"After a long search, {hero.id} found what {hero.pronoun()} was looking for.")
    propagate(world)

def share_offer(world: World, hero: Entity, companion: Entity) -> None:
    world.say(f"{hero.id} looked at {world.quest.noun_label}, then at {companion.id}.")
    world.say(f'"You need this more than I do," said {hero.id}. "Let us share it together."')
    propagate(world)

def resolution(world: World, hero: Entity, companion: Entity) -> None:
    world.say(f"So {hero.id} and {companion.id} shared {world.quest.noun_label}.")
    world.say(f"{companion.id} felt better, and {hero.id} felt happy.")
    world.say(f"From that day on, they were the dearest of friends.")
    world.say(f"*{world.quest.sharing_lesson}*")

# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, quest: Quest, companion_cfg: Companion,
         hero_name: str, hero_type: str, hero_trait: str) -> World:
    world = World(setting, quest, companion_cfg)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=[hero_trait, "little"],
    ))
    companion = world.add(Entity(
        id=companion_cfg.name, kind="character", type=companion_cfg.type,
        traits=[companion_cfg.trait, world.companion.need],
    ))

    # Act 1
    introduce(world, hero)
    world.para()
    tell_quest(world, hero)
    world.para()
    meet_companion(world, hero, companion)

    # Act 2
    world.para()
    discover(world, hero)
    world.para()
    share_offer(world, hero, companion)

    # Act 3
    world.para()
    resolution(world, hero, companion)

    world.facts.update(hero=hero, companion=companion, quest=quest,
                       setting=setting, companion_cfg=companion_cfg)
    return world

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    companion: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A / Knowledge
# ---------------------------------------------------------------------------
KINDNESS_FACTS = {
    "sharing": [
        ("Why is sharing important?",
         "Sharing makes others happy and brings friends closer. When you share, "
         "you show you care, and the joy becomes twice as big.")
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a special journey where someone looks for something "
         "important or magical, and often learns a lesson along the way.")
    ],
    "acorn": [
        ("What is a golden acorn?",
         "A golden acorn is a magical nut that glows. It is rare and precious, "
         "but its true power comes from being shared.")
    ],
    "star": [
        ("What does catching a falling star mean?",
         "Catching a falling star is a folk tale idea – it means finding something "
         "bright and magical, and using its light to help others.")
    ],
    "pearl": [
        ("What is a moon pearl?",
         "A moon pearl is a shiny white stone that glows like the moon. "
         "It gives light and warmth to anyone nearby.")
    ],
    "squirrel": [
        ("What does a squirrel eat?",
         "Squirrels eat nuts, seeds, and berries. They are often hungry in winter.")
    ],
    "rabbit": [
        ("Why would a rabbit be lost?",
         "Rabbits can lose their way in the dark. They need light to find home.")
    ],
    "owl": [
        ("Why can't the owl see?",
         "Some owls are born blind. They rely on other senses and the kindness of others.")
    ],
}
KNOWLEDGE_ORDER = ["sharing", "quest", "acorn", "star", "pearl", "squirrel", "rabbit", "owl"]

def generation_prompts(world: World) -> list[str]:
    q = world.quest
    c = world.companion_cfg
    hero = world.facts["hero"]
    return [
        f"Write a short folk tale about a {hero.type} named {hero.id} who goes on a "
        f"quest to {q.verb} and meets a {c.type} in need.",
        f"Tell a gentle story where a {hero.type} finds something dear but learns "
        f"that sharing brings true happiness.",
        f"Create a folk tale for young children about kindness, using the words "
        f"'dear' and '{q.noun_label}'.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    q = world.quest
    setting = world.setting
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    comp_sub = comp.pronoun("subject")
    qa = [
        QAItem(
            question=f"Who is the hero in the folk tale set in {setting.place}?",
            answer=f"The hero is a {hero.traits[0]} {hero.type} named {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} set out to do?",
            answer=f"{hero.id} went on a quest to {q.verb} in {setting.place}.",
        ),
        QAItem(
            question=f"Who did {hero.id} meet during the quest?",
            answer=f"{hero.id} met a {comp.type} named {comp.id} who was {world.companion.trait}.",
        ),
        QAItem(
            question=f"How did {hero.id} help {comp.id}?",
            answer=f"{hero.id} decided to share {q.noun_label} with {comp.id}. That made "
                   f"{comp.id} feel better, and they became dear friends.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {q.sharing_lesson}",
        ),
    ]
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.quest.id, world.companion.type, "sharing", "quest"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KINDNESS_FACTS[tag])
    return out

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for quest in QUESTS:
            for companion in COMPANIONS:
                # Always valid in this simple world – all combinations make sense.
                combos.append((place, quest, companion))
    return combos

# ---------------------------------------------------------------------------
# CLI / ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% All combinations are valid – no constraint needed for this simple folk tale domain.
valid_story(Place, Quest, Companion) :- setting(Place), quest(Quest), companion(Companion).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)

def asp_verify() -> int:
    import asp
    program = asp_facts() + "\n" + ASP_RULES + "\n#show valid_story/3."
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk Tale story world: a dear hero, a quest, and the gift of sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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

def resolve_params(args, rng):
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.companion:
        combos = [c for c in combos if c[2] == args.companion]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, quest, companion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = rng.choice(HERO_TRAITS)
    return StoryParams(place=place, quest=quest, companion=companion,
                       name=name, gender=gender, trait=trait)

def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    quest = QUESTS[params.quest]
    companion_cfg = COMPANIONS[params.companion]
    hero_type = params.gender
    world = tell(setting, quest, companion_cfg, params.name, hero_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- world model trace ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print("\n== Generation Prompts ==")
        for p in sample.prompts:
            print(f"  • {p}")
        print("\n== Story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}\n")
        print("\n== World Knowledge QA ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}\n")

def main():
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_facts() + "\n" + ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        program = asp_facts() + "\n" + ASP_RULES + "\n#show valid_story/3."
        model = asp.one_model(program)
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} valid stories:")
        for p, q, c in stories:
            print(f"  {p:8} {q:8} {c:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        combos = valid_combos()
        for place, quest, companion in combos:
            params = StoryParams(place=place, quest=quest, companion=companion,
                                 name=random.choice(HERO_NAMES),
                                 gender=random.choice(["girl", "boy"]),
                                 trait=random.choice(HERO_TRAITS))
            samples.append(generate(params))
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story not in [s.story for s in samples]:
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.name}: {sample.params.quest} at {sample.params.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
