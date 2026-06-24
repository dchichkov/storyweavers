#!/usr/bin/env python3
"""
A small folk-tale story world about shiny foil, sticky goop, a comic mistake,
and a happy ending.

Seed idea:
- A child or small folk-tale hero finds a messy goop situation.
- A foil object is the reasonable helper/fix.
- Conflict comes from the goop causing trouble and a foiled plan.
- Humor comes from the awkward, sticky, shiny mishap.
- The ending should feel warm, tidy, and complete.

This file is standalone and uses only the stdlib plus the shared Storyweavers
results/asp helpers.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"goop": 0.0, "shine": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "conflict": 0.0, "amusement": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class FoilItem:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fix_for: set[str]
    plural: bool = False
    humorous: str = ""


@dataclass
class GoopSource:
    id: str
    label: str
    verb: str
    mess: str
    zone: set[str]
    joke: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character" or actor.meters["goop"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            if item.protective:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got sticky and dirty.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.memes["worry"] < THRESHOLD or actor.memes["amusement"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_mess, _r_conflict):
            res = fn(world)
            if res:
                changed = True
                produced.extend(x for x in res if x != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(goop: GoopSource, prize: Entity) -> bool:
    return prize.label in {"apron", "cloak", "shirt", "cap", "boots"} or True if prize else False


def select_foil(goop: GoopSource, prize: Entity) -> Optional[FoilItem]:
    for foil in FOIL_ITEMS:
        if goop.id in foil.fix_for and prize.label in foil.covers or prize.id in foil.covers:
            return foil
    return None


def tell(setting: Setting, goop: GoopSource, foil_prize: str, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    prize_cfg = PRIZES[foil_prize]
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg["type"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        plural=prize_cfg.get("plural", False),
    ))
    hero.memes["joy"] += 1
    world.say(f"Long ago, in {setting.place}, there lived a {hero_type} named {hero_name}.")
    world.say(f"{hero_name} loved {goop.joke} and thought shiny things were grand.")
    world.say(f"{parent.pronoun('possessive').capitalize()} {parent.label if parent.label else 'parent'} had given {hero_name} {prize.phrase}.")
    world.para()
    world.say(f"One day at {setting.place}, {hero_name} tried to {goop.verb}.")
    hero.meters["goop"] += 1
    hero.memes["amusement"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=True)
    world.say(f"That made the day funny in a sad sort of way, for {hero_name} looked like a pie that had learned to sneeze.")
    world.para()
    foil_def = select_foil(goop, prize)
    if foil_def is None:
        raise StoryError("No reasonable foil fix exists for this story.")
    foil = world.add(Entity(id=foil_def.id, type="foil", label=foil_def.label, phrase=foil_def.phrase, protective=True, covers=set(foil_def.covers)))
    foil.worn_by = hero.id
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    world.say(f"Then {parent.label if parent.label else 'the parent'} laughed and said, 'Quick now, let's use {foil.label}!'")
    world.say(f"They fitted {foil.label} over the messy part, and at once the sticky trouble was caught before it could spread.")
    world.say(f"{hero_name} went back to {goop.verb}, and this time the goop slipped off the shiny cover like a raindrop on a silver leaf.")
    world.say(f"In the end, {hero_name} was clean enough for supper, {parent.label if parent.label else 'the parent'} was smiling, and even the foil seemed pleased with itself.")
    world.facts.update(hero=hero, parent=parent, prize=prize, foil=foil, goop=goop, setting=setting)
    return world


SETTINGS = {
    "village": Setting(place="the village green"),
    "kitchen": Setting(place="the old kitchen", indoors=True),
    "market": Setting(place="the market square"),
    "barn": Setting(place="the barn"),
}

GOOPS = {
    "jam": GoopSource(
        id="jam",
        label="jam",
        verb="stir the berry jam",
        mess="sticky",
        zone={"hands", "torso"},
        joke="licking the spoon twice and then pretending nothing happened",
        tags={"sweet", "sticky"},
    ),
    "porridge": GoopSource(
        id="porridge",
        label="porridge",
        verb="carry the porridge pot",
        mess="sloppy",
        zone={"hands", "torso"},
        joke="splashing one spoonful onto the nose of another spoonful",
        tags={"soft", "messy"},
    ),
    "goop": GoopSource(
        id="goop",
        label="goop",
        verb="poke the moon-goop",
        mess="gooey",
        zone={"hands", "torso"},
        joke="touching the blobby moon-goop with a stick and then laughing at the stick",
        tags={"gooey", "glowy"},
    ),
}

FOIL_ITEMS = [
    FoilItem(
        id="foil_cap",
        label="a shiny foil cap",
        phrase="a shiny foil cap",
        covers={"head"},
        fix_for={"goop", "jam"},
        humorous="It looked like a fish wearing a moonbeam.",
    ),
    FoilItem(
        id="foil_wrap",
        label="a sheet of foil",
        phrase="a sheet of foil",
        covers={"hands", "torso"},
        fix_for={"goop", "jam", "porridge"},
        humorous="It crinkled like a tiny thundercloud made of silver.",
    ),
    FoilItem(
        id="foil_apron",
        label="a foil apron",
        phrase="a foil apron",
        covers={"torso"},
        fix_for={"jam", "porridge", "goop"},
        humorous="It shone so much the hens squinted at it.",
    ),
]

PRIZES = {
    "apron": {"label": "apron", "phrase": "a clean apron with little flowers", "type": "thing"},
    "shirt": {"label": "shirt", "phrase": "a neat shirt with blue buttons", "type": "thing"},
    "cap": {"label": "cap", "phrase": "a wool cap with a red feather", "type": "thing"},
}

GIRL_NAMES = ["Mara", "Elin", "Nina", "Tilda", "Poppy"]
BOY_NAMES = ["Bram", "Owen", "Hugo", "Milo", "Rafe"]
TRAITS = ["cheerful", "curious", "merry", "sly", "pluckish"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for goop in GOOPS:
            for prize in PRIZES:
                combos.append((place, goop, prize))
    return combos


@dataclass
class StoryParams:
    place: str
    goop: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child about {f["hero"].id}, {f["goop"].label}, and shiny {f["foil"].label}.',
        f"Tell a humorous story where {f['hero'].id} makes a messy mistake with {f['goop'].label} but ends with a happy fix.",
        f'Write a gentle tale set at {f["setting"].place} that includes foil, goop, and a kind helper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, goop, foil = f["hero"], f["parent"], f["prize"], f["goop"], f["foil"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, who lives a small folk-tale day full of {goop.label} and shiny foil.",
        ),
        QAItem(
            question=f"What made the trouble in the story?",
            answer=f"The trouble came when {hero.id} tried to {goop.verb}, and the {goop.mess} goop got on {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What helped fix the mess?",
            answer=f"{foil.label} helped by covering the messy part so the goop would not spread any farther.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} clean enough for supper and everyone smiling at the clever shiny fix.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foil?",
            answer="Foil is a thin, shiny metal sheet that crinkles easily and can cover or wrap things.",
        ),
        QAItem(
            question="What is goop?",
            answer="Goop is a sticky, messy substance that can cling to hands, clothes, and tools.",
        ),
        QAItem(
            question="Why do people laugh in a humorous story?",
            answer="People laugh when something is silly, surprising, or awkward in a safe and friendly way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} worn_by={e.worn_by}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_goop(G) :- goop(G).
valid_prize(R) :- prize(R).
valid_story(P,G,R) :- valid_place(P), valid_goop(G), valid_prize(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GOOPS:
        lines.append(asp.fact("goop", g))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world of foil, goop, humor, conflict, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goop", choices=GOOPS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.goop is None or c[1] == args.goop)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, goop, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, goop=goop, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], GOOPS[params.goop], params.prize, params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (place, goop, prize) combos:\n")
        for c in combos:
            print("  ", c)
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="village", goop="jam", prize="apron", name="Mara", gender="girl", parent="mother", trait="cheerful"),
            StoryParams(place="kitchen", goop="porridge", prize="shirt", name="Bram", gender="boy", parent="father", trait="curious"),
            StoryParams(place="market", goop="goop", prize="cap", name="Tilda", gender="girl", parent="mother", trait="merry"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.goop} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
