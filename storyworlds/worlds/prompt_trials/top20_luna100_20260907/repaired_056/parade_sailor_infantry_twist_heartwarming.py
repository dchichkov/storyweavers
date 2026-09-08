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
        "setting": "Harbor Square",
        "landmark": "a blue lighthouse",
        "surface": "sun-warmed cobblestones",
    },
    "willow avenue": {
        "setting": "Willow Avenue",
        "landmark": "a row of bright paper flags",
        "surface": "a clean road beneath rustling trees",
    },
    "market green": {
        "setting": "Market Green",
        "landmark": "a fountain full of floating flowers",
        "surface": "soft grass beside the market stalls",
    },
    "old station": {
        "setting": "the Old Station",
        "landmark": "a clock with golden hands",
        "surface": "polished stones by the waiting platform",
    },
}

CHAR_NAMES = ("Luna", "Mara", "Nico", "Suri", "Theo", "Pip", "Iris", "Jasper")
MOODS = ("hopeful", "careful", "cheerful", "patient", "curious")

CASES = (
    {
        "name": "the quiet drum",
        "opening": "The town had practiced its welcome parade for weeks, but one sailor was missing from the first row.",
        "problem": "A young sailor named Tomas had returned from a long voyage, yet he stood behind the crowd with his head bowed.",
        "wrong_idea": "Luna thought Tomas was too shy to join the parade.",
        "clue": "His polished boots were ready, but one brass button on his coat was wrapped in a tiny blue ribbon.",
        "twist": "Tomas was not waiting for courage; he was waiting for his little sister, who marched with the infantry band and had promised to surprise him.",
        "action": "Luna and her friend followed the ribbon to the band tent and invited the girl to lead Tomas into the square.",
        "result": "the sailor stepped forward when he heard his sister's drumbeat, and the whole parade made room for them together.",
        "ending": "When the drums began, Tomas lifted his sister onto his shoulders, and the parade moved beneath a shining sea of flags.",
        "lesson": "quietness can hide love, planning, or a surprise rather than fear",
        "sounds": ("tap", "rat-a-tat", "cheer"),
    },
    {
        "name": "the borrowed flag",
        "opening": "The welcome parade was ready to begin when the infantry company discovered that its oldest flag had vanished.",
        "problem": "The flag mattered because it had traveled with the town's sailors through storms and homecomings.",
        "wrong_idea": "Luna guessed that a gust of wind had carried it into the harbor.",
        "clue": "A trail of yellow thread led from the flagpole to a basket beside the children's craft table.",
        "twist": "The flag had not blown away at all; a group of children had borrowed it to mend a torn corner before the parade.",
        "action": "Luna asked the children to bring the flag back and helped them stitch the corner with the yellow thread.",
        "result": "the repaired flag flew at the front, and the children marched proudly behind it.",
        "ending": "The sailors saluted, the infantry stepped in time, and the little menders waved from the safest place in the parade.",
        "lesson": "a missing object may be safe with a helper who is trying to care for it",
        "sounds": ("flutter", "snip", "clap"),
    },
    {
        "name": "the last place in line",
        "opening": "At sunrise, the parade captain counted every sailor and infantry marcher twice.",
        "problem": "There was one empty place beside the town's oldest sailor, Captain Vale.",
        "wrong_idea": "Luna thought the captain had forgotten the parade route.",
        "clue": "Captain Vale kept glancing toward the bakery, where a warm loaf sat beside a small pair of boots.",
        "twist": "He was saving the place for a bakery helper who had cared for his dog while he was away at sea.",
        "action": "Luna carried the loaf to the bakery door and asked the helper to join the waiting line.",
        "result": "Captain Vale's empty place filled with the friend he had hoped to thank.",
        "ending": "The old sailor marched slowly, smiling beside the baker's helper as the parade passed the ringing harbor bells.",
        "lesson": "an empty place can be an invitation waiting for the right person",
        "sounds": ("bell", "shuffle", "ding"),
    },
    {
        "name": "the backwards march",
        "opening": "The infantry band began the parade with a bright tune, but one sailor kept marching backward.",
        "problem": "Everyone worried that the sailor had forgotten the steps and might bump into the float behind him.",
        "wrong_idea": "Luna decided he was trying to make the parade silly.",
        "clue": "The sailor's eyes stayed on a small red wagon carrying a covered bundle.",
        "twist": "He was walking backward so he could guide his elderly neighbor safely over the uneven stones.",
        "action": "Luna asked the band to slow the tune and helped the neighbor hold the wagon's handle.",
        "result": "the sailor could face forward again, and the neighbor rode comfortably at the heart of the parade.",
        "ending": "The music swelled as the wagon rolled past, and the sailor's backward steps became the kindest steps anyone remembered.",
        "lesson": "an unusual action may make sense when you discover whom it protects",
        "sounds": ("toot", "step-step", "whoop"),
    },
    {
        "name": "the secret salute",
        "opening": "The parade captain announced a special salute for every sailor returning home.",
        "problem": "One young infantry marcher refused to raise his hand when the salute began.",
        "wrong_idea": "Luna worried that he did not respect the sailors.",
        "clue": "He held a paper star in his other hand and kept looking toward a hospital window.",
        "twist": "The marcher was saving his hand for a private salute to his mother, who had watched every parade from that window while recovering.",
        "action": "Luna asked the captain to pause at the window so the marcher could share both salutes.",
        "result": "the sailor received the public welcome, and the mother received the greeting meant only for her.",
        "ending": "Two hands rose at the window, and the parade continued with every heart feeling a little lighter.",
        "lesson": "respect can be shown in public and in a quiet way meant for one special person",
        "sounds": ("whistle", "rustle", "soft cheer"),
    },
    {
        "name": "the empty drum",
        "opening": "The infantry drummer tapped the opening beat, and nothing answered from the largest drum.",
        "problem": "Without its deep sound, the sailors at the back could not keep the parade's pace.",
        "wrong_idea": "Luna thought the drummer had broken the instrument.",
        "clue": "A small note was tucked inside the drum, beside a photograph of a sailor in a knitted cap.",
        "twist": "The drum was being used as a hiding place for a welcome letter written by the drummer's father, who was at sea.",
        "action": "Luna helped deliver the letter to the drummer before the band tried again.",
        "result": "The drummer's worried hands steadied, and the repaired drum led the parade with a warm boom.",
        "ending": "The beat rolled across the square, carrying one sailor's love farther than any letter could travel alone.",
        "lesson": "a pause may hold an important message that deserves attention",
        "sounds": ("tap", "boom", "hush"),
    },
    {
        "name": "the rain parade",
        "opening": "Clouds gathered over the town just as the sailors and infantry began lining up.",
        "problem": "The parade's paper decorations would melt if the rain arrived before the march was finished.",
        "wrong_idea": "Luna wanted to cancel everything at once.",
        "clue": "The sailors were carrying spare canvas, and the infantry had placed baskets beneath every awning.",
        "twist": "They had planned a shorter route beneath covered walkways so the parade could still welcome children and elders.",
        "action": "Luna helped move the signs and invited families to stand beneath the awnings.",
        "result": "the parade stayed dry enough to continue, and no one had to hurry through the storm.",
        "ending": "Rain drummed on the roofs while the parade's real music traveled safely from awning to awning.",
        "lesson": "a changed plan can preserve the joy while protecting the people who share it",
        "sounds": ("drip", "drum-drum", "laugh"),
    },
    {
        "name": "the lantern boat",
        "opening": "At dusk, the parade reached the harbor with one last lantern boat waiting on the water.",
        "problem": "The boat would not glow, so the sailors could not see the message painted along its side.",
        "wrong_idea": "Luna thought the lanterns had been forgotten at the parade shed.",
        "clue": "An infantry child held a pocket mirror and pointed it toward the lighthouse.",
        "twist": "The boat's lantern was meant to catch the lighthouse beam, and the child had discovered the missing angle.",
        "action": "Luna helped turn the boat until the beam touched its silver reflector.",
        "result": "the lantern shone, revealing a message thanking every sailor who had come home.",
        "ending": "The glowing words floated across the harbor, and the parade answered with a quiet, joyful cheer.",
        "lesson": "a small helper may notice the one detail that lets everyone's work shine",
        "sounds": ("splash", "click", "ahh"),
    },
)

OPENINGS = (
    "Luna loved parades because every person carried a story into the street.",
    "The town woke early, polishing brass and tying ribbons for the homecoming parade.",
    "There were flags in every window and warm bread in every doorway.",
    "The parade began as a simple welcome, but Luna soon noticed something unusual.",
    "Music filled the morning, and the sailors and infantry prepared to march together.",
)

DIALOGUES = (
    ("Maybe he is waiting for someone", "Then let us look for a clue, not make a guess"),
    ("Should we tell the captain", "First we should ask kindly and listen to the answer"),
    ("The parade cannot stop for one mystery", "A caring parade makes room for people who need help"),
    ("I thought I understood", "We can change our minds when new evidence arrives"),
    ("Why is that object important", "We will know more if we learn who is caring for it"),
)

ASP_RULES = r"""
kind(parade).
kind(sailor).
kind(infantry).
kind(twist).
kind(heartwarming).

feature(parade) :- kind(parade).
feature(sailor) :- kind(sailor).
feature(infantry) :- kind(infantry).
feature(twist) :- kind(twist).
feature(heartwarming) :- kind(heartwarming).

usable_place(P) :- place(P), has_parade_route(P), has_landmark(P).
story_ready(P) :- usable_place(P), has_sailor(P), has_infantry(P), has_twist(P).

place("harbor_square").
place("willow_avenue").
place("market_green").
place("old_station").

has_parade_route("harbor_square").
has_parade_route("willow_avenue").
has_parade_route("market_green").
has_parade_route("old_station").

has_landmark("harbor_square").
has_landmark("willow_avenue").
has_landmark("market_green").
has_landmark("old_station").

has_sailor("harbor_square").
has_sailor("willow_avenue").
has_sailor("market_green").
has_sailor("old_station").

has_infantry("harbor_square").
has_infantry("willow_avenue").
has_infantry("market_green").
has_infantry("old_station").

has_twist("harbor_square").
has_twist("willow_avenue").
has_twist("market_green").
has_twist("old_station").

#show story_ready/1.
#show usable_place/1.
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
    companion: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming parade storyworld about sailors, infantry, and a gentle twist.")
    ap.add_argument("--place", choices=tuple(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--companion")
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        key = place.replace(" ", "_")
        lines.extend(
            [
                asp.fact("place", key),
                asp.fact("has_parade_route", key),
                asp.fact("has_landmark", key),
                asp.fact("has_sailor", key),
                asp.fact("has_infantry", key),
                asp.fact("has_twist", key),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    py_usable = {(p.replace(" ", "_"),) for p in PLACES}
    py_ready = {(p.replace(" ", "_"),) for p in PLACES}
    model = asp.one_model(asp_program("#show usable_place/1.\n#show story_ready/1."))
    clingo_usable = set(asp.atoms(model, "usable_place"))
    clingo_ready = set(asp.atoms(model, "story_ready"))
    if clingo_usable == py_usable and clingo_ready == py_ready:
        print(f"OK: clingo gate matches Python reasoning ({len(py_ready)} story-ready places).")
        return 0
    print("MISMATCH:")
    print("usable only in clingo:", sorted(clingo_usable - py_usable))
    print("usable only in python:", sorted(py_usable - clingo_usable))
    print("ready only in clingo:", sorted(clingo_ready - py_ready))
    print("ready only in python:", sorted(py_ready - clingo_ready))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(tuple(PLACES))
    if place not in PLACES:
        raise StoryError(f"Unknown parade place: {place}.")
    hero = args.hero or rng.choice(CHAR_NAMES)
    if hero not in CHAR_NAMES:
        raise StoryError(f"Unknown hero {hero!r}; choose a name from the character registry.")
    companion = args.companion or rng.choice([name for name in CHAR_NAMES if name != hero])
    if companion not in CHAR_NAMES or companion == hero:
        raise StoryError("The hero and companion must be two different registered characters.")
    mood = args.mood or rng.choice(MOODS)
    if mood not in MOODS:
        raise StoryError(f"Unknown mood {mood!r}.")
    return StoryParams(place=place, hero=hero, companion=companion, mood=mood, seed=args.seed)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    identity = "|".join((params.place, params.hero, params.companion, params.mood))
    return int.from_bytes(hashlib.blake2b(identity.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("A parade story needs a registered place.")
    if params.hero == params.companion:
        raise StoryError("The hero and companion cannot be the same person.")

    seed = _story_seed(params)
    rng = random.Random(seed)
    case = CASES[seed % len(CASES)]
    intro = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    dialogue = DIALOGUES[(seed // (len(CASES) * len(OPENINGS))) % len(DIALOGUES)]
    place = PLACES[params.place]

    world = World(place=place["setting"])
    hero = Entity(
        id=params.hero,
        kind="character",
        label="parade helper",
        type="child",
        meters={"energy": 1.0, "distance_to_parade": 2.0},
        memes={"hope": 1.0, "care": 0.8},
        location=params.place,
    )
    companion = Entity(
        id=params.companion,
        kind="character",
        label="friend",
        type="child",
        meters={"energy": 0.9, "distance_to_parade": 2.0},
        memes={"curiosity": 1.0, "care": 0.8},
        location=params.place,
    )
    sailor = Entity(
        id="sailor",
        kind="character",
        label="returning sailor",
        type="sailor",
        meters={"distance_to_parade": 1.0},
        memes={"belonging": 0.5, "hope": 0.7},
        location=params.place,
    )
    infantry = Entity(
        id="infantry",
        kind="group",
        label="infantry band",
        type="infantry",
        meters={"distance_to_parade": 0.0},
        memes={"welcome": 1.0},
        location=params.place,
    )
    ribbon = Entity(
        id="ribbon",
        kind="object",
        label="a small blue ribbon",
        type="clue",
        meters={"distance_to_parade": 1.0},
        memes={"meaning": 0.2},
        location=params.place,
    )
    world.entities = {e.id: e for e in (hero, companion, sailor, infantry, ribbon)}

    world.say(f"{intro} In {place['setting']}, {place['landmark']} shone above {place['surface']}.")
    world.say(f"{params.hero}, a {params.mood} young helper, arrived with {params.companion} before the parade began.")
    world.say("Sailors stood beside the infantry band, ready to welcome someone home.")
    world.say(case["opening"])
    world.say(case["problem"])

    world.para()
    world.say(f"{params.hero} noticed the puzzle first. {case['wrong_idea']}")
    world.say(f"'{dialogue[0]},' {params.companion} said. '{dialogue[1]},' replied {params.hero}.")
    world.say(f"Instead of rushing, they watched carefully. {case['clue']}")
    world.say(f"Their first idea changed when they discovered the twist: {case['twist']}")

    world.para()
    world.say(f"Together, {params.hero} and {params.companion} {case['action']}")
    world.say(f"Then {case['result']}")
    world.say(f"The sailor and the infantry thanked the two friends, and the parade continued with a little more room for kindness.")
    world.say(f"The lesson was simple: {case['lesson'].capitalize()}.")
    world.say(case["ending"])

    hero.meters["distance_to_parade"] = 0.0
    companion.meters["distance_to_parade"] = 0.0
    sailor.memes["belonging"] = 1.0
    sailor.memes["relief"] = 1.0
    infantry.memes["joy"] = 1.0
    ribbon.memes["meaning"] = 1.0

    world.trace = [
        f"noticed:{case['wrong_idea']}",
        f"observed:{case['clue']}",
        f"twist:{case['twist']}",
        f"helped:{case['action']}",
        f"resolved:{case['result']}",
    ]
    world.facts = {
        "place": params.place,
        "setting": place["setting"],
        "hero": params.hero,
        "companion": params.companion,
        "case": case["name"],
        "problem": case["problem"],
        "wrong_idea": case["wrong_idea"],
        "clue": case["clue"],
        "twist": case["twist"],
        "action": case["action"],
        "result": case["result"],
        "lesson": case["lesson"],
    }

    prompts = [
        f"Write a heartwarming parade story in {place['setting']} featuring a sailor, an infantry band, and a gentle twist.",
        f"Tell how {params.hero} and {params.companion} solve {case['name']} by looking for evidence instead of guessing.",
        f"Write a child-friendly homecoming story that ends with the sailor and infantry sharing a joyful parade.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} notice during the parade?",
            answer=f"{params.hero} noticed that {case['problem']}",
        ),
        QAItem(
            question=f"What did {params.hero} first think?",
            answer=f"{params.hero} first thought that {case['wrong_idea'].rstrip('.')}.",
        ),
        QAItem(
            question="What clue changed the first idea?",
            answer=f"They noticed that {case['clue']}",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case['twist']}",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{case['action'].capitalize()} As a result, {case['result']}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized line or group that travels through a place while people watch, listen, and celebrate.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on a boat or ship and learns how to move safely across water.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work on foot as part of a military group.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the reader thought was happening, often caused by a new clue.",
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
            bits = [f"label={entity.label}", f"type={entity.type}"]
            if entity.location:
                bits.append(f"location={entity.location}")
            if entity.meters:
                bits.append(f"meters={entity.meters}")
            if entity.memes:
                bits.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.kind} {' '.join(bits)}")
        for item in sample.world.trace:
            print(f"  event: {item}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="harbor square", hero="Luna", companion="Mara", mood="hopeful", seed=11),
    StoryParams(place="willow avenue", hero="Nico", companion="Suri", mood="careful", seed=22),
    StoryParams(place="market green", hero="Theo", companion="Pip", mood="cheerful", seed=33),
    StoryParams(place="old station", hero="Iris", companion="Jasper", mood="patient", seed=44),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show usable_place/1.\n#show story_ready/1."))
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or len(sample.story_qa) < 3:
                print("MISMATCH: generated story verification failed.")
                sys.exit(1)
        print("OK: generated stories passed.")
        return

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show usable_place/1.\n#show story_ready/1."))
        print(asp.atoms(model, "usable_place"))
        print(asp.atoms(model, "story_ready"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 1)):
            local_seed = (args.seed if args.seed is not None else rng.randrange(2**31)) + index
            local_rng = random.Random(local_seed)
            params = resolve_params(args, local_rng)
            params.seed = local_seed
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
