#!/usr/bin/env python3
"""
storyworlds/worlds/cheek_dim_reconciliation_twist_misunderstanding_mystery.py
=============================================================================

A small mystery storyworld with a child-friendly misunderstanding, a twist, and
a reconciliation beat. The seed word "cheek-dim" is treated as a world texture:
the light is dim enough to make faces and clues easy to misread.

The domain premise:
- A young sleuth notices a strange clue in a cheek-dim room.
- A misunderstanding makes them suspect the wrong person.
- A twist reveals the clue's true source.
- Reconciliation follows once the mistake is repaired.

The story is modeled as a tiny simulation:
- Characters and objects have physical meters and emotional memes.
- Clues can be hidden, misread, revealed, or matched to their owner.
- A mistaken accusation increases conflict; the correction lowers it.
- The ending image proves what changed in the world.

The world stays small on purpose: only the combinations that produce a sensible
mystery are allowed.

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
    discovered_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    misread_as: str
    true_source: str
    twist: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_discovery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    clue = world.get("clue")
    if clue.hidden and hero.meters.get("observing", 0) >= THRESHOLD:
        sig = ("discover", clue.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        clue.hidden = False
        clue.discovered_by = hero.id
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
        out.append(f"{hero.id} noticed a small clue by the wall.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    clue = world.get("clue")
    if clue.hidden:
        return []
    if hero.memes.get("suspicion", 0) < THRESHOLD:
        return []
    sig = ("misunderstanding", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["hurt"] = helper.memes.get("hurt", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    return ["__misunderstanding__"]


def _r_twist(world: World) -> list[str]:
    clue = world.get("clue")
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    if clue.hidden:
        return []
    if hero.meters.get("checking", 0) < THRESHOLD:
        return []
    sig = ("twist", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    return [world.facts["mystery"].twist]


def _r_reconciliation(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    if hero.memes.get("conflict", 0) < THRESHOLD:
        return []
    if hero.meters.get("apology", 0) < THRESHOLD:
        return []
    sig = ("reconcile", hero.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] = 0
    helper.memes["hurt"] = 0
    hero.memes["warmth"] = hero.memes.get("warmth", 0) + 1
    helper.memes["warmth"] = helper.memes.get("warmth", 0) + 1
    return [world.facts["mystery"].fix]


CAUSAL_RULES = [
    _r_discovery,
    _r_misunderstanding,
    _r_twist,
    _r_reconciliation,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__misunderstanding__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "hall": Setting(
        place="the hall",
        detail="The hall was cheek-dim, with a narrow lamp leaving the corners soft and blue.",
        affords={"inspect", "search"},
    ),
    "garden": Setting(
        place="the garden",
        detail="The garden looked quiet under the late light, and the hedges made hiding places.",
        affords={"inspect", "search"},
    ),
    "kitchen": Setting(
        place="the kitchen",
        detail="The kitchen had one small lamp on, so every spoon and bowl cast a long shadow.",
        affords={"inspect", "search"},
    ),
}

MYSTERIES = {
    "green_smudge": Mystery(
        id="green_smudge",
        clue="a green smudge on the windowsill",
        misread_as="paint left by a careless guest",
        true_source="a dusty leaf that brushed the sill in the wind",
        twist="The green mark was not paint at all; it was a leaf-print from the open window.",
        fix="Then the hero turned and smiled at the helper. 'I was wrong,' the hero said, and the helper smiled back.",
        tags={"leaf", "window", "green"},
    ),
    "tiny_bells": Mystery(
        id="tiny_bells",
        clue="the faint jingle of tiny bells",
        misread_as="a sneaky visitor hiding nearby",
        true_source="a kitten's collar from the next room",
        twist="The jingle came from a kitten, not a stranger.",
        fix="The hero laughed softly and apologized for the worry, and the helper's shoulders relaxed at once.",
        tags={"bell", "cat", "sound"},
    ),
    "blue_scratch": Mystery(
        id="blue_scratch",
        clue="a blue scratch on the table",
        misread_as="a mark made by a broken toy",
        true_source="a ribbon caught under a bowl and dragged across the wood",
        twist="The scratch was only a ribbon trail, not damage from a broken toy.",
        fix="The hero and helper put the bowl back together and shared a small relieved grin.",
        tags={"ribbon", "table", "blue"},
    ),
}

HERO_NAMES = ["Mia", "Noah", "Lina", "Eli", "Ava", "Finn", "Zoe", "Theo"]
HELPER_NAMES = ["June", "Milo", "Iris", "Ben", "Nora", "Otto", "Lila", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if "search" in setting.affords and "inspect" in setting.affords:
                combos.append((place, mid))
    return combos


def select_name(rng: random.Random, gender: str, used: set[str]) -> str:
    pool = HERO_NAMES if gender == "girl" else [n for n in HELPER_NAMES if n not in used]
    if not pool:
        pool = HERO_NAMES + HELPER_NAMES
    choice = rng.choice(pool)
    used.add(choice)
    return choice


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if not valid_combos():
        raise StoryError("No valid mystery combinations available.")


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label="clue",
        phrase=mystery.clue,
        hidden=True,
    ))

    world.facts.update(hero=hero, helper=helper, mystery=mystery)

    world.say(f"{hero.id} and {helper.id} walked into {setting.place}.")
    world.say(setting.detail)
    world.say(f"{hero.id} was a little {hero.type} with a careful eye, and {helper.id} liked to listen.")

    world.para()
    world.say(f"Then {hero.id} noticed {mystery.clue}.")
    hero.meters["observing"] = 1
    propagate(world, narrate=True)

    world.para()
    hero.memes["suspicion"] = 1
    world.say(f"In the cheek-dim light, {hero.id} guessed it was {mystery.misread_as}.")
    world.say(f"{helper.id} looked surprised and hurt, because that was not what had happened.")

    propagate(world, narrate=True)

    world.para()
    hero.meters["checking"] = 1
    world.say(f"{hero.id} looked closer and followed the clue all the way to its true source.")
    propagate(world, narrate=True)

    world.para()
    hero.meters["apology"] = 1
    world.say(f"{hero.id} took a breath and said sorry to {helper.id}.")
    propagate(world, narrate=True)

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["clue"] = clue
    return world


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        f'Write a child-friendly mystery story in a cheek-dim place that includes "{m.clue}".',
        f"Tell a story where {hero.id} misunderstands {helper.id}, then learns the truth and reconciles.",
        f"Write a short mystery with a twist and a gentle apology at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    setting: Setting = world.setting
    return [
        QAItem(
            question=f"Who was looking for answers in {setting.place}?",
            answer=f"{hero.id} was looking for answers in {setting.place}, and {helper.id} stayed beside {hero.pronoun('object')} while they searched.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed {mystery.clue} first.",
        ),
        QAItem(
            question=f"What mistake did {hero.id} make in the cheek-dim light?",
            answer=f"{hero.id} thought the clue was {mystery.misread_as}. That was the misunderstanding.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=mystery.twist,
        ),
        QAItem(
            question=f"How did the story end between {hero.id} and {helper.id}?",
            answer=f"{mystery.fix} They ended the story calm, close, and friendly again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story about noticing clues, asking questions, and finding out what really happened.",
        ),
        QAItem(
            question="Why can dim light cause a misunderstanding?",
            answer="Dim light can make shapes and colors harder to see, so someone may guess wrong before they look again.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, talk kindly, and make peace after a disagreement.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader thought was true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.hidden:
            bits.append("hidden=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.kind:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid if the place affords searching and inspecting.
valid_story(P, M) :- setting(P), mystery(M), affords(P, search), affords(P, inspect).

% The clue can be discovered when the hero is observing.
discoverable(H, C) :- observing(H), clue(C).

% A misunderstanding happens when a discovered clue is misread.
misunderstanding(H, M) :- discoverable(H, C), clue_for(C, M).

% The twist arrives after closer checking.
twist(H, M) :- checking(H), clue_for(_, M).

% Reconciliation requires an apology after conflict.
reconciled(H, X) :- apology(H), conflict(H), helper(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_for", f"clue_{mid}", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cheek-dim mystery with misunderstanding, twist, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid mystery combination matches the given options.")
    place, mystery = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    used: set[str] = set()
    hero_name = args.hero_name or select_name(rng, hero_gender, used)
    helper_name = args.helper_name or select_name(rng, helper_gender, used)
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def select_name(rng: random.Random, gender: str, used: set[str]) -> str:
    pool = HERO_NAMES if gender == "girl" else HELPER_NAMES
    pool = [n for n in pool if n not in used] or HERO_NAMES + HELPER_NAMES
    name = rng.choice(pool)
    used.add(name)
    return name


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
    )
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


CURATED = [
    StoryParams(place="hall", mystery="green_smudge", hero_name="Mia", hero_gender="girl", helper_name="June", helper_gender="girl"),
    StoryParams(place="kitchen", mystery="tiny_bells", hero_name="Noah", hero_gender="boy", helper_name="Nora", helper_gender="girl"),
    StoryParams(place="garden", mystery="blue_scratch", hero_name="Ava", hero_gender="girl", helper_name="Ben", helper_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:")
        for place, mystery in combos:
            print(f"  {place:8} {mystery}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
