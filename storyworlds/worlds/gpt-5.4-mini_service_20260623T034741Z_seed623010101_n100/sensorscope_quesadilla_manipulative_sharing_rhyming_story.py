#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/sensorscope_quesadilla_manipulative_sharing_rhyming_story.py
==============================================================================================================

A tiny, standalone story world about sharing a quesadilla, a sneaky child,
and a handy sensorscope. The prose is written as a rhyming story, while the
world model tracks physical meters and emotional memes so the ending follows
from state changes rather than from a frozen paragraph with swapped words.

Seed tale imagined from the prompt:
- A child has a quesadilla.
- Another child acts manipulative and tries to get it all.
- A sensorscope helps them notice what is really going on.
- They choose sharing instead of trickery.
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

SHARE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
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
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    setting_line: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    slices: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str = "kitchen"
    hero: str = "Mina"
    hero_gender: str = "girl"
    helper: str = "Pip"
    helper_gender: str = "boy"
    snack: str = "quesadilla"
    tool: str = "sensorscope"
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        setting_line="The kitchen was bright, with warm light and a table for two.",
        allows={"share", "watch"},
    ),
    "picnic": Place(
        id="picnic",
        label="the picnic blanket",
        setting_line="On the picnic blanket, the grass waved and the napkins sat neat.",
        allows={"share", "watch"},
    ),
    "playroom": Place(
        id="playroom",
        label="the playroom",
        setting_line="In the playroom, a little rug and a low table made a cozy beat.",
        allows={"share", "watch"},
    ),
}

SNACKS = {
    "quesadilla": Snack(
        id="quesadilla",
        label="quesadilla",
        phrase="a warm quesadilla",
        slices=2,
        tags={"food", "share", "quesadilla"},
    ),
}

TOOLS = {
    "sensorscope": Tool(
        id="sensorscope",
        label="sensorscope",
        phrase="a shiny sensorscope",
        purpose="look for clues",
        tags={"tool", "sensorscope"},
    ),
}

NAMES = ["Mina", "Luna", "Ivy", "Nora", "Tia", "Zoe", "Pip", "Ben", "Max", "Toby"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for snack in SNACKS:
            for tool in TOOLS:
                for _ in range(1):
                    combos.append((place, snack, tool, "sharing"))
    return combos


def build_world(place: Place) -> World:
    return World(place=place)


def _init_actor(ent: Entity, name: str, gender: str, role: str) -> Entity:
    ent.id = name
    ent.type = gender
    ent.role = role
    ent.kind = "character"
    ent.meters = {"hungry": 0.0, "shared": 0.0, "taken": 0.0}
    ent.memes = {"joy": 0.0, "worry": 0.0, "greed": 0.0, "kindness": 0.0, "trick": 0.0}
    ent.attrs = {"role": role}
    return ent


def _rhymed_intro(hero: Entity, helper: Entity, snack: Snack, world: World) -> None:
    world.say(
        f"{hero.id} had {snack.phrase}, fresh and neat, "
        f"and smiled at the smell of the cheesy treat."
    )
    world.say(
        f"{helper.id} was nearby, with a grin that could beam, "
        f"but {helper.id} had a plan that was not very sweet."
    )
    hero.memes["joy"] += 1
    hero.meters["shared"] += 0


def _manipulative_push(world: World, hero: Entity, helper: Entity, snack: Snack) -> None:
    helper.memes["trick"] += 1
    helper.memes["greed"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'"Give me the whole {snack.id}," {helper.id} said with a sigh, '
        f'"I need it more than you do, so hand it to me by and by."'
    )
    world.say(
        f"But the words felt manipulative, sly as a cloud, "
        f"like a sneaky small whisper that talked far too loud."
    )


def _peek_with_sensorscope(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    world.say(
        f"{hero.id} held up the {tool.label} and gave it a look, "
        f"then peered for the truth like a page in a book."
    )
    world.say(
        f"The little scope showed the helper's true wish in a flash: "
        f"not to share kindly, but to grab the snack fast."
    )
    hero.memes["worry"] += 0.5
    hero.attrs["saw_trick"] = True


def _share_turn(world: World, hero: Entity, helper: Entity, snack: Snack) -> None:
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.meters["shared"] += 1
    helper.meters["shared"] += 1
    helper.meters["taken"] = 0
    world.say(
        f'"Let’s share," {hero.id} said with a smile, '
        f'"One slice for you, one slice for me, and both of us will stay awhile."'
    )
    world.say(
        f"They split the {snack.id} in two, nice and fair, "
        f"and the room filled with warm, happy, cheesy air."
    )


def _ending(world: World, hero: Entity, helper: Entity, snack: Snack, tool: Tool) -> None:
    world.say(
        f"The {tool.label} sat down, its job now complete, "
        f"because truth and kind sharing made the story sweet."
    )
    world.say(
        f"{hero.id} kept the first slice, {helper.id} got the next, "
        f"and nobody left with a sour, sad text."
    )
    world.say(
        f"So when a snack looks tempting and someone seems sly, "
        f"the best move is sharing and asking, 'Why?'"
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")

    world = build_world(PLACES[params.place])
    hero = _init_actor(world.add(Entity(id=params.hero)), params.hero, params.hero_gender, "hero")
    helper = _init_actor(world.add(Entity(id=params.helper)), params.helper, params.helper_gender, "helper")
    snack = SNACKS[params.snack]
    tool = TOOLS[params.tool]

    world.facts.update(hero=hero, helper=helper, snack=snack, tool=tool, place=world.place)

    world.say(world.place.setting_line)
    _rhymed_intro(hero, helper, snack, world)

    world.para()
    _manipulative_push(world, hero, helper, snack)
    _peek_with_sensorscope(world, hero, helper, tool)

    world.para()
    _share_turn(world, hero, helper, snack)
    _ending(world, hero, helper, snack, tool)

    world.facts.update(
        shared=hero.meters["shared"] >= SHARE_THRESHOLD,
        saw_trick=bool(hero.attrs.get("saw_trick")),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    snack: Snack = f["snack"]
    tool: Tool = f["tool"]
    place: Place = f["place"]
    return [
        f"Write a rhyming story about {hero.id} and {helper.id} in {place.label} that includes the word '{tool.label}'.",
        f"Tell a child-friendly rhyming tale where a {snack.id} is shared after a manipulative request, and the word '{tool.label}' appears.",
        f"Write a simple sharing story in rhyme with a {tool.label}, a {snack.id}, and a sneaky moment that turns kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    snack: Snack = f["snack"]
    tool: Tool = f["tool"]
    place: Place = f["place"]

    qa = [
        QAItem(
            question=f"Who had the quesadilla at first in {place.label}?",
            answer=f"{hero.id} had the quesadilla first. {hero.id} was enjoying a warm snack before the sharing turn began.",
        ),
        QAItem(
            question=f"What did the manipulative helper try to do to the {snack.id}?",
            answer=f"{helper.id} tried to get the whole {snack.id} by using pushy words. The request was not kind, so it needed a careful answer.",
        ),
        QAItem(
            question=f"What did the {tool.label} help {hero.id} notice?",
            answer=f"The {tool.label} helped {hero.id} notice that {helper.id} was not really asking to share. It showed the sneaky plan behind the words.",
        ),
    ]
    if f.get("saw_trick"):
        qa.append(
            QAItem(
                question=f"Why did {hero.id} decide to share after using the {tool.label}?",
                answer=f"{hero.id} saw that the request was manipulative and unfair. After that, {hero.id} chose sharing so both children could enjoy the snack.",
            )
        )
    if f.get("shared"):
        qa.append(
            QAItem(
                question=f"How did the story end for {hero.id} and {helper.id}?",
                answer=f"They split the quesadilla into two fair pieces and both smiled. The ending was warm and kind because sharing solved the problem.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    snack: Snack = f["snack"]
    tool: Tool = f["tool"]
    out = [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person have some of what you have. It is a kind way to make sure everyone gets a turn.",
        ),
        QAItem(
            question=f"What is a {snack.id}?",
            answer="A quesadilla is a warm food made with tortillas and cheese, often folded and cooked until it is melty.",
        ),
        QAItem(
            question=f"What is a {tool.label} for?",
            answer="A sensorscope is a pretend or story tool for looking carefully and finding clues. It helps a character notice what is really going on.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(place="kitchen", hero="Mina", hero_gender="girl", helper="Pip", helper_gender="boy", snack="quesadilla", tool="sensorscope"),
        StoryParams(place="picnic", hero="Luna", hero_gender="girl", helper="Ben", helper_gender="boy", snack="quesadilla", tool="sensorscope"),
        StoryParams(place="playroom", hero="Ivy", hero_gender="girl", helper="Toby", helper_gender="boy", snack="quesadilla", tool="sensorscope"),
    ]


CURATED = valid_story_params()


ASP_RULES = r"""
place(kitchen). place(picnic). place(playroom).
snack(quesadilla).
tool(sensorscope).
feature(sharing).

valid(P,S,T,F) :- place(P), snack(S), tool(T), feature(F).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("feature", "sharing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set((p, s, t, "sharing") for p, s, t, _ in valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set == clingo_set:
        print(f"OK: ASP matches Python valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity:")
        print(" only in python:", sorted(python_set - clingo_set))
        print(" only in clingo:", sorted(clingo_set - python_set))

    sample = generate(valid_story_params()[0])
    if not sample.story.strip():
        print("MISMATCH: generate() produced empty story.")
        return 1
    _ = sample.to_json()
    print("OK: generate() smoke test and JSON serialization passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming sharing story world with a sensorscope and a quesadilla.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.snack is None or c[1] == args.snack)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, snack, tool, _feature = rng.choice(sorted(combos))
    hero = args.name or rng.choice([n for n in NAMES if n != (args.helper or "")])
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    hero_gender = "girl" if hero in {"Mina", "Luna", "Ivy", "Nora", "Tia", "Zoe"} else "boy"
    helper_gender = "girl" if helper in {"Mina", "Luna", "Ivy", "Nora", "Tia", "Zoe"} else "boy"
    return StoryParams(place=place, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, snack=snack, tool=tool)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
