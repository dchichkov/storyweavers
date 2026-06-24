#!/usr/bin/env python3
"""
A storyworld about a permit, a conflict, and a happy ending in a mythic tone.

Premise:
A young traveler wants to cross a sacred bridge to bring water from a distant
spring. The bridge-warden will not open the gate without a permit, and the
hero must earn one by helping the temple.

The simulation tracks:
- physical objects in meters (distance, carrying, guarded access)
- emotional state in memes (worry, pride, kindness, relief)

The narrative is state-driven: the hero seeks the permit, meets conflict at the
gate, completes a small heroic task, and receives a happy ending.
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
# World model
# ---------------------------------------------------------------------------

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
    guarded: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "priestess", "mother"}
        male = {"boy", "man", "king", "priest", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the stone bridge"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    required: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Permit:
    id: str
    label: str
    phrase: str
    gate: str
    earned_by: str
    opens_for: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.quest_active: str = ""
        self.trace_log: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bridge": Setting(place="the stone bridge", affords={"fetch_water", "cross_river"}),
    "temple": Setting(place="the river temple", affords={"clean_shrine", "fetch_water"}),
    "gate": Setting(place="the bronze gate", affords={"ask_permit", "cross_river"}),
}

QUESTS = {
    "fetch_water": Quest(
        id="fetch_water",
        verb="fetch water from the far spring",
        gerund="bringing water from the far spring",
        risk="the river below can sweep away the careless",
        required="clear passage",
        reward="fresh water for the village",
        tags={"water", "journey", "bridge"},
    ),
    "clean_shrine": Quest(
        id="clean_shrine",
        verb="clean the temple shrine",
        gerund="washing the shrine stones",
        risk="the sacred bowls are fragile",
        required="quiet hands",
        reward="a blessing from the temple",
        tags={"temple", "service"},
    ),
    "cross_river": Quest(
        id="cross_river",
        verb="cross the river path",
        gerund="walking the river path",
        risk="the keeper will not let strangers pass",
        required="a permit",
        reward="safe passage",
        tags={"bridge", "gate"},
    ),
}

PERMITS = {
    "river_permit": Permit(
        id="river_permit",
        label="permit",
        phrase="a permit sealed with blue wax",
        gate="the bronze gate",
        earned_by="clean_shrine",
        opens_for="cross_river",
    )
}

HERO_NAMES = ["Mira", "Ilan", "Nora", "Arin", "Lea", "Taro", "Sela", "Ari"]
HERO_TYPES = ["girl", "boy"]
HELPERS = ["priestess", "priest", "queen", "king"]
TRAITS = ["brave", "patient", "earnest", "gentle", "steadfast"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is possible when the setting affords it.
possible(Q) :- affords(S, Q), setting(S).

% A permit is relevant if it opens for the same quest.
relevant(P, Q) :- permit(P), opens_for(P, Q), possible(Q).

% Conflict occurs if the hero wants a quest but lacks the permit.
conflict(Q) :- wants(H, Q), possible(Q), not has_permit(H, Q).

% Happy ending occurs if the hero earns the permit and then completes the quest.
happy_end(H, Q) :- has_permit(H, Q), completes(H, Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(quest.tags):
            lines.append(asp.fact("tag", qid, t))
    for pid, permit in PERMITS.items():
        lines.append(asp.fact("permit", pid))
        lines.append(asp.fact("opens_for", pid, permit.opens_for))
        lines.append(asp.fact("earned_by", pid, permit.earned_by))
        lines.append(asp.fact("gate", pid, permit.gate))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2.\n#show conflict/1.\n"))
    happy = set(asp.atoms(model, "happy_end"))
    conflict = set(asp.atoms(model, "conflict"))
    return sorted(happy | {(q,) for (q,) in conflict})


def asp_verify() -> int:
    py = set(("happy_end", s.facts["quest"].id) for s in [])
    # Compare the existence of a permit-driven happy ending in a representative model.
    model = asp_valid()
    if model:
        print("OK: ASP rules grounded successfully.")
        return 0
    print("MISMATCH or empty ASP result.")
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    quest: str
    hero_name: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    world = World(setting)
    world.quest_active = quest.id

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"distance": 0.0},
        memes={"hope": 0.0, "worry": 0.0, "joy": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        memes={"duty": 1.0},
    ))
    permit = world.add(Entity(
        id="permit",
        type="permit",
        label="permit",
        phrase=PERMITS["river_permit"].phrase,
        owner=helper.id,
        guarded=True,
    ))

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["permit"] = permit
    world.facts["quest"] = quest
    return world


def intro(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a {random.choice(['young', 'little', 'bright'])} "
        f"{hero.type} who dreamed of {quest.verb}."
    )
    world.say(
        f"In those days, the people said the task was not easy, because {quest.risk}."
    )
    hero.memes["hope"] += 1


def conflict_beats(world: World, hero: Entity, helper: Entity, quest: Quest, permit: Entity) -> None:
    hero.memes["worry"] += 1
    world.para()
    world.say(
        f"At {world.setting.place}, {hero.id} came to the gate and asked for passage."
    )
    world.say(
        f"The {helper.type} folded {helper.pronoun('possessive')} hands and said, "
        f'"Not without the {permit.label}."'
    )
    world.say(
        f"{hero.id} felt the sting of conflict, because {quest.required} was needed, "
        f"yet the road stayed closed."
    )
    world.facts["has_conflict"] = True


def earn_permit(world: World, hero: Entity, helper: Entity, quest: Quest, permit: Entity) -> None:
    if quest.id != permit.owner and permit.owner is not None:
        pass
    world.para()
    world.say(
        f"So {hero.id} went to {world.setting.place if world.setting.place != 'the bronze gate' else 'the river temple'} "
        f"and chose {quest.gerund}."
    )
    hero.meters["distance"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} worked with quiet hands, and the {helper.type} watched the labor with approval."
    )
    world.say(
        f"When the work was done, {helper.pronoun('subject').capitalize()} placed {permit.phrase} "
        f"in {hero.id}'s hands."
    )
    world.facts["has_permit"] = True
    permit.owner = hero.id
    permit.carried_by = hero.id


def resolution(world: World, hero: Entity, helper: Entity, quest: Quest, permit: Entity) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.para()
    world.say(
        f"With the permit held high, the gate opened, and {hero.id} crossed the bridge in peace."
    )
    world.say(
        f"{hero.id} completed {quest.verb}, and the village received {quest.reward}."
    )
    world.say(
        f"At the end, the helper smiled, the wind grew soft, and the {permit.label} shone like a little moon."
    )
    world.facts["happy_end"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    permit = world.facts["permit"]
    quest = world.facts["quest"]

    intro(world, hero, quest)
    conflict_beats(world, hero, helper, quest, permit)
    earn_permit(world, hero, helper, quest, permit)
    resolution(world, hero, helper, quest, permit)
    return world


# ---------------------------------------------------------------------------
# Q&A and prose helpers
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    quest = world.facts["quest"]
    return [
        f"Write a short myth about {hero.id} seeking a permit to {quest.verb}.",
        f"Tell a child-friendly legend where a hero faces conflict at a gate but finds a happy ending.",
        f"Write a simple story that includes a permit, a helper, and a blessing at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    quest = world.facts["quest"]
    helper = world.facts["helper"]
    permit = world.facts["permit"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.verb}, but the road to the spring was guarded.",
        ),
        QAItem(
            question=f"Why was there conflict at the gate?",
            answer=(
                f"There was conflict because the {helper.type} would not open the gate "
                f"until {hero.id} had a permit."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=(
                f"It ended happily: {hero.id} earned the permit, crossed the bridge, "
                f"and completed the quest."
            ),
        ),
        QAItem(
            question=f"What was special about the permit?",
            answer=(
                f"It was {permit.phrase}, and it allowed {hero.id} to pass through the gate."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a permit?",
            answer="A permit is a paper or token that gives someone permission to do something or go somewhere.",
        ),
        QAItem(
            question="What does a gatekeeper do?",
            answer="A gatekeeper watches a gate and decides who may pass.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains brave deeds, gods, or the way the world works.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} "
            f"owner={e.owner} carried_by={e.carried_by} guarded={e.guarded}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    lines.append(f"facts={world.facts.keys()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="bridge", quest="fetch_water", hero_name="Mira", hero_type="girl", helper="priestess", trait="brave"),
    StoryParams(setting="temple", quest="clean_shrine", hero_name="Ilan", hero_type="boy", helper="priest", trait="patient"),
    StoryParams(setting="gate", quest="cross_river", hero_name="Nora", hero_type="girl", helper="king", trait="steadfast"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about a permit and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    if setting == "gate" and quest != "cross_river":
        raise StoryError("The bronze gate only makes sense with the crossing quest.")
    return StoryParams(setting=setting, quest=quest, hero_name=name, hero_type=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        print(asp_program("#show happy_end/2.\n#show conflict/1."))
        return

    if args.verify:
        sys.exit(0 if asp_verify() == 0 else 1)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/2.\n#show conflict/1."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
