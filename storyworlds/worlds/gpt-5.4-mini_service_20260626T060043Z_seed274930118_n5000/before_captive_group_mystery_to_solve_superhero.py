#!/usr/bin/env python3
"""
Superhero mystery storyworld: before a group rescues a captive, they must solve
a small mystery in time.

A child-facing domain with a clear turn:
- A hero hears that someone is captive.
- The hero and a group of helpers follow clues.
- Solving the mystery reveals where the captive is held and how to reach them.
- The team acts together, and the ending proves the change.

The world models both physical meters and emotional memes, and the narrative
changes based on the simulated state rather than a fixed text shell.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the city"
    indoor: bool = False
    clues: list[str] = field(default_factory=list)
    hazards: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    clue: str
    reveal: str
    solved_by: str
    location: str
    danger: str
    rescue_tool: str
    action: str
    consequence: str


@dataclass
class TeamMember:
    id: str
    type: str
    label: str
    skill: str
    aid: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city": Setting(
        place="the city",
        clues=["a window reflection", "a loose cape thread", "a muddy boot print"],
        hazards=["locked door", "high roof", "dark alley"],
    ),
    "dock": Setting(
        place="the harbor docks",
        clues=["a rope fiber", "a salt stain", "a lantern flicker"],
        hazards=["slippery boards", "fog bank", "stacked crates"],
    ),
    "museum": Setting(
        place="the museum",
        clues=["a tiny paint chip", "a quiet echo", "a half-open map case"],
        hazards=["glass hallway", "silent gallery", "hidden stair"],
    ),
}

MYSTERIES = {
    "signal": Mystery(
        id="signal",
        clue="a blinking signal on the skyline",
        reveal="a hidden door behind the old clock tower",
        solved_by="reading the signal pattern",
        location="the clock tower",
        danger="a stuck steel gate",
        rescue_tool="a magnetic beam",
        action="pulling the gate open",
        consequence="the path to the captive room",
    ),
    "shadow": Mystery(
        id="shadow",
        clue="a shadow that did not match the clouds",
        reveal="a secret tunnel under the square",
        solved_by="following the shadow's edge",
        location="the square",
        danger="a low tunnel",
        rescue_tool="a bright lantern",
        action="lighting the tunnel",
        consequence="the hidden stairs to the cellar",
    ),
    "note": Mystery(
        id="note",
        clue="a tiny note tucked into a flower pot",
        reveal="a side hall behind the painted wall",
        solved_by="matching the note to the map",
        location="the gallery",
        danger="a heavy wall panel",
        rescue_tool="a careful lever",
        action="lifting the wall panel",
        consequence="the room where the captive waited",
    ),
}

TEAM = [
    TeamMember(id="Nova", type="girl", label="Nova", skill="seeing clues fast", aid="she noticed details nobody else saw"),
    TeamMember(id="Comet", type="boy", label="Comet", skill="jumping across obstacles", aid="he reached high places quickly"),
    TeamMember(id="Echo", type="girl", label="Echo", skill="listening for tiny sounds", aid="she heard the right clue at the right time"),
    TeamMember(id="Bolt", type="boy", label="Bolt", skill="moving quickly", aid="he rushed tools where they were needed"),
]

HERO_NAMES = ["Mira", "Kai", "Tara", "Jude", "Lena", "Owen", "Zuri", "Milo"]
CAPTIVE_NAMES = ["Pip", "Rae", "Noel", "Ivy", "June", "Ari"]
TRAITS = ["brave", "kind", "quick", "careful", "bright", "gentle"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    captive_name: str
    captive_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The setting supports clues, dangers, and one mystery.
valid_story(S, M) :- setting(S), mystery(M), supports(S, M).

% A mystery is supported when its clue and reveal fit the setting.
supports(S, M) :- clue_at(S, C), mystery_clue(M, C), reveal_at(S, R), mystery_reveal(M, R).

% The rescue is reasonable only if the team has a matching tool for the danger.
can_rescue(M) :- mystery_danger(M, D), tool_for(D, T), rescue_tool(M, T).

% We want stories where there is something captive and the group can solve it.
complete_story(S, M) :- valid_story(S, M), can_rescue(M), captive_exists(S).

#show valid_story/2.
#show complete_story/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in s.clues:
            lines.append(asp.fact("clue_at", sid, c))
        for h in s.hazards:
            lines.append(asp.fact("hazard_at", sid, h))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_clue", mid, m.clue))
        lines.append(asp.fact("mystery_reveal", mid, m.reveal))
        lines.append(asp.fact("mystery_danger", mid, m.danger))
        lines.append(asp.fact("rescue_tool", mid, m.rescue_tool))
    for tool in ["magnetic beam", "bright lantern", "careful lever"]:
        lines.append(asp.fact("tool_for", tool, tool))
    lines.append(asp.fact("captive_exists", "yes"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    python_set = set(valid_story_pairs())
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python ({len(python_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def valid_story_pairs() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.hero_name == params.captive_name:
        raise StoryError("The hero and the captive must be different characters.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("Hero type must be girl or boy.")
    if params.captive_type not in {"girl", "boy"}:
        raise StoryError("Captive type must be girl or boy.")


# ---------------------------------------------------------------------------
# Simulation / narration
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    validate_params(params)
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=[params.trait, "superhero"],
        role="hero",
        meters={"energy": 2.0, "hope": 1.5},
        memes={"courage": 2.0, "worry": 0.2},
    ))
    captive = world.add(Entity(
        id=params.captive_name,
        kind="character",
        type=params.captive_type,
        label=params.captive_name,
        traits=["captive", "waiting"],
        role="captive",
        meters={"energy": 0.8},
        memes={"fear": 1.4, "hope": 0.5},
    ))
    group_names = [m.label for m in TEAM]
    team = []
    for member in TEAM:
        ent = world.add(Entity(
            id=member.id,
            kind="character",
            type=member.type,
            label=member.label,
            role="helper",
            traits=["member", "heroic"],
            meters={"energy": 1.0},
            memes={"teamwork": 1.0},
        ))
        team.append(ent)

    world.facts.update(
        hero=hero,
        captive=captive,
        team=team,
        mystery=mystery,
        group_names=group_names,
        setting=setting,
        params=params,
    )
    return world


def opening(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    captive = f["captive"]
    mystery = f["mystery"]
    setting = f["setting"]
    world.say(
        f"{hero.id} was a {hero.traits[0]} superhero who always looked for the truth before acting."
    )
    world.say(
        f"One day, {hero.id} heard that {captive.id} was captive somewhere in {setting.place}."
    )
    world.say(
        f"All anyone knew before the rescue was {mystery.clue}."
    )


def investigation(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    team = f["team"]
    world.para()
    hero.memes["worry"] += 0.4
    world.say(
        f"{hero.id} did not rush in. Instead, {hero.pronoun()} called a group of helpers and solved the mystery first."
    )
    world.say(
        f"{team[0].label} watched for small signs, {team[1].label} climbed high, {team[2].label} listened closely, and {team[3].label} carried the tools."
    )
    world.say(
        f"Together they followed the clue until they understood {mystery.solved_by}."
    )
    world.say(
        f"That is how they found {mystery.reveal}."
    )


def rescue(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    captive = f["captive"]
    mystery = f["mystery"]
    captive.memes["fear"] = max(0.0, captive.memes.get("fear", 0.0) - 1.1)
    captive.memes["hope"] = captive.memes.get("hope", 0.0) + 1.0
    hero.memes["courage"] += 0.8
    world.para()
    world.say(
        f"The group saw the danger: {mystery.danger} blocked the way to {captive.id}."
    )
    world.say(
        f"So {hero.id} and the group used {mystery.rescue_tool} for {mystery.action}."
    )
    world.say(
        f"That opened {mystery.consequence}, and at last they reached {captive.id}."
    )
    world.say(
        f"{captive.id} was safe, and the whole group smiled because the mystery was solved."
    )


def ending(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    captive = f["captive"]
    world.para()
    world.say(
        f"Before the day ended, {hero.id} and the group led {captive.id} back into the light."
    )
    world.say(
        f"{captive.id} was no longer captive, and the superhero group stood together like a bright shield."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    opening(world)
    investigation(world)
    rescue(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story about a group solving a mystery before rescuing a captive in {f["setting"].place}.',
        f"Tell a child-friendly story where {f['hero'].id} and a group of helpers solve a clue before they free {f['captive'].id}.",
        f"Write a short mystery-to-solve adventure with a captive, a group, and a brave superhero.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captive = f["captive"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a {hero.traits[0]} superhero, and a group of helpers in {setting.place}.",
        ),
        QAItem(
            question=f"What was the first mystery clue before anyone found {captive.id}?",
            answer=f"The first clue was {mystery.clue}.",
        ),
        QAItem(
            question=f"How did the group solve the problem before rescuing {captive.id}?",
            answer=f"They solved it by {mystery.solved_by}, which led them to {mystery.reveal}.",
        ),
        QAItem(
            question=f"What made the rescue possible?",
            answer=f"The team used {mystery.rescue_tool} for {mystery.action}, and that opened {mystery.consequence}.",
        ),
        QAItem(
            question=f"How did {captive.id} change by the end?",
            answer=f"{captive.id} went from being captive and worried to being safe and hopeful with the group nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to understand by looking for clues.",
        ),
        QAItem(
            question="What is a group?",
            answer="A group is a set of people who work together or stay together for a shared job.",
        ),
        QAItem(
            question="What does captive mean?",
            answer="Captive means being held somewhere and not free to leave.",
        ),
        QAItem(
            question="Why do superheroes work together?",
            answer="Superheroes work together because different helpers can bring different skills to solve a problem faster and safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
             "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--captive-name", choices=CAPTIVE_NAMES)
    ap.add_argument("--captive-type", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    captive_type = args.captive_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    captive_name = args.captive_name or rng.choice(CAPTIVE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        captive_name=captive_name,
        captive_type=captive_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def valid_story_pairs() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2.\n#show complete_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_stories()
        print(f"{len(pairs)} compatible setting/mystery pairs:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("city", "signal", "Mira", "girl", "Pip", "boy", "brave"),
            StoryParams("dock", "shadow", "Kai", "boy", "Rae", "girl", "careful"),
            StoryParams("museum", "note", "Lena", "girl", "June", "girl", "kind"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name} / {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
