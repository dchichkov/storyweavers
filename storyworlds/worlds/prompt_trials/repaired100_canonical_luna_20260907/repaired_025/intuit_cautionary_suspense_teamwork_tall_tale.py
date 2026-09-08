#!/usr/bin/env python3
"""
A compact Tall Tale world about intuiting danger, careful teamwork, and a
cautionary rescue on a very tall bell tower.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    secure: bool = False


@dataclass
class Setting:
    place: str = "the tallest bell tower in the valley"
    affords: set[str] = field(default_factory=lambda: {"height", "wind", "bell", "rescue"})


@dataclass(frozen=True)
class Tale:
    id: str
    opening: str
    warning: str
    clue: str
    teamwork: str
    action: str
    resolution: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


TALES = [
    Tale(
        "thunder_rope",
        "In the valley stood a bell tower so tall that clouds sometimes mistook it for a mountain.",
        "One windy afternoon, the keeper's red kite snagged beside the giant bell, and the old rope began to fray.",
        "Luna felt the tower shiver before anyone else saw the crack in the upper rail.",
        "Mara tied a safety line around the lower post while Luna counted the bell's swinging breaths.",
        "Luna climbed only when Mara called, then hooked the kite loose with a shepherd's crook.",
        "The rope was saved, the kite came down, and the bell rang once to celebrate their careful work.",
        "From then on, every child in the valley checked a rope before pulling it, even if the rope looked brave.",
    ),
    Tale(
        "moon_ladder",
        "The tower rose above the roofs like a wooden road to the moon.",
        "A moon-painted weather vane spun loose at the very top while a gust pushed a ladder toward the edge.",
        "Luna intuited that the quietest gust was more dangerous than the loud ones because it pulled the ladder sideways.",
        "Mara planted both boots against the stair beam and passed up a short tether instead of sending Luna higher.",
        "Together they drew the ladder inward, then fastened the vane with a brass pin.",
        "The vane pointed safely at the moon, and the ladder rested flat against the tower.",
        "The town learned that a tall tale becomes a wise tale when nobody is too proud to use a tether.",
    ),
    Tale(
        "storm_basket",
        "At noon, the bell tower cast a shadow long enough to cover three gardens and a sleeping dog.",
        "A basket of messenger swallows broke loose near the top as storm clouds piled over the valley.",
        "Luna noticed that the basket swung in a rhythm just before each dangerous gust.",
        "Mara held the counter-rope while Luna waited for the calm beat and spoke each move aloud.",
        "They pulled the basket toward the inner ledge and closed its latch before the next gust.",
        "The swallows flew free under the eaves, and the storm passed without carrying anyone away.",
        "Afterward, the villagers called the basket enormous, but they called the teamwork even bigger.",
    ),
    Tale(
        "sunset_flag",
        "The tower's flag could be seen from villages that had never seen one another.",
        "A torn flag wrapped around the lightning rod as sunset wind climbed the tower.",
        "Luna intuited that tugging the cloth would make the metal rod sway.",
        "Mara lowered a loop from below while Luna waited beside the stair window for a safe angle.",
        "They loosened the cloth one fold at a time and never pulled against the rod.",
        "The flag floated down like a red river, and the lightning rod stood straight.",
        "The repaired flag flew the next morning, reminding everyone that caution can wave proudly.",
    ),
]

NAMES = ["Luna", "Mara", "Pip", "Tavi", "Nell"]
TRAITS = ["quick-eyed", "thoughtful", "steady", "curious", "careful"]


@dataclass
class StoryParams:
    hero: str
    trait: str
    teammate: str
    tale: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale world of intuition, caution, suspense, and teamwork.")
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--teammate", choices=NAMES)
    ap.add_argument("--tale", choices=[t.id for t in TALES])
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
    hero = args.hero or "Luna"
    teammate = args.teammate or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(
        hero=hero,
        trait=args.trait or rng.choice(TRAITS),
        teammate=teammate,
        tale=args.tale or rng.choice([t.id for t in TALES]),
    )


def tell(params: StoryParams) -> World:
    tale = next(t for t in TALES if t.id == params.tale)
    world = World(Setting())
    hero = world.add(Entity(
        params.hero, "character", "child", params.hero,
        meters={"height_reached": 0.0, "careful_moves": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "intuition": 0.0},
    ))
    teammate = world.add(Entity(
        params.teammate, "character", "teammate", params.teammate,
        meters={"rope_strength": 1.0},
        memes={"trust": 0.0, "focus": 0.0},
    ))
    rope = world.add(Entity("safety_rope", "thing", "rope", "the safety rope", secure=False))
    danger = world.add(Entity("tower_danger", "thing", "hazard", "the swaying tower rail", secure=False))
    world.facts.update(tale=tale, hero=hero, teammate=teammate, rope=rope, danger=danger)

    world.say(tale.opening)
    world.say(f"{params.hero}, a {params.trait} climber, had come to inspect the tower with {params.teammate}.")
    world.say(tale.warning)
    world.para()
    hero.memes["worry"] = 1.0
    hero.memes["intuition"] = 1.0
    world.say(f'"Wait," said {params.hero}. "I intuit that the tower is warning us."')
    world.say(f'"Then we listen before we climb," replied {params.teammate}.')
    world.say(tale.clue)
    world.say(tale.teamwork)
    teammate.memes["trust"] = 1.0
    teammate.memes["focus"] = 1.0
    rope.secure = True
    world.say(f"{params.teammate} secured {rope.label} before {params.hero} took one more step.")
    hero.meters["careful_moves"] += 1.0
    hero.meters["height_reached"] += 1.0
    hero.memes["courage"] = 1.0
    world.say(tale.action)
    world.fired.add("caution_used")
    world.fired.add("teamwork_used")
    world.para()
    danger.secure = True
    world.say(tale.resolution)
    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 2.0
    world.say(f"{params.hero} climbed down beside {params.teammate}, wiser than when the tall tale began.")
    world.say(tale.ending)
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    teammate: Entity = world.facts["teammate"]  # type: ignore[assignment]
    return [
        f"Write a Tall Tale about {hero.id} using intuition to notice danger in {world.setting.place}.",
        f"Show {hero.id} and {teammate.id} solving the suspenseful problem through caution and teamwork.",
        f"End with a clear lesson about why people should listen when they intuit that something is unsafe: {tale.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    teammate: Entity = world.facts["teammate"]  # type: ignore[assignment]
    return [
        QAItem(f"What danger did {hero.id} and {teammate.id} face?", tale.warning),
        QAItem(f"What did {hero.id} intuit?", tale.clue),
        QAItem(f"How did {teammate.id} help?", tale.teamwork),
        QAItem(f"How did the pair act cautiously?", f"{teammate.id} secured the safety rope before {hero.id} continued, and they moved only when the tower was safe."),
        QAItem("How did teamwork change the ending?", tale.resolution),
        QAItem("What lesson did the tall tale teach?", tale.ending),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean to intuit something?", "To intuit something means to sense or understand it quickly without needing every fact explained first."),
        QAItem("What does caution mean?", "Caution means taking care to avoid danger instead of rushing into a risky action."),
        QAItem("What is suspense?", "Suspense is the worried excitement people feel while waiting to learn what will happen."),
        QAItem("What is teamwork?", "Teamwork is when people share a task and help one another reach a goal."),
        QAItem("What is a tall tale?", "A tall tale is a story told with exaggerated size or adventure, often carrying a useful lesson."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:14} type={entity.type:10} meters={entity.meters} "
            f"memes={entity.memes} secure={entity.secure}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.teammate:
        raise StoryError("The hero and teammate must be different people so teamwork can occur.")
    if params.tale not in {t.id for t in TALES}:
        raise StoryError("That tale is not part of this small bell-tower world.")
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
valid_story(H, T, Tale) :-
    hero(H),
    teammate(T),
    tale(Tale),
    H != T,
    cautionary(Tale),
    suspenseful(Tale),
    teamwork(Tale).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", n) for n in NAMES]
    lines += [asp.fact("teammate", n) for n in NAMES]
    for tale in TALES:
        lines.append(asp.fact("tale", tale.id))
        lines.append(asp.fact("cautionary", tale.id))
        lines.append(asp.fact("suspenseful", tale.id))
        lines.append(asp.fact("teamwork", tale.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {
        (hero, teammate, tale.id)
        for hero in NAMES
        for teammate in NAMES
        if hero != teammate
        for tale in TALES
    }
    if actual == expected:
        print(f"OK: clingo gate matches python gate ({len(expected)} combinations).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in clingo:", sorted(actual - expected))
    print("only in python:", sorted(expected - actual))
    return 1


CURATED = [
    StoryParams("Luna", "quick-eyed", "Mara", "thunder_rope", 0),
    StoryParams("Luna", "thoughtful", "Pip", "moon_ladder", 1),
    StoryParams("Luna", "steady", "Tavi", "storm_basket", 2),
    StoryParams("Luna", "careful", "Nell", "sunset_flag", 3),
]


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(p) for p in CURATED]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for i in range(max(1, args.n)):
        params = resolve_params(args, random.Random(base + i))
        params.seed = base + i
        samples.append(generate(params))
    return samples


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
        print(f"{len(combos)} valid story combinations.")
        for combo in combos[:20]:
            print(combo)
        return

    samples = build_story_from_args(args)
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
