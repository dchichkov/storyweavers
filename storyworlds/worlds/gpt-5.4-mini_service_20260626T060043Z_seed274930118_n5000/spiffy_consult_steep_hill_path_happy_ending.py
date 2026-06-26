#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spiffy_consult_steep_hill_path_happy_ending.py
===========================================================================================================================

A tiny story world in a ghost-story mood: a spiffy helper, a steep hill path,
a worried child, and a happy ending reached by consulting the right clue.

Premise:
- A child and a small ghost-like helper are trying to go down a steep hill path.
- The path is slippery, and a prized lantern is at risk.
- Instead of rushing, they consult a map and choose the safer switchback trail.

State-driven turn:
- The child grows uneasy on the steep slope.
- The helper notices the danger and consults the map.
- The chosen detour lowers risk and keeps the lantern safe.

Resolution:
- They arrive at the bottom with the lantern intact.
- The child feels proud, the helper feels spiffy, and the ending is calm and warm.
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Terrain:
    place: str = "the steep hill path"
    steepness: float = 1.0
    slippery: bool = True
    afford: set[str] = field(default_factory=lambda: {"walk", "consult", "detour"})


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    safe_route: bool = False


class World:
    def __init__(self, terrain: Terrain) -> None:
        self.terrain = terrain
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.route: str = "direct"
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        c = World(self.terrain)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.route = self.route
        c.facts = dict(self.facts)
        return c


def path_risk(world: World) -> float:
    risk = world.terrain.steepness
    if world.terrain.slippery and world.route == "direct":
        risk += 1.0
    if world.route == "switchback":
        risk -= 0.75
    return max(risk, 0.0)


def check_slip(world: World) -> list[str]:
    out: list[str] = []
    risk = path_risk(world)
    for hero in world.characters():
        if hero.meters.get("careful", 0.0) < THRESHOLD:
            continue
        if risk < THRESHOLD:
            continue
        sig = ("slip", hero.id, world.route)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
        out.append(f"The path looked too steep, and {hero.id} slowed down.")
    return out


def apply_rules(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in check_slip(world):
            changed = True
            produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, hero: Entity, tool: Tool) -> dict:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    if tool.safe_route:
        sim.route = "switchback"
    else:
        sim.route = "direct"
    hero2.meters["careful"] = hero2.meters.get("careful", 0.0) + 1.0
    apply_rules(sim, narrate=False)
    lantern = sim.get("lantern")
    return {
        "risk": path_risk(sim),
        "safe": sim.route == "switchback" and lantern.meters.get("safe", 0.0) < THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    world.say(
        f"{hero.id} and {friend.id} reached {world.terrain.place}, where the hill rose sharply and the air felt quiet."
    )
    world.say(
        f"{friend.id} looked very spiffy in a neat little cape, as if even a ghost could dress for a serious walk."
    )
    world.say(
        f"They carried a {tool.label} because the lantern would need a careful plan."
    )


def concern(world: World, hero: Entity, lantern: Entity) -> None:
    hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1.0
    lantern.meters["at_risk"] = lantern.meters.get("at_risk", 0.0) + 1.0
    world.say(
        f"The path dropped away fast, and {hero.id} hugged the {lantern.label} a little tighter."
    )


def consult(world: World, friend: Entity, hero: Entity, tool: Tool) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(
        f"{friend.id} said they should consult the map instead of guessing."
    )
    world.say(
        f'With a soft "oo-oo," {friend.id} pointed out a safer switchback trail hidden beside the hill.'
    )
    if tool.safe_route:
        world.route = "switchback"


def choose(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    prediction = predict(world, hero, tool)
    world.facts["predicted_risk"] = prediction["risk"]
    if prediction["safe"]:
        hero.meters["careful"] = hero.meters.get("careful", 0.0) + 1.0
        world.say(
            f"{hero.id} nodded, because the switchback looked much safer than the straight drop."
        )
    else:
        raise StoryError("This story needs a tool that can lead to a safer route.")


def travel(world: World, hero: Entity, friend: Entity, lantern: Entity, tool: Tool) -> None:
    world.route = "switchback" if tool.safe_route else "direct"
    apply_rules(world, narrate=True)
    if world.route == "switchback":
        lantern.meters["safe"] = lantern.meters.get("safe", 0.0) + 1.0
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
        world.say(
            f"They took the winding path, and each careful step made the hill feel a little less tall."
        )
    else:
        raise StoryError("The direct route is too risky for a happy ending here.")


def ending(world: World, hero: Entity, friend: Entity, lantern: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.say(
        f"By the time they reached the bottom, the {lantern.label} was still bright, and the night felt friendly again."
    )
    world.say(
        f"{hero.id} smiled, and {friend.id} drifted beside {hero.pronoun('object')} like a tiny lantern-shadow with a happy ending."
    )


def tell_story(name: str, friend_name: str, seed: Optional[int] = None) -> World:
    terrain = Terrain()
    world = World(terrain)
    hero = world.add(Entity(id=name, kind="character", type="girl", label=name))
    friend = world.add(Entity(id=friend_name, kind="ghost", type="ghost", label=friend_name))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", owner=hero.id, caretaker=hero.id))
    map_tool = Tool(id="map", label="small map", helps={"consult"}, safe_route=True)

    hero.meters["careful"] = 0.0
    hero.memes["curious"] = 1.0
    friend.memes["spiffy"] = 1.0

    introduce(world, hero, friend, map_tool)
    world.para()
    concern(world, hero, lantern)
    consult(world, friend, hero, map_tool)
    choose(world, hero, friend, map_tool)
    world.para()
    travel(world, hero, friend, lantern, map_tool)
    ending(world, hero, friend, lantern)

    world.facts.update(hero=hero, friend=friend, lantern=lantern, tool=map_tool, terrain=terrain)
    return world


@dataclass
class StoryParams:
    name: str
    friend_name: str
    seed: Optional[int] = None


NAMES = ["Mina", "Iris", "Nora", "Lena", "Ada", "June"]
GHOST_NAMES = ["Murmur", "Pip", "Boo", "Wisp", "Moth"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A spiffy ghost-story about consulting a map on a steep hill path.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=GHOST_NAMES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(GHOST_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly ghost story with a spiffy helper who must consult a map on a steep hill path.',
        f"Tell a short story where {f['hero'].id} and {f['friend'].id} walk the steep hill path and keep a lantern safe.",
        'Write a happy-ending story that uses the words spiffy and consult and ends with a safer way down the hill.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    lantern = f["lantern"]
    return [
        QAItem(
            question=f"Why did {friend.id} tell {hero.id} to consult the map?",
            answer="Because the steep hill path looked risky, and the map showed a safer switchback trail.",
        ),
        QAItem(
            question=f"What did {hero.id} try to keep safe on the hill path?",
            answer=f"{hero.id} tried to keep the {lantern.label} safe while going down the steep hill path.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} and {friend.id} reaching the bottom safely and the {lantern.label} still bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to consult something?",
            answer="To consult something means to look at it or ask about it for help before making a choice.",
        ),
        QAItem(
            question="What does spiffy mean?",
            answer="Spiffy means neat, sharp, and nicely dressed or arranged.",
        ),
        QAItem(
            question="What is a switchback trail?",
            answer="A switchback trail is a path that turns back and forth so it can climb or descend more gently.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  route={world.route}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts describe the path, the consult action, and the safe route.
safe_route(switchback).
dangerous_route(direct).

happy_end(H, F) :- hero(H), friend(F), consults(F), safe_route(switchback).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("friend", "ghost"),
        asp.fact("place", "steep_hill_path"),
        asp.fact("consults", "ghost"),
        asp.fact("tool", "map"),
        asp.fact("route", "switchback"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show happy_end/2.\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    atoms = set(asp.atoms(model, "happy_end"))
    expected = {("hero", "ghost")}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params.name, params.friend_name, params.seed)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show happy_end/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/2."))
        print(sorted(set(asp.atoms(model, "happy_end"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", friend_name="Wisp"),
            StoryParams(name="Iris", friend_name="Boo"),
            StoryParams(name="Nora", friend_name="Murmur"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} with {sample.params.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
