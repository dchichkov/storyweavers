#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

PLACES = {
    "moonlit orchard": {
        "setting": "the moonlit orchard",
        "safe": True,
        "has_tomb": True,
        "has_dinette": True,
    },
    "silver castle garden": {
        "setting": "the silver castle garden",
        "safe": True,
        "has_tomb": True,
        "has_dinette": True,
    },
    "whispering hill": {
        "setting": "the whispering hill",
        "safe": True,
        "has_tomb": True,
        "has_dinette": False,
    },
}

NAMES = ("Luna", "Mara", "Pip", "Elio", "Nell", "Toby", "Iris", "Jasper")
MOODS = ("brave", "kind", "patient", "curious")
MAJOR_TITLES = ("Major Rowan", "Major Bell", "Major Thorne", "Major Finch")

TALES = (
    {
        "title": "The Rhyme Beneath the Rose",
        "opening": "One blue evening, Luna found a silver rhyme carved beside an old tomb.",
        "rhyme": "At the dinette, set the plate; the lost moon key will open the gate.",
        "mistake": "thought the tomb itself was hungry and needed a dinner plate",
        "clue": "the carved moon pointed from the tomb toward a tiny dinette beneath a rose arbor",
        "turn": "the rhyme was a direction, not a request to feed the tomb",
        "action": "placed a wooden plate on the dinette and read the next line aloud",
        "result": "a hidden drawer opened and revealed the moon key",
        "ending": "The moon key shone like a small star, and the old tomb rested peacefully among the roses.",
        "lesson": "a rhyme may hide a path, so look for what each word points toward",
    },
    {
        "title": "The Major's Midnight Feast",
        "opening": "At midnight, Major Rowan asked the children to solve a mystery before the castle bells rang three times.",
        "rhyme": "By the tomb, do not gloom; find the dinette in the room.",
        "mistake": "believed the tomb was the room and searched among its stones",
        "clue": "a warm square of light glowed from a garden room beside the tomb",
        "turn": "the rhyme led them beside the tomb to a little dinette, where a letter waited",
        "action": "carried the letter to Major Rowan instead of opening the sealed tomb",
        "result": "the major learned that the missing lantern had been borrowed by the castle cook",
        "ending": "The cook returned the lantern, and Major Rowan served warm cakes at the bright little dinette.",
        "lesson": "when a clue sounds gloomy, follow its whole rhyme before making a frightening guess",
    },
    {
        "title": "The Dinette of Dawn",
        "opening": "Before sunrise, a fairy bell rang from a stone tomb at the edge of the kingdom.",
        "rhyme": "When bells resume, leave the tomb; share bread at the dinette room.",
        "mistake": "wanted to stay beside the tomb until the bell stopped",
        "clue": "the bell changed to a gentle chime whenever someone entered the nearby dining nook",
        "turn": "the rhyme promised that sharing breakfast would make the fairy bell quiet",
        "action": "invited the lonely gatekeeper to the dinette and shared bread and berry jam",
        "result": "the bell softened into birdsong and the gate opened for travelers",
        "ending": "Dawn spilled gold across the stones while friends laughed around the tiny dinette.",
        "lesson": "kind company can solve a riddle that force cannot",
    },
    {
        "title": "Major Moon's Lost Crown",
        "opening": "Major Bell lost a moon-shaped crown during a parade through the enchanted village.",
        "rhyme": "Past the tomb, follow the plume; crown rests where small tables bloom.",
        "mistake": "searched for a feather plume on top of the tomb",
        "clue": "white feathers marked a trail toward a room filled with little tables and painted chairs",
        "turn": "the rhyme pointed past the tomb to the dinette where the parade children had placed the crown",
        "action": "asked each child what they had seen and found the crown beneath a napkin",
        "result": "Major Bell thanked them and changed the parade route to pass safely around the old stones",
        "ending": "The crown gleamed above the major's smile as the parade danced past the moonlit dinette.",
        "lesson": "a clear question can reveal where a missing treasure truly went",
    },
)

DIALOGUES = (
    ("Is the tomb calling for supper?", "Perhaps the rhyme is calling us somewhere else."),
    ("Should we open the tomb?", "No. We can solve the clue without disturbing a resting place."),
    ("The rhyme sounds scary.", "Its ending may be a map in disguise."),
    ("I found the dinette!", "Then let us see what the rhyme asks us to do there."),
    ("Major, what do you know?", "Only that the old words must be read with care."),
    ("What if we are wrong?", "We will test the safest idea first."),
)

OPENERS = (
    "The kingdom had many secrets, but wise folk solved them gently.",
    "That night, even the fireflies seemed to wait for an answer.",
    "A small mystery can grow large when a rhyme points into the dark.",
    "In the fairy kingdom, old stones often remembered what people forgot.",
)

ASP_RULES = r"""
kind(tomb).
kind(dinette).
kind(major).
feature(rhyme).
style(fairy_tale).
setting(P) :- safe_place(P).
has_feature(P, rhyme) :- safe_place(P), has_tomb(P), has_dinette(P).
valid_story(P) :- safe_place(P), has_tomb(P), has_dinette(P), has_feature(P, rhyme).
safe_place(moonlit_orchard).
safe_place(silver_castle_garden).
safe_place(whispering_hill).
has_tomb(moonlit_orchard).
has_tomb(silver_castle_garden).
has_tomb(whispering_hill).
has_dinette(moonlit_orchard).
has_dinette(silver_castle_garden).
has_dinette(whispering_hill) :- false.
#show has_feature/2.
#show valid_story/1.
"""

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    major: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fairy tale about a tomb, a dinette, and a major rhyme.")
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
    for place, meta in PLACES.items():
        name = place.replace(" ", "_")
        if meta["safe"]:
            lines.append(asp.fact("safe_place", name))
        if meta["has_tomb"]:
            lines.append(asp.fact("has_tomb", name))
        if meta["has_dinette"]:
            lines.append(asp.fact("has_dinette", name))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    expected = {
        (place.replace(" ", "_"), "rhyme")
        for place, meta in PLACES.items()
        if meta["safe"] and meta["has_tomb"] and meta["has_dinette"]
    }
    model = asp.one_model(asp_program("#show has_feature/2."))
    actual = set(asp.atoms(model, "has_feature"))
    if actual == expected:
        print(f"OK: clingo gate matches Python reasoning ({len(actual)} facts).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(actual - expected))
    print("only in python:", sorted(expected - actual))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        place for place, meta in PLACES.items()
        if meta["safe"] and meta["has_tomb"] and meta["has_dinette"]
    ]
    place = args.place or rng.choice(choices)
    if place not in choices:
        raise StoryError("This tale needs a safe place with both a tomb and a dinette.")
    hero = rng.choice(NAMES)
    companion = rng.choice([name for name in NAMES if name != hero])
    major = rng.choice(MAJOR_TITLES)
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, companion=companion, major=major, mood=mood)


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    value = "|".join((params.place, params.hero, params.companion, params.major, params.mood))
    return int.from_bytes(hashlib.blake2b(value.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    meta = PLACES[params.place]
    if not (meta["safe"] and meta["has_tomb"] and meta["has_dinette"]):
        raise StoryError("The selected place cannot support the tomb-and-dinette rhyme.")
    seed = story_seed(params)
    rng = random.Random(seed)
    tale = TALES[seed % len(TALES)]
    opener = OPENERS[(seed // len(TALES)) % len(OPENERS)]
    dialogue = DIALOGUES[(seed // (len(TALES) * len(OPENERS))) % len(DIALOGUES)]

    world = World(place=meta["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="young quester",
        meters={"distance_to_tomb": 4.0, "distance_to_dinette": 9.0},
        memes={"courage": 0.7, "wonder": 0.8},
        location=params.place,
    )
    companion = Entity(
        id=params.companion,
        kind="character",
        label="trusted companion",
        meters={"distance_to_tomb": 4.0, "distance_to_dinette": 9.0},
        memes={"care": 0.9, "wonder": 0.6},
        location=params.place,
    )
    tomb = Entity(
        id="tomb",
        kind="landmark",
        label="old stone tomb",
        meters={"height": 1.4},
        memes={"mystery": 1.0, "disturbed": 0.0},
        location=params.place,
    )
    dinette = Entity(
        id="dinette",
        kind="place",
        label="tiny garden dinette",
        meters={"table_height": 0.7},
        memes={"welcome": 0.8},
        location=params.place,
    )
    major = Entity(
        id="major",
        kind="character",
        label=params.major,
        meters={"distance_to_hero": 12.0},
        memes={"trust": 0.5},
        location=params.place,
    )
    world.entities = {e.id: e for e in (hero, companion, tomb, dinette, major)}

    world.say(opener)
    world.say(f"{tale['opening']} {params.hero}, a {params.mood} child, stood in {world.place} with {params.companion}.")
    world.say(f"{params.major} watched from the garden path, holding a lantern and waiting for the old words to make sense.")
    world.say("The stone carried this rhyme: " + tale["rhyme"])

    world.para()
    world.say(f"{params.companion} {tale['mistake']}.")
    world.say(f"'{dialogue[0]}' {params.companion} asked. '{dialogue[1]}' answered {params.hero}.")
    world.say(f"They did not touch the sealed tomb. Instead, they noticed that {tale['clue']}.")
    world.say(f"Then they understood that {tale['turn']}")

    world.para()
    world.say(f"Together, {params.hero} and {params.companion} {tale['action']}.")
    world.say(f"{params.major} listened as they explained every step, and {tale['result']}.")
    world.say(f"The rhyme had changed from a frightening puzzle into a helpful path.")
    world.say(tale["ending"])
    world.say(f"The lesson was simple: {tale['lesson'].capitalize()}.")

    hero.meters["distance_to_tomb"] = 0.0
    hero.meters["distance_to_dinette"] = 0.0
    companion.meters["distance_to_tomb"] = 0.0
    companion.meters["distance_to_dinette"] = 0.0
    hero.memes["courage"] = 1.0
    companion.memes["care"] = 1.0
    major.memes["trust"] = 1.0
    tomb.memes["disturbed"] = 0.0
    dinette.memes["welcome"] = 1.0

    world.trace = [
        f"rhyme_received:{tale['rhyme']}",
        f"misunderstanding:{tale['mistake']}",
        f"clue_observed:{tale['clue']}",
        f"meaning_corrected:{tale['turn']}",
        f"resolved:{tale['result']}",
    ]
    world.facts = {
        "place": params.place,
        "setting": meta["setting"],
        "tomb": "old stone tomb",
        "dinette": "tiny garden dinette",
        "major": params.major,
        "rhyme": tale["rhyme"],
        "misunderstanding": tale["mistake"],
        "clue": tale["clue"],
        "resolution": tale["result"],
        "lesson": tale["lesson"],
    }

    prompts = [
        f"Write a fairy tale in {meta['setting']} involving a tomb, a dinette, and {params.major}.",
        f"Use a rhyme to show how {params.hero} and {params.companion} solve a safe mystery near the tomb.",
        "Tell a gentle story in which careful listening changes a frightening guess into a helpful discovery.",
    ]
    story_qa = [
        QAItem(
            question=f"What rhyme did {params.hero} and {params.companion} find?",
            answer=f"They found the rhyme, “{tale['rhyme']}” It gave them a direction instead of asking them to disturb the tomb.",
        ),
        QAItem(
            question="What did the first guess get wrong?",
            answer=f"The first guess {tale['mistake']}. The children later checked the whole rhyme and the nearby clues.",
        ),
        QAItem(
            question="What clue changed their minds?",
            answer=f"They noticed that {tale['clue']}. That detail showed where the rhyme was really pointing.",
        ),
        QAItem(
            question=f"How did {params.major} help?",
            answer=f"{params.major} listened as the children explained every step, and their careful solution showed that the mystery could be solved without opening the sealed tomb.",
        ),
        QAItem(
            question="What lesson did the tale teach?",
            answer=f"It taught that {tale['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a tomb?",
            answer="A tomb is a place where a dead person may be respectfully remembered and laid to rest.",
        ),
        QAItem(
            question="What is a dinette?",
            answer="A dinette is a small dining area or a little table where people can share food.",
        ),
        QAItem(
            question="Why can a rhyme be useful in a fairy tale?",
            answer="A rhyme can make a clue memorable while hiding a direction, warning, or promise inside its playful words.",
        ),
        QAItem(
            question="What does major mean in this story?",
            answer="Major is the title of an important officer who helps watch over the kingdom and its people.",
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
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.kind}; location={entity.location}; "
                f"meters={entity.meters}; memes={entity.memes}"
            )
        for item in sample.world.trace:
            print(f"  event: {item}")
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


CURATED = [
    StoryParams("moonlit orchard", "Luna", "Pip", "Major Rowan", "brave"),
    StoryParams("silver castle garden", "Mara", "Elio", "Major Bell", "kind"),
    StoryParams("moonlit orchard", "Iris", "Toby", "Major Finch", "patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show has_feature/2.\n#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show has_feature/2.\n#show valid_story/1."))
        print(asp.atoms(model, "has_feature"))
        print(asp.atoms(model, "valid_story"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            if args.seed is not None:
                params.seed = args.seed + index
            sample = generate(params)
            if sample.story in seen:
                continue
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
