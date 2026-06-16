#!/usr/bin/env python3
"""
Journey Tales Generator

Generate short scripted Journey-style stories with no runtime LLMs and no
external dependencies. The story shapes are inspired by TinyStories kernels like:

    Journey(hero, companion=..., destination=..., process=..., outcome=...)
    Journey(hero, state=Routine(...), catalyst=..., conflict=..., transformation=...)
    Journey(hero, process=Walk + Discover + Return, insight=...)

Run this file to print 1,000 unique stories separated by four newlines.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass, field
from typing import Callable


# =============================================================================
# SMALL WORLD MODEL
# =============================================================================


@dataclass(frozen=True)
class Memeplex:
    name: str
    weight: float = 1.0

    def __truediv__(self, amount: float) -> "Memeplex":
        return Memeplex(self.name, self.weight / amount)


@dataclass
class Character:
    name: str
    kind: str
    traits: tuple[str, ...]
    gender: str = "neutral"
    tags: frozenset[str] = frozenset()
    memes: dict[str, float] = field(default_factory=dict)

    @property
    def subject(self) -> str:
        if self.gender == "girl":
            return "she"
        if self.gender == "boy":
            return "he"
        if "group" in self.tags:
            return "they"
        return "it"

    @property
    def object(self) -> str:
        if self.gender == "girl":
            return "her"
        if self.gender == "boy":
            return "him"
        if "group" in self.tags:
            return "them"
        return "it"

    @property
    def possessive(self) -> str:
        if self.gender == "girl":
            return "her"
        if self.gender == "boy":
            return "his"
        if "group" in self.tags:
            return "their"
        return "its"

    @property
    def intro_noun(self) -> str:
        if self.kind in {"girl", "boy", "child"}:
            return f"little {self.kind}"
        return self.kind

    def add_meme(self, meme: Memeplex) -> None:
        self.memes[meme.name] = self.memes.get(meme.name, 0.0) + meme.weight


@dataclass(frozen=True)
class Place:
    name: str
    prep: str
    tags: frozenset[str]

    @property
    def phrase(self) -> str:
        return f"{self.prep} {self.name}"


@dataclass(frozen=True)
class Route:
    name: str
    steps: tuple[str, ...]
    tags: frozenset[str]


@dataclass
class JourneyWorld:
    hero: Character
    origin: Place
    destination: Place
    facts: set[str] = field(default_factory=set)
    carriers: dict[str, dict[str, float]] = field(default_factory=dict)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)

    def embed(self, carrier: str, meme: Memeplex) -> None:
        self.carriers.setdefault(carrier, {})
        self.carriers[carrier][meme.name] = self.carriers[carrier].get(meme.name, 0.0) + meme.weight
        if carrier == self.hero.name:
            self.hero.add_meme(meme)


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str = ""
    follow_up_answer: str = ""


# =============================================================================
# VOCABULARY
# =============================================================================


BOY_NAMES = (
    "Tim", "Ben", "Max", "Sammy", "Leo", "Jack", "Milo", "Noah",
    "Finn", "Theo", "Owen", "Nico", "Eli", "Toby",
)
GIRL_NAMES = (
    "Lily", "Sue", "Mia", "Anna", "Ruby", "Zoe", "Clara", "Lucy",
    "Ivy", "Nina", "Ella", "Maya", "Rose", "Violet",
)
ANIMAL_NAMES = (
    "Bobo", "Spot", "Pip", "Nibbles", "Teddy", "Sunny", "Coco",
    "Pebble", "Poppy", "Daisy", "Red", "Blue",
)

CHILD_TRAITS = (
    "curious", "playful", "careful", "brave", "gentle", "eager",
    "organized", "hopeful", "kind", "quiet", "excited", "patient",
)
ANIMAL_TRAITS = (
    "friendly", "small", "restless", "quick", "happy", "curious",
    "helpful", "furry", "bright", "sleepy", "hungry", "loyal",
)

PLACES = (
    Place("home", "at", frozenset({"home", "safe", "inside"})),
    Place("park", "at the", frozenset({"outside", "play", "public"})),
    Place("garden", "in the", frozenset({"outside", "plants", "home"})),
    Place("forest", "in the", frozenset({"outside", "trees", "wild"})),
    Place("beach", "on the", frozenset({"outside", "water", "sand"})),
    Place("pond", "by the", frozenset({"outside", "water"})),
    Place("shop", "at the", frozenset({"inside", "public", "things"})),
    Place("library", "at the", frozenset({"inside", "quiet", "books"})),
    Place("school", "at", frozenset({"inside", "public", "friends"})),
    Place("hill", "on the", frozenset({"outside", "view"})),
    Place("playground", "at the", frozenset({"outside", "play", "public"})),
    Place("little bridge", "by the", frozenset({"outside", "path", "water"})),
)

ROUTES = (
    Route("zigzag path", ("followed a zigzag path", "stepped around little stones"), frozenset({"outside"})),
    Route("quiet street", ("walked down a quiet street", "looked both ways at the corner"), frozenset({"safe", "public"})),
    Route("leafy trail", ("followed a leafy trail", "listened to birds in the trees"), frozenset({"outside", "trees"})),
    Route("sandy path", ("walked over soft sand", "watched the bright water"), frozenset({"outside", "water"})),
    Route("painted hallway", ("walked down a painted hallway", "passed many small doors"), frozenset({"inside"})),
    Route("garden row", ("walked beside the flowers", "counted leaves along the way"), frozenset({"plants", "outside"})),
)

WEATHER = (
    ("rain", "dark clouds rolled in and rain began to fall", {"outside", "water"}),
    ("wind", "a strong wind pushed leaves across the path", {"outside"}),
    ("bright sun", "the sun came out and warmed the way", {"outside"}),
    ("quiet", "everything became calm and quiet", set()),
)

DISCOVERIES = ("thin wire", "new spoon", "red ball", "music box", "shiny medal", "small map", "green feather")
GIFTS = ("delicate doll", "paper flower", "tiny cake", "blue whistle", "wooden toy", "warm scarf")
ACTIVITIES = (
    ("dance", "dance"),
    ("paint pictures", "painting"),
    ("sing", "song"),
    ("sort toys", "toy sorting"),
    ("take pictures", "picture taking"),
    ("look for shells", "shell hunt"),
    ("watch the tide", "tide watching"),
)
HELP_NEEDS = ("find a lost medal", "carry a little bag", "show the safe path", "bring soft leaves", "find a quiet bench")
BAD_END_OBJECTS = ("painting", "camera", "paper hat", "little kite", "toy boat", "birthday doll")
TRIP_ACTIVITIES = (
    ("slide", "went down it slowly"),
    ("swing", "swung back and forth"),
    ("big tree", "looked up at its leaves"),
    ("quiet bench", "sat on it for a rest"),
    ("funny path", "followed its bends"),
    ("little pond", "watched the tiny ripples"),
)


# =============================================================================
# HELPERS
# =============================================================================


def article(noun: str) -> str:
    return "an" if noun.strip()[:1].lower() in "aeiou" else "a"


def cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def clean(story: str) -> str:
    lines = [line.strip() for line in story.strip().splitlines()]
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs)


def phrase(noun: str) -> str:
    if noun.startswith(("a ", "an ", "the ", "some ")):
        return noun
    if noun.endswith("s") and noun not in {"grass"}:
        return noun
    return f"{article(noun)} {noun}"


def place_object(place: Place) -> str:
    if place.name in {"home", "school"}:
        return place.name
    return f"the {place.name}"


def movement_phrase(place: Place) -> str:
    if place.name == "home":
        return "home"
    return f"to {place_object(place)}"


def toward_phrase(place: Place) -> str:
    if place.name == "home":
        return "toward home"
    return f"toward {place_object(place)}"


def choose_place(*required: str, avoid: Place | None = None) -> Place:
    choices = [p for p in PLACES if all(tag in p.tags for tag in required)]
    if avoid is not None:
        choices = [p for p in choices if p.name != avoid.name]
    return random.choice(choices or [p for p in PLACES if p != avoid] or list(PLACES))


def choose_route(origin: Place, destination: Place) -> Route:
    tags = destination.tags
    choices = [r for r in ROUTES if not r.tags or r.tags & tags]
    if "outside" in destination.tags:
        choices = [r for r in choices if "inside" not in r.tags]
    if "water" not in destination.tags:
        choices = [r for r in choices if "water" not in r.tags]
    return random.choice(choices)


def choose_bad_weather(place: Place) -> tuple[str, str, set[str]]:
    choices = [w for w in WEATHER if w[0] in {"rain", "wind"} and (not w[2] or w[2] & place.tags)]
    return random.choice(choices)


def choose_character(kind: str | None = None) -> Character:
    kind = kind or random.choice(("girl", "boy", "dog", "cat", "bird", "frog", "bear", "car"))
    if kind == "girl":
        return Character(random.choice(GIRL_NAMES), "girl", tuple(random.sample(CHILD_TRAITS, 2)), "girl", frozenset({"person", "child", "walks"}))
    if kind == "boy":
        return Character(random.choice(BOY_NAMES), "boy", tuple(random.sample(CHILD_TRAITS, 2)), "boy", frozenset({"person", "child", "walks"}))
    tags = {
        "dog": {"animal", "walks", "sniffs"},
        "cat": {"animal", "walks", "climbs"},
        "bird": {"animal", "flies"},
        "frog": {"animal", "hops", "water"},
        "bear": {"animal", "walks", "strong"},
        "car": {"vehicle", "drives"},
    }.get(kind, {"animal"})
    return Character(random.choice(ANIMAL_NAMES), kind, tuple(random.sample(ANIMAL_TRAITS, 2)), "neutral", frozenset(tags))


def choose_companion(exclude: Character | None = None) -> Character:
    companions = [
        Character("Mom", "mother", ("caring", "calm"), "girl", frozenset({"person", "adult", "walks"})),
        Character("Dad", "father", ("kind", "careful"), "boy", frozenset({"person", "adult", "walks"})),
        Character("Grandma", "grandma", ("warm", "wise"), "girl", frozenset({"person", "adult", "walks"})),
        Character("Tom", "boy", ("skeptical", "loud"), "boy", frozenset({"person", "child", "walks"})),
        Character("Sue", "girl", ("friendly", "happy"), "girl", frozenset({"person", "child", "walks"})),
        Character("Bird", "bird", ("yellow", "helpful"), "neutral", frozenset({"animal", "flies"})),
        Character("Cat", "cat", ("wise", "big"), "neutral", frozenset({"animal", "walks"})),
    ]
    if exclude is not None:
        companions = [c for c in companions if c.name != exclude.name]
    return random.choice(companions)


def intro(hero: Character, origin: Place) -> str:
    desc = f"{' '.join(hero.traits[:2])} {hero.intro_noun}".strip()
    return f"Once upon a time, there was {article(desc)} {desc} named {hero.name}. {hero.name} spent many days {origin.phrase}."


def travel_lines(hero: Character, route: Route) -> str:
    first, second = random.sample(route.steps, 2) if len(route.steps) >= 2 else (route.steps[0], route.steps[0])
    return f"{hero.name} {first}. Then {hero.subject} {second}."


def ending(world: JourneyWorld, fallback: str) -> str:
    joy = world.hero.memes.get("Joy", 0.0)
    pride = world.hero.memes.get("Pride", 0.0)
    care = world.hero.memes.get("Care", 0.0)
    confidence = world.hero.memes.get("Confidence", 0.0)
    if confidence >= 0.8:
        return f"{world.hero.name} learned that a journey can make a small heart feel brave."
    if care >= 0.8:
        return f"{world.hero.name} learned that going somewhere matters most when someone is helped."
    if pride >= 0.7:
        return f"{world.hero.name} felt proud and remembered the whole journey."
    if joy >= 0.7:
        return f"{world.hero.name} was glad for the journey and wanted to remember it."
    return fallback


def build_questions(story: str) -> list[QA]:
    """Create simple reading-comprehension questions grounded in the story text."""
    questions: list[QA] = []

    named = re.search(r"named ([A-Z][A-Za-z]+)", story)
    hero = named.group(1) if named else "the main character"
    if named:
        questions.append(QA("Who is the main character in the story?", hero))

    desc = re.search(r"there was (?:a|an) ([^.]+?) named " + re.escape(hero), story)
    if desc:
        questions.append(QA(f"What kind of character was {hero}?", desc.group(1)))

    origin = re.search(re.escape(hero) + r" spent many days ([^.]+)\.", story)
    if origin:
        questions.append(QA(f"Where did {hero} spend many days?", origin.group(1)))

    destination = re.search(r"(?:Let us go|journey|went|followed the clue) (to [^.]+?)(?:\.|$)", story)
    if destination:
        questions.append(QA("Where did the journey go?", destination.group(1)))

    trouble = re.search(r"Then trouble came\. ([^.]+)\.", story)
    if trouble:
        questions.append(QA("What trouble happened on the journey?", trouble.group(1)))

    lost = re.search(re.escape(hero) + r" loved (?:his|her|its) ([^.]*) and wanted to show it", story)
    if lost:
        questions.append(QA(f"What did {hero} bring on the journey?", lost.group(1)))

    found = re.search(r"There, (?:he|she|it|they) found (?:a|an) ([^.]+)\.", story)
    if found:
        questions.append(QA(f"What did {hero} find?", found.group(1)))

    helper = re.search(r"([A-Z][A-Za-z]+) needed someone to ([^.]+)\.", story)
    if helper:
        questions.append(QA(f"Who needed help?", helper.group(1)))
        questions.append(QA(f"What help was needed?", helper.group(2)))

    endings = list(re.finditer(re.escape(hero) + r" (learned|felt|was glad) ([^.]+)\.", story))
    if endings:
        learned = endings[-1]
        verb, answer = learned.group(1), learned.group(2)
        if verb == "learned":
            questions.append(QA(f"What did {hero} learn at the end?", answer))
        elif verb == "felt":
            questions.append(QA(f"How did {hero} feel at the end?", answer))
        else:
            questions.append(QA(f"What happened at the end?", f"{hero} was glad {answer}"))

    return enrich_questions(hero, questions[:5])


def full_answer(hero: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if lower.startswith("who is the main character"):
        return f"The main character is {answer}. The journey story follows {answer} from the beginning to the ending."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description gives the reader a first picture of {hero} before the journey starts."
    if "where did" in lower and "spend many days" in lower:
        return f"{hero} spent many days {answer}. This is the starting place before {hero} goes somewhere new."
    if "where did the journey go" in lower:
        return f"The journey went {answer}. That destination gives the trip its direction."
    if "what trouble happened" in lower:
        return f"The trouble was that {answer.lower()}. This made the journey harder and gave {hero} something to handle."
    if "bring on the journey" in lower:
        return f"{hero} brought {hero}'s {answer}. The item mattered because {hero} wanted to show it to everyone."
    if "what did" in lower and "find" in lower:
        return f"{hero} found a {answer}. Finding it is one of the important discoveries on the journey."
    if "who needed help" in lower:
        return f"{answer} needed help. That need made the journey about caring for someone else, not only traveling."
    if "what help was needed" in lower:
        return f"The help needed was to {answer}. {hero} had to pay attention and respond kindly."
    if "learn" in lower:
        return f"{hero} learned {answer}. The lesson shows how the journey changed what {hero} understood."
    if "how did" in lower and "feel" in lower:
        return f"{hero} felt {answer}. That feeling shows the emotional result of the trip."
    if "what happened at the end" in lower:
        return f"At the end, {answer}. This gives the journey a clear closing moment."
    return f"The answer is {answer}. This detail is stated in the story."


def follow_up_for(hero: str, question: str, answer: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes for {hero} during the journey?",
            f"{hero} moves from the starting situation into a new experience. By the end, {hero} has learned, helped, found something, or felt something different.",
        )
    if "trouble" in lower or "help" in lower:
        return (
            "Why does that moment matter?",
            f"That moment matters because it gives {hero} a real challenge. The journey becomes more meaningful when {hero} has to choose what to do.",
        )
    if "learn" in lower or "feel" in lower or "at the end" in lower or "happened at the end" in lower:
        return (
            "What does the ending tell us about the journey?",
            "The ending tells us that the trip was not just about moving from one place to another. It also changed the character's feelings or understanding.",
        )
    return (
        "How does this detail help the story?",
        "This detail helps the reader follow the journey. It explains where the character begins, where the character goes, or what happens along the way.",
    )


def enrich_questions(hero: str, questions: list[QA]) -> list[QA]:
    enriched: list[QA] = []
    for item in questions:
        answer = full_answer(hero, item.question, item.answer)
        follow_question, follow_answer = follow_up_for(hero, item.question, answer)
        enriched.append(QA(item.question, answer, follow_question, follow_answer))
    return enriched


def format_story_with_qa(story: str) -> str:
    questions = build_questions(story)
    if not questions:
        return story
    lines = [story, "", "Questions:"]
    for i, qa in enumerate(questions, 1):
        lines.append(f"{i}. {qa.question}")
        lines.append(f"Answer: {qa.answer}")
        if qa.follow_up_question:
            lines.append(f"Follow-up: {qa.follow_up_question}")
            lines.append(f"Answer: {qa.follow_up_answer}")
    return "\n".join(lines)


def record_json(story: str) -> str:
    return json.dumps(
        {
            "story": story,
            "questions": [
                {
                    "question": qa.question,
                    "answer": qa.answer,
                    "follow_up_question": qa.follow_up_question,
                    "follow_up_answer": qa.follow_up_answer,
                    "turns": [
                        {"role": "user", "content": qa.question},
                        {"role": "assistant", "content": qa.answer},
                        {"role": "user", "content": qa.follow_up_question},
                        {"role": "assistant", "content": qa.follow_up_answer},
                    ] if qa.follow_up_question else [
                        {"role": "user", "content": qa.question},
                        {"role": "assistant", "content": qa.answer},
                    ],
                }
                for qa in build_questions(story)
            ],
        },
        ensure_ascii=False,
    )


# =============================================================================
# JOURNEY STORY SHAPES
# =============================================================================


def companion_trip_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "frog")))
    companion = choose_companion(hero)
    origin = choose_place("home")
    destination = random.choice([p for p in PLACES if p.name in {"park", "playground", "garden", "pond", "library"}])
    route = choose_route(origin, destination)
    world = JourneyWorld(hero, origin, destination)
    activity, activity_action = random.choice(TRIP_ACTIVITIES)
    world.embed(hero.name, Memeplex("Anticipation"))

    story = f"""
{intro(hero, origin)} One morning, {companion.name} said, "Let us go {movement_phrase(destination)}."

{hero.name} felt ready. {travel_lines(hero, route)}

When they reached {place_object(destination)}, {hero.name} saw {phrase(activity)}. {cap(hero.subject)} {activity_action} while {companion.name} stayed close.

After a while, they sat together and rested. {hero.name} asked, "Can we come back another day?"

{companion.name} smiled and said yes.
"""
    world.embed(hero.name, Memeplex("Joy"))
    world.embed(hero.name, Memeplex("Confidence"))
    return clean(story + "\n" + ending(world, "The day became a good memory."))


def solo_exploration_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bird", "cat", "car")))
    origin = choose_place("safe")
    destination = choose_place("outside", avoid=origin)
    route = choose_route(origin, destination)
    world = JourneyWorld(hero, origin, destination)
    seen = random.choice(("green trees", "round stones", "busy ants", "soft sand", "bright flowers", "wide clouds"))
    world.embed(hero.name, Memeplex("Curiosity"))

    story = f"""
{intro(hero, origin)} {cap(hero.subject)} wanted to see something new.

So {hero.name} began a small journey. {travel_lines(hero, route)}

At {place_object(destination)}, {hero.subject} saw {seen}. {cap(hero.subject)} stopped, looked, and listened.

The new place felt big at first, but {hero.name} moved slowly and stayed safe.

When it was time to go back, {hero.name} knew the way home.
"""
    world.mark("returned")
    world.embed(hero.name, Memeplex("Pride"))
    world.embed(hero.name, Memeplex("Confidence"))
    return clean(story + "\n" + ending(world, "The journey ended safely."))


def lost_and_returned_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "cat")))
    finder = choose_companion(hero)
    origin = choose_place("home")
    destination = choose_place("public")
    route = choose_route(origin, destination)
    world = JourneyWorld(hero, origin, destination)
    item = random.choice(("whistle", "red ball", "medal", "toy car", "little book", "blue ribbon"))
    world.mark(f"lost:{item}")

    story = f"""
{intro(hero, origin)} {cap(hero.subject)} loved {hero.possessive} {item} and wanted to show it to everyone.

{hero.name} took it on a journey {movement_phrase(destination)}. {travel_lines(hero, route)}

But when {hero.name} looked for the {item}, it was gone. {cap(hero.subject)} felt worried and searched everywhere.

Later, {finder.name} came with a smile. "I found this," said {finder.name}. It was the {item}.

{hero.name} thanked {finder.name} and held the {item} carefully.
"""
    world.mark(f"returned:{item}")
    world.embed(hero.name, Memeplex("Relief"))
    world.embed(hero.name, Memeplex("Joy"))
    return clean(story + "\n" + ending(world, "The journey taught carefulness and trust."))


def weather_trouble_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "bird")))
    origin = choose_place("home")
    destination = choose_place("outside", avoid=origin)
    route = choose_route(origin, destination)
    weather, weather_line, _ = choose_bad_weather(destination)
    world = JourneyWorld(hero, origin, destination)
    object_name = random.choice(BAD_END_OBJECTS)

    story = f"""
{intro(hero, origin)} One day, {hero.name} carried {phrase(object_name)} {toward_phrase(destination)}.

The journey began well. {travel_lines(hero, route)}

Then trouble came. {cap(weather_line)}. {hero.name} tried to protect the {object_name}.

But the {weather} was too much. The {object_name} got ruined, and {hero.name} felt sad.

At home, {hero.name} dried off and took a quiet breath.
"""
    world.mark(f"damaged:{object_name}")
    world.embed(hero.name, Memeplex("Sadness"))
    return clean(story + f"\n{hero.name} learned to check the sky before taking precious things on a journey.")


def helping_journey_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "bear")))
    helper = choose_companion(hero)
    origin = choose_place("home")
    destination = choose_place("outside", avoid=origin)
    route = choose_route(origin, destination)
    need = random.choice(HELP_NEEDS)
    world = JourneyWorld(hero, origin, destination)
    world.embed(hero.name, Memeplex("Care"))

    story = f"""
{intro(hero, origin)} {helper.name} needed someone to {need}.

{hero.name} said, "I can help." Together, they went {movement_phrase(destination)}.

{travel_lines(hero, route)} The way was not too easy, but {hero.name} kept going.

At last, the helping work was done. {helper.name} said, "Thank you, {hero.name}."

{hero.name} felt tired, but happy.
"""
    world.mark("helped")
    world.embed(hero.name, Memeplex("Care"))
    world.embed(hero.name, Memeplex("Joy"))
    return clean(story + "\n" + ending(world, "Helping made the journey feel important."))


def discovery_adoption_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bird", "cat")))
    origin = choose_place("home")
    destination = choose_place(random.choice(("inside", "outside")), avoid=origin)
    route = choose_route(origin, destination)
    found = random.choice(DISCOVERIES)
    use = random.choice(("rest", "play", "eat better", "make music", "find the way", "decorate the room"))
    world = JourneyWorld(hero, origin, destination)

    story = f"""
{intro(hero, origin)} Something shiny made {hero.name} curious.

{hero.name} followed the clue {movement_phrase(destination)}. {travel_lines(hero, route)}

There, {hero.subject} found {phrase(found)}. At first, {hero.name} did not know what it was for.

Then {hero.name} tried it gently. The {found} helped {hero.object} {use}.

From that day on, {hero.name} used the {found} with care.
"""
    world.mark(f"adopted:{found}")
    world.embed(hero.name, Memeplex("Surprise"))
    world.embed(hero.name, Memeplex("Joy"))
    return clean(story + "\n" + ending(world, "The journey turned a mystery into a useful surprise."))


def social_confidence_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bird", "dog")))
    other = choose_companion(hero)
    origin = choose_place("home")
    destination = choose_place("public", avoid=origin)
    route = choose_route(origin, destination)
    activity, activity_noun = random.choice(ACTIVITIES)
    world = JourneyWorld(hero, origin, destination)
    world.embed(hero.name, Memeplex("Shyness") / 2)

    story = f"""
{intro(hero, origin)} {cap(hero.subject)} liked to {activity}, but did not like doing it where others could see.

One day, {hero.name} took a journey {movement_phrase(destination)}. {travel_lines(hero, route)}

{other.name} watched and said, "That looks wonderful. May I try too?"

At first, {hero.name} felt shy. Then {hero.subject} shared the {activity_noun} with {other.name}.

Soon they were both smiling, and other friends came near.
"""
    world.embed(hero.name, Memeplex("Confidence"))
    world.embed(hero.name, Memeplex("Joy"))
    return clean(story + "\n" + ending(world, "Sharing made the journey brighter."))


STORY_GENERATORS: tuple[Callable[[], str], ...] = (
    companion_trip_story,
    solo_exploration_story,
    lost_and_returned_story,
    weather_trouble_story,
    helping_journey_story,
    discovery_adoption_story,
    social_confidence_story,
)


def generate_unique_stories(count: int = 1000, seed: int | None = None) -> list[str]:
    if seed is not None:
        random.seed(seed)

    stories: list[str] = []
    seen: set[str] = set()
    attempts = 0
    max_attempts = count * 10

    while len(stories) < count and attempts < max_attempts:
        attempts += 1
        story = random.choice(STORY_GENERATORS)()
        if story not in seen:
            seen.add(story)
            stories.append(story)

    if len(stories) < count:
        raise RuntimeError(f"Only generated {len(stories)} unique stories after {attempts} attempts.")
    return stories


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate standalone Journey-style scripted stories.")
    parser.add_argument("-n", "--num", type=int, default=1000, help="Number of stories to print.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed.")
    parser.add_argument("--with-qa", action="store_true", help="Append generated questions and answers after each story.")
    parser.add_argument("--format", choices=("text", "jsonl"), default="text", help="Output format.")
    args = parser.parse_args()

    stories = generate_unique_stories(args.num, seed=args.seed)
    if args.format == "jsonl":
        for story in stories:
            print(record_json(story))
    elif args.with_qa:
        print("\n\n\n\n".join(format_story_with_qa(story) for story in stories))
    else:
        print("\n\n\n\n".join(stories))


if __name__ == "__main__":
    main()
