#!/usr/bin/env python3
"""
Quest Tales Generator

Generate short scripted Quest-style stories with no runtime LLMs and no external
dependencies. The shapes are inspired by TinyStories kernels such as:

    Quest(hero, state=Routine+Longing(goal), obstacle=..., process=..., result=...)
    Quest(hero, goal=Deliver(item), catalyst=Request(...), process=..., outcome=...)
    Quest(search=home, participants=[hero, helper])

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
    """Tiny weighted concept bundle used to steer endings and wording."""

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
        if self.kind in {"mom", "dad", "grandma", "grandpa"}:
            return self.kind
        return self.kind

    @property
    def trait_text(self) -> str:
        return " ".join(self.traits[:2])

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
class Obstacle:
    name: str
    tags: frozenset[str]
    line: str
    bad_for: frozenset[str] = frozenset()
    good_for: frozenset[str] = frozenset()


@dataclass
class QuestWorld:
    hero: Character
    place: Place
    facts: set[str] = field(default_factory=set)
    carriers: dict[str, dict[str, float]] = field(default_factory=dict)

    def embed(self, carrier: str, meme: Memeplex) -> None:
        self.carriers.setdefault(carrier, {})
        self.carriers[carrier][meme.name] = self.carriers[carrier].get(meme.name, 0.0) + meme.weight
        if carrier == self.hero.name:
            self.hero.add_meme(meme)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)

    def has(self, fact: str) -> bool:
        return fact in self.facts


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
    "Tim", "Ben", "Sam", "Leo", "Milo", "Noah", "Eli", "Finn",
    "Theo", "Jack", "Oscar", "Hugo", "Max", "Owen", "Toby", "Nico",
)
GIRL_NAMES = (
    "Lily", "Mia", "Zoe", "Ruby", "Nina", "Ivy", "Chloe", "Anna",
    "Ella", "Lucy", "Clara", "Sophie", "Maya", "Rose", "Violet", "Luna",
)
ANIMAL_NAMES = (
    "Bobo", "Pip", "Nibbles", "Teddy", "Moss", "Sunny", "Coco",
    "Daisy", "Pebble", "Poppy", "Sparky", "Bean", "Wiggle", "Biscuit",
)

CHILD_TRAITS = (
    "curious", "brave", "kind", "playful", "careful", "eager",
    "gentle", "helpful", "shy", "bright", "patient", "hopeful",
)
ANIMAL_TRAITS = (
    "small", "happy", "quick", "gentle", "hungry", "playful",
    "curious", "kind", "sleepy", "furry", "bouncy", "friendly",
)

PLACES = (
    Place("park", "at the", frozenset({"outside", "public", "play"})),
    Place("wide field", "in the", frozenset({"outside", "open"})),
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("forest", "in the", frozenset({"outside", "trees"})),
    Place("beach", "on the", frozenset({"outside", "sand", "water"})),
    Place("pond", "by the", frozenset({"outside", "water"})),
    Place("school yard", "in the", frozenset({"outside", "public", "play"})),
    Place("backyard", "in the", frozenset({"outside", "home", "play"})),
    Place("kitchen", "in the", frozenset({"inside", "home", "food"})),
    Place("playroom", "in the", frozenset({"inside", "home", "play"})),
    Place("attic", "in the", frozenset({"inside", "home", "hidden"})),
    Place("library", "at the", frozenset({"inside", "public", "quiet"})),
)

OBSTACLES = (
    Obstacle("too high", frozenset({"height"}), "It was too high to reach."),
    Obstacle("a locked little gate", frozenset({"locked"}), "A little gate was locked tight."),
    Obstacle("a muddy path", frozenset({"mud"}), "The path was muddy and slow."),
    Obstacle("a wide puddle", frozenset({"water"}), "A wide puddle blocked the way."),
    Obstacle("a strong wind", frozenset({"wind"}), "A strong wind pushed against the quest."),
    Obstacle("a dark corner", frozenset({"dark"}), "The next place looked dark and quiet."),
    Obstacle("a tall place", frozenset({"height"}), "The thing they needed sat up high."),
    Obstacle("a missing clue", frozenset({"clue"}), "At first, there was no clue at all."),
    Obstacle("a heavy load", frozenset({"heavy"}), "The load was heavy and hard to move."),
    Obstacle("a sleepy moment", frozenset({"tired"}), "The quest felt hard because everyone was tired."),
)

TREATS = ("cake", "apple", "cookie", "berry pie", "warm bread", "sweet carrot", "muffin")
LOST_OBJECTS = ("radio", "red ball", "toy boat", "blue ribbon", "story book", "little bell", "shiny key")
DELIVERY_ITEMS = ("letter", "paper star", "basket of berries", "small lunch", "flower crown", "warm scarf")
REPAIR_TARGETS = ("toy train", "wooden cart", "kite", "bird house", "little bridge", "doll bed")
DISCOVERIES = ("secret room", "tiny door", "glowing stone", "old map", "hidden nest", "music box")
HELP_TASKS = (
    ("carry water", ("bucket", "small pail"), ("tiny plants", "the family garden", "baby birds")),
    ("bring a bucket", ("bucket", "small cart"), ("a tired friend", "the family garden")),
    ("pick berries", ("basket", "cloth bag"), ("Grandma", "a hungry friend", "the picnic table")),
    ("find a safe path", ("map", "bright ribbon"), ("a lost child", "a tired friend")),
    ("gather soft leaves", ("basket", "cloth bag"), ("baby birds", "a small nest", "a cold bunny")),
)
TOOLS = ("springy stick", "small ladder", "bright ribbon", "map", "lantern", "basket", "rope", "shovel")


# =============================================================================
# HELPERS
# =============================================================================


def article(noun: str) -> str:
    first = noun.strip()[:1].lower()
    return "an" if first in "aeiou" else "a"


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


def choose_character(kind: str | None = None) -> Character:
    kind = kind or random.choice(("girl", "boy", "bunny", "cat", "dog", "bear", "bee", "squirrel", "duck"))
    if kind == "girl":
        return Character(
            random.choice(GIRL_NAMES),
            "girl",
            tuple(random.sample(CHILD_TRAITS, 2)),
            "girl",
            frozenset({"child", "person", "hands", "walks"}),
        )
    if kind == "boy":
        return Character(
            random.choice(BOY_NAMES),
            "boy",
            tuple(random.sample(CHILD_TRAITS, 2)),
            "boy",
            frozenset({"child", "person", "hands", "walks"}),
        )
    tags = {
        "bunny": {"animal", "small", "hops"},
        "cat": {"animal", "small", "climbs"},
        "dog": {"animal", "runs"},
        "bear": {"animal", "strong"},
        "bee": {"animal", "flies", "small"},
        "squirrel": {"animal", "climbs", "small"},
        "duck": {"animal", "swims", "walks"},
    }.get(kind, {"animal"})
    return Character(
        random.choice(ANIMAL_NAMES),
        kind,
        tuple(random.sample(ANIMAL_TRAITS, 2)),
        "neutral",
        frozenset(tags),
    )


def choose_helper(exclude: Character | None = None) -> Character:
    options = [
        Character("Mom", "mom", ("kind", "calm"), "girl", frozenset({"person", "adult", "hands", "walks"})),
        Character("Dad", "dad", ("helpful", "patient"), "boy", frozenset({"person", "adult", "hands", "walks"})),
        Character("Grandma", "grandma", ("wise", "warm"), "girl", frozenset({"person", "adult", "hands", "walks"})),
        Character("Owl", "owl", ("wise", "quiet"), "neutral", frozenset({"animal", "flies"})),
        Character("Mouse", "mouse", ("small", "quick"), "neutral", frozenset({"animal", "small"})),
        Character("Mole", "mole", ("gentle", "good"), "neutral", frozenset({"animal", "digs"})),
        Character("Robin", "bird", ("bright", "helpful"), "neutral", frozenset({"animal", "flies"})),
    ]
    if exclude is not None:
        options = [c for c in options if c.name != exclude.name]
    return random.choice(options)


def intro(hero: Character, place: Place) -> str:
    trait = hero.trait_text
    desc = f"{trait} {hero.intro_noun}".strip()
    return f"Once upon a time, there was {article(desc)} {desc} named {hero.name}. {hero.name} liked to spend time {place.phrase}."


def choose_obstacle(goal_tags: set[str], hero: Character, place: Place) -> Obstacle:
    allowed_by_goal = {
        "reach": {"height", "tired"},
        "lost": {"clue", "dark", "mud", "water", "wind", "tired"},
        "deliver": {"locked", "mud", "water", "wind", "dark", "heavy", "tired"},
        "repair": {"locked", "clue", "dark", "heavy", "tired"},
        "rescue": {"locked", "mud", "water", "dark", "heavy", "tired"},
        "discover": {"locked", "mud", "water", "wind", "dark", "clue", "tired"},
        "service": {"locked", "mud", "water", "wind", "heavy", "tired"},
    }
    allowed_tags: set[str] | None = None
    for tag in goal_tags:
        if tag in allowed_by_goal:
            allowed_tags = set(allowed_by_goal[tag]) if allowed_tags is None else allowed_tags & allowed_by_goal[tag]

    compatible = []
    for obstacle in OBSTACLES:
        if allowed_tags is not None and not (obstacle.tags & allowed_tags):
            continue
        if obstacle.tags & {"mud", "wind"} and "outside" not in place.tags:
            continue
        if "water" in obstacle.tags and not ({"outside", "water"} & place.tags):
            continue
        if obstacle.bad_for and obstacle.bad_for & hero.tags:
            continue
        if obstacle.good_for and not obstacle.good_for & hero.tags:
            continue
        if "inside_only" in goal_tags and "outside" in obstacle.tags:
            continue
        compatible.append(obstacle)
    return random.choice(compatible or list(OBSTACLES))


def effort_line(hero: Character, obstacle: Obstacle, tool: str) -> str:
    if "height" in obstacle.tags:
        if "climbs" in hero.tags:
            return f"{hero.name} climbed carefully, then used {article(tool)} {tool} to get closer."
        if "flies" in hero.tags:
            return f"{hero.name} flew up carefully, with {article(tool)} {tool} to mark the way."
        return f"{hero.name} stood on tiptoe and used {article(tool)} {tool} to reach higher."
    if "locked" in obstacle.tags:
        return f"{hero.name} looked around and used {article(tool)} {tool} to find another safe way."
    if "mud" in obstacle.tags or "water" in obstacle.tags:
        return f"{hero.name} moved slowly and used {article(tool)} {tool} to cross without falling."
    if "dark" in obstacle.tags:
        return f"{hero.name} took {article(tool)} {tool} and made the dark place feel less scary."
    if "heavy" in obstacle.tags:
        return f"{hero.name} pulled with care and used {article(tool)} {tool} to make the load easier."
    return f"{hero.name} kept trying and used {article(tool)} {tool} in a clever way."


def noun_phrase(noun: str) -> str:
    if noun.startswith(("some ", "the ", "a ", "an ")):
        return noun
    if noun.endswith("s") and noun not in {"grass"}:
        return noun
    return f"{article(noun)} {noun}"


def ending_from_world(world: QuestWorld, default: str) -> str:
    joy = world.hero.memes.get("Joy", 0.0)
    pride = world.hero.memes.get("Pride", 0.0)
    kindness = world.hero.memes.get("Kindness", 0.0)
    if kindness >= 0.8:
        return f"{world.hero.name} learned that a quest feels best when it helps someone else."
    if pride >= 0.7:
        return f"{world.hero.name} felt proud because the quest had been hard, but {world.hero.subject} did not give up."
    if joy >= 0.7:
        return f"{world.hero.name} felt happy and remembered that trying step by step can lead to good things."
    return default


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

    place = re.search(re.escape(hero) + r" liked to spend time ([^.]+)\.", story)
    if place:
        questions.append(QA(f"Where did {hero} like to spend time?", place.group(1)))

    wanted = re.search(r"saw (?:a|an) ([^.]*) and wanted to taste it", story)
    if wanted:
        questions.append(QA(f"What did {hero} want to taste?", wanted.group(1)))

    lost = re.search(re.escape(hero) + r" lost (?:his|her|its) ([^.]+)\.", story)
    if lost:
        questions.append(QA(f"What did {hero} lose?", lost.group(1)))

    needed = re.search(r"That morning, ([A-Z][A-Za-z]+) needed (?:a|an) ([^.]+)\.", story)
    if needed:
        questions.append(QA(f"What did {needed.group(1)} need?", needed.group(2)))

    broken = re.search(r"had (?:a|an) ([^.]+) that was broken", story)
    if broken:
        questions.append(QA(f"What was broken?", broken.group(1)))

    stuck = re.search(r"It was ([A-Z][A-Za-z]+)\. [A-Z][A-Za-z]+ was stuck in ([^.]+)\.", story)
    if stuck:
        questions.append(QA("Who needed help?", stuck.group(1)))
        questions.append(QA(f"Where was {stuck.group(1)} stuck?", stuck.group(2)))

    obstacle = re.search(r"(?:Soon there was a problem|But the quest was not easy|The quest was harder than it looked)\. ([^.]+)\.", story)
    if obstacle:
        questions.append(QA("What made the quest hard?", obstacle.group(1)))

    found = re.search(r"At (?:last|the end of the path), " + re.escape(hero) + r" found (?:a|an|the) ([^.]+)\.", story)
    if found:
        questions.append(QA(f"What did {hero} find?", found.group(1)))

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
        return f"The main character is {answer}. The story follows {answer} as the quest unfolds."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description helps show what {hero} was like before the quest began."
    if "where did" in lower and "spend time" in lower:
        return f"{hero} liked to spend time {answer}. That place is where the story starts."
    if "want to taste" in lower:
        return f"{hero} wanted to taste the {answer}. The wish to taste it is what started this quest."
    if "what did" in lower and "lose" in lower:
        return f"{hero} lost the {answer}. Losing it made {hero} search carefully for help and clues."
    if "what did" in lower and "need" in lower:
        return f"The character needed a {answer}. That need gave {hero} a reason to begin the quest."
    if "what was broken" in lower:
        return f"The {answer} was broken. {hero} worked on the quest so it could become useful again."
    if "who needed help" in lower:
        return f"{answer} needed help. {hero} heard the call and chose to help instead of walking away."
    if "where was" in lower and "stuck" in lower:
        return f"The character was stuck in {answer}. That problem made the rescue part of the quest important."
    if "what made the quest hard" in lower:
        return f"The hard part was that {answer.lower()}. {hero} had to keep trying even though the quest was not easy."
    if "what did" in lower and "find" in lower:
        return f"{hero} found the {answer}. Finding it shows that the careful search paid off."
    if "learn" in lower:
        return f"{hero} learned {answer}. The ending turns the quest into a lesson about what matters."
    if "how did" in lower and "feel" in lower:
        return f"{hero} felt {answer}. That feeling shows how the quest changed {hero}."
    if "what happened at the end" in lower:
        return f"At the end, {answer}. This closes the quest with a clear result."
    return f"The answer is {answer}. This detail comes directly from the story."


def follow_up_for(hero: str, question: str, answer: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What does {hero} do in the story?",
            f"{hero} takes part in the main quest. The story is built around what happens to {hero} and how {hero} responds.",
        )
    if "kind of character" in lower:
        return (
            f"What does that tell us about the quest?",
            f"It suggests {hero} approaches the challenge in a recognizable way. "
            f"Those traits shape how {hero} keeps going and what others feel in the story.",
        )
    if "quest hard" in lower or "stuck" in lower or "broken" in lower or "lose" in lower:
        return (
            "How does the character respond to the problem?",
            f"{hero} keeps going and looks for a way to solve the problem. The response is active instead of giving up.",
        )
    if "where did" in lower and "spend time" in lower:
        return (
            "How did that place shape the quest?",
            f"The setting mattered because it changed what was possible in the story. "
            f"It also gave the quest a clear and memorable path.",
        )
    if "who needed help" in lower or "stuck" in lower:
        return (
            f"What made {hero} decide to help?",
            f"{hero} heard the call and chose empathy over fear. That choice carries the whole quest forward.",
        )
    if "what did" in lower and "want to taste" in lower:
        return (
            "How did that desire change the quest?",
            f"The desire set a clear goal and gave {hero} a reason to start moving. "
            f"It also makes the later challenge feel earned.",
        )
    if "where did" in lower and "stuck" not in lower and "help" in lower:
        return (
            f"What helped {hero} stay focused?",
            f"{hero} stayed focused by staying calm, finding one useful step, and repeating the effort. "
            f"That pattern usually turns a problem into a solvable task.",
        )
    if "what did" in lower and ("find" in lower or "discover" in lower):
        return (
            "Why was that discovery important?",
            "That finding connected the entire quest into a complete arc. "
            f"It gave the ending a concrete reason to change how {hero} feels.",
        )
    if "learn" in lower or "happened at the end" in lower or "feel" in lower:
        return (
            "Why is that ending important?",
            "The ending is important because it shows the result of the quest. It also gives the story its lesson or emotional payoff.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain what is happening in the story. It gives the quest a clearer beginning, problem, or result.",
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
# QUEST STORY SHAPES
# =============================================================================


def reach_treat_story() -> str:
    hero = choose_character(random.choice(("bunny", "cat", "squirrel", "girl", "boy")))
    place = random.choice([p for p in PLACES if "food" in p.tags or "play" in p.tags or "outside" in p.tags])
    world = QuestWorld(hero, place)
    treat = random.choice(TREATS)
    obstacle = choose_obstacle({"reach"}, hero, place)
    tool = random.choice(("springy stick", "small ladder", "box", "smooth stone"))
    world.embed(hero.name, Memeplex("Longing"))

    story = f"""
{intro(hero, place)} One day, {hero.subject} saw {article(treat)} {treat} and wanted to taste it.

But the quest was not easy. {obstacle.line} {cap(hero.subject)} looked at the {treat} and took a deep breath.

Then {effort_line(hero, obstacle, tool)} {cap(hero.subject)} tried once, tried twice, and tried one more time.

At last, {hero.name} reached the {treat}. {cap(hero.subject)} took a little taste and smiled.
"""
    world.embed(hero.name, Memeplex("Joy"))
    return clean(story + "\n" + ending_from_world(world, "The quest taught patience."))


def lost_object_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "cat", "bunny")))
    helper = choose_helper(hero)
    place = random.choice([p for p in PLACES if "public" in p.tags or "outside" in p.tags or "hidden" in p.tags])
    world = QuestWorld(hero, place)
    obj = random.choice(LOST_OBJECTS)
    clue = random.choice(("soft music", "tiny tracks", "a red mark", "a little sound", "a shiny corner"))
    hiding_place = random.choice(("under a bench", "behind a bush", "inside a box", "near a tree", "beside a basket"))
    world.mark(f"lost:{obj}")
    world.embed(hero.name, Memeplex("Worry"))

    story = f"""
{intro(hero, place)} One day, {hero.name} lost {hero.possessive} {obj}.

{hero.name} looked left and right, but the {obj} was gone. {helper.name} came by and said, "Let us follow one small clue."

They found {clue} {hiding_place}. The clue made the quest feel possible again.

Together, {hero.name} and {helper.name} searched carefully. At last, they found the {obj} {hiding_place}.
"""
    world.mark(f"found:{obj}")
    world.embed(hero.name, Memeplex("Joy"))
    world.embed(hero.name, Memeplex("Friendship"))
    return clean(story + f"\n{hero.name} thanked {helper.name}. Looking together had turned a sad search into a happy quest.")


def delivery_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "duck", "bear")))
    receiver = choose_helper(hero)
    place = random.choice([p for p in PLACES if "outside" in p.tags or "public" in p.tags])
    world = QuestWorld(hero, place)
    item = random.choice(DELIVERY_ITEMS)
    obstacle = choose_obstacle({"deliver"}, hero, place)
    container = random.choice(("bag", "basket", "cloth pouch", "small pack"))
    aid = random.choice(("map", "bright ribbon", "walking stick", "little lantern"))
    world.embed(hero.name, Memeplex("Responsibility"))

    story = f"""
{intro(hero, place)} That morning, {receiver.name} needed {article(item)} {item}.

{hero.name} said, "I can bring it." {cap(hero.subject)} put the {item} in {article(container)} {container} and started the quest.

Soon there was a problem. {obstacle.line} {effort_line(hero, obstacle, aid)}

At last, {hero.name} reached {receiver.name} and gave {receiver.object} the {item}. {receiver.name} smiled and said, "Thank you for coming all this way."
"""
    world.mark(f"delivered:{item}")
    world.embed(hero.name, Memeplex("Pride"))
    world.embed(hero.name, Memeplex("Kindness"))
    return clean(story + "\n" + ending_from_world(world, "The quest was finished."))


def repair_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bear", "squirrel", "cat")))
    helper = choose_helper(hero)
    place = random.choice([p for p in PLACES if "home" in p.tags or "outside" in p.tags])
    world = QuestWorld(hero, place)
    target = random.choice(REPAIR_TARGETS)
    material = random.choice(("smooth wood", "strong string", "soft cloth", "sticky paste", "flat stone", "clean paper"))
    obstacle = choose_obstacle({"repair"}, hero, place)
    world.mark(f"broken:{target}")
    world.embed(hero.name, Memeplex("Care"))

    story = f"""
{intro(hero, place)} {cap(hero.subject)} had {article(target)} {target} that was broken.

{hero.name} wanted to fix it, but {obstacle.name} made the work hard. {helper.name} said, "A good quest starts with finding the right thing."

They searched and found {noun_phrase(material)}. Then {hero.name} held the pieces still while {helper.name} helped.

Slowly, the {target} became strong again. {hero.name} tested it gently, and it worked.
"""
    world.mark(f"fixed:{target}")
    world.embed(hero.name, Memeplex("Joy"))
    world.embed(hero.name, Memeplex("Pride"))
    return clean(story + "\n" + ending_from_world(world, "Fixing something took care and time."))


def rescue_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "bear", "bee", "squirrel")))
    friend = choose_helper(hero)
    place = random.choice([p for p in PLACES if "outside" in p.tags or "hidden" in p.tags or "inside" in p.tags])
    world = QuestWorld(hero, place)
    stuck_place = random.choice(("a little hole", "a box", "some tall grass", "a low branch", "a quiet corner"))
    obstacle = choose_obstacle({"rescue"}, hero, place)
    tool = random.choice(("rope", "lantern", "stick", "basket", "soft scarf"))
    world.embed(hero.name, Memeplex("Kindness"))

    story = f"""
{intro(hero, place)} Then {hero.name} heard a tiny call for help.

It was {friend.name}. {friend.name} was stuck in {stuck_place}. {obstacle.line}

{hero.name} did not run away. {effort_line(hero, obstacle, tool)} Then {hero.subject} called, "Hold on. I am here."

With one careful pull, {friend.name} was free. {friend.name} was safe again, and both of them laughed with relief.
"""
    world.mark(f"safe:{friend.name}")
    world.embed(hero.name, Memeplex("Joy"))
    world.embed(hero.name, Memeplex("Kindness"))
    return clean(story + "\n" + ending_from_world(world, "Helping made the quest worth doing."))


def discovery_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "cat", "bee", "squirrel", "duck")))
    place = random.choice([p for p in PLACES if "hidden" in p.tags or "outside" in p.tags or "quiet" in p.tags])
    world = QuestWorld(hero, place)
    clue = random.choice(("old map", "soft song", "glowing pebble", "paper arrow", "tiny bell"))
    discovery = random.choice(DISCOVERIES)
    obstacle = choose_obstacle({"discover"}, hero, place)
    tool = random.choice(TOOLS)
    world.embed(hero.name, Memeplex("Curiosity"))

    story = f"""
{intro(hero, place)} One day, {hero.subject} found {article(clue)} {clue}.

The {clue} seemed to say, "Come and see." So {hero.name} began a quiet quest.

{obstacle.line} {effort_line(hero, obstacle, tool)}

At the end of the path, {hero.name} found {article(discovery)} {discovery}. It was small, wonderful, and real.
"""
    world.mark(f"known:{discovery}")
    world.embed(hero.name, Memeplex("Joy"))
    return clean(story + "\n" + ending_from_world(world, "The quest showed that careful looking can find hidden wonders."))


def service_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bear", "duck", "dog")))
    helper = choose_helper(hero)
    place = random.choice([p for p in PLACES if "outside" in p.tags or "home" in p.tags])
    world = QuestWorld(hero, place)
    task, tool_choices, receivers = random.choice(HELP_TASKS)
    receiver = random.choice(receivers)
    obstacle = choose_obstacle({"service"}, hero, place)
    tool = random.choice(tool_choices)
    world.embed(hero.name, Memeplex("Kindness"))

    story = f"""
{intro(hero, place)} {helper.name} asked {hero.name} to help {task} for {receiver}.

{hero.name} wanted to help, so {hero.subject} picked up {article(tool)} {tool} and began.

The quest was harder than it looked. {obstacle.line} Still, {hero.name} kept going slowly and safely.

When the work was done, {receiver} had what they needed. {helper.name} clapped and said, "You helped with a big heart."
"""
    world.mark("helped")
    world.embed(hero.name, Memeplex("Kindness"))
    world.embed(hero.name, Memeplex("Pride"))
    return clean(story + "\n" + ending_from_world(world, "A helpful quest can make a small person feel big inside."))


STORY_GENERATORS: tuple[Callable[[], str], ...] = (
    reach_treat_story,
    lost_object_story,
    delivery_story,
    repair_story,
    rescue_story,
    discovery_story,
    service_story,
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
    parser = argparse.ArgumentParser(description="Generate standalone Quest-style scripted stories.")
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
