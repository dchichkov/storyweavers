#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/emergency_clamp_starfish_friendship_quest_transformation_animal.py
======================================================================================================

A small animal-story world about an emergency, a clamp, a starfish, and the
friendship that turns a scary quest into a gentle transformation.

Premise:
- A young sea animal friend sees an emergency at the tidepool reef.
- A starfish is stuck under a clamp.
- The friends go on a short quest to free it.
- The hero changes from worried to brave, and the starfish changes from stuck
  to safe and smiling.

The world is deliberately compact and classical: a few typed entities, physical
meters, emotional memes, and a tiny forward simulation that drives the prose.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    stuck: bool = False
    transformable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"octopus", "seal", "otter", "crab", "fish", "starfish", "turtle"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the tidepool reef"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    used_for: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_clamp_hurts(world: World) -> list[str]:
    out: list[str] = []
    clamp = world.entities.get("clamp")
    if not clamp or clamp.carried_by is None:
        return out
    carrier = world.get(clamp.carried_by)
    if carrier.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("clamp_hurts", carrier.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.memes["stress"] = carrier.memes.get("stress", 0) + 1
    out.append(f"The clamp looked heavy, and {carrier.id} felt the worry pinch harder.")
    return out


def _r_free_starfish(world: World) -> list[str]:
    out: list[str] = []
    star = world.entities.get("starfish")
    clamp = world.entities.get("clamp")
    if not star or not clamp:
        return out
    if not star.stuck:
        return out
    helper = world.entities.get("hero")
    if not helper:
        return out
    if helper.memes.get("brave", 0) < THRESHOLD:
        return out
    if helper.meters.get("tool_use", 0) < THRESHOLD:
        return out
    sig = ("free_starfish",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    star.stuck = False
    star.meters["safe"] = star.meters.get("safe", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    out.append("The clamp opened, and the starfish wriggled free at last.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    star = world.entities.get("starfish")
    if not hero or not star:
        return out
    if hero.memes.get("brave", 0) < THRESHOLD or star.meters.get("safe", 0) < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    star.meters["glow"] = star.meters.get("glow", 0) + 1
    out.append("The hero felt changed, from shy and shaky to steady and bright.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_sents: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_clamp_hurts, _r_free_starfish, _r_transformation):
            sents = rule(world)
            if sents:
                changed = True
                all_sents.extend(sents)
    if narrate:
        for s in all_sents:
            world.say(s)
    return all_sents


SETTING = Setting(place="the tidepool reef", affords={"quest", "emergency", "transformation"})

QUESTS = {
    "rescue": Quest(
        id="rescue",
        verb="help the starfish",
        gerund="helping the starfish",
        rush="rush to the reef",
        danger="the clamp might hurt the starfish",
        keyword="starfish",
        tags={"emergency", "starfish", "clamp", "quest", "friendship", "transformation"},
    )
}

TOOLS = {
    "shell_wedge": Tool(
        id="shell_wedge",
        label="a smooth shell wedge",
        phrase="a smooth shell wedge",
        helps={"clamp"},
        used_for={"freeing"},
        prep="pick up a smooth shell wedge",
        tail="used the shell wedge to pry the clamp open",
    )
}

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nori", "Kiki"]
BOY_NAMES = ["Pip", "Milo", "Jasper", "Tomo", "Rai"]
ANIMALS = ["octopus", "otter", "seal", "crab", "fish", "turtle"]
TRAITS = ["gentle", "curious", "shy", "brave", "kind", "lively"]


@dataclass
class StoryParams:
    name: str
    animal: str
    trait: str
    friend_name: str
    friend_animal: str
    quest: str
    tool: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world: emergency, clamp, starfish, friendship, quest, transformation."
    )
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--friend-name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--friend-animal", choices=ANIMALS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
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
    quest = args.quest or "rescue"
    tool = args.tool or "shell_wedge"
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    animal = args.animal or rng.choice(ANIMALS)
    trait = args.trait or rng.choice(TRAITS)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    friend_animal = args.friend_animal or rng.choice([a for a in ANIMALS if a != animal])
    return StoryParams(
        name=name,
        animal=animal,
        trait=trait,
        friend_name=friend_name,
        friend_animal=friend_animal,
        quest=quest,
        tool=tool,
    )


def _do_quest(world: World, hero: Entity, friend: Entity, star: Entity, clamp: Entity, tool: Tool) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"One morning at {world.setting.place}, {hero.id} the {hero.type} saw an emergency: "
        f"a starfish was stuck under the clamp."
    )
    world.say(
        f"{friend.id} came quickly too, because friends do not leave when the tidepool feels scary."
    )
    world.para()
    world.say(f"{hero.id} wanted to {QUESTS['rescue'].verb}, but {tool.prep} first.")
    world.say(f"{hero.id} and {friend.id} followed the quest path over the wet stones.")
    world.say(f"They found {tool.phrase} near a warm shell pile.")
    hero.meters["tool_use"] = hero.meters.get("tool_use", 0) + 1
    clamp.carried_by = hero.id
    hero.memes["brave"] = hero.memes.get("brave", 0) + 1
    world.say(
        f"{hero.id} held the tool with careful paws and started the rescue, even though the clamp looked hard to move."
    )
    propagate(world, narrate=True)
    clamp.carried_by = None
    world.say(tool.tail.capitalize() + ".")
    propagate(world, narrate=True)
    world.para()
    if not star.stuck:
        world.say(
            f"The starfish blinked awake, safe again, and {friend.id} cheered as the water sparkled around them."
        )
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        traits=[params.trait],
        meters={"tool_use": 0.0},
        memes={"worry": 0.0, "brave": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_animal,
        traits=["kind"],
        memes={"support": 0.0},
    ))
    star = world.add(Entity(
        id="starfish",
        kind="character",
        type="starfish",
        label="starfish",
        stuck=True,
        transformable=True,
        meters={"safe": 0.0, "glow": 0.0},
        memes={"hope": 0.0},
    ))
    clamp = world.add(Entity(
        id="clamp",
        type="clamp",
        label="clamp",
        phrase="the clamp",
        stuck=False,
        carried_by=None,
    ))
    world.facts.update(hero=hero, friend=friend, star=star, clamp=clamp, params=params)
    world.say(
        f"{hero.id} was a {params.trait} {params.animal} who loved small quests with {friend.id}, "
        f"because friendship made even a tidepool day feel big."
    )
    world.say(
        f"On that day, the two friends spotted a starfish in an emergency under a clamp."
    )
    world.para()
    _do_quest(world, hero, friend, star, clamp, TOOLS[params.tool])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short animal story about {hero.id} the {hero.type}, friendship, and a starfish emergency.',
        f"Tell a gentle quest story where {friend.id} helps {hero.id} free a starfish from a clamp.",
        f'Write an Animal Story with the words "emergency", "clamp", and "starfish" that ends in transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    star = f["star"]
    clamp = f["clamp"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who saw the emergency at the tidepool reef?",
            answer=f"{hero.id} saw it first, and {friend.id} rushed over to help.",
        ),
        QAItem(
            question=f"What was stuck under the clamp?",
            answer=f"The starfish was stuck under the clamp until the friends used the shell wedge.",
        ),
        QAItem(
            question=f"How did friendship matter in the quest?",
            answer=f"{friend.id} stayed close and helped {hero.id} stay brave, so the rescue could happen.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} changed from worried to brave, and the starfish changed from stuck to safe.",
        ),
        QAItem(
            question=f"Why was the clamp important in this story?",
            answer=f"The clamp was the thing that made the emergency real, because it held the starfish down until the friends opened it.",
        ),
        QAItem(
            question=f"What kind of story was this with {params.animal} and {params.friend_animal} friends?",
            answer="It was an Animal Story about a quest, a rescue, and a gentle transformation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a starfish?",
            answer="A starfish is a sea animal with arms that lives in salt water and moves slowly over rocks.",
        ),
        QAItem(
            question="What is a clamp?",
            answer="A clamp is something that holds tightly, like a tool or fastener that squeezes and keeps things in place.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about another friend, helping them, and staying with them when things are hard.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone tries to reach a goal, like helping a friend or finding something important.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new state, like feeling braver or becoming safe after being stuck.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.stuck:
            bits.append("stuck=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.quest in QUESTS and params.tool in TOOLS


CURATED = [
    StoryParams(name="Mina", animal="octopus", trait="shy", friend_name="Pip", friend_animal="otter", quest="rescue", tool="shell_wedge"),
    StoryParams(name="Luna", animal="seal", trait="gentle", friend_name="Rai", friend_animal="turtle", quest="rescue", tool="shell_wedge"),
    StoryParams(name="Tomo", animal="crab", trait="curious", friend_name="Kiki", friend_animal="fish", quest="rescue", tool="shell_wedge"),
]


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("The requested story does not fit this small animal world.")
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


ASP_RULES = r"""
% The Python world is tiny: a rescue story is valid when a quest, tool, and
% emergency all match the registries.
valid_story(N, F, Q, T) :- name(N), friend(F), quest(Q), tool(T), rescue_quest(Q), shell_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("name", n))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("rescue_quest", "rescue"))
    lines.append(asp.fact("shell_tool", "shell_wedge"))
    for n in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("friend", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for n in GIRL_NAMES + BOY_NAMES:
        for f in GIRL_NAMES + BOY_NAMES:
            for q in QUESTS:
                for t in TOOLS:
                    if q == "rescue" and t == "shell_wedge":
                        py_set.add((n, f, q, t))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        i += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos.")
        for combo in combos[:20]:
            print(combo)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = build_story_from_args(args)

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
