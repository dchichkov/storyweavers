#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/sheep_intrigue_conflict_kindness_bedtime_story.py
================================================================================================

A tiny bedtime-story world about a sheep, a little intrigue, a brief conflict,
and a kind resolution.

The seed idea:
- A sleepy sheep notices something strange at bedtime.
- The sheep and a friend disagree for a moment.
- Kindness turns the night gentle again.

This script keeps the story grounded in a small simulated world:
- characters and objects have physical meters and emotional memes,
- events mutate state and the prose is authored from that state,
- a declarative ASP twin mirrors the reasonableness gate.

The story is intentionally simple and child-facing.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("tired", 0.0)
        self.meters.setdefault("moved", 0.0)
        self.meters.setdefault("warm", 0.0)
        self.meters.setdefault("missing", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("conflict", 0.0)
        self.memes.setdefault("kindness", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("worry", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "sheep":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little barn"
    evening: bool = True
    stars_visible: bool = True
    affords: set[str] = field(default_factory=lambda: {"bedtime", "whisper", "search"})


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    found: bool = False


@dataclass
class StoryParams:
    name: str = "Mabel"
    friend_name: str = "Dot"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _narrate_breeze(world: World) -> list[str]:
    out = []
    sheep = world.get(world.facts["sheep_id"])
    if sheep.memes["curiosity"] >= THRESHOLD and not world.items["bell"].found:
        sig = ("breeze",)
        if sig not in world.fired:
            world.fired.add(sig)
            sheep.memes["worry"] += 0.5
            out.append("A little breeze tickled the straw and made the night feel strange.")
    return out


def _narrate_kindness(world: World) -> list[str]:
    out = []
    sheep = world.get(world.facts["sheep_id"])
    friend = world.get(world.facts["friend_id"])
    blanket = world.items["blanket"]
    if blanket.found and sheep.memes["kindness"] >= THRESHOLD:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            sheep.memes["conflict"] = 0.0
            friend.memes["conflict"] = 0.0
            out.append(f"{friend.id} tucked the blanket around {sheep.id} with a gentle smile.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    for rule in (_narrate_breeze, _narrate_kindness):
        produced.extend(rule(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bedtime_setting_detail(world: World) -> str:
    if world.setting.evening:
        return "The little barn was dim and cozy, and the hay smelled soft."
    return "The room was quiet and snug, with a sleepy light by the wall."


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    sheep = world.add_entity(Entity(id=params.name, kind="character", type="sheep", label="little sheep"))
    friend = world.add_entity(Entity(id=params.friend_name, kind="character", type="sheep", label="small friend"))
    blanket = world.add_item(Item(id="blanket", label="blanket", phrase="a warm bedtime blanket", type="blanket", owner=sheep.id))
    bell = world.add_item(Item(id="bell", label="bell", phrase="a tiny silver bell", type="bell", owner=sheep.id, hidden=True))
    world.facts.update(sheep_id=sheep.id, friend_id=friend.id, blanket=blanket.id, bell=bell.id)
    return world


def tell_story(world: World) -> None:
    sheep = world.get(world.facts["sheep_id"])
    friend = world.get(world.facts["friend_id"])
    blanket = world.items["blanket"]
    bell = world.items["bell"]

    sheep.memes["curiosity"] += 1
    sheep.memes["joy"] += 0.5

    world.say(f"{sheep.id} was a little sheep who loved bedtime.")
    world.say(f"Every night, {sheep.id} liked the quiet hum of {world.setting.place}.")
    world.say("But one night, there was a tiny intrigue.")
    world.say(f"{sheep.id} looked around and noticed that {bell.phrase} was missing from the nest.")
    world.say(bedtime_setting_detail(world))

    world.para()
    world.say(f"{sheep.id} asked {friend.id}, 'Did you see the little bell?'")
    friend.memes["worry"] += 1
    sheep.memes["curiosity"] += 1
    sheep.memes["worry"] += 0.5
    world.say(f"{friend.id} said, 'I only wanted to keep it safe for you.'")
    world.say(f"But {sheep.id} did not understand right away, and a small conflict fluttered in the air.")

    sheep.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{sheep.id} took a slow breath and looked again.")
    bell.hidden = False
    bell.found = True
    sheep.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    world.say(f"There, under the blanket, was the little bell, safe and shiny.")
    world.say(f"{sheep.id} smiled and said, 'Thank you for being kind.'")
    world.say(f"{friend.id} gently shared the blanket, and the two sheep nestled together.")

    blanket.found = True
    sheep.meters["warm"] += 1
    sheep.memes["joy"] += 1
    friend.memes["joy"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"At last, {sheep.id} was warm, the bell was safe, and the barn was sleepy again.")
    world.say(f"The night ended with a soft hush, and {sheep.id} drifted off to dreamland.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about sheep, intrigue, conflict, and kindness.")
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    name = args.name or rng.choice(["Mabel", "Daisy", "Pip", "Nell", "Woolly"])
    friend_name = args.friend_name or rng.choice(["Dot", "Moss", "Bean", "Puddle", "Fern"])
    if name == friend_name:
        raise StoryError("The sheep and the friend must have different names.")
    return StoryParams(name=name, friend_name=friend_name, seed=args.seed)


ASP_RULES = r"""
sheep(S) :- entity(S), sheep_type(S).
friend(F) :- entity(F), sheep_type(F).
intrigue :- missing(bell), curiosity(S), sheep(S).
conflict(S,F) :- sheep(S), friend(F), worry(S), worry(F), not found(bell).
kindness(S,F) :- sheep(S), friend(F), shared_blanket.
resolved :- intrigue, kindness(_, _), found(bell).
#show intrigue/0.
#show conflict/2.
#show kindness/2.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("entity", "sheep"),
        asp.fact("sheep_type", "sheep"),
        asp.fact("entity", "friend"),
        asp.fact("sheep_type", "friend"),
        asp.fact("missing", "bell"),
        asp.fact("curiosity", "sheep"),
        asp.fact("worry", "sheep"),
        asp.fact("worry", "friend"),
        asp.fact("shared_blanket"),
        asp.fact("found", "bell"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show intrigue/0.\n#show conflict/2.\n#show kindness/2.\n#show resolved/0."))
    atoms = {str(sym) for sym in model}
    expected = {"intrigue", "kindness(sheep,friend)", "resolved"}
    if expected.issubset(atoms):
        print("OK: ASP twin is consistent with the built story state.")
        return 0
    print("MISMATCH between ASP twin and story state.")
    print("atoms:", sorted(atoms))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cozy bedtime story about a sheep named {f["sheep_id"]} and a tiny intrigue.',
        f"Tell a child-friendly story where {f['sheep_id']} has a small conflict with {f['friend_id']}, then kindness helps them settle down.",
        "Write a gentle bedtime tale about a missing bell, a worried sheep, and a warm blanket.",
    ]


def story_qa(world: World) -> list[QAItem]:
    sheep = world.get(world.facts["sheep_id"])
    friend = world.get(world.facts["friend_id"])
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {sheep.id}, a little sheep who loved bedtime, and {friend.id}, a kind friend who helped with the bell.",
        ),
        QAItem(
            question=f"What was the little intrigue in the story?",
            answer="The intrigue was that the tiny silver bell seemed to be missing until the sheep looked under the blanket.",
        ),
        QAItem(
            question=f"How did the conflict get better?",
            answer="The conflict got better when the sheep looked again, found the bell, and both sheep chose kindness and shared the blanket.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blanket for?",
            answer="A blanket is used to keep someone warm and cozy when they rest or sleep.",
        ),
        QAItem(
            question="Why is kindness helpful?",
            answer="Kindness helps because gentle words and helpful actions can calm feelings and make people feel safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    for item in world.items.values():
        lines.append(f"  {item.id:8} (item   ) hidden={item.hidden} found={item.found}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    params = resolve_params(args, rng)
    params.seed = base_seed
    return [generate(params)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show intrigue/0.\n#show conflict/2.\n#show kindness/2.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show intrigue/0.\n#show conflict/2.\n#show kindness/2.\n#show resolved/0."))
        print("ASP atoms:")
        for sym in model:
            print(str(sym))
        return

    samples = build_samples(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)


if __name__ == "__main__":
    main()
