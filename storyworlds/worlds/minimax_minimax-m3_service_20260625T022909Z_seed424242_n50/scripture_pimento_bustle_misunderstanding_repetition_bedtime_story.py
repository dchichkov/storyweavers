#!/usr/bin/env python3
"""
storyworlds/worlds/scripture_pimento_bustle_misunderstanding_repetition_bedtime_story.py
=========================================================================================

A small simulated story domain built from the seed
``scripture / pimento / bustle`` with narrative instruments
``Misunderstanding`` and ``Repetition``, told in the warm cadence
of a ``Bedtime Story``.

Premise (the seed tale this world re-tells with constraint-checked
variation):

    Once upon a time, in a small house at the edge of the orchard,
    there lived a little girl named Wren. Every evening before
    bed, Grandmother read aloud from an old, leather-bound
    scripture -- a thin volume of short parables, each tucked
    inside a paper sleeve. The scripture smelled faintly of
    pimento from the kitchen, where a pot of spiced rice was
    always on the stove.

    Tonight, the scripture opened to a parable about a bustling
    market that had grown too loud. Grandmother read the first
    line -- "The merchants argued, and the town went still" --
    and then stopped. "What do you think they argued about,
    little one?" she asked.

    Wren thought very hard. "About pimento," she said, sure of
    herself. "Because pimento makes everything a bustle -- a
    busy, warm bustle."

    Grandmother smiled. "That is a kind answer. Let us read
    again, and see."

    They read the parable three times. Each time, Wren guessed
    a different cause for the silence: first pimento, then a
    bustle of carts, then a child who had lost a coin. Each
    time, Grandmother said, "Let us read again." Each time,
    the scripture ended the same way: the merchants grew
    quiet because someone, very small, had begun to sing.

    At last Wren understood. The misunderstanding had been her
    own -- she had been filling the parable with bustle when
    the parable was, in truth, very still. She put her head on
    Grandmother's shoulder. The pot of pimento rice whispered
    on the stove. And the scripture, closed at last, kept its
    secret.

The world model encodes:

    * a HERO (a child with curiosity and a soft stubbornness)
    * a TELLER (a grandparent who reads the bedtime scripture)
    * a SCRIPTURE (the chosen parable, with its own number of
      readings and a hidden moral line)
    * a KITCHEN (a setting that may be busy or quiet, scented
      by PIMENTO and warmed by a RICE pot)
    * an ARGUED_CAUSE (the cause the child guesses, drawn from a
      small registry: pimento, bustle of carts, lost coin, song)
    * a TRUE_CAUSE (always 'song' -- the parable's quiet moral,
      never shown as the guess)

Causal rules (forward-chained):

    reading scripture  -> scripture.times_read += 1
    guessed wrong      -> hero.confusion += 1
    guess == 'song'    -> hero.understanding += 1  (the right answer)
    understanding ≥ 1  -> tells = True              (the resolution)

Narrative instruments:

    Misunderstanding -- the hero's guess diverges from the
        parable's truth, and that divergence is named in prose.
    Repetition -- the scripture is read aloud THREE times; each
        reading carries a small repetition of cadence so the
        story has the refrain-like feel of a bedtime tale.

Style: warm, image-led, gentle on the ear. Short paragraphs.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run
# directly: add the package dir (storyworlds/) to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

READINGS = 3   # the bedtime cadence -- scripture is read aloud three times


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation, with
# two numeric dimensions (meters = physical, memes = emotional).
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "place" | "book"
    type: str = "thing"            # girl, boy, grandmother, scripture, pot, ...
    label: str = ""                # short reference, e.g. "grandmother"
    phrase: str = ""               # full noun phrase, e.g. "Grandmother, in her soft blue shawl"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    scent: str = ""                # for the kitchen / pot: "pimento"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandmother", "mother", "woman"}
        male = {"boy", "grandfather", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Scripture:
    """A parable read at bedtime."""
    id: str
    title: str                  # short reference, e.g. "the parable of the market"
    opener: str                 # first line, repeated each reading
    moral: str                  # the closing line, repeated each reading
    true_cause: str            # always "song" -- the parable's quiet truth
    keyword: str = ""           # generation prompt word


@dataclass
class Cause:
    """A wrong guess the child may offer."""
    id: str                     # pimento | bustle | coin | song
    phrase: str                 # how it appears in the prose
    line: str                   # the child's spoken line
    wrong: bool = True          # song is the only non-wrong one


@dataclass
class StoryParams:
    """Per-story knobs; reproducible given these + a seed."""
    scripture: str
    name: str
    gender: str
    teller: str                 # "grandmother" | "grandfather"
    tell_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_understanding(world: World) -> list[str]:
    """A guess equal to the true cause unlocks the hero's understanding."""
    out: list[str] = []
    for actor in world.characters():
        if actor.type not in {"girl", "boy"}:
            continue
        if actor.memes["understanding"] >= THRESHOLD:
            continue
        if actor.memes["last_guess"] != world.facts.get("true_cause"):
            continue
        sig = ("understanding", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["understanding"] += 1
        actor.memes["confusion"] = 0.0
        out.append("__understanding__")
    return out


def _r_confusion(world: World) -> list[str]:
    """A wrong guess adds to the hero's confusion (the misunderstanding)."""
    out: list[str] = []
    for actor in world.characters():
        if actor.type not in {"girl", "boy"}:
            continue
        if actor.memes["confusion"] < THRESHOLD:
            continue
        sig = ("confusion", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        # Each unit of confusion is paired with a quietly-busy kitchen.
        world.facts["confused"] = True
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="confusion", apply=_r_confusion),
    Rule(name="understanding", apply=_r_understanding),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__understanding__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what counts as a reasonable bedtime story.
# ---------------------------------------------------------------------------
def wrong_causes() -> list[str]:
    """All causes except the parable's true one (the bedtime misunderstanding)."""
    return [c.id for c in CAUSES if c.id != "song"]


def pick_guess_sequence(rng: random.Random, count: int) -> list[str]:
    """A short sequence of guesses for the three readings.

    Bedtime convention: the child guesses wrong the first two times
    (the misunderstanding), then guesses right on the third (the turn).
    The specific wrong causes vary so the prose stays fresh.
    """
    wrongs = list(wrong_causes())
    rng.shuffle(wrongs)
    seq: list[str] = []
    if count <= 0:
        return seq
    if count == 1:
        return ["song"]
    # Two wrongs, then a right.
    seq.append(wrongs[0])
    if count >= 2:
        seq.append(wrongs[1] if len(wrongs) > 1 else wrongs[0])
    if count >= 3:
        seq.append("song")
    return seq[:count]


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def kitchen_detail(kitchen: Entity, bustle: bool) -> str:
    if bustle:
        return ("The kitchen behind them was a warm bustle -- a pot of "
                "pimento rice whispered on the stove, and the windows "
                "fogged with the steam of it.")
    return ("The kitchen behind them was very still. The pot of pimento "
            "rice had gone quiet on the stove, and only the smallest "
            "thread of steam rose from its lid.")


def opener_line(hero: Entity, scripture: Entity) -> str:
    return f"{hero.id} settled at {hero.pronoun('possessive')} {scripture.label_word}'s knee."


def reading_beat(world: World, hero: Entity, teller: Entity, scripture: Entity,
                 turn: int, guess_id: str) -> None:
    """One full reading: opener line, the moral, then the hero's guess."""
    scripture.meters["readings"] += 1
    if turn == 0:
        # First reading: introduce the scripture with the kitchen detail.
        world.say(
            f"The {scripture.label} opened with a small sigh of old paper. "
            f"{scripture.phrase.capitalize()} read aloud, very softly:"
        )
        world.say(f'"{scripture.opener}"')
        world.say(f'"{scripture.moral}"')
    else:
        # Repetition: a short refrain-like echo of the opener.
        world.say(f'Again, the {teller.label_word} read: "{scripture.opener}"')
        world.say(f'Again, the line that came after: "{scripture.moral}"')

    cause = CAUSES_BY_ID[guess_id]
    if cause.wrong:
        hero.memes["last_guess"] = guess_id
        hero.memes["confusion"] += 1
        world.say(
            f'"{cause.line}" {hero.id} said, sure of {hero.pronoun("object")}self. '
            f"The {teller.label_word} only smiled. \"Let us read again,\" she said."
        )
    else:
        hero.memes["last_guess"] = guess_id
        world.say(
            f'"{cause.line}" {hero.id} said, very quietly this time, as if the '
            f"answer had been waiting at the back of {hero.pronoun('possessive')} "
            f"thoughts all along."
        )
    propagate(world, narrate=False)


def resolve_beat(world: World, hero: Entity, teller: Entity, scripture: Entity,
                 kitchen: Entity) -> None:
    """The resolution: understanding clears the misunderstanding, the kitchen
    goes quiet, the scripture closes, the child rests."""
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(
        f"Then the {teller.label_word} closed the {scripture.label} with both "
        f"hands, and the room grew very still."
    )
    world.say(kitchen_detail(kitchen, bustle=False))
    world.say(
        f"{hero.id} understood at last. The parable had never been about "
        f"pimento or bustling carts at all -- it had been about a small, "
        f"quiet voice that the merchants finally heard."
    )
    world.say(
        f"{hero.id} put {hero.pronoun('possessive')} head on {hero.pronoun('possessive')} "
        f"{teller.label_word}'s shoulder. The {scripture.label} rested, closed, on "
        f"{hero.pronoun('possessive')} lap. And the pimento rice, on the stove, "
        f"kept its own small secret for the night."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(scripture: Scripture, hero_name: str, hero_type: str,
         hero_traits: list[str], teller_type: str, tell_trait: str,
         rng: random.Random) -> World:
    world = World()
    world.weather = ""
    world.facts["true_cause"] = scripture.true_cause

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + hero_traits,
        label_word="grand" + ("mother" if teller_type == "grandmother" else "father"),
    ))
    # Override label_word: this hero refers to "grandmother"/"grandfather".
    hero.label_word = "grandmother" if teller_type == "grandmother" else "grandfather"

    teller = world.add(Entity(
        id="Teller", kind="character", type=teller_type,
        label="the grandmother" if teller_type == "grandmother" else "the grandfather",
        label_word="grandmother" if teller_type == "grandmother" else "grandfather",
        traits=[tell_trait, "patient"],
    ))
    scripture_e = world.add(Entity(
        id="scripture", kind="book", type="scripture",
        label=scripture.id == "market" and "scripture" or "scripture",
        label_word="grandmother" if teller_type == "grandmother" else "grandfather",
        phrase=scripture.title,
    ))
    # Patch: ensure scripture.label is the short noun used in prose.
    scripture_e.label = "scripture"
    scripture_e.phrase = scripture.title

    kitchen = world.add(Entity(
        id="kitchen", kind="place", type="kitchen",
        label="kitchen", phrase="the small kitchen",
        scent="pimento",
    ))
    pot = world.add(Entity(
        id="pot", kind="thing", type="pot",
        label="pot", phrase="the pot of pimento rice",
        owner=teller.id, scent="pimento",
    ))

    # Act 1 -- setup.
    world.say(
        f"In a small house at the edge of the orchard, {hero.id} and "
        f"{hero.pronoun('possessive')} {teller.label_word} were getting "
        f"ready for bed."
    )
    world.say(kitchen_detail(kitchen, bustle=True))
    world.say(
        f"{teller.phrase.capitalize()} took the old {scripture_e.label} from "
        f"its shelf. It smelled faintly of pimento from the kitchen."
    )
    world.say(opener_line(hero, scripture_e))

    # Act 2 -- the three readings (Misunderstanding + Repetition).
    world.para()
    guess_seq = pick_guess_sequence(rng, READINGS)
    for turn, gid in enumerate(guess_seq):
        reading_beat(world, hero, teller, scripture_e, turn, gid)

    # Act 3 -- resolution.
    world.para()
    resolve_beat(world, hero, teller, scripture_e, kitchen)

    world.facts.update(
        hero=hero, teller=teller, scripture=scripture, scripture_e=scripture_e,
        kitchen=kitchen, pot=pot, guesses=guess_seq,
        resolved=hero.memes["understanding"] >= THRESHOLD,
        confused=hero.memes["confusion"] >= THRESHOLD,
        readings=scripture_e.meters["readings"],
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SCRIPTURES = {
    "market": Scripture(
        id="market",
        title="the parable of the market",
        opener="The merchants argued, and the town went still.",
        moral="And in the stillness, a small voice began to sing.",
        true_cause="song",
        keyword="scripture",
    ),
    "orchard": Scripture(
        id="orchard",
        title="the parable of the orchard",
        opener="The apples ripened, and the birds fell quiet.",
        moral="And in the quiet, one small bird began to sing.",
        true_cause="song",
        keyword="scripture",
    ),
    "river": Scripture(
        id="river",
        title="the parable of the river",
        opener="The boats grew still, and the oars went quiet.",
        moral="And in the quiet, a child at the bank began to sing.",
        true_cause="song",
        keyword="scripture",
    ),
}

CAUSES = [
    Cause(
        id="pimento",
        phrase="pimento",
        line="About pimento, of course. Because pimento makes everything a bustle -- a busy, warm bustle.",
    ),
    Cause(
        id="bustle",
        phrase="a bustle of carts",
        line="About a bustle of carts in the square -- that is why the merchants could not hear.",
    ),
    Cause(
        id="coin",
        phrase="a lost coin",
        line="About a child who had lost a coin. The merchants were looking for it.",
    ),
    Cause(
        id="song",
        phrase="a song",
        line="About a song. A small one, that the merchants finally heard.",
        wrong=False,
    ),
]
CAUSES_BY_ID = {c.id: c for c in CAUSES}

GIRL_NAMES = ["Wren", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively", "thoughtful"]
TELL_TRAITS = ["patient", "soft-voiced", "gentle", "warm", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(scripture, name, gender) triples that pass the bedtime constraint.

    The constraint here is gentle: every scripture pairs with every child
    name/gender, and the storyteller can be either grandmother or grandfather.
    """
    out: list[tuple[str, str, str]] = []
    for sid in SCRIPTURES:
        for gender in ("girl", "boy"):
            names = GIRL_NAMES if gender == "girl" else BOY_NAMES
            for n in names:
                out.append((sid, n, gender))
    return out


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, scripture, teller = f["hero"], f["scripture"], f["teller"]
    return [
        f'Write a short bedtime story for a 3-to-5-year-old on the theme '
        f'"a small misunderstanding, a quiet truth" that includes the word '
        f'"scripture".',
        f"Tell a gentle bedtime story where {hero.id} listens to "
        f"{teller.label_word} read a scripture aloud three times, and only "
        f"on the third reading understands what the parable is really about.",
        f'Write a simple bedtime story that uses the word "pimento" and '
        f"ends with a child resting against a grandparent while the kitchen "
        f"goes still.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, scripture, teller = f["hero"], f["scripture"], f["teller"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    guesses = f["guesses"]
    final_guess = guesses[-1] if guesses else "song"
    final_phrase = CAUSES_BY_ID[final_guess].phrase

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who reads the scripture to {hero.id} before bed in the small "
                f"house at the edge of the orchard?"
            ),
            answer=(
                f"{pos.capitalize()} {teller.label_word} reads the scripture to "
                f"{hero.id}. The scripture is an old, leather-bound book of "
                f"short parables, and it smells faintly of pimento from the "
                f"kitchen."
            ),
        ),
        QAItem(
            question=(
                f"How many times does {teller.label_word} read the scripture "
                f"aloud to {hero.id} in the bedtime story?"
            ),
            answer=(
                f"{teller.label_word.capitalize()} reads the scripture aloud "
                f"three times. The same opener and the same moral line come "
                f"back each time, like a small refrain."
            ),
        ),
        QAItem(
            question=(
                f"What was the misunderstanding {hero.id} had about the "
                f"{scripture.title} on the first two readings?"
            ),
            answer=(
                f"At first {hero.id} thought the parable was about pimento, "
                f"and then about a bustle of carts -- both busy, warm answers. "
                f"Each time, {teller.label_word} only smiled and said, "
                f'"Let us read again."'
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} finally understand about the "
                f"{scripture.title} on the third reading?"
            ),
            answer=(
                f"On the third reading, {hero.id} guessed that the merchants "
                f"had gone still because of a song -- a small, quiet voice "
                f"they finally heard. That was the truth of the parable."
            ),
        ),
        QAItem(
            question=(
                f"How did the kitchen change between the busy beginning and "
                f"the quiet end of the bedtime story with {hero.id} and "
                f"{pos} {teller.label_word}?"
            ),
            answer=(
                f"At the start, the kitchen was a warm bustle, with pimento "
                f"rice whispering on the stove. At the end, the kitchen went "
                f"very still -- only a thin thread of steam rose from the pot."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"scripture", "pimento", "bustle", "bedtime", "misunderstanding",
            "repetition", "song"}
    out: list[QAItem] = []
    if "scripture" in tags:
        out.extend([
            QAItem(
                question="What is a scripture?",
                answer=(
                    "A scripture is a holy or sacred book of stories and "
                    "teachings, often read slowly and aloud."
                ),
            ),
            QAItem(
                question="Why do people read scripture at bedtime?",
                answer=(
                    "Reading scripture at bedtime is a calm, gentle ritual. "
                    "The soft voice and the short stories help a child feel "
                    "safe and ready to sleep."
                ),
            ),
        ])
    if "pimento" in tags:
        out.extend([
            QAItem(
                question="What is pimento?",
                answer=(
                    "Pimento is a small, sweet red pepper. It is dried and "
                    "ground into a soft, warm spice that smells like a "
                    "kitchen in autumn."
                ),
            ),
            QAItem(
                question="Why might a kitchen smell of pimento?",
                answer=(
                    "A kitchen smells of pimento when a pot of spiced rice "
                    "or stew is cooking on the stove. The steam carries the "
                    "warm, sweet scent through the whole house."
                ),
            ),
        ])
    if "bustle" in tags:
        out.extend([
            QAItem(
                question="What does bustle mean?",
                answer=(
                    "Bustle means busy, gentle motion -- the way a kitchen "
                    "looks when pots are on the stove and people are moving "
                    "about, helping each other."
                ),
            ),
            QAItem(
                question="What is the opposite of a bustle?",
                answer=(
                    "The opposite of a bustle is stillness -- a quiet room "
                    "where nothing is moving and you can hear your own breath."
                ),
            ),
        ])
    if "misunderstanding" in tags:
        out.extend([
            QAItem(
                question="What is a misunderstanding?",
                answer=(
                    "A misunderstanding is when two people think the same "
                    "thing means different things. It is usually fixed by "
                    "asking again, or by listening one more time."
                ),
            ),
        ])
    if "repetition" in tags:
        out.extend([
            QAItem(
                question="What is repetition in a story?",
                answer=(
                    "Repetition is when the same words or phrases come back "
                    "again and again. In a bedtime story it works like a "
                    "small refrain -- it helps the listener feel held."
                ),
            ),
        ])
    if "song" in tags:
        out.extend([
            QAItem(
                question="Why do small, quiet voices matter in a parable?",
                answer=(
                    "In many parables, a small, quiet voice matters because "
                    "it is the one the loud people finally hear when they "
                    "stop arguing."
                ),
            ),
        ])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.scent:
            bits.append(f"scent={e.scent}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  guesses: {world.facts.get('guesses')}")
    lines.append(f"  true_cause: {world.facts.get('true_cause')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scripture="market", name="Wren", gender="girl",
                teller="grandmother", tell_trait="patient"),
    StoryParams(scripture="orchard", name="Tim", gender="boy",
                teller="grandfather", tell_trait="soft-voiced"),
    StoryParams(scripture="river", name="Mia", gender="girl",
                teller="grandmother", tell_trait="gentle"),
    StoryParams(scripture="market", name="Ben", gender="boy",
                teller="grandmother", tell_trait="warm"),
    StoryParams(scripture="orchard", name="Zoe", gender="girl",
                teller="grandfather", tell_trait="quiet"),
]


def explain_rejection(teller: str, scripture_id: str) -> str:
    if teller not in {"grandmother", "grandfather"}:
        return (f"(No story: the storyteller must be a grandmother or a "
                f"grandfather -- '{teller}' is not a bedtime storyteller.)")
    if scripture_id not in SCRIPTURES:
        return (f"(No story: the scripture '{scripture_id}' is not in the "
                f"registry. Try one of: {', '.join(SCRIPTURES)}.)")
    return "(No story: the chosen options do not describe a bedtime story.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) twin -- a small reasonableness gate (scripture + teller +
# gender form a valid bedtime story).  Inline rules, facts emitted from the
# registries, clingo imported lazily so prose runs without it.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A scripture + a child gender + a storyteller form a valid bedtime story
% when the scripture is in the registry, the storyteller is a grandparent,
% and the child is either a girl or a boy.
valid(S, G, T) :- scripture(S), gender(G), teller(T).

% The turn: the child must guess the wrong cause before the right one.
has_misunderstanding(C) :- wrong_cause(C).
resolves(C) :- true_cause(C).
ok_story(S, G, T) :- valid(S, G, T), has_misunderstanding(C1),
                     resolves(C2), C1 != C2.
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SCRIPTURES.items():
        lines.append(asp.fact("scripture", sid))
        lines.append(asp.fact("scripture_opener", sid, s.opener))
        lines.append(asp.fact("scripture_moral", sid, s.moral))
        lines.append(asp.fact("scripture_cause", sid, s.true_cause))
    for c in CAUSES:
        lines.append(asp.fact("cause", c.id))
        if c.wrong:
            lines.append(asp.fact("wrong_cause", c.id))
        else:
            lines.append(asp.fact("true_cause", c.id))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    for t in ("grandmother", "grandfather"):
        lines.append(asp.fact("teller", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_ok_stories() -> list[tuple]:
    """Clingo's view of valid bedtime-story options."""
    import asp
    model = asp.one_model(asp_program("#show ok_story/3."))
    return sorted(set(asp.atoms(model, "ok_story")))


def asp_verify() -> int:
    """Confirm the inline ASP gate agrees with the Python valid_combos()."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
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
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: scripture, pimento, bustle -- "
                    "a small misunderstanding cleared by a quiet truth. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--scripture", choices=SCRIPTURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teller", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the 3 Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible bedtime-story set via clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.teller and args.teller not in {"grandmother", "grandfather"}:
        raise StoryError(explain_rejection(args.teller, args.scripture or "market"))
    if args.scripture and args.scripture not in SCRIPTURES:
        raise StoryError(explain_rejection(args.teller or "grandmother", args.scripture))

    combos = [c for c in valid_combos()
              if (args.scripture is None or c[0] == args.scripture)
              and (args.gender is None or c[2] == args.gender)]
    if not combos:
        raise StoryError("(No valid bedtime story matches the given options.)")

    sid, name, gender = rng.choice(sorted(combos))
    if args.name:
        name = args.name
    teller = args.teller or rng.choice(["grandmother", "grandfather"])
    tell_trait = rng.choice(TELL_TRAITS)
    return StoryParams(
        scripture=sid,
        name=name,
        gender=gender,
        teller=teller,
        tell_trait=tell_trait,
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random((params.seed or 0) ^ hash((params.scripture, params.name,
                                                   params.gender, params.teller)))
    hero_traits = [rng.choice(TRAITS), "stubborn"]
    world = tell(SCRIPTURES[params.scripture], params.name, params.gender,
                 hero_traits, params.teller, params.tell_trait, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show ok_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_ok_stories()
        print(f"{len(triples)} compatible bedtime-story options:\n")
        for sid, gender, teller in triples:
            print(f"  scripture={sid:9} gender={gender:5} teller={teller}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            header = f"### {p.name}: {p.scripture} with {p.teller}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
