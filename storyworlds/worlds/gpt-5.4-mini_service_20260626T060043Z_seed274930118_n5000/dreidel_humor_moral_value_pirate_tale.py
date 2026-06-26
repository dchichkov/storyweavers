#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a dreidel, a joke, and a moral choice.

This world models a small shipboard scene in which a young pirate enjoys
spinning a dreidel for fun, but a tempting shortcut creates a problem. The
captain warns the crew, the youngster faces a choice, and the ending proves a
moral change through a concrete state shift.

The tale is designed to stay close to a pirate-story tone while still being
child-facing, causal, and grounded in simulation.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

# A small, fixed set of moral/social states we can narrate.
MORAL_WORDS = {
    "honest": "honest",
    "kind": "kind",
    "fair": "fair",
    "helpful": "helpful",
    "greedy": "greedy",
    "sneaky": "sneaky",
}

# Humor beats are soft and child-friendly.
JOKE_BEATS = {
    "spinning": "The dreidel spun so fast it looked like a tiny top with a hat.",
    "tumble": "When it tipped over, it landed with a silly little clack.",
    "prize": "The shiny prize bounced like it wanted to join the game.",
    "tease": "The monkey kept grinning as if it knew the punch line already.",
}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate", "captain"}
        # Captain is neutral enough for our purposes; use "they" if not clear.
        if self.type in female and self.type != "captain":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type != "captain":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pirate ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    mess: str
    theme: str
    keyword: str = "dreidel"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    value: str
    plural: bool = False


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the pirate ship", affords={"spin", "joke", "share"}),
    "dock": Setting(place="the dock", affords={"spin", "joke", "share"}),
    "island": Setting(place="the palm island", affords={"spin", "joke", "share"}),
}

ACTIVITIES = {
    "spin": Activity(
        id="spin",
        verb="spin the dreidel",
        gerund="spinning the dreidel",
        rush="spin it too fast",
        danger="it might fly off the barrel",
        mess="bump",
        theme="dreidel",
        keyword="dreidel",
        tags={"dreidel", "humor"},
    ),
    "joke": Activity(
        id="joke",
        verb="tell a joke",
        gerund="telling jokes",
        rush="blurt it out too soon",
        danger="the joke might be mean instead of funny",
        mess="hurt",
        theme="humor",
        keyword="joke",
        tags={"humor"},
    ),
    "share": Activity(
        id="share",
        verb="share the prize",
        gerund="sharing treasure",
        rush="grab the prize for oneself",
        danger="the crew might feel cheated",
        mess="sting",
        theme="moral",
        keyword="share",
        tags={"moral", "value"},
    ),
}

PRIZES = {
    "coin": Prize(label="coin", phrase="a shiny gold coin", type="coin", value="gold coin"),
    "shell": Prize(label="shell", phrase="a bright sea shell", type="shell", value="sea shell"),
    "apple": Prize(label="apple", phrase="a red apple from the galley", type="apple", value="apple"),
}

TOKENS = {
    "dreidel": Token(
        id="dreidel",
        label="dreidel",
        phrase="a small spinning dreidel with carved letters",
        helps={"spin", "joke"},
        covers={"fun"},
    ),
    "lantern": Token(
        id="lantern",
        label="lantern",
        phrase="a little lantern that glowed like a warm star",
        helps={"joke", "share"},
        covers={"light"},
    ),
    "rope": Token(
        id="rope",
        label="rope",
        phrase="a coil of rope to steady the deck",
        helps={"spin", "share"},
        covers={"steady"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Zoe", "Pia", "Ruby"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Jace", "Levi", "Ned"]
TRAITS = ["brave", "cheeky", "curious", "lively", "playful", "small"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen setting affords the activity and the prize
% is one the crew can honestly argue about in a pirate tale.
valid_story(S,A,P) :- affords(S,A), prize(P), reasonable(P), activity(A).

% Dreidel stories are always available in this world, but the scene must still
% have a sensible moral turn.
reasonable(coin) :- activity(spin).
reasonable(shell) :- activity(joke).
reasonable(apple) :- activity(share).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.affords:
            for pid in PRIZES:
                if is_reasonable(aid, pid):
                    combos.append((sid, aid, pid))
    return combos


def is_reasonable(activity_id: str, prize_id: str) -> bool:
    if activity_id == "spin" and prize_id in {"coin", "shell"}:
        return True
    if activity_id == "joke" and prize_id in {"shell", "apple"}:
        return True
    if activity_id == "share" and prize_id in {"coin", "apple"}:
        return True
    return False


def select_token(activity: Activity) -> Token:
    for tok in TOKENS.values():
        if activity.id in tok.helps:
            return tok
    return TOKENS["dreidel"]


def predict(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "trouble": sim.facts.get("trouble", False),
        "hurt": sim.facts.get("hurt", False),
        "sting": sim.facts.get("sting", False),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    if activity.id == "joke":
        actor.memes["humor"] = actor.memes.get("humor", 0.0) + 1.0
    if activity.id == "share":
        actor.memes["moral_value"] = actor.memes.get("moral_value", 0.0) + 1.0
    if activity.id == "spin":
        world.facts["spin_fast"] = True
    if narrate:
        world.say(f"{actor.id} was {activity.gerund}.")


def cause_trouble(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    if activity.id == "spin":
        world.facts["trouble"] = True
        world.say(f"It was funny at first, but {activity.danger}.")
    elif activity.id == "joke":
        world.facts["hurt"] = True
        world.say("The first joke was not kind, and the crew's smiles sank like pebbles.")
    elif activity.id == "share":
        world.facts["sting"] = True
        world.say("The greedy grab made the others stare, because one hand had taken too much.")


def moral_turn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity, token: Token) -> bool:
    if activity.id == "spin":
        world.say(
            f'{captain.pronoun("subject").capitalize()} laughed and said, '
            f'"Spin slower, matey. A dreidel can be funny without flying like a gull!"'
        )
        return True
    if activity.id == "joke":
        world.say(
            f'{captain.pronoun("subject").capitalize()} tapped the lantern and said, '
            f'"A good joke makes hearts lighter, not smaller."'
        )
        return True
    if activity.id == "share":
        world.say(
            f'{captain.pronoun("subject").capitalize()} nodded and said, '
            f'"Fair sharing keeps the whole crew steady."'
        )
        return True
    return False


def resolution(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity, token: Token) -> None:
    if activity.id == "spin":
        world.say(
            f'They set the dreidel on the barrel and used the {token.label} to keep it from skittering. '
            f'After that, {hero.id} spun it gently, and the crew giggled when it wobbled and stopped on its side.'
        )
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        hero.memes["moral_value"] = hero.memes.get("moral_value", 0.0) + 1.0
    elif activity.id == "joke":
        hero.memes["kind"] = hero.memes.get("kind", 0.0) + 1.0
        world.say(
            f"{hero.id} tried again with a kinder joke. This time the ship shook with happy laughter, "
            f"and the little dreidel clicked along like it was applauding."
        )
    elif activity.id == "share":
        hero.memes["fair"] = hero.memes.get("fair", 0.0) + 1.0
        world.say(
            f"{hero.id} split the prize into fair pieces and passed one to each matey. "
            f"The deck felt lighter, and even the dreidel looked pleased beside the shared treasure."
        )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, captain_type: str = "captain") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious"])
    ))
    captain = world.add(Entity(
        id="Captain", kind="character", type=captain_type, label="the captain"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=captain.id
    ))
    token = world.add(Entity(
        id="token", type="token", label=select_token(activity).label, phrase=select_token(activity).phrase
    ))

    hero.memes["love_play"] = 1.0
    hero.memes["moral_value"] = 0.0
    hero.memes["humor"] = 0.0

    world.say(
        f"{hero.id} was a little {hero.traits[1] if len(hero.traits) > 1 else 'cheeky'} {hero.type} "
        f"on {world.setting.place}, and {hero.pronoun('possessive')} favorite toy was {token.phrase}."
    )
    world.say(
        f"{hero.id} loved {activity.gerund}, because the little dreidel made the deck feel like a game."
    )
    world.say(
        f"One bright day, {hero.id} and {hero.pronoun('possessive')} {captain.label} found {prize.phrase} by the mast."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {activity.danger}."
    )

    world.para()
    do_activity(world, hero, activity, narrate=False)
    cause_trouble(world, hero, activity, prize)
    moral_turn(world, captain, hero, activity, prize, token)

    world.para()
    resolution(world, captain, hero, activity, prize, token)
    world.facts.update(hero=hero, captain=captain, prize=prize, token=token, activity=activity, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short pirate tale for a young child that features a {f["token"].label} and the word "dreidel".',
        f"Tell a funny-but-kind story where {hero.id} wants to {activity.verb} but learns a moral lesson about {prize.label}.",
        f"Write a pirate story with humor and a moral value beat that ends with {hero.id} making a fair choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, activity = f["hero"], f["captain"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} make the better choice?",
            answer=f"{captain.label.capitalize()} helped {hero.id} see a better way.",
        ),
        QAItem(
            question=f"What was the story's important lesson?",
            answer="The story showed that being fair and kind is better than acting greedy or mean.",
        ),
        QAItem(
            question=f"What toy made the pirate tale feel silly and fun?",
            answer=f"The dreidel made the tale feel silly and fun.",
        ),
        QAItem(
            question=f"How did the ending change what {hero.id} did?",
            answer=f"At the end, {hero.id} chose a fair and kinder way instead of the risky choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dreidel?",
            answer="A dreidel is a small spinning top with four sides that can be used as a game toy.",
        ),
        QAItem(
            question="What does it mean to be fair?",
            answer="Being fair means giving everyone a reasonable share and not taking too much for yourself.",
        ),
        QAItem(
            question="Why are jokes sometimes funny?",
            answer="Jokes are funny when they surprise people in a lighthearted way and make them laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------


CURATED = [
    StoryParams(setting="ship", activity="spin", prize="coin", name="Mina", gender="girl", captain="captain", trait="cheeky"),
    StoryParams(setting="dock", activity="joke", prize="shell", name="Finn", gender="boy", captain="captain", trait="playful"),
    StoryParams(setting="island", activity="share", prize="apple", name="Nora", gender="girl", captain="captain", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld with a dreidel, humor, and a moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain"])
    ap.add_argument("--name")
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
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.captain,
    )
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
