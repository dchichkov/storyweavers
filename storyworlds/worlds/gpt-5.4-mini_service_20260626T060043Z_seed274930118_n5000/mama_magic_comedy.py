#!/usr/bin/env python3
"""
A tiny comedy-magic storyworld about a mama whose careful spell plans keep a
small household mishap funny instead of disastrous.

Premise:
- A child wants to use a magic trick.
- Mama knows the trick can go silly in a specific way.
- They argue a little, then find a safer magical version.
- The ending proves the change in the world state.

This script is standalone and follows the storyworld contract.
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
# World model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: {"mess": 0.0, "sparkle": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "worry": 0.0, "laugh": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mama", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Spell:
    id: str
    label: str
    verb: str
    hazard: str
    result: str
    mess_kind: str
    splash_zone: set[str]
    fix_label: str
    fix_kind: str
    fix_covers: set[str]
    fix_guards: set[str]


@dataclass
class StoryParams:
    spell: str
    name: str
    child_type: str
    mother_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, spell: Spell):
        self.spell = spell
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        import copy
        w = World(self.spell)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SPELLS = {
    "broom-bubbles": Spell(
        id="broom-bubbles",
        label="broom-bubbles",
        verb="make the broom dance",
        hazard="sprinkle soap foam everywhere",
        result="the floor turns foamy",
        mess_kind="foam",
        splash_zone={"floor", "hands"},
        fix_label="an apron",
        fix_kind="apron",
        fix_covers={"torso"},
        fix_guards={"foam"},
    ),
    "cookie-crowns": Spell(
        id="cookie-crowns",
        label="cookie-crowns",
        verb="turn plain cookies into tiny crowns",
        hazard="dust the kitchen with sugar glitter",
        result="the table sparkles",
        mess_kind="glitter",
        splash_zone={"table", "hands"},
        fix_label="a baking cape",
        fix_kind="baking cape",
        fix_covers={"torso"},
        fix_guards={"glitter"},
    ),
    "singing-spoons": Spell(
        id="singing-spoons",
        label="singing-spoons",
        verb="make the spoons sing",
        hazard="jiggle jam onto the chairs",
        result="the room gets sticky",
        mess_kind="jam",
        splash_zone={"chairs", "hands"},
        fix_label="oven mitts",
        fix_kind="oven mitts",
        fix_covers={"hands"},
        fix_guards={"jam"},
    ),
}

NAMES = ["Lina", "Milo", "Nia", "Owen", "Pia", "Theo"]
MAMA_NAMES = ["Mama June", "Mama Rose", "Mama Lin", "Mama Bea", "Mama Dot"]
CHILD_TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def spell_at_risk(spell: Spell) -> bool:
    return bool(spell.splash_zone)


def select_fix(spell: Spell) -> Optional[tuple[str, str]]:
    if spell.fix_kind and spell.mess_kind in spell.fix_guards:
        return spell.fix_kind, spell.fix_label
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, spell in SPELLS.items():
        if spell_at_risk(spell) and select_fix(spell):
            out.append(("kitchen", sid))
    return out


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def predict_mess(world: World, child: Entity) -> bool:
    sim = world.copy()
    perform_magic(sim, child, narrate=False)
    return any(e.meters["mess"] >= THRESHOLD for e in sim.entities.values())


def perform_magic(world: World, child: Entity, narrate: bool = True) -> None:
    spell = world.spell
    child.meters["mess"] += 1
    child.meters[spell.mess_kind] = child.meters.get(spell.mess_kind, 0.0) + 1
    child.memes["joy"] += 1
    if narrate:
        world.say(f"{child.id} tried to {spell.verb}, and the magic popped like a joke.")
    for item in world.entities.values():
        if item.worn_by == child.id and spell.mess_kind in item.covers:
            sig = ("mess", item.id, spell.mess_kind)
            if sig not in world.fired:
                world.fired.add(sig)
                item.meters["mess"] += 1
                if narrate:
                    world.say(f"{item.label.capitalize()} got {spell.result} all over it.")


def maybe_warn(world: World, mama: Entity, child: Entity) -> bool:
    if not predict_mess(world, child):
        return False
    world.facts["worry"] = True
    world.say(
        f'"If you do that now, the {world.spell.label} will {world.spell.hazard}," '
        f"{mama.pronoun('subject').capitalize()} said, smiling because she knew the trick was funny, not scary."
    )
    return True


def offer_fix(world: World, mama: Entity, child: Entity) -> Optional[Entity]:
    fix = select_fix(world.spell)
    if not fix:
        return None
    fix_kind, fix_label = fix
    gear = world.add(Entity(
        id="fix",
        kind="thing",
        type=fix_kind,
        label=fix_label,
        protective=True,
        covers=set(world.spell.fix_covers),
        owner=child.id,
        caretaker=mama.id,
    ))
    if predict_mess(world, child):
        del world.entities[gear.id]
        return None
    world.say(
        f'{mama.id} grinned. "How about we use {fix_label} first, then try the magic?"'
    )
    return gear


def accept_fix(world: World, mama: Entity, child: Entity, gear: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["laugh"] += 1
    world.say(
        f"{child.id} giggled and hugged {mama.pronoun('object')}. "
        f"Together they put on {gear.label}, and the plan felt less like a mess and more like a prank."
    )
    world.say(
        f"At the end, {child.id} was still {world.spell.verb}, but the room stayed tidy and everybody laughed."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(spell: Spell, child_name: str, child_type: str, mama_name: str) -> World:
    world = World(spell)
    mama = world.add(Entity(id=mama_name, kind="character", type="mama", label="mama"))
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="teacup" if spell.id == "singing-spoons" else "kitchen floor",
        label="the little kitchen",
        phrase="the little kitchen",
        owner=child.id,
        caretaker=mama.id,
    ))
    _ = item

    world.say(f"{child.id} loved magic, especially the silly kind that made grown-ups groan and smile.")
    world.say(f"{mama_name} was a mama who could spot trouble and turn it into a joke.")
    world.say(f"One day, {child.id} wanted to {spell.verb}.")

    world.para()
    maybe_warn(world, mama, child)
    world.say(f"{child.id} tried to start anyway, but the spell only got more ridiculous.")
    world.say(f"Then the kitchen looked ready for {spell.result}.")

    world.para()
    gear = offer_fix(world, mama, child)
    if gear:
        accept_fix(world, mama, child, gear)
    else:
        world.say(f"So they paused, picked a calmer trick, and saved the big spell for later.")

    world.facts.update(child=child, mama=mama, gear=gear, spell=spell)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    spell = f["spell"]
    return [
        f'Write a short comedy story for a child about "{spell.label}" and a mama who finds a safer magic plan.',
        f"Tell a funny, gentle story where {f['child'].id} wants to {spell.verb} but {f['mama'].id} worries about the mess.",
        f'Write a child-friendly magic story that ends with everyone laughing and the room staying tidy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mama = f["mama"]
    spell = f["spell"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do with the magic?",
            answer=f"{child.id} wanted to {spell.verb}.",
        ),
        QAItem(
            question=f"Why did {mama.id} worry about the spell?",
            answer=f"{mama.id} worried because the {spell.label} would {spell.hazard} and make a mess.",
        ),
        QAItem(
            question="What made the story end happily?",
            answer=f"They chose a safer plan with {world.get('fix').label if f.get('gear') else 'a calmer trick'}, so the magic stayed funny and the room stayed tidy.",
        ),
    ]
    if f.get("gear"):
        qa.append(QAItem(
            question="What helped the child try the magic without making a mess?",
            answer=f"{f['gear'].label} helped because it covered the right part and kept the {spell.mess_kind} away.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who is a mama?",
            answer="A mama is a mother who cares for a child and helps keep things safe.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising that makes impossible things happen, like a spoon singing or a broom dancing.",
        ),
        QAItem(
            question="Why can comedy be funny?",
            answer="Comedy is funny because harmless trouble, odd sounds, and silly surprises can make people laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
spell_at_risk(S) :- spell(S), splash_zone(S,_).
has_fix(S) :- spell(S), fix(S), fix_guards(S,M), mess_of(S,M), fix_covers(S,_).
valid_story(S) :- spell_at_risk(S), has_fix(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("mess_of", sid, s.mess_kind))
        lines.append(asp.fact("fix", sid))
        lines.append(asp.fact("fix_guards", sid, s.mess_kind))
        for r in sorted(s.splash_zone):
            lines.append(asp.fact("splash_zone", sid, r))
        for r in sorted(s.fix_covers):
            lines.append(asp.fact("fix_covers", sid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((sid,) for _, sid in valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Python only:", sorted(py - asp_set))
    print("ASP only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy-magic storyworld with a mama and a safer spell.")
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--mother-name", choices=MAMA_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
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


def valid_story_choices() -> list[str]:
    return [sid for _, sid in valid_combos()]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spell and args.spell not in SPELLS:
        raise StoryError("Unknown spell.")
    spell_id = args.spell or rng.choice(valid_story_choices())
    if spell_id not in SPELLS:
        raise StoryError("No valid spell available.")
    name = args.name or rng.choice(NAMES)
    mother_name = args.mother_name or rng.choice(MAMA_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    return StoryParams(spell=spell_id, name=name, child_type=child_type, mother_name=mother_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SPELLS[params.spell], params.name, params.child_type, params.mother_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(spell="broom-bubbles", name="Lina", child_type="girl", mother_name="Mama Rose"),
    StoryParams(spell="cookie-crowns", name="Theo", child_type="boy", mother_name="Mama Bea"),
    StoryParams(spell="singing-spoons", name="Pia", child_type="girl", mother_name="Mama Lin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("\n".join(str(t) for t in asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
