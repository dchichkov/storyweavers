#!/usr/bin/env python3
"""
A small comedy storyworld about a pit, a contingency plan, and a misunderstanding
that gets cleared up through dialogue.
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
# Core world model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Contingency:
    id: str
    label: str
    phrase: str
    action: str
    backup: str
    reason: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mood: str = "light"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "yard": Setting(place="the yard", affords={"dig", "talk"}),
    "garden": Setting(place="the garden", affords={"dig", "talk"}),
    "field": Setting(place="the field", affords={"dig", "talk"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"talk"}),
}

CONTINGENCIES = {
    "sandbags": Contingency(
        id="sandbags",
        label="sandbags",
        phrase="a stack of sandbags",
        action="line the pit with sandbags",
        backup="bring the sandbags over",
        reason="to keep the sides from slumping",
        helps="the pit stays neat and safe",
        tags={"pit", "backup"},
    ),
    "planks": Contingency(
        id="planks",
        label="planks",
        phrase="two sturdy planks",
        action="bridge the pit with planks",
        backup="fetch the planks",
        reason="to make a little bridge",
        helps="everyone can step across without wobbling",
        tags={"pit", "backup"},
    ),
    "broom": Contingency(
        id="broom",
        label="a broom",
        phrase="a broom with a blue handle",
        action="sweep the loose dirt away",
        backup="grab the broom",
        reason="to tidy the mess after digging",
        helps="the dirt doesn't end up in everyone's shoes",
        tags={"cleanup"},
    ),
    "sign": Contingency(
        id="sign",
        label="a sign",
        phrase="a bright sign that says 'Careful!'",
        action="set up a warning sign",
        backup="set out the sign",
        reason="to keep curious feet from the edge",
        helps="nobody stumbles into the pit",
        tags={"warning", "pit"},
    ),
}

HERO_NAMES = ["Mina", "Owen", "Tara", "Pip", "Jasper", "Nia", "Luca", "Mira"]
PARTNER_NAMES = ["Aunt Joy", "Uncle Ben", "Dad", "Mom", "Coach Kim", "Neighbor Jo"]
TRAITS = ["cheerful", "curious", "bouncy", "silly", "brave"]


@dataclass
class StoryParams:
    place: str
    contingency: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def pit_risk(setting: Setting, contingency: Contingency) -> bool:
    return "pit" in contingency.tags and "dig" in setting.affords


def select_contingency(contingency: Contingency) -> bool:
    return contingency.id in CONTINGENCIES


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for cid, cont in CONTINGENCIES.items():
            if pit_risk(setting, cont) and select_contingency(cont):
                out.append((place, cid))
    return out


def explain_rejection(setting: Setting, cont: Contingency) -> str:
    if "pit" not in cont.tags:
        return "(No story: that contingency does not relate to a pit, so the misunderstanding would be weak.)"
    if "dig" not in setting.affords:
        return f"(No story: {setting.place} does not support digging, so there is no pit to worry about.)"
    return "(No story: that combination does not make a clear, funny problem.)"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def _mutate_dig(world: World, hero: Entity, cont: Contingency, narrate: bool = True) -> None:
    hero.meters["busy"] = hero.meters.get("busy", 0) + 1
    hero.memes["excited"] = hero.memes.get("excited", 0) + 1
    if narrate:
        world.say(f"{hero.id} started digging a pit, humming like the job was a joke told by the dirt.")
    if cont.id == "sign":
        world.say("There was just one little problem: the sign was still leaning face-down in the grass.")


def _mutate_misunderstanding(world: World, hero: Entity, partner: Entity, cont: Contingency) -> None:
    sig = ("misunderstanding", hero.id, cont.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["confused"] = hero.memes.get("confused", 0) + 1
    partner.memes["confused"] = partner.memes.get("confused", 0) + 1
    world.say(
        f"{partner.id} squinted at the pit and said, "
        f'"You want me to {cont.action}?"'
    )
    world.say(
        f"{hero.id} blinked and laughed. "
        f'"No, no — I meant the contingency {cont.label}, not that I had changed my mind!"'
    )


def _mutate_dialogue(world: World, hero: Entity, partner: Entity, cont: Contingency) -> None:
    sig = ("dialogue", hero.id, cont.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    partner.memes["relief"] = partner.memes.get("relief", 0) + 1
    world.say(
        f'"Oh!" said {partner.id}. "You want the backup plan, not a dramatic hole surprise."'
    )
    world.say(
        f'"Exactly," said {hero.id}. "Let's {cont.backup} so {cont.helps}."'
    )
    world.say(
        f"So they got to work together, and the pit suddenly looked less like a problem and more like a punchline."
    )


def propagate(world: World, hero: Entity, partner: Entity, cont: Contingency) -> None:
    _mutate_misunderstanding(world, hero, partner, cont)
    _mutate_dialogue(world, hero, partner, cont)


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(setting: Setting, cont: Contingency, hero_name: str, partner_name: str, trait: str) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", meters={}, memes={}))
    partner = world.add(Entity(id=partner_name, kind="character", type="adult", meters={}, memes={}))
    hero.memes["joy"] = 1
    partner.memes["worry"] = 1

    world.say(f"{hero.id} was a {trait} kid who loved making a big plan look tiny.")
    world.say(f"One afternoon at {setting.place}, {hero.id} wanted to dig a pit and had a contingency: {cont.phrase}.")
    world.para()
    world.say(f"{partner.id} walked over and asked why {hero.id} kept pointing at the dirt with such serious eyebrows.")
    _mutate_dig(world, hero, cont)
    propagate(world, hero, partner, cont)
    world.para()
    world.say(
        f"In the end, {partner.id} helped with the backup, and the pit ended up neat, safe, and just silly enough to make everyone grin."
    )

    world.facts.update(hero=hero, partner=partner, contingency=cont, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, cont, setting = f["hero"], f["contingency"], f["setting"]
    return [
        f'Write a short comedic story about a child named {hero.id} who makes a contingency plan involving {cont.label}.',
        f'Tell a funny story set at {setting.place} where a pit causes a misunderstanding and then gets cleared up with dialogue.',
        f'Write a child-friendly comedy about "a pit" and "{cont.label}" where two characters talk it out.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, cont, setting = f["hero"], f["partner"], f["contingency"], f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to dig a pit and had a contingency plan ready in case the hole needed help.",
        ),
        QAItem(
            question=f"Why did {partner.id} misunderstand {hero.id}?",
            answer=f"{partner.id} thought {hero.id} meant the contingency itself as the main action, so the pit plan sounded mixed up for a moment.",
        ),
        QAItem(
            question=f"How did they fix the misunderstanding?",
            answer=f"They talked it through, and {hero.id} explained that {cont.phrase} was the backup plan, not the whole joke.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the pit was handled with the contingency plan, and the two of them were smiling instead of confused.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pit?",
            answer="A pit is a hole or hollow in the ground that can be dug for a project or a game.",
        ),
        QAItem(
            question="What is a contingency plan?",
            answer="A contingency plan is a backup plan you can use if the first idea needs help or does not work out.",
        ),
        QAItem(
            question="Why can a misunderstanding be funny in a story?",
            answer="A misunderstanding can be funny because characters say the wrong thing at first, then laugh when they finally explain what they meant.",
        ),
        QAItem(
            question="What does dialogue mean in a story?",
            answer="Dialogue means the characters are talking to each other in their own words.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
pit_risk(Place, C) :- affords(Place, dig), contingency(C), pit_related(C).
valid(Place, C) :- pit_risk(Place, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for cid, c in CONTINGENCIES.items():
        lines.append(asp.fact("contingency", cid))
        if "pit" in c.tags:
            lines.append(asp.fact("pit_related", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: pit, contingency, misunderstanding, dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--contingency", choices=CONTINGENCIES)
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=PARTNER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.contingency:
        setting = SETTINGS[args.place]
        cont = CONTINGENCIES[args.contingency]
        if not pit_risk(setting, cont):
            raise StoryError(explain_rejection(setting, cont))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.contingency is None or c[1] == args.contingency)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, cid = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    partner = args.partner or rng.choice(PARTNER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, contingency=cid, name=name, partner=partner, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CONTINGENCIES[params.contingency], params.name, params.partner, params.trait)
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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
    StoryParams(place="yard", contingency="sandbags", name="Mina", partner="Aunt Joy", trait="cheerful"),
    StoryParams(place="garden", contingency="planks", name="Owen", partner="Dad", trait="silly"),
    StoryParams(place="field", contingency="sign", name="Tara", partner="Neighbor Jo", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.contingency} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
