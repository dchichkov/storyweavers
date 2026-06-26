#!/usr/bin/env python3
"""
A standalone story world for a slice-of-life tale about intelligence,
sharing, teamwork, and a small conflict that ends in cooperation.

Seed idea:
- A very smart child loves solving puzzles.
- The child has a special set of strategy cards / logic tiles / markers.
- Friends want to share them for a team challenge.
- The child worries about losing them or not being credited.
- A gentle conflict grows.
- The group finds a fair sharing plan and succeeds together.

This file implements a small simulated world where meters track things like
focus, frustration, trust, and teamwork; memes track social-emotional state.
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
# World entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    activity: str
    setting_line: str
    affordance: str
    mood: str


@dataclass
class Skill:
    id: str
    label: str
    phrase: str
    activity_line: str
    risk_line: str
    team_line: str
    conflicts_with: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)


@dataclass
class TeamItem:
    id: str
    label: str
    phrase: str
    color: str
    plural: bool = False


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SCENES = {
    "classroom": Scene(
        place="the classroom",
        activity="solve a team puzzle",
        setting_line="The classroom was bright and calm, with a table of puzzle pieces waiting near the window.",
        affordance="table",
        mood="quiet",
    ),
    "library": Scene(
        place="the library corner",
        activity="build a story map",
        setting_line="The library corner was soft and still, with low shelves and a big paper map on the table.",
        affordance="table",
        mood="calm",
    ),
    "clubroom": Scene(
        place="the clubroom",
        activity="finish a group project",
        setting_line="The clubroom hummed with tiny voices, paper scraps, and a long table full of shared supplies.",
        affordance="table",
        mood="busy",
    ),
}

SKILLS = {
    "logic_tiles": Skill(
        id="logic_tiles",
        label="logic tiles",
        phrase="a neat box of logic tiles",
        activity_line="loved sorting the logic tiles into clever patterns",
        risk_line="the tiles might get mixed up or lost if everybody handled them at once",
        team_line="the tiles worked best when the group used them carefully together",
        conflicts_with={"grabby"},
        supports={"sharing", "teamwork", "intelligence"},
    ),
    "marker_set": Skill(
        id="marker_set",
        label="marker set",
        phrase="a bright marker set",
        activity_line="enjoyed drawing clear arrows and labels on big paper",
        risk_line="the markers might dry out or roll away if they were not shared neatly",
        team_line="the markers were perfect for making one plan that everyone could see",
        conflicts_with={"messy"},
        supports={"sharing", "teamwork"},
    ),
    "story_cards": Skill(
        id="story_cards",
        label="story cards",
        phrase="a pack of story cards",
        activity_line="liked arranging the cards into smart story steps",
        risk_line="the cards could get bent if people snatched them too fast",
        team_line="the cards helped the group think together and make one good plan",
        conflicts_with={"grabby"},
        supports={"sharing", "teamwork", "intelligence"},
    ),
}

TEAM_ITEMS = {
    "clipboard": TeamItem(id="clipboard", label="clipboard", phrase="a sturdy clipboard", color="blue"),
    "timer": TeamItem(id="timer", label="timer", phrase="a little kitchen timer", color="yellow"),
    "sticky_notes": TeamItem(id="sticky_notes", label="sticky notes", phrase="a stack of sticky notes", color="green", plural=True),
}

HERO_NAMES = ["Mina", "Eli", "Noah", "Iris", "Theo", "Lina", "Soren", "Pia"]
FRIEND_NAMES = ["Jae", "Rin", "Nia", "Omar", "Zuri", "Finn", "Bea", "Tari"]
TRAITS = ["bright", "careful", "curious", "patient", "quick-thinking", "serious"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    scene: str
    skill: str
    team_item: str
    name: str
    gender: str
    friend: str
    parent_or_teacher: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    world = World(scene=scene)

    hero_type = params.gender
    helper_type = "boy" if params.gender == "girl" else "girl"

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_type,
        meters={"focus": 2.0, "trust": 1.0, "frustration": 0.0, "sharing": 0.0, "teamwork": 0.0},
        memes={"pride": 1.0, "care": 1.0, "worry": 0.0, "conflict": 0.0, "joy": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=helper_type,
        meters={"focus": 1.5, "trust": 1.0, "frustration": 0.0, "sharing": 0.0, "teamwork": 0.0},
        memes={"pride": 0.5, "care": 1.0, "worry": 0.0, "conflict": 0.0, "joy": 0.0},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=params.parent_or_teacher,
        meters={"calm": 2.0, "trust": 2.0, "patience": 2.0},
        memes={"warmth": 2.0, "worry": 0.0, "joy": 0.0},
    ))
    skill = SKILLS[params.skill]
    item = TEAM_ITEMS[params.team_item]
    tool = world.add(Entity(
        id=skill.id,
        type="tool",
        label=skill.label,
        phrase=skill.phrase,
        owner=hero.id,
        caretaker=adult.id,
        held_by=hero.id,
        plural=False,
        meters={"order": 2.0, "value": 1.0},
        memes={"specialness": 2.0},
    ))
    shared = world.add(Entity(
        id=item.id,
        type="tool",
        label=item.label,
        phrase=item.phrase,
        owner=adult.id,
        caretaker=adult.id,
        held_by=None,
        plural=item.plural,
        meters={"helpfulness": 2.0},
        memes={"shared": 0.0},
    ))

    world.facts.update(hero=hero, friend=friend, adult=adult, skill=skill, item=shared, tool=tool)
    return world


def intro(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    skill: Skill = f["skill"]
    world.say(
        f"{hero.id} was a {hero.pronoun('subject')} little {hero.type} who was known for {world.scene.mood} "
        f"thinking and a very high kind of intelligence."
    )
    world.say(
        f"{hero.id} {skill.activity_line}, and {skill.label} always seemed to make {hero.pronoun('possessive')} eyes shine."
    )


def setup_need(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    tool: Entity = f["tool"]
    adult: Entity = f["adult"]
    world.say(
        f"One afternoon, {hero.id}, {friend.id}, and {adult.pronoun('possessive')} class gathered at {world.scene.place}."
    )
    world.say(world.scene.setting_line)
    world.say(
        f"They wanted to {world.scene.activity}, and {item.phrase} would help everyone stay organized."
    )
    world.say(
        f"{hero.id} already had {tool.phrase}, but {friend.id} wanted to use it too."
    )


def cause_conflict(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    adult: Entity = f["adult"]
    skill: Skill = f["skill"]
    shared: Entity = f["item"]

    hero.meters["sharing"] += 0.5
    hero.memes["worry"] += 1.0
    hero.memes["pride"] += 1.0
    friend.memes["conflict"] += 1.0
    hero.memes["conflict"] += 1.0
    world.say(
        f"{hero.id} held the {skill.label} close and frowned. {skill.risk_line.capitalize()}."
    )
    world.say(
        f'"But I know how to use it best," {hero.id} said, and {friend.id} reached for {shared.label} at the same time.'
    )
    world.say(
        f"{friend.id} wanted a turn, and the room went quiet with a small, sticky conflict."
    )
    adult.memes["worry"] += 1.0


def resolve_teamwork(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    adult: Entity = f["adult"]
    skill: Skill = f["skill"]
    shared: Entity = f["item"]

    hero.meters["trust"] += 1.0
    friend.meters["trust"] += 1.0
    hero.meters["teamwork"] += 1.0
    friend.meters["teamwork"] += 1.0
    hero.meters["sharing"] += 1.0
    friend.meters["sharing"] += 1.0
    hero.memes["conflict"] = 0.0
    friend.memes["conflict"] = 0.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    adult.memes["joy"] += 1.0
    shared.memes["shared"] = 1.0

    world.say(
        f"{adult.type.capitalize()} smiled and suggested a fair plan: one person would sort, one would label, and one would check."
    )
    world.say(
        f"{hero.id} took a breath, handed over {skill.label}, and said that {friend.id} could help."
    )
    world.say(
        f'{friend.id} grinned and said, "You do the clever part, and I will keep the pieces in order."'
    )
    world.say(
        f"That turned the problem into teamwork, and {skill.team_line.lower()}."
    )
    world.say(
        f"Together they finished {world.scene.activity}, and {hero.id} learned that sharing did not make the thinking smaller."
    )


def ending(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    skill: Skill = f["skill"]
    world.say(
        f"By the end, {hero.id} was still the smartest kid in the room, but now {hero.id} looked happier when {friend.id} joined in."
    )
    world.say(
        f"The {skill.label} stayed safe on the table, and the group's finished work looked neat and proud."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    setup_need(world)
    world.para()
    cause_conflict(world)
    world.para()
    resolve_teamwork(world)
    world.para()
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Registries and parameter resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [(scene, skill, item) for scene in SCENES for skill in SKILLS for item in TEAM_ITEMS]


def explain_rejection(scene: str, skill: str, item: str) -> str:
    return (
        f"(No story: the requested combination {scene}/{skill}/{item} does not fit this simple slice-of-life scene.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: intelligence, sharing, teamwork, and a small conflict in a slice-of-life scene."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--skill", choices=SKILLS)
    ap.add_argument("--item", choices=TEAM_ITEMS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent-or-teacher", choices=["mother", "father", "teacher"], dest="parent_or_teacher")
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
    scene = args.scene or rng.choice(list(SCENES))
    skill = args.skill or rng.choice(list(SKILLS))
    item = args.item or rng.choice(list(TEAM_ITEMS))
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES if gender == "girl" else HERO_NAMES + ["Owen", "Kai"])
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    parent_or_teacher = args.parent_or_teacher or rng.choice(["teacher", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        scene=scene,
        skill=skill,
        team_item=item,
        name=name,
        gender=gender,
        friend=friend,
        parent_or_teacher=parent_or_teacher,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    skill: Skill = f["skill"]
    return [
        f'Write a short slice-of-life story about a very intelligent child named {hero.id} who learns to share {skill.label}.',
        f"Tell a gentle story where {hero.id} and a friend disagree over {skill.phrase}, then solve the problem with teamwork.",
        f'Write a child-friendly story that includes the words "intelligence", "sharing", "teamwork", and "conflict".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    adult: Entity = f["adult"]
    skill: Skill = f["skill"]
    qa = [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, a very intelligent child who learns to share and work with {friend.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} want to do together?",
            answer=f"They wanted to {world.scene.activity}, and {skill.label} helped them do it well.",
        ),
        QAItem(
            question=f"Why did the small conflict start?",
            answer=f"The conflict started because {hero.id} wanted to keep {skill.label} to {hero.id.lower()}self, while {friend.id} also wanted a turn.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{adult.pronoun('subject').capitalize()} helped them make a fair plan, and then {hero.id} shared {skill.label} so the group could finish together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} was still smart, but {hero.id} was also kinder about sharing, and the team finished the job happily.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    skill: Skill = f["skill"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"What is sharing?",
            answer="Sharing means letting other people use something, enjoy something, or be part of a turn instead of keeping it all for yourself.",
        ),
        QAItem(
            question=f"What is teamwork?",
            answer="Teamwork means people work together, help each other, and each do a part of the job so the whole group can finish.",
        ),
        QAItem(
            question=f"What is a conflict?",
            answer="A conflict is a disagreement or a moment when people want different things and need to work it out.",
        ),
        QAItem(
            question=f"Why might {skill.label} be useful in a group?",
            answer=f"{skill.label.capitalize()} can help a group think carefully, keep ideas organized, and make a better plan together.",
        ),
        QAItem(
            question=f"What does {item.label} help a group do?",
            answer=f"{item.label.capitalize()} helps the group keep track of materials so everyone can use them without confusion.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a scene, a skill, and a shared item are available.
valid_story(S, K, I) :- scene(S), skill(K), item(I).

% Intelligence high: the hero must be able to use a skill that supports intelligence.
intelligent_story(K) :- skill(K), supports(K, intelligence).

% Sharing and teamwork are required for this world.
team_story(K) :- skill(K), supports(K, sharing), supports(K, teamwork).

% Conflict appears when the skill has a matching tension mode.
conflict_story(K) :- skill(K), conflicts_with(K, grabby).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for k, skill in SKILLS.items():
        lines.append(asp.fact("skill", k))
        for tag in skill.supports:
            lines.append(asp.fact("supports", k, tag))
        for c in skill.conflicts_with:
            lines.append(asp.fact("conflicts_with", k, c))
    for i in TEAM_ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(clingo_model, "valid_story"))
    if py != clingo_set:
        print("MISMATCH between ASP and Python:")
        print("python:", sorted(py))
        print("asp:   ", sorted(clingo_set))
        return 1

    sample = generate(resolve_params(argparse.Namespace(
        scene=None, skill=None, item=None, name=None, friend=None, gender=None,
        parent_or_teacher=None, trait=None
    ), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generated story is empty")
        return 1
    print(f"OK: ASP parity and sample generation verified ({len(py)} combos).")
    return 0


# ---------------------------------------------------------------------------
# Emission / CLI
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("classroom", "logic_tiles", "clipboard", "Mina", "girl", "Jae", "teacher", "bright"),
            StoryParams("library", "story_cards", "sticky_notes", "Eli", "boy", "Rin", "father", "curious"),
            StoryParams("clubroom", "marker_set", "timer", "Iris", "girl", "Nia", "mother", "patient"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.skill} in {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
