#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero tale with acreage, a yak,
and a hostile surprise.

Seed tale:
- A kid hero protects a family acreage.
- A yak is a gentle companion and a clue-bearing helper.
- A hostile surprise interrupts a quiet day.
- The hero uses a quick, kind superhero fix to keep everyone safe.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    acreage: str
    has_barn: bool = True
    has_fence: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    surprise: str
    hostile: bool
    causes_alarm: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    action: str
    safe_action: str
    use_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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

        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    threat: str
    power: str
    seed: Optional[int] = None


PLACES = {
    "acreage": Place(name="the acreage", acreage="the wide family acreage", tags={"acreage", "farm", "field"}),
    "backyard": Place(name="the backyard", acreage="the small backyard acreage", tags={"acreage", "yard"}),
    "hill": Place(name="the hill farm", acreage="the windy hill acreage", tags={"acreage", "hill"}),
}

HERO_NAMES = ["Nova", "Milo", "Tess", "Juno", "Rae", "Arlo", "Pia", "Ezra"]
SIDEKICK_NAMES = ["Bram", "Kip", "Dot", "Pip", "Sage", "Boo"]

THREATS = {
    "storm_yak": Threat(
        id="storm_yak",
        label="a hostile surprise from a stormy yak",
        surprise="suddenly charged out from behind the hay bales",
        hostile=True,
        tags={"yak", "hostile", "surprise"},
    ),
    "drone": Threat(
        id="drone",
        label="a hostile surprise from a buzzing drone",
        surprise="whirred down low over the corn rows",
        hostile=True,
        tags={"hostile", "surprise"},
    ),
    "mudslide": Threat(
        id="mudslide",
        label="a hostile surprise from a muddy slide of earth",
        surprise="rolled from the far bank after heavy rain",
        hostile=True,
        tags={"hostile", "surprise"},
    ),
}

POWERS = {
    "shield": Power(
        id="shield",
        label="shield burst",
        action="throw up a bright shield",
        safe_action="guide the danger away",
        use_line="Nova lifted both hands, and a shining shield bloomed over the path.",
        ending_line="The shield kept the yard calm, and the surprise rolled past harmlessly.",
        tags={"shield", "bright", "safe"},
    ),
    "speak": Power(
        id="speak",
        label="soothing voice",
        action="call out in a calm voice",
        safe_action="steady the frightened creature",
        use_line="Nova used a calm, steady voice, and the whole acre seemed to breathe slower.",
        ending_line="The angry moment softened, and the surprise lost its bite.",
        tags={"voice", "calm", "safe"},
    ),
    "scoop": Power(
        id="scoop",
        label="sky scoop",
        action="scoop up trouble and toss it beyond the fence",
        safe_action="carry the problem clear of the animals",
        use_line="Nova spun fast, scooped the trouble cleanly, and flung it over the far fence.",
        ending_line="The field was safe again, and the animals could go back to grazing.",
        tags={"scoop", "move", "safe"},
    ),
}


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.threat not in THREATS:
        raise StoryError("Unknown threat.")
    if params.power not in POWERS:
        raise StoryError("Unknown power.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    place = PLACES[params.place]
    threat = THREATS[params.threat]
    power = POWERS[params.power]

    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, role="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="yak", role="sidekick"))
    menace = world.add(Entity(id="menace", kind="thing", type=threat.id, label=threat.label, role="threat"))

    hero.meters["courage"] = 1
    hero.memes["hope"] = 1
    sidekick.meters["strength"] = 1
    sidekick.memes["trust"] = 1
    menace.memes["hostility"] = 1 if threat.hostile else 0

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        menace=menace,
        threat=threat,
        power=power,
        place=place,
    )

    world.say(
        f"{hero.id} was a small superhero who watched over {place.acreage}. "
        f"{sidekick.id} the yak stayed close by, because the two of them liked the quiet fields."
    )
    world.say(
        f"On a bright day, {hero.id} and {sidekick.id} walked past the fence and checked the grass, "
        f"the barn, and the garden rows."
    )

    world.para()
    world.say(
        f"Then came a surprise: {threat.label} {threat.surprise}. "
        f"The hostile rush made the chickens scatter and the hay wobble in a nervous pile."
    )
    hero.memes["fear"] = 1
    hero.memes["alarm"] = 1
    sidekick.memes["startled"] = 1
    menace.meters["near"] = 1

    world.para()
    world.say(
        f"{hero.id} did not run away. Instead, {hero.pronoun().capitalize()} remembered the right kind of hero work "
        f"for this kind of surprise."
    )
    world.say(power.use_line)
    hero.meters["power_used"] = 1
    if power.id == "shield":
        menace.meters["blocked"] = 1
    elif power.id == "speak":
        menace.memes["hostility"] = 0
        menace.meters["settled"] = 1
    else:
        menace.meters["removed"] = 1

    world.para()
    world.say(
        f"{sidekick.id} nudged the fence gate shut while {hero.id} finished the rescue. "
        f"{power.ending_line}"
    )
    hero.memes["hope"] += 1
    hero.memes["pride"] = 1
    sidekick.memes["trust"] += 1
    menace.meters["near"] = 0

    world.para()
    world.say(
        f"After that, the acreage felt peaceful again. {hero.id} and {sidekick.id} stood together by the barn, "
        f"watching the sunlight rest on the fields like a warm blanket."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].name
    threat = f["threat"].label
    power = f["power"].label
    return [
        f'Write a short superhero story for young children set on {place} that includes a yak and a surprise.',
        f"Tell a gentle but exciting story where {f['hero'].id} uses a {power} to handle {threat} on the acreage.",
        "Write a child-facing story about a hero, a yak friend, and a hostile surprise that ends safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    menace = f["menace"]
    threat = f["threat"]
    power = f["power"]
    place = f["place"].acreage
    return [
        QAItem(
            question=f"Who was the superhero watching over {place}?",
            answer=f"{hero.id} was the superhero watching over {place}, and {sidekick.id} the yak stayed with {hero.id}.",
        ),
        QAItem(
            question=f"What hostile surprise appeared on the acreage?",
            answer=f"{threat.label} appeared as a hostile surprise, and it {threat.surprise}.",
        ),
        QAItem(
            question=f"How did {hero.id} handle the surprise?",
            answer=f"{hero.id} used a {power.label} to handle the danger, and that helped keep the acreage safe.",
        ),
        QAItem(
            question=f"Why did the story end calmly?",
            answer=f"It ended calmly because {hero.id} and {sidekick.id} stopped the threat and stood together by the barn after the rescue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an acreage?",
            answer="An acreage is a piece of land, often with fields, fences, or a farm-like space on it.",
        ),
        QAItem(
            question="What is a yak?",
            answer="A yak is a large animal with a thick coat. Yaks can live in cold places and are strong and sturdy.",
        ),
        QAItem(
            question="What does hostile mean?",
            answer="Hostile means unfriendly or dangerous, like something that might hurt people or cause trouble.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something that happens suddenly when you do not expect it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = list(PLACES.keys())
THREAT_IDS = list(THREATS.keys())
POWER_IDS = list(POWERS.keys())


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(SETTINGS)
    threat = args.threat or rng.choice(THREAT_IDS)
    power = args.power or rng.choice(POWER_IDS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        threat=threat,
        power=power,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
threat(T) :- threat_name(T).
power(P) :- power_name(P).

hostile_surprise(T) :- threat(T), hostile(T), surprise_event(T).
safe_resolution(P) :- power(P), helps_safe(P).

valid_story(Place, Threat, Power) :-
    place(Place),
    threat(Threat),
    power(Power),
    hostile(Threat),
    surprise_event(Threat),
    helps_safe(Power).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        if t.hostile:
            lines.append(asp.fact("hostile", tid))
        lines.append(asp.fact("surprise_event", tid))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("helps_safe", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, t, pw) for p in PLACES for t in THREATS for pw in POWERS}
    clingo_set = set(asp_valid_stories())
    if clingo_set == py:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(clingo_set - py))
    print("only in Python:", sorted(py - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with acreage, yak, and hostile surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREAT_IDS)
    ap.add_argument("--power", choices=POWER_IDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="acreage", hero_name="Nova", hero_type="girl", sidekick_name="Bram", threat="storm_yak", power="shield"),
        StoryParams(place="backyard", hero_name="Milo", hero_type="boy", sidekick_name="Kip", threat="drone", power="speak"),
        StoryParams(place="hill", hero_name="Tess", hero_type="girl", sidekick_name="Dot", threat="mudslide", power="scoop"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for st in stories:
            print(" ", st)
        return

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.threat} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
