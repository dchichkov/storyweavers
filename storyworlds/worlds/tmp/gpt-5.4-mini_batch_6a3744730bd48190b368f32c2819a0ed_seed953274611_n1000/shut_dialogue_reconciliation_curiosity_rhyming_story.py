#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shut_dialogue_reconciliation_curiosity_rhyming_story.py
======================================================================================

A tiny storyworld about a child, a shut door, a curious question, and a rhyming
reconciliation. The world is built from state changes, dialogue, and a small
turning point: someone shuts something, someone gets curious, words are spoken,
and the two sides make up again.

This script is self-contained except for the shared result containers and the
shared ASP helper.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Thing:
    id: str
    label: str
    kind: str = "thing"
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    type: str = "place"
    doors: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    id: str
    label: str
    opening: str
    rhyming_line: str
    shut_object: str
    curiosity_object: str
    reconciliation_line: str
    ending_image: str
    music: str = "soft rhyme"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    scene: str
    actor: str
    actor_gender: str
    friend: str
    friend_gender: str
    parent: str
    parent_gender: str
    shut_object: str
    curiosity_object: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SCENES = {
    "garden_gate": Scene(
        id="garden_gate",
        label="the garden gate",
        opening="At the garden gate, the little day began to sway.",
        rhyming_line="One friend said, 'Let it shut!' and the latch went click-clack-clay.",
        shut_object="gate",
        curiosity_object="rosebush",
        reconciliation_line="They spoke in gentle tones, and both felt light as straw.",
        ending_image="The gate stood open wide, and they skipped through without a flaw.",
    ),
    "treehouse": Scene(
        id="treehouse",
        label="the treehouse stair",
        opening="Up the treehouse stair, the summer air was fair.",
        rhyming_line="One child said, 'Please shut the hatch!' and then they paused to stare.",
        shut_object="hatch",
        curiosity_object="bluebird nest",
        reconciliation_line="They asked one careful question, then shared a friendly grin.",
        ending_image="The hatch was open easy, and both went climbing in.",
    ),
    "toy_box": Scene(
        id="toy_box",
        label="the toy box lid",
        opening="By the toy box bright, the playroom hummed with light.",
        rhyming_line="One child said, 'Shut the lid!' and made the other blink at night.",
        shut_object="lid",
        curiosity_object="crayon tunnel",
        reconciliation_line="They wondered what was hidden, then talked it through with grace.",
        ending_image="The lid stayed half-open kindly, and smiles returned to place.",
    ),
}

SHUT_OBJECTS = {
    "gate": Thing(id="gate", label="gate"),
    "hatch": Thing(id="hatch", label="hatch"),
    "lid": Thing(id="lid", label="lid"),
}

CURIOSITY_OBJECTS = {
    "rosebush": Thing(id="rosebush", label="rosebush"),
    "bluebird nest": Thing(id="bluebird nest", label="bluebird nest"),
    "crayon tunnel": Thing(id="crayon tunnel", label="crayon tunnel"),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ivy", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Sam", "Noah"]
TRAITS = ["curious", "gentle", "bright", "cheerful", "thoughtful"]


def pronoun_for_gender(g: str, case: str = "subject") -> str:
    if g == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if g == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, o, c) for s in SCENES for o in SHUT_OBJECTS for c in CURIOSITY_OBJECTS]


def explain_rejection(scene: str, shut_object: str, curiosity_object: str) -> str:
    return f"(No story: scene={scene}, shut={shut_object}, curiosity={curiosity_object} is not a reasonableness problem in this world, but the explicit options did not match.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about shut things, curiosity, and making up.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--shut", choices=SHUT_OBJECTS)
    ap.add_argument("--curiosity", choices=CURIOSITY_OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.shut is None or c[1] == args.shut)
              and (args.curiosity is None or c[2] == args.curiosity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, shut_object, curiosity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene=scene, actor=name, actor_gender=gender, friend=friend, friend_gender=friend_gender, parent=parent, parent_gender=parent, shut_object=shut_object, curiosity_object=curiosity)


def _say_rhyme(world: World, scene: Scene, actor: Entity, friend: Entity, parent: Entity) -> None:
    world.say(scene.opening)
    world.say(f"{actor.id} and {friend.id} came near, with laughter soft and clear.")
    world.say(scene.rhyming_line)
    actor.memes["impulse"] += 1
    friend.memes["curiosity"] += 1
    world.say(f"{friend.id} peered at the {scene.curiosity_object} and asked, \"What's hiding here?\"")
    world.say(f"{actor.id} started to shut the {scene.shut_object}, but {friend.id} wanted near.")


def _tension(world: World, actor: Entity, friend: Entity, parent: Entity, scene: Scene) -> None:
    actor.memes["annoyed"] += 1
    friend.memes["curious"] += 1
    world.say(f"\"Wait,\" said {friend.id}, \"I only want a peek, a tiny little look.\"")
    world.say(f"\"No rough stuff,\" said {actor.id}, \"we can talk and not just book.\"")
    world.say(f"{parent.label_word.capitalize()} heard the hushed-up fuss and came with calm and care.")
    world.say(f"\"You may both ask questions first,\" {parent.id} said, \"and then decide what's there.\"")
    world.facts["shut_state"] = "almost"


def _reconcile(world: World, actor: Entity, friend: Entity, parent: Entity, scene: Scene) -> None:
    actor.memes["softness"] += 1
    friend.memes["relief"] += 1
    world.say(scene.reconciliation_line)
    world.say(f"{actor.id} said, \"I can be kind.\" {friend.id} said, \"I can wait.\"")
    world.say(f"{parent.id} smiled and showed them both how to pause and communicate.")
    world.say(f'Together they asked, "Can we shut it gently, then open it again?"')
    world.say(f"\"Yes,\" came the answer, \"that is a clever, friendly plan.\"")
    world.facts["reconciled"] = True
    world.facts["shut_state"] = "gentle"


def _ending(world: World, scene: Scene, actor: Entity, friend: Entity) -> None:
    actor.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(scene.ending_image)
    world.say(f"{actor.id} and {friend.id} walked away as pals again, feeling bright and small.")
    world.say("The shut-up moment was not the end at all; it helped them understand it all.")


def tell(params: StoryParams) -> World:
    world = World()
    scene = SCENES[params.scene]
    actor = world.add(Entity(id=params.actor, kind="character", type=params.actor_gender, role="actor", traits=["curious"]))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend", traits=["curious"]))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent_gender, role="parent", label=f"the {params.parent}"))
    world.add(SHUT_OBJECTS[params.shut_object])
    world.add(CURIOSITY_OBJECTS[params.curiosity_object])
    _say_rhyme(world, scene, actor, friend, parent)
    world.para()
    _tension(world, actor, friend, parent, scene)
    world.para()
    _reconcile(world, actor, friend, parent, scene)
    _ending(world, scene, actor, friend)
    world.facts.update(actor=actor, friend=friend, parent=parent, scene=scene, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    scene = world.facts["scene"]
    return [
        f"Write a short rhyming story for a young child about {p.actor} and {p.friend} near {scene.label}, where someone says shut and curiosity leads to a gentle conversation.",
        f"Tell a rhyme-filled story with dialogue, curiosity, and reconciliation, using the word shut and ending with {p.actor} and {p.friend} making up.",
        f"Write a simple rhyming tale about a shut {p.shut_object} and a curious question that turns into a friendly agreement.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    scene = world.facts["scene"]
    actor = world.facts["actor"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {actor.id} and {friend.id} near {scene.label}, where a shut moment led to a gentle talk. In the end, the adults helped turn a small disagreement into a friendly plan."
        ),
        QAItem(
            question=f"Why did {friend.id} get curious?",
            answer=f"{friend.id} wanted to know what was by the {p.curiosity_object}, so {friend.pronoun()} asked instead of guessing. That curiosity started the middle of the story, but it also helped the two children talk things through."
        ),
        QAItem(
            question=f"How did {actor.id} and {friend.id} reconcile?",
            answer=f"They slowed down, listened, and agreed to be gentle with the {p.shut_object}. After that, they were friends again and could keep playing together."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.scene} feeling peaceful again, and with {actor.id} and {friend.id} walking away side by side. The last image shows that the shut moment changed into a shared understanding."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does shut mean?",
            answer="Shut means closed. Something that is shut is not open until someone opens it again."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to ask questions and learn more. It can help children discover new things when they ask kindly."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a disagreement. It happens when people talk, listen, and become friendly again."
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if getattr(e, "label", ""):
            bits.append(f"label={e.label}")
        if getattr(e, "role", ""):
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} {getattr(e, 'type', 'thing'):7} {' '.join(bits)}")
    lines.append(f"  facts={world.facts.get('shut_state', '')} reconciled={world.facts.get('reconciled', False)}")
    return "\n".join(lines)


def valid_story_combination(params: StoryParams) -> bool:
    return params.scene in SCENES and params.shut_object in SHUT_OBJECTS and params.curiosity_object in CURIOSITY_OBJECTS


ASP_RULES = r"""
valid(Scene, Shut, Cur) :- scene(Scene), shut_object(Shut), curiosity_object(Cur).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    parts = []
    for s in SCENES:
        parts.append(asp.fact("scene", s))
    for s in SHUT_OBJECTS:
        parts.append(asp.fact("shut_object", s))
    for c in CURIOSITY_OBJECTS:
        parts.append(asp.fact("curiosity_object", c))
    return "\n".join(parts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if not valid_story_combination(params):
        raise StoryError("(Invalid story parameters.)")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.shut is None or c[1] == args.shut)
              and (args.curiosity is None or c[2] == args.curiosity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, shut_object, curiosity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    friend = args.friend or rng.choice([n for n in friend_pool if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        scene=scene,
        actor=name,
        actor_gender=gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        parent_gender=parent,
        shut_object=shut_object,
        curiosity_object=curiosity,
    )


CURATED = [
    StoryParams(scene="garden_gate", actor="Lily", actor_gender="girl", friend="Finn", friend_gender="boy", parent="mother", parent_gender="mother", shut_object="gate", curiosity_object="rosebush"),
    StoryParams(scene="treehouse", actor="Leo", actor_gender="boy", friend="Mia", friend_gender="girl", parent="father", parent_gender="father", shut_object="hatch", curiosity_object="bluebird nest"),
    StoryParams(scene="toy_box", actor="Ava", actor_gender="girl", friend="Noah", friend_gender="boy", parent="mother", parent_gender="mother", shut_object="lid", curiosity_object="crayon tunnel"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, shut, cur in asp_valid_combos():
            print(f"  {s:12} {shut:10} {cur}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
