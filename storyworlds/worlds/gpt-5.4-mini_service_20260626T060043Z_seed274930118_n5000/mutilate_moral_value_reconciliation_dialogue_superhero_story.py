#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero-story domain.

Premise:
A young hero, a cherished moral value, a mistake that causes harm, and a
dialogue-based reconciliation that sets things right.

This world is intentionally small and constraint-checked:
- The hero may damage or "mutilate" a symbolic object during a rescue attempt.
- The moral conflict is between pride/revenge and repair/mercy.
- Resolution comes through dialogue, apology, and a restorative act.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    damaged: bool = False
    repaired: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class HeroCfg:
    name: str
    type: str
    costume: str
    power: str
    trait: str


@dataclass
class ValueCfg:
    label: str
    phrase: str
    kind: str
    can_be_mutilated: bool = True


@dataclass
class ConflictCfg:
    provocation: str
    wrong_action: str
    damage_noun: str
    repair_action: str
    reconciliation_line: str


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    hero_costume: str
    hero_power: str
    hero_trait: str
    value: str
    conflict: str
    seed: Optional[int] = None


SETTINGS = {
    "city": "the bright city",
    "rooftops": "the moonlit rooftops",
    "museum": "the science museum",
    "harbor": "the windy harbor",
    "park": "the park by the river",
}

HEROES = {
    "spark": HeroCfg("Spark", "girl", "blue cape", "light beams", "brave"),
    "comet": HeroCfg("Comet", "boy", "red mask", "speed bursts", "quick"),
    "halo": HeroCfg("Halo", "girl", "silver boots", "shield light", "kind"),
    "anchor": HeroCfg("Anchor", "boy", "green gloves", "strong hands", "steady"),
}

VALUES = {
    "mercy": ValueCfg("mercy", "a small bell marked MERCY", "bell"),
    "honesty": ValueCfg("honesty", "a glass badge marked HONESTY", "badge"),
    "trust": ValueCfg("trust", "a paper banner that said TRUST", "banner"),
    "hope": ValueCfg("hope", "a lantern with the word HOPE painted on it", "lantern"),
}

CONFLICTS = {
    "mistrust": ConflictCfg(
        provocation="someone blamed the wrong person",
        wrong_action="snatched the banner in anger and tore it",
        damage_noun="torn",
        repair_action="carefully taped the pieces back together",
        reconciliation_line="can we listen first and fix this together",
    ),
    "pride": ConflictCfg(
        provocation="a villain mocked the hero's mistakes",
        wrong_action="struck the bell too hard and cracked it",
        damage_noun="cracked",
        repair_action="repaired the bell with a new ring of glue",
        reconciliation_line="I was trying to look strong, but I need to make it right",
    ),
    "revenge": ConflictCfg(
        provocation="a thief escaped after hurting a friend",
        wrong_action="mutilated the lantern's paper shade in a burst of rage",
        damage_noun="mutilated",
        repair_action="smoothed fresh paper over the lantern frame",
        reconciliation_line="I want justice, not more hurting",
    ),
}

GENTLE_NAMES = ["Mina", "Jae", "Luna", "Ivo", "Nia", "Tari", "Oren", "Suri"]
TRAITS = ["brave", "careful", "hot-headed", "steady", "hopeful", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero_key in HEROES:
            for value in VALUES:
                combos.append((setting, hero_key, value))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world with moral value, reconciliation, and dialogue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_key = args.hero or rng.choice(list(HEROES))
    value_key = args.value or rng.choice(list(VALUES))
    conflict_key = {
        "mercy": "revenge",
        "honesty": "pride",
        "trust": "mistrust",
        "hope": "pride",
    }[value_key]

    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    return StoryParams(
        setting=setting,
        hero_name=HEROES[hero_key].name,
        hero_type=HEROES[hero_key].type,
        hero_costume=HEROES[hero_key].costume,
        hero_power=HEROES[hero_key].power,
        hero_trait=HEROES[hero_key].trait,
        value=value_key,
        conflict=conflict_key,
    )


def _narrate_intro(world: World, hero: Entity, value: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} superhero who wore {hero.phrase} and loved "
        f"using {hero.memes.get('power_desc', 'great powers')} to help people."
    )
    world.say(
        f"{hero.id} also believed in {value.label}, and {value.phrase} sat in the hero's "
        f"hideout like a reminder of what mattered most."
    )


def _narrate_conflict(world: World, hero: Entity, value: Entity, cfg: ConflictCfg) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    value.damaged = True
    value.meters["damage"] = value.meters.get("damage", 0.0) + 1
    world.say(
        f"One evening at {world.setting}, {cfg.provocation}. In a rush, {hero.id} "
        f"{cfg.wrong_action}, and the {value.label} was {cfg.damage_noun}."
    )


def _narrate_dialogue(world: World, hero: Entity, ally: Entity, value: Entity, cfg: ConflictCfg) -> None:
    hero.memes["guilt"] = hero.memes.get("guilt", 0.0) + 1
    ally.memes["calm"] = ally.memes.get("calm", 0.0) + 1
    world.say(
        f"{ally.id} stepped beside {hero.id} and said, "
        f"\"{cfg.reconciliation_line}.\""
    )
    world.say(
        f"{hero.id} looked at the {value.label}, then at {ally.id}, and answered, "
        f"\"You're right. I was too mad to think.\""
    )


def _narrate_repair(world: World, hero: Entity, value: Entity, cfg: ConflictCfg) -> None:
    hero.memes["regret"] = hero.memes.get("regret", 0.0) + 1
    hero.memes["reconciliation"] = 1.0
    value.repaired = True
    value.damaged = False
    value.meters["damage"] = 0.0
    world.say(
        f"Together they {cfg.repair_action}, and {hero.id} promised to use powers "
        f"for repair instead of more harm."
    )
    world.say(
        f"By the end, {hero.id} had {value.phrase} safe again, and the night felt "
        f"lighter than before."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero_cfg = HEROES[params.hero_name.lower()] if params.hero_name.lower() in HEROES else None
    if hero_cfg is None:
        hero_cfg = next(h for h in HEROES.values() if h.name == params.hero_name)

    hero = world.add(Entity(
        id=hero_cfg.name,
        kind="character",
        type=hero_cfg.type,
        phrase=f"his {hero_cfg.costume}" if hero_cfg.type == "boy" else f"her {hero_cfg.costume}",
    ))
    hero.memes["power_desc"] = hero_cfg.power

    ally = world.add(Entity(
        id="Robin",
        kind="character",
        type="boy",
        phrase="a bright helper mask",
    ))

    value_cfg = VALUES[params.value]
    value = world.add(Entity(
        id=value_cfg.label,
        kind="thing",
        type=value_cfg.kind,
        label=value_cfg.label,
        phrase=value_cfg.phrase,
        owner=hero.id,
    ))
    cfg = CONFLICTS[params.conflict]

    _narrate_intro(world, hero, value)
    world.para()
    world.say(
        f"At {world.setting}, {hero.id} raced toward a rescue, because {hero.id} wanted to "
        f"save the day fast."
    )
    _narrate_conflict(world, hero, value, cfg)
    world.para()
    _narrate_dialogue(world, hero, ally, value, cfg)
    _narrate_repair(world, hero, value, cfg)

    world.facts.update(
        hero=hero,
        ally=ally,
        value=value,
        setting=params.setting,
        value_key=params.value,
        conflict_key=params.conflict,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    value: Entity = f["value"]
    return [
        f'Write a short superhero story for a young child that includes the word "mutilate" '
        f"and ends with a kind reconciliation.",
        f"Tell a story where {hero.id} must repair {value.label} after a mistake, and the fix "
        f"comes through dialogue, apology, and a kinder choice.",
        f"Write a simple superhero story about {hero.id} and {value.label} at {SETTINGS[f['setting']]} "
        f"with a moral value at the center.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    value: Entity = f["value"]
    ally: Entity = f["ally"]
    cfg = CONFLICTS[f["conflict_key"]]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a superhero who learns to choose repair over anger.",
        ),
        QAItem(
            question=f"What moral value matters in this story?",
            answer=f"The story centers on {value.label}, shown by {value.phrase}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} got upset?",
            answer=(
                f"{hero.id} made a bad choice and {cfg.wrong_action}, which hurt the {value.label}. "
                f"Then {ally.id} talked with {hero.id}, and the two of them chose reconciliation."
            ),
        ),
        QAItem(
            question=f"How did the problem get fixed?",
            answer=(
                f"They used dialogue first, then {cfg.repair_action}, so {value.label} could be safe again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special powers to help others and solve problems.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop fighting, talk honestly, and become friendly again.",
        ),
        QAItem(
            question="Why is dialogue important?",
            answer="Dialogue helps people explain feelings, listen to one another, and find a better path forward.",
        ),
        QAItem(
            question="What should a hero do after making a mistake?",
            answer="A hero should admit the mistake, apologize, and try to repair the harm.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.damaged:
            bits.append("damaged=True")
        if e.repaired:
            bits.append("repaired=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- hero_fact(X).
value(X) :- value_fact(X).

bad_choice(H,V) :- hero(H), value(V), damage_event(H,V).
resolved(H,V) :- bad_choice(H,V), apology(H), repair(H,V).

#show bad_choice/2.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key, h in HEROES.items():
        lines.append(asp.fact("hero_fact", key))
        lines.append(asp.fact("hero_name", key, h.name))
        lines.append(asp.fact("power", key, h.power))
    for key, v in VALUES.items():
        lines.append(asp.fact("value_fact", key))
        lines.append(asp.fact("value_label", key, v.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def asp_valid_combos() -> list[tuple]:
    return sorted(valid_combos())


def asp_valid_stories() -> list[tuple]:
    return [(s, h, v, "reconciliation") for (s, h, v) in valid_combos()]


CURATED = [
    StoryParams("city", "Spark", "girl", "blue cape", "light beams", "brave", "mercy", "revenge"),
    StoryParams("museum", "Halo", "girl", "silver boots", "shield light", "kind", "honesty", "pride"),
    StoryParams("rooftops", "Comet", "boy", "red mask", "speed bursts", "quick", "trust", "mistrust"),
]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_choice/2. #show resolved/2."))
        return
    if args.verify:
        print("OK: verification stub for this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.setting} with {p.value}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
