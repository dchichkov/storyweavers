#!/usr/bin/env python3
"""
Standalone storyworld: Brighten the Forum Conflict.

A small superhero-style world in which a young hero wants to brighten a forum
for a community meeting, but a rival keeps blocking the plan until a clever,
safe compromise wins the day.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

HEROES = [
    "Nova",
    "Spark",
    "Comet",
    "Radiant",
    "Blaze",
    "Halo",
    "Pulse",
    "Lumen",
]
SIDEKICKS = [
    "Milo",
    "Tess",
    "Juno",
    "Aria",
    "Finn",
    "Pia",
    "Theo",
    "Nina",
]
RIVALS = [
    "Grim",
    "Shade",
    "Murk",
    "Rattle",
    "Gloom",
    "Snarl",
]
PLACES = [
    "the forum",
    "the city forum",
    "the community forum",
]
ACTIONS = [
    "brighten the forum",
    "brighten the room",
    "light up the forum",
]
TOOLS = [
    "a lantern drone",
    "a ribbon of warm lights",
    "a mirror kite",
    "a sun panel",
]
HELPERS = [
    "a helper cart",
    "a battery pack",
    "a silver ladder",
    "a safe switch",
]



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    rival: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    rival: str
    place: str
    action: str
    tool: str
    helper: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class World:
    hero: Entity
    sidekick: Entity
    rival: Entity
    place: str
    action: str
    tool: str
    helper: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def tell(params: StoryParams) -> World:
    hero = Entity(id=params.hero, kind="character", type="hero", label=params.hero)
    sidekick = Entity(id=params.sidekick, kind="character", type="sidekick", label=params.sidekick)
    rival = Entity(id=params.rival, kind="character", type="rival", label=params.rival)
    world = World(hero=hero, sidekick=sidekick, rival=rival, place=params.place,
                  action=params.action, tool=params.tool, helper=params.helper)

    hero.memes["hope"] = 1
    hero.memes["duty"] = 1
    rival.memes["grudge"] = 1
    rival.meters["blocking"] = 1
    sidekick.memes["trust"] = 1

    world.say(
        f"{hero.id} was a small superhero with a bright cape and a brave heart. "
        f"{hero.pronoun().capitalize()} liked helping people when the day felt dim."
    )
    world.say(
        f"One afternoon, {hero.id} and {sidekick.id} hurried to {world.place}. "
        f"They planned to {world.action} so the neighbors could meet in a cheerful glow."
    )
    world.say(
        f"{hero.id} brought {world.tool}, because a safe hero always used careful tools."
    )

    world.para()
    hero.memes["purpose"] += 1
    rival.memes["conflict"] += 1
    world.say(
        f"But {rival.id} stepped into the doorway and frowned. "
        f'“No bright ideas here,” {rival.pronoun()} muttered. “The forum stays dark.”'
    )
    world.say(
        f"{hero.id} felt the conflict pull tight in {hero.pronoun('possessive')} chest. "
        f"The forum needed light, but a loud argument would only scare the crowd."
    )
    world.say(
        f"{sidekick.id} pointed to {world.helper}. “We can still fix this without a fight,” "
        f"{sidekick.pronoun()} said."
    )

    world.para()
    sidekick.memes["calm"] += 1
    hero.memes["care"] += 1
    rival.meters["blocking"] = 0
    rival.memes["conflict"] = 0
    world.say(
        f"So {hero.id} set down {world.tool}, used {world.helper}, and invited {rival.id} "
        f"to help hold the lights above the seats."
    )
    world.say(
        f"The room began to brighten in a soft, friendly way. "
        f"People smiled, because the glow was warm and the path was clear."
    )
    world.say(
        f"At last, {rival.id} saw that the forum could shine without anyone getting hurt. "
        f"{hero.id} stood tall, and the whole forum looked ready for a hopeful meeting."
    )

    world.facts.update(
        hero=hero.id,
        sidekick=sidekick.id,
        rival=rival.id,
        place=world.place,
        action=world.action,
        tool=world.tool,
        helper=world.helper,
        conflict=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "brighten" and the word "forum".',
        f"Tell a gentle superhero story where {_safe_fact(world, f, "hero")} wants to {_safe_fact(world, f, "action")} at {_safe_fact(world, f, "place")} but {_safe_fact(world, f, "rival")} causes conflict, then they find a safe way forward.",
        f"Write a story about a brave hero, a forum, and a problem that gets solved with teamwork instead of a fight.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who wanted to {_safe_fact(world, f, "action")} at {_safe_fact(world, f, "place")}?",
            answer=f"{_safe_fact(world, f, "hero")} wanted to {_safe_fact(world, f, "action")} at {_safe_fact(world, f, "place")} so everyone could meet in a brighter, happier place.",
        ),
        QAItem(
            question=f"Who caused the conflict in the forum?",
            answer=f"{_safe_fact(world, f, "rival")} caused the conflict by blocking the doorway and saying the forum should stay dark.",
        ),
        QAItem(
            question=f"What helped the hero solve the problem without a fight?",
            answer=f"{_safe_fact(world, f, "helper")} helped because it let {_safe_fact(world, f, "hero")} and the others hold the lights safely and brighten the forum together.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the forum bright and calm, and {_safe_fact(world, f, "hero")} standing proudly after turning the argument into teamwork.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a forum?",
            answer="A forum is a place where people gather to talk, listen, and share ideas.",
        ),
        QAItem(
            question="What does brighten mean?",
            answer="To brighten means to make something lighter, clearer, or more cheerful.",
        ),
        QAItem(
            question="Why do heroes use careful tools?",
            answer="Heroes use careful tools so they can help safely and avoid hurting anyone or breaking things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in [world.hero, world.sidekick, world.rival]:
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"place={world.place}")
    lines.append(f"tool={world.tool}")
    lines.append(f"helper={world.helper}")
    lines.append(f"action={world.action}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld about brightening a forum.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
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
    return StoryParams(
        hero=getattr(args, "hero", None) or rng.choice(HEROES),
        sidekick=getattr(args, "sidekick", None) or rng.choice(SIDEKICKS),
        rival=getattr(args, "rival", None) or rng.choice(RIVALS),
        place=getattr(args, "place", None) or rng.choice(PLACES),
        action=getattr(args, "action", None) or rng.choice(ACTIONS),
        tool=getattr(args, "tool", None) or rng.choice(TOOLS),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
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


ASP_RULES = r"""
hero(X) :- hero_name(X).
sidekick(X) :- sidekick_name(X).
rival(X) :- rival_name(X).
place(X) :- place_name(X).
tool(X) :- tool_name(X).
helper(X) :- helper_name(X).

conflict_story(H,R,P) :- hero(H), rival(R), place(P).
brighten_goal(H,P) :- hero(H), place(P).
resolved_story(H,R,P) :- conflict_story(H,R,P), brighten_goal(H,P).
#show conflict_story/3.
#show resolved_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for h in HEROES:
        lines.append(asp.fact("hero_name", h))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick_name", s))
    for r in RIVALS:
        lines.append(asp.fact("rival_name", r))
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    for t in TOOLS:
        lines.append(asp.fact("tool_name", t))
    for h in HELPERS:
        lines.append(asp.fact("helper_name", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp  # type: ignore
    except Exception:
        import asp  # noqa: F401
    import asp as aspmod
    model = aspmod.one_model(asp_program("#show conflict_story/3.\n#show resolved_story/3."))
    atoms = {str(s) for s in model}
    if atoms:
        print("OK: ASP program grounded successfully.")
        return 0
    print("MISMATCH or empty ASP model.")
    return 1


def build_sample_list(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("Nova", "Milo", "Shade", "the forum", "brighten the forum", "a lantern drone", "a silver ladder"),
            StoryParams("Spark", "Tess", "Gloom", "the community forum", "light up the forum", "a ribbon of warm lights", "a safe switch"),
        ]
        return [generate(p) for p in curated]
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            i += 1
            continue
        seen.add(sample.story)
        samples.append(sample)
        i += 1
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show conflict_story/3.\n#show resolved_story/3."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        print(asp_program("#show conflict_story/3.\n#show resolved_story/3."))
        return

    samples = build_sample_list(args)
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
