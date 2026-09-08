#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "harbor square": {
        "setting": "the bright harbor square",
        "feature": "a fountain shaped like a seashell",
        "route": "the pier road",
    },
    "cobble avenue": {
        "setting": "the sunlit cobble avenue",
        "feature": "a row of flower boxes",
        "route": "the old clock tower",
    },
    "lighthouse green": {
        "setting": "the grassy green beneath the lighthouse",
        "feature": "a red-and-white signal flag",
        "route": "the lighthouse gate",
    },
    "river market": {
        "setting": "the busy river market",
        "feature": "a bridge covered with paper lanterns",
        "route": "the riverside bandstand",
    },
}

NAMES = ("Luna", "Mira", "Theo", "Pia", "Noah", "Sami", "Ivy", "Jules")
MOODS = ("hopeful", "careful", "cheerful", "patient")
INSTRUMENTS = ("brass drum", "small trumpet", "silver whistle", "wooden flute")
FLAGS = ("blue", "gold", "green", "scarlet")

CASES = (
    {
        "title": "the silent drum",
        "opening": "The town parade was ready to begin, but the infantry band's big drum made no sound.",
        "mistake": "thought the sailor leading the band had lost the drumsticks overboard",
        "clue": "a little paper boat was tucked inside the drum, holding a note with a familiar name",
        "turn": "the drum was silent because the sailor had hidden it there to protect a surprise message from the rain",
        "action": "read the dry note aloud and carried it to the end of the parade line",
        "result": "the note invited an old sailor to lead the final march beside the infantry musicians",
        "ending": "When the drum finally boomed, the sailor smiled from the front row, and every flag seemed to wave for him.",
        "lesson": "a quiet pause can be part of a loving plan",
    },
    {
        "title": "the backwards march",
        "opening": "The parade's infantry company marched backward past the harbor boats, making everyone whisper.",
        "mistake": "believed the sailors had taught the soldiers the wrong steps",
        "clue": "each backward step brought the marchers closer to a small child waiting beside the route",
        "turn": "the unusual march was a gentle rescue plan for a sailor's daughter who was too shy to join the crowd",
        "action": "opened a space in the line and invited the child to hold the parade's smallest flag",
        "result": "she took three brave steps forward and found her waiting family among the musicians",
        "ending": "The parade turned forward together, with the smallest flag dancing highest above the happy street.",
        "lesson": "a strange-looking choice may be making room for someone who needs courage",
    },
    {
        "title": "the missing blue flag",
        "opening": "Just before the parade, the infantry flag bearer discovered that the blue flag was gone.",
        "mistake": "suspected that a playful sailor had borrowed it to decorate a boat",
        "clue": "a blue corner showed beneath the blanket of an elderly sailor resting near the bandstand",
        "turn": "the sailor had wrapped the flag around his shoulders because he was cold after waiting to see the parade",
        "action": "asked permission, warmed him with a proper coat, and returned the flag to its pole",
        "result": "the sailor chose to walk beside the infantry instead of sitting alone",
        "ending": "The blue flag rose over the march, while the old sailor's coat and the parade colors shone side by side.",
        "lesson": "kind questions can reveal a need hidden inside a mistake",
    },
    {
        "title": "the empty sailor seat",
        "opening": "A decorated sailor's chair stood empty at the parade review, and the brass band stopped playing.",
        "mistake": "thought the sailor had changed his mind about coming home",
        "clue": "a trail of bright buttons led from the chair toward the infantry children's rehearsal tent",
        "turn": "the sailor was helping a nervous young drummer fasten a uniform button before the ceremony",
        "action": "announced the drummer's name and saved a place for the sailor beside the band",
        "result": "the young drummer played the opening beat, and the sailor joined the applause",
        "ending": "The empty chair no longer mattered; two generations sat together beneath the parade banners.",
        "lesson": "someone may be missing from a place because they are helping somewhere else",
    },
    {
        "title": "the gentle detour",
        "opening": "The parade route suddenly bent away from the harbor, and the infantry captain looked worried.",
        "mistake": "assumed a sailor had confused the map while tying flags to the masts",
        "clue": "the detour passed the small clinic where a child could watch safely from a window",
        "turn": "the captain had changed the route so a sick child would not miss the parade",
        "action": "quieted the drums near the clinic, lifted the flags high, and waved toward the window",
        "result": "the child smiled and raised a paper sailor hat in reply",
        "ending": "The parade returned to the harbor with softer hearts and a paper hat bobbing in every memory.",
        "lesson": "the best route is sometimes the one that reaches a person who cannot come outside",
    },
)

OPENINGS = (
    "The morning began with polished shoes, bright ribbons, and a promise of music.",
    "Sunlight spilled over the street as the town prepared its warmest welcome.",
    "Long before the first drumbeat, the parade route was full of small acts of care.",
    "The flags were ready, the sailors were smiling, and the infantry band was tuning up.",
)

MOVES = (
    "Luna checked the route instead of blaming the nearest person.",
    "Luna asked each helper what they had seen and what they only guessed.",
    "Luna listened for the detail that did not fit the first explanation.",
    "Luna and the helper followed the safest clue through the waiting crowd.",
)

DIALOGUE = (
    ("Maybe the sailor caused the trouble", "Maybe, but we should ask what he needs before we decide"),
    ("Why is the infantry line changing", "Let us watch where it leads before we call it wrong"),
    ("The parade must go on perfectly", "A parade is better when someone who needs kindness can enjoy it"),
    ("I found a clue", "Then let us share it gently and check the whole story"),
    ("Should we hurry to fix this", "We can move quickly without forgetting to be kind"),
)

ASP_RULES = r"""
kind(parade).
kind(sailor).
kind(infantry).
feature(twist).
style(heartwarming).

setting("harbor_square").
setting("cobble_avenue").
setting("lighthouse_green").
setting("river_market").

supports("harbor_square", parade).
supports("cobble_avenue", parade).
supports("lighthouse_green", parade).
supports("river_market", parade).

has_role("harbor_square", sailor).
has_role("cobble_avenue", sailor).
has_role("lighthouse_green", sailor).
has_role("river_market", sailor).

has_unit("harbor_square", infantry).
has_unit("cobble_avenue", infantry).
has_unit("lighthouse_green", infantry).
has_unit("river_market", infantry).

valid(P) :- setting(P), supports(P, parade), has_role(P, sailor), has_unit(P, infantry).
#show valid/1.
#show feature/1.
#show style/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    mood: str
    instrument: str
    flag: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming parade storyworld with a sailor, infantry, and a twist.")
    parser.add_argument("--place", choices=PLACES)
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


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        key = place.replace(" ", "_")
        lines.extend(
            (
                asp.fact("setting", key),
                asp.fact("supports", key, "parade"),
                asp.fact("has_role", key, "sailor"),
                asp.fact("has_unit", key, "infantry"),
            )
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    found = set(asp.atoms(model, "valid"))
    expected = {(place.replace(" ", "_"),) for place in PLACES}
    if found != expected:
        print("MISMATCH:")
        print("only in clingo:", sorted(found - expected))
        print("only in python:", sorted(expected - found))
        return 1
    print(f"OK: clingo gate matches Python reasoning ({len(found)} settings).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError("The parade needs a known setting.")
    hero = rng.choice(NAMES)
    helper = rng.choice([name for name in NAMES if name != hero])
    return StoryParams(
        place=place,
        hero=hero,
        helper=helper,
        mood=rng.choice(MOODS),
        instrument=rng.choice(INSTRUMENTS),
        flag=rng.choice(FLAGS),
        seed=args.seed,
    )


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    raw = "|".join((params.place, params.hero, params.helper, params.mood, params.instrument, params.flag))
    return int.from_bytes(hashlib.blake2b(raw.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("The parade setting is not registered.")
    if params.hero == params.helper:
        raise StoryError("The parade needs two different people so their dialogue can matter.")

    seed = story_seed(params)
    rng = random.Random(seed)
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    move = MOVES[(seed // (len(CASES) * len(OPENINGS))) % len(MOVES)]
    dialogue = DIALOGUE[(seed // (len(CASES) * len(OPENINGS) * len(MOVES))) % len(DIALOGUE)]
    meta = PLACES[params.place]

    world = World(place=meta["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="parade helper",
        type="helper",
        meters={"walking": 1.0, "attention": 1.0},
        memes={"hope": 0.8, "kindness": 0.7},
        location=params.place,
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        label="parade companion",
        type="companion",
        meters={"walking": 0.8, "attention": 0.8},
        memes={"hope": 0.7, "kindness": 0.8},
        location=params.place,
    )
    sailor = Entity(
        id="sailor",
        kind="character",
        label="returning sailor",
        type="sailor",
        meters={"walking": 0.6, "strength": 0.8},
        memes={"homesick": 0.4, "joy": 0.5},
        location=params.place,
    )
    infantry = Entity(
        id="infantry",
        kind="group",
        label="town infantry band",
        type="infantry",
        meters={"marching": 1.0},
        memes={"pride": 0.8, "care": 0.7},
        location=params.place,
    )
    flag = Entity(
        id="flag",
        kind="object",
        label=f"{params.flag} parade flag",
        type="flag",
        meters={"height": 2.0},
        memes={"welcome": 0.6},
        location=params.place,
    )
    world.entities = {entity.id: entity for entity in (hero, helper, sailor, infantry, flag)}

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} parade helper, stood in {world.place} with {params.helper} "
        f"as sailors and the infantry band prepared to march."
    )
    world.say(f"The {params.instrument} waited beside the {params.flag} flag, and {meta['feature']} sparkled nearby.")
    world.say(case["opening"])

    world.para()
    world.say(move)
    world.say(f"{params.helper} pointed toward the sailors. '{dialogue[0]},' {params.helper} said.")
    world.say(f"'{dialogue[1]},' answered {params.hero}. They agreed to look before making a judgment.")
    world.say(f"Their first idea did not solve anything: they {case['mistake']}.")
    world.say(f"Then {params.hero} noticed that {case['clue']}.")

    world.para()
    world.say(f"That was the twist: {case['turn']}.")
    world.say(f"{params.hero} and {params.helper} {case['action']}.")
    world.say(f"Because they paused to understand the clue, {case['result']}.")
    world.say(f"The parade moved again, and the lesson was simple: {case['lesson'].capitalize()}.")
    world.say(case["ending"])

    hero.meters["attention"] = 1.5
    helper.meters["attention"] = 1.3
    sailor.memes["joy"] = 1.0
    sailor.memes["homesick"] = 0.0
    infantry.memes["welcome"] = 1.0
    flag.memes["welcome"] = 1.0

    world.trace = [
        f"parade_started:{params.place}",
        f"first_guess:{case['mistake']}",
        f"clue_found:{case['clue']}",
        f"twist_revealed:{case['turn']}",
        f"welcome_completed:{case['result']}",
    ]
    world.facts = {
        "place": params.place,
        "setting": meta["setting"],
        "hero": params.hero,
        "helper": params.helper,
        "case": case["title"],
        "twist": case["turn"],
        "resolution": case["result"],
        "lesson": case["lesson"],
        "roles": ("sailor", "infantry"),
    }

    prompts = [
        f"Write a heartwarming parade story in {meta['setting']} with a sailor, an infantry band, and a gentle twist.",
        f"Show how {params.hero} and {params.helper} discover why the parade is not going as expected.",
        f"Include a {params.flag} flag, a {params.instrument}, spoken dialogue, and an ending that proves someone feels welcomed.",
    ]
    story_qa = [
        QAItem(
            question="What problem interrupted the parade?",
            answer=f"The parade was interrupted by {case['opening'].lower()} The unusual event made the helpers investigate instead of rushing ahead.",
        ),
        QAItem(
            question=f"What did {params.helper} first think?",
            answer=f"{params.helper} first thought that they {case['mistake']}. That explanation changed when the new clue appeared.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case['turn'].capitalize()}. The hidden reason turned the problem into a chance to care for someone.",
        ),
        QAItem(
            question="How did the parade end?",
            answer=f"{params.hero} and {params.helper} {case['action']}. As a result, {case['result']}.",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"They learned that {case['lesson']}. Their patience helped the parade become more welcoming.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk, play music, carry signs or flags, and share a celebration.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on a boat or ship and learns how to stay safe on the water.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry is a group of soldiers who travel and work on foot. In this gentle story, the infantry appears as a marching ceremonial band.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            details = [f"label={entity.label}"]
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} " + " ".join(details))
        for event in sample.world.trace:
            print(f"  event: {event}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = (
    StoryParams("harbor square", "Luna", "Mira", "hopeful", "brass drum", "blue"),
    StoryParams("lighthouse green", "Theo", "Pia", "careful", "small trumpet", "gold"),
    StoryParams("river market", "Noah", "Ivy", "cheerful", "wooden flute", "green"),
)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1.\n#show feature/1.\n#show style/1."))
        print(asp.atoms(model, "valid"))
        print(asp.atoms(model, "feature"))
        print(asp.atoms(model, "style"))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            seed = (args.seed if args.seed is not None else random.randrange(2**31)) + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
