#!/usr/bin/env python3
"""
Storyworld: wxyz ninth regret teamwork magic flashback tall

A small, self-contained story simulation in a tall-tale style.
A team faces a mistake, remembers an earlier moment, and uses magic plus teamwork
to set things right.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    name: str
    sidekick: str
    seed: Optional[int] = None


PLACES = {
    "barn": "the old red barn",
    "ridge": "the windy ridge",
    "fair": "the county fair",
    "dock": "the long dock",
}

NAMES = ["Wxyz", "Pip", "Mabel", "Rusty", "June", "Hank"]
SIDEKICKS = ["ninth lantern", "golden mule", "patchwork kite", "silver shovel"]

SETTING_ADJ = {
    "barn": "tall and creaky",
    "ridge": "high and sweeping",
    "fair": "bright and bustling",
    "dock": "long and swaying",
}

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"dust": 0.0, "travel": 0.0},
        memes={"pride": 1.0, "regret": 0.0, "hope": 1.0},
    ))
    partner = world.add(Entity(
        id="team",
        kind="character",
        type="friend",
        label="the team",
        meters={"carry": 0.0, "work": 0.0},
        memes={"teamwork": 0.0, "worry": 1.0},
    ))
    magic = world.add(Entity(
        id="magic",
        kind="thing",
        type="wand",
        label="a twinkling spell",
        phrase="a twinkling spell",
        meters={"spark": 0.0},
        memes={"magic": 1.0},
    ))
    flashback = world.add(Entity(
        id="flashback",
        kind="thing",
        type="memory",
        label="an old memory",
        phrase="an old memory",
        meters={"remembered": 0.0},
        memes={"flashback": 1.0},
    ))
    item = world.add(Entity(
        id="sidekick",
        kind="thing",
        type="thing",
        label=params.sidekick,
        phrase=params.sidekick,
        owner=hero.id,
        meters={"lost": 1.0, "found": 0.0},
        memes={"important": 1.0},
    ))
    world.facts.update(hero=hero.id, sidekick=item.label, place=params.place)
    return world


def tell_story(world: World) -> None:
    hero = next(e for e in world.entities.values() if e.kind == "character" and e.id != "team")
    team = world.get("team")
    magic = world.get("magic")
    flashback = world.get("flashback")
    item = world.get("sidekick")

    world.say(
        f"Folks said {hero.id} was a small spark of a child, but {hero.pronoun()} had a heart big enough to "
        f"fill {world.place}."
    )
    world.say(
        f"{hero.id} and {team.label} were setting out to carry {item.label} across {world.place}, "
        f"which was as {SETTING_ADJ[world.facts['place']]} as any place could be."
    )
    world.say(
        f"They loved the work, because {hero.id} believed teamwork could tug a cloud, and magic could wink at a river."
    )

    world.para()
    hero.meters["travel"] += 1.0
    team.memes["teamwork"] += 1.0
    world.say(
        f"But on the ninth mile, {hero.id} stopped short and felt a sharp regret in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"{hero.id} had once bragged about handling the whole job alone, and that old boast had let {item.label} slip away."
    )
    flashback.meters["remembered"] += 1.0
    hero.memes["regret"] += 1.0
    world.say(
        f"Then a flashback came nosing in like a fox: there had been a windy moment before, and the mistake had been plain as day."
    )

    world.para()
    magic.meters["spark"] += 1.0
    world.say(
        f"{hero.id} held up the twinkling spell, and the team gathered close as three bells in a storm."
    )
    world.say(
        f"One carried, one steadied, and one sang a brave tune, and together they made the path easy for {item.label}."
    )
    team.memes["teamwork"] += 2.0
    item.meters["found"] = 1.0
    item.meters["lost"] = 0.0
    hero.memes["regret"] = 0.0
    hero.memes["hope"] += 1.0
    world.say(
        f"With a flash and a flourish, the {item.label} was found, and the whole crew laughed like thunder rolling over a golden field."
    )
    world.say(
        f"{hero.id} said the old regret had taught {hero.pronoun('object')} something useful: a tall job is safer when many hands share it."
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.get(world.facts["hero"])
    item = world.get("sidekick")
    return [
        'Write a Tall Tale for a child that includes the words "wxyz", "ninth", and "regret".',
        f"Tell a story about {hero.id}, {item.label}, teamwork, magic, and a flashback, ending in a cheerful fix.",
        "Write a big-hearted tale where a mistake is remembered, then solved by friends working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero"])
    item = world.get("sidekick")
    return [
        QAItem(
            question=f"Why did {hero.id} feel regret on the ninth mile?",
            answer=(
                f"{hero.id} felt regret because {hero.pronoun()} remembered bragging about doing the job alone, "
                f"and that old mistake had let {item.label} slip away."
            ),
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=(
                f"The flashback helped {hero.id} remember that the earlier boast was the reason {item.label} had been lost."
            ),
        ),
        QAItem(
            question="How did the team fix the problem?",
            answer=(
                f"They used teamwork and a twinkling spell to carry, steady, and search together until {item.label} was found."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story for {hero.id}?",
            answer=(
                f"{hero.id} stopped feeling regret and ended with more hope, because the group found {item.label} together."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help one another to reach the same goal.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is when something wondrous happens that feels beyond everyday life, like a spell or a sparkle that changes what is possible.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory that takes the story back to something that happened before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that could produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:9} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
teamwork(H) :- helps(H,team).
regret(H) :- remembers_mistake(H).
fixed(Item) :- found(Item), teamwork(team), magic_used(magic).
story_ok :- hero(H), fixed(Item), helps(H,team).
#show story_ok/0.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero_name", "wxyz"))
    lines.append(asp.fact("helps", "wxyz", "team"))
    lines.append(asp.fact("remembers_mistake", "wxyz"))
    lines.append(asp.fact("found", "sidekick"))
    lines.append(asp.fact("magic_used", "magic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP twin accepts the story pattern.")
        return 0
    print("MISMATCH: ASP twin rejected the story pattern.")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if not params.name:
        raise StoryError("Missing hero name.")
    if not params.sidekick:
        raise StoryError("Missing sidekick object.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about teamwork, magic, and regret.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = args.place or rng.choice(list(PLACES))
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    params = StoryParams(place=place, name=name, sidekick=sidekick)
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


CURATED = [
    StoryParams(place="barn", name="Wxyz", sidekick="ninth lantern"),
    StoryParams(place="ridge", name="Pip", sidekick="patchwork kite"),
    StoryParams(place="fair", name="Mabel", sidekick="golden mule"),
    StoryParams(place="dock", name="Rusty", sidekick="silver shovel"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(sym.name == "story_ok" for sym in model) else "no_model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
            header = f"### {p.name} at {p.place} with {p.sidekick}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
