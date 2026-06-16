#!/usr/bin/env python3
"""
Discovery Tales Generator

Generate short scripted Discovery-style stories with no runtime LLMs and no
external dependencies. The story shapes are inspired by TinyStories kernels like:

    Discovery(hero, state=..., catalyst=Find(...), process=..., transformation=...)
    Journey(hero, process=Explore(...) + Discover(...), insight=...)
    Discover(object, content=...)

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
class DiscoveryWorld:
    hero: Character
    place: Place
    facts: set[str] = field(default_factory=set)
    carriers: dict[str, dict[str, float]] = field(default_factory=dict)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)

    def embed(self, carrier: str, meme: Memeplex) -> None:
        self.carriers.setdefault(carrier, {})
        self.carriers[carrier][meme.name] = self.carriers[carrier].get(meme.name, 0.0) + meme.weight
        if carrier == self.hero.name:
            self.hero.add(meme)


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str = ""
    follow_up_answer: str = ""


# =============================================================================
# VOCABULARY
# =============================================================================


BOY_NAMES = ("Timmy", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn", "Theo", "Remy")
GIRL_NAMES = ("Lily", "Mia", "Sue", "Olive", "Ruby", "Zoe", "Clara", "Lucy", "Ivy", "Nina", "Ella")
ANIMAL_NAMES = ("Timmy", "Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo")

CHILD_TRAITS = ("curious", "playful", "hopeful", "careful", "brave", "eager", "kind", "patient", "adventurous")
ANIMAL_TRAITS = ("curious", "small", "quick", "hungry", "gentle", "bright", "playful", "careful", "sleepy")
KINDS = ("mouse", "frog", "rat", "bear", "cat", "dog", "bunny", "bird")

PLACES = (
    Place("garden", "in the", frozenset({"outside", "plants", "hidden"})),
    Place("park", "at the", frozenset({"outside", "public", "play"})),
    Place("forest", "in the", frozenset({"outside", "wild", "hidden"})),
    Place("kitchen", "in the", frozenset({"inside", "food"})),
    Place("bedroom", "in the", frozenset({"inside", "home"})),
    Place("backyard", "in the", frozenset({"outside", "home"})),
    Place("cave", "in the", frozenset({"inside", "hidden", "rock"})),
    Place("swamp", "in the", frozenset({"outside", "water", "wild"})),
    Place("beach", "on the", frozenset({"outside", "water"})),
)

ROUTINES = (
    "played near a favorite leaf", "collected shiny rocks", "rode a little bike",
    "looked for colorful leaves", "walked slowly and listened", "played with toy cars",
    "sang a happy song", "helped tidy a shelf", "watched the clouds",
)
DISCOVERIES = (
    "shiny mark", "old toy car", "secret path", "tiny box", "glowing rock",
    "lost necklace", "big piece of cheese", "hidden pond", "small map",
    "toy airplane", "magic wand", "sparkly shell",
)
CONTAINERS = ("box", "treasure chest", "paper bag", "old jar", "wooden case", "toy basket")
CONTENTS = ("gold coins", "a hungry kitten", "a silver key", "bright beads", "a folded map", "a soft scarf")
OBSTACLES = (
    "a storm began outside", "a tall shelf stood in the way", "a careful grown-up said to wait",
    "a loud noise made everything feel strange", "a muddy patch blocked the path",
    "a shadow made the place look scary",
)
HELPERS = ("Mom", "Dad", "Grandma", "a friendly duck", "a little turtle", "a kind neighbor")
LESSONS = (
    "small discoveries can become big memories",
    "being curious works best with care",
    "a discovery is better when it is shared",
    "waiting can keep something special safe",
    "looking closely can turn worry into wonder",
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


def choose_place(hero: Character) -> Place:
    choices = list(PLACES)
    if hero.kind in {"fish", "duck"}:
        choices = [p for p in choices if "water" in p.tags]
    if hero.kind == "bear":
        choices += [p for p in PLACES if p.name in {"cave", "forest"}]
    return random.choice(choices)


def description(char: Character) -> str:
    return f"{' '.join(char.traits)} {char.intro_noun}".strip()


def intro(char: Character, place: Place) -> str:
    desc = description(char)
    return f"Once upon a time, there was {article(desc)} {desc} named {char.name}. {char.name} spent many days {place.phrase}."


def ending(world: DiscoveryWorld, fallback: str) -> str:
    wonder = world.hero.memes.get("Wonder", 0.0)
    pride = world.hero.memes.get("Pride", 0.0)
    care = world.hero.memes.get("Care", 0.0)
    if care >= 0.8:
        return f"{world.hero.name} learned that a discovery is better when it is shared."
    if pride >= 0.8:
        return f"{world.hero.name} felt proud because careful work had made the discovery shine."
    if wonder >= 0.8:
        return f"{world.hero.name} remembered that looking closely can turn an ordinary day into wonder."
    return fallback


# =============================================================================
# STORY SHAPES
# =============================================================================


def hidden_treasure_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "mouse", "bunny")))
    place = choose_place(hero)
    world = DiscoveryWorld(hero, place)
    routine = random.choice(ROUTINES)
    discovery = random.choice(("shiny mark", "small map", "sparkly shell", "silver key"))

    story = f"""
{intro(hero, place)} Every day, {hero.subject} {routine}.

One day, {hero.name} noticed {article(discovery)} {discovery} where no one else had looked. {cap(hero.subject)} bent close and felt excited.

At first, {hero.name} wanted to run away and tell everyone. Then {hero.subject} decided to stay nearby so the discovery would not get lost.

Soon friends came to see it. They were amazed, and {hero.name} felt proud to show them.
"""
    world.embed(hero.name, Memeplex("Pride", 0.9))
    world.embed(hero.name, Memeplex("Care", 0.4))
    return clean(story + "\n" + ending(world, "The discovery became a special memory."))


def clean_and_reveal_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "cat", "dog")))
    place = choose_place(hero)
    world = DiscoveryWorld(hero, place)
    thing = random.choice(("toy car", "wooden boat", "painted box", "little bell", "old spoon", "tiny drum"))
    obstacle = random.choice(OBSTACLES)

    story = f"""
{intro(hero, place)} One morning, {hero.name} found {article(thing)} {thing} under some dust.

The {thing} looked dull and forgotten. {hero.name} got a soft cloth and cleaned it slowly.

Then trouble came. {cap(obstacle)}. {hero.name} kept the {thing} safe and waited.

When the trouble passed, the {thing} was bright again. {hero.name} showed it to {random.choice(HELPERS)} with a big smile.
"""
    world.embed(hero.name, Memeplex("Pride", 1.0))
    return clean(story + "\n" + ending(world, "The discovery was worth the careful work."))


def found_friend_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bear", "frog")))
    place = choose_place(hero)
    world = DiscoveryWorld(hero, place)
    container = random.choice(CONTAINERS)
    content = random.choice(("a hungry kitten", "a tiny bird", "a sleepy puppy", "a lost bunny"))

    story = f"""
{intro(hero, place)} {cap(hero.subject)} heard a small sound coming from {article(container)} {container}.

{hero.name} opened it gently and discovered {content} inside. The little animal looked hungry and scared.

{hero.name} brought food and spoke in a soft voice. Slowly, the animal came closer.

By the end of the day, the discovery had become a new friend.
"""
    world.embed(hero.name, Memeplex("Care", 1.0))
    world.embed(hero.name, Memeplex("Wonder", 0.6))
    return clean(story + "\n" + ending(world, "Kindness helped the discovery feel safe."))


def magical_place_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bear", "rat")))
    place = choose_place(hero)
    world = DiscoveryWorld(hero, place)
    discovered = random.choice(("glowing rock", "secret path", "hidden pond", "tiny door", "silver feather"))
    feeling = random.choice(("safe", "brave", "happy", "quiet inside", "full of wonder"))

    story = f"""
{intro(hero, place)} {cap(hero.subject)} wanted to explore a little farther than usual.

Past a familiar path, {hero.name} discovered {article(discovered)} {discovered}. It made the whole place feel magical.

{hero.name} watched carefully instead of grabbing it. The discovery seemed to glow brighter when {hero.subject} stayed gentle.

After a while, {hero.name} went home feeling {feeling} and promised to visit again.
"""
    world.embed(hero.name, Memeplex("Wonder", 1.0))
    return clean(story + "\n" + ending(world, "The magical place stayed in the hero's memory."))


def obstacle_reward_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "rat", "mouse")))
    place = choose_place(hero)
    world = DiscoveryWorld(hero, place)
    reward = random.choice(("cheese", "ice cream", "blueberry muffin", "warm cookie", "sweet apple"))
    obstacle = random.choice(("a steep hill", "a sleepy cat", "a locked gate", "a muddy path", "a high shelf"))

    story = f"""
{intro(hero, place)} {cap(hero.subject)} smelled something delicious and followed the smell.

Soon {hero.name} discovered {article(reward)} {reward}, but {obstacle} stood in the way.

{hero.name} stopped and made a careful plan. Step by step, {hero.subject} found a safe way around the problem.

At last, {hero.name} reached the {reward}. The treat tasted even better because the search had been hard.
"""
    world.embed(hero.name, Memeplex("Pride", 0.7))
    world.embed(hero.name, Memeplex("Wonder", 0.5))
    return clean(story + f"\n{hero.name} learned that being curious works best with care.")


STORY_SHAPES = (
    hidden_treasure_story,
    clean_and_reveal_story,
    found_friend_story,
    magical_place_story,
    obstacle_reward_story,
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

    place = re.search(re.escape(hero) + r" spent many days ([^.]+)\.", story)
    if place:
        questions.append(QA(f"Where did {hero} spend many days?", place.group(1)))

    found = re.search(re.escape(hero) + r" (?:noticed|found|discovered|opened it gently and discovered) (?:a|an)? ?([^.,]+)", story)
    if found:
        questions.append(QA(f"What did {hero} discover?", found.group(1).strip()))

    problem = re.search(r"Then trouble came\. ([^.]+)\.", story)
    if problem:
        questions.append(QA("What trouble happened after the discovery?", problem.group(1)))

    obstacle = re.search(r"but (a|an) ([^.]+) stood in the way\.", story)
    if obstacle:
        questions.append(QA("What stood in the way?", f"{obstacle.group(1)} {obstacle.group(2)}"))

    response_patterns = [
        (re.escape(hero) + r" watched carefully instead of grabbing it\.", "by watching carefully instead of grabbing it"),
        (re.escape(hero) + r" brought food and spoke in a soft voice\.", "by bringing food and speaking in a soft voice"),
        (re.escape(hero) + r" kept the ([^.]+) safe and waited\.", "by keeping the \\1 safe and waiting"),
        (re.escape(hero) + r" stopped and made a careful plan\.", "by stopping and making a careful plan"),
        (re.escape(hero) + r" decided to stay nearby so the discovery would not get lost\.", "by staying nearby so the discovery would not get lost"),
    ]
    for pattern, template in response_patterns:
        response = re.search(pattern, story)
        if response:
            answer = response.expand(template)
            questions.append(QA(f"How did {hero} respond?", answer))
            break

    ending_match = list(re.finditer(re.escape(hero) + r" (learned|felt|remembered) ([^.]+)\.", story))
    if ending_match:
        final = ending_match[-1]
        verb, answer = final.group(1), final.group(2)
        if verb == "learned":
            questions.append(QA(f"What did {hero} learn?", answer))
        elif verb == "felt":
            questions.append(QA(f"How did {hero} feel at the end?", answer))
        else:
            questions.append(QA(f"What did {hero} remember?", answer))

    return enrich_questions(hero, questions[:6])


def full_answer(hero: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if lower.startswith("who is the main character"):
        return f"The main character is {answer}. The discovery story follows {answer} as something hidden or surprising is found."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description shows what {hero} was like before the discovery."
    if "where did" in lower:
        return f"{hero} spent many days {answer}. This setting is where the ordinary day begins."
    if "what did" in lower and "discover" in lower:
        thing = answer if answer.startswith(("a ", "an ", "the ")) else f"{article(answer)} {answer}"
        return f"{hero} discovered {thing}. The discovery changes the ordinary day into something special."
    if "trouble happened" in lower:
        return f"The trouble was that {answer.lower()}. This tested whether {hero} could protect or understand the discovery."
    if "stood in the way" in lower:
        return f"{answer.capitalize()} stood in the way. The obstacle made {hero} slow down and make a careful plan."
    if "how did" in lower and "respond" in lower:
        response = answer if answer.startswith("by ") else f"by {answer}"
        return f"{hero} responded {response}. The response shows care instead of grabbing or rushing."
    if "what did" in lower and "learn" in lower:
        return f"{hero} learned {answer}. The lesson connects curiosity with care."
    if "how did" in lower and "feel" in lower:
        return f"{hero} felt {answer}. That feeling shows what the discovery meant by the end."
    if "remember" in lower:
        memory = answer[5:] if answer.startswith("that ") else answer
        return f"{hero} remembered that {memory}. This turns the discovery into a lasting idea."
    return f"The answer is {answer}. This detail comes directly from the discovery story."


def follow_up_for(hero: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes for {hero}?",
            f"{hero} begins in an ordinary place and then notices something new. The discovery gives {hero} a choice about how to act.",
        )
    if "discover" in lower:
        return (
            "Why is the discovery important?",
            "The discovery is important because it creates the main turn in the story. It gives the character something to protect, understand, share, or enjoy.",
        )
    if "trouble" in lower or "stood in the way" in lower:
        return (
            "Why does the obstacle matter?",
            "The obstacle matters because it keeps the discovery from being too easy. It asks the character to be careful and patient.",
        )
    if "respond" in lower:
        return (
            "What does that response show?",
            "The response shows that curiosity can be gentle. The character treats the discovery as something worth caring for.",
        )
    if "learn" in lower or "feel" in lower or "remember" in lower:
        return (
            "How does the ending complete the discovery?",
            "The ending completes the discovery by showing what the character understands or feels afterward. The found thing becomes part of a lesson or memory.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain the ordinary beginning, the hidden discovery, or the careful ending. It keeps the story grounded in the text.",
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
    parser = argparse.ArgumentParser(description="Generate scripted discovery tales.")
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
