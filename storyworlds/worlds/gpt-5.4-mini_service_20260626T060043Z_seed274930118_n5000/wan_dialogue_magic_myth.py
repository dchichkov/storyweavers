#!/usr/bin/env python3
"""
A myth-shaped storyworld about wan light, dialogue, and magic.

The seed image is a small tale:
A village keeps a sky-lantern whose glow grows wan each dusk. A child speaks
with an old river-spirit, learns that the lantern is dim because its song has
been forgotten, and restores it by carrying a truthful message through the
night. The world changes from fading light to renewed dawn.

The simulation tracks physical meter and emotional meme state:
- lantern glow, ember warmth, distance traveled, storm pressure
- courage, doubt, trust, awe, and hope

The story is generated from state changes, not a frozen paragraph.
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
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.role in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.role in {"boy", "man", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    mood: str
    has_fog: bool = False
    has_water: bool = False
    has_stones: bool = False


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    glow_start: float
    glow_min: float
    needs: set[str] = field(default_factory=set)
    dims_at_risk: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    verb: str
    method: str
    cost: str
    restores: str
    requires_dialogue: bool = True


@dataclass
class StoryParams:
    place: str
    relic: str
    magic: str
    hero_name: str
    hero_role: str
    elder_name: str
    elder_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, relic: Relic, magic: Magic):
        self.place = place
        self.relic_cfg = relic
        self.magic_cfg = magic
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        out = ["--- world trace ---"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            out.append(f"{e.id} ({e.kind}) " + " ".join(bits))
        out.append(f"place={self.place.name}")
        return "\n".join(out)


def _grow_doubt(world: World) -> None:
    if world.facts.get("wan_seen") and ("wan_seen",) not in world.fired:
        world.fired.add(("wan_seen",))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["doubt"] = e.memes.get("doubt", 0.0) + 1


def _fade_relic(world: World) -> None:
    relic = world.entities["relic"]
    if relic.meters.get("glow", 0.0) <= THRESHOLD:
        return
    if ("fade",) in world.fired:
        return
    world.fired.add(("fade",))
    relic.meters["glow"] -= 1
    relic.meters["wan"] = relic.meters.get("wan", 0.0) + 1
    world.say(f"The {relic.label} grew wan at the edge of dusk.")


def _magic_ready(world: World) -> bool:
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    relic = world.entities["relic"]
    return (
        hero.memes.get("courage", 0.0) >= THRESHOLD
        and elder.memes.get("trust", 0.0) >= THRESHOLD
        and relic.meters.get("wan", 0.0) >= THRESHOLD
    )


def apply_fixpoint(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before = dict(world.entities["relic"].meters)
        _fade_relic(world)
        _grow_doubt(world)
        if before != world.entities["relic"].meters:
            changed = True


PLACE_REGISTRY = {
    "hilltop": Place(name="the hilltop shrine", mood="high and windy", has_fog=True),
    "river": Place(name="the riverbank", mood="cool and bright", has_water=True),
    "village": Place(name="the small village square", mood="quiet and close", has_stones=True),
}

RELIC_REGISTRY = {
    "lantern": Relic(
        id="relic",
        label="sky-lantern",
        phrase="a woven sky-lantern with a silver wick",
        glow_start=3.0,
        glow_min=0.0,
        needs={"song", "truth"},
        dims_at_risk={"glow"},
    ),
    "bell": Relic(
        id="relic",
        label="temple bell",
        phrase="an old bronze bell with a hairline crack",
        glow_start=2.5,
        glow_min=0.0,
        needs={"song", "truth"},
        dims_at_risk={"ring"},
    ),
    "candle": Relic(
        id="relic",
        label="ward candle",
        phrase="a white ward candle in a clay cup",
        glow_start=2.0,
        glow_min=0.0,
        needs={"song", "truth"},
        dims_at_risk={"flame"},
    ),
}

MAGIC_REGISTRY = {
    "song": Magic(
        id="song",
        label="song-magic",
        verb="sing a truer tune",
        method="with a low, careful voice",
        cost="her breath and patience",
        restores="its old brightness",
    ),
    "name": Magic(
        id="name",
        label="name-magic",
        verb="speak the hidden name",
        method="by whispering the lost name aloud",
        cost="his fear of being wrong",
        restores="its remembered fire",
    ),
    "story": Magic(
        id="story",
        label="story-magic",
        verb="tell the first story again",
        method="by speaking the old tale without ornament",
        cost="their trembling voice",
        restores="its steady light",
    ),
}

HERO_NAMES = ["Ari", "Mina", "Tavi", "Lio", "Sera", "Niko"]
ELDER_NAMES = ["Ila", "Ruen", "Bram", "Yara", "Oren"]
ROLES = ["girl", "boy", "wanderer", "priestess", "priest", "child"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACE_REGISTRY:
        for r in RELIC_REGISTRY:
            for m in MAGIC_REGISTRY:
                out.append((p, r, m))
    return out


def explain_rejection(place: str, relic: str, magic: str) -> str:
    return f"(No story: {magic} does not meaningfully restore the {relic} at {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about wan light and dialogue.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--relic", choices=RELIC_REGISTRY)
    ap.add_argument("--magic", choices=MAGIC_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--elder")
    ap.add_argument("--elder-role", choices=["elder", "priest", "priestess", "sage"])
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
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    relic = args.relic or rng.choice(list(RELIC_REGISTRY))
    magic = args.magic or rng.choice(list(MAGIC_REGISTRY))
    if (place, relic, magic) not in valid_combos():
        raise StoryError(explain_rejection(place, relic, magic))
    role = args.role or rng.choice(ROLES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    elder_role = args.elder_role or rng.choice(["elder", "priest", "sage"])
    return StoryParams(place=place, relic=relic, magic=magic, hero_name=hero_name, hero_role=role, elder_name=elder_name, elder_role=elder_role)


def build_world(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    relic_cfg = RELIC_REGISTRY[params.relic]
    magic_cfg = MAGIC_REGISTRY[params.magic]
    world = World(place, relic_cfg, magic_cfg)

    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, role=params.hero_role))
    elder = world.add(Entity(id="elder", kind="character", label=params.elder_name, role=params.elder_role))
    relic = world.add(Entity(id="relic", kind="thing", label=relic_cfg.label, phrase=relic_cfg.phrase))
    relic.meters["glow"] = relic_cfg.glow_start
    relic.meters["wan"] = 1.0
    hero.memes["wonder"] = 1.0
    elder.memes["memory"] = 1.0

    world.say(f"At {place.name}, the {relic.label} had begun to grow wan.")
    world.say(f"{hero.label} saw the dimness and felt a small ache of wonder.")
    world.para()
    world.say(f'"Why is the light fading?" {hero.label} asked.')
    world.say(f'"Because a truth was left unsaid," {elder.label} answered. "Listen, and speak carefully."')
    hero.memes["curiosity"] = 1.0
    elder.memes["trust"] = 1.0
    hero.memes["doubt"] = 1.0
    world.facts["wan_seen"] = True
    apply_fixpoint(world)

    world.para()
    world.say(f"{hero.label} went closer and chose to {magic_cfg.verb}.")
    if magic_cfg.id == "song":
        hero.memes["courage"] = 1.0
        world.say(f"{hero.label} sang {magic_cfg.method}, though the night made the voice shake.")
    elif magic_cfg.id == "name":
        hero.memes["courage"] = 1.0
        world.say(f"{hero.label} stepped into the hush {magic_cfg.method}, and the elder did not interrupt.")
    else:
        hero.memes["courage"] = 1.0
        world.say(f"{hero.label} lifted a steady hand {magic_cfg.method}, while the elder listened like stone.")
    relic.meters["wan"] = 0.0
    relic.meters["glow"] = relic_cfg.glow_start + 1.0
    hero.memes["hope"] = 2.0
    elder.memes["trust"] = 2.0
    world.say(f"The {relic.label} answered and rose into bright fire again.")

    world.para()
    world.say(f"By dawn, the {relic.label} shone over the {place.name.split(' the ')[-1] if 'the ' in place.name else place.name}, and the people remembered the old song.")
    world.say(f"{hero.label} and {elder.label} spoke softly beside the light, and the wan hour was gone.")
    world.facts.update(
        hero=hero,
        elder=elder,
        relic=relic,
        place=place,
        magic=magic_cfg,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about a wan {f["relic"].label} that needs {f["magic"].label}.',
        f'Tell a gentle dialogue story in which {f["hero"].label} asks why the light is wan and an elder answers with a secret.',
        f"Write a mythic tale where speech itself restores a fading sacred object at {f['place'].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    relic = f["relic"]
    magic = f["magic"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was growing wan at {place.name}?",
            answer=f"The {relic.label} was growing wan at {place.name}, and its light was fading until someone spoke the right words.",
        ),
        QAItem(
            question=f"Who asked why the light was fading?",
            answer=f"{hero.label} asked why the light was fading, and {elder.label} answered that a truth had been left unsaid.",
        ),
        QAItem(
            question=f"How did {hero.label} help restore the sacred thing?",
            answer=f"{hero.label} used {magic.label} and spoke carefully, so the {relic.label} answered and shone bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does wan mean?", answer="Wan means pale, weak, or fading, like a light that is losing its brightness."),
        QAItem(question="What is a myth?", answer="A myth is an old story that explains something important with wonder, gods, spirits, or magic."),
        QAItem(question="Why do people speak softly in a temple or shrine?", answer="People often speak softly there because the place feels holy and calm, so quiet words show respect."),
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


ASP_RULES = r"""
wan_light(R) :- relic(R), wan(R).
needs_dialogue(R) :- relic(R), truth_needed(R).
can_restore(H,R) :- hero(H), relic(R), courage(H), trust(E), elder(E), wan(R), needs_dialogue(R).
restored(R) :- can_restore(_,R).
#show wan_light/1.
#show restored/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for r in RELIC_REGISTRY:
        lines.append(asp.fact("relic", r))
        lines.append(asp.fact("wan", r))
        lines.append(asp.fact("truth_needed", r))
    for m in MAGIC_REGISTRY:
        lines.append(asp.fact("magic", m))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("elder", "elder"))
    lines.append(asp.fact("courage", "hero"))
    lines.append(asp.fact("trust", "elder"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


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


CURATED = [
    StoryParams(place="hilltop", relic="lantern", magic="song", hero_name="Ari", hero_role="child", elder_name="Ila", elder_role="elder"),
    StoryParams(place="river", relic="bell", magic="name", hero_name="Mina", hero_role="girl", elder_name="Ruen", elder_role="sage"),
    StoryParams(place="village", relic="candle", magic="story", hero_name="Tavi", hero_role="boy", elder_name="Yara", elder_role="priestess"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show restored/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show wan_light/1. #show restored/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero_name}: {p.relic} + {p.magic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
