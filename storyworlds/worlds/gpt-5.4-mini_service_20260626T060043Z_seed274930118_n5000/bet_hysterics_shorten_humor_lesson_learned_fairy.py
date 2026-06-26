#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a foolish bet, a burst of hysterics,
and a clever way to shorten a task until the lesson is learned.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    kind: str = "character"
    role: str = "child"
    title: str = ""
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"princess", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"prince", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ObjectThing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    atmosphere: str
    has_fountain: bool = False


@dataclass
class Bet:
    wager: str
    task: str
    shortened_task: str
    reward: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    rival: str
    bet: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "castle": Setting(place="the moonlit castle", atmosphere="silver and quiet", has_fountain=True),
    "forest": Setting(place="the green forest", atmosphere="mossy and bright", has_fountain=False),
    "village": Setting(place="the tiny village square", atmosphere="warm and busy", has_fountain=True),
}

BETS = {
    "ladder": Bet(
        wager="a jar of honey cakes",
        task="count every stone from the gate to the tower",
        shortened_task="count only the bright stones by the fountain",
        reward="the silver ribbon",
        lesson="a wise plan is better than a grand boast",
    ),
    "hay": Bet(
        wager="a basket of berries",
        task="carry a hay bale all the way across the yard",
        shortened_task="carry only a small armful of hay",
        reward="the golden thimble",
        lesson="laughing at a dare can still teach a useful lesson",
    ),
    "riddle": Bet(
        wager="a tiny carved bell",
        task="sing a song without stopping for the whole walk home",
        shortened_task="sing just one chorus by the fountain",
        reward="the rose-gold comb",
        lesson="shortening a task can turn trouble into a kinder game",
    ),
}

HEROES = [
    ("Rosalind", "princess"),
    ("Gareth", "prince"),
    ("Mina", "girl"),
    ("Pip", "boy"),
]

RIVALS = [
    ("Bram", "boy"),
    ("Lila", "girl"),
    ("Sir Nettle", "knight"),
    ("Nora", "girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale about a bet, hysterics, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--rival")
    ap.add_argument("--bet", choices=BETS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    bet = args.bet or rng.choice(list(BETS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    rival = args.rival or rng.choice([r for r, _ in RIVALS])
    return StoryParams(setting=setting, hero=hero, rival=rival, bet=bet)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    bet = BETS[params.bet]
    world = World(setting)

    hero_role = next(role for name, role in HEROES if name == params.hero)
    rival_role = next(role for name, role in RIVALS if name == params.rival)

    hero = world.add(Character(id=params.hero, role=hero_role, title="young", label=params.hero))
    rival = world.add(Character(id=params.rival, role=rival_role, title="clever", label=params.rival))
    prize = world.add(ObjectThing(id="prize", label=bet.reward, phrase=bet.reward))
    wager = world.add(ObjectThing(id="wager", label=bet.wager, phrase=bet.wager))

    hero.memes["pride"] = 2
    rival.memes["teasing"] = 1
    hero.meters["determination"] = 1

    world.say(
        f"Once upon a time, in {setting.place}, {hero.id} boasted that {hero.pronoun('subject')} could win a bet."
    )
    world.say(
        f"{rival.id} laughed and offered {wager.phrase} if {hero.id} could finish {bet.task} before sunset."
    )
    world.say(
        f"The words sparkled in the air, and {hero.id} said yes too quickly, because pride can be a slippery shoe."
    )

    world.para()
    hero.memes["worry"] = 1
    hero.memes["hysterics"] = 1
    world.say(
        f"At first {hero.id} tried bravely, but the task felt as long as a dragon's tail."
    )
    world.say(
        f"Then {hero.id} flung {hero.pronoun('possessive')} hands in the air and broke into hysterics."
    )
    world.say(
        f"{rival.id} was startled, and even the fountain seemed to hold its breath."
    )

    world.para()
    hero.memes["calm"] = 1
    world.say(
        f"A kindly old baker passed by and said, \"A clever fairy tale does not always ask for the longest road.\""
    )
    world.say(
        f"So {hero.id} chose to shorten the task to {bet.shortened_task}, which was still fair but no longer impossible."
    )
    hero.meters["progress"] = 1
    world.say(
        f"{hero.id} finished that smaller task with a puff and a laugh, and {rival.id} had to admit it was fair."
    )
    world.say(
        f"In the end, {hero.id} kept {prize.phrase}, {hero.pronoun('subject')} learned {bet.lesson}, and the hysterics turned into giggles."
    )

    world.facts.update(hero=hero, rival=rival, bet=bet, setting=setting, prize=prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    bet = f["bet"]
    return [
        f'Write a short fairy tale about {hero.id} making a foolish bet with {rival.id}.',
        f"Tell a gentle story where a child gets into hysterics and then learns to shorten a hard task.",
        f'Write a humorous fairy tale that includes the words "bet", "hysterics", and "shorten".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    bet = f["bet"]
    return [
        QAItem(
            question=f"What did {rival.id} offer if {hero.id} could finish the bet?",
            answer=f"{rival.id} offered {bet.wager} if {hero.id} could finish {bet.task}.",
        ),
        QAItem(
            question=f"What happened when the task felt too hard for {hero.id}?",
            answer=f"{hero.id} broke into hysterics because the task felt too long and too hard.",
        ),
        QAItem(
            question=f"How did {hero.id} make the task easier?",
            answer=f"{hero.id} chose to shorten the task to {bet.shortened_task}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned {bet.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bet?",
            answer="A bet is an agreement where people promise something if one of them can do a challenge.",
        ),
        QAItem(
            question="What are hysterics?",
            answer="Hysterics are a big burst of wild upset crying or laughing that can happen when feelings get too strong.",
        ),
        QAItem(
            question="What does shorten mean?",
            answer="To shorten something is to make it smaller, briefer, or not as long.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    for title, items in [
        ("Generation prompts", sample.prompts),
        ("Story questions", sample.story_qa),
        ("World knowledge questions", sample.world_qa),
    ]:
        lines.append(f"== {title} ==")
        if title == "Generation prompts":
            for i, p in enumerate(items, 1):
                lines.append(f"{i}. {p}")
        else:
            for qa in items:
                lines.append(f"Q: {qa.question}")
                lines.append(f"A: {qa.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        if isinstance(e, Character):
            lines.append(f"  {e.id:10} character meters={e.meters} memes={e.memes}")
        else:
            lines.append(f"  {e.id:10} thing     label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
rival(R) :- rival_name(R).
shorten(B) :- bet(B), task(B,T), shortened(B,S), shorter(S,T).
lesson_learned(H) :- hero(H), calmed(H), shortened_task(H).
humor(H) :- hero(H), hysterics(H), then_giggles(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_fountain:
            lines.append(asp.fact("fountain", sid))
    for bid, b in BETS.items():
        lines.append(asp.fact("bet", bid))
        lines.append(asp.fact("wager", bid, b.wager))
        lines.append(asp.fact("task", bid, b.task))
        lines.append(asp.fact("shortened", bid, b.shortened_task))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shorten/1. #show humor/1. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for bet in BETS:
                params = StoryParams(setting=setting, hero="Rosalind", rival="Bram", bet=bet)
                samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
