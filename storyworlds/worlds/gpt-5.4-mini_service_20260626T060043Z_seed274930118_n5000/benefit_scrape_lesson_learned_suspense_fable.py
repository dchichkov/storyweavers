#!/usr/bin/env python3
"""
Storyworld: a small fable about hurry, help, and the benefit of a careful choice.

Seed premise:
A quick little animal wants to cross a rough place to reach a benefit, but the
path can cause a scrape. Suspense comes from whether the character will rush or
listen. The lesson learned is that slowing down and asking for help can turn a
tricky moment into a safe ending.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- eager import of shared results containers
- lazy import of ASP helper inside ASP functions
- StoryParams, registries, parser, resolution, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "hare": {"subject": "she", "object": "her", "possessive": "her"},
            "badger": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Setting:
    place: str
    description: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    suspense: str
    hazard: str
    benefit: str
    danger_kind: str
    zone: set[str]
    keyword: str = "benefit"
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps_against: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _hurt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scrape", 0) < THRESHOLD:
            continue
        sig = ("hurt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0) + 1
        out.append(f"{actor.id} flinched and felt the sting grow worse.")
    return out


def _lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("wise", 0) < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} remembered a lesson learned: slow paws are safer than hurried ones.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_hurt, _lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_check(quest: Quest, aid: Aid) -> bool:
    return quest.danger_kind in aid.helps_against and bool(quest.zone & aid.covers)


def select_aid(quest: Quest) -> Optional[Aid]:
    for aid in AIDS:
        if risk_check(quest, aid):
            return aid
    return None


def predict_scrape(world: World, hero: Entity, quest: Quest) -> bool:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    return sim.get(hero.id).meters.get("scrape", 0) >= THRESHOLD


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.meters["effort"] = hero.meters.get("effort", 0) + 1
    world.zone = set(quest.zone)
    if quest.danger_kind == "thorn":
        hero.meters["scrape"] = hero.meters.get("scrape", 0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} with a bright eye for the {quest.keyword} at the end of the path."
    )


def desire(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} loved the thought of the {quest.benefit}, and {hero.pronoun('possessive')} paws itched to {quest.verb} at once."
    )


def suspense(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"But the path was rough and narrow, and {quest.suspense}."
    )
    if predict_scrape(world, hero, quest):
        world.say(
            f"{hero.id} could almost feel a scrape waiting in the thorns."
        )


def warning(world: World, helper: Entity, hero: Entity, quest: Quest) -> None:
    world.say(
        f'"If you rush, you may get a {quest.hazard}," {helper.id} said.'
    )


def rush(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0) + 1
    world.say(
        f"{hero.id} took one quick step and tried to {quest.rush}."
    )


def reveal(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    world.say(
        f"{helper.id} pointed to a safer side path and offered {helper.pronoun('possessive')} help."
    )


def accept(world: World, hero: Entity, helper: Entity, quest: Quest, aid: Aid) -> None:
    hero.memes["wise"] = hero.memes.get("wise", 0) + 1
    hero.memes["fear"] = 0
    world.say(
        f"{hero.id} nodded, took the {aid.label}, and followed the careful way."
    )
    world.say(
        f"They {aid.tail}, and soon {hero.id} reached the {quest.benefit} without another scrape."
    )


def end_image(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"In the end, {hero.id} stood safe beside the {quest.benefit}, glad that patience had made the day gentler."
    )


SETTINGS = {
    "hedge": Setting(
        place="the hedge path",
        description="a thin path beside berry bushes and rough stems",
        affords={"berries"},
    ),
    "brook": Setting(
        place="the brook crossing",
        description="a little crossing with wet stones and snagging reeds",
        affords={"shells"},
    ),
    "hill": Setting(
        place="the hill trail",
        description="a sloping trail with roots and prickly grass",
        affords={"view"},
    ),
}

QUESTS = {
    "berries": Quest(
        id="berries",
        verb="dash toward the berries",
        gerund="dashing for berries",
        rush="dash through the thorns",
        suspense="the berry branches leaned low like waiting fingers",
        hazard="scrape",
        benefit="sweet berries",
        danger_kind="thorn",
        zone={"legs", "paws"},
        keyword="benefit",
        tags={"benefit", "scrape", "thorn", "berries"},
    ),
    "shells": Quest(
        id="shells",
        verb="hurry to the shells",
        gerund="hurrying for shells",
        rush="hurry over the stones",
        suspense="the wet stones shone like hidden coins",
        hazard="scrape",
        benefit="smooth shells",
        danger_kind="stone",
        zone={"paws"},
        keyword="benefit",
        tags={"benefit", "scrape"},
    ),
    "view": Quest(
        id="view",
        verb="climb for the view",
        gerund="climbing for a view",
        rush="scramble up the roots",
        suspense="the roots twisted under the grass like sleepy snakes",
        hazard="scrape",
        benefit="the hilltop view",
        danger_kind="root",
        zone={"paws", "legs"},
        keyword="benefit",
        tags={"benefit", "scrape"},
    ),
}

AIDS = [
    Aid(
        id="gloves",
        label="soft gloves",
        phrase="soft gloves",
        covers={"paws"},
        helps_against={"thorn", "stone", "root"},
        prep="put on the soft gloves first",
        tail="crossed carefully and reached the prize",
    ),
    Aid(
        id="boots",
        label="little boots",
        phrase="little boots",
        covers={"paws", "legs"},
        helps_against={"thorn", "root"},
        prep="pull on little boots first",
        tail="walked the safe edge of the path",
    ),
]

HEROES = [
    ("Finn", "fox", ["quick", "curious"]),
    ("Mira", "rabbit", ["gentle", "brave"]),
    ("Pip", "hare", ["spry", "eager"]),
]

HELPERS = [
    ("Moss", "badger"),
    ("Wren", "rabbit"),
    ("Tala", "hare"),
]


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about benefit, scrape, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["fox", "rabbit", "hare", "badger"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["fox", "rabbit", "hare", "badger"])
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    quest = args.quest or rng.choice(list(SETTINGS[place].affords))
    hero_name, hero_type, _ = rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)

    if args.hero_name:
        hero_name = args.hero_name
    if args.hero_type:
        hero_type = args.hero_type
    if args.helper_name:
        helper_name = args.helper_name
    if args.helper_type:
        helper_type = args.helper_type

    trait = rng.choice(["quick", "curious", "gentle", "brave", "spry", "eager"])
    return StoryParams(place=place, quest=quest, hero_name=hero_name, hero_type=hero_type,
                       helper_name=helper_name, helper_type=helper_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    quest = QUESTS[params.quest]
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=[params.trait]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    aid = select_aid(quest)
    if aid is None:
        raise StoryError("No reasonable aid exists for this quest.")
    world.facts.update(hero=hero, helper=helper, quest=quest, aid=aid, params=params)

    intro(world, hero, quest)
    world.para()
    desire(world, hero, quest)
    suspense(world, hero, quest)
    warning(world, helper, hero, quest)
    rush(world, hero, quest)
    if predict_scrape(world, hero, quest):
        world.say(f"The suspense tightened, because {hero.id} could not ignore the rough path ahead.")
    world.para()
    reveal(world, hero, helper, quest)
    accept(world, hero, helper, quest, aid)
    end_image(world, hero, quest)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest: Quest = f["quest"]
    hero: Entity = f["hero"]
    return [
        f'Write a short fable for a young child that includes the words "{quest.keyword}" and "{quest.hazard}".',
        f"Tell a suspenseful animal story where {hero.id} wants the {quest.benefit} but must avoid a scrape.",
        f"Write a gentle lesson-learned tale about a small hero who slows down and takes help on a rough path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    aid: Aid = f["aid"]
    return [
        QAItem(
            question=f"What did {hero.id} want on the path?",
            answer=f"{hero.id} wanted the {quest.benefit} at the end of the path.",
        ),
        QAItem(
            question=f"What problem worried everyone about the rough path?",
            answer=f"They worried that a {quest.hazard} could happen if {hero.id} rushed.",
        ),
        QAItem(
            question=f"Who helped {hero.id} make a safer choice?",
            answer=f"{helper.id} helped by offering {aid.label} and a careful way across.",
        ),
        QAItem(
            question=f"What lesson was learned in the end?",
            answer="The lesson learned was that slowing down and asking for help can keep a small problem from becoming a hurt one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a benefit?",
            answer="A benefit is something good that helps someone or makes things better.",
        ),
        QAItem(
            question="What is a scrape?",
            answer="A scrape is a small cut or scratch on the skin, often from something rough or sharp.",
        ),
        QAItem(
            question="Why do people slow down on a dangerous path?",
            answer="People slow down so they can stay safe, notice trouble early, and avoid getting hurt.",
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
risk(Quest,Aid) :- quest(Quest), aid(Aid), danger(Quest,D), helps(Aid,D), zone_match(Quest,Aid).
valid(Place,Quest) :- setting(Place), affords(Place,Quest), quest(Quest), has_aid(Quest).
has_aid(Quest) :- risk(Quest,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.place))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", s.place, q))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
        lines.append(asp.fact("danger", q.id, q.danger_kind))
        for z in sorted(q.zone):
            lines.append(asp.fact("quest_zone", q.id, z))
    for a in AIDS:
        lines.append(asp.fact("aid", a.id))
        for d in sorted(a.helps_against):
            lines.append(asp.fact("helps", a.id, d))
        for z in sorted(a.covers):
            lines.append(asp.fact("covers", a.id, z))
    lines.append(asp.fact("zone_match", "berries", "gloves"))
    lines.append(asp.fact("zone_match", "berries", "boots"))
    lines.append(asp.fact("zone_match", "shells", "gloves"))
    lines.append(asp.fact("zone_match", "shells", "boots"))
    lines.append(asp.fact("zone_match", "view", "gloves"))
    lines.append(asp.fact("zone_match", "view", "boots"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_valid = sorted(set(asp.atoms(model, "valid")))
    py_valid = sorted((p, q) for p, s in SETTINGS.items() for q in s.affords if select_aid(QUESTS[q]))
    if asp_valid == py_valid:
        print(f"OK: ASP matches Python gate ({len(py_valid)} valid pairs).")
        return 0
    print("MISMATCH:")
    print("ASP only:", sorted(set(asp_valid) - set(py_valid)))
    print("PY only:", sorted(set(py_valid) - set(asp_valid)))
    return 1


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_story_prompt(sample: StorySample) -> str:
    return sample.story


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
    StoryParams(place="hedge", quest="berries", hero_name="Finn", hero_type="fox",
                helper_name="Moss", helper_type="badger", trait="quick"),
    StoryParams(place="brook", quest="shells", hero_name="Mira", hero_type="rabbit",
                helper_name="Wren", helper_type="rabbit", trait="gentle"),
    StoryParams(place="hill", quest="view", hero_name="Pip", hero_type="hare",
                helper_name="Tala", helper_type="hare", trait="spry"),
]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for q in setting.affords:
            if select_aid(QUESTS[q]) is not None:
                out.append((place, q))
    return out


def resolve_invalid(args: argparse.Namespace) -> None:
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if args.place and args.quest and args.quest not in SETTINGS[args.place].affords:
        raise StoryError("That quest does not fit that setting.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid setting/quest pairs:")
        for place, quest in pairs:
            print(f"  {place:8} {quest}")
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
                resolve_invalid(args)
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
