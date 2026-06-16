#!/usr/bin/env python3
"""
Friendship Tales Generator

Generate short scripted Friendship-style stories with no runtime LLMs and no
external dependencies. The story shapes are inspired by TinyStories kernels like:

    Friendship(A, B)
    Conflict(...), Resolution(Friendship(...) + Lesson(...))
    Help(A, target=B) + Friendship(A, B)
    Adventure(A + B, state=Routine + Friendship, process=..., resolution=...)

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
    tags: frozenset[str] = frozenset()
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
class FriendshipWorld:
    first: Character
    second: Character
    place: Place
    links: dict[tuple[str, str], float] = field(default_factory=dict)

    def bond(self, a: Character, b: Character, amount: float = 0.5) -> None:
        key = tuple(sorted((a.name, b.name)))
        self.links[key] = self.links.get(key, 0.0) + amount
        a.add(Memeplex("Friendship", amount))
        b.add(Memeplex("Friendship", amount))

    def trust(self) -> float:
        key = tuple(sorted((self.first.name, self.second.name)))
        return self.links.get(key, 0.0)


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
    "Lily", "Mia", "Anna", "Ruby", "Zoe", "Clara", "Lucy",
    "Ivy", "Nina", "Ella", "Maya", "Rose", "Violet", "Sophie",
)
ANIMAL_NAMES = (
    "Bobo", "Spot", "Pip", "Nibbles", "Teddy", "Sunny", "Coco",
    "Pebble", "Poppy", "Daisy", "Flame", "Blue", "Bean",
)

CHILD_TRAITS = (
    "curious", "quiet", "playful", "careful", "brave", "gentle",
    "eager", "kind", "shy", "cheerful", "patient", "hopeful",
)
ANIMAL_TRAITS = (
    "friendly", "small", "restless", "quick", "happy", "curious",
    "helpful", "furry", "bright", "sleepy", "loyal", "gentle",
)

KINDS = ("cat", "dog", "bird", "bunny", "bear", "frog", "puppy", "kitten")

PLACES = (
    Place("park", "at the", frozenset({"outside", "play", "public"})),
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("school", "at", frozenset({"inside", "public", "children"})),
    Place("library", "at the", frozenset({"inside", "quiet", "books"})),
    Place("beach", "on the", frozenset({"outside", "water"})),
    Place("forest", "in the", frozenset({"outside", "trees"})),
    Place("playground", "at the", frozenset({"outside", "play"})),
    Place("little hill", "on the", frozenset({"outside", "view"})),
    Place("backyard", "in the", frozenset({"outside", "home"})),
)

ACTIVITIES = (
    "build a tower", "draw a picture", "kick a ball", "look for shells",
    "sort shiny stones", "sing a song", "make a tiny boat", "plant seeds",
    "play dress-up", "read a funny book", "fly a kite",
)
PROBLEMS = (
    "the tower fell down", "the ball rolled under a bench",
    "the kite string got tangled", "the picture tore a little",
    "the boat tipped over", "the seeds spilled on the ground",
    "the book dropped into a puddle", "the shiny stones scattered everywhere",
)
HELP_ACTIONS = (
    "held the string steady", "picked up the pieces", "found the missing part",
    "shared a better idea", "carried the heavy bag", "stood close and listened",
    "showed a safe path", "gave a gentle push",
)
MAGIC_THINGS = (
    "moving rainbow", "glowing leaf", "tiny door", "singing shell",
    "sparkly map", "silver feather", "friendly cloud",
)
LESSONS = (
    "friends listen before they speak",
    "sharing makes play feel bigger",
    "a kind helper can become a true friend",
    "friendship grows when someone says sorry",
    "different friends can enjoy the same adventure",
    "being gentle keeps a friendship strong",
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


def choose_character(kind: str | None = None, avoid: str = "") -> Character:
    if kind is None:
        kind = random.choice(("girl", "boy") + KINDS)
    if kind == "girl":
        name = random.choice([n for n in GIRL_NAMES if n != avoid])
        return Character(name, "girl", tuple(random.sample(CHILD_TRAITS, 2)), "girl")
    if kind == "boy":
        name = random.choice([n for n in BOY_NAMES if n != avoid])
        return Character(name, "boy", tuple(random.sample(CHILD_TRAITS, 2)), "boy")
    name = random.choice([n for n in ANIMAL_NAMES if n != avoid])
    return Character(name, kind, tuple(random.sample(ANIMAL_TRAITS, 2)))


def compatible(a: Character, b: Character, place: Place) -> bool:
    if a.name == b.name:
        return False
    if place.name == "library" and ("restless" in a.traits or "restless" in b.traits):
        return False
    if "water" in place.tags and (a.kind == "kitten" or b.kind == "kitten"):
        return False
    return True


def choose_pair(place: Place | None = None) -> tuple[Character, Character, Place]:
    for _ in range(80):
        place = place or random.choice(PLACES)
        first = choose_character()
        second = choose_character(avoid=first.name)
        if compatible(first, second, place):
            return first, second, place
    first = Character("Lily", "girl", ("kind", "patient"), "girl")
    second = Character("Pip", "bird", ("small", "friendly"))
    return first, second, Place("garden", "in the", frozenset({"outside", "plants"}))


def intro(char: Character) -> str:
    desc = description(char)
    return f"there was {article(desc)} {desc} named {char.name}"


def description(char: Character) -> str:
    traits = " ".join(char.traits)
    return f"{traits} {char.intro_noun}".strip()


def ending(world: FriendshipWorld, fallback: str) -> str:
    trust = world.trust()
    if trust >= 1.0:
        return f"{world.first.name} and {world.second.name} became close friends and remembered that {random.choice(LESSONS)}."
    if trust >= 0.6:
        return f"{world.first.name} and {world.second.name} became friends because they chose kindness."
    return fallback


# =============================================================================
# STORY SHAPES
# =============================================================================


def new_friend_story() -> str:
    first, second, place = choose_pair()
    world = FriendshipWorld(first, second, place)
    activity = random.choice(ACTIVITIES)
    shared = random.choice(("took turns", "laughed together", "made room for each other", "tried again together"))

    story = f"""
Once upon a time, {intro(first)}. {cap(first.subject)} liked to spend quiet time {place.phrase}.

One day, {first.name} saw {second.name}, {article(description(second))} {description(second)}, trying to {activity}. {first.name} felt a little shy, but {first.subject} said hello.

{second.name} smiled and asked, "Do you want to play too?" Soon they {shared}.

The game felt better with two friends instead of one. {first.name} and {second.name} promised to meet again.
"""
    world.bond(first, second, 0.8)
    return clean(story + "\n" + ending(world, "They had made a new friendship."))


def repaired_conflict_story() -> str:
    first, second, place = choose_pair()
    world = FriendshipWorld(first, second, place)
    activity = random.choice(ACTIVITIES)
    problem = random.choice(PROBLEMS)

    story = f"""
Once upon a time, {intro(first)}. There was also {article(description(second))} {description(second)} named {second.name}.

{first.name} and {second.name} were {place.phrase} and wanted to {activity}. At first, both of them wanted to choose every rule.

Then trouble came. {cap(problem)}. {first.name} blamed {second.name}, and {second.name} looked hurt.

After a quiet moment, {first.name} said, "I'm sorry. We can fix it together." {second.name} nodded and helped.

They fixed the problem more easily as a team.
"""
    world.bond(first, second, 1.0)
    return clean(story + "\n" + ending(world, "Their friendship became stronger."))


def helper_friendship_story() -> str:
    first, second, place = choose_pair()
    world = FriendshipWorld(first, second, place)
    need = random.choice(PROBLEMS)
    help_action = random.choice(HELP_ACTIONS)

    story = f"""
Once upon a time, {intro(first)}. {cap(first.subject)} was walking {place.phrase}.

Nearby, {second.name} was upset because {need}. {first.name} stopped and asked, "Do you need help?"

{second.name} said yes. {first.name} {help_action}, and {second.name} tried again.

The problem did not feel so big anymore. {second.name} thanked {first.name} and asked to stay together for a while.

Helping had turned two strangers into friends.
"""
    world.bond(first, second, 0.9)
    return clean(story + "\n" + ending(world, "Kindness began the friendship."))


def magical_adventure_story() -> str:
    first, second, place = choose_pair()
    world = FriendshipWorld(first, second, place)
    magic = random.choice(MAGIC_THINGS)
    sight = random.choice(("tiny stars", "bright flowers", "silver paths", "soft clouds", "dancing lights"))

    story = f"""
Once upon a time, {intro(first)}. {first.name}'s good friend {second.name} came to play with {first.name} {place.phrase}.

While they were playing, they found {article(magic)} {magic}. It shimmered and invited them closer.

{first.name} and {second.name} stayed close and followed it. They saw {sight} and whispered, "Wow."

When the wonder faded, the two friends were back {place.phrase}. They laughed because the adventure was even better together.
"""
    world.bond(first, second, 1.1)
    return clean(story + "\n" + ending(world, "The shared adventure became their favorite story."))


def unlikely_friends_story() -> str:
    place = random.choice([p for p in PLACES if p.name not in {"library", "beach"}])
    first, second, place = choose_pair(place)
    world = FriendshipWorld(first, second, place)
    difference = random.choice((
        f"{first.name} liked quiet games, but {second.name} liked noisy games",
        f"{first.name} moved slowly, but {second.name} moved quickly",
        f"{first.name} liked to plan, but {second.name} liked surprises",
        f"{first.name} was shy, but {second.name} liked saying hello",
    ))
    activity = random.choice(ACTIVITIES)

    story = f"""
Once upon a time, {intro(first)}. There was also {article(description(second))} {description(second)} named {second.name}.

At first, they seemed too different to be friends. {difference}.

Then they both wanted to {activity}. {first.name} shared one idea, and {second.name} shared another.

Their two ideas worked well together. By the end of the day, each one liked something new.
"""
    world.bond(first, second, 0.85)
    return clean(story + "\n" + ending(world, "Different ways of playing made the friendship richer."))


STORY_SHAPES = (
    new_friend_story,
    repaired_conflict_story,
    helper_friendship_story,
    magical_adventure_story,
    unlikely_friends_story,
)


def generate_unique_stories(count: int) -> list[str]:
    stories: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(stories) < count and attempts < count * 80:
        attempts += 1
        story = random.choice(STORY_SHAPES)()
        key = story[:220] + story[-220:]
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
    names = re.findall(r"named ([A-Z][A-Za-z]+)", story)
    comma_friend = re.search(r"saw ([A-Z][A-Za-z]+), (?:a|an) ", story)
    if comma_friend:
        names.append(comma_friend.group(1))
    friend_match = re.search(r"friend ([A-Z][A-Za-z]+) came to meet", story)
    if friend_match:
        names.append(friend_match.group(1))
    names = list(dict.fromkeys(names))
    first = names[0] if names else "the first character"
    second = names[1] if len(names) > 1 else "the other character"

    if names:
        questions.append(QA("Who are the main friends in the story?", " and ".join(names[:2])))

    desc = re.search(r"there was (?:a|an) ([^.]+?) named " + re.escape(first), story)
    if desc:
        questions.append(QA(f"What kind of character was {first}?", desc.group(1)))

    place = re.search(r"(?:time|visit|back) ((?:at|in|on) the [^.]+|at school)\.", story)
    if place:
        questions.append(QA("Where did the friendship story happen?", place.group(1)))

    problem = re.search(r"Then trouble came\. ([^.]+)\.", story)
    if problem:
        questions.append(QA("What problem happened?", problem.group(1)))

    apology = re.search(r'"I\'m sorry\. ([^"]+)"', story)
    if apology:
        questions.append(QA(f"What did {first} say to repair the friendship?", f"I'm sorry. {apology.group(1)}"))

    help_action = re.search(re.escape(first) + r" ([^.]+), and " + re.escape(second) + r" tried again\.", story)
    if help_action:
        questions.append(QA(f"How did {first} help {second}?", help_action.group(1)))

    magic = re.search(r"they found (?:a|an) ([^.]+)\.", story)
    if magic:
        questions.append(QA("What magical thing did the friends find?", magic.group(1)))

    lesson = re.search(r"remembered that ([^.]+)\.", story)
    if lesson:
        questions.append(QA("What did the friends remember?", lesson.group(1)))
    elif "became friends because" in story:
        reason = re.search(r"became friends because ([^.]+)\.", story)
        if reason:
            questions.append(QA("Why did the characters become friends?", reason.group(1)))

    return enrich_questions(first, second, questions[:6])


def full_answer(first: str, second: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if "main friends" in lower:
        return f"The main friends are {answer}. The story focuses on how their friendship begins, changes, or grows stronger."
    if "what kind of character" in lower:
        return f"{first} was {article(answer)} {answer}. This introduction helps show what {first} was like before the friendship moment."
    if "where did" in lower:
        return f"The story happened {answer}. That setting gives the friends a place to meet, play, help, or repair a problem."
    if "what problem happened" in lower:
        return f"The problem was that {answer.lower()}. The problem gives the characters a chance to choose kindness."
    if "repair the friendship" in lower:
        return f"{first} said, \"{answer}\". The apology matters because it turns hurt feelings into a chance to work together."
    if "how did" in lower and "help" in lower:
        return f"{first} helped by {answer}. The help shows that friendship can begin with one careful, kind action."
    if "magical thing" in lower:
        thing = answer if answer.startswith(("a ", "an ", "the ")) else f"{article(answer)} {answer}"
        return f"The friends found {thing}. The magical discovery gave them an adventure they could share."
    if "remember" in lower:
        return f"The friends remembered that {answer}. That lesson explains what the friendship taught them."
    if "why did" in lower and "become friends" in lower:
        return f"They became friends because {answer}. The reason shows the emotional center of the story."
    return f"The answer is {answer}. This detail is grounded in the friendship story."


def follow_up_for(first: str, second: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main friends" in lower:
        return (
            "How does their relationship change?",
            f"{first} and {second} become closer through play, help, apology, or a shared adventure. The story treats friendship as something built through action.",
        )
    if "problem" in lower or "repair" in lower:
        return (
            "Why is the repair important?",
            "The repair is important because friendship is tested by the problem. The characters choose to fix the hurt instead of staying upset.",
        )
    if "help" in lower:
        return (
            "What does the helping moment show?",
            "The helping moment shows that a friend notices when someone needs support. It turns care into something visible.",
        )
    if "magical" in lower:
        return (
            "Why is sharing the adventure important?",
            "Sharing the adventure is important because the wonder belongs to both friends. It gives them a memory they can keep together.",
        )
    if "remember" in lower or "become friends" in lower:
        return (
            "What is the lesson about friendship?",
            "The lesson is that friendship grows through kindness, listening, sharing, and repair. The ending names the value of staying gentle with each other.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain how the friendship starts or changes. It points to the setting, the challenge, or the kindness in the story.",
    )


def enrich_questions(first: str, second: str, questions: list[QA]) -> list[QA]:
    enriched: list[QA] = []
    for item in questions:
        answer = full_answer(first, second, item.question, item.answer)
        follow_question, follow_answer = follow_up_for(first, second, item.question)
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
    parser = argparse.ArgumentParser(description="Generate scripted friendship tales.")
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
