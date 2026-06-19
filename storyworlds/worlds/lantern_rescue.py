#!/usr/bin/env python3
"""
lantern_rescue.py
=================

A tiny StoryWorld for the seed:

    words: lantern, turtle, whisper
    features: Kindness, Cautionary, Mystery
    style: Fable

The story is generated from a small simulated world: a child hears a mysterious
night sound, discovers a lost creature, chooses a gentle guide, and uses a
lantern to lead the creature home. The Python validity gate and the inline ASP
rules intentionally encode the same constraints.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Place:
    key: str
    phrase: str
    destinations: tuple[str, ...]
    landmark: str


@dataclass(frozen=True)
class Creature:
    key: str
    phrase: str
    destination: str
    need: str
    sound: str
    thanks: str
    accepts: tuple[str, ...]


@dataclass(frozen=True)
class Guide:
    key: str
    phrase: str
    action: str
    quality: str


@dataclass
class StoryParams:
    place: str
    creature: str
    guide: str
    hero: str
    gender: str
    mentor: str
    seed: int


@dataclass
class Entity:
    name: str
    kind: str
    tags: dict[str, str] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], bool]


@dataclass
class World:
    params: StoryParams
    place: Place
    creature: Creature
    guide: Guide
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for name, ent in self.entities.items():
            detail = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            memes = f" memes={ent.memes}" if ent.memes else ""
            suffix = f" {detail}" if detail else ""
            rows.append(f"  {name:<8} ({ent.kind:<10}){suffix}{memes}")
        rows.append(f"  place destinations: {', '.join(self.place.destinations)}")
        rows.append(f"  fired rules: {self.fired_rules}")
        return "\n".join(rows)


PLACES: dict[str, Place] = {
    "moon_pier": Place("moon_pier", "the moonlit pier", ("pond", "tide_pool"), "a silver rope rail"),
    "reed_marsh": Place("reed_marsh", "the whispering reed marsh", ("pond", "reeds", "nest"), "a bent willow"),
    "foggy_bridge": Place("foggy_bridge", "the foggy footbridge", ("pond", "nest"), "three glowing stones"),
    "pine_cove": Place("pine_cove", "the pine cove path", ("tide_pool", "nest"), "a fallen pine cone"),
}

CREATURES: dict[str, Creature] = {
    "turtle": Creature(
        "turtle",
        "a small turtle with moon-dust on its shell",
        "pond",
        "a safe pond path",
        "scritch... scritch...",
        "My feet found the water again",
        ("whisper", "hum"),
    ),
    "frog": Creature(
        "frog",
        "a green frog tangled in reeds",
        "reeds",
        "the reed bed",
        "ribbit? ribbit?",
        "The reeds know my name again",
        ("whisper", "hum"),
    ),
    "duckling": Creature(
        "duckling",
        "a lost duckling with a trembling beak",
        "nest",
        "the warm nest",
        "peep-peep-nowhere",
        "The nest sounds like home",
        ("whisper", "hum", "tap"),
    ),
    "crab": Creature(
        "crab",
        "a little crab walking in worried sideways circles",
        "tide_pool",
        "the tide pool",
        "click-click-lost",
        "The tide pool remembers me",
        ("whisper", "tap"),
    ),
}

GUIDES: dict[str, Guide] = {
    "whisper": Guide("whisper", "a careful whisper", "whispered beside the lantern", "quiet"),
    "hum": Guide("hum", "a low humming tune", "hummed beside the lantern", "steady"),
    "tap": Guide("tap", "three soft lantern taps", "tapped gently on the lantern handle", "patient"),
    "shout": Guide("shout", "a loud shout", "shouted into the dark", "startling"),
}

HEROES = {
    "girl": ("Mira", "Nora", "Lina", "June", "Rose"),
    "boy": ("Theo", "Finn", "Sam", "Eli", "Ben"),
}

MENTORS = ("grandmother", "uncle", "aunt", "father", "mother")


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def _article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def _with_article(text: str) -> str:
    if text.startswith(("a ", "an ", "the ")):
        return text
    return f"{_article(text)} {text}"


def valid_combo(place: str, creature: str, guide: str) -> bool:
    if place not in PLACES or creature not in CREATURES or guide not in GUIDES:
        return False
    c = CREATURES[creature]
    return c.destination in PLACES[place].destinations and guide in c.accepts


def invalid_reason(place: str, creature: str, guide: str) -> str:
    if place not in PLACES:
        return f"No story: unknown place {place!r}."
    if creature not in CREATURES:
        return f"No story: unknown creature {creature!r}."
    if guide not in GUIDES:
        return f"No story: unknown guide {guide!r}."
    c = CREATURES[creature]
    p = PLACES[place]
    if c.destination not in p.destinations:
        return f"No story: {p.phrase} does not lead to the {c.destination} needed by the {c.key}."
    if guide not in c.accepts:
        return f"No story: {GUIDES[guide].phrase} would not safely guide the {c.key}; try {', '.join(c.accepts)}."
    return "No story: the requested rescue is not reasonable."


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for creature in CREATURES:
            for guide in GUIDES:
                if valid_combo(place, creature, guide):
                    combos.append((place, creature, guide))
    return combos


def _r_darkness_creates_mystery(world: World) -> bool:
    creature = world.entities["Creature"]
    creature.add_meme("lost", 1.0)
    creature.add_meme("mystery", 0.7)
    world.note(f"The night hid the way to the {world.creature.destination}.")
    return True


def _r_gentle_guidance_rescues(world: World) -> bool:
    hero = world.entities["Hero"]
    creature = world.entities["Creature"]
    lantern = world.entities["Lantern"]
    hero.add_meme("kindness", 1.0)
    hero.add_meme("caution", 0.6)
    creature.add_meme("safe", 1.0)
    creature.tags["destination"] = world.creature.destination
    lantern.tags["used_for"] = "guidance"
    world.note(f"{hero.name} used {world.guide.phrase} and the lantern to guide the {world.creature.key}.")
    return True


RULES = [
    Rule("mystery", _r_darkness_creates_mystery),
    Rule("guided_home", _r_gentle_guidance_rescues),
]


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    creature = CREATURES[params.creature]
    guide = GUIDES[params.guide]
    world = World(params=params, place=place, creature=creature, guide=guide)
    world.entities["Hero"] = Entity(params.hero, params.gender, {"role": "helper"})
    world.entities["Mentor"] = Entity(params.mentor.title(), params.mentor, {"role": "caution"})
    world.entities["Creature"] = Entity(creature.key, creature.key, {"need": creature.need})
    world.entities["Lantern"] = Entity("lantern", "object", {"light": "warm"})
    for rule in RULES:
        if rule.apply(world):
            world.fired_rules.append(rule.name)
    return world


def _render_story(world: World) -> str:
    p = world.params
    he, his, him = _pronouns(p.gender)
    place = world.place
    creature = world.creature
    guide = world.guide
    mentor = p.mentor
    creature_intro = _with_article(creature.phrase)

    opening = (
        f"Once, when the moon tucked itself behind a cloud, {p.hero} carried a brass lantern "
        f"through {place.phrase} with {his} {mentor}. The lantern made a small golden circle, "
        f"but beyond it the night kept its secrets."
    )
    sound = creature.sound if creature.sound[-1] in ".!?" else f"{creature.sound}."
    mystery = (
        f"Near {place.landmark}, {p.hero} heard a whispery sound: \"{sound}\" "
        f"There, in the edge of the lantern light, was {creature_intro}."
    )
    warning = (
        f"\"A lost creature needs a calm guide, not a frightened hurry,\" said {his} {mentor}. "
        f"{p.hero} wanted to rush ahead, but {he} remembered that a bright lantern can help "
        f"only when the hand that holds it is gentle."
    )
    rescue = (
        f"So {p.hero} {guide.action}, moving one careful step at a time. The {creature.key} "
        f"followed the glow until the path reached {creature.need}."
    )
    ending = (
        f"\"{creature.thanks},\" said the {creature.key}. {p.hero} smiled and carried the "
        f"lantern home a little lower, so smaller feet could see it too. The fable says: "
        f"kindness is brightest when it walks slowly enough for someone else."
    )
    return "\n\n".join([opening, mystery, warning, rescue, ending])


def _prompts(world: World) -> list[str]:
    return [
        'Write a mysterious kindness fable for children using the words "lantern", "turtle", and "whisper".',
        f"Tell a cautionary night story where {world.params.hero} helps {world.creature.phrase} using {world.guide.phrase}.",
        "Write a gentle animal-rescue tale where a lantern helps only because the child stays calm.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    p = world.params
    c = world.creature
    _he, his, _him = _pronouns(p.gender)
    return [
        QAItem("Who is the story about?", f"It is about {p.hero}, {his} {p.mentor}, and {c.phrase}. The mentor matters because the child wants to help quickly but needs a calmer way."),
        QAItem(
            "What was mysterious at first?",
            f"{p.hero} heard the sound \"{c.sound}\" before seeing the {c.key}. The lantern revealed what the dark had hidden.",
        ),
        QAItem(
            "What caution did the mentor give?",
            f"{p.mentor.title()} warned that a lost creature needs a calm guide, not frightened hurry. That kept {p.hero} from rushing.",
        ),
        QAItem(
            "How did the child help?",
            f"{p.hero} used {world.guide.phrase} and the brass lantern to guide the {c.key} to {c.need}. The help worked because the signal was gentle enough for a frightened creature to follow.",
        ),
        QAItem(
            "What lesson does the fable teach?",
            "It teaches that kindness works best when it is patient. The child had to slow down so the smaller creature could follow safely.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    base = [
        QAItem(
            "Why can a lantern help at night?",
            "A lantern makes nearby obstacles easier to see. It also gives a small safe point to follow in the dark.",
        ),
        QAItem(
            "Why should someone avoid shouting near a lost animal?",
            "A loud shout can startle a lost animal and make it run the wrong way. A quiet signal is safer when the animal is already frightened.",
        ),
    ]
    if world.creature.key == "turtle":
        base.append(QAItem("Why do turtles need a safe pond path?", "Turtles move slowly on land, so a clear path helps them reach water without getting trapped or scared."))
    if world.creature.key == "frog":
        base.append(QAItem("Why do frogs like reeds?", "Reeds give frogs cover near water. They can hide there and stay close to damp places."))
    if world.creature.key == "duckling":
        base.append(QAItem("Why do ducklings follow sounds?", "Ducklings use calls to stay near their family. Gentle repeated sounds can help them find the right direction."))
    if world.creature.key == "crab":
        base.append(QAItem("Why do crabs need tide pools?", "A tide pool keeps a small crab damp and sheltered until the tide changes again."))
    return base


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.place, params.creature, params.guide):
        raise StoryError(invalid_reason(params.place, params.creature, params.guide))
    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = """
combo(P,C,G) :-
    place(P),
    creature(C),
    guide(G),
    creature_dest(C,D),
    place_dest(P,D),
    accepts(C,G).

ok :- chosen(P,C,G), combo(P,C,G).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows = []
    for key, place in PLACES.items():
        rows.append(fact("place", key))
        for dest in place.destinations:
            rows.append(fact("place_dest", key, dest))
    for key, creature in CREATURES.items():
        rows.append(fact("creature", key))
        rows.append(fact("creature_dest", key, creature.destination))
        for guide in creature.accepts:
            rows.append(fact("accepts", key, guide))
    for key in GUIDES:
        rows.append(fact("guide", key))
    if params is not None:
        rows.append(fact("chosen", params.place, params.creature, params.guide))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    symbols = solve(asp_program(), models=0)
    combos: set[tuple[str, str, str]] = set()
    for model in symbols:
        combos.update(atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    asp = asp_valid_combos()
    if py != asp:
        only_py = sorted(py - asp)
        only_asp = sorted(asp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos)."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate lantern rescue storyworld samples.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--creature", choices=sorted(CREATURES))
    parser.add_argument("--guide", choices=sorted(GUIDES))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES), default=None)
    parser.add_argument("--mentor", choices=MENTORS)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str], index: int = 0) -> StoryParams:
    rng = random.Random(args.seed + index)
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    mentor = args.mentor or rng.choice(MENTORS)
    place, creature, guide = combo
    return StoryParams(place=place, creature=creature, guide=guide, hero=hero, gender=gender, mentor=mentor, seed=args.seed + index)


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    rng = random.Random(args.seed + index)
    combos = valid_combos()
    if args.place or args.creature or args.guide:
        place = args.place or rng.choice(sorted(PLACES))
        creature = args.creature or rng.choice(sorted(CREATURES))
        guide = args.guide or rng.choice(sorted(GUIDES))
        if not valid_combo(place, creature, guide):
            raise StoryError(invalid_reason(place, creature, guide))
        combo = (place, creature, guide)
    else:
        combo = rng.choice(combos)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Generation prompts -- asks that would produce this story ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for place, creature, guide in sorted(asp_valid_combos()):
        print(f"{place}\t{creature}\t{guide}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            for i, combo in enumerate(valid_combos(), 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {sample.params.hero}: {combo[1]} with {combo[2]} at {combo[0]}")
                if i != len(valid_combos()) and not args.json:
                    print("\n" + "=" * 70 + "\n")
            return 0
        for i in range(max(1, args.n)):
            sample = generate(resolve_params(args, i))
            emit(sample, args, f"### variant {i + 1}" if args.n > 1 and not args.json else None)
            if i != max(1, args.n) - 1 and not args.json:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
