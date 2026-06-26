#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/standard_froyo_strew_sound_effects_transformation_foreshadowing.py
===============================================================================================================================

A small whodunit-style story world about a standard froyo shop, a scattered
strew of toppings, and a gentle mystery with sound effects, foreshadowing,
and transformation.

The world is built from a short premise:
A careful child visits a froyo shop where the standard cup should stay neat.
Then something gets strewed across the counter, the clues pile up, and a small
detective story unfolds until the culprit is found.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script under storyworlds/worlds/
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- story-driven state with physical meters and emotional memes
- inline ASP_RULES twin and a Python reasonableness gate
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    area: str = ""
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
    place: str = "the froyo shop"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    sound: str
    foreshadow: str
    keyword: str = "froyo"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    area: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, area: str) -> bool:
        return any(item.area == area for item in self.worn_items(actor) if item.label and item.meters.get("protect", 0) >= THRESHOLD)

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shop": Setting(place="the froyo shop", indoor=True, affords={"mix", "strew"}),
    "counter": Setting(place="the froyo counter", indoor=True, affords={"mix", "strew"}),
}

ACTIONS = {
    "strew": Action(
        id="strew",
        verb="strew sprinkles on the froyo",
        gerund="strewed sprinkles across the counter",
        mess="strewn",
        soil="stuck all over the counter",
        zone={"counter", "floor"},
        sound="skrrt",
        foreshadow="A few stray sprinkles had already been left near the napkin box.",
        keyword="strew",
    ),
    "mix": Action(
        id="mix",
        verb="mix the froyo",
        gerund="mixing the froyo",
        mess="swirled",
        soil="swirled out of place",
        zone={"bowl", "counter"},
        sound="whirr",
        foreshadow="The spoon left a tiny spiral in the empty cup.",
        keyword="standard",
    ),
}

PRIZES = {
    "cup": Prize(label="cup", phrase="a standard froyo cup", type="cup", area="counter"),
    "cone": Prize(label="cone", phrase="a plain cone", type="cone", area="counter"),
}

GEAR = [
    Gear(
        id="napkin",
        label="a stack of napkins",
        covers={"counter"},
        guards={"strewn"},
        prep="move the napkins over the counter",
        tail="slid the napkins into place",
    ),
    Gear(
        id="tray",
        label="a clean tray",
        covers={"counter"},
        guards={"strewn", "swirled"},
        prep="put the froyo on a clean tray",
        tail="set the cup on the tray",
    ),
]

GIRL_NAMES = ["Mia", "Nora", "Lila", "Sophie", "Ava", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Eli", "Finn", "Theo"]
TRAITS = ["curious", "careful", "brave", "patient", "clever"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.area in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.mess in gear.guards and prize.area in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            action = ACTIONS[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(action, prize) and select_gear(action, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(action: Action, prize: Prize) -> str:
    return (
        f"(No story: {action.gerund} would not reasonably damage {prize.phrase}, "
        f"so there is no honest mystery to solve.)"
    )


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mess", 0) >= THRESHOLD:
            for item in world.entities.values():
                if item.caretaker == actor.id:
                    item.meters["dirty"] = item.meters.get("dirty", 0) + 1
                    produced.append("That would mean extra cleanup.")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": prize.meters.get("dirty", 0) >= THRESHOLD,
        "cleanup": sum(e.meters.get("dirty", 0) for e in sim.entities.values()),
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.meters["mess"] = actor.meters.get("mess", 0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0) + 1
    world.zone = set(action.zone)
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"With a {action.sound}, the froyo began to {action.gerund}.")


# ---------------------------------------------------------------------------
# Narrative functions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who liked things in a "
        f"standard order, especially {prize.phrase}."
    )
    world.say(
        f"{parent.label} kept the counter neat, and the froyo shop smelled sweet and cold."
    )


def setup_froyo(world: World, hero: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"One day, {hero.id} watched the froyo machine go {action.sound}, {action.foreshadow}"
    )
    world.say(
        f"{hero.id} wanted to {action.verb}, but {hero.pronoun('possessive')} {world.facts['parent'].label} said to wait."
    )


def trouble(world: World, hero: Entity, action: Action) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} tipped closer anyway. {action.sound.capitalize()}! "
        f"A tiny pile of sprinkles got strewed across the counter."
    )
    world.say(
        f"Then the whole place went quiet except for the refrigerator's hum."
    )


def investigate(world: World, hero: Entity, parent: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"{parent.label} narrowed {parent.pronoun('possessive')} eyes and said, "
        f'"Who moved the standard cup?"'
    )
    world.say(
        f"{hero.id} looked at the counter, then at the floor, and noticed the clue from before: "
        f"{action.foreshadow.lower()}"
    )


def reveal(world: World, hero: Entity, parent: Entity, prize: Entity, action: Action) -> Optional[Gear]:
    gear = select_gear(action, prize)
    if gear is None:
        return None
    helper = world.facts["helper"]
    gear_ent = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        area="counter",
        meters={"protect": 1.0},
    ))
    gear_ent.worn_by = hero.id
    world.say(
        f"At last, {helper.id} admitted it: {helper.pronoun().capitalize()} had tried to help and had "
        f"strewed the sprinkles by accident."
    )
    world.say(
        f"{parent.label} did not scold. Instead, {parent.pronoun('subject')} smiled and said, "
        f'"Let us fix it the standard way."'
    )
    world.say(
        f"They {gear.prep}, and the mess stopped spreading."
    )
    return gear


def resolve(world: World, hero: Entity, parent: Entity, prize: Entity, action: Action, gear: Gear) -> None:
    helper = world.facts["helper"]
    helper.memes["worry"] = 0
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} watched the froyo transform back into a neat swirl. "
        f"The counter looked tidy again, and the mystery was solved."
    )
    world.say(
        f"{helper.id} cleaned up with napkins, and the last little {action.sound} was only a memory."
    )
    world.say(
        f"In the end, the froyo was still standard, the toppings were back in place, and everyone could taste dessert again."
    )


# ---------------------------------------------------------------------------
# Complete tale construction
# ---------------------------------------------------------------------------
def tell(setting: Setting, action: Action, prize_cfg: Prize,
         hero_name: str = "Mia", hero_type: str = "girl",
         parent_type: str = "mother", helper_name: str = "Sam") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["standard", "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy", label=helper_name))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, area=prize_cfg.area, caretaker=parent.id))
    world.facts.update(hero=hero, parent=parent, helper=helper, prize=prize, action=action, setting=setting)

    introduce(world, hero, parent, prize)
    world.para()
    setup_froyo(world, hero, prize, action)
    trouble(world, hero, action)
    investigate(world, hero, parent, prize, action)
    world.para()
    gear = reveal(world, hero, parent, prize, action)
    if gear:
        resolve(world, hero, parent, prize, action, gear)
    world.facts["gear"] = gear
    world.facts["resolved"] = gear is not None
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit for a young child about a standard froyo cup, a scattered strew of sprinkles, and a small mystery at a shop counter.',
        f"Tell a gentle detective story where {f['hero'].id} notices a {f['action'].sound} sound, follows a foreshadowed clue, and learns who strewed the sprinkles.",
        f"Write a simple mystery story that includes the word \"{f['action'].keyword}\" and ends with the froyo being neat again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, helper, prize, action = f["hero"], f["parent"], f["helper"], f["prize"], f["action"]
    qa = [
        QAItem(
            question=f"What kind of froyo did {hero.id} care about in the story?",
            answer=f"{hero.id} cared about {prize.phrase}, because {hero.pronoun('possessive')} {parent.label if parent.label else 'parent'} wanted the counter to stay neat.",
        ),
        QAItem(
            question=f"What sound was heard when the trouble started?",
            answer=f"The story made the sound {action.sound}, which signaled that something had just been strewed across the counter.",
        ),
        QAItem(
            question=f"What clue was hinted at before the mystery was solved?",
            answer=f"The foreshadowing clue was that {action.foreshadow.lower()}",
        ),
    ]
    if f["resolved"]:
        qa.append(
            QAItem(
                question="Who turned out to be the one who caused the mess?",
                answer=f"It was {helper.id}; {helper.pronoun().capitalize()} had tried to help and accidentally strewed the sprinkles.",
            )
        )
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended with the froyo neat again, the counter cleaned up, and the little mystery solved kindly.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is froyo?",
            answer="Froyo is frozen yogurt, a cold dessert that is soft, sweet, and often topped with sprinkles or fruit.",
        ),
        QAItem(
            question="What does strew mean?",
            answer="To strew something means to scatter it around in a loose, messy way.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word or phrase that helps the reader hear what is happening, like skrrt or whirr.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint early in a story that helps the reader guess what may happen later.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes from one form or state into another, like a messy counter becoming neat again.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), area(P,R).
has_fix(A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), area(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, action.mess))
        for r in sorted(action.zone):
            lines.append(asp.fact("zone", aid, r))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("area", prid, prize.area))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
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
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: standard froyo, strew, sound effects, transformation, foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.action and args.prize:
        action = ACTIONS[args.action]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(action, prize) and select_gear(action, prize)):
            raise StoryError(explain_rejection(action, prize))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, action_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.area:
            bits.append(f"area={e.area}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
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
    StoryParams(place="shop", action="strew", prize="cup", name="Mia", gender="girl", parent="mother", trait="clever"),
    StoryParams(place="counter", action="mix", prize="cone", name="Leo", gender="boy", parent="father", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:\n")
        for item in vals:
            print("  ", item)
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
            header = f"### {p.name}: {p.action} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
