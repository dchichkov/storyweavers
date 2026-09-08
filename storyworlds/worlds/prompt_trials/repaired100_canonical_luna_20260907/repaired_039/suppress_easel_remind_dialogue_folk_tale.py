#!/usr/bin/env python3
"""A child-facing folk tale about a noisy easel, a quiet lesson, and remembering kindly."""

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
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Easel:
    name: str
    material: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Mara"
    place: str = "the hill village"
    lesson: str = "remember the bell before the wind"
    easel: str = "the old wooden easel"


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    objects: dict[str, Easel] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = ["Luna", "Tavi", "Neri", "Pip", "Sela"]
HELPERS = ["Mara", "Grandmother Iva", "Old Tom", "Bela", "Aunt Noma"]
PLACES = ["the hill village", "the riverside village", "the village square", "the orchard hamlet"]
LESSONS = [
    "remember the bell before the wind",
    "listen before you hurry",
    "share the work before the storm",
    "remember what the old tools teach",
]
EASELS = [
    "the old wooden easel",
    "the painted village easel",
    "the crooked cedar easel",
    "the little market easel",
]

TRIALS = [
    {
        "key": "wind",
        "trouble": "A sharp wind rattled the easel and sent the painted notice sliding toward the well.",
        "clue": "the easel's back peg was resting outside its socket",
        "failed": "Luna tried to hold the notice alone, but the loose peg made the whole frame dance",
        "hero": "caught the lower edge of the notice",
        "helper": "pressed a flat stone against the easel's foot",
        "fix": "Luna held the board steady while Mara pushed the peg home and tied a cord around the frame",
        "result": "The notice stood firm, and the villagers could read it before the next gust.",
        "ending": "the old easel cast a straight shadow beside the well",
    },
    {
        "key": "bell",
        "trouble": "The market bell rang by itself, and every startled goat bumped the easel as it fled.",
        "clue": "the bell rope had caught beneath one leg",
        "failed": "Luna tried to suppress the ringing with both hands, but the trapped rope pulled harder",
        "hero": "guided the goats toward the grain shed",
        "helper": "lifted the easel just high enough to free the rope",
        "fix": "They moved the animals first, then freed the rope and set the easel on level ground.",
        "result": "The bell grew quiet, and the market notice stayed bright and readable.",
        "ending": "the goats nibbled calmly while the bell rested in its wooden cradle",
    },
    {
        "key": "rain",
        "trouble": "Clouds burst over the square, and rain began to wash the village map from the easel.",
        "clue": "a woven awning was rolled up beside the baker's door",
        "failed": "Luna tried to suppress the spreading drops with her sleeve, but the wet cloth smeared the ink",
        "hero": "held the map board beneath the awning",
        "helper": "unrolled the cover and tied its two corners",
        "fix": "They sheltered the board first, then copied the few blurred marks from memory.",
        "result": "The map was saved, and the travelers found the road to the warm inn.",
        "ending": "rain tapped the awning while the rescued map dried in a golden patch of light",
    },
    {
        "key": "crow",
        "trouble": "A clever crow stole the bright ribbon from the easel and perched on the roof with it.",
        "clue": "a bowl of shiny pebbles sat near the fountain",
        "failed": "Luna waved her arms to suppress the crow's boasting, but the bird only flew higher",
        "hero": "placed the pebbles in a neat shining trail",
        "helper": "held the easel so the ribbon would not fall into the mud",
        "fix": "They traded the pebbles for the ribbon and tied it back with a double knot.",
        "result": "The crow took the pebbles, and the ribbon once again marked the village path.",
        "ending": "two black eyes gleamed above the square while the ribbon danced below",
    },
]

OPENINGS = [
    "{hero} lived in {place}, where every useful word was painted before it was spoken.",
    "In {place}, people trusted old tools, clear voices, and the memory of their neighbors.",
    "Long ago, {hero} watched over the notice board in {place}.",
]

def build_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different people")
    world = World(params=params)
    world.people = {
        params.hero: Person(params.hero, "young keeper"),
        params.helper: Person(params.helper, "village helper"),
    }
    world.objects = {
        "easel": Easel("easel", params.easel, meters={"stability": 0.35})
    }
    return world


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    trial = rng.choice(TRIALS)
    p = params

    world.say(rng.choice(OPENINGS).format(hero=p.hero, place=p.place))
    world.say(f"{p.hero} cared for {p.easel}, which held the village notice above the dusty road.")
    world.say(f"The notice reminded everyone to {p.lesson}.")
    world.para()

    world.say(trial["trouble"])
    world.say(f'"I must suppress this trouble at once," {p.hero} cried.')
    world.say(f'"Do not fight the noise before you find its cause," {p.helper} replied. "What does the easel remind you to inspect?"')
    world.say(f"{p.hero} looked closely and saw that {trial['clue']}.")
    world.say(f'"Now I remember," {p.hero} said. "The loose part is calling for help."')
    world.say(f"At first, {p.hero} tried alone, but {trial['failed']}.")

    world.para()
    world.say(f'"Let us use our hands wisely," said {p.helper}. "You take one task, and I will take another."')
    world.say(f"{p.hero} {trial['hero']}, while {p.helper} {trial['helper']}.")
    world.say(trial["fix"])
    world.say(f'"A quiet plan can be stronger than a loud struggle," {p.helper} reminded {p.hero}.')
    world.say(trial["result"])

    world.para()
    world.say(f"{p.hero} read the notice aloud: “Remember to {p.lesson}.”")
    world.say(f"The villagers nodded, for the words were no longer merely painted; they had become true.")
    world.say(f"When evening came, {trial['ending']}.")
    world.say(f"{p.hero} thanked {p.helper}, and {p.helper} answered, “A good reminder is a gift we give one another.”")

    world.people[p.hero].meters.update(courage=1.0, attention=1.0)
    world.people[p.hero].memes.update(remembrance=1.0, cooperation=1.0)
    world.people[p.helper].meters.update(patience=1.0, care=1.0)
    world.people[p.helper].memes.update(remembrance=1.0, cooperation=1.0)
    world.objects["easel"].meters["stability"] = 1.0
    world.objects["easel"].memes["reminder"] = 1.0
    world.facts.update(
        trial=trial["key"],
        trouble=trial["trouble"],
        clue=trial["clue"],
        failed=trial["failed"],
        hero_task=trial["hero"],
        helper_task=trial["helper"],
        fix=trial["fix"],
        result=trial["result"],
        ending=trial["ending"],
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Tell a folk tale about {p.hero} and {p.helper} repairing {p.easel}.",
        f"Write a child-friendly story where someone must suppress a disturbance and remember a useful clue.",
        f"Create a tale in which dialogue changes the characters' plan and an easel becomes a reminder.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            f"What trouble threatened the notice?",
            f"{f['trouble']} The disturbance put the notice and the village message at risk.",
        ),
        QAItem(
            "What clue helped the characters choose a better plan?",
            f"They noticed that {f['clue']}. This clue showed what needed repair instead of encouraging them to struggle blindly.",
        ),
        QAItem(
            "How did the two characters divide the work?",
            f"{p.hero} {f['hero_task']}, while {p.helper} {f['helper_task']}. Their separate jobs made the repair safer.",
        ),
        QAItem(
            "How did dialogue change what happened?",
            f"{p.helper} urged {p.hero} to inspect the cause before fighting the trouble. After hearing that reminder, {p.hero} found that {f['clue']} and changed plans.",
        ),
        QAItem(
            "What proved that the problem was solved?",
            f"{f['result']} The ending image was that {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to suppress a disturbance?",
            "To suppress a disturbance means to make it quieter or stop it from spreading. A wise person first checks the cause instead of merely pushing against the noise.",
        ),
        QAItem(
            "What is an easel?",
            "An easel is a stand that holds a painting, drawing, sign, or board upright so people can work on it or see it.",
        ),
        QAItem(
            "Why can a reminder be helpful?",
            "A reminder brings an important idea back to someone's attention. It can help a person choose carefully when surprise or hurry makes remembering difficult.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
easel(E) :- easel_name(E).
repair_needed(E) :- easel(E), disturbance.
dialogue_guides(H,K) :- hero(H), helper(K), speaks(K), clue_found, listens(H).
remembered(H) :- hero(H), reminder, listens(H).
resolved(E) :- repair_needed(E), dialogue_guides(_, _), remembered(_), shared_repair.
folk_tale(H,K,E) :- hero(H), helper(K), easel(E), resolved(E).
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp
    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("helper_name", p.helper),
            asp.fact("easel_name", "easel"),
            asp.fact("disturbance"),
            asp.fact("speaks", p.helper),
            asp.fact("clue_found"),
            asp.fact("listens", p.hero),
            asp.fact("reminder"),
            asp.fact("shared_repair"),
        ]
    )


def asp_program(show: str = "#show folk_tale/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    atoms = asp.atoms(asp.one_model(asp_program()), "folk_tale")
    ok = bool(atoms)
    print("OK: ASP and Python agree on the repaired easel tale." if ok else "MISMATCH: ASP tale atom missing.")
    if not ok:
        return 1
    sample = generate(StoryParams(seed=17))
    checks = ("easel", "remind", "suppress")
    if not all(word in sample.story.lower() for word in checks):
        print("MISMATCH: generated story lacks a required narrative instrument.")
        return 1
    print("OK: generated story exercises dialogue, suppression, and remembrance.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--lesson", choices=LESSONS)
    parser.add_argument("--easel", choices=EASELS)
    parser.add_argument("--seed", type=int)
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        lesson=args.lesson or rng.choice(LESSONS),
        easel=args.easel or rng.choice(EASELS),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(
            "\n--- trace ---\n"
            f"hero={sample.world.params.hero}\n"
            f"helper={sample.world.params.helper}\n"
            f"trial={sample.world.facts['trial']}\n"
            f"clue={sample.world.facts['clue']}\n"
            f"resolved={sample.world.facts['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        atoms = asp.atoms(asp.one_model(asp_program()), "folk_tale")
        print("1 repaired easel folk tale pattern." if atoms else "0 repaired easel folk tale patterns.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = len(TRIALS) if args.all else args.n

    for i in range(count):
        seed = base_seed + i
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
