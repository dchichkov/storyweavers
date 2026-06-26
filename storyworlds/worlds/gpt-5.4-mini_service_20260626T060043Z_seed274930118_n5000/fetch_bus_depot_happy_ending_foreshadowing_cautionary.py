#!/usr/bin/env python3
"""
storyworlds/worlds/fetch_bus_depot_happy_ending_foreshadowing_cautionary.py
============================================================================

A standalone story world for a small Adventure tale set at a bus depot.

Premise:
- A child must fetch a lost delivery tag / parcel from a busy bus depot.
- The depot has caution signs and foreshadowing details that matter later.
- A helper, a map, and a bus schedule create a safe, happy ending.

The world is intentionally small and constraint-checked:
- typed entities have physical meters and emotional memes
- the simulated state drives the prose
- invalid combinations raise StoryError
- inline ASP rules mirror the Python reasonableness gate
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
    wearable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bus depot"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str


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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_scared(world: World) -> list[str]:
    out = []
    kid = world.get("hero")
    if kid.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("scared",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["caution"] = kid.memes.get("caution", 0) + 1
    out.append("The caution signs made the child slow down and look twice.")
    return out


def _r_recover(world: World) -> list[str]:
    out = []
    kid = world.get("hero")
    prize = world.get("prize")
    if prize.meters.get("lost", 0) < THRESHOLD:
        return out
    sig = ("recover",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["found"] = 1
    out.append("A careful look through the depot found the lost prize at last.")
    return out


CAUSAL_RULES = [
    _r_scared,
    _r_recover,
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


def predict_loss(world: World, quest: Quest) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    if quest.id == "parcel":
        sim.get("prize").meters["lost"] = 1
    return sim.get("prize").meters.get("found", 0) < THRESHOLD and sim.get("prize").meters.get("lost", 0) >= THRESHOLD


def introduce(world: World, hero: Entity, helper: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a brave young traveler who had to fetch a missing {prize.label} "
        f"from {world.setting.place}."
    )
    world.say(
        f"{hero.id} loved adventure, and {quest.clue} hinted that this errand would not be simple."
    )
    helper.memes["calm"] = helper.memes.get("calm", 0) + 1
    world.say(
        f"At the depot, {helper.label} watched the lanes and said they could help if {hero.id} stayed alert."
    )


def set_out(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"One busy morning, {hero.id} hurried into {world.setting.place}, ready to {quest.verb}."
    )
    world.say(
        f"Nearby, a torn timetable fluttered in the draft, and that was the first foreshadowing sign."
    )


def caution(world: World, hero: Entity, prize: Entity, quest: Quest) -> None:
    if predict_loss(world, quest):
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(
            f'"If you rush, you might lose the {prize.label}," a sign seemed to warn, '
            f"and {hero.id} slowed down."
        )


def search(world: World, hero: Entity, helper: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} followed the map between the benches and the ticket window, while {helper.label} pointed to the platforms."
    )
    world.say(
        f"Together they looked under a bench, beside a crate, and near the luggage shelf."
    )
    if quest.id == "parcel":
        prize.meters["lost"] = 1
        propagate(world, narrate=False)


def happy_turn(world: World, hero: Entity, helper: Entity, prize: Entity, gear: Gear) -> None:
    world.say(
        f"Then {helper.label} remembered {gear.label} and used it to check the clue one more time."
    )
    world.say(
        f'They {gear.tail}, and at the end of the lane {hero.id} found the {prize.label} safely waiting.'
    )


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    prize.meters["found"] = 1
    world.say(
        f"{hero.id} grinned, tucked the {prize.label} in {hero.pronoun('possessive')} pocket, and thanked {helper.label}."
    )
    world.say(
        f"The depot lights glowed warm as the bus doors sighed shut, and the day ended safely after the daring fetch."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=helper_name))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))
    introduce(world, hero, helper, prize, quest)
    world.para()
    set_out(world, hero, quest, prize)
    caution(world, hero, prize, quest)
    search(world, hero, helper, prize, quest)
    world.para()
    gear = Gear(
        id="labeled_ticket",
        label="the bright depot ticket",
        helps={"find"},
        prep="checked the bright depot ticket",
        tail="checked the bright depot ticket and traced the right platform"
    )
    happy_turn(world, hero, helper, prize, gear)
    resolve(world, hero, helper, prize)
    world.facts.update(hero=hero, helper=helper, prize=prize, quest=quest, gear=gear)
    return world


SETTINGS = {
    "depot": Setting(place="the bus depot", affords={"fetch"}),
}

QUESTS = {
    "fetch": Quest(
        id="fetch",
        verb="fetch the missing parcel",
        gerund="fetching the missing parcel",
        rush="dash through the depot",
        risk="lose the parcel in the crowd",
        clue="the timetable had a circle around platform three",
        tags={"fetch", "adventure", "cautionary", "foreshadowing"},
    ),
}

PRIZES = {
    "parcel": Prize(
        id="parcel",
        label="parcel",
        phrase="a small paper-wrapped parcel",
        region="hands",
    ),
}

HERO_NAMES = ["Niko", "Ari", "Milo", "Tessa", "Rin", "Pia"]
HELPER_NAMES = ["Ms. Jun", "Aunt Vale", "Mrs. Tavi", "Coach Fern"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for q in setting.affords:
            for p in PRIZES:
                out.append((place, q, p))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    quest = f["quest"].verb
    prize = f["prize"].label
    return [
        f"Write a short adventure story about {hero} who must {quest} at a bus depot.",
        f"Tell a cautious but happy story where {helper} helps {hero} find a lost {prize}.",
        f"Create a child-friendly adventure with foreshadowing at the bus depot and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    prize = f["prize"].label
    return [
        QAItem(
            question=f"What did {hero} have to do at the bus depot?",
            answer=f"{hero} had to fetch the missing {prize} from the bus depot."
        ),
        QAItem(
            question=f"Who helped {hero} at the depot?",
            answer=f"{helper} helped {hero} look carefully and stay safe."
        ),
        QAItem(
            question="What was the cautionary warning in the story?",
            answer="The story warned that rushing through the depot could make the parcel get lost in the crowd."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses stop, park, and get ready for trips."
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small clue early on that helps the reader guess what may matter later."
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story warns about a danger or mistake so someone can choose a safer path."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A quest is valid if the setting affords it.
valid_story(Place, Quest, Prize) :- affords(Place, Quest), prize(Prize).

% This world always has a safe helping path for the fetch quest.
has_safe_help(Quest) :- valid_story(_, Quest, _), quest(Quest).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
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
    ap = argparse.ArgumentParser(description="Adventure story world: fetch at the bus depot.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(combos)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, quest=quest, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize], params.hero, params.helper)
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
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = [StoryParams(place="depot", quest="fetch", prize="parcel", hero=h, helper=k) for h, k in zip(HERO_NAMES[:1], HELPER_NAMES[:1])]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
