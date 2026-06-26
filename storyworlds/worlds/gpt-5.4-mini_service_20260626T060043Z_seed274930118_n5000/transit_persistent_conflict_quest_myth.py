#!/usr/bin/env python3
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
class StoryParams:
    bridge: str
    quest: str
    hero: str
    guide: str
    transit: str
    conflict: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    name: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Character:
    id: str
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Relic:
    id: str
    name: str
    kind: str = "relic"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    bridge: Place
    hero: Character
    guide: Character
    relic: Relic
    transit: str
    conflict: str
    quest: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    world_state: dict[str, float] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


BRIDGES = {
    "stone": "the Stone Bridge",
    "sky": "the Sky Road",
    "river": "the River Crossing",
    "gate": "the Old Gate",
}

QUESTS = {
    "star": "seek the lost star",
    "spring": "find the hidden spring",
    "torch": "return the moon-torch",
    "song": "carry back the first song",
}

TRANSITS = {
    "ferry": "take the ferry",
    "foot": "walk the long road",
    "horse": "ride the wind-horse",
    "boat": "cross by boat",
}

CONFLICTS = {
    "storm": "a storm that blocked the road",
    "shadow": "a shadow that would not pass",
    "river": "a river that rose each night",
    "tower": "a tower that kept its door shut",
}

HEROES = ["Ari", "Mira", "Solen", "Neris", "Tavi", "Liora"]
GUIDES = ["Old Hale", "Grandmother Iva", "the Lantern Keeper", "the River Singer"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic transit quest with persistent conflict.")
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--guide")
    ap.add_argument("--transit", choices=TRANSITS)
    ap.add_argument("--conflict", choices=CONFLICTS)
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


def _choose(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    bridge = args.bridge or _choose(rng, list(BRIDGES))
    quest = args.quest or _choose(rng, list(QUESTS))
    transit = args.transit or _choose(rng, list(TRANSITS))
    conflict = args.conflict or _choose(rng, list(CONFLICTS))
    hero = args.hero or _choose(rng, HEROES)
    guide = args.guide or _choose(rng, GUIDES)

    if bridge == "gate" and transit == "ferry":
        raise StoryError("The Old Gate does not suit a ferry crossing.")
    if quest == "song" and conflict == "tower":
        raise StoryError("The first song cannot be recovered while the tower keeps its door shut.")

    return StoryParams(
        bridge=bridge,
        quest=quest,
        hero=hero,
        guide=guide,
        transit=transit,
        conflict=conflict,
    )


def make_world(params: StoryParams) -> World:
    bridge = Place(id=params.bridge, name=BRIDGES[params.bridge], meters={"distance": 6.0}, memes={"memory": 1.0})
    hero = Character(id=params.hero, name=params.hero, role="hero", meters={"hope": 1.0}, memes={"resolve": 1.0})
    guide = Character(id=params.guide, name=params.guide, role="guide", meters={"age": 7.0}, memes={"patience": 2.0})
    relic = Relic(id=params.quest, name=QUESTS[params.quest], owner=hero.id, meters={"shine": 1.0}, memes={"call": 1.0})
    world = World(bridge=bridge, hero=hero, guide=guide, relic=relic, transit=params.transit, conflict=params.conflict, quest=params.quest)

    hero.meters["distance"] = 0.0
    hero.meters["weariness"] = 0.0
    hero.memes["doubt"] = 0.0
    guide.memes["calm"] = 1.0
    bridge.meters["bitter_wind"] = 1.0 if params.conflict in {"storm", "river"} else 0.5
    world.world_state["blocked"] = 1.0
    world.world_state["answered"] = 0.0
    world.world_state["returned"] = 0.0
    return world


def story_intro(world: World) -> None:
    world.say(f"In the old days, {world.hero.name} came to {world.bridge.name} with a quiet quest to {world.relic.name}.")
    world.say(f"{world.hero.name} was not alone, for {world.guide.name} had walked many roads and knew the speech of patient things.")


def story_conflict(world: World) -> None:
    world.para()
    world.say(f"But {CONFLICTS[world.facts['conflict_id']]} waited there, and it made the way hard to cross.")
    world.say(f"{world.hero.name} took the {TRANSITS[world.facts['transit_id']]} anyway, though the road dragged on and the hour grew heavy.")
    world.hero.meters["distance"] += 3.0
    world.hero.meters["weariness"] += 1.0
    world.hero.memes["doubt"] += 1.0
    world.world_state["blocked"] = 1.0


def story_persistence(world: World) -> None:
    world.say(f"Still, {world.hero.name} did not turn back, for the quest was persistent and would not leave the heart.")
    world.say(f"{world.guide.name} lifted a lamp and said the old lesson: a road can resist the feet, but not a vow.")
    world.hero.memes["resolve"] += 1.0
    world.guide.meters["light"] = 1.0
    world.world_state["blocked"] = 0.0


def story_resolution(world: World) -> None:
    world.para()
    world.say(f"At last {world.hero.name} crossed {world.bridge.name}, and the conflict softened as if it had heard a truer name.")
    world.say(f"{world.hero.name} found the lost star with tired hands and a steady breath, then carried it home like a ember in a bowl.")
    world.world_state["answered"] = 1.0
    world.world_state["returned"] = 1.0
    world.relic.owner = world.hero.id
    world.hero.meters["distance"] += 1.0
    world.hero.memes["joy"] = 1.0
    world.hero.memes["doubt"] = 0.0


def generate_story(world: World) -> None:
    world.facts["transit_id"] = world.transit
    world.facts["conflict_id"] = world.conflict
    world.facts["quest_id"] = world.quest
    story_intro(world)
    story_conflict(world)
    story_persistence(world)
    story_resolution(world)


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short myth about {world.hero.name} who must {TRANSITS[world.transit]} to {world.relic.name}.",
        f"Tell a child-friendly legend where {CONFLICTS[world.conflict]} delays a quest, but persistence wins.",
        f"Write a mythic story about a hero, a guide, and {world.bridge.name} with a gentle ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What did {world.hero.name} want to do at {world.bridge.name}?",
            answer=f"{world.hero.name} wanted to {world.relic.name}, which was the heart of the quest.",
        ),
        QAItem(
            question=f"Why was the journey hard for {world.hero.name}?",
            answer=f"The journey was hard because {CONFLICTS[world.conflict]} stood in the way and made the transit slow.",
        ),
        QAItem(
            question=f"How did {world.hero.name} keep going?",
            answer=f"{world.hero.name} kept going because the quest was persistent, and {world.guide.name} gave calm advice and light.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {world.hero.name} crossed {world.bridge.name}, found the lost {world.relic.name}, and brought it home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is transit?",
            answer="Transit means traveling from one place to another, like walking, riding, or sailing across a road or river.",
        ),
        QAItem(
            question="What does persistent mean?",
            answer="Persistent means keeping on even when something is hard or slow.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a purpose, where someone travels to find, deliver, or rescue something important.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or struggle that makes the hero work hard before things can be put right.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story that uses wonder, travel, and big symbols to explain brave things in the world.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for obj in [world.bridge, world.hero, world.guide, world.relic]:
        lines.append(
            f"  {obj.id:10} meters={dict(obj.meters)} memes={dict(obj.memes)}"
        )
    lines.append(f"  state={dict(world.world_state)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(hero).
guide(guide).
quest(quest).
transit(transit).
conflict(conflict).

persistent(quest).
mythic(quest).

reachable(B) :- bridge(B).
hard(B) :- conflict(conflict), bridge(B).

resolves(B) :- bridge(B), persistent(quest), transit(transit).
valid_story(B,Q,T,C) :- bridge(B), quest(Q), transit(T), conflict(C), persistent(Q), mythic(Q).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("bridge", k) for k in BRIDGES
    ]
    lines += [asp.fact("quest", k) for k in QUESTS]
    lines += [asp.fact("transit", k) for k in TRANSITS]
    lines += [asp.fact("conflict", k) for k in CONFLICTS]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = set(asp.atoms(model, "valid_story"))
    python = {(b, q, t, c) for b in BRIDGES for q in QUESTS for t in TRANSITS for c in CONFLICTS if not (b == "gate" and t == "ferry") and not (q == "song" and c == "tower")}
    if atoms == python:
        print(f"OK: clingo gate matches Python gate ({len(atoms)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def resolve_story(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return resolve_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def curated() -> list[StoryParams]:
    return [
        StoryParams(bridge="stone", quest="star", hero="Ari", guide="Old Hale", transit="foot", conflict="storm"),
        StoryParams(bridge="river", quest="spring", hero="Mira", guide="Grandmother Iva", transit="boat", conflict="river"),
        StoryParams(bridge="sky", quest="torch", hero="Solen", guide="the Lantern Keeper", transit="horse", conflict="shadow"),
        StoryParams(bridge="gate", quest="song", hero="Neris", guide="the River Singer", transit="foot", conflict="tower"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible mythic stories:\n")
        for s in stories:
            print("  ", s)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen = set()
        for i in range(max(args.n, 1) * 50):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.hero} | {p.quest} | {p.bridge}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
