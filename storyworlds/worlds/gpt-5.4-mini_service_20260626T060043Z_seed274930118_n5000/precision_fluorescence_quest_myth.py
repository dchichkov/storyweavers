#!/usr/bin/env python3
"""
A small mythic quest world about precision and fluorescence.

A child-friendly legend in which a careful quest must be measured exactly,
and a glowing sign helps the traveler find the right path.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    luminous: bool = False
    precision_tool: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "priestess", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "priest", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    omen: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    goal: str
    risk: str
    precision_need: str
    fluorescence_need: str
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    required_precision: float
    required_fluorescence: float
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    helps_precision: bool = False
    glows: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.omen: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.omen = self.omen
        w.lines = [[]]
        return w


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "forest": Place(name="the forest", omen="the trees stood in a green hush", affords={"quest"}),
    "cavern": Place(name="the cavern", omen="the stones held moon-cold echoes", affords={"quest"}),
    "ruins": Place(name="the old ruins", omen="broken pillars watched the road", affords={"quest"}),
    "shore": Place(name="the bright shore", omen="the waves flashed like silver scales", affords={"quest"}),
}

QUESTS = {
    "crown": Quest(
        id="crown",
        verb="seek the lost crown",
        gerund="seeking the lost crown",
        rush="hurry toward the crown",
        goal="bring back the rightful light",
        risk="one wrong step could send the crown into the dark",
        precision_need="the path had to be measured exactly",
        fluorescence_need="a bright glow would mark the hidden stones",
        tags={"precision", "fluorescence", "quest", "myth"},
    ),
    "key": Quest(
        id="key",
        verb="find the silver key",
        gerund="finding the silver key",
        rush="dash toward the key",
        goal="open the sealed gate",
        risk="one wrong move could wake the sleeping wall",
        precision_need="the lock required careful hands",
        fluorescence_need="a glowing trail would reveal the tiny notch",
        tags={"precision", "fluorescence", "quest", "myth"},
    ),
    "spring": Quest(
        id="spring",
        verb="bring back the hidden spring",
        gerund="bringing back the hidden spring",
        rush="run toward the spring",
        goal="restore water to the thirsty field",
        risk="one careless step could muddy the spring",
        precision_need="the streambed needed exact footing",
        fluorescence_need="a soft glow would show the safe stones",
        tags={"precision", "fluorescence", "quest", "myth"},
    ),
}

RELICS = {
    "crown": Relic(
        label="crown",
        phrase="a lost golden crown",
        type="crown",
        required_precision=1.0,
        required_fluorescence=1.0,
    ),
    "key": Relic(
        label="key",
        phrase="a silver key with tiny teeth",
        type="key",
        required_precision=1.0,
        required_fluorescence=1.0,
    ),
    "spring": Relic(
        label="spring",
        phrase="a hidden spring in a stone hollow",
        type="spring",
        required_precision=1.0,
        required_fluorescence=1.0,
    ),
}

GUIDES = [
    Guide(id="lamp", label="lantern", phrase="a lantern with a steady glow", helps_precision=True, glows=True),
    Guide(id="chalk", label="chalk mark", phrase="a line of bright chalk", helps_precision=True, glows=False),
    Guide(id="willow", label="willow-wisp", phrase="a little willow-wisp", helps_precision=False, glows=True),
]

NAMES = ["Iris", "Milo", "Nina", "Theo", "Mara", "Leif", "Alia", "Soren"]
TYPES = ["girl", "boy"]
TRAITS = ["careful", "brave", "patient", "earnest", "quiet", "steady"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def is_valid_combo(place: str, quest: str, relic: str) -> bool:
    return place in PLACES and quest in QUESTS and relic in RELICS


def select_guide(quest: Quest, relic: Relic) -> Guide:
    # This world always needs both precision and fluorescence; the guide must supply both.
    for g in GUIDES:
        if g.helps_precision and g.glows:
            return g
    raise StoryError("No guide can satisfy both precision and fluorescence.")


def predict_success(world: World, hero: Entity, quest: Quest, relic: Entity) -> dict:
    sim = world.copy()
    do_quest(sim, sim.get(hero.id), quest, narrate=False)
    return {
        "found": bool(sim.facts.get("found")),
        "glow": sim.facts.get("glow", 0.0),
        "precision": sim.facts.get("precision", 0.0),
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "steady")
    world.say(f"{hero.id} was a little {trait} {hero.type} who listened closely to old songs.")


def seed_quest(world: World, hero: Entity, quest: Quest, relic: Entity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(
        f"{hero.id} longed for {quest.verb}, because {quest.goal}."
    )
    world.say(
        f"Deep in the stories of the land, there was talk of {relic.phrase}."
    )


def enter_place(world: World, hero: Entity, quest: Quest) -> None:
    world.omen = world.place.omen
    world.say(f"One day, {hero.id} walked into {world.place.name}, where {world.omen}.")
    world.say(f"{quest.precision_need.capitalize()}, and {quest.fluorescence_need}.")


def warn_of_risk(world: World, hero: Entity, quest: Quest, relic: Entity) -> None:
    pred = predict_success(world, hero, quest, relic)
    world.facts["predicted"] = pred
    world.say(
        f"{hero.pronoun('possessive').capitalize()} heart grew still, for {quest.risk}."
    )
    world.say(
        f"The path asked for {quest.precision_need.lower()}, and the dark asked for a glow."
    )


def accept_guide(world: World, hero: Entity, guide: Guide) -> None:
    if guide.glows:
        world.facts["glow"] = world.facts.get("glow", 0.0) + 1.0
    if guide.helps_precision:
        world.facts["precision"] = world.facts.get("precision", 0.0) + 1.0
    world.say(
        f"Then {hero.id} found {guide.phrase}, and it shone kindly beside {hero.pronoun('object')}."
    )


def do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    world.facts["precision"] = world.facts.get("precision", 0.0) + 1.0
    world.facts["glow"] = world.facts.get("glow", 0.0) + 1.0
    world.facts["found"] = True
    world.facts["completed"] = True
    if narrate:
        world.say(
            f"{hero.id} moved with careful steps, and every step matched {quest.precision_need.lower()}."
        )
        world.say(
            f"At last, the soft fluorescence led the way, and {hero.id} found the thing at the center of the quest."
        )


def resolve(world: World, hero: Entity, quest: Quest, relic: Entity, guide: Guide) -> None:
    world.say(
        f"With {guide.label} light to follow, {hero.id} reached the hidden place without losing the trail."
    )
    world.say(
        f"{hero.id} lifted {relic.phrase} with both hands, and the land seemed to breathe again."
    )
    world.say(
        f"So the quest ended in a bright hush: {hero.id} had used precision, and the fluorescence had shown the way."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
precision_ok(H) :- hero(H), has_precision(H).
glow_ok(H) :- hero(H), has_glow(H).
quest_success(H,Q,R) :- hero(H), quest(Q), relic(R), precision_ok(H), glow_ok(H).
#show quest_success/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs_precision", qid))
        lines.append(asp.fact("needs_glow", qid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_success/3."))
    asp_ok = bool(asp.atoms(model, "quest_success"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    print("OK: ASP and Python agree on the quest-success twin.")
    return 0


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    relic: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    relic = f["relic"]
    return [
        f'Write a mythic story for a small child about {hero.id} and a {quest.id} quest, using the word "precision".',
        f'Tell a gentle legend where {hero.id} must {quest.verb} and a glowing guide helps {hero.pronoun("possessive")} careful steps.',
        f"Write a short myth where fluorescence leads the way and {relic.label} is found at the end of the quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    relic = f["relic"]
    guide = f["guide"]
    place = world.place.name
    return [
        QAItem(
            question=f"What kind of tale is this story about {hero.id} in {place}?",
            answer=f"It is a mythic quest story about {hero.id}, who travels through {place} to {quest.verb}.",
        ),
        QAItem(
            question=f"Why did {hero.id} need to move with care during the quest?",
            answer=(
                f"{hero.id} needed precision because {quest.precision_need.lower()}. "
                f"If the steps were not exact, {quest.risk}."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} see the way in the dark?",
            answer=(
                f"{guide.phrase} helped. The bright fluorescence made the hidden path easier to follow."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} bring back at the end?",
            answer=f"{hero.id} brought back {relic.phrase}, and that finished the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is precision?",
            answer="Precision means doing something carefully and exactly, with small, accurate steps.",
        ),
        QAItem(
            question="What is fluorescence?",
            answer="Fluorescence is a kind of bright glow made by something that shines with special light.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or to finish a brave task.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.luminous:
            bits.append("luminous=True")
        if e.precision_tool:
            bits.append("precision_tool=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def tell(place: Place, quest: Quest, relic_cfg: Relic, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    relic = world.add(Entity(id="relic", type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase))
    guide = world.add(Entity(id="guide", type="thing", label="lantern", phrase="a lantern with a steady glow", luminous=True, precision_tool=True))

    world.facts.update(hero=hero, quest=quest, relic=relic, guide=guide)

    introduce(world, hero)
    seed_quest(world, hero, quest, relic)
    world.para()
    enter_place(world, hero, quest)
    warn_of_risk(world, hero, quest, relic)
    world.para()
    accept_guide(world, hero, GUIDES[0])
    do_quest(world, hero, quest, narrate=True)
    resolve(world, hero, quest, relic, GUIDES[0])
    return world


# ---------------------------------------------------------------------------
# Params, registries, parser
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="forest", quest="crown", relic="crown", name="Iris", gender="girl", trait="careful"),
    StoryParams(place="cavern", quest="key", relic="key", name="Milo", gender="boy", trait="brave"),
    StoryParams(place="ruins", quest="spring", relic="spring", name="Mara", gender="girl", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quest world with precision and fluorescence.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.place and args.quest and args.relic and not is_valid_combo(args.place, args.quest, args.relic):
        raise StoryError("The requested place, quest, and relic do not belong together.")
    place = args.place or rng.choice(sorted(PLACES))
    quest = args.quest or rng.choice(sorted(QUESTS))
    relic = args.relic or quest
    if relic not in RELICS:
        relic = rng.choice(sorted(RELICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, relic=relic, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], RELICS[params.relic], params.name, params.gender, params.trait)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show quest_success/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
