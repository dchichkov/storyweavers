#!/usr/bin/env python3
"""
A small folk-tale story world about kindness, surprise, friendship, a tiny mag,
and a gecko that learns to trust.

The premise is simple: in a village, a child finds a little mag and meets a shy
gecko. The child tries to keep the mag safe, the gecko becomes curious, and a
surprise opens the way to friendship.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "wet": 0.0, "worry": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "surprise": 0.0, "friendship": 0.0, "curiosity": 0.0, "fear": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    wonder: str
    reveals: str
    topic: str
    used_in: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    type: str
    label: str
    shy: bool = True
    likes: set[str] = field(default_factory=set)
    gift_topic: str = ""


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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village_green": Setting(place="the village green", affords={"find", "share"}),
    "lantern_hut": Setting(place="the lantern hut", indoors=True, affords={"find", "read"}),
    "orchard": Setting(place="the old orchard", affords={"find", "share"}),
}

ARTIFACTS = {
    "mag": Artifact(
        id="mag",
        label="mag",
        phrase="a little mag with a bright cover",
        wonder="glimmer",
        reveals="a surprise picture of a faraway hill",
        topic="mag",
        used_in={"find", "read"},
    ),
    "shellbook": Artifact(
        id="shellbook",
        label="shellbook",
        phrase="a shellbook with a woven strap",
        wonder="hum",
        reveals="a surprise map of the creek path",
        topic="surprise",
        used_in={"find", "read"},
    ),
}

COMPANIONS = {
    "gecko": Companion(
        id="gecko",
        type="gecko",
        label="gecko",
        shy=True,
        likes={"warm stone", "kind voice", "water bowl"},
        gift_topic="kindness",
    ),
    "moth": Companion(
        id="moth",
        type="moth",
        label="moth",
        shy=True,
        likes={"lamp", "quiet song"},
        gift_topic="surprise",
    ),
}

ACTIVITY_WORDS = {
    "find": {
        "verb": "find",
        "gerund": "finding",
        "gesture": "look beneath the bench",
        "risk": "startle",
        "effect": {"surprise": 1.0, "curiosity": 1.0},
    },
    "share": {
        "verb": "share",
        "gerund": "sharing",
        "gesture": "set out a little bowl of water",
        "risk": "none",
        "effect": {"kindness": 1.0, "friendship": 1.0},
    },
    "read": {
        "verb": "read",
        "gerund": "reading",
        "gesture": "open the bright pages slowly",
        "risk": "captivate",
        "effect": {"surprise": 1.0, "friendship": 0.5},
    },
}


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    artifact: str
    companion: str
    hero_name: str
    hero_type: str = "girl"
    parent_type: str = "mother"
    trait: str = "kind"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable if the place affords the chosen activity.
valid_story(Place, Act, Art, Comp) :- affords(Place, Act), artifact(Art), companion(Comp).

% The mag-like artifact is central only when it can be found or read.
usable_artifact(Art, Act) :- artifact(Art), used_in(Art, Act).

% A gecko is a good fit for kindness stories because it likes gentle care.
good_companion(Comp) :- companion(Comp), gift_topic(Comp, kindness).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("used_in", aid, *sorted(art.used_in)[0:1]) if False else "")
        for act in sorted(art.used_in):
            lines.append(asp.fact("used_in", aid, act))
        lines.append(asp.fact("topic", aid, art.topic))
    for cid, comp in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        lines.append(asp.fact("gift_topic", cid, comp.gift_topic))
    return "\n".join(line for line in lines if line)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_stories() ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python story gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(params: StoryParams) -> bool:
    setting = SETTINGS.get(params.place)
    artifact = ARTIFACTS.get(params.artifact)
    companion = COMPANIONS.get(params.companion)
    if not setting or not artifact or not companion:
        return False
    if params.activity not in setting.affords:
        return False
    if params.activity not in artifact.used_in:
        return False
    if params.companion == "gecko" and params.trait not in {"kind", "curious", "gentle"}:
        return False
    return True


def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for act in SETTINGS[place].affords:
            for art in ARTIFACTS:
                for comp in COMPANIONS:
                    params = StoryParams(place=place, activity=act, artifact=art, companion=comp, hero_name="Lina")
                    if valid_story(params):
                        out.append((place, act, art, comp))
    return out


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: str, artifact: Artifact, companion: Companion,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "patient"]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    comp = world.add(Entity(id=companion.id, kind="character", type=companion.type, label=companion.label, traits=["shy"]))

    world.facts.update(hero=hero, parent=parent, comp=comp, artifact=artifact, activity=activity)

    # Act 1: discovery
    world.say(
        f"Long ago, in {setting.place}, {hero.id} was a {trait} little {hero.type} who loved folk songs and quiet paths."
    )
    world.say(
        f"One morning, {hero.id} noticed {artifact.phrase} near a stone wall."
    )
    world.say(
        f"{artifact.label.capitalize()} had a soft {artifact.wonder}, and {hero.id} wondered if it hid a story."
    )

    # Act 2: surprise and tension
    world.para()
    world.say(
        f"As {hero.id} began {ACTIVITY_WORDS[activity]['gerund']}, a shy {comp.label} peeked out from a crack in the stones."
    )
    comp.memes["fear"] += 1
    comp.memes["curiosity"] += 1
    hero.memes["surprise"] += 1
    world.say(
        f"The little {comp.label} stared at {artifact.label} because it looked like a tiny treasure."
    )
    world.say(
        f"{hero.id} could see the {comp.label} was not trying to steal anything; it was only captivated by the shine."
    )

    # Act 3: kindness -> friendship
    world.para()
    if activity == "find":
        world.say(
            f"{hero.id} did not chase the {comp.label}. Instead, {hero.id} knelt down and spoke in a soft voice."
        )
        world.say(
            f"Then {hero.id} used a gentle hand to {ACTIVITY_WORDS['share']['gesture']} beside the warm stone."
        )
        world.say(
            f"The {comp.label} crept closer, and the surprise became kindness when the little creature lapped the water."
        )
        comp.memes["fear"] = 0.0
        comp.memes["friendship"] += 1
        hero.memes["kindness"] += 1
        hero.memes["friendship"] += 1
        world.say(
            f"Inside {artifact.label}, {artifact.reveals} was hidden, and that second surprise made {hero.id} laugh."
        )
        world.say(
            f"By sunset, {hero.id} and the {comp.label} were sitting together on the same stone, as if they had always been friends."
        )
    else:
        world.say(
            f"{hero.id} opened {artifact.label} slowly, so the bright pages would not frighten the {comp.label}."
        )
        world.say(
            f"The pages showed {artifact.reveals}, and the little {comp.label} blinked with wonder."
        )
        world.say(
            f"{hero.id} offered a cup of water and a crumb of bread, and that kindness softened the shy heart at once."
        )
        comp.memes["fear"] = 0.0
        comp.memes["friendship"] += 1
        hero.memes["kindness"] += 1
        hero.memes["friendship"] += 1
        world.say(
            f"Before the stars came out, the {comp.label} curled beside {hero.id}, and the village felt blessed by a small surprise."
        )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk-tale story for a child about kindness, surprise, and friendship that includes the word "{f["artifact"].label}".',
        f"Tell a gentle story where {f['hero'].id} and a gecko meet in {world.setting.place} and a small surprise leads to friendship.",
        f'Write a simple story with a magical little "{f["artifact"].label}" and a shy gecko that ends with kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, comp, art = f["hero"], f["parent"], f["comp"], f["artifact"]
    return [
        QAItem(
            question=f"Who found {art.label} in the story?",
            answer=f"{hero.id} found {art.label} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What kind of creature was the shy friend?",
            answer=f"The shy friend was a {comp.label}, and it watched {hero.id} with curious eyes.",
        ),
        QAItem(
            question=f"What made the gecko and the child become friends?",
            answer=(
                f"{hero.id} showed kindness by speaking softly and sharing water, "
                f"so the surprise turned into friendship."
            ),
        ),
        QAItem(
            question=f"What surprise was hidden in {art.label}?",
            answer=f"{art.reveals.capitalize()} was hidden in {art.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone is gentle, helpful, and caring toward another person or creature.",
        ),
        QAItem(
            question="What is surprise?",
            answer="A surprise is something unexpected that makes people pause and look closely.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm bond between friends who trust and enjoy being together.",
        ),
        QAItem(
            question="What is a gecko?",
            answer="A gecko is a small lizard that can climb walls and often likes warm places.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="village_green", activity="find", artifact="mag", companion="gecko", hero_name="Lina", hero_type="girl", parent_type="mother", trait="kind"),
    StoryParams(place="lantern_hut", activity="read", artifact="shellbook", companion="gecko", hero_name="Marek", hero_type="boy", parent_type="father", trait="gentle"),
    StoryParams(place="orchard", activity="find", artifact="shellbook", companion="gecko", hero_name="Nia", hero_type="girl", parent_type="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: kindness, surprise, friendship, mag, gecko.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=["find", "share", "read"])
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["kind", "curious", "gentle", "brave"])
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
    place = args.place or rng.choice(list(SETTINGS))
    setting = SETTINGS[place]

    activity = args.activity or rng.choice(sorted(setting.affords))
    artifact = args.artifact or rng.choice([a for a in ARTIFACTS if activity in ARTIFACTS[a].used_in])
    companion = args.companion or "gecko"

    params = StoryParams(
        place=place,
        activity=activity,
        artifact=artifact,
        companion=companion,
        hero_name=args.name or rng.choice(["Lina", "Mira", "Suri", "Pavo", "Tia"]),
        hero_type=args.gender or rng.choice(["girl", "boy"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(["kind", "curious", "gentle"]),
    )

    if not valid_story(params):
        raise StoryError("The chosen options do not make a reasonable folk-tale story.")
    return params


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid story parameters for this world.")
    world = tell(
        SETTINGS[params.place],
        params.activity,
        ARTIFACTS[params.artifact],
        COMPANIONS[params.companion],
        params.hero_name,
        params.hero_type,
        params.parent_type,
        params.trait,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name}: {p.activity} in {p.place} with {p.companion}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
