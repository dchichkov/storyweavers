#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/fudgecicle_radar_inner_monologue_happy_ending_moral.py
=========================================================================================================

A small storyworld about a child, a weather radar, and the choice to share a
fudgecicle. The stories are heartwarming, state-driven, and built around an
inner monologue that turns into a kind moral choice with a happy ending.

Seed story premise:
---
A child is excited about the last fudgecicle at home, but a rainy afternoon and
a little sibling's disappointment make the choice feel bigger. A family radar
screen helps them wait for better weather, and the child learns that sharing can
make a treat feel sweeter.

World model:
---
    child.hunger, child.joy, child.greed, child.kindness, child.patience
    sibling.hunger, sibling.joy
    weather.rain, weather.clear
    treat.available, treat.shared
    radar.seen_clear_window
    parent.warmth, family.cozy

Scripted beats:
---
    setup                    -> child notices one fudgecicle and feels torn
    inner monologue          -> child privately weighs keeping vs sharing
    radar forecast           -> parent checks radar and promises a dry window
    moral turn               -> child decides to share
    happy ending             -> both children enjoy the treat and the outing
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    weather: str = "rainy"
    affordances: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "kitchen"
    weather: str = "rainy"
    name: str = "Maya"
    sibling_name: str = "Owen"
    child_type: str = "girl"
    sibling_type: str = "boy"
    parent_type: str = "mother"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTING = Setting(place="the kitchen", weather="rainy", affordances={"wait", "share", "watch_radar"})


def valid_combos() -> list[tuple[str, str]]:
    return [("kitchen", "rainy")]


def explain_rejection() -> str:
    return "(No story: this little world is built for a rainy kitchen afternoon.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld: a fudgecicle, a radar, and a moral choice.")
    ap.add_argument("--place", choices=["kitchen"], default=None)
    ap.add_argument("--weather", choices=["rainy"], default=None)
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
    if args.place and args.place != "kitchen":
        raise StoryError(explain_rejection())
    if args.weather and args.weather != "rainy":
        raise StoryError(explain_rejection())
    return StoryParams(
        place="kitchen",
        weather="rainy",
        name=rng.choice(["Maya", "Lina", "Nora", "Ivy"]),
        sibling_name=rng.choice(["Owen", "Ben", "Theo", "Finn"]),
        child_type=rng.choice(["girl", "boy"]),
        sibling_type=rng.choice(["boy", "girl"]),
        parent_type=rng.choice(["mother", "father"]),
        seed=None,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.child_type, role="child",
                             meters={"hunger": 1.0}, memes={"joy": 1.0, "worry": 1.0, "kindness": 0.0, "patience": 0.0}))
    sibling = world.add(Entity(id=params.sibling_name, kind="character", type=params.sibling_type, role="sibling",
                               meters={"hunger": 1.0}, memes={"joy": 0.5}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="mom" if params.parent_type == "mother" else "dad",
                              memes={"warmth": 1.0}))
    treat = world.add(Entity(id="fudgecicle", kind="thing", type="treat", label="fudgecicle",
                             phrase="the last fudgecicle", meters={"available": 1.0}, memes={"temptation": 1.0}))
    radar = world.add(Entity(id="radar", kind="thing", type="tool", label="radar",
                             phrase="the little weather radar", meters={"on": 1.0}, memes={"hope": 1.0}))
    weather = world.add(Entity(id="weather", kind="thing", type="weather", label="rain", meters={"rain": 1.0, "clear": 0.0}))
    world.facts.update(child=child, sibling=sibling, parent=parent, treat=treat, radar=radar, weather=weather)

    world.say(f"{child.id} found {treat.phrase} waiting in the freezer.")
    world.say(f"{child.id} really wanted it, because {child.id} had been thinking about it all afternoon.")
    world.say(f"{sibling.id} peeked in too and looked hopeful.")
    world.para()
    child.memes["worry"] += 1.0
    child.memes["greed"] = 1.0
    world.say(f'Inside, {child.id} thought, "If I eat it now, it will all be mine. But {sibling.id} will feel sad."')
    world.say(f'That thought made {child.id} pause, holding the cool wrapper with both hands.')
    world.para()
    parent.memes["warmth"] += 1.0
    world.say(f'{parent.id} turned on the {radar.label} and watched the screen glow softly.')
    world.say(f'"The rain will pass soon," {parent.id} said. "We can wait for a dry walk after we share a treat."')
    child.memes["patience"] += 1.0
    world.say(f'{child.id} took a slow breath and decided that sharing would feel better than grabbing.')
    world.para()
    child.memes["kindness"] += 2.0
    child.memes["joy"] += 1.5
    sibling.memes["joy"] += 2.0
    treat.meters["shared"] = 1.0
    world.say(f'{child.id} split the fudgecicle in half and gave {sibling.id} the bigger smile, not the bigger piece.')
    world.say(f"Later, when the radar said the clouds were leaving, the family went outside together with sticky hands and happy hearts.")
    world.say(f"By the end of the evening, {child.id} knew something sweet: sharing did not make the treat smaller; it made the whole moment warmer.")
    world.facts.update(shared=True, moral="sharing", ending="happy")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, s = f["child"], f["sibling"]
    return [
        f'Write a heartwarming story for a young child that includes the words "fudgecicle" and "radar".',
        f"Tell a gentle story where {c.id} wants the last fudgecicle, but hears a kind inner monologue and chooses to share with {s.id}.",
        f"Write a happy story about waiting for rain to pass, using a radar screen, and ending with a moral about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, s, p, r = f["child"], f["sibling"], f["parent"], f["radar"]
    return [
        QAItem(
            question=f"What did {c.id} find in the freezer?",
            answer=f"{c.id} found the last fudgecicle in the freezer. It was the only one, so it felt very tempting at first.",
        ),
        QAItem(
            question=f"What did {c.id} think about before deciding what to do?",
            answer=f"{c.id} thought about keeping the fudgecicle all to {c.pronoun('object')}, but then remembered how sad {s.id} might feel. That inner monologue helped {c.id} choose kindness.",
        ),
        QAItem(
            question=f"How did the radar help the family?",
            answer=f"The radar showed that the rain would pass soon. That meant the family could wait for a dry walk instead of rushing, and the treat became part of a calmer, happier evening.",
        ),
        QAItem(
            question=f"Why did {c.id} share the fudgecicle?",
            answer=f"{c.id} shared because {c.id} cared about {s.id} and wanted everyone to feel included. The story's moral is that sharing can make a sweet thing feel even better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a radar?",
            answer="A radar is a machine that helps people notice things like weather by sending out signals and showing what is nearby. In this story, it helped the family know the rain would pass.",
        ),
        QAItem(
            question="What is a fudgecicle?",
            answer="A fudgecicle is a frozen chocolate treat on a stick. It is sweet and cold, which is why it was so tempting in the story.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have to someone else or letting them enjoy it too. It is a kind way to show that other people's feelings matter.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
shared_story :- treat(fudgecicle), tool(radar), moral(sharing), ending(happy).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("treat", "fudgecicle"),
        asp.fact("tool", "radar"),
        asp.fact("moral", "sharing"),
        asp.fact("ending", "happy"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shared_story/0."))
    ok = bool(asp.atoms(model, "shared_story"))
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    if ok and "fudgecicle" in sample.story and "radar" in sample.story:
        print("OK: ASP and Python storyworld checks passed.")
        return 0
    print("MISMATCH in verification.")
    return 1


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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.meters, e.memes, e.attrs)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", weather="rainy", name="Maya", sibling_name="Owen", child_type="girl", sibling_type="boy", parent_type="mother"),
    StoryParams(place="kitchen", weather="rainy", name="Lina", sibling_name="Ben", child_type="girl", sibling_type="boy", parent_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shared_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("shared story: fudgecicle + radar + sharing + happy ending")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
