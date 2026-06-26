#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shrine_select_significant_quest_ghost_story.py
===============================================================================================================

A small ghost-story world about a shrine, a careful selection, and one
significant quest.

Seed-tale premise:
---
A quiet child named Nia follows a pale glow to an old shrine in the woods.
There, a friendly ghost guards three offerings. Only one offering can begin the
significant quest: the one that belongs at the shrine. Nia has to look closely,
listen to the ghost, and select the right token before night grows darker.

World model:
---
- The shrine has an atmosphere meter that deepens with dusk.
- Offerings have significance and fit with one quest.
- The ghost's calm or worry changes with Nia's choice.
- A correct selection completes the quest and leaves the shrine peaceful.
- A wrong selection raises the shrine's unease and forces a do-over.

The prose is driven by the simulated state, not by a frozen paragraph template.
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
    placed_at: Optional[str] = None
    selected: bool = False
    revealed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def get(self, key: str, default: float = 0.0) -> float:
        return self.meters.get(key, default)

    def feel(self, key: str, default: float = 0.0) -> float:
        return self.memes.get(key, default)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Shrine:
    name: str = "the shrine"
    dusk: float = 0.0
    hush: float = 0.0
    peace: float = 0.0
    unease: float = 0.0
    lit: bool = False
    blessing: str = "soft"

    def is_dark(self) -> bool:
        return self.dusk >= 1.0 and not self.lit


@dataclass
class Quest:
    id: str
    title: str
    clue: str
    right_item: str
    ending: str
    danger: str
    significance: str
    place_hint: str = "the shrine"


@dataclass
class World:
    shrine: Shrine
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        return World(
            shrine=copy.deepcopy(self.shrine),
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
            paragraphs=[[]],
            trace_log=list(self.trace_log),
        )


QUESTS = {
    "lantern": Quest(
        id="lantern",
        title="the lantern quest",
        clue="The ghost points to a lamp with a moon on its glass.",
        right_item="lantern",
        ending="the path glowed all the way to the shrine gate",
        danger="the shrine path would stay shadowy",
        significance="It lights the way for visitors who come with kind intentions.",
    ),
    "ribbon": Quest(
        id="ribbon",
        title="the ribbon quest",
        clue="The ghost whispers that a ribbon tied to cedar branches will be enough.",
        right_item="ribbon",
        ending="the knot held steady in the wind",
        danger="the offerings would blow loose in the dark",
        significance="It marks a wish so the shrine can remember it.",
    ),
    "bowl": Quest(
        id="bowl",
        title="the bowl quest",
        clue="The ghost nods toward a small bowl used for water and flowers.",
        right_item="bowl",
        ending="the water stayed still and bright",
        danger="the shrine would have no calm place for the blessing",
        significance="It carries water that keeps the shrine gentle.",
    ),
}

SETTINGS = {
    "woodland": {"place": "the old shrine in the woods", "dusk": True},
    "hill": {"place": "the hilltop shrine", "dusk": True},
    "garden": {"place": "the garden shrine", "dusk": False},
}

HERO_NAMES = ["Nia", "Mina", "Tori", "Kira", "Lumi", "Sora"]
GHOST_NAMES = ["Wisp", "Morrow", "Pale Friend", "Sable", "Murmur"]
TRAITS = ["careful", "quiet", "brave", "curious", "gentle"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    hero_name: str
    hero_trait: str
    ghost_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost story world: a child, a shrine, a significant quest, and a choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--ghost", choices=GHOST_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    hero_trait = args.trait or rng.choice(TRAITS)
    ghost_name = args.ghost or rng.choice(GHOST_NAMES)
    return StoryParams(
        setting=setting,
        quest=quest,
        hero_name=hero_name,
        hero_trait=hero_trait,
        ghost_name=ghost_name,
    )


def _intro(world: World, hero: Entity, ghost: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a {hero.feel('trait_word', 0) or hero.type} child who liked quiet places."
    )
    world.say(
        f"One evening, {hero.id} followed a pale glow to {world.shrine.name}, where {ghost.id} waited."
    )
    world.say(
        f"{ghost.id} guarded a significant quest: {quest.title}. {quest.significance}"
    )


def _atmosphere(world: World, hero: Entity, ghost: Entity, quest: Quest) -> None:
    if world.shrine.is_dark():
        world.say(
            f"The air under the trees felt very still, and {world.shrine.name} was getting dark."
        )
    else:
        world.say(f"The light was soft at {world.shrine.name}, and the stones looked warm.")
    world.say(f"{ghost.id} lifted a finger and said, \"{quest.clue}\"")
    world.say(
        f"{hero.id} looked at the three offerings and tried to select the one that belonged to the shrine."
    )


def _choose(world: World, hero: Entity, ghost: Entity, quest: Quest, choice: str) -> None:
    if choice not in world.entities:
        raise StoryError("The story tried to select an offering that does not exist.")
    item = world.get(choice)
    if item.selected:
        raise StoryError("That offering was already selected.")
    item.selected = True
    hero.meters["attention"] = hero.get("attention") + 1
    if item.type == quest.right_item:
        item.revealed = True
        world.shrine.peace += 1.0
        world.shrine.hush += 1.0
        world.shrine.lit = True
        ghost.memes["relief"] = ghost.feel("relief") + 1.0
        hero.memes["courage"] = hero.feel("courage") + 1.0
        world.facts["success"] = True
        world.say(
            f"{hero.id} selected the {item.label}, and {ghost.id} gave a tiny nod."
        )
        world.say(
            f"At once, {quest.ending}, and {ghost.id} smiled like a lantern in fog."
        )
    else:
        world.shrine.unease += 1.0
        world.shrine.dusk += 0.4
        ghost.memes["worry"] = ghost.feel("worry") + 1.0
        world.facts["success"] = False
        world.facts["wrong_choice"] = item.id
        world.say(
            f"{hero.id} selected the {item.label}, but {ghost.id}'s face went dim."
        )
        world.say(
            f"That was not the right offering, so {quest.danger}."
        )


def _repair(world: World, hero: Entity, ghost: Entity, quest: Quest) -> None:
    if world.facts.get("success"):
        return
    right = world.get(quest.right_item)
    right.selected = True
    right.revealed = True
    world.shrine.unease = max(0.0, world.shrine.unease - 1.0)
    world.shrine.peace += 1.0
    world.shrine.lit = True
    ghost.memes["relief"] = ghost.feel("relief") + 1.0
    hero.memes["understanding"] = hero.feel("understanding") + 1.0
    world.say(
        f"{hero.id} looked again, listened more carefully, and then selected the {right.label}."
    )
    world.say(
        f"This time {ghost.id} looked bright, because {quest.ending}."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    shrine = Shrine(name=setting["place"], dusk=1.0 if setting["dusk"] else 0.4)
    world = World(shrine=shrine)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="girl" if params.hero_name in {"Nia", "Mina", "Kira", "Lumi"} else "boy",
        label=params.hero_name,
    ))
    hero.meters["attention"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["understanding"] = 0.0
    hero.memes["trait_word"] = 0.0

    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type="ghost",
        label=params.ghost_name,
    ))
    quest = QUESTS[params.quest]
    world.facts["quest"] = quest

    offerings = [
        ("lantern", "lantern", "a small brass lantern"),
        ("ribbon", "ribbon", "a red ribbon that fluttered like a bird"),
        ("bowl", "bowl", "a shallow bowl for water and flowers"),
    ]
    for oid, otype, phrase in offerings:
        world.add(Entity(id=oid, kind="thing", type=otype, label=otype, phrase=phrase))

    _intro(world, hero, ghost, quest)
    world.para()
    _atmosphere(world, hero, ghost, quest)
    _choose(world, hero, ghost, quest, quest.right_item)
    world.para()
    _repair(world, hero, ghost, quest)
    world.say(
        f"{hero.id} left the shrine feeling that the night had turned gentler than before."
    )

    world.facts.update(
        hero=hero,
        ghost=ghost,
        setting=params.setting,
        quest=quest.id,
        shrine=world.shrine,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    q: Quest = world.facts["quest_obj"]
    hero: Entity = world.facts["hero"]
    ghost: Entity = world.facts["ghost"]
    return [
        f'Write a child-friendly ghost story about a shrine, a significant quest, and the word "{q.id}".',
        f"Tell a gentle story where {hero.id} meets {ghost.id} at a shrine and has to select the right item.",
        f"Write a short eerie-but-kind story that ends with {q.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q: Quest = QUESTS[world.facts["quest"]]
    hero: Entity = world.facts["hero"]
    ghost: Entity = world.facts["ghost"]
    setting = SETTINGS[world.facts["setting"]]["place"]
    success = world.facts.get("success", False)

    qa = [
        QAItem(
            question=f"Where did {hero.id} go to meet {ghost.id}?",
            answer=f"{hero.id} went to {setting}, where {ghost.id} was waiting beside the shrine.",
        ),
        QAItem(
            question=f"What did {ghost.id} ask {hero.id} to do with the offerings?",
            answer=f"{ghost.id} asked {hero.id} to select the offering that matched the significant quest.",
        ),
        QAItem(
            question=f"Why was the quest significant?",
            answer=q.significance,
        ),
    ]
    if success:
        qa.append(
            QAItem(
                question=f"What happened after {hero.id} selected the right item?",
                answer=f"The shrine grew peaceful, {ghost.id} smiled, and {q.ending}.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"What did {hero.id} do after the first choice was wrong?",
                answer=f"{hero.id} looked again, listened more carefully, and selected the {q.right_item}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shrine?",
            answer="A shrine is a special place where people may leave offerings, remember someone, or feel close to a spirit or a memory.",
        ),
        QAItem(
            question="What does it mean to select something?",
            answer="To select something means to choose it carefully from a few choices.",
        ),
        QAItem(
            question="What does significant mean?",
            answer="Significant means important enough to matter a lot.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a task or search that someone does because it matters to them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(
        f"shrine: dusk={world.shrine.dusk:.1f} hush={world.shrine.hush:.1f} peace={world.shrine.peace:.1f} "
        f"unease={world.shrine.unease:.1f} lit={world.shrine.lit}"
    )
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes} selected={e.selected}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="woodland", quest="lantern", hero_name="Nia", hero_trait="careful", ghost_name="Wisp"),
    StoryParams(setting="hill", quest="ribbon", hero_name="Mina", hero_trait="curious", ghost_name="Morrow"),
    StoryParams(setting="garden", quest="bowl", hero_name="Lumi", hero_trait="gentle", ghost_name="Pale Friend"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("right_item", qid, q.right_item))
    for oid, _, _ in [("lantern", "lantern", ""), ("ribbon", "ribbon", ""), ("bowl", "bowl", "")]:
        lines.append(asp.fact("offering", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_choice(Q, O) :- quest(Q), right_item(Q, O).
significant_quest(Q) :- quest(Q), right_item(Q, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_choices() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_choice/2."))
    return sorted(set(asp.atoms(model, "valid_choice")))


def asp_verify() -> int:
    py = sorted((qid, q.right_item) for qid, q in QUESTS.items())
    cl = asp_valid_choices()
    if py == cl:
        print(f"OK: ASP gate matches Python reasonableness ({len(py)} choices).")
        return 0
    print("Mismatch between ASP and Python:")
    print("Python:", py)
    print("ASP   :", cl)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["quest_obj"] = QUESTS[params.quest]
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params_for_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        return CURATED
    params = resolve_params(args, rng)
    params.seed = args.seed
    return [params]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_choice/2."))
        return
    if args.asp:
        choices = asp_valid_choices()
        print(f"{len(choices)} valid quest choices:")
        for qid, item in choices:
            print(f"  {qid}: {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
