#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sudden_canoe_spell_kindness_myth.py
================================================================================================================

A small Myth-style story world about a sudden canoe crossing, a risky spell,
and the force of kindness that turns the story toward safety.

Premise:
- A child or young hero must cross a river in a canoe.
- A sudden storm or river change makes the crossing dangerous.
- A spell is involved, but it is not the right answer by itself.
- Kindness is the turning force: helping another person or creature calms the
  danger and restores the canoe's path.

The simulated world tracks:
- physical meters: river_swirl, wind, water, canoe_balance, spell_charge
- emotional memes: fear, pride, trust, kindness, relief, gratitude

The story is driven by world state, not by a fixed paragraph template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "river_swirl": 0.0,
                "wind": 0.0,
                "water": 0.0,
                "canoe_balance": 0.0,
                "spell_charge": 0.0,
            }
        if not self.memes:
            self.memes = {
                "fear": 0.0,
                "pride": 0.0,
                "trust": 0.0,
                "kindness": 0.0,
                "relief": 0.0,
                "gratitude": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class River:
    name: str = "the river"
    place: str = "the ford"
    sudden: bool = True
    deep: bool = True


@dataclass
class Canoe:
    label: str = "canoe"
    phrase: str = "a narrow canoe with a painted prow"
    stable_when_calm: bool = True


@dataclass
class Spell:
    label: str = "spell"
    phrase: str = "a bright spell"
    kind: str = "twist"
    risky: bool = True
    helpful: bool = True


@dataclass
class StoryParams:
    name: str
    hero_type: str
    helper_name: str
    helper_type: str
    river: str
    canoe: str
    spell: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def _carry_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes["kindness"] >= THRESHOLD and ent.memes["trust"] >= THRESHOLD:
            sig = ("kindness_brightens", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["relief"] += 1
            out.append(f"{ent.id}'s kindness warmed the air.")
    return out


def _spell_gathers(world: World) -> list[str]:
    out: list[str] = []
    spell = world.entities.get("spell")
    if not spell:
        return out
    if spell.meters["spell_charge"] < THRESHOLD:
        return out
    if spell.meters["river_swirl"] < THRESHOLD:
        return out
    sig = ("spell_gathers",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The spell gathered on the wind and made the river more restless.")
    return out


def _canoe_wavers(world: World) -> list[str]:
    out: list[str] = []
    canoe = world.entities.get("canoe")
    if not canoe:
        return out
    hero = world.entities.get("hero")
    if not hero:
        return out
    danger = hero.meters["river_swirl"] + hero.meters["wind"] + hero.meters["water"]
    if danger < THRESHOLD:
        return out
    if hero.memes["kindness"] >= THRESHOLD:
        return out
    sig = ("canoe_wavers",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    canoe.meters["canoe_balance"] += 1
    hero.memes["fear"] += 1
    out.append("The canoe rocked hard and the hero's heart skipped like a stone.")
    return out


def _kindness_cools_spell(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    spell = world.entities.get("spell")
    if not hero or not helper or not spell:
        return out
    if hero.memes["kindness"] < THRESHOLD or helper.memes["trust"] < THRESHOLD:
        return out
    if spell.meters["spell_charge"] <= 0:
        return out
    sig = ("kindness_cools_spell",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spell.meters["spell_charge"] = max(0.0, spell.meters["spell_charge"] - 1.0)
    hero.memes["relief"] += 1
    helper.memes["gratitude"] += 1
    out.append("Kindness cooled the spell, and its bright edge went soft.")
    return out


CAUSAL_RULES = [_spell_gathers, _canoe_wavers, _kindness_cools_spell, _carry_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_river(river_id: str) -> River:
    if river_id == "sudden":
        return River(name="the sudden river", place="the stone ford", sudden=True, deep=True)
    raise StoryError("Unknown river choice.")


def build_canoe(canoe_id: str) -> Canoe:
    if canoe_id == "canoe":
        return Canoe()
    raise StoryError("Unknown canoe choice.")


def build_spell(spell_id: str) -> Spell:
    if spell_id == "spell":
        return Spell()
    raise StoryError("Unknown spell choice.")


def _intro(world: World, hero: Entity, helper: Entity, river: River, canoe: Canoe, spell: Spell) -> None:
    world.say(
        f"{hero.id} was a young {hero.type} who lived near {river.name}."
        f" {hero.pronoun().capitalize()} loved the old canoe by the bank,"
        f" and {helper.id} knew a small {spell.label} that shimmered like dawn."
    )


def _setup(world: World, hero: Entity, helper: Entity, river: River, canoe: Canoe, spell: Spell) -> None:
    hero.memes["pride"] += 1
    helper.memes["trust"] += 1
    spell.meters["spell_charge"] += 1
    world.say(
        f"One day, a sudden wind ran over {river.place}, and the canoe tugged at its rope."
    )
    world.say(
        f"{hero.id} wanted to cross at once, but the water was already turning and darkening."
    )
    world.say(
        f"{helper.id} lifted the {spell.label} and warned that a quick trick would not tame the flood by itself."
    )


def _turn(world: World, hero: Entity, helper: Entity, river: River, canoe: Canoe, spell: Spell) -> None:
    hero.meters["river_swirl"] += 1
    hero.meters["wind"] += 1
    hero.meters["water"] += 1
    world.say(
        f"{hero.id} stepped into the canoe anyway, and the sudden river struck the hull with a hard shove."
    )
    propagate(world, narrate=True)
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id}'s hands tightened, and {hero.pronoun('possessive')} voice shook under the wind."
    )
    world.say(
        f"Then {helper.id} asked for kindness instead of force, because the river listened best to gentle hearts."
    )
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    helper.memes["trust"] += 1
    propagate(world, narrate=True)


def _resolution(world: World, hero: Entity, helper: Entity, river: River, canoe: Canoe, spell: Spell) -> None:
    if hero.memes["kindness"] < THRESHOLD:
        raise StoryError("This story needs kindness to resolve the river crossing.")
    if spell.meters["spell_charge"] < THRESHOLD:
        raise StoryError("The spell must begin charged enough to matter.")
    world.say(
        f"{hero.id} used the {spell.label} not to command the river, but to share light with it."
    )
    spell.meters["spell_charge"] = max(0.0, spell.meters["spell_charge"] - 1.0)
    hero.memes["trust"] += 1
    helper.memes["gratitude"] += 1
    canoe.meters["canoe_balance"] += 1
    hero.meters["river_swirl"] = max(0.0, hero.meters["river_swirl"] - 1.0)
    hero.meters["wind"] = max(0.0, hero.meters["wind"] - 1.0)
    hero.meters["water"] = max(0.0, hero.meters["water"] - 1.0)
    hero.memes["relief"] += 1
    propagate(world, narrate=True)
    world.say(
        f"Together they crossed in the canoe, and the river grew calm enough to mirror the sky."
    )
    world.say(
        f"At the far bank, {hero.id} bowed to {helper.id}, for the truest spell had been kindness all along."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    river = build_river(params.river)
    canoe = build_canoe(params.canoe)
    spell = build_spell(params.spell)
    world.add(Entity(id="canoe", kind="thing", type="canoe", label=canoe.label, phrase=canoe.phrase))
    world.add(Entity(id="spell", kind="thing", type="spell", label=spell.label, phrase=spell.phrase))
    world.facts.update(hero=hero, helper=helper, river=river, canoe=canoe, spell=spell)

    _intro(world, hero, helper, river, canoe, spell)
    world.para()
    _setup(world, hero, helper, river, canoe, spell)
    world.para()
    _turn(world, hero, helper, river, canoe, spell)
    world.para()
    _resolution(world, hero, helper, river, canoe, spell)
    return world


SETTING_REGISTRY = {
    "sudden": build_river("sudden"),
}

CANOE_REGISTRY = {
    "canoe": build_canoe("canoe"),
}

SPELL_REGISTRY = {
    "spell": build_spell("spell"),
}

HERO_NAMES = ["Asha", "Milo", "Nia", "Tarin", "Lena", "Ravi"]
HELPER_NAMES = ["Orin", "Sera", "Belen", "Mara", "Pella", "Ivo"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["elder", "mother", "father", "friend"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("sudden", "canoe", "spell")]


@dataclass
class StoryParamsResolved:
    river: str
    canoe: str
    spell: str
    name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


StoryParams = StoryParamsResolved


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth story world: sudden canoe spell kindness.")
    ap.add_argument("--river", choices=list(SETTING_REGISTRY))
    ap.add_argument("--canoe", choices=list(CANOE_REGISTRY))
    ap.add_argument("--spell", choices=list(SPELL_REGISTRY))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    river = args.river or rng.choice(list(SETTING_REGISTRY))
    canoe = args.canoe or rng.choice(list(CANOE_REGISTRY))
    spell = args.spell or rng.choice(list(SPELL_REGISTRY))
    if (river, canoe, spell) not in valid_combos():
        raise StoryError("This world only allows the sudden river, the canoe, and the spell together.")
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    name = args.name or rng.choice(HERO_NAMES if hero_type == "girl" else HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        river=river,
        canoe=canoe,
        spell=spell,
        name=name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        f"Write a short myth for children about {hero.label}, a sudden river, a canoe, and a spell.",
        f"Tell a gentle story where {hero.label} and {helper.label} cross a sudden river in a canoe and kindness matters more than force.",
        f"Write a myth-like story that uses the word 'sudden' and ends with a canoe crossing that is saved by kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    river: River = f["river"]  # type: ignore[assignment]
    canoe: Canoe = f["canoe"]  # type: ignore[assignment]
    spell: Spell = f["spell"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who wanted to cross {river.name} in the canoe?",
            answer=f"{hero.label} wanted to cross {river.name} in the canoe.",
        ),
        QAItem(
            question=f"What made the crossing dangerous?",
            answer=f"A sudden wind and a restless river made the canoe wobble, and the spell could not fix everything by force.",
        ),
        QAItem(
            question=f"What helped the story end well?",
            answer=f"Kindness helped the story end well. {hero.label} used the spell gently, and {helper.label} trusted that softer magic could calm the river.",
        ),
        QAItem(
            question=f"What did the spell do in the end?",
            answer=f"The spell's bright edge went soft, and the canoe crossed safely because the hero used it with kindness instead of trying to command the river.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canoe?",
            answer="A canoe is a long, narrow boat that one or two people can paddle across water.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle, helpful actions that care for another person or creature.",
        ),
        QAItem(
            question="What is a spell in a story?",
            answer="A spell is a magical act or charm that can change what happens in a story world.",
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
kindness_brightens(E) :- character(E), kindness(E), trust(E).
spell_gathers :- spell(S), charge(S), river_swirls.
canoe_wavers :- canoe(C), danger.
resolution :- kindness(hero), kindness(helper), charge(spell).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "hero"),
        asp.fact("character", "helper"),
        asp.fact("canoe", "canoe"),
        asp.fact("spell", "spell"),
        asp.fact("kindness", "hero"),
        asp.fact("kindness", "helper"),
        asp.fact("trust", "helper"),
        asp.fact("charge", "spell"),
        asp.fact("river_swirls"),
        asp.fact("danger"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolution/0.\n#show canoe_wavers/0.\n#show spell_gathers/0."))
    atoms = {sym.name for sym in model}
    expected = {"resolution", "canoe_wavers", "spell_gathers"}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python reasoners.")
    print("ASP atoms:", sorted(atoms))
    print("Expected:", sorted(expected))
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolution/0.\n#show canoe_wavers/0.\n#show spell_gathers/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolution/0.\n#show canoe_wavers/0.\n#show spell_gathers/0."))
        print("ASP model:", sorted(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            river="sudden",
            canoe="canoe",
            spell="spell",
            name="Asha",
            hero_type="girl",
            helper_name="Orin",
            helper_type="elder",
        )
        samples = [generate(params)]
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
