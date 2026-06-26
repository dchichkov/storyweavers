#!/usr/bin/env python3
"""
storyworlds/worlds/cud_whip_twist_repetition_cautionary_myth.py
===============================================================

A small myth-style storyworld about a creature that chews cud, a whip,
and a cautionary twist that repeats like an old warning.

Premise seed:
- A calm grazer chews cud beside a shepherd's path.
- A whip appears as a threat or tool.
- The story turns on a repeated warning and a twist: force startles,
  but care, patience, and a wiser path keep the creature safe.

This world is designed to stay child-facing, concrete, and state-driven.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"danger": 0.0, "tired": 0.0, "safe": 0.0, "hurt": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "trust": 0.0, "worry": 0.0, "caution": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "shepherd"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the stone hillside"
    feature: str = "gray grass"
    affords: set[str] = field(default_factory=lambda: {"chew", "walk", "warn"})


@dataclass
class Creature:
    type: str
    label: str
    phrase: str
    voice: str
    age: str = "young"


@dataclass
class Threat:
    id: str
    label: str
    phrase: str
    danger_kind: str
    noise: str
    is_symbolic: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    soft: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.story_marks: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.story_marks = list(self.story_marks)
        return c


@dataclass
class StoryParams:
    place: str
    creature: str
    threat: str
    tool: str
    name: str
    keeper: str
    seed: Optional[int] = None


SETTINGS = {
    "hillside": Setting(place="the stone hillside", feature="gray grass"),
    "valley": Setting(place="the green valley", feature="tall reeds"),
    "barnyard": Setting(place="the old barnyard", feature="dusty straw", affords={"chew", "walk", "warn", "hide"}),
}

CREATURES = {
    "calf": Creature(type="calf", label="calf", phrase="a small brown calf", voice="soft lowing"),
    "goat": Creature(type="goat", label="goat", phrase="a bright-eyed goat", voice="thin bleating"),
    "lamb": Creature(type="lamb", label="lamb", phrase="a white lamb", voice="soft baaing"),
}

THREATS = {
    "whip": Threat(id="whip", label="whip", phrase="a long whip", danger_kind="sharp fear", noise="crack", is_symbolic=False),
    "thunder": Threat(id="thunder", label="thunder", phrase="a rolling thunderclap", danger_kind="loud fear", noise="boom", is_symbolic=True),
}

TOOLS = {
    "cloak": Tool(id="cloak", label="cloak", phrase="a wool cloak", purpose="cover and calm", soft=True),
    "branch": Tool(id="branch", label="branch", phrase="a green branch", purpose="offer shade and a quiet sign", soft=True),
    "bell": Tool(id="bell", label="bell", phrase="a small bell", purpose="call the keeper home", soft=True),
}

NAMES = ["Mira", "Tala", "Niko", "Pella", "Orin", "Sera", "Bram", "Eli", "Ivo", "Rhea"]


def valid_story(creature: Creature, threat: Threat, tool: Tool) -> bool:
    if threat.id == "whip" and not tool.soft:
        return False
    return True


def reason_rejection(creature: Creature, threat: Threat, tool: Tool) -> str:
    return (
        f"(No story: this myth needs a soft answer to {threat.label}. "
        f"The chosen tool does not change the danger in a believable way.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about cud, whip, caution, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--keeper")
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
    place = args.place or rng.choice(list(SETTINGS))
    creature = args.creature or rng.choice(list(CREATURES))
    threat = args.threat or rng.choice(list(THREATS))
    tool = args.tool or rng.choice(list(TOOLS))

    if not valid_story(CREATURES[creature], THREATS[threat], TOOLS[tool]):
        raise StoryError(reason_rejection(CREATURES[creature], THREATS[threat], TOOLS[tool]))

    name = args.name or rng.choice(NAMES)
    keeper = args.keeper or rng.choice(["shepherd", "guardian", "herder"])
    return StoryParams(place=place, creature=creature, threat=threat, tool=tool, name=name, keeper=keeper)


def _risk_score(creature: Entity, threat: Threat) -> float:
    return creature.memes["caution"] + (1.0 if threat.id == "whip" else 0.5)


def predict(world: World, creature: Entity, threat: Threat) -> dict:
    sim = world.copy()
    c = sim.get(creature.id)
    c.memes["fear"] += 1
    c.meters["danger"] += 1
    if threat.id == "whip":
        c.memes["worry"] += 1
    return {"afraid": c.memes["fear"] >= THRESHOLD, "danger": c.meters["danger"] >= THRESHOLD}


def introduce(world: World, hero: Entity, creature: Creature) -> None:
    world.say(
        f"On {world.setting.place}, there lived {hero.pronoun('possessive')} "
        f"{creature.phrase} named {hero.id}."
    )
    world.say(
        f"{hero.id} loved to chew cud in the long, quiet hours, when the grass was "
        f"still and the sky looked old and kind."
    )


def speak_of_cud(world: World, hero: Entity) -> None:
    hero.meters["safe"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"Each time {hero.id} chewed cud, {hero.pronoun('subject')} grew calmer, "
        f"as if the slow chewing were a small prayer."
    )


def bring_threat(world: World, hero: Entity, threat: Threat) -> None:
    hero.meters["danger"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"Then someone came with {threat.phrase}, and the air seemed to snap when "
        f"it made its {threat.noise}."
    )


def caution(world: World, keeper: Entity, hero: Entity, threat: Threat) -> None:
    hero.memes["caution"] += 1
    world.say(
        f"{keeper.id} raised {keeper.pronoun('possessive')} hand and said, "
        f'"A whip is not a lesson for a living heart. Go softly."'
    )
    world.say(
        f"{keeper.id} said it once, then again, because old myths remember the same warning twice."
    )


def twist(world: World, hero: Entity, keeper: Entity, threat: Threat, tool: Tool) -> None:
    if threat.id == "whip":
        hero.memes["fear"] += 1
        if tool.id == "cloak":
            world.say(
                f"The twist was this: the whip was lifted, but {keeper.id} put a wool cloak "
                f"between fear and skin."
            )
        elif tool.id == "branch":
            world.say(
                f"The twist was this: the whip was lifted, but {keeper.id} held up a green branch "
                f"and stepped between them."
            )
        else:
            world.say(
                f"The twist was this: the whip was lifted, yet {keeper.id} rang a small bell, "
                f"calling the calmer way back."
            )
    else:
        world.say(
            f"The twist was this: the thunder rolled, but it only frightened the ears, not the body."
        )


def repetition(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} listened, chewed cud, listened again, and chewed cud again, "
        f"like a creature that had learned to wait for wisdom."
    )


def resolve(world: World, hero: Entity, keeper: Entity, threat: Threat, tool: Tool) -> None:
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["relief"] += 1
    hero.meters["safe"] += 1
    world.say(
        f"At last, the rough moment passed. {keeper.id} kept {tool.phrase} between them, "
        f"and {hero.id} stood still until the fear dropped away."
    )
    world.say(
        f"In the end, {hero.id} was still chewing cud under the wide sky, and the whip had become "
        f"a warning no one wanted to repeat."
    )


def tell(setting: Setting, creature: Creature, threat: Threat, tool: Tool, name: str, keeper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=creature.type, label=creature.label, phrase=creature.phrase))
    keeper = world.add(Entity(id=keeper_type, kind="character", type=keeper_type, label=keeper_type))
    world.facts.update(hero=hero, keeper=keeper, creature=creature, threat=threat, tool=tool, setting=setting)

    introduce(world, hero, creature)
    speak_of_cud(world, hero)
    world.para()
    bring_threat(world, hero, threat)
    caution(world, keeper, hero, threat)
    repetition(world, hero)
    world.para()
    twist(world, hero, keeper, threat, tool)
    resolve(world, hero, keeper, threat, tool)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child about {f["hero"].id}, cud, and {f["threat"].label}.',
        f"Tell a cautionary tale where a {f['creature'].label} learns to stay calm when {f['threat'].label} appears.",
        f'Write a simple story that repeats the warning "go softly" and ends with safety beside the hill.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, keeper, creature, threat, tool = f["hero"], f["keeper"], f["creature"], f["threat"], f["tool"]
    return [
        QAItem(
            question=f"What kind of creature was {hero.id} in the myth?",
            answer=f"{hero.id} was {creature.phrase}, a young {creature.label} who liked to chew cud on the hillside.",
        ),
        QAItem(
            question=f"Why did {keeper.id} warn {hero.id} about {threat.label}?",
            answer=f"{keeper.id} warned {hero.id} because {threat.phrase} could frighten a living heart, and the tale wanted caution instead of harm.",
        ),
        QAItem(
            question=f"What repeated action helped {hero.id} stay calm?",
            answer=f"{hero.id} chewed cud, listened, and chewed cud again, which made the creature calmer and steadier.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the threatening moment did not end with injury; {keeper.id} used {tool.phrase} and a gentler choice to keep {hero.id} safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} safe on {world.setting.place}, still chewing cud, while the old warning stayed in memory.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is cud?",
        answer="Cud is food that some animals chew, swallow, and chew again, like cows and calves do when they rest.",
    ),
    QAItem(
        question="What is a whip?",
        answer="A whip is a long strip of leather or cord that can crack loudly, but it should not be used to hurt animals.",
    ),
    QAItem(
        question="Why do people repeat warnings in stories?",
        answer="People repeat warnings so the listener remembers them, especially when the warning is important.",
    ),
    QAItem(
        question="What does caution mean?",
        answer="Caution means being careful and thinking before acting so nobody gets hurt.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  marks: {world.story_marks}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
entity(hero).
entity(keeper).
danger(whip).
cautionary(whip).
repetition(cud).
twist(soft_answer).

safe_story(H) :- entity(H), repetition(cud), cautionary(whip), twist(soft_answer).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/1."))
    ok = bool(asp.atoms(model, "safe_story"))
    if ok:
        print("OK: ASP twin produces a safe_story model.")
        return 0
    print("MISMATCH: ASP twin failed to produce a safe_story model.")
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="hillside", creature="calf", threat="whip", tool="cloak", name="Mira", keeper="shepherd"),
        StoryParams(place="valley", creature="goat", threat="whip", tool="branch", name="Tala", keeper="guardian"),
        StoryParams(place="barnyard", creature="lamb", threat="thunder", tool="bell", name="Rhea", keeper="herder"),
    ]


CURATED = build_curated()


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CREATURES[params.creature],
        THREATS[params.threat],
        TOOLS[params.tool],
        params.name,
        params.keeper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(asp_program("#show safe_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe_story/1."))
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.creature} with {p.threat} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
