#!/usr/bin/env python3
"""
storyworlds/worlds/little_misunderstanding_tall_tale.py
========================================================

A tiny tall-tale world about a little misunderstanding that gets bigger than a
barn before it gets untangled again.

The seed story premise:
- A little child sees something odd.
- The odd thing is misunderstood in an exaggerated, tall-tale way.
- A helper explains the truth.
- The fear shrinks, the world settles, and the ending shows what changed.

The simulation keeps both physical meters and emotional memes:
- meters: size, distance, loudness, wobble, glow, etc.
- memes: curiosity, worry, courage, relief, pride, confusion

The story is not a frozen template; the state drives what gets narrated.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    feature: str  # what the scene visibly contains: "hill", "barn", "well", ...


@dataclass
class Misunderstanding:
    id: str
    observed: str
    actual: str
    exaggeration: str
    clue: str
    resolve_speech: str
    meter: str
    meme: str


@dataclass
class StoryParams:
    place: str
    misunderstanding: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hill": Setting(place="the windy hill", feature="a crooked old hat"),
    "barn": Setting(place="the red barnyard", feature="a round water tank"),
    "river": Setting(place="the river bend", feature="a shiny rope in the reeds"),
    "orchard": Setting(place="the apple orchard", feature="a white sack on a branch"),
}

MISTAKES = {
    "hat": Misunderstanding(
        id="hat",
        observed="a hat as big as a wagon wheel",
        actual="a lonely hat on a fence post",
        exaggeration="a giant hat the size of a moonbeam",
        clue="the fence post was wearing it, not the sky",
        resolve_speech="It's only a hat on the post, not a giant coming to town!",
        meter="towering",
        meme="confusion",
    ),
    "rope": Misunderstanding(
        id="rope",
        observed="a snake as long as a fence line",
        actual="a rope tied to a stump",
        exaggeration="a long snake the length of three wagons",
        clue="the stump had tied knots in it",
        resolve_speech="It's a rope, not a snake, and it's tied to the stump!",
        meter="snaking",
        meme="worry",
    ),
    "sack": Misunderstanding(
        id="sack",
        observed="a cloud with a pocket",
        actual="a sack of apples",
        exaggeration="a cloud carrying a whole orchard in its pocket",
        clue="one apple peeked out and rolled downhill",
        resolve_speech="That's a sack of apples, not a cloud at all!",
        meter="bulging",
        meme="surprise",
    ),
}

HELPERS = {
    "grandpa": {"type": "man", "label": "Grandpa", "speech": "chuckled"},
    "grandma": {"type": "woman", "label": "Grandma", "speech": "laughed"},
    "neighbor": {"type": "man", "label": "the neighbor", "speech": "grinned"},
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ada", "June", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Max", "Eli", "Leo", "Finn"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the setting shows the clue for the misunderstanding.
valid_story(P, M, H) :- place(P), mistake(M), helper(H), clue_visible(P, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("feature", pid, s.feature))
    for mid, m in MISTAKES.items():
        lines.append(asp.fact("mistake", mid))
        lines.append(asp.fact("observed", mid, m.observed))
        lines.append(asp.fact("actual", mid, m.actual))
        lines.append(asp.fact("clue_text", mid, m.clue))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    # Hand-authored compatibility facts: each setting can show the clue for the
    # one misunderstanding it is designed around.
    for pid, mid in compatible_pairs():
        lines.append(asp.fact("clue_visible", pid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_pairs() -> list[tuple[str, str]]:
    return sorted(compatible_pairs())


def compatible_pairs() -> list[tuple[str, str]]:
    return [
        ("hill", "hat"),
        ("barn", "rope"),
        ("orchard", "sack"),
        ("river", "rope"),
    ]


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = {(p, m, h) for p, m in compatible_pairs() for h in HELPERS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid stories ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python validity:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_little(name: str) -> str:
    return f"little {name}"


def maybe_article(text: str) -> str:
    if text[:1].lower() in "aeiou":
        return f"an {text}"
    return f"a {text}"


def setup_story(world: World, hero: Entity, helper: Entity, mistake: Misunderstanding) -> None:
    hero.memes["curiosity"] = 1.0
    hero.memes["confusion"] = 0.0
    helper.memes["calm"] = 1.0
    world.say(
        f"{hero.id} was a little {hero.type} who noticed every speck of strange news "
        f"on {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved wandering there because even a small thing "
        f"could look like {mistake.exaggeration} when the wind had a story to tell."
    )
    world.say(
        f"That day, {hero.id} and {helper.label} were near {world.setting.place} when "
        f"{hero.id} saw {mistake.observed}."
    )


def feel_big(world: World, hero: Entity, mistake: Misunderstanding) -> None:
    hero.memes["fear"] = 1.0
    hero.meters["distance_to_trouble"] = 1.0
    hero.meters[mistake.meter] = 1.0
    world.say(
        f"To {hero.id}, it looked like {mistake.exaggeration}. "
        f"{hero.pronoun().capitalize()} backed up three tiny steps, but in a tall-tale world "
        f"three steps can feel like three miles."
    )
    world.say(
        f"{hero.id} called out, \"Look out!\" and the worry in {hero.pronoun('possessive')} voice "
        f"grew as big as a barn roof."
    )


def investigate(world: World, hero: Entity, helper: Entity, mistake: Misunderstanding) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    helper.meters["near"] = 1.0
    world.say(
        f"{helper.label} did not laugh at once. {helper.label} walked closer, slow as a milk cart, "
        f"and peered at the thing from the side."
    )
    world.say(
        f"Then {helper.label} pointed to {mistake.clue} and said, \"Hold on now. "
        f"{mistake.resolve_speech}\""
    )


def resolve(world: World, hero: Entity, helper: Entity, mistake: Misunderstanding) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 1.0
    hero.memes["pride"] = 1.0
    hero.meters[mistake.meter] = 0.0
    hero.meters["distance_to_trouble"] = 0.0
    world.say(
        f"{hero.id}'s eyes grew round, then bright. The giant thing shrank back into an ordinary "
        f"{mistake.actual}, and the whole misunderstanding turned inside out like a sock."
    )
    world.say(
        f"{helper.label} {HELPERS[helper.id]['speech']} and {hero.id} laughed too. "
        f"In the end, the wind had only borrowed a scary shape for a minute, and now everybody "
        f"could see the truth plain as daylight."
    )


def story_seed_text(world: World, hero: Entity, helper: Entity, mistake: Misunderstanding) -> str:
    return (
        f"{hero.id} saw {mistake.observed} at {world.setting.place}, thought it was "
        f"{mistake.exaggeration}, and later learned it was really {mistake.actual}."
    )


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A little tall-tale storyworld built around a misunderstanding."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=MISTAKES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.misunderstanding:
        if (args.place, args.misunderstanding) not in compatible_pairs():
            raise StoryError("That setting does not support that misunderstanding in this world.")
    choices = [p for p in compatible_pairs()
               if (args.place is None or p[0] == args.place)
               and (args.misunderstanding is None or p[1] == args.misunderstanding)]
    if not choices:
        raise StoryError("No valid story matches the chosen options.")
    place, misunderstanding = rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, misunderstanding=misunderstanding, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    mistake = MISTAKES[params.misunderstanding]
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={},
    ))
    helper_def = HELPERS[params.helper]
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=helper_def["type"],
        label=helper_def["label"],
        meters={},
        memes={},
    ))

    setup_story(world, hero, helper, mistake)
    world.para()
    feel_big(world, hero, mistake)
    investigate(world, hero, helper, mistake)
    world.para()
    resolve(world, hero, helper, mistake)

    world.facts.update(
        hero=hero,
        helper=helper,
        mistake=mistake,
        setting=world.setting,
    )

    story = world.render()
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mistake: Misunderstanding = f["mistake"]
    helper: Entity = f["helper"]
    return [
        f'Write a tall-tale story for a young child about "{mistake.observed}" at {world.setting.place}.',
        f"Tell a little misunderstanding story where {hero.id} thinks something is {mistake.exaggeration} "
        f"and {helper.label} helps explain the truth.",
        f'Create a short child-facing story using the word "little" and ending with the truth about '
        f"{mistake.actual}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mistake: Misunderstanding = f["mistake"]
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {hero.id} think {mistake.observed} was at {place}?",
            answer=f"{hero.id} thought it was {mistake.exaggeration}, because it looked strange from far away.",
        ),
        QAItem(
            question=f"Who helped {hero.id} figure out the truth about the thing at {place}?",
            answer=f"{helper.label} helped by walking closer, looking carefully, and pointing out {mistake.clue}.",
        ),
        QAItem(
            question=f"What was the thing really?",
            answer=f"It was really {mistake.actual}, not a giant {mistake.exaggeration.split(' a ')[-1] if ' a ' in mistake.exaggeration else 'thing'} at all.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the misunderstanding was solved?",
            answer=f"{hero.id} felt relieved and proud, because the big scary idea shrank down into an ordinary thing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to misunderstand something?",
            answer="To misunderstand something means to think it is one thing when it is really something else.",
        ),
        QAItem(
            question="Why can small things seem big in a tall tale?",
            answer="In a tall tale, the storyteller makes things sound extra huge or extra grand, so a little thing can seem bigger than life.",
        ),
        QAItem(
            question="What should someone do before they panic about a strange sight?",
            answer="They should look again, move closer if it is safe, and ask someone wiser to help check it.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_pairs() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_facts_show() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_facts_show())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_pairs()
        print(f"{len(combos)} valid (place, mistake, helper) combinations:\n")
        for p, m, h in combos:
            print(f"  {p:8} {m:14} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hill", misunderstanding="hat", name="Lily", gender="girl", helper="grandpa"),
            StoryParams(place="barn", misunderstanding="rope", name="Ben", gender="boy", helper="neighbor"),
            StoryParams(place="orchard", misunderstanding="sack", name="Mia", gender="girl", helper="grandma"),
            StoryParams(place="river", misunderstanding="rope", name="Leo", gender="boy", helper="neighbor"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.misunderstanding} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
