#!/usr/bin/env python3
"""
storyworlds/worlds/deaf_transformation_twist_lesson_learned_fable.py
=====================================================================

A small fable-style storyworld about a deaf character, a surprising twist, and
a transformation that teaches a lesson learned.

Seed inspiration:
- A village animal/fable tale where a deaf rabbit is mocked for missing calls,
  then uses sight, touch, and kindness to save the day.
- The turn is not merely a fixed moral; it is a simulated change in state:
  public teasing -> a practical problem -> a useful adaptation -> respect.

The world tracks:
- physical meters: distance, sound signals, visibility, objects carried, etc.
- emotional memes: trust, shame, pride, gratitude, curiosity, respect.

The story is generated from simulated state; the ending proves what changed.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World entities and state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the green field"
    mood: str = "bright"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    cue: str
    twist: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects_from: set[str] = field(default_factory=set)
    aids: set[str] = field(default_factory=set)
    kind: str = "thing"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


def _increase(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _increase_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Narrative mechanics
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there lived a little {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} was deaf, but {hero.pronoun('possessive')} eyes and hands were quick."
    )


def show_life(world: World, hero: Entity, action: Action) -> None:
    _increase_meme(hero, "curiosity")
    world.say(
        f"{hero.id} loved {action.gerund}, and {action.cue} helped {hero.pronoun()} notice the world in a careful way."
    )


def mockery(world: World, hero: Entity, crowd: Entity) -> None:
    _increase_meme(hero, "shame")
    _increase_meme(crowd, "pride")
    world.say(
        f"Some animals laughed because they thought {hero.id} missed too much. "
        f"They forgot that being deaf did not mean being foolish."
    )


def problem_arrives(world: World, hero: Entity, action: Action) -> None:
    _increase(hero, "distance", 1)
    _increase_meme(hero, "concern")
    world.say(
        f"One morning, a danger came to the field, and the smallest sign was the first clue. "
        f"{hero.id} could not hear it, but {hero.pronoun()} could see the trouble growing."
    )


def hint_of_twist(world: World, hero: Entity, tool: Tool) -> None:
    _increase_meme(hero, "attention")
    world.say(
        f"{hero.id} noticed {tool.phrase} shining near a stone. "
        f"It was not a noisy answer; it was a clever one."
    )


def use_tool(world: World, hero: Entity, tool: Tool, action: Action) -> None:
    _increase_meme(hero, "confidence")
    _increase(hero, "signal", 1)
    world.say(
        f"{hero.id} picked up {tool.phrase} and waved it where the light could catch it. "
        f"That sign told the others to follow {hero.pronoun('object')} at once."
    )


def rescue(world: World, hero: Entity, crowd: Entity, action: Action) -> None:
    _increase_meme(hero, "pride")
    _increase_meme(crowd, "respect", 2)
    _increase_meme(crowd, "gratitude", 1)
    world.say(
        f"The others finally saw the danger and hurried after {hero.id}. "
        f"Because {hero.pronoun()} had noticed the clue first, the whole field was saved."
    )


def lesson(world: World, hero: Entity, crowd: Entity, action: Action) -> None:
    _increase_meme(crowd, "humility")
    _increase_meme(hero, "peace")
    world.say(
        f"Afterward, no one laughed. They learned that deaf ears can still belong to a wise friend, "
        f"and that every problem can have a different way in."
    )


# ---------------------------------------------------------------------------
# ASP twin + reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A hero is deaf if the registry marks them so.
deaf(hero(H)) :- hero(H), trait(H,deaf).

% A useful tool helps when it provides a visible or tactile signal.
helps(T, A) :- tool(T), action(A), aids(T, visible_signal), action_cue(A, visible).
helps(T, A) :- tool(T), action(A), aids(T, tactile_signal), action_cue(A, tactile).

% The twist is reasonable when the deaf hero can notice the tool without hearing.
reasonable_story(H, A, T) :- deaf(hero(H)), hero_has(H, T), helps(T, A).

% The lesson is learned when the crowd moves from mockery to respect.
lesson_learned(H) :- hero(H), disrespect(H), later_respect(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_cue", aid, "visible" if "visible" in a.tags else "tactile"))
        for t in sorted(a.tags):
            lines.append(asp.fact("action_tag", aid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.protects_from):
            lines.append(asp.fact("protects", tid, p))
        for x in sorted(t.aids):
            lines.append(asp.fact("aids", tid, x))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
        if h["deaf"]:
            lines.append(asp.fact("trait", hid, "deaf"))
        if h["tool"]:
            lines.append(asp.fact("hero_has", hid, h["tool"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    return len(asp.atoms(model, "reasonable_story")) > 0


def asp_verify() -> int:
    python_ok = any(
        is_reasonable_story(hero, action, tool)
        for hero in HEROES
        for action in ACTIONS
        for tool in TOOLS
    )
    asp_ok = asp_reasonable()
    if python_ok == asp_ok:
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print(f"MISMATCH: python={python_ok} asp={asp_ok}")
    return 1


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "field": Setting(place="the green field", mood="bright", affords={"signal", "run"}),
    "orchard": Setting(place="the old orchard", mood="golden", affords={"signal", "search"}),
    "brook": Setting(place="the little brook", mood="clear", affords={"signal", "cross"}),
}

ACTIONS = {
    "seek": Action(
        id="seek",
        verb="search for the lost lamb",
        gerund="searching for the lost lamb",
        cue="the path could be read by footprints and bright stones",
        twist="the danger was not where the crowd expected",
        lesson="kindness and attention can make up for what the ears cannot do",
        tags={"visible"},
    ),
    "signal": Action(
        id="signal",
        verb="signal the others",
        gerund="watching for signs",
        cue="a bright flag could be seen from far away",
        twist="the first good answer was a sign in the light",
        lesson="a clear sign can speak without a sound",
        tags={"visible"},
    ),
    "cross": Action(
        id="cross",
        verb="cross the brook",
        gerund="crossing carefully",
        cue="stones showed where each step should go",
        twist="the safe path was revealed by ripples and reeds",
        lesson="looking closely can keep everyone safe",
        tags={"tactile"},
    ),
}

TOOLS = {
    "flag": Tool(
        id="flag",
        label="a bright red flag",
        phrase="a bright red flag",
        protects_from=set(),
        aids={"visible_signal"},
    ),
    "bell": Tool(
        id="bell",
        label="a little bell",
        phrase="a little bell tied to a post",
        protects_from=set(),
        aids={"sound"},
    ),
    "staff": Tool(
        id="staff",
        label="a smooth walking staff",
        phrase="a smooth walking staff",
        protects_from=set(),
        aids={"tactile_signal"},
    ),
}

HEROES = {
    "Mara": {"deaf": True, "tool": "flag", "type": "rabbit"},
    "Niko": {"deaf": True, "tool": "staff", "type": "fox"},
    "Tavi": {"deaf": True, "tool": "flag", "type": "goat"},
}

CROWD = {"type": "animals"}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    hero: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_reasonable_story(hero_id: str, action_id: str, tool_id: str) -> bool:
    hero = HEROES[hero_id]
    action = ACTIONS[action_id]
    tool = TOOLS[tool_id]
    return hero["deaf"] and ((tool.aids & {"visible_signal", "tactile_signal"}) and True)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_info = HEROES[params.hero]
    hero = world.add(Entity(id=params.hero, kind="character", type=hero_info["type"], label=params.hero))
    crowd = world.add(Entity(id="crowd", kind="character", type="animals", label="the crowd"))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=TOOLS[hero_info["tool"]].label, phrase=TOOLS[hero_info["tool"]].phrase))
    action = ACTIONS[params.action]

    world.facts.update(hero=hero, crowd=crowd, tool=tool, action=action, setting=setting)

    introduce(world, hero)
    show_life(world, hero, action)
    mockery(world, hero, crowd)
    world.para()
    problem_arrives(world, hero, action)
    hint_of_twist(world, hero, tool)
    use_tool(world, hero, tool, action)
    rescue(world, hero, crowd, action)
    world.para()
    lesson(world, hero, crowd, action)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    action: Action = f["action"]  # type: ignore[assignment]
    tool: Entity = f["tool"]  # type: ignore[assignment]
    return [
        f"Write a short fable about a deaf {hero.type} who uses {tool.phrase} to help with {action.verb}.",
        f"Tell a gentle lesson-learned story where {hero.id} is deaf, there is a twist, and the ending shows respect.",
        f"Create a child-friendly fable in which a quiet sign matters more than a loud voice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    action: Action = f["action"]  # type: ignore[assignment]
    tool: Entity = f["tool"]  # type: ignore[assignment]
    crowd: Entity = f["crowd"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the fable about?",
            answer=f"The fable is about {hero.id}, a deaf {hero.type} who learns to use sight and signs wisely.",
        ),
        QAItem(
            question=f"What did {hero.id} do when the trouble began?",
            answer=f"{hero.id} noticed the problem first, picked up {tool.phrase}, and signaled the others to follow.",
        ),
        QAItem(
            question=f"What changed in the crowd by the end?",
            answer=f"The crowd stopped mocking {hero.id} and learned respect, because {hero.id} saved them with a clever sign.",
        ),
        QAItem(
            question=f"What is the lesson learned in this story?",
            answer=f"The lesson is that being deaf does not stop someone from being wise, helpful, and brave.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean if someone is deaf?",
            answer="If someone is deaf, they cannot hear sounds or hear them clearly, so they often use other clues like sight or touch.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        ),
        QAItem(
            question="Why can a flag be useful?",
            answer="A flag can be useful because it is easy to see from far away, so it can help people notice a signal without hearing a sound.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="field", action="seek", hero="Mara"),
    StoryParams(place="orchard", action="signal", hero="Niko"),
    StoryParams(place="brook", action="cross", hero="Tavi"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if args.action and args.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    hero = args.hero or rng.choice(list(HEROES))
    if not is_reasonable_story(hero, action, HEROES[hero]["tool"]):
        raise StoryError("The chosen combination does not support a reasonable deaf-fable twist.")
    if action not in SETTINGS[place].affords and place == "brook" and action == "seek":
        pass
    return StoryParams(place=place, action=action, hero=hero)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-style world about deafness, twist, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero", choices=HEROES)
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


def asp_valid_triples() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    triples = asp.atoms(model, "reasonable_story")
    return sorted(set(triples))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show reasonable_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
