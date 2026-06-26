#!/usr/bin/env python3
"""
A small ghost-story world about a child, a rosemary patch, a risky dare, and a
reconciliation with a gentle ghost.

This script models a tiny classical simulation:
- a child wants to "qualify" by doing a scary task in a graveyard garden
- a warning about something "lethal" changes the plan
- dialogue, caution, and reconciliation drive the plot
- the ending proves what changed in the world state
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

HERO_NAMES = ["Mina", "Eli", "Nora", "Theo", "Lily", "Owen", "Pia", "Ruben"]
GHOST_NAMES = ["Grey", "Moss", "Iris", "Wisp"]
TRAITS = ["brave", "curious", "careful", "quiet", "stubborn", "gentle"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old garden"
    weather: str = "misty"
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    danger: str
    caution: str
    zone: str
    keyword: str


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    challenge: str
    charm: str
    name: str
    gender: str
    ghost: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


def _warn_lethal(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    ghost = world.entities.get("ghost")
    if not hero or not ghost:
        return out
    if hero.memes.get("fear", 0.0) < THRESHOLD:
        return out
    sig = ("warn", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hesitation"] = hero.memes.get("hesitation", 0.0) + 1
    out.append("The warning made the air feel colder.")
    return out


def _reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    ghost = world.entities.get("ghost")
    if not hero or not ghost:
        return out
    if hero.memes.get("kindness", 0.0) < THRESHOLD or ghost.memes.get("sadness", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile", hero.id, ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] = 0.0
    ghost.memes["sadness"] = 0.0
    ghost.visible = True
    out.append("The coldness loosened, like a fist opening.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_warn_lethal, _reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "garden": Setting(place="the old garden", weather="misty", affords={"listen", "qualify"}),
    "path": Setting(place="the stone path", weather="foggy", affords={"listen", "qualify"}),
    "yard": Setting(place="the moonlit yard", weather="still", affords={"listen", "qualify"}),
}

CHALLENGES = {
    "qualify": Challenge(
        id="qualify",
        verb="qualify for the midnight bell",
        gerund="qualifying for the midnight bell",
        danger="lethal",
        caution="careful",
        zone="graveyard gate",
        keyword="qualify",
    ),
    "cross": Challenge(
        id="cross",
        verb="cross the silent gate",
        gerund="crossing the silent gate",
        danger="lethal",
        caution="slow",
        zone="graveyard gate",
        keyword="lethal",
    ),
}

CHARMS = {
    "rosemary": Charm(
        id="rosemary",
        label="a sprig of rosemary",
        phrase="a small sprig of rosemary tied with string",
        helps={"fear", "sadness"},
    ),
    "lantern": Charm(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a warm flame",
        helps={"fear"},
    ),
    "stone": Charm(
        id="stone",
        label="a river stone",
        phrase="a smooth river stone for a pocket",
        helps={"sadness"},
    ),
}


@dataclass
class Rule:
    name: str
    apply: callable


def ghost_story_sound(challenge: Challenge) -> str:
    return {
        "qualify": "the bell would not ring unless the brave child stayed calm",
        "cross": "the gate looked like it was holding its breath",
    }.get(challenge.id, "the night felt full of waiting")


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was quiet under the mist."


def _do_challenge(world: World, hero: Entity, ghost: Entity, challenge: Challenge, charm: Charm, narrate: bool = True) -> None:
    if challenge.id not in world.setting.affords:
        raise StoryError("This setting cannot host that challenge.")
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    ghost.memes["sadness"] = ghost.memes.get("sadness", 0.0) + 1
    hero.meters[challenge.zone] = hero.meters.get(challenge.zone, 0.0) + 1
    if charm.id in {"rosemary", "lantern"}:
        hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    propagate(world, narrate=narrate)


def predict_outcome(world: World, hero: Entity, ghost: Entity, challenge: Challenge, charm: Charm) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get("hero"), sim.get("ghost"), challenge, charm, narrate=False)
    return {
        "fear": sim.get("hero").memes.get("fear", 0.0),
        "reconciled": sim.get("ghost").memes.get("sadness", 0.0) == 0.0,
    }


def introduce(world: World, hero: Entity, ghost: Entity, challenge: Challenge, charm: Charm) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.meters if False) if False else world.facts['trait']} {hero.type} who noticed quiet places.")
    world.say(f"{hero.id} loved the strange hush of {world.setting.place}, and {ghost.id} was the ghost who lived there.")
    world.say(f"At the edge of the path, {CHARMS[charm.id].label} smelled like a garden after rain.")


def dialogue(world: World, hero: Entity, ghost: Entity, challenge: Challenge, charm: Charm) -> None:
    world.say(f'"I want to {challenge.verb}," {hero.id} whispered.')
    world.say(f'"That sounds {challenge.danger}," said {ghost.id}. "Some doors stay shut for a reason."')
    world.say(f"{hero.id} held up {charm.phrase} and said, \"I only want to be brave enough to {challenge.keyword}.\"")
    world.say(f'"Brave is good," said {ghost.id}, "but careless can be lethal."')


def caution(world: World, hero: Entity, ghost: Entity, challenge: Challenge, charm: Charm) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    ghost.memes["sadness"] = ghost.memes.get("sadness", 0.0) + 1
    world.say(f"The ghost pointed at the dark gate and warned that the wrong step could be lethal.")
    world.say(f"{hero.id} stopped, because the rosemary in {charm.label} made the warning feel real.")


def reconciliation(world: World, hero: Entity, ghost: Entity, challenge: Challenge, charm: Charm) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    ghost.memes["sadness"] = ghost.memes.get("sadness", 0.0) + 1
    world.say(f"{hero.id} offered {charm.label} to {ghost.id} instead of pushing forward.")
    world.say(f"{ghost.id} smiled at the rosemary smell and said the bell could wait.")
    propagate(world, narrate=True)
    world.say(f"Together they chose a safer way to prove courage, and the gate no longer felt hungry.")


def tell(setting: Setting, challenge: Challenge, charm: Charm, hero_name: str, hero_type: str, ghost_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost_name))
    world.facts["trait"] = trait
    world.facts["challenge"] = challenge
    world.facts["charm"] = charm
    world.facts["hero"] = hero
    world.facts["ghost"] = ghost

    world.say(f"{hero.id} was a {trait} {hero_type} named {hero_name}.")
    world.say(f"{setting_detail(setting)} {ghost_name} waited there like a pale thought.")
    world.say(f"{hero.id} carried {charm.phrase}, and the rosemary smell clung to {hero.pronoun('possessive')} sleeve.")
    world.para()
    dialogue(world, hero, ghost, challenge, charm)
    caution(world, hero, ghost, challenge, charm)
    world.para()
    reconciliation(world, hero, ghost, challenge, charm)

    world.facts["resolved"] = ghost.memes.get("sadness", 0.0) == 0.0
    world.facts["fear"] = hero.memes.get("fear", 0.0)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    charm = f["charm"]
    return [
        f'Write a child-friendly ghost story that includes "{charm.label}" and the word "qualify".',
        f"Tell a spooky-but-gentle story where {hero.label} tries to {challenge.verb} but learns caution first.",
        f"Write a short ghost story with dialogue, a warning about something lethal, and a peaceful reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    challenge = f["challenge"]
    charm = f["charm"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who wanted to {challenge.verb} in the old garden?",
            answer=f"{hero.label}, a {trait} {hero.type}, wanted to {challenge.verb}.",
        ),
        QAItem(
            question=f"What did the ghost warn might be {challenge.danger}?",
            answer=f"The ghost warned that careless steps near the gate could be {challenge.danger}.",
        ),
        QAItem(
            question=f"What did {hero.label} carry that smelled like rosemary?",
            answer=f"{hero.label} carried {charm.phrase}, and the rosemary smell helped the mood soften.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {ghost.label}?",
            answer=f"They chose a safer way to show courage, and {ghost.label} stopped feeling sad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rosemary?",
            answer="Rosemary is a fragrant herb with needle-like leaves. People often use it in cooking or keep it in a garden.",
        ),
        QAItem(
            question="What does qualify mean?",
            answer="To qualify means to meet the needed condition or prove you are ready for something.",
        ),
        QAItem(
            question="What does lethal mean?",
            answer="Lethal means something can cause death. It is a serious word used for very dangerous things.",
        ),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge == "qualify" and args.charm == "stone":
        raise StoryError("A stone does not help with this rosemary ghost story.")
    place = args.place or rng.choice(sorted(SETTINGS))
    challenge = args.challenge or "qualify"
    charm = args.charm or "rosemary"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    ghost = args.ghost or rng.choice(GHOST_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if challenge not in CHALLENGES:
        raise StoryError("Unknown challenge.")
    if charm not in CHARMS:
        raise StoryError("Unknown charm.")
    return StoryParams(place=place, challenge=challenge, charm=charm, name=name, gender=gender, ghost=ghost, trait=trait)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with dialogue, caution, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ghost")
    ap.add_argument("--trait", choices=TRAITS)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CHALLENGES[params.challenge],
        CHARMS[params.charm],
        params.name,
        params.gender,
        params.ghost,
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


ASP_RULES = r"""
% A story is valid when a hero, a ghost, a challenge, and a charm are present.
valid_story(P, C, T) :- place(P), challenge(C), charm(T).

% The dangerous word in this world is lethal.
cautionary(C) :- challenge(C), danger(C, lethal).

% Reconciliation is possible when rosemary-like charm helps fear and sadness.
reconcile_possible(T) :- charm(T), helps(T, fear), helps(T, sadness).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("danger", cid, c.danger))
    for tid, t in CHARMS.items():
        lines.append(asp.fact("charm", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, c, t) for p in SETTINGS for c in CHALLENGES for t in CHARMS}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="garden", challenge="qualify", charm="rosemary", name="Mina", gender="girl", ghost="Grey", trait="careful"),
    StoryParams(place="path", challenge="cross", charm="lantern", name="Eli", gender="boy", ghost="Wisp", trait="curious"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not lead to a gentle ghostly reconciliation.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
