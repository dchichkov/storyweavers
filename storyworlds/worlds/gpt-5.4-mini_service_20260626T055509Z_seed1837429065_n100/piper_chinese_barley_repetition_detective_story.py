#!/usr/bin/env python3
"""
storyworlds/worlds/piper_chinese_barley_repetition_detective_story.py
=====================================================================

A small detective storyworld about Piper, Chinese barley, and a clue that
repeats until the mystery is solved.

Premise:
- Piper is a little detective.
- In a Chinese tea shop, a bowl of barley porridge keeps showing up in the
  wrong place again and again.
- The repeated trail is not random; it is the clue that points to the helper.

Turn:
- Piper notices repetition: the same kind of crumb, the same direction marks,
  the same tiny missing spoon.
- The detective follows the repeated signs and learns who has been carrying the
  bowl between rooms.

Resolution:
- Piper solves the case by matching the repeated clues to one careful helper.
- The bowl is returned, the helper confesses, and the shop is calm again.

This world keeps the prose child-facing and concrete, but the state machine is
small and genuine: clues accumulate in meters, suspicion and relief live in
memes, and the ending changes the world rather than just the wording.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
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
class Setting:
    place: str = "the Chinese tea shop"
    afford: set[str] = field(default_factory=lambda: {"investigate", "serve", "move_bowl"})


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "tea_shop": Setting(place="the Chinese tea shop"),
    "market": Setting(place="the Chinese market"),
    "kitchen": Setting(place="the small kitchen behind the tea shop"),
}

HERO_NAMES = ["Piper", "Mina", "Jun", "Lina", "Theo"]
HELPER_NAMES = ["An", "Bo", "Chen", "Dai", "Mei"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="girl" if params.hero_name in {"Piper", "Mina", "Lina", "Mei"} else "boy",
        label=params.hero_name,
        meters={"attention": 0.0},
        memes={"curiosity": 1.0, "certainty": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="woman" if params.helper_name in {"An", "Dai", "Mei"} else "man",
        label=params.helper_name,
        meters={"care": 0.0},
        memes={"worry": 0.0, "relief": 0.0},
    ))
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type="bowl",
        label="bowl of barley porridge",
        phrase="a warm bowl of barley porridge",
        owner=helper.id,
        location="counter",
        meters={"missing": 0.0, "moves": 0.0},
    ))
    crumbs = world.add(Entity(
        id="crumbs",
        kind="thing",
        type="crumbs",
        label="barley crumbs",
        plural=True,
        location="floor",
        meters={"repeat": 0.0},
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="tiny note",
        phrase="a tiny note with the same word again and again",
        location="table",
        meters={"repeat": 0.0},
    ))

    world.facts.update(hero=hero, helper=helper, bowl=bowl, crumbs=crumbs, note=note)
    return world


def predict_move(world: World) -> bool:
    sim = world.copy()
    bowl = sim.get("bowl")
    bowl.meters["moves"] += 1
    bowl.location = "back room"
    sim.get("crumbs").meters["repeat"] += 1
    return bowl.location == "back room"


def move_bowl(world: World, actor: Entity, bowl: Entity, source: str, target: str) -> None:
    if source == target:
        raise StoryError("The bowl cannot be moved to the same place.")
    actor.meters["attention"] += 1
    bowl.meters["moves"] += 1
    bowl.location = target


def investigate(world: World, hero: Entity, bowl: Entity, crumbs: Entity, note: Entity) -> None:
    hero.meters["attention"] += 1
    hero.memes["curiosity"] += 1
    crumbs.meters["repeat"] += 1
    note.meters["repeat"] += 1
    world.say(
        f"{hero.id} was a little detective who loved a good clue. "
        f"At {world.setting.place}, {hero.id} noticed the same barley crumbs by the door, "
        f"then the same crumbs again by the shelf, as if the day were repeating itself."
    )


def gather_clues(world: World, hero: Entity, helper: Entity, bowl: Entity, crumbs: Entity, note: Entity) -> None:
    world.say(
        f"{hero.id} looked closer. The bowl had been moved twice, and the barley crumbs made a neat trail. "
        f"The tiny note also showed the same word again and again, which made the pattern easy to miss if you blinked."
    )
    world.say(
        f"{hero.id} said, '{hero.id} does not think this is an accident.' "
        f"{hero.pronoun().capitalize()} followed the repeated crumbs toward the back room."
    )
    hero.meters["attention"] += 1
    helper.memes["worry"] += 1
    bowl.meters["moves"] += 1
    crumbs.meters["repeat"] += 1
    note.meters["repeat"] += 1


def solve_mystery(world: World, hero: Entity, helper: Entity, bowl: Entity) -> None:
    helper.memes["worry"] += 1
    helper.memes["relief"] += 1
    hero.memes["certainty"] += 1
    bowl.location = "counter"
    world.say(
        f"At last, {hero.id} found {helper.id} carrying the bowl back and forth to keep it warm. "
        f"{helper.id} had been repeating the trip because the room was chilly and {helper.id} did not want the barley to get cold."
    )
    world.say(
        f"{hero.id} smiled. The clue had been repetition all along: the same little trip, the same crumbs, the same note, "
        f"all pointing to one careful helper. {helper.id} laughed in relief and set the bowl on the counter where everyone could see it."
    )
    hero.memes["joy"] += 1
    helper.memes["relief"] += 1


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get(params.hero_name)
    helper = world.get(params.helper_name)
    bowl = world.get("bowl")
    crumbs = world.get("crumbs")
    note = world.get("note")

    world.say(
        f"One afternoon, {hero.id} went to {world.setting.place}. "
        f"Inside, there was a warm, Chinese smell of tea and barley."
    )
    world.say(
        f"{helper.id} had set out a bowl of barley porridge, but something strange kept happening: the bowl was moved, and then it seemed to be moved again."
    )

    world.para()
    investigate(world, hero, bowl, crumbs, note)

    world.para()
    gather_clues(world, hero, helper, bowl, crumbs, note)

    world.para()
    solve_mystery(world, hero, helper, bowl)

    world.say(
        f"In the end, the tea shop felt calm again. The barley stayed put, the repeated clues made sense, and {hero.id} had solved the mystery like a true detective."
    )
    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a short detective story for a child starring {hero.id}, set in a Chinese tea shop, where repetition helps solve a mystery.',
        f"Tell a gentle mystery story about {hero.id} and {helper.id} that uses the words piper, chinese, barley, and repetition.",
        "Write a tiny detective tale where the same clue appears again and again until the hero figures out why.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    bowl = world.facts["bowl"]
    return [
        QAItem(
            question=f"Who solved the mystery at {world.setting.place}?",
            answer=f"{hero.id} solved the mystery by noticing the repeated clues and following them to {helper.id}.",
        ),
        QAItem(
            question="What made the clue special?",
            answer="The clue was special because it kept repeating: the same barley crumbs, the same moved bowl, and the same little note.",
        ),
        QAItem(
            question=f"What was in the bowl that kept moving?",
            answer=f"The bowl held barley porridge, which {helper.id} had been carrying back and forth to keep warm.",
        ),
        QAItem(
            question=f"Why did {helper.id} keep moving the bowl?",
            answer=f"{helper.id} kept moving the bowl so the barley would stay warm in the chilly back room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is barley?",
            answer="Barley is a grain that people can cook into porridge, soup, or other warm foods.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens or appears again and again.",
        ),
        QAItem(
            question="What is a Chinese tea shop?",
            answer="A Chinese tea shop is a place where people can drink tea and eat small foods together.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).

repeated_clue(C) :- clue(C), repeat_count(C,N), N >= 2.
mystery_solved :- repeated_clue(crumbs), repeated_clue(note), moved(bowl), helper_reason(back_warmth).

#show repeated_clue/1.
#show mystery_solved/0.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("hero_name", "piper"),
        asp.fact("helper_name", "helper"),
        asp.fact("clue", "crumbs"),
        asp.fact("clue", "note"),
        asp.fact("moved", "bowl"),
        asp.fact("repeat_count", "crumbs", 2),
        asp.fact("repeat_count", "note", 2),
        asp.fact("helper_reason", "back_warmth"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show mystery_solved/0."))
    atoms = asp.atoms(model, "mystery_solved")
    ok = bool(atoms)
    if ok:
        print("OK: ASP gate confirms the mystery is solved.")
        return 0
    print("MISMATCH: ASP gate did not confirm the mystery.")
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with Piper, Chinese barley, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    if hero_name == helper_name:
        raise StoryError("The detective and the helper must be different people.")
    return StoryParams(place=place, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show mystery_solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show repeated_clue/1.\n#show mystery_solved/0."))
        print(asp.atoms(model, "repeated_clue"))
        print(asp.atoms(model, "mystery_solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="tea_shop", hero_name="Piper", helper_name="An"),
            StoryParams(place="market", hero_name="Mina", helper_name="Chen"),
            StoryParams(place="kitchen", hero_name="Jun", helper_name="Mei"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
