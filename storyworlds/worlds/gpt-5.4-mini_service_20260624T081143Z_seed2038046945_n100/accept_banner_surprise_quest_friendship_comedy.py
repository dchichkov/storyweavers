#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/accept_banner_surprise_quest_friendship_comedy.py
============================================================================================================

A tiny comedy storyworld about a surprising quest, a friendship choice, and a
banner that turns out to be more useful than anyone expected.

Premise:
- A child-like character wants to complete a small quest.
- A friend worries that the quest plan is too plain and wants a surprise.
- The group accepts a funny compromise involving a banner.
- The ending image proves the change: the quest is completed, the banner helps,
  and friendship becomes the winning punchline.

This file is standalone and uses only the Python stdlib plus the shared
storyworld result containers.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str]


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    surprise: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Banner:
    id: str
    label: str
    phrase: str
    helps: set[str]
    opens: set[str]
    prep: str
    payoff: str
    plural: bool = False


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


def _default_meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _default_meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def quest_risk(task: Task) -> bool:
    return task.mess in {"sticky", "muddy", "painted"}


def choose_banner(task: Task, banner: Banner) -> bool:
    return task.mess in banner.helps and task.id in banner.opens


def valid_combo(task: Task, banner: Banner) -> bool:
    return quest_risk(task) and choose_banner(task, banner)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for t in TASKS.values():
        for b in BANNERS.values():
            if valid_combo(t, b):
                combos.append((t.id, b.id))
    return combos


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    hero.meters[task.mess] = _default_meter(hero, task.mess) + 1
    hero.memes["energy"] = _default_meme(hero, "energy") + 1
    if narrate:
        world.say(f"{hero.id} started to {task.verb}, and the day got busier at once.")


def predict_funny_mess(world: World, hero: Entity, task: Task) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    _do_task(sim, sim.get(hero.id), task, narrate=False)
    return {
        "messy": _default_meter(sim.get(hero.id), task.mess) >= THRESHOLD,
        "energy": _default_meme(sim.get(hero.id), "energy"),
    }


def banner_effect(world: World, hero: Entity, banner: Banner) -> None:
    banner_ent = world.add(Entity(
        id=banner.id,
        type="banner",
        label=banner.label,
        phrase=banner.phrase,
        owner=hero.id,
        plural=banner.plural,
    ))
    banner_ent.worn_by = hero.id
    hero.memes["pride"] = _default_meme(hero, "pride") + 1
    world.say(
        f"They hung up {banner.phrase}, and suddenly the whole place looked like it was clapping."
    )


def tell(world: World, hero: Entity, friend: Entity, task: Task, banner: Banner) -> None:
    world.say(
        f"{hero.id} was a lively {hero.type} who loved tiny adventures and big jokes."
    )
    world.say(
        f"{friend.id} was {friend.pronoun('subject')} best friend, and together they liked "
        f"to find small quests that felt important."
    )
    world.say(
        f"One day, {hero.id} wanted to {task.verb}, because {task.surprise} sounded far too funny to ignore."
    )
    world.para()
    world.say(
        f"But {friend.id} had a surprise of {friend.pronoun('possessive')} own: "
        f"{task.risk} would make the quest a sticky comedy."
    )
    prediction = predict_funny_mess(world, hero, task)
    if not prediction["messy"]:
        raise StoryError("This task is not risky enough to build a real comedy problem.")
    world.say(
        f"\"We should {task.rush},\" said {friend.id}, \"but only after we think of a clever banner.\""
    )
    hero.memes["curiosity"] = _default_meme(hero, "curiosity") + 1
    world.say(
        f"{hero.id} blinked, then laughed. \"I accept the banner plan,\" {hero.pronoun('subject')} said."
    )
    world.say(
        f"That was the kind of quest only friends could make sound normal."
    )
    world.para()
    banner_effect(world, hero, banner)
    hero.memes["joy"] = _default_meme(hero, "joy") + 1
    friend.memes["joy"] = _default_meme(friend, "joy") + 1
    hero.meters[task.mess] = 0.0
    world.say(
        f"With {banner.label} in place, {hero.id} could {task.verb} without turning the day into a mess."
    )
    world.say(
        f"{hero.id} and {friend.id} finished the quest together, and even the banner seemed to grin."
    )
    world.facts.update(hero=hero, friend=friend, task=task, banner=banner, resolved=True)


SETTINGS = {
    "town_square": Setting(place="the town square", affords={"parade", "quest"}),
    "garden_gate": Setting(place="the garden gate", affords={"quest", "gather"}),
    "clubhouse": Setting(place="the clubhouse", affords={"quest", "decorate"}),
}

TASKS = {
    "quest": Task(
        id="quest",
        verb="search for the missing kite key",
        gerund="searching for the missing kite key",
        rush="dash to the fountain and check under the bench",
        surprise="it promised one tiny surprise after another",
        mess="sticky",
        risk="the glue on the map would get all over their hands",
        tags={"quest", "surprise"},
    ),
    "parade": Task(
        id="parade",
        verb="lead the paper parade",
        gerund="leading the paper parade",
        rush="run ahead while waving the signs",
        surprise="the parade wanted a silly little wow",
        mess="painted",
        risk="the paint on the banners would smear everywhere",
        tags={"banner", "comedy"},
    ),
    "gather": Task(
        id="gather",
        verb="gather the lost marbles",
        gerund="gathering the lost marbles",
        rush="crawl under the table and count them twice",
        surprise="the marble jar kept wiggling like it knew a joke",
        mess="muddy",
        risk="their knees would get muddy in the grass",
        tags={"friendship", "surprise"},
    ),
}

BANNERS = {
    "cheer_banner": Banner(
        id="cheer_banner",
        label="cheer banner",
        phrase="a bright cheer banner",
        helps={"sticky", "muddy"},
        opens={"quest", "gather"},
        prep="hang up the cheer banner first",
        payoff="the banner fluttered like it was telling the joke for them",
    ),
    "silly_banner": Banner(
        id="silly_banner",
        label="silly banner",
        phrase="a big silly banner",
        helps={"painted", "sticky"},
        opens={"parade", "quest"},
        prep="unfurl the silly banner at once",
        payoff="the banner made the whole plan look delightfully official",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Nia", "Finn", "Lia", "Omar"]
FRIEND_NAMES = ["Pip", "Momo", "Juno", "Bea", "Rex", "Tia"]


@dataclass
class StoryParams:
    place: str
    task: str
    banner: str
    name: str
    friend: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for bid, b in BANNERS.items():
        lines.append(asp.fact("banner", bid))
        lines.append(asp.fact("helps", bid, *sorted(b.helps)) if False else "")
        for m in sorted(b.helps):
            lines.append(asp.fact("helps", bid, m))
        for o in sorted(b.opens):
            lines.append(asp.fact("opens", bid, o))
    return "\n".join(x for x in lines if x)


ASP_RULES = r"""
valid(T,B) :- task(T), banner(B), mess_of(T,M), helps(B,M), opens(B,T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a surprising quest and a banner.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--banner", choices=BANNERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.task and args.banner and not valid_combo(TASKS[args.task], BANNERS[args.banner]):
        raise StoryError("That banner does not really solve this quest in a funny way.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.banner:
        combos = [c for c in combos if c[2] == args.banner]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    _, task, banner = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    return StoryParams(place=args.place or rng.choice(list(SETTINGS)), task=task, banner=banner, name=name, friend=friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    banner = f["banner"]
    return [
        f"Write a funny short story about a child who wants to {task.verb} and a friend who suggests {banner.label}.",
        f"Tell a comedy story with a surprise quest, a friendship choice, and the words accept and banner.",
        f"Make a small children's story where {f['hero'].id} and {f['friend'].id} solve a quest by using a banner.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, task, banner = f["hero"], f["friend"], f["task"], f["banner"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What plan did {friend.id} suggest before the quest got funny?",
            answer=f"{friend.id} suggested using {banner.phrase} and accepting the banner plan.",
        ),
        QAItem(
            question=f"How did the friends finish the story?",
            answer=f"They accepted the banner idea, completed the quest, and laughed together at the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banner?",
            answer="A banner is a long piece of cloth or paper with a message, picture, or decoration on it.",
        ),
        QAItem(
            question="What does accept mean?",
            answer="To accept something means to agree to it or say yes to it.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small search or adventure to find something or finish a job.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means being kind, helpful, and happy to spend time with a friend.",
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Nia", "Lia"} else "boy"))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl" if params.friend in {"Bea", "Tia"} else "boy"))
    task = TASKS[params.task]
    banner = BANNERS[params.banner]
    tell(world, hero, friend, task, banner)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="garden_gate", task="quest", banner="cheer_banner", name="Mina", friend="Pip"),
    StoryParams(place="clubhouse", task="parade", banner="silly_banner", name="Toby", friend="Bea"),
    StoryParams(place="garden_gate", task="gather", banner="cheer_banner", name="Nia", friend="Juno"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(python_set - asp_set))
    print("only asp:", sorted(asp_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
