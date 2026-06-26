#!/usr/bin/env python3
"""
storyworlds/worlds/leotard_additive_shield_sound_effects_bad_ending.py
=====================================================================

A small space-adventure storyworld about a child performer on a rocket ship,
a sparkly leotard, a tricky fuel additive, and a shield that cannot save the day.

The premise is intentionally narrow:
- a little space kid loves a glittery leotard and a noisy rocket ride
- the ship needs a fuel additive to make the engine hum safely
- the additive is spilled, the shield is damaged, and the ending goes badly

This world includes:
- typed entities with meters and memes
- state-driven prose
- a reasonableness gate
- an inline ASP twin
- sound-effect narration
- a bad ending
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
    broken: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    sound: str
    mess: str
    damage: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Shield:
    id: str
    label: str
    prep: str
    tail: str
    blocks: set[str]


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


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


SETTINGS = {
    "orbit_lab": Setting(place="the orbit lab", affords={"stabilize"}),
    "launch_deck": Setting(place="the launch deck", affords={"stabilize"}),
}

ACTIONS = {
    "stabilize": Action(
        id="stabilize",
        verb="help the engine stay calm",
        sound="whirr-whirr",
        mess="sparks",
        damage="overheated",
        zone="engine",
        keyword="shield",
        tags={"shield", "space"},
    ),
    "test_run": Action(
        id="test_run",
        verb="test the thrusters",
        sound="brrrmmm",
        mess="shakes",
        damage="misfired",
        zone="ship",
        keyword="additive",
        tags={"additive", "space"},
    ),
}

PRIZES = {
    "leotard": Prize(
        label="leotard",
        phrase="a silver leotard with bright stripes",
        type="leotard",
        region="torso",
        genders={"girl"},
    ),
    "jumpsuit": Prize(
        label="jumpsuit",
        phrase="a shiny jumpsuit",
        type="jumpsuit",
        region="torso",
    ),
}

SHIELDS = [
    Shield(
        id="shield",
        label="a shield panel",
        prep="lock the shield panel over the engine",
        tail="locked the shield panel into place",
        blocks={"sparks", "shakes"},
    )
]

GIRL_NAMES = ["Nova", "Mila", "Zuri", "Pip", "Luna"]
BOY_NAMES = ["Finn", "Ollie", "Timo", "Max", "Jett"]
TRAITS = ["brave", "bouncy", "curious", "daring"]


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region == "torso"


def select_shield(action: Action, prize: Prize) -> Optional[Shield]:
    for shield in SHIELDS:
        if action.mess in shield.blocks and prize.region == "torso":
            return shield
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            action = ACTIONS[action_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(action, prize) and select_shield(action, prize):
                    out.append((place, action_id, prize_id))
    return out


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("sound_of", aid, a.sound))
        for r in [a.zone]:
            lines.append(asp.fact("reaches", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for sh in SHIELDS:
        lines.append(asp.fact("shield", sh.id))
        for b in sorted(sh.blocks):
            lines.append(asp.fact("blocks", sh.id, b))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- reaches(A,R), worn_on(P,R).
protects(S,A,P) :- shield(S), prize_at_risk(A,P), mess_of(A,M), blocks(S,M).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
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
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a leotard, additive, and shield.")
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


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return "(No story: that prize would not be threatened by this space test.)"
    return "(No story: there is no shield in this world that can honestly protect that prize from this action.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.prize:
        if not (prize_at_risk(ACTIONS[args.action], PRIZES[args.prize]) and select_shield(ACTIONS[args.action], PRIZES[args.prize])):
            raise StoryError(explain_rejection(ACTIONS[args.action], PRIZES[args.prize]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def predict_bad(world: World, actor: Entity, action: Action, prize_id: str) -> bool:
    sim = world.copy()
    hero = sim.get(actor.id)
    hero.meters[action.mess] = 1.0
    prize = sim.get(prize_id)
    prize.broken = True
    return True


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", meters={}, memes={}))
    prize = world.add(Entity(id="Prize", type=params.prize, label=params.prize, phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=parent.id, worn_by=hero.id, meters={}, memes={}))
    action = ACTIONS[params.action]
    shield_def = select_shield(action, PRIZES[params.prize])

    world.say(f"{hero.id} was a {params.trait} little astronaut who loved {prize.phrase}.")
    world.say(f"The ship went {action.sound}! {hero.pronoun().capitalize()} liked the noisy hum of the orbit lab.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {params.parent} checked the control panel and said the engine needed an additive before launch.")
    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {params.parent} went to {world.setting.place}.")
    world.say(f"{hero.id} wanted to {action.verb}, but the fuel additive splashed near the engine.")
    world.say(f"Skrrt! The shield panel buzzed, but it was too late.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {prize.label} got {action.mess}, and the ship smelled {action.damage}.")
    world.para()
    world.say(f"{params.parent.capitalize()} tried to {shield_def.prep if shield_def else 'cover the engine'}, but the damage kept spreading.")
    world.say(f"Wham! The shield failed, the console blinked red, and the rocket drifted off course.")
    world.say(f"In the end, {hero.id} stared at the dark window while the leotard was ruined and the mission had to stop.")

    hero.memes["worry"] = 1.0
    prize.broken = True
    world.facts.update(hero=hero, parent=parent, prize=prize, action=action, shield=shield_def, bad_end=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a small child that includes "{f["prize"].label}", "{f["action"].keyword}", and a shield.',
        f"Tell a gentle rocket-ship story where {f['hero'].id} loves a {f['prize'].label} but a fuel additive causes trouble.",
        f"Write a child-facing story with sound effects like boom and whirr, ending in a bad outcome for the ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, action = f["hero"], f["parent"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"What did {hero.id} love at the start of the story?",
            answer=f"{hero.id} loved the {prize.label} and wanted to wear it during the space adventure.",
        ),
        QAItem(
            question=f"What caused trouble for {hero.id} and {parent.label}?",
            answer=f"The fuel additive caused trouble when it splashed near the engine during the test run.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly: the shield failed, the ship drifted off course, and the mission had to stop.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shield in a space story?",
            answer="A shield is a protective barrier that helps block danger, heat, or sparks around a ship or engine.",
        ),
        QAItem(
            question="What does an additive do?",
            answer="An additive is something you add to another material to change how it works, like helping fuel run better.",
        ),
        QAItem(
            question="What is a leotard?",
            answer="A leotard is a snug one-piece outfit often worn for dance or gymnastics.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.broken:
            bits.append("broken=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="orbit_lab", action="stabilize", prize="leotard", name="Nova", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="launch_deck", action="test_run", prize="leotard", name="Luna", gender="girl", parent="father", trait="curious"),
]


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


def asp_valid_stories_list() -> list[tuple]:
    return asp_valid_stories()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories_list()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, action, prize in triples:
            genders = sorted(g for (pl, ac, pr, g) in stories if (pl, ac, pr) == (place, action, prize))
            print(f"  {place:12} {action:10} {prize:10}  [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
