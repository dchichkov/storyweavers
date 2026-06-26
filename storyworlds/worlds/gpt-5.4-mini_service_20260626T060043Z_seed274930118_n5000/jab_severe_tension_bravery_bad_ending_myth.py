#!/usr/bin/env python3
"""
A small mythic storyworld about a brave challenger, a sharp jab, and the
severe tension that follows when courage and pride collide.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protector: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "goddess", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "god", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    affirms: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    act: str
    jab: str
    severe: str
    tension: str
    scar: str
    risk: float
    tag: str


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        other = World(self.place)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "worn_by": v.worn_by,
            "protector": v.protector, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        other.events = list(self.events)
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hill": Place(name="the moonlit hill", affirms={"spear", "shield", "cloak"}),
    "temple": Place(name="the stone temple", affirms={"spear", "shield"}),
    "shore": Place(name="the black shore", affirms={"spear", "cloak"}),
}

CHALLENGES = {
    "jab": Challenge(
        id="jab",
        act="jab",
        jab="a sudden jab",
        severe="severe tension",
        tension="tension",
        scar="a stinging mark",
        risk=1.0,
        tag="jab",
    ),
    "oath": Challenge(
        id="oath",
        act="break the oath",
        jab="a cutting jab of words",
        severe="severe tension",
        tension="tension",
        scar="a broken vow",
        risk=1.0,
        tag="oath",
    ),
    "storm": Challenge(
        id="storm",
        act="face the storm",
        jab="a cold jab of wind",
        severe="severe tension",
        tension="tension",
        scar="a soaked cloak",
        risk=1.0,
        tag="storm",
    ),
}

ARTIFACTS = {
    "shield": Artifact(
        id="shield", label="shield", phrase="a round bronze shield", region="arm",
        protects={"jab"}, plural=False
    ),
    "cloak": Artifact(
        id="cloak", label="cloak", phrase="a dusk cloak", region="shoulders",
        protects={"storm", "words"}, plural=False
    ),
    "helm": Artifact(
        id="helm", label="helm", phrase="a hollow helm", region="head",
        protects={"jab"}, plural=False
    ),
}

NAMES = ["Aster", "Iris", "Dorian", "Lyra", "Orin", "Mira", "Eira", "Cyrus"]
TITLES = ["brave", "bold", "steady", "fierce", "young"]
KINDS = {"girl", "boy", "woman", "man"}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A challenge is reasonable for the hero if the place affirms the needed rite.
can_face(P, C) :- place(P), challenge(C), affirms(P, C).

% A protective artifact is compatible if it guards against the challenge's harm.
protects(A, C) :- artifact(A), challenge(C), guards(A, C).

% A story is valid when the hero can face the challenge and has at least one
% compatible safeguard. The bad ending is still possible, but only under a real
% risk.
valid_story(P, C, A) :- can_face(P, C), protects(A, C).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(place.affirms):
            lines.append(asp.fact("affirms", pid, c))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("jab", cid, ch.jab))
        lines.append(asp.fact("severe", cid, ch.severe))
        lines.append(asp.fact("tension", cid, ch.tension))
        lines.append(asp.fact("risk", cid, int(ch.risk)))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        for c in sorted(art.protects):
            lines.append(asp.fact("guards", aid, c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> set[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


# ---------------------------------------------------------------------------
# Core story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    artifact: str
    name: str
    kind: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, place in SETTINGS.items():
        for c, ch in CHALLENGES.items():
            if p not in SETTINGS:
                continue
            for a, art in ARTIFACTS.items():
                if c in place.affirms and c in art.protects:
                    out.append((p, c, a))
    return out


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.artifact is None or combo[2] == args.artifact)
    ]
    if not combos:
        raise StoryError("No valid mythic combination matches those choices.")
    return rng.choice(sorted(combos))


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.kind,
        label=params.name,
        meters={"courage": 1.0},
        memes={"bravery": 1.0},
    ))
    foe = world.add(Entity(
        id="Foe",
        kind="character",
        type="god",
        label="the dark rival",
        meters={"jab_power": 1.0},
        memes={"pride": 1.0},
    ))
    art = world.add(Entity(
        id=params.artifact,
        kind="thing",
        type="artifact",
        label=ARTIFACTS[params.artifact].label,
        phrase=ARTIFACTS[params.artifact].phrase,
        owner=hero.id,
        worn_by=hero.id,
        protector=True,
    ))
    chal = CHALLENGES[params.challenge]

    # Act I
    world.say(f"At {world.place.name}, {hero.ref()} was known as a {params.kind} of {params.name.lower()} and a {random.choice(TITLES)} heart.")
    world.say(f"{hero.ref()} loved the old songs of bravery, where a small hand could hold a great fate.")
    world.say(f"One dawn, {hero.ref()} carried {art.phrase} and stood before {world.place.name}.")

    # Act II
    world.say(f"Then the dark rival sent {chal.jab}, and the air filled with {chal.tension}.")
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    hero.memes["bravery"] += 1.0
    hero.meters["hurt"] = hero.meters.get("hurt", 0.0) + chal.risk
    world.say(f"{hero.ref()} did not flee. {hero.pronoun().capitalize()} answered with {chal.act} and stood in the glare.")
    if params.artifact in {"shield", "helm"}:
        world.say(f"The {art.label} took the force of the blow, but not all of it.")
    else:
        world.say(f"The {art.label} could not stop the blow, and the wound grew worse.")

    # Act III: bad ending / resolution image
    world.facts = {
        "hero": hero,
        "foe": foe,
        "artifact": art,
        "challenge": chal,
        "place": params.place,
        "resolved": False,
        "bad_ending": True,
    }
    if params.artifact in {"shield", "helm"} and params.challenge == "jab":
        world.say(f"Still, the jab found a gap, and {hero.ref()} fell with {chal.severe}.")
        world.say(f"The songs of the hill remembered {hero.ref()}, but they ended on a quiet stone.")
    else:
        world.say(f"The struggle ended badly. {hero.ref()} stood, but only with {chal.severe}, and the night kept the victory.")
        world.say(f"By morning, the hill held only silence and {chal.scar}.")
    return world


def generate_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    chal: Challenge = f["challenge"]
    return [
        f"Write a short myth about {hero.ref()} facing {chal.jab} at {world.place.name}.",
        f"Tell a child-friendly legend where bravery meets {chal.severe} and the ending is sad.",
        f"Compose a mythic story about courage, a sharp jab, and a final quiet loss.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    art: Entity = f["artifact"]
    chal: Challenge = f["challenge"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.ref()}, who was brave even when {chal.jab} came from the dark rival.",
        ),
        QAItem(
            question=f"What did {hero.ref()} carry into the trial?",
            answer=f"{hero.ref()} carried {art.phrase} before stepping into {world.place.name}.",
        ),
        QAItem(
            question=f"What made the air feel heavy in the middle of the story?",
            answer=f"The dark rival's {chal.jab} made the air fill with {chal.tension}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: {hero.ref()} was left with {chal.severe}, and the place grew quiet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing to keep going even when you feel afraid.",
        ),
        QAItem(
            question="What does a shield do?",
            answer="A shield helps block a blow so part of the impact does not reach the body.",
        ),
        QAItem(
            question="What is tension in a story?",
            answer="Tension is the uneasy feeling when something important might go wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    bits = ["--- trace ---"]
    for e in world.entities.values():
        bits.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=generate_story_text(world),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of bravery, jab, and severe tension.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--challenge", choices=CHALLENGES.keys())
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=sorted(KINDS))
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
    combo = select_combo(args, rng)
    place, challenge, artifact = combo
    name = args.name or rng.choice(NAMES)
    kind = args.kind or rng.choice(sorted(KINDS))
    return StoryParams(place=place, challenge=challenge, artifact=artifact, name=name, kind=kind)


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show valid_story/3.\n")
    asp_set = set(asp.atoms(model, "valid_story"))
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in Python:", sorted(py - asp_set))
    print("Only in ASP:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show valid_story/3.\n")
        vals = sorted(set(asp.atoms(model, "valid_story")))
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, chal, art in valid_combos():
            params = StoryParams(
                place=place,
                challenge=chal,
                artifact=art,
                name=random.choice(NAMES),
                kind=random.choice(sorted(KINDS)),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
