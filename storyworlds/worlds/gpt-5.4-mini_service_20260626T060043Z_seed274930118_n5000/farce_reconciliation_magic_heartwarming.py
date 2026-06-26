#!/usr/bin/env python3
"""
storyworlds/worlds/farce_reconciliation_magic_heartwarming.py
==============================================================

A small storyworld about a magical farce that ends in reconciliation.

Premise:
- A child wants to use a bit of magic to make a simple task easier.
- The magic goes gloriously wrong in a silly, harmless way.
- Everybody gets flustered, then the family repairs the mistake together.
- The ending is warm, concrete, and shows what changed.

This world is intentionally narrow: it prefers a few plausible, good stories
over many weak variants.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    verb: str
    gerund: str
    glitch: str
    mess: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class MagicItem:
    id: str
    label: str
    prep: str
    fix: str
    produces: set[str]
    requires: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.silliness: float = 0.0

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.silliness = self.silliness
        w.paragraphs = [[]]
        return w


def _r_confetti(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("confusion", 0) < THRESHOLD:
            continue
        sig = ("confetti", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["confetti"] = e.meters.get("confetti", 0.0) + 1
        out.append(f"Soft confetti drifted onto the floor.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.silliness < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig not in world.fired:
        world.fired.add(sig)
        out.append("The room felt lighter, like laughter had turned on the lamp.")
    return out


CAUSAL_RULES = [
    _r_confetti,
    _r_laugh,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_scene() -> tuple[Setting, Spell, Treasure, MagicItem]:
    setting = Setting(place="the little kitchen", indoor=True, affords={"sparkle", "float", "clean"})
    spell = Spell(
        id="sparkle",
        verb="cast a sparkle spell",
        gerund="casting sparkle spells",
        glitch="made the spoon bounce instead of stay still",
        mess="sparkles",
        effect="bright and bouncy",
        tags={"magic", "sparkle", "farce"},
    )
    treasure = Treasure(
        label="birthday cake",
        phrase="a small birthday cake with blue frosting",
        type="cake",
        plural=False,
    )
    item = MagicItem(
        id="wand",
        label="a tiny wand",
        prep="tap the cake stand gently with the wand",
        fix="tap the spoon, then whisper a sorry spell",
        produces={"sparkles", "bounce"},
        requires={"magic"},
    )
    return setting, spell, treasure, item


def reasonableness_gate(spell: Spell, treasure: Treasure, item: MagicItem) -> None:
    if "magic" not in spell.tags:
        raise StoryError("This world needs a magic spell to create the farce.")
    if treasure.type != "cake":
        raise StoryError("This world is tuned for a cake that can survive a silly mishap.")
    if "sparkles" not in item.produces:
        raise StoryError("The magical tool must be able to produce harmless nonsense.")


def predict_mess(world: World, child: Entity, spell: Spell, treasure_id: str) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.memes["eager"] = child2.memes.get("eager", 0.0) + 1
    sim.silliness += 1
    treasure = sim.get(treasure_id)
    treasure.meters["mess"] = treasure.meters.get("mess", 0.0) + 1
    treasure.memes["confusion"] = treasure.memes.get("confusion", 0.0) + 1
    return {"touched": treasure.meters["mess"] >= THRESHOLD, "confusion": treasure.memes["confusion"]}


def tell(params: "StoryParams") -> World:
    setting, spell, treasure, item = build_scene()
    reasonableness_gate(spell, treasure, item)

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait, "hopeful"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    cake = world.add(Entity(
        id="Cake",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    wand = world.add(Entity(
        id=item.id,
        type="wand",
        label=item.label,
        owner=child.id,
        caretaker=parent.id,
        plural=item.plural,
    ))
    wand.worn_by = child.id

    # Act 1
    world.say(
        f"{child.id} was a little {params.trait} {params.gender} who loved magic."
    )
    world.say(
        f"{child.pronoun().capitalize()} had a birthday wish for {cake.phrase}, "
        f"and {child.pronoun('possessive')} {parent.label} had set it on the table."
    )
    world.say(
        f"{child.id} wanted to {spell.verb} so the candles would be easier to carry."
    )

    # Act 2
    world.para()
    pred = predict_mess(world, child, spell, cake.id)
    world.say(
        f"But when {child.id} waved {child.pronoun('possessive')} {wand.label}, "
        f"the spell {spell.glitch}."
    )
    child.memes["confusion"] = child.memes.get("confusion", 0.0) + 1
    child.memes["embarrassment"] = child.memes.get("embarrassment", 0.0) + 1
    cake.meters["mess"] = cake.meters.get("mess", 0.0) + 1
    cake.memes["confusion"] = cake.memes.get("confusion", 0.0) + 1
    world.silliness += 1
    propagate(world, narrate=True)
    world.say(
        f"The frosting went wobbly, the spoon gave a tiny hop, and the kitchen "
        f"looked suddenly like a joke."
    )
    world.say(
        f"{parent.pronoun().capitalize()} gasped, then saw that nobody was hurt."
    )

    # Act 3
    world.para()
    parent.memes["care"] = parent.memes.get("care", 0.0) + 1
    child.memes["shame"] = child.memes.get("shame", 0.0) + 0.5
    world.say(
        f"{parent.id} knelt beside {child.id} and said, "
        f"\"Let's fix it together.\""
    )
    world.say(
        f"They used a spoon to smooth the frosting, and {child.id} said sorry "
        f"without being pushed."
    )
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["love"] = child.memes.get("love", 0.0) + 1
    parent.memes["love"] = parent.memes.get("love", 0.0) + 1
    cake.meters["mess"] = 0.0
    cake.memes["confusion"] = 0.0
    world.say(
        f"At last the cake stood neat again, with one crooked candle and "
        f"all the laughter still warm in the room."
    )
    world.say(
        f"{child.id} carefully set down {child.pronoun('possessive')} {wand.label}, "
        f"and the family shared the cake together."
    )

    world.facts.update(
        child=child,
        parent=parent,
        cake=cake,
        wand=wand,
        spell=spell,
        setting=setting,
        predicted=pred,
        resolved=True,
    )
    return world


@dataclass
class StoryParams:
    place: str = "kitchen"
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the little kitchen", indoor=True, affords={"sparkle", "clean"}),
    "parlor": Setting(place="the sunny parlor", indoor=True, affords={"sparkle", "float"}),
    "workbench": Setting(place="the back workbench", indoor=True, affords={"sparkle", "clean", "float"}),
}

SPELLS = {
    "sparkle": Spell(
        id="sparkle",
        verb="cast a sparkle spell",
        gerund="casting sparkle spells",
        glitch="made the spoon bounce instead of stay still",
        mess="sparkles",
        effect="bright and bouncy",
        tags={"magic", "sparkle", "farce"},
    )
}

TRAITS = ["curious", "gentle", "cheerful", "shy", "brave", "playful"]
GIRL_NAMES = ["Mina", "Lina", "Tessa", "Ivy", "Nora", "Ruby", "Elsie", "Pippa"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Bram", "Eli", "Noah", "Finn", "Jasper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a heartwarming story about a child, a tiny magic mishap, and a kind repair.',
        f"Tell a funny but gentle story where {child.id} tries to use magic in {f['setting'].place} and then makes things right with family.",
        "Write a short story with farce, reconciliation, and a cozy ending around cake and laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cake = f["cake"]
    spell = f["spell"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do with magic?",
            answer=f"{child.id} wanted to {spell.verb} so the cake table would be easier and prettier to use.",
        ),
        QAItem(
            question=f"What went wrong when {child.id} used the wand?",
            answer=f"The spell {spell.glitch}, which made the scene silly instead of neat.",
        ),
        QAItem(
            question=f"How did {parent.label} help after the mistake?",
            answer=f"{parent.label} helped fix the cake with {child.id}, then said they could make it right together.",
        ),
        QAItem(
            question=f"What was special about the ending?",
            answer=f"The cake was neat again, and the family shared it with the laughter still warm in the room.",
        ),
    ]
    if f.get("predicted", {}).get("touched"):
        qa.append(
            QAItem(
                question=f"Why did {parent.label} worry before the spell?",
                answer=(
                    f"{parent.label} could see that if {child.id} used the magic, "
                    f"the cake would get messy, so the worry was about fixing the "
                    f"birthday cake afterward."
                ),
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is a special kind of make-believe power that can do surprising things.",
        ),
        QAItem(
            question="What is a farce?",
            answer="A farce is a very silly story where mix-ups and misunderstandings pile up in a funny way.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and make peace again.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  silliness={world.silliness}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the child uses magic, the spell makes a harmless mess,
% and the family can reconcile by fixing the object together.

valid_setting(S) :- setting(S).
valid_spell(P) :- spell(P), magic_spell(P).
valid_item(I) :- item(I), can_fix(I).

farce(SP, IT) :- valid_spell(SP), valid_item(IT), produces(SP, M), produces(IT, M).
needs_reconciliation(Child, Parent) :- farce(SP, IT), child(Child), parent(Parent).

happy_end(Child, Parent) :- needs_reconciliation(Child, Parent), reconcile(Child, Parent).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in SPELLS.items():
        lines.append(asp.fact("spell", pid))
        if "magic" in p.tags:
            lines.append(asp.fact("magic_spell", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    lines.append(asp.fact("item", "wand"))
    lines.append(asp.fact("can_fix", "wand"))
    lines.append(asp.fact("produces", "sparkle", "sparkles"))
    lines.append(asp.fact("produces", "wand", "sparkles"))
    lines.append(asp.fact("child", "mina"))
    lines.append(asp.fact("parent", "mother"))
    lines.append(asp.fact("reconcile", "mina", "mother"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    asp_ok = bool(asp.atoms(model, "happy_end"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming magical farce storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="kitchen", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="parlor", name="Theo", gender="boy", parent="father", trait="playful"),
    StoryParams(place="workbench", name="Ruby", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/2."))
        print("happy_end atoms:", asp.atoms(model, "happy_end"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
