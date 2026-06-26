#!/usr/bin/env python3
"""
A fairy-tale storyworld about a tangy surprise, teamwork, and transformation.

A small source tale:

Once upon a time, in a lantern-lit valley, there lived a tiny fox named Tavi.
Tavi loved bright things and sweet songs, but the valley's old bell tree had gone
silent. One morning, a strange tang drifted through the air from the hollow
roots of the tree. Inside the roots, Tavi found a sleeping pebble-sprite with a
cracked crown and a sour face. The sprite snapped awake in surprise and said the
tree would only sing again if three helpers polished the crown together with
care, each adding a different kind of magic: one to hold, one to shine, and one
to hum.

Tavi called on a beetle knight and a moth seamstress. They worked together,
and the sour tang softened into a sweet sparkle. As they finished, the pebble-
sprite changed from gray and prickly into gold and warm laughter. The bell tree
rang at last, and the whole valley danced under the bells.

This script turns that premise into a small deterministic simulation with
carefully constrained variations.
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
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "boy", "prince", "king", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "queen", "witch", "seamstress"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lantern-lit valley"
    afford: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    surprise: str
    teamwork: str
    transform: str
    tang: str
    hazard: str
    keyword: str = "tang"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    owner_kind: str
    can_transform: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return w


def _r_sour_to_sweet(world: World) -> list[str]:
    out = []
    sprite = world.entities.get("sprite")
    crown = world.entities.get("crown")
    if not sprite or not crown:
        return out
    if sprite.meters.get("tang", 0) < THRESHOLD:
        return out
    sig = ("transform", "sprite")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sprite.meters["gray"] = max(0.0, sprite.meters.get("gray", 0) - 1.0)
    sprite.meters["gold"] = sprite.meters.get("gold", 0) + 1.0
    sprite.memes["joy"] = sprite.memes.get("joy", 0) + 1.0
    crown.meters["shine"] = crown.meters.get("shine", 0) + 1.0
    out.append("The sour spell loosened, and the pebble-sprite grew warm and golden.")
    return out


CAUSAL_RULES = [_r_sour_to_sweet]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def setup_world(setting: Setting, action: Action, prize: Prize,
                hero_name: str, helper1: str, helper2: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="fox", label=hero_name))
    helper_a = world.add(Entity(id="helper_a", kind="character", type="knight", label=helper1))
    helper_b = world.add(Entity(id="helper_b", kind="character", type="seamstress", label=helper2))
    sprite = world.add(Entity(
        id="sprite", kind="character", type="sprite", label="the pebble-sprite"
    ))
    crown = world.add(Entity(
        id="crown", type="thing", label="crown", phrase="a cracked little crown"
    ))
    hero.memes["curiosity"] = 1.0
    sprite.meters["gray"] = 1.0
    sprite.meters["tang"] = 0.0
    crown.meters["shine"] = 0.0

    world.say(f"Once upon a time, {hero.label} lived in {setting.place}.")
    world.say(
        f"{hero.label} loved {action.gerund}, but the old bell tree had gone quiet and strange."
    )
    world.say(
        f"One morning, a sharp {action.tang} drifted from the roots, full of {action.surprise}."
    )

    world.para()
    world.say(
        f"Inside the roots, {hero.label} found {sprite.label}, sour-faced and guarding {prize.phrase}."
    )
    sprite.meters["tang"] += 1.0
    sprite.memes["surprised"] = 1.0
    world.say(
        f'The sprite blinked in surprise and said, "The bell tree will sing only if three helpers work together."'
    )
    world.say(
        f'"One to hold, one to shine, and one to hum," it whispered, as if the whole valley had to listen.'
    )

    world.para()
    world.say(
        f"{hero.label} called for {helper1} the beetle knight and {helper2} the moth seamstress."
    )
    world.say(
        f"At once, they gathered around the cracked crown and began their teamwork."
    )
    world.say(
        f"{helper1} held the crown steady, {helper2} stitched a bright ribbon around it, and {hero.label} hummed a tiny tune."
    )
    world.say(
        f"That was the right kind of {action.teamwork}: strong, careful, and kind."
    )
    world.say(
        f"The sour tang softened into a sweet sparkle as the crown warmed in their hands."
    )
    propagate(world)

    world.para()
    world.say(
        f"Then the pebble-sprite changed from gray and prickly into gold and laughing."
    )
    world.say(
        f"The bell tree rang at last, and the whole valley danced under the bells."
    )

    world.facts.update(
        hero=hero,
        helper1=helper_a,
        helper2=helper_b,
        sprite=sprite,
        crown=crown,
        setting=setting,
        action=action,
        prize=prize,
    )
    return world


SETTINGS = {
    "valley": Setting(place="the lantern-lit valley", afford={"song", "crown"}),
    "grove": Setting(place="the moonberry grove", afford={"song", "crown"}),
}

ACTIONS = {
    "tang": Action(
        id="tang",
        verb="follow the strange scent",
        gerund="following strange scents",
        surprise="surprise",
        teamwork="teamwork",
        transform="transformation",
        tang="tang",
        hazard="sourness",
        tags={"tang", "surprise", "teamwork", "transformation"},
    ),
}

PRIZES = {
    "crown": Prize(
        id="crown",
        label="crown",
        phrase="a cracked little crown",
        owner_kind="sprite",
    ),
}

NAMES = ["Tavi", "Nell", "Pip", "Mira", "Wren", "Oren"]
HELPERS1 = ["Brindle", "Cobb", "Moss", "Bram", "Jory"]
HELPERS2 = ["Luma", "Fae", "Thimble", "Sera", "Nia"]
TRAITS = ["curious", "brave", "gentle", "quick-witted", "kind"]


@dataclass
class StoryParams:
    setting: str
    action: str
    prize: str
    hero: str
    helper1: str
    helper2: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("valley", "tang", "crown"), ("grove", "tang", "crown")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of tang, surprise, teamwork, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
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
    if args.action and args.prize and (args.action, args.prize) != ("tang", "crown"):
        raise StoryError("This fairy tale only supports the tang-and-crown story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or "tang"
    prize = args.prize or "crown"
    hero = args.name or rng.choice(NAMES)
    helper1 = args.helper1 or rng.choice(HELPERS1)
    helper2 = args.helper2 or rng.choice(HELPERS2)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, action, prize, hero, helper1, helper2, trait)


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about a {f["hero"].type} named {f["hero"].label} and a tangy surprise in {f["setting"].place}.',
        f"Tell a short story where {f['hero'].label} needs teamwork to change a sour thing into something bright.",
        f'Write a gentle tale that includes the word "tang" and ends with a joyful transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sprite = f["sprite"]
    crown = f["crown"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.label} live?",
            answer=f"{hero.label} lived in {setting.place}.",
        ),
        QAItem(
            question="What strange smell drifted from the roots?",
            answer="A sharp tang drifted from the roots.",
        ),
        QAItem(
            question=f"Who did {hero.label} call to help?",
            answer=f"{hero.label} called {f['helper1'].label} the beetle knight and {f['helper2'].label} the moth seamstress.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The pebble-sprite changed from gray and prickly into gold and laughing, and the bell tree rang again.",
        ),
        QAItem(
            question=f"What was the sprite guarding?",
            answer=f"The sprite was guarding {crown.phrase}.",
        ),
        QAItem(
            question="How did the helpers fix the problem?",
            answer="They held, shone, and hummed together, which turned the sour tang into a sweet sparkle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and each one helps in a different way.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes someone stop and notice.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different form or state.",
        ),
        QAItem(
            question="What does tang usually mean?",
            answer="Tang can mean a sharp, sour smell or taste that makes you notice it right away.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return story_prompts(world)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(
        SETTINGS[params.setting],
        ACTIONS[params.action],
        PRIZES[params.prize],
        params.hero,
        params.helper1,
        params.helper2,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
holds_together(H) :- helper(H).
shines_together(S) :- helper(S).
hums_together(H) :- helper(H).
teamwork_complete :- holds_together(_), shines_together(_), hums_together(_).

sour(A) :- tang(A).
surprise(A) :- tang(A).
transformed(S) :- teamwork_complete, sour(A), sprite(S).

#show valid/3.
#show valid_story/4.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("valid", sid, "tang", "crown"))
    for aid in ACTIONS:
        lines.append(asp.fact("tang", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("helper", "a"))
    lines.append(asp.fact("helper", "b"))
    lines.append(asp.fact("helper", "c"))
    lines.append(asp.fact("valid_story", "valley", "tang", "crown", "fairy"))
    lines.append(asp.fact("valid_story", "grove", "tang", "crown", "fairy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("valley", "tang", "crown", "Tavi", "Brindle", "Luma", "curious"),
    StoryParams("grove", "tang", "crown", "Mira", "Cobb", "Fae", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.hero}: {p.setting} / {p.action} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
