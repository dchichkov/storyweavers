#!/usr/bin/env python3
"""
Loss Tales Generator

Generate short scripted Loss/Search-style stories with no runtime LLMs and no
external dependencies. The story shapes are inspired by TinyStories kernels like:

    Loss(hero, state=..., catalyst=..., process=Search + Acceptance, ...)
    Search(hero, item, process=..., resolution=Return(...))
    Quest(hero, goal=Find(item), consequence=Loss(item))

Run this file to print 1,000 unique stories separated by four newlines.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass, field


# =============================================================================
# SMALL WORLD MODEL
# =============================================================================


@dataclass(frozen=True)
class Memeplex:
    name: str
    weight: float = 1.0


@dataclass
class Character:
    name: str
    kind: str
    traits: tuple[str, ...]
    gender: str = "neutral"
    memes: dict[str, float] = field(default_factory=dict)

    @property
    def subject(self) -> str:
        if self.gender == "girl":
            return "she"
        if self.gender == "boy":
            return "he"
        return "it"

    @property
    def object(self) -> str:
        if self.gender == "girl":
            return "her"
        if self.gender == "boy":
            return "him"
        return "it"

    @property
    def possessive(self) -> str:
        if self.gender == "girl":
            return "her"
        if self.gender == "boy":
            return "his"
        return "its"

    @property
    def intro_noun(self) -> str:
        if self.kind in {"girl", "boy", "child"}:
            return f"little {self.kind}"
        return self.kind

    def add(self, meme: Memeplex) -> None:
        self.memes[meme.name] = self.memes.get(meme.name, 0.0) + meme.weight


@dataclass(frozen=True)
class Place:
    name: str
    prep: str
    tags: frozenset[str]

    @property
    def phrase(self) -> str:
        return f"{self.prep} {self.name}"


@dataclass
class LossWorld:
    hero: Character
    place: Place
    lost_item: str
    recovered: bool = False
    facts: set[str] = field(default_factory=set)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)

    def recover(self) -> None:
        self.recovered = True
        self.hero.add(Memeplex("Relief", 1.0))


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str = ""
    follow_up_answer: str = ""


# =============================================================================
# VOCABULARY
# =============================================================================


BOY_NAMES = ("Timmy", "Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn")
GIRL_NAMES = ("Lily", "Amy", "Anna", "Mia", "Sue", "Ruby", "Zoe", "Clara", "Lucy", "Ivy")
ANIMAL_NAMES = ("Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo")

CHILD_TRAITS = ("playful", "curious", "careful", "worried", "hopeful", "proud", "kind", "nervous", "gentle")
ANIMAL_TRAITS = ("friendly", "small", "quick", "curious", "happy", "gentle", "playful", "loyal", "sleepy")
KINDS = ("dog", "cat", "bunny", "mouse", "bear", "frog")

PLACES = (
    Place("park", "at the", frozenset({"outside", "public", "play"})),
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("school", "at", frozenset({"inside", "public"})),
    Place("bedroom", "in the", frozenset({"inside", "home"})),
    Place("backyard", "in the", frozenset({"outside", "home"})),
    Place("bus stop", "at the", frozenset({"public", "travel"})),
    Place("beach", "on the", frozenset({"outside", "water"})),
    Place("kitchen", "in the", frozenset({"inside", "home"})),
)

ITEMS = (
    "red whistle", "favorite arrow", "blue ball", "toy car", "small phone",
    "yellow hat", "shiny key", "silver cap", "little shield", "paper boat",
    "striped scarf", "tiny bell",
)
HELPERS = ("Mom", "Dad", "Grandma", "Sam", "a kind worker", "a helpful dog", "a friendly bird")
SEARCH_SPOTS = (
    ("under the bench", "behind the tree", "beside the flowers"),
    ("inside the bag", "under the toys", "near the table"),
    ("by the swings", "near the slide", "beside the path"),
    ("under the shells", "near the towel", "beside the sandcastle"),
)
DISTRACTIONS = ("butterfly", "funny cloud", "singing bird", "rainbow", "friendly puppy")
LESSONS = (
    "important things need careful places",
    "asking for help can make a search easier",
    "not every lost thing comes back, but happy days can still return",
    "searching calmly works better than panicking",
    "kind people can help return what was lost",
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


def choose_character(kind: str | None = None) -> Character:
    if kind is None:
        kind = random.choice(("girl", "boy") + KINDS)
    if kind == "girl":
        return Character(random.choice(GIRL_NAMES), "girl", tuple(random.sample(CHILD_TRAITS, 2)), "girl")
    if kind == "boy":
        return Character(random.choice(BOY_NAMES), "boy", tuple(random.sample(CHILD_TRAITS, 2)), "boy")
    return Character(random.choice(ANIMAL_NAMES), kind, tuple(random.sample(ANIMAL_TRAITS, 2)))


def description(char: Character) -> str:
    return f"{' '.join(char.traits)} {char.intro_noun}".strip()


def intro(hero: Character, place: Place) -> str:
    desc = description(hero)
    return f"Once upon a time, there was {article(desc)} {desc} named {hero.name}. {hero.name} liked to spend time {place.phrase}."


def item_phrase(item: str) -> str:
    if item.startswith(("a ", "an ", "the ")):
        return item
    return f"{article(item)} {item}"


def ending(world: LossWorld, fallback: str) -> str:
    if world.recovered:
        return f"{world.hero.name} learned that {random.choice([LESSONS[0], LESSONS[1], LESSONS[3], LESSONS[4]])}."
    if "accepted" in world.facts:
        return f"{world.hero.name} learned that {LESSONS[2]}."
    return fallback


# =============================================================================
# STORY SHAPES
# =============================================================================


def lost_object_search_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "cat")))
    place = random.choice(PLACES)
    item = random.choice(ITEMS)
    world = LossWorld(hero, place, item)
    spots = random.choice(SEARCH_SPOTS)

    story = f"""
{intro(hero, place)} {cap(hero.subject)} brought {item_phrase(item)} because it felt special.

After a while, {hero.name} reached for the {item}, but it was gone. {cap(hero.subject)} felt worried and looked around.

{hero.name} searched {spots[0]}, {spots[1]}, and {spots[2]}. The search felt long.

At last, {hero.name} found the {item} near a quiet corner. {cap(hero.subject)} held it carefully and took a deep breath.
"""
    world.recover()
    return clean(story + "\n" + ending(world, "The lost thing came back."))


def helper_return_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"school", "park", "bus stop", "garden"}])
    item = random.choice(ITEMS)
    helper = random.choice(HELPERS)
    world = LossWorld(hero, place, item)

    story = f"""
{intro(hero, place)} {hero.name} wanted to show everyone {item_phrase(item)}.

When {hero.name} checked {hero.possessive} bag, the {item} was missing. {cap(hero.subject)} felt sad and scared.

{hero.name} asked friends and grown-ups if they had seen it. No one knew at first.

Later, {helper} found the {item} and brought it back. {hero.name} smiled and said thank you.

The returned {item} felt even more precious than before.
"""
    world.recover()
    return clean(story + "\n" + ending(world, "Someone kind helped return the lost thing."))


def acceptance_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "mouse", "bunny")))
    place = random.choice([p for p in PLACES if p.name in {"park", "backyard", "garden", "beach"}])
    item = random.choice(("favorite leaf", "paper boat", "old TV show", "little shell", "soap bubble"))
    distraction = random.choice(DISTRACTIONS)
    world = LossWorld(hero, place, item)

    story = f"""
{intro(hero, place)} For many days, {hero.name} loved {item_phrase(item)}.

One day, the {item} was gone. {hero.name} searched and searched, but it did not come back.

At first, {hero.name} felt very sad. {cap(hero.subject)} missed the {item} and did not know what to do.

Then {hero.name} noticed {article(distraction)} {distraction}. It did not replace the lost thing, but it made the day feel a little brighter.

{hero.name} still remembered the {item}, but {hero.subject} also found something new to enjoy.
"""
    world.mark("accepted")
    return clean(story + "\n" + ending(world, "The day became gentle again."))


def taken_then_recovered_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "dog", "bear")))
    place = random.choice([p for p in PLACES if "outside" in p.tags])
    item = random.choice(("little shield", "blue ball", "yellow hat", "paper boat"))
    taker = random.choice(("wind", "sneaky crow", "big wave", "rolling cart"))
    world = LossWorld(hero, place, item)

    story = f"""
{intro(hero, place)} {hero.name} was proud of {hero.possessive} {item}.

Suddenly, the {taker} took the {item} away. {hero.name} gasped and ran after it.

The chase was not easy. {hero.name} had to slow down, look carefully, and choose a safe path.

Finally, {hero.name} reached the {item}. It was dusty, but it was safe.

{hero.name} cleaned it off and held it close.
"""
    world.recover()
    return clean(story + "\n" + ending(world, "The lost thing was safe again."))


def shared_search_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    friend = choose_character(random.choice(("girl", "boy", "dog", "cat")))
    if friend.name == hero.name:
        friend = Character("Sam", "boy", ("helpful", "kind"), "boy")
    place = random.choice([p for p in PLACES if p.name in {"park", "garden", "school", "backyard"}])
    item = random.choice(ITEMS)
    world = LossWorld(hero, place, item)

    story = f"""
{intro(hero, place)} {friend.name} was there too.

{hero.name} lost {hero.possessive} {item} while playing. {cap(hero.subject)} looked ready to cry.

{friend.name} said, "I will help you search." Together they checked near the path, under a bench, and beside the flowers.

They found the {item} tucked under a leaf. {hero.name} thanked {friend.name} for staying.

The search felt easier with a friend.
"""
    world.recover()
    return clean(story + "\n" + ending(world, "A friend made the loss less scary."))


STORY_SHAPES = (
    lost_object_search_story,
    helper_return_story,
    acceptance_story,
    taken_then_recovered_story,
    shared_search_story,
)


def generate_unique_stories(count: int) -> list[str]:
    stories: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(stories) < count and attempts < count * 80:
        attempts += 1
        story = random.choice(STORY_SHAPES)()
        key = story[:240] + story[-240:]
        if key not in seen:
            seen.add(key)
            stories.append(story)
    if len(stories) < count:
        raise RuntimeError(f"Only generated {len(stories)} unique stories after {attempts} attempts")
    return stories


# =============================================================================
# QUESTION GENERATION
# =============================================================================


def build_questions(story: str) -> list[QA]:
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

    lost_patterns = [
        re.search(r"the ([^.,]+) was missing", story),
        re.search(re.escape(hero) + r" lost (?:his|her|its) ([^.]+?) while", story),
        re.search(r"the ([^.,]+) was gone", story),
        re.search(r"took the ([^.,]+) away", story),
    ]
    for lost in lost_patterns:
        if lost:
            questions.append(QA("What was lost?", lost.group(1)))
            break

    feeling = re.search(re.escape(hero) + r" felt ([^.!?\n]+)[.!?]", story)
    if feeling:
        questions.append(QA(f"How did {hero} feel?", feeling.group(1)))

    search = re.search(re.escape(hero) + r" searched ([^.]+)\.", story)
    if search:
        questions.append(QA(f"Where did {hero} search?", search.group(1)))

    helper = re.search(r"Later, ([A-Z][A-Za-z]+|a [a-z ]+) found the ([^.,]+) and brought it back", story)
    if helper:
        questions.append(QA("Who returned the lost thing?", helper.group(1)))

    friend = re.search(r"([A-Z][A-Za-z]+) said, \"I will help you search\.\"", story)
    if friend:
        questions.append(QA("Who helped with the search?", friend.group(1)))

    found = re.search(r"(?:At last, " + re.escape(hero) + r" found|They found|Finally, " + re.escape(hero) + r" reached) the ([^.,]+?)(?: near| tucked|[.,])", story)
    if found:
        questions.append(QA("Was the lost thing found?", f"yes, the {found.group(1)} was found"))
    elif "did not come back" in story:
        questions.append(QA("Was the lost thing found?", "no, it did not come back"))

    lessons = list(re.finditer(re.escape(hero) + r" learned (?:that )?([^.]+)\.", story))
    if lessons:
        questions.append(QA(f"What did {hero} learn?", lessons[-1].group(1)))

    return enrich_questions(hero, questions[:6])


def full_answer(hero: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if lower.startswith("who is the main character"):
        return f"The main character is {answer}. The loss story follows {answer} as something important goes missing."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description shows what {hero} was like before the loss happened."
    if "where did" in lower and "search" in lower:
        return f"{hero} searched {answer}. The search shows that {hero} tried carefully before giving up or finding help."
    if "where did" in lower:
        return f"{hero} liked to spend time {answer}. That place is where the loss or search begins."
    if "what was lost" in lower:
        return f"The lost thing was the {answer}. Losing it creates the main problem in the story."
    if "how did" in lower and "feel" in lower:
        return f"{hero} felt {answer}. That feeling shows why the missing thing mattered."
    if "who returned" in lower:
        return f"{answer} returned the lost thing. That help changes the loss into relief."
    if "who helped" in lower:
        return f"{answer} helped with the search. Searching together made the problem less lonely."
    if "was the lost thing found" in lower:
        return f"{answer.capitalize()}. This answer tells whether the story ends with recovery or acceptance."
    if "what did" in lower and "learn" in lower:
        lesson = answer if answer.startswith("that ") else f"that {answer}"
        return f"{hero} learned {lesson}. The lesson gives meaning to the loss."
    return f"The answer is {answer}. This detail comes directly from the loss story."


def follow_up_for(hero: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes for {hero}?",
            f"{hero} begins with something familiar and then has to face losing it. The change is emotional as much as practical.",
        )
    if "what was lost" in lower or "feel" in lower:
        return (
            "Why does the loss matter?",
            "The loss matters because the missing thing has meaning to the character. It makes the character worried, sad, or careful.",
        )
    if "search" in lower or "returned" in lower or "helped" in lower:
        return (
            "What does the search show?",
            "The search shows effort and care. It also shows whether the character can ask for help or accept help from someone kind.",
        )
    if "found" in lower or "learn" in lower:
        return (
            "How does the ending handle the loss?",
            "The ending either restores the lost thing or helps the character accept what happened. That gives the story its emotional shape.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain what was missing, who helped, or how the character changed. It keeps the answer grounded in the story.",
    )


def enrich_questions(hero: str, questions: list[QA]) -> list[QA]:
    enriched: list[QA] = []
    for item in questions:
        answer = full_answer(hero, item.question, item.answer)
        follow_question, follow_answer = follow_up_for(hero, item.question)
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
                    ],
                }
                for qa in build_questions(story)
            ],
        },
        ensure_ascii=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate scripted loss tales.")
    parser.add_argument("-n", "--num", type=int, default=1000, help="Number of stories to print.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed.")
    parser.add_argument("--with-qa", action="store_true", help="Append generated questions and answers after each story.")
    parser.add_argument("--format", choices=("text", "jsonl"), default="text", help="Output format.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    stories = generate_unique_stories(args.num)

    if args.format == "jsonl":
        for story in stories:
            print(record_json(story))
    elif args.with_qa:
        print("\n\n\n\n".join(format_story_with_qa(story) for story in stories))
    else:
        print("\n\n\n\n".join(stories))


if __name__ == "__main__":
    main()
