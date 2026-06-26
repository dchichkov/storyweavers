#!/usr/bin/env python3
"""
A tall-tale story world about a goalie, a quest, a splice, cauliflower, and a
dialogue-driven repair.
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
    carried_by: Optional[str] = None
    damaged: bool = False
    fixed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    obstacle: str
    resolution: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    can_fix: set[str] = field(default_factory=set)
    can_cut: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def can_splice(quest: Quest, tool: Tool) -> bool:
    return "splice" in quest.tags and "splice" in tool.can_fix


def requires_cauliflower(quest: Quest) -> bool:
    return "cauliflower" in quest.tags


def predict_fix(world: World, hero_id: str, quest: Quest, tool_id: str) -> bool:
    sim = world.copy()
    hero = sim.get(hero_id)
    tool = sim.get(tool_id)
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    if can_splice(quest, Tool(tool.id, tool.label, tool.phrase, can_fix={"splice"}, can_cut=set())):
        return True
    return False


def setup_story(world: World, hero: Entity, goalie: Entity, quest: Quest, cauliflower: Entity) -> None:
    world.say(
        f"On the edge of a wind-whipped field, {hero.id} was a {hero.type} with a heart "
        f"big as a barn door and a grin that could outshine a lantern."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the grand old goalie, {goalie.id}, who could "
        f"stop a thunderball with one mitten and a wink."
    )
    world.say(
        f"Before the moon climbed high, there came a quest: the goalie's net had sprung a tear, "
        f"and the only way to mend it was to {quest.goal}."
    )
    world.say(
        f"That same day, a giant cauliflower rolled in from the market cart, as pale and proud "
        f"as a cloud that had forgotten how to rain."
    )


def dialogue_scene(world: World, hero: Entity, goalie: Entity, quest: Quest, cauliflower: Entity) -> None:
    world.para()
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    goalie.meters["tear"] = 1.0
    world.say(
        f'"Do we fix it now?" asked {hero.id}.'
    )
    world.say(
        f'"Aye," said {goalie.id}, "but a plain patch will not do. We must {quest.goal}, '
        f"and we must do it with a tool cleverer than a crow and kinder than a lullaby.""
    )
    world.say(
        f'"Could the cauliflower help?" {hero.id} asked, holding up the great white head.'
    )
    world.say(
        f'"Only if it can carry the stitch and keep the tear from running wild," said {goalie.id}, '
        f"twirling the broken cord like a mustache in the wind."
    )
    world.say(
        f'{hero.id} laughed so hard the scarecrow blushed.'
    )


def do_quest(world: World, hero: Entity, goalie: Entity, quest: Quest, cauliflower: Entity, tool: Entity) -> bool:
    world.para()
    if not requires_cauliflower(quest):
        raise StoryError("This quest must involve cauliflower to match the world seed.")
    hero.memes["determination"] = hero.memes.get("determination", 0.0) + 1
    world.say(
        f"So {hero.id} set off like a sparrow on a fence rail, carrying the cauliflower under "
        f"{hero.pronoun('possessive')} arm and the splice tool in the other hand."
    )
    world.say(
        f"The wind boomed, the grass bowed, and the broken net shivered as if it were trying to "
        f"remember how to be whole."
    )
    if not can_splice(quest, tool):
        world.say(
            f"But the tool was no good for a splice, so the tear stayed open like a mouth with no song."
        )
        return False
    world.say(
        f"{hero.id} pressed the cauliflower against the torn ropes and used the splice tool to thread "
        f"the fibers together, one brave loop at a time."
    )
    cauliflower.fixed = True
    goalie.fixed = True
    world.get(goalie.id).fixed = True
    world.get(goalie.id).meters["tear"] = 0.0
    world.get(goalie.id).memes["relief"] = 1.0
    world.get(hero.id).memes["pride"] = 1.0
    world.say(
        f"The splice held. The net sang. Even the moon, up in the rafters of the sky, seemed to lean closer."
    )
    return True


def ending(world: World, hero: Entity, goalie: Entity, quest: Quest, cauliflower: Entity, success: bool) -> None:
    world.para()
    if success:
        world.say(
            f'"You did it," said {goalie.id}. "You turned a cabbage-field problem into a champion\'s fix."'
        )
        world.say(
            f'{hero.id} bowed like a barnyard knight, and the cauliflower rode home in triumph, '
            f"still white as a winter tale and now famous for saving a goalie."
        )
    else:
        world.say(
            f'"We will try again at dawn," said {goalie.id}, and {hero.id} promised to return with a better splice.'
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "field": Place(name="the windy field", sky="open", affords={"quest", "dialogue"}),
    "meadow": Place(name="the moonlit meadow", sky="open", affords={"quest", "dialogue"}),
    "rink": Place(name="the old rink", sky="cold", affords={"quest", "dialogue"}),
}

QUESTS = {
    "cauliflower_splice": Quest(
        id="cauliflower_splice",
        goal="splice the torn goalie net",
        obstacle="a rip in the net that keeps widening",
        resolution="the net mends and holds",
        risk="the goalie cannot keep the goal safe",
        tags={"cauliflower", "splice", "goalie", "quest", "dialogue"},
    )
}

TOOLS = {
    "splice_tool": Tool(
        id="splice_tool",
        label="splice tool",
        phrase="a long needle made for mending rope",
        can_fix={"splice"},
        can_cut={"rope"},
    )
}

GIRL_NAMES = ["Mara", "Tess", "June", "Pippa", "Ivy"]
BOY_NAMES = ["Bram", "Otis", "Ned", "Finn", "Cal"]
TRAITS = ["bold", "bright-eyed", "nimble", "cheerful", "sturdy"]


@dataclass
class StoryParams:
    place: str = "field"
    quest: str = "cauliflower_splice"
    tool: str = "splice_tool"
    name: str = "Mara"
    gender: str = "girl"
    goalie_name: str = "Gus"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world: cauliflower, splice, goalie, quest, dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--goalie-name")
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    tool = args.tool or "splice_tool"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    goalie_name = args.goalie_name or rng.choice(["Gus", "Hank", "Bess", "Milo"])
    return StoryParams(place=place, quest=quest, tool=tool, name=name, gender=gender, goalie_name=goalie_name)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    goalie = world.add(Entity(id=params.goalie_name, kind="character", type="goalie"))
    cauliflower = world.add(Entity(id="cauliflower", kind="thing", type="cauliflower", label="cauliflower"))
    tool = world.add(Entity(id=params.tool, kind="thing", type="tool", label="splice tool", phrase=TOOLS[params.tool].phrase))
    quest = QUESTS[params.quest]

    setup_story(world, hero, goalie, quest, cauliflower)
    dialogue_scene(world, hero, goalie, quest, cauliflower)
    success = do_quest(world, hero, goalie, quest, cauliflower, tool)
    ending(world, hero, goalie, quest, cauliflower, success)

    world.facts = {"hero": hero, "goalie": goalie, "cauliflower": cauliflower, "tool": tool, "quest": quest, "success": success}
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a tall tale about a child who helps a goalie mend a torn net with a splice tool and a cauliflower.",
        f"Tell a dialogue-heavy quest story where {hero.id} and a goalie solve a rope problem with a cauliflower.",
        "Write a child-friendly tall tale that ends with a net mended by a splice and a hero praised for bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, goalie, quest, success = f["hero"], f["goalie"], f["quest"], f["success"]
    return [
        QAItem(
            question=f"Who went on the quest in the story?",
            answer=f"{hero.id} went on the quest to help {goalie.id} fix the torn goalie net.",
        ),
        QAItem(
            question=f"What problem did the goalie have?",
            answer=f"{goalie.id} had a torn net that needed a splice before the goal could stay safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The splice held, the net was fixed, and the cauliflower became part of the tale of the rescue.",
        ) if success else QAItem(
            question=f"How did the story end?",
            answer="The first try did not finish the repair, so the hero and goalie promised to try again with a better splice.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a goalie?",
            answer="A goalie is a player who guards the goal and tries to stop the ball or puck from getting in.",
        ),
        QAItem(
            question="What is a splice?",
            answer="A splice is a way of joining rope or cord together so the two ends become one strong piece.",
        ),
        QAItem(
            question="What is cauliflower?",
            answer="Cauliflower is a pale vegetable that grows in a round head made of little florets.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *sample.prompts, "", "== Story QA =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="field", quest="cauliflower_splice", tool="splice_tool", name="Mara", gender="girl", goalie_name="Gus"),
    StoryParams(place="meadow", quest="cauliflower_splice", tool="splice_tool", name="Bram", gender="boy", goalie_name="Hank"),
]


ASP_RULES = r"""
place(field).
place(meadow).
place(rink).

quest(cauliflower_splice).
tag(cauliflower_splice, cauliflower).
tag(cauliflower_splice, splice).
tag(cauliflower_splice, goalie).
tag(cauliflower_splice, quest).
tag(cauliflower_splice, dialogue).

tool(splice_tool).
can_fix(splice_tool, splice).

valid_story(P, Q, T) :- place(P), quest(Q), tool(T), tag(Q, splice), can_fix(T, splice).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for tag in sorted(q.tags):
            lines.append(asp.fact("tag", qid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fx in sorted(t.can_fix):
            lines.append(asp.fact("can_fix", tid, fx))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, q, t) for p in PLACES for q in QUESTS for t in TOOLS if can_splice(QUESTS[q], TOOLS[t])}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("Mismatch between clingo and Python gates.")
    print("clingo-only:", sorted(clingo_set - py_set))
    print("python-only:", sorted(py_set - clingo_set))
    return 1


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
        print(f"{len(combos)} compatible story combos")
        for row in combos:
            print(row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
