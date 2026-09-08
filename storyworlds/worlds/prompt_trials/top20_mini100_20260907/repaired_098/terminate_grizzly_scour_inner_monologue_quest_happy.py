#!/usr/bin/env python3
"""A small superhero storyworld about a quest, a grizzly menace, and a hero's choice."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Hero:
    name: str
    alias: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    name: str
    kind: str = "city"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class QuestState:
    target: str
    need: str
    hazard: str
    solution: str
    done: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    setting_name: str = "Harbor City"
    hero_name: str = "Nova"
    hero_alias: str = "Star Shield"
    sidekick_name: str = "Bean"
    sidekick_alias: str = "Comet"
    grizzly_name: str = "Grizzla"
    quest_target: str = "the moon key"
    quest_need: str = "the city vault cannot open without it"
    quest_hazard: str = "a grizzly has been ransacking the museum steps"
    quest_solution: str = "the key is hidden in the old bell tower"
    route: str = "inner_monologue_first"
    tone: str = "bright"


@dataclass(frozen=True)
class QuestCase:
    setup: str
    worry: str
    first_action: str
    failed_reason: str
    clue: str
    cause: str
    brave_move: str
    fix: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    hero: Hero
    sidekick: Hero
    grizzly: Hero
    quest: QuestState
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "Harbor City": Setting(name="Harbor City"),
    "Sunrise Bay": Setting(name="Sunrise Bay"),
    "Metro Heights": Setting(name="Metro Heights"),
}

HEROES = [
    ("Nova", "Star Shield"),
    ("Iris", "Pulse Arrow"),
    ("Jett", "Night Lantern"),
    ("Mina", "Sky Spark"),
]

SIDEKICKS = [
    ("Bean", "Comet"),
    ("Tobi", "Zip"),
    ("Lina", "Glow"),
    ("Pip", "Ray"),
]

GRIZZLIES = [
    ("Grizzla", "grizzly"),
    ("Bruno", "grizzly"),
    ("Tundra", "grizzly"),
]

CASES = {
    "museum_steps": QuestCase(
        setup="the museum steps were being torn up by a grizzly's heavy paws",
        worry="the front doors could be damaged before the night gala",
        first_action="scouted the steps from a rooftop and watched the grizzly's path",
        failed_reason="the grizzly only chased a cart of fish crackers and never touched the doors",
        clue="crumbs led away from the steps and into the bell tower alley",
        cause="the grizzly wanted the fish smell from a stuck delivery basket",
        brave_move="spoke softly, lowered the basket with a rope, and kept the grizzly calm",
        fix="moved the basket, sealed the cracked fish crate, and guided the grizzly back to the park",
        lesson="hero work is not just stopping danger; it is understanding what the fear is reaching for",
        ending="the museum lights shone cleanly on quiet steps while the happy gala began",
    ),
    "river_bridge": QuestCase(
        setup="the river bridge kept shaking whenever the grizzly thundered nearby",
        worry="delivery bikes could slip into the water",
        first_action="checked the bridge bolts with a flashlight while the sidekick held the line",
        failed_reason="the bolts were tight, so the shaking was not from broken metal",
        clue="muddy paw prints stopped at a popcorn cart under the bridge",
        cause="the grizzly was following the sweet smell of caramel corn",
        brave_move="stood between the cart and the road and offered the grizzly an empty lunch pail",
        fix="cleared the cart, opened the park path, and sent the grizzly toward the berry grove",
        lesson="a quest can begin with danger and end with kindness when the real need is found",
        ending="the bridge settled still beneath a gold sunset and every bike rolled home safely",
    ),
    "library_roof": QuestCase(
        setup="the library roof had started to groan in the middle of rain",
        worry="the newest comics could get soaked",
        first_action="climbed to the safe ladder platform and checked the roof seam",
        failed_reason="the seam was dry, so the groan came from somewhere else",
        clue="a torn kite string was snagged on the roof vent",
        cause="wind had pulled a kite into the vent and made it tap like a drum",
        brave_move="called to the grizzly below to keep still while the hero cut the string from the platform",
        fix="freed the vent, patched the loose gutter, and stored the comics in dry bins",
        lesson="sometimes the loudest alarm is only a trapped thing asking to be noticed",
        ending="rain faded over a dry library and the comics waited like treasure on the shelves",
    ),
    "tram_tunnel": QuestCase(
        setup="the tram tunnel was dark because a grizzly had blocked the light gate",
        worry="riders needed a safe way through before dinner",
        first_action="flashed a lamp along the tunnel wall and measured the shadow",
        failed_reason="the gate was fine; the shadow came from a stacked sign cart",
        clue="the cart wheel had rolled over a trail of spilled berry jam",
        cause="the grizzly had followed jam jars from a dropped delivery crate",
        brave_move="talked the grizzly through a side door instead of chasing it deeper",
        fix="rolled the cart aside, cleaned the jam, and reopened the light gate",
        lesson="courage can sound calm even in a tunnel",
        ending="the tram lights blinked on and the last car sailed home bright and safe",
    ),
}

ROUTES = (
    "inner_monologue_first",
    "quest_first",
    "dialogue_first",
    "danger_first",
    "sidekick_first",
    "question_first",
)

ASP_RULES = r"""
quest_ready(H) :- hero(H), has_quest(H), knows_clue(H).
happy_ending(H) :- hero(H), quest_ready(H), solves_problem(H).
valid_story :- happy_ending(hero).
"""


def quest_id(target: str) -> str:
    return "quest_" + "".join(ch if ch.isalnum() else "_" for ch in target.lower()).strip("_")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("hero", "hero"),
        asp.fact("has_quest", "hero"),
        asp.fact("knows_clue", "hero"),
        asp.fact("solves_problem", "hero"),
    ]
    for target, _, _ in (
        ("the moon key", "", ""),
        ("museum steps", "", ""),
        ("river bridge", "", ""),
        ("library roof", "", ""),
        ("tram tunnel", "", ""),
    ):
        lines.append(asp.fact("quest", quest_id(target)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show happy_ending/1."))
    asp_happy = set(asp.atoms(model, "happy_ending"))
    py_happy = {("hero",)}
    if asp_happy == py_happy:
        print("OK: clingo gate matches python reasoning (happy ending holds).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(asp_happy))
    print("python:", sorted(py_happy))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(v)
        for v in (
            params.seed,
            params.setting_name,
            params.hero_name,
            params.hero_alias,
            params.sidekick_name,
            params.sidekick_alias,
            params.grizzly_name,
            params.quest_target,
            params.route,
            params.tone,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.setting_name not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting_name}")
    if params.quest_target not in {"the moon key", "museum steps", "river bridge", "library roof", "tram tunnel"}:
        raise StoryError(f"Unknown quest target: {params.quest_target}")
    setting = SETTINGS[params.setting_name]
    return World(
        setting=Setting(name=setting.name, kind=setting.kind),
        hero=Hero(name=params.hero_name, alias=params.hero_alias, role="superhero"),
        sidekick=Hero(name=params.sidekick_name, alias=params.sidekick_alias, role="sidekick"),
        grizzly=Hero(name=params.grizzly_name, alias="Grizzly", role="grizzly"),
        quest=QuestState(
            target=params.quest_target,
            need=params.quest_need,
            hazard=params.quest_hazard,
            solution=params.quest_solution,
        ),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    hero, sidekick, grizzly, quest, setting = (
        world.hero,
        world.sidekick,
        world.grizzly,
        world.quest,
        world.setting,
    )
    case = CASES["museum_steps" if params.quest_target == "the moon key" else params.quest_target if params.quest_target in CASES else "museum_steps"]

    hero.memes.update(courage=1, focus=1)
    sidekick.memes.update(hope=1, trust=1)
    grizzly.meters["weight"] = 220

    openings = {
        "inner_monologue_first": f"{hero.name} tugged at the cape and thought, I can do this. {quest.need.capitalize()}, and {quest.hazard}.",
        "quest_first": f"The quest began in {setting.name}. {quest.need.capitalize()}, and {case.setup}.",
        "dialogue_first": f'"We need a plan," said {sidekick.name}. "{hero.name}, will you lead the quest?" {hero.name} nodded because {quest.need}.',
        "danger_first": f"{case.setup.capitalize()}. {quest.need.capitalize()}, and the grizzly was already close to the square.",
        "sidekick_first": f"{sidekick.name} spotted the problem first: {case.setup}. That meant {quest.need}.",
        "question_first": f'"Why is a grizzly here?" {hero.name} asked in {setting.name}. The answer mattered because {quest.need}.',
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f'"I will scour for clues," {hero.name} said, and the word sounded like a promise.',
                f'"We scour the area, not the crowd," {sidekick.name} whispered, and {hero.name} smiled.',
                f'"If we scour the streets carefully, we might find the truth," {hero.name} told the sidekick.',
                f'"No rushing," {hero.name} said. "We scour with our eyes and keep everyone safe."',
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"Their inner monologue stayed quiet but sharp: {hero.name} knew a hero must not terminate a problem by guessing.",
                f"{hero.name} thought, A quest is a promise to stay brave until the last clue makes sense.",
                f"Inside, {hero.name} worried about the grizzly, yet kept the face steady for the city.",
                f"{hero.name} remembered that happy endings are built one careful choice at a time.",
            ]
        )
    )

    world.para()
    world.say(f"First, {hero.name} {case.first_action}.")
    world.say(
        rng.choice(
            [
                f"But that idea did not finish the quest, because {case.failed_reason}.",
                f"The first guess failed; {case.failed_reason}.",
                f'"That is not it," {sidekick.name} said gently, because {case.failed_reason}.',
                f"Even the grizzly paused, but the clue was still hidden because {case.failed_reason}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"Then they noticed the key clue: {case.clue}.",
                f"A brighter clue appeared next: {case.clue}.",
                f"{sidekick.name} pointed and said, '{case.clue.capitalize()}.'",
                f"The trail changed when they saw that {case.clue}.",
            ]
        )
    )
    world.say(f"It all fit together: {case.cause}. That explained why {quest.hazard}.")

    world.para()
    world.say(
        rng.choice(
            [
                f'{hero.name} took a slow breath. "We do not need to fight the grizzly," the hero said. "We need to help it."',
                f'"Can we finish this without hurting anyone?" {hero.name} asked. {sidekick.name} answered, "Yes, if we stay calm."',
                f"{hero.name}'s heart pounded, but the hero still said, 'We can be brave and gentle.'",
                f'"The safest answer is the best answer," {sidekick.name} said, and {hero.name} agreed.',
            ]
        )
    )
    world.say(f"Then {hero.name} {case.brave_move}.")
    hero.memes["bravery"] = 2
    quest.done = True
    world.say(f"After that, they {case.fix}.")
    setting.meters["safe_paths"] = 1
    grizzly.meters["calm"] = 1

    world.para()
    world.say(
        rng.choice(
            [
                f"At the end of the quest, {case.lesson}.",
                f"{sidekick.name} grinned and said, 'That was a real hero quest.' {hero.name} replied, '{case.lesson.capitalize()}.'",
                f"The city learned a small superhero truth: {case.lesson}.",
                f"{hero.name} wrote the lesson in the hero notebook: {case.lesson}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"By sunset, {case.ending}.",
                f"The final scene was simple: {case.ending}.",
                f"Before the stars came out, {case.ending}.",
                f"At last, {case.ending}.",
            ]
        )
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        grizzly=grizzly,
        setting=setting,
        quest=quest,
        case=case,
        solved=True,
        happy=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    return [
        f"Write a superhero story about {f['hero'].name} and {f['sidekick'].name} on a quest in {f['setting'].name}.",
        f"Include an inner monologue, a grizzly problem, and the word scour as the heroes search for the truth.",
        f"End with a happy ending showing how they {case.fix}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    return [
        QAItem(
            question=f"What quest did {f['hero'].name} need to finish?",
            answer=f"{f['hero'].name} needed to finish the quest to solve why {case.setup}."),
        QAItem(
            question=f"Why did the first superhero plan fail?",
            answer=f"The first plan failed because {case.failed_reason}."),
        QAItem(
            question=f"What clue revealed the real cause?",
            answer=f"The clue was that {case.clue}. It showed that {case.cause}."),
        QAItem(
            question=f"How did the hero treat the grizzly at the end?",
            answer=f"{f['hero'].name} stayed calm, used a gentle solution, and helped the grizzly instead of hurting it."),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"They {case.fix}, and then {case.ending}."),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in a superhero story?",
            answer="A quest is a mission or search where the hero keeps going until an important problem is solved."),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thinking, like a short thought the reader can hear."),
        QAItem(
            question="What does it mean to scour for clues?",
            answer="To scour for clues means to search carefully and thoroughly."),
        QAItem(
            question="Can a superhero story end happily without a fight?",
            answer="Yes. A happy ending can come from courage, wise choices, and helping others safely."),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large bear."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest storyworld with a grizzly, scour, and a happy ending.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--setting")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_name = args.setting or rng.choice(sorted(SETTINGS))
    hero_name, hero_alias = rng.choice(HEROES)
    sidekick_name, sidekick_alias = rng.choice(SIDEKICKS)
    grizzly_name, _ = rng.choice(GRIZZLIES)
    target = rng.choice(list(CASES))
    return StoryParams(
        seed=args.seed,
        setting_name=setting_name,
        hero_name=args.hero_name or hero_name,
        hero_alias=hero_alias,
        sidekick_name=args.sidekick_name or sidekick_name,
        sidekick_alias=sidekick_alias,
        grizzly_name=grizzly_name,
        quest_target=target if target == "the moon key" else target,
        quest_need=CASES[target].worry.replace("the ", "the "),
        quest_hazard=CASES[target].setup,
        quest_solution=CASES[target].fix,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.setting, world.hero, world.sidekick, world.grizzly):
        lines.append(f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}")
    lines.append(
        f"quest: target={world.quest.target!r} need={world.quest.need!r} "
        f"hazard={world.quest.hazard!r} solution={world.quest.solution!r} done={world.quest.done}"
    )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show happy_ending/1."))
        print(sorted(set(asp.atoms(model, "happy_ending"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = 3 if args.all else args.n
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

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
