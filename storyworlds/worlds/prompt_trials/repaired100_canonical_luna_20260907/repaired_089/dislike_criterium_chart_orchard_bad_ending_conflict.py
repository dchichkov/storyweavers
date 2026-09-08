#!/usr/bin/env python3
"""
Storyworld: dislike_criterium_chart_orchard_bad_ending_conflict

A small orchard myth about dislike, a fair criterium chart, conflict, and
reconciliation after a tempting bad ending is avoided.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"conflict": 0.0, "fairness": 0.0, "trust": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"dislike": 0.0, "anger": 0.0, "relief": 0.0, "pride": 0.0})


@dataclass
class OrchardThing:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"value": 0.0, "risk": 0.0})


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    orchard: str
    fruit: str
    criterium: str
    chart: str
    myth_mode: str = "moonlit"
    seed: Optional[int] = None


ORCHARDS = [
    "the Hill of Seven Apple Trees",
    "the orchard beside the old well",
    "the valley orchard",
    "the orchard of silver leaves",
]

FRUITS = [
    "a golden pear",
    "a red moon-apple",
    "a blue plum",
    "a honey-colored quince",
]

HERO_NAMES = ["Luna", "Mira", "Tavi", "Neri"]
FRIEND_NAMES = ["Pax", "Orin", "Sela", "Bram"]

CRITERIA = [
    "brightest color, sweetest scent, and kindest sharing",
    "ripeness, careful picking, and generous giving",
    "beauty, taste, and care for the tree",
    "freshness, fragrance, and what the fruit could teach",
]

CHARTS = [
    "a bark chart marked with three stars",
    "a leaf chart painted in berry juice",
    "a moon-white chart tied to an ash branch",
    "a woven chart with one row for each fair test",
]

MYTH_MODES = ("moonlit", "dawn", "old-song", "storm", "harvest")

TALES = [
    {
        "omen": "the oldest tree opened one silver blossom in the shape of a small crown",
        "temptation": "tear the crown away and hide it so the other children could not win",
        "dislike": "Luna disliked the way the contest made every good fruit feel like a rival",
        "bad_ending": "If the crown were stolen, the orchard would close its roots and bear bitter fruit for every family",
        "clue": "the crown's shadow pointed to three unpicked fruits, not to the largest one",
        "repair": "read the chart aloud, tested each fruit by the same criterium, and invited the other pickers to taste together",
        "result": "the crown melted into three drops of light, one for each tree that had been cared for",
        "lesson": "a fair measure can turn rivalry into a path home",
        "ending": "At sunset, three trees glowed softly, and no child carried the crown alone",
    },
    {
        "omen": "a fox-shaped cloud rested above the orchard gate without moving",
        "temptation": "declare one perfect fruit before anyone else could inspect it",
        "dislike": "Luna disliked the whisper that only a single winner mattered",
        "bad_ending": "A hasty choice would send the fox-cloud down as a storm and wash the orchard's roots bare",
        "clue": "raindrops on the chart gathered beside the words about sharing",
        "repair": "asked the growers to judge the fruits by the same three marks and added a sharing row to the chart",
        "result": "the fox-cloud opened its eyes, saw the fair table, and became a silver breeze",
        "lesson": "a contest becomes wise when its rules leave room for everyone",
        "ending": "The silver breeze carried the shared scent of fruit over every tree",
    },
    {
        "omen": "a small stone bell rang whenever someone spoke an unkind judgment",
        "temptation": "hide the chart and tell the judges that a disliked rival had failed",
        "dislike": "Luna disliked Sela's boast, but disliked lying even more",
        "bad_ending": "A false score would make the bell crack and wake the thorn spirit beneath the roots",
        "clue": "the bell stayed quiet when Sela admitted that her fruit needed another day",
        "repair": "told the truth, let Sela revise her entry, and used the chart to compare work rather than people",
        "result": "the thorn spirit slept while the bell became a clear singing note",
        "lesson": "reconciliation begins when truth is safer than winning",
        "ending": "Sela and Luna hung the singing bell together beneath the oldest branch",
    },
    {
        "omen": "three bees drew a shining circle around the fairest basket",
        "temptation": "push a friend's basket outside the circle and call it an accident",
        "dislike": "Luna disliked the friend's boast and felt a hot wish to make the boast disappear",
        "bad_ending": "The bees would seal the orchard gate if the circle were broken by spite",
        "clue": "the bees visited baskets in the order the trees had been watered",
        "repair": "checked the watering marks, apologized for the shove, and asked the friend to help count the bees' pattern",
        "result": "the bees widened the circle until every cared-for basket stood inside",
        "lesson": "repairing harm can make a boundary wide enough for friendship",
        "ending": "The orchard gate opened, and bees hummed above two baskets set side by side",
    },
]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.characters: dict[str, Character] = {}
        self.things: dict[str, OrchardThing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def build_world(params: StoryParams) -> World:
    if params.hero_name == params.friend_name:
        raise StoryError("hero and friend must have different names")
    if params.criterium not in CRITERIA:
        raise StoryError("unknown criterium")
    if params.chart not in CHARTS:
        raise StoryError("unknown chart")

    tale = random.Random(params.seed or 0).choice(TALES)
    world = World(params)
    hero = Character("hero", params.hero_name, "child", "chart keeper")
    friend = Character("friend", params.friend_name, "child", "fruit picker")
    chart = OrchardThing("chart", params.chart, "fairness tool", params.hero_name)
    fruit = OrchardThing("fruit", params.fruit, "contest fruit")
    tree = OrchardThing("tree", "the oldest orchard tree", "mythic tree")

    world.characters[hero.id] = hero
    world.characters[friend.id] = friend
    world.things[chart.id] = chart
    world.things[fruit.id] = fruit
    world.things[tree.id] = tree

    openings = {
        "moonlit": f"Under a moon as round as a silver coin, {params.hero_name} entered {params.orchard}.",
        "dawn": f"At dawn, when dew jeweled every blade of grass, {params.hero_name} entered {params.orchard}.",
        "old-song": f"An old song says that {params.hero_name} entered {params.orchard} when the trees began to whisper.",
        "storm": f"Before a storm crossed the hills, {params.hero_name} hurried into {params.orchard}.",
        "harvest": f"On harvest day, {params.hero_name} carried an empty basket into {params.orchard}.",
    }
    world.say(openings[params.myth_mode])
    world.say(f"There the oldest tree showed {tale['omen']}. The village had chosen {params.hero_name} and {params.friend_name} to judge {params.fruit} by the criterium of {params.criterium}.")
    world.say(f"Beside the weighing stone lay {params.chart}, ready to record what was true rather than what anyone merely wished.")
    world.para()

    hero.meters["conflict"] += 1
    hero.memes["dislike"] += 1
    friend.meters["conflict"] += 1
    world.say(f"{tale['dislike']}. {params.hero_name} looked at {params.friend_name}, who was polishing a fruit as if it already wore a crown.")
    world.say(f'"The chart is mine to keep," {params.hero_name} said. "{params.friend_name}, do not change the marks."')
    world.say(f'"And the winner is mine to become," {params.friend_name} answered. "Why should your dislike decide my worth?"')
    world.say(f"Their conflict grew beneath the branches, and {params.hero_name}'s first temptation was to {tale['temptation']}.")
    world.say(f"If that happened, {tale['bad_ending']}.")
    hero.meters["conflict"] += 1
    hero.memes["anger"] += 1
    friend.memes["anger"] += 1
    world.para()

    world.say(f"Then the old tree shook one leaf onto the ground. Its vein pointed to a clue: {tale['clue']}.")
    world.say(f'"I do dislike how this contest makes us fight," {params.hero_name} admitted. "But I do not want a bad ending for you or for the orchard."')
    world.say(f'"I dislike being treated like a rival more than a friend," {params.friend_name} replied. "Will you let me help make the test fair?"')
    world.say(f"{params.hero_name} lowered the chart. Together they {tale['repair']}.")
    hero.meters["fairness"] += 2
    friend.meters["fairness"] += 2
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.para()

    world.say(f"The orchard listened. {tale['result']}.")
    world.say(f"{params.hero_name} erased the spiteful mark, and {params.friend_name} placed a fresh mark beside it. They compared the fruit, not each other's hearts.")
    world.say(f'"I am sorry I wanted to win by hiding the truth," {params.hero_name} said.')
    world.say(f'"And I am sorry I made winning sound more important than friendship," {params.friend_name} said.')
    world.say(f"Their reconciliation warmed the roots. {params.hero_name} learned that {tale['lesson']}.")
    hero.meters["trust"] += 2
    friend.meters["trust"] += 2
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(f"{tale['ending']}.")
    world.facts.update(
        hero=hero,
        friend=friend,
        chart=chart,
        fruit=fruit,
        tree=tree,
        omen=tale["omen"],
        temptation=tale["temptation"],
        dislike=tale["dislike"],
        bad_ending=tale["bad_ending"],
        clue=tale["clue"],
        repair=tale["repair"],
        result=tale["result"],
        lesson=tale["lesson"],
        ending=tale["ending"],
        orchard=params.orchard,
        criterium=params.criterium,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    return [
        f"Write a myth-like orchard story about {hero.name} and {friend.name}, whose dislike causes conflict during a fruit criterium.",
        f"Tell a story in which {hero.name} uses {f['chart'].label} to judge {f['fruit'].label} fairly and avoid a bad ending.",
        f"Write a reconciliation tale where two orchard children speak honestly, repair their conflict, and learn that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    chart: OrchardThing = f["chart"]
    fruit: OrchardThing = f["fruit"]
    return [
        QAItem(
            question=f"Why did {hero.name} and {friend.name} begin to conflict?",
            answer=f"They began to conflict because {f['dislike']}. Their disagreement grew when the fruit contest seemed to make one child a winner and the other a rival.",
        ),
        QAItem(
            question=f"What bad ending did the orchard warn them about?",
            answer=f"The orchard warned that {f['bad_ending']}. This made their selfish plan dangerous for everyone, not just unfair to one friend.",
        ),
        QAItem(
            question=f"How did the chart help settle the criterium?",
            answer=f"The children used {chart.label} to {f['repair']}. The chart gave them shared evidence instead of letting dislike choose the result.",
        ),
        QAItem(
            question=f"How did the reconciliation happen?",
            answer=f"{hero.name} and {friend.name} admitted what they had done, apologized, and worked together. Their honest words led to this result: {f['result']}.",
        ),
        QAItem(
            question="What final image proves that the orchard was healed?",
            answer=f"The final image is this: {f['ending']}. It shows that the conflict ended in shared care rather than victory over a friend.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a criterium?",
            answer="A criterium is a set of standards or tests used to judge something fairly.",
        ),
        QAItem(
            question="What is a chart?",
            answer="A chart is an organized display that records information so people can compare facts clearly.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the making of peace after a conflict, usually through truth, apology, and changed actions.",
        ),
        QAItem(
            question="What does dislike mean?",
            answer="Dislike means not enjoying or not approving of someone or something, though it does not have to become cruelty.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.id}: name={character.name} role={character.role} "
            f"meters={dict(character.meters)} memes={dict(character.memes)}"
        )
    for thing in world.things.values():
        lines.append(f"{thing.id}: label={thing.label} kind={thing.kind} meters={dict(thing.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
peaceful_myth(S) :- story(S), has_dislike(S), has_conflict(S), fair_chart(S), reconciliation(S), avoids_bad_ending(S).
has_dislike(S) :- story(S), dislike_present(S).
has_conflict(S) :- story(S), conflict_present(S).
fair_chart(S) :- story(S), chart_used(S), criterium_used(S).
reconciliation(S) :- story(S), apology(S), shared_work(S).
avoids_bad_ending(S) :- story(S), truthful_choice(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp
    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("dislike_present", "s1"),
            asp.fact("conflict_present", "s1"),
            asp.fact("chart_used", "s1"),
            asp.fact("criterium_used", "s1"),
            asp.fact("apology", "s1"),
            asp.fact("shared_work", "s1"),
            asp.fact("truthful_choice", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        hero_name="Luna",
        friend_name="Pax",
        orchard="the valley orchard",
        fruit="a golden pear",
        criterium=CRITERIA[0],
        chart=CHARTS[0],
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show peaceful_myth/1.\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "peaceful_myth"))
    if found == {("s1",)}:
        print("OK: ASP gate matches the orchard reconciliation pattern.")
        return 0
    print("MISMATCH: ASP did not recognize the orchard myth.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Myth-like orchard world of dislike, a criterium chart, conflict, and reconciliation.")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--orchard", choices=ORCHARDS)
    parser.add_argument("--fruit", choices=FRUITS)
    parser.add_argument("--criterium", choices=CRITERIA)
    parser.add_argument("--chart", choices=CHARTS)
    parser.add_argument("--myth-mode", choices=MYTH_MODES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([name for name in FRIEND_NAMES if name != hero_name])
    return StoryParams(
        hero_name=hero_name,
        friend_name=friend_name,
        orchard=args.orchard or rng.choice(ORCHARDS),
        fruit=args.fruit or rng.choice(FRUITS),
        criterium=args.criterium or rng.choice(CRITERIA),
        chart=args.chart or rng.choice(CHARTS),
        myth_mode=args.myth_mode or rng.choice(MYTH_MODES),
    )


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


CURATED = [
    StoryParams(
        hero_name="Luna",
        friend_name="Pax",
        orchard="the orchard of silver leaves",
        fruit="a red moon-apple",
        criterium=CRITERIA[0],
        chart=CHARTS[2],
        myth_mode="moonlit",
    ),
    StoryParams(
        hero_name="Mira",
        friend_name="Orin",
        orchard="the valley orchard",
        fruit="a golden pear",
        criterium=CRITERIA[1],
        chart=CHARTS[1],
        myth_mode="dawn",
    ),
    StoryParams(
        hero_name="Tavi",
        friend_name="Sela",
        orchard="the orchard beside the old well",
        fruit="a blue plum",
        criterium=CRITERIA[2],
        chart=CHARTS[0],
        myth_mode="old-song",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
