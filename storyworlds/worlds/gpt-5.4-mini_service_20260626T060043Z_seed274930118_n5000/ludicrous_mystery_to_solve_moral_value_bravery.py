#!/usr/bin/env python3
"""
A small fable-style storyworld about a ludicrous mystery, a moral choice, and
the kind of bravery that means doing the right thing even when you feel small.

Seed tale:
A tiny hedgehog named Pip lives beside a quiet orchard. One morning, the village
bell is missing, and everyone assumes the loud badger did it because he is noisy
and proud. Pip does not like being in the middle of things, but the duckling
Mina notices that the bell rope is cut with neat little bites, not big claw
marks. Pip follows the clues through the orchard, finds that a squirrel has
hidden the bell in a nest because she wanted the sound all to herself, and must
decide whether to blame the badger or speak the truth. Pip chooses honesty,
returns the bell, and learns that bravery can be gentle.

World model:
- Entities have physical meters and emotional memes.
- Mystery state is driven by clues, suspicion, concealment, and discovery.
- Moral value is modeled as honesty / fairness / blame / gratitude.
- Bravery is modeled as fear vs. action, especially when speaking up would be
  awkward or unpopular.

The prose is fable-like: concrete, short, and causal.
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
# Entities and world
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("hiddenness", "distance", "damage"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "bravery", "honesty", "suspicion", "relief",
                   "pride", "kindness", "guilt", "gratitude", "curiosity"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "duck", "hen", "mouse", "sheep", "fox"}
        male = {"boy", "badger", "dog", "rooster", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        return World(
            place=self.place,
            weather=self.weather,
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Story knobs
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    culprit: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    missing_place: str
    clue_kind: str
    clue_phrase: str
    reveal_phrase: str
    suspicious_about: str
    value: str
    moral: str


@dataclass
class CharacterSpec:
    type: str
    label: str
    phrase: str
    traits: list[str] = field(default_factory=list)


SETTINGS = {
    "orchard": "the orchard",
    "hill": "the hill",
    "riverbank": "the riverbank",
    "meadow": "the meadow",
}

CHARACTERS = {
    "hedgehog": CharacterSpec("hedgehog", "Pip", "a tiny hedgehog", ["small", "careful"]),
    "duckling": CharacterSpec("duck", "Mina", "a bright duckling", ["quick", "curious"]),
    "badger": CharacterSpec("badger", "Bram", "a loud badger", ["noisy", "proud"]),
    "squirrel": CharacterSpec("squirrel", "Sella", "a clever squirrel", ["nimble", "secretive"]),
    "fox": CharacterSpec("fox", "Fenn", "a fox with a soft voice", ["quiet", "watchful"]),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        label="the village bell",
        phrase="the shiny bell from the green post",
        missing_place="the bell post",
        clue_kind="bites",
        clue_phrase="tiny bite marks on the rope",
        reveal_phrase="hidden in a nest of leaves",
        suspicious_about="the badger",
        value="truth",
        moral="honesty",
    ),
    "jam": Mystery(
        id="jam",
        label="the strawberry jam",
        phrase="the jar of strawberry jam from the pantry shelf",
        missing_place="the pantry",
        clue_kind="crumbs",
        clue_phrase="crumbs shaped like little stars",
        reveal_phrase="pushed behind a flowerpot",
        suspicious_about="the fox",
        value="sharing",
        moral="fairness",
    ),
    "kite": Mystery(
        id="kite",
        label="the red kite",
        phrase="the bright red kite from the barn hook",
        missing_place="the barn",
        clue_kind="string",
        clue_phrase="a long string caught on a thorn",
        reveal_phrase="tied high in a tree",
        suspicious_about="the squirrel",
        value="care",
        moral="kindness",
    ),
}

MORAL_WORDS = ["honesty", "fairness", "kindness"]
PLACES = list(SETTINGS.keys())


# ---------------------------------------------------------------------------
# Reasonable model
# ---------------------------------------------------------------------------
def mystery_reasonable(mystery: Mystery) -> bool:
    return bool(mystery.clue_phrase and mystery.reveal_phrase and mystery.moral in MORAL_WORDS)


def valid_combo(place: str, mystery_id: str, hero_type: str, friend_type: str) -> bool:
    if place == "orchard" and mystery_id == "bell":
        return True
    if place == "hill" and mystery_id == "kite":
        return True
    if place == "riverbank" and mystery_id == "jam":
        return True
    if place == "meadow" and mystery_id in {"bell", "kite"}:
        return True
    return False


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% place(P). mystery(M). hero_type(T). friend_type(T).
% compatible(P,M) means the mystery can plausibly happen there.
% clue(M,C) and reveal(M,R) describe the trail and the answer.
% moral(M,W) names the value the story teaches.
% suspicious(M,S) marks who people first blame.
% reasonable_story(P,M) is the declarative twin of valid_combo().

compatible(orchard, bell).
compatible(hill, kite).
compatible(riverbank, jam).
compatible(meadow, bell).
compatible(meadow, kite).

reasonable_story(P,M) :- compatible(P,M), clue(M,_), reveal(M,_), moral(M,_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue_kind))
        lines.append(asp.fact("reveal", mid, m.reveal_phrase))
        lines.append(asp.fact("moral", mid, m.moral))
        lines.append(asp.fact("suspicious", mid, m.suspicious_about))
    for t in CHARACTERS:
        lines.append(asp.fact("hero_type", t))
        lines.append(asp.fact("friend_type", t))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/2."))
    return sorted(set(asp.atoms(model, "reasonable_story")))

def asp_verify() -> int:
    py = {(p, m) for p in SETTINGS for m in MYSTERIES if valid_combo(p, m, "hedgehog", "duckling")}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python only:", sorted(py - asp_set))
    print("asp only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like world of mystery, moral choice, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=list(MYSTERIES))
    ap.add_argument("--hero", choices=list(CHARACTERS))
    ap.add_argument("--friend", choices=list(CHARACTERS))
    ap.add_argument("--culprit", choices=list(CHARACTERS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.place and not valid_combo(args.place, args.mystery, "", ""):
        raise StoryError("That place and mystery do not fit this fable world.")
    combos = [(p, m) for p in PLACES for m in MYSTERIES if valid_combo(p, m, "", "")]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No reasonable story matches those choices.")
    place, mystery_id = rng.choice(sorted(combos))
    mystery = MYSTERIES[mystery_id]
    hero = args.hero or "hedgehog"
    friend = args.friend or "duckling"
    culprit = args.culprit or {"bell": "squirrel", "jam": "fox", "kite": "badger"}[mystery_id]
    if hero == culprit:
        raise StoryError("The hero cannot also be the culprit in this story.")
    if friend == culprit:
        raise StoryError("The friend cannot also be the culprit in this story.")
    return StoryParams(place=place, mystery=mystery_id, culprit=culprit, hero=hero, hero_type=CHARACTERS[hero].type,
                       friend=friend, friend_type=CHARACTERS[friend].type)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    mystery = MYSTERIES[params.mystery]
    world = World(place=SETTINGS[params.place], weather="clear")
    hero_spec = CHARACTERS[params.hero]
    friend_spec = CHARACTERS[params.friend]
    culprit_spec = CHARACTERS[params.culprit]

    hero = world.add(Entity(id="hero", kind="character", type=hero_spec.type, label=hero_spec.label, phrase=hero_spec.phrase))
    friend = world.add(Entity(id="friend", kind="character", type=friend_spec.type, label=friend_spec.label, phrase=friend_spec.phrase))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_spec.type, label=culprit_spec.label, phrase=culprit_spec.phrase))
    prize = world.add(Entity(id="prize", kind="thing", type="thing", label=mystery.label, phrase=mystery.phrase))

    world.facts.update(hero=hero, friend=friend, culprit=culprit, prize=prize, mystery=mystery, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    culprit: Entity = f["culprit"]
    prize: Entity = f["prize"]
    mystery: Mystery = f["mystery"]
    params: StoryParams = f["params"]

    hero.memes["curiosity"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"In {world.place}, there lived {hero.phrase} named {hero.label} who loved small questions and quiet paths."
    )
    world.say(
        f"One bright morning, {mystery.phrase} was gone, and everyone in {world.place} began to whisper about {mystery.suspicious_about}."
    )

    world.para()
    friend.memes["curiosity"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"{friend.label} pointed to {mystery.clue_phrase}, which did not look like a big paw-print or a harsh shove."
    )
    world.say(
        f"{hero.label} felt a flutter of fear, because speaking carefully is harder than guessing loudly."
    )
    hero.memes["bravery"] += 1

    world.para()
    if mystery.id == "bell":
        world.say(
            f"{hero.label} followed the soft clues past the berry bushes and under the low roots of the old apple tree."
        )
    elif mystery.id == "jam":
        world.say(
            f"{hero.label} followed the crumbs past the pantry door and around the watering can by the porch."
        )
    else:
        world.say(
            f"{hero.label} followed the string past the barn wall and up the hill where the wind played tricks."
        )
    world.say(
        f"There, {mystery.reveal_phrase}, {culprit.label} had tucked away {prize.it()} for {culprit.pronoun('possessive')} own delight."
    )

    world.para()
    culprit.memes["guilt"] += 1
    culprit.memes["suspicion"] += 1
    hero.memes["honesty"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.label} could have blamed {mystery.suspicious_about} and let the village shout, but {hero.pronoun()} chose the truer road."
    )
    world.say(
        f"{hero.label} said, \"The clues show who hid {prize.it()}. It was not {mystery.suspicious_about}; it was {culprit.label}.\""
    )
    world.say(
        f"The villagers grew quiet, and then the truth made them kinder."
    )

    world.para()
    culprit.memes["guilt"] -= 0.5
    culprit.memes["gratitude"] += 1
    hero.memes["relief"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"{culprit.label} returned {prize.it()} at once, and {mystery.value} replaced the silly guesswork."
    )
    world.say(
        f"At sunset, {hero.label} stood small but steady beneath the bell post, learning that bravery can be gentle when it tells the truth."
    )
    world.facts["resolved"] = True
    world.facts["ending"] = f"{prize.label} returned; truth chosen; {mystery.moral} learned."


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(sample: StorySample) -> list[str]:
    f = sample.world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    return [
        f'Write a fable for a young child about a "{mystery.id}" mystery, a brave choice, and a moral lesson in {mystery.moral}.',
        f"Tell a short story where {hero.label} follows clues, avoids a false blame, and learns that bravery can be quiet.",
        f"Write a child-friendly fable that includes the word 'ludicrous' and ends with the truth being returned to the village.",
    ]


def story_qa(sample: StorySample) -> list[QAItem]:
    f = sample.world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    culprit: Entity = f["culprit"]
    params: StoryParams = f["params"]
    place = SETTINGS[params.place]
    return [
        QAItem(
            question=f"What was missing in {place}?",
            answer=f"{mystery.label} was missing, and that made everyone in {place} curious.",
        ),
        QAItem(
            question=f"What clue helped {friend.label} and {hero.label} solve the mystery?",
            answer=f"They found {mystery.clue_phrase}, which was a careful clue and not a wild guess.",
        ),
        QAItem(
            question=f"Who hid the missing thing?",
            answer=f"{culprit.label} hid it, even though the first blame fell on {mystery.suspicious_about}.",
        ),
        QAItem(
            question=f"What moral did {hero.label} learn?",
            answer=f"{hero.label} learned {mystery.moral}, because telling the truth was the brave thing to do.",
        ),
    ]


def world_knowledge_qa(sample: StorySample) -> list[QAItem]:
    f = sample.world.facts
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question="What does brave mean?",
            answer="Brave means doing what is right or needed even when you feel scared.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not know yet, so you look for clues and think carefully.",
        ),
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth and not pretending something false is true.",
        ),
        QAItem(
            question="Why can blaming the wrong animal be unkind?",
            answer="Blaming the wrong animal can hurt feelings and hide the real answer, so it is better to be fair.",
        ),
        QAItem(
            question="What does ludicrous mean?",
            answer="Ludicrous means so silly or strange that it almost makes people laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"facts: {world.facts.get('ending', '')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    story = world.render()
    sample = StorySample(
        params=params,
        story=story,
        prompts=prompts(StorySample(params=params, story=story, world=world)),
        story_qa=story_qa(StorySample(params=params, story=story, world=world)),
        world_qa=world_knowledge_qa(StorySample(params=params, story=story, world=world)),
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="orchard", mystery="bell", culprit="squirrel", hero="hedgehog", hero_type="hedgehog", friend="duckling", friend_type="duck"),
        StoryParams(place="riverbank", mystery="jam", culprit="fox", hero="duckling", hero_type="duck", friend="hedgehog", friend_type="hedgehog"),
        StoryParams(place="hill", mystery="kite", culprit="badger", hero="hedgehog", hero_type="hedgehog", friend="duckling", friend_type="duck"),
        StoryParams(place="meadow", mystery="bell", culprit="squirrel", hero="duckling", hero_type="duck", friend="hedgehog", friend_type="hedgehog"),
    ]


def asp_valid_story_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/2."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_story_combos()
        print(f"{len(combos)} compatible story combos:")
        for p, m in combos:
            print(f"  {p:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            rng = random.Random(seed)
            i += 1
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
