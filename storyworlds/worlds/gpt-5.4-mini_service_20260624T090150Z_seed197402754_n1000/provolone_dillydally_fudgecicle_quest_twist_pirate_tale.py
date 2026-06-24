#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a crew quest, a delayed departure, and a twist
involving provolone and a fudgecicle.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    kind_tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "pirate"}
        female = {"girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    objective: str
    peril: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    fix: str
    helps: set[str]
    guards: set[str]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    twist: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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

    def pirates(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "dock": Setting(place="the windy dock", kind="dock", affords={"quest"}),
    "harbor": Setting(place="the harbor pier", kind="harbor", affords={"quest"}),
    "cave": Setting(place="the sea cave", kind="cave", affords={"quest"}),
}

QUESTS = {
    "treasure": Quest(
        id="treasure",
        verb="seek the hidden treasure",
        gerund="seeking hidden treasure",
        rush="dash to the map chest",
        objective="the hidden treasure map",
        peril="the tide could swallow the path",
        tags={"quest", "map"},
    ),
    "lantern": Quest(
        id="lantern",
        verb="find the lost lantern",
        gerund="hunting for the lost lantern",
        rush="rush toward the dark shelf",
        objective="the lost lantern",
        peril="the cave could go dark",
        tags={"quest", "lantern"},
    ),
    "shell": Quest(
        id="shell",
        verb="carry the shell to the captain",
        gerund="carrying the shell carefully",
        rush="hurry to the raft",
        objective="the shell for the captain",
        peril="a splash could spoil the prize",
        tags={"quest", "shell"},
    ),
}

PRIZES = {
    "provolone": Entity(id="provolone_cfg", type="food", label="provolone", phrase="a wedge of provolone", kind="thing"),
    "fudgecicle": Entity(id="fudgecicle_cfg", type="treat", label="fudgecicle", phrase="a cold fudgecicle", kind="thing"),
}

TWISTS = {
    "provolone": Twist(
        id="provolone",
        label="provolone",
        reveal="the cheese had been tucked inside the map chest all along",
        fix="they shared the provolone before the tide could touch it",
        helps={"quest"},
        guards={"melty"},
    ),
    "fudgecicle": Twist(
        id="fudgecicle",
        label="fudgecicle",
        reveal="the cold treat was not a prize at all, but a clue that led to the next cove",
        fix="they saved the fudgecicle in a shady bucket and followed the sticky trail",
        helps={"quest"},
        guards={"sticky"},
    ),
}


GIRL_NAMES = ["Mara", "Nina", "Tess", "Lina", "Rosa"]
BOY_NAMES = ["Finn", "Pax", "Jory", "Milo", "Rafe"]
TRAITS = ["brave", "curious", "cheery", "spry", "stubborn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a quest and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=["captain", "mom", "dad", "aunt"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    prize = args.prize or rng.choice(list(PRIZES))
    twist = args.twist or prize
    if prize != twist:
        raise StoryError("The twist must match the chosen prize in this small tale.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or rng.choice(["captain", "mom", "dad", "aunt"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, twist=twist, name=name, gender=gender, captain=captain, trait=trait)


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity]:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name, kind_tags={"pirate"}))
    captain = world.add(Entity(id="Captain", kind="character", type="pirate", label=f"the {params.captain}"))
    prize = world.add(Entity(id="Prize", kind="thing", type=params.prize, label=params.prize, phrase=PRIZES[params.prize].phrase))
    twist = world.add(Entity(id="Twist", kind="thing", type=params.twist, label=params.twist, phrase=TWISTS[params.twist].reveal))
    return hero, captain, prize, twist


def _narrate_setup(world: World, hero: Entity, captain: Entity, quest: Quest, prize: Entity) -> None:
    world.say(f"{hero.id} was a {hero.pronoun('subject') == 'they' and 'small' or 'little'} {hero.type} pirate who loved a good quest.")
    world.say(f"{hero.id} wanted to {quest.verb}, and the crew knew {quest.gerund} meant a fine day at sea.")
    world.say(f"{hero.id} also carried {prize.phrase} in a little satchel, because {prize.label} made the voyage feel lucky.")
    world.say(f"The {captain.label} watched the clouds and nodded at the map.")


def _dillydally(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["delay"] = hero.memes.get("delay", 0) + 1
    world.para()
    world.say(f"But {hero.id} began to dillydally by the dock, turning {prize.item_pronoun()} over and over in {hero.pronoun('possessive')} hands.")
    world.say(f"That slow pause made the crew tap their boots, because {quest.peril}.")


def _twist(world: World, hero: Entity, quest: Quest, prize: Entity, twist: Twist) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    world.para()
    if twist.id == "provolone":
        world.say(f"Then came the twist: {twist.reveal}.")
        world.say(f"The crew laughed, and {hero.id} stopped dillydallying at once, because {twist.fix}.")
        world.say(f"{hero.id} tucked the provolone safely away and hurried off to {quest.verb}.")
    else:
        world.say(f"Then came the twist: {twist.reveal}.")
        world.say(f"{hero.id} set the fudgecicle in a shady bucket, and the sweet drip pointed the way to the next cove.")
        world.say(f"So the crew followed the sticky trail and kept the quest moving.")


def _ending(world: World, hero: Entity, captain: Entity, quest: Quest, prize: Entity, twist: Twist) -> None:
    world.para()
    world.say(f"At last {hero.id} did {quest.gerund}, and the {captain.label} cheered.")
    world.say(f"By the end, the {prize.label} was safe, the ship was ready, and {hero.id} had learned not to dillydally when a quest was calling.")
    if twist.id == "provolone":
        world.say(f"The little wedge of provolone still smelled sharp and good in {hero.id}'s satchel.")
    else:
        world.say(f"The cool fudgecicle was gone, but the cove they found was better than any treat.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero, captain, prize, twist_ent = _setup(world, params)
    quest = QUESTS[params.quest]
    twist = TWISTS[params.twist]
    world.facts.update(hero=hero, captain=captain, prize=prize, twist=twist_ent, quest=quest, params=params)
    _narrate_setup(world, hero, captain, quest, prize)
    _dillydally(world, hero, quest, prize)
    _twist(world, hero, quest, prize, twist)
    _ending(world, hero, captain, quest, prize, twist)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    q = world.facts["quest"]
    return [
        f"Write a short pirate tale for a child where {p.name} must {q.verb} but keeps dillydallying.",
        f"Tell a sea story that includes provolone and a twist, with a cheerful pirate ending.",
        f"Write a gentle quest story in pirate style that uses the word fudgecicle and ends with a clear change.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    q: Quest = world.facts["quest"]
    prize: Entity = world.facts["prize"]
    twist: Entity = world.facts["twist"]
    return [
        QAItem(
            question=f"What did {p.name} keep doing instead of starting the quest?",
            answer=f"{p.name} kept dillydallying by the dock while the crew waited for {q.verb}."
        ),
        QAItem(
            question=f"What prize did {p.name} carry during the trip?",
            answer=f"{p.name} carried {prize.phrase} in a little satchel."
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was about {twist.label}, and it changed how the crew finished the quest."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does dillydally mean?", answer="Dillydally means to waste time or move too slowly when you should be getting started."),
        QAItem(question="What is provolone?", answer="Provolone is a kind of cheese with a sharp, salty taste."),
        QAItem(question="What is a fudgecicle?", answer="A fudgecicle is a frozen chocolate treat on a stick."),
        QAItem(question="What is a quest?", answer="A quest is a search or mission to find something important."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise change that makes the story turn in a new way."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
setting(dock). setting(harbor). setting(cave).
quest(treasure). quest(lantern). quest(shell).
prize(provolone). prize(fudgecicle).
twist(provolone). twist(fudgecicle).
valid(P,Q,R,T) :- setting(P), quest(Q), prize(R), twist(T), R = T.
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    parts = []
    for s in SETTINGS:
        parts.append(asp.fact("setting", s))
    for q in QUESTS:
        parts.append(asp.fact("quest", q))
    for p in PRIZES:
        parts.append(asp.fact("prize", p))
    for t in TWISTS:
        parts.append(asp.fact("twist", t))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(p, q, r, t) for p in SETTINGS for q in QUESTS for r in PRIZES for t in TWISTS if r == t}
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only asp:", sorted(asp_set - py_set))
    print("only python:", sorted(py_set - asp_set))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, q, r, t) for p in SETTINGS for q in QUESTS for r in PRIZES for t in TWISTS if r == t]


CURATED = [
    StoryParams(place="dock", quest="treasure", prize="provolone", twist="provolone", name="Mara", gender="girl", captain="captain", trait="curious"),
    StoryParams(place="harbor", quest="lantern", prize="fudgecicle", twist="fudgecicle", name="Finn", gender="boy", captain="dad", trait="brave"),
]


def resolve_rejection(args: argparse.Namespace) -> None:
    raise StoryError("This pirate tale only supports matching prize/twist pairs: provolone with provolone, fudgecicle with fudgecicle.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prize and args.twist and args.prize != args.twist:
        resolve_rejection(args)
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    prize = args.prize or rng.choice(list(PRIZES))
    twist = args.twist or prize
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or rng.choice(["captain", "mom", "dad", "aunt"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, twist=twist, name=name, gender=gender, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
