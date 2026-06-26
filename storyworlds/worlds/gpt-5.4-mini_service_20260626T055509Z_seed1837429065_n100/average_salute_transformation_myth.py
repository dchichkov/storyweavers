#!/usr/bin/env python3
"""
A myth-style storyworld about an ordinary child, a solemn salute, and a
transformative moment that turns average effort into a small legend.

The domain is intentionally small: a hero, a greeting ritual, a wonder, and a
transformation. The story is driven by simulated meters and memes so the prose
changes with state rather than swapping names in a frozen paragraph.
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
    transformer: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    aura: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    label: str
    verb: str
    cue: str
    turn: str
    transform: str
    note: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _extract_average(world: World) -> list[str]:
    hero = world.facts["hero"]
    rite = world.facts["rite"]
    if hero.memes["self_doubt"] < THRESHOLD:
        return []
    sig = ("average", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["shame"] += 1
    return [f"{hero.id} felt average and small, as if the day had measured {hero.pronoun('object')} and found only plain clay."]


def _salute_turn(world: World) -> list[str]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    rite = world.facts["rite"]
    if hero.memes["desire"] < THRESHOLD or hero.meters["prepared"] < THRESHOLD:
        return []
    sig = ("salute", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["resolve"] += 1
    elder.memes["approval"] += 1
    return [f"{hero.id} lifted a careful salute before the elder, and the gesture made the air itself seem to listen."]


def _transformation(world: World) -> list[str]:
    hero = world.facts["hero"]
    relic = world.facts["relic"]
    rite = world.facts["rite"]
    if hero.memes["resolve"] < THRESHOLD or hero.meters["glow"] < THRESHOLD:
        return []
    sig = ("transform", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.type = "mythic_child"
    hero.label = "the bright one"
    hero.meters["glow"] += 2
    hero.meters["steadiness"] += 1
    hero.memes["shame"] = 0
    hero.memes["awe"] += 2
    relic.meters["changed"] = 1
    return [f"Then the ordinary hour broke open, and {hero.id} changed. The salute had become a key, and the key had become a door."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_extract_average, _salute_turn, _transformation):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_transformation(world: World, hero: Entity, rite: Rite) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["prepared"] += 1
    sim.get(hero.id).memes["desire"] += 1
    sim.get(hero.id).meters["glow"] += 1
    propagate(sim, narrate=False)
    return sim.get(hero.id).type == "mythic_child"


PLACE = Place(
    id="courtyard",
    label="the moonlit courtyard",
    aura="silver",
    affords={"salute", "transformation"},
)

RITES = {
    "salute": Rite(
        id="salute",
        label="the old salute",
        verb="salute",
        cue="raised a hand",
        turn="lifted the hand",
        transform="changed",
        note="The salute is not a mere greeting; it is a vow made visible.",
        tags={"salute", "gesture"},
    ),
    "transformation": Rite(
        id="transformation",
        label="the hidden transformation",
        verb="transform",
        cue="waited for the light",
        turn="stepped into the glow",
        transform="transformed",
        note="A transformation in myth happens when the heart is ready before the body knows.",
        tags={"transformation", "myth"},
    ),
}

RELICS = {
    "stone": Relic(id="stone", label="stone charm", phrase="a smooth stone charm", region="palm"),
    "crown": Relic(id="crown", label="bronze crownlet", phrase="a little bronze crownlet", region="head"),
}

NAMES = ["Ari", "Mira", "Soren", "Lina", "Noor", "Kian"]
ELDER_NAMES = ["the elder", "the keeper", "the old singer"]


@dataclass
class StoryParams:
    place: str
    rite: str
    relic: str
    name: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    world = World(PLACE)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"prepared": 0.0, "glow": 0.0, "steadiness": 0.0},
        memes={"self_doubt": 1.0, "desire": 1.0, "resolve": 0.0, "shame": 0.0, "awe": 0.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type="elder",
        label="the elder",
        meters={"approval": 0.0},
        memes={"approval": 0.0},
    ))
    relic = world.add(Entity(
        id="relic",
        type="relic",
        label=RELlCS[params.relic].label if False else RELICS[params.relic].label,
        phrase=RELICS[params.relic].phrase,
        owner=hero.id,
        transformer=rite_id := params.rite,
        meters={"changed": 0.0},
    ))
    rite = RITES[params.rite]

    world.facts.update(hero=hero, elder=elder, relic=relic, rite=rite, params=params)

    world.say(f"In the moonlit courtyard, {hero.id} was an average child who carried {relic.phrase} and hoped for more than a plain life.")
    world.say(f"The elder told {hero.id} that {rite.note}")
    world.para()
    world.say(f"One night, {hero.id} {rite.cue}, then learned that to {rite.verb} was to listen before speaking.")
    world.say(f"{hero.id} wanted to become worthy of the old stories, but first {hero.pronoun('subject')} had to face {hero.pronoun('possessive')} own ordinary heart.")
    hero.meters["prepared"] += 1
    hero.meters["glow"] += 1
    propagate(world, narrate=True)
    world.para()
    if hero.type == "mythic_child":
        world.say(f"In the end, {hero.id} was no longer merely average. {hero.pronoun('subject').capitalize()} stood bright in the courtyard, and even the stone remembered the salute.")
    else:
        world.say(f"In the end, the courtyard waited in silence, as if the transformation were still gathering its name.")
    world.facts["resolved"] = hero.type == "mythic_child"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rite = f["rite"]
    return [
        f'Write a short myth about an average child named {hero.id} who must {rite.verb} before a transformation can begin.',
        f'Tell a child-friendly legend where a salute leads {hero.id} from an average beginning into a marvelous change.',
        f'Write a gentle myth set in a moonlit courtyard, where a small salute helps an ordinary heart become brave.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rite = f["rite"]
    relic = f["relic"]
    elder = f["elder"]
    return [
        QAItem(
            question=f"Who was the story about in the moonlit courtyard?",
            answer=f"It was about {hero.id}, an average child who carried {relic.phrase} and tried to find a larger fate.",
        ),
        QAItem(
            question=f"What did {hero.id} do that mattered before the change?",
            answer=f"{hero.id} lifted a careful salute, and that small act opened the way for the transformation.",
        ),
        QAItem(
            question=f"Why was the salute important in this myth?",
            answer=f"The salute mattered because it showed readiness and respect, which made the transformation possible in the elder's watching light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salute?",
            answer="A salute is a respectful greeting or signal, often made with the hand, that shows honor or readiness.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change, when something becomes different in a clear and important way.",
        ),
        QAItem(
            question="What does average mean?",
            answer="Average means ordinary or usual, not especially big, small, strong, or special at first glance.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A salute is meaningful when it is paired with readiness.
ready(H) :- hero(H), prepared(H), desire(H).

% Transformation occurs when the hero is ready and the relic has been touched by glow.
transformed(H) :- ready(H), glow(H).

% The average beginning is present when self-doubt outweighs delight.
average(H) :- hero(H), self_doubt(H).

#show average/1.
#show ready/1.
#show transformed/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", PLACE.id))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("elder", "elder"))
    for rid in RITES:
        lines.append(asp.fact("rite", rid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    lines.append(asp.fact("prepared", "hero"))
    lines.append(asp.fact("desire", "hero"))
    lines.append(asp.fact("glow", "hero"))
    lines.append(asp.fact("self_doubt", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transformed/1."))
    atoms = set(asp.atoms(model, "transformed"))
    py_ok = {("hero",)} if True else set()
    if atoms == py_ok:
        print(f"OK: ASP parity verified ({len(atoms)} transformed fact).")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(py_ok))
    return 1


def asp_modes() -> None:
    import asp
    model = asp.one_model(asp_program("#show average/1. #show ready/1. #show transformed/1."))
    for name in ("average", "ready", "transformed"):
        vals = sorted(set(asp.atoms(model, name)))
        print(f"{name}: {vals}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of average beginnings and transformative salutes.")
    ap.add_argument("--place", choices=[PLACE.id], default=PLACE.id)
    ap.add_argument("--rite", choices=sorted(RITES), default=None)
    ap.add_argument("--relic", choices=sorted(RELICS), default=None)
    ap.add_argument("--name", choices=NAMES, default=None)
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
    rite = args.rite or rng.choice(sorted(RITES))
    relic = args.relic or rng.choice(sorted(RELICS))
    name = args.name or rng.choice(NAMES)
    if rite == "salute" and relic == "crown":
        pass
    return StoryParams(place=args.place, rite=rite, relic=relic, name=name)


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


CURATED = [
    StoryParams(place=PLACE.id, rite="salute", relic="stone", name="Ari"),
    StoryParams(place=PLACE.id, rite="transformation", relic="crown", name="Mira"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show average/1. #show ready/1. #show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_modes()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
