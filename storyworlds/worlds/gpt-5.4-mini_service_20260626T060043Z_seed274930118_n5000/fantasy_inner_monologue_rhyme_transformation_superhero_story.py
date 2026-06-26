#!/usr/bin/env python3
"""
storyworlds/worlds/fantasy_inner_monologue_rhyme_transformation_superhero_story.py
===================================================================================

A small fantasy-superhero story world with three guiding features:
inner monologue, rhyme, and transformation.

Seed tale premise:
---
A shy child in a fantasy town hears trouble in the square. A stolen star-sigil
has dimmed the lantern tower, and a tiny dragon is too frightened to help. The
child thinks through the problem in a quiet inner monologue, speaks a rhyming
self-encouragement, and transforms into a bright superhero form. With courage,
a gadget, and a helper, the child restores the star-sigil and saves the night.

World model:
---
- A hero has bravery, sparkle, and a transformed superhero form.
- A threat can darken the lantern tower and frighten a helper.
- A magical rhyme can trigger transformation if the hero has enough courage.
- Transformation changes what the hero can do physically, and also boosts
  confidence and hope.
- Resolution restores light and ends with a triumphant fantasy image.

The script is intentionally self-contained and uses only the stdlib plus the
shared result containers.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    companion: Optional[str] = None
    worn_by: Optional[str] = None
    grants: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
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
    fantasy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    noun: str
    verb: str
    effect: str
    damage: str
    target: str
    zone: set[str]
    rhyme_word: str
    keyword: str = "fantasy"


@dataclass
class Power:
    id: str
    label: str
    phrase: str
    grants: set[str]
    trigger: str
    transform_to: str
    rhyme_line: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.state: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = copy.deepcopy(self.facts)
        clone.state = copy.deepcopy(self.state)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lantern_square": Setting("the lantern square", True, {"watch", "rescue", "shine"}),
    "moon_bridge": Setting("the moon bridge", True, {"cross", "rescue", "shine"}),
    "ivy_keep": Setting("the ivy keep", True, {"watch", "rescue", "climb"}),
}

TROUBLES = {
    "storm": Trouble(
        id="storm",
        noun="storm cloud",
        verb="smother",
        effect="dimming",
        damage="dark",
        target="lantern tower",
        zone={"sky", "tower"},
        rhyme_word="glow",
    ),
    "thorn": Trouble(
        id="thorn",
        noun="thorn bramble",
        verb="tangle",
        effect="snagging",
        damage="stuck",
        target="bridge gate",
        zone={"ground", "feet"},
        rhyme_word="free",
    ),
    "smoke": Trouble(
        id="smoke",
        noun="smoke puff",
        verb="fog",
        effect="clouding",
        damage="gray",
        target="sky lantern",
        zone={"sky", "hands"},
        rhyme_word="bright",
    ),
}

POWERS = {
    "star_cape": Power(
        id="star_cape",
        label="star cape",
        phrase="a silver star cape",
        grants={"fly", "shine", "brave"},
        trigger="When I hear the rhyme, I can rise in time",
        transform_to="star-suited hero",
        rhyme_line="Star and spark, I'll light the dark!",
        plural=False,
    ),
    "moon_mask": Power(
        id="moon_mask",
        label="moon mask",
        phrase="a moon mask with a bright clasp",
        grants={"see", "dash", "brave"},
        trigger="When I speak with care, moon power answers there",
        transform_to="moon-glimmer hero",
        rhyme_line="Moon so round, I'm strong and sound!",
        plural=False,
    ),
    "comet_boots": Power(
        id="comet_boots",
        label="comet boots",
        phrase="comet boots with golden sparks",
        grants={"run", "jump", "brave"},
        trigger="When my thoughts turn bold, my feet turn gold",
        transform_to="comet-crowned hero",
        rhyme_line="Comet feet, we can't be beat!",
        plural=True,
    ),
}

HERO_NAMES = ["Nia", "Milo", "Tess", "Arin", "Luna", "Jasper", "Iris", "Finn"]
HELPER_NAMES = ["Pip", "Brim", "Suki", "Cleo"]
TRAITS = ["shy", "small", "gentle", "curious", "quiet", "nervy"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    power: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for trouble_id, t in TROUBLES.items():
            if trouble_id not in s.affords and "rescue" not in s.affords:
                continue
            for power_id, p in POWERS.items():
                if power_id == "star_cape" and trouble_id == "storm":
                    out.append((place, trouble_id, power_id))
                elif power_id == "moon_mask" and trouble_id in {"smoke", "storm"}:
                    out.append((place, trouble_id, power_id))
                elif power_id == "comet_boots" and trouble_id in {"thorn", "smoke"}:
                    out.append((place, trouble_id, power_id))
    return out


def choose_power(trouble: Trouble) -> Power:
    if trouble.id == "storm":
        return POWERS["star_cape"]
    if trouble.id == "thorn":
        return POWERS["comet_boots"]
    return POWERS["moon_mask"]


def hero_innermonologue(hero: Entity, trouble: Trouble, power: Power) -> list[str]:
    return [
        f"\"{hero.id}, breathe,\" {hero.pronoun('object')} told {hero.pronoun('object')}self. "
        f"\"The {trouble.noun} looks huge, but I can still think.\"",
        f"\"If I trust the {power.label}, then I can change the night.\"",
    ]


def predict_resolution(world: World, hero: Entity, trouble: Trouble) -> bool:
    sim = world.copy()
    simulate_transformation(sim, hero.id, trouble.id, narrate=False)
    return bool(sim.facts.get("resolved"))


def simulate_transformation(world: World, hero_id: str, trouble_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    trouble = TROUBLES[trouble_id]
    power = world.facts["power"]

    if hero.memes.get("courage", 0.0) < THRESHOLD:
        return

    sig = ("transform", hero.id, power.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    hero.meters["spark"] = hero.meters.get("spark", 0.0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)

    old_form = hero.type
    hero.type = power.transform_to
    hero.label = f"{hero.id} in {power.label}"
    hero.meters["power"] = hero.meters.get("power", 0.0) + 1

    world.facts["transformed"] = True
    if narrate:
        world.say(
            f'{hero.id} whispered, "{power.rhyme_line}" and felt a bright change begin.'
        )
        world.say(
            f"{hero.id}'s shoulders shimmered, {hero.pronoun()} grew bold, and "
            f"{hero.pronoun('possessive')} {old_form} self became a {power.transform_to}."
        )


def resolve_trouble(world: World, hero_id: str, trouble_id: str, helper_id: str) -> None:
    hero = world.get(hero_id)
    helper = world.get(helper_id)
    trouble = TROUBLES[trouble_id]
    power: Power = world.facts["power"]

    if hero.type != power.transform_to:
        raise StoryError("The hero must transform before solving the trouble.")

    sig = ("resolve", trouble.id, hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    if trouble.id == "storm":
        world.say(
            f"With a star-bright sweep, {hero.id} flew up to the lantern tower and "
            f"pushed the storm cloud aside."
        )
    elif trouble.id == "thorn":
        world.say(
            f"With quick comet steps, {hero.id} zipped across the thorn bramble "
            f"and snapped the tangled vines apart."
        )
    else:
        world.say(
            f"With moon-bright eyes, {hero.id} found the smoky trail and waved it "
            f"away from the sky lantern."
        )

    helper.memes["hope"] = helper.memes.get("hope", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.facts["resolved"] = True
    world.facts["helper"] = helper
    world.say(
        f"{helper.id} clapped, and the bright magic returned to {trouble.target}."
    )


def tell_story(world: World, hero: Entity, helper: Entity, trouble: Trouble, power: Power) -> World:
    world.facts.update(hero=hero, helper=helper, trouble=trouble, power=power)

    world.say(
        f"In {world.setting.place}, {hero.id} was a {hero.meters.get('height_word', 'small')} "
        f"{hero.type if hero.type != 'thing' else 'child'} who loved the whisper of fantasy nights."
    )
    world.say(
        f"Still, {hero.id} had a shy heart, and {hero.pronoun('possessive')} "
        f"courage meter was low when the {trouble.noun} drifted over the square."
    )

    world.para()
    world.say(
        f"The {trouble.noun} began to {trouble.verb} the {trouble.target}, leaving the air "
        f"{trouble.damage} and dull."
    )
    world.say(
        f"{helper.id} looked small beside the trouble, so {hero.id} had to decide what to do."
    )
    for line in hero_innermonologue(hero, trouble, power):
        world.say(line)

    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"{hero.id} took one tiny step and said the rhyme out loud: \"{power.rhyme_line}\""
    )

    simulate_transformation(world, hero.id, trouble.id, narrate=True)

    world.para()
    resolve_trouble(world, hero.id, trouble.id, helper.id)

    if world.facts.get("resolved"):
        world.say(
            f"In the end, {hero.id} stood tall in {power.label}, and the night looked "
            f"like a storybook sky with a new golden glow."
        )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "fantasy": [
        (
            "What is a fantasy story?",
            "A fantasy story is a made-up story that can have magic, strange creatures, and wonderful places that do not exist in real life.",
        )
    ],
    "transform": [
        (
            "What does it mean to transform?",
            "To transform means to change into a different form, often in a big and surprising way.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like bright and light.",
        )
    ],
    "inner_monologue": [
        (
            "What is inner monologue?",
            "Inner monologue is the quiet thinking a character does inside their own mind.",
        )
    ],
    "hero": [
        (
            "What is a superhero?",
            "A superhero is a character who uses special powers and brave choices to help others.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    power = f["power"]
    return [
        f'Write a short fantasy superhero story for young children that includes inner monologue and the rhyme "{power.rhyme_line}".',
        f"Tell a gentle story where {hero.id} feels shy at first, thinks quietly, transforms, and helps with the {trouble.noun}.",
        f'Write a story about a child who says "{power.rhyme_line}" and becomes brave enough to save the day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    trouble = f["trouble"]
    power = f["power"]
    qa = [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"The story was about {hero.id}, a {hero.pronoun('object')} who started out shy but became brave in the fantasy town.",
        ),
        QAItem(
            question=f"What problem did {hero.id} have to solve?",
            answer=f"{hero.id} had to stop the {trouble.noun} from {trouble.verb}ing the {trouble.target} and making everything go dark.",
        ),
        QAItem(
            question=f"What rhyme helped {hero.id} change?",
            answer=f'{hero.id} said "{power.rhyme_line}", and that rhyme helped trigger the transformation.',
        ),
        QAItem(
            question=f"Who helped at the end?",
            answer=f"{helper.id} helped by watching closely and cheering when the bright magic came back.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"What changed after {hero.id} transformed?",
                answer=f"{hero.id} changed from a shy child into a {power.transform_to}, and then {hero.id} could solve the trouble with brave, quick action.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["fantasy", "inner_monologue", "rhyme", "transform", "hero"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
trouble(T) :- trouble_id(T).
power(P) :- power_id(P).

compatible(P, T) :- power_kind(P, star), trouble_kind(T, storm).
compatible(P, T) :- power_kind(P, moon), trouble_kind(T, smoke).
compatible(P, T) :- power_kind(P, moon), trouble_kind(T, storm).
compatible(P, T) :- power_kind(P, comet), trouble_kind(T, thorn).
compatible(P, T) :- power_kind(P, comet), trouble_kind(T, smoke).

valid_story(P, T) :- compatible(P, T).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble_id", tid))
        lines.append(asp.fact("trouble_kind", tid, t.id))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power_id", pid))
        if pid == "star_cape":
            lines.append(asp.fact("power_kind", pid, "star"))
        elif pid == "moon_mask":
            lines.append(asp.fact("power_kind", pid, "moon"))
        else:
            lines.append(asp.fact("power_kind", pid, "comet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((p, t) for p, t, _ in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="lantern_square", trouble="storm", power="star_cape", name="Nia", helper="Pip", trait="shy"),
    StoryParams(place="moon_bridge", trouble="thorn", power="comet_boots", name="Milo", helper="Brim", trait="quiet"),
    StoryParams(place="ivy_keep", trouble="smoke", power="moon_mask", name="Luna", helper="Suki", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fantasy superhero story world with inner monologue, rhyme, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    if args.power and args.trouble:
        p, t = POWERS[args.power], TROUBLES[args.trouble]
        ok = (p.id == "star_cape" and t.id == "storm") or \
             (p.id == "moon_mask" and t.id in {"smoke", "storm"}) or \
             (p.id == "comet_boots" and t.id in {"thorn", "smoke"})
        if not ok:
            raise StoryError("That power cannot reasonably solve that trouble.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.power is None or c[2] == args.power)]
    if not combos:
        raise StoryError("No valid story matches the requested options.")
    place, trouble, power = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        trouble=trouble,
        power=power,
        name=args.name or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Nia", "Tess", "Luna", "Iris"} else "boy",
        meters={"spark": 0.0, "power": 0.0},
        memes={"fear": 1.0, "courage": 0.0, "confidence": 0.0, "joy": 0.0, "bravery": 0.0},
    ))
    helper = world.add(Entity(id=params.helper, kind="character", type="sprite", meters={}, memes={"hope": 0.0}))
    trouble = TROUBLES[params.trouble]
    power = POWERS[params.power]

    world.facts.update(hero=hero, helper=helper, trouble=trouble, power=power)
    tell_story(world, hero, helper, trouble, power)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.grants:
            bits.append(f"grants={sorted(e.grants)}")
        lines.append(f"  {e.id:10} ({e.type:18}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, t in combos:
            print(f"  {p:14} {t:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
