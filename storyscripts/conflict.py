#!/usr/bin/env python3
"""
Conflict Tales Generator

Generate short scripted Conflict/Resolution-style stories with no runtime LLMs
and no external dependencies. The story shapes are inspired by TinyStories
kernels like:

    Conflict(A, B, cause=...)
    Resolution(share(...), lesson=...)
    Apology(...) + Repair(...) + Reconciliation(...)

Run this file to print 1,000 unique stories separated by four newlines.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass, field


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
class ConflictWorld:
    first: Character
    second: Character
    place: Place
    facts: set[str] = field(default_factory=set)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)

    def resolve(self) -> None:
        self.first.add(Memeplex("Repair", 1.0))
        self.second.add(Memeplex("Repair", 1.0))
        self.mark("resolved")


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str = ""
    follow_up_answer: str = ""


BOY_NAMES = ("Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn", "Theo", "Benny")
GIRL_NAMES = ("Lily", "Sara", "Mia", "Anna", "Ruby", "Zoe", "Clara", "Lucy", "Ivy", "Nina", "Emma")
ANIMAL_NAMES = ("Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo")

CHILD_TRAITS = ("creative", "curious", "playful", "sensitive", "stubborn", "kind", "careful", "excited", "friendly")
ANIMAL_TRAITS = ("playful", "small", "quick", "gentle", "curious", "friendly", "sleepy", "loyal", "happy")
KINDS = ("dog", "cat", "bunny", "rabbit", "bear", "frog", "mouse")

PLACES = (
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("park", "at the", frozenset({"outside", "play", "public"})),
    Place("playroom", "in the", frozenset({"inside", "home", "play"})),
    Place("school", "at", frozenset({"inside", "public"})),
    Place("backyard", "in the", frozenset({"outside", "home"})),
    Place("little house", "in the", frozenset({"inside", "home"})),
)

SPECIAL_THINGS = ("favorite chair", "shiny stone", "red crayon", "big brown ball", "toy truck", "pink dress", "blue snake", "soft blanket")
ACTIVITIES = ("drawing pictures", "playing with clay", "building a tower", "playing with cars", "rolling a stone", "making a pretend club")
REPAIRS = (
    "made a new shape from the broken pieces",
    "took turns and shared the special thing",
    "gave the toy back and asked to play together",
    "used both ideas in one picture",
    "made a new rule that felt fair",
    "said sorry and helped clean up",
)
LESSONS = (
    "sharing can make play better",
    "different ideas can both matter",
    "saying sorry helps repair hurt feelings",
    "taking turns is kinder than grabbing",
    "a mistake can become a new idea",
)


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


def polish_text(story: str) -> str:
    return re.sub(r"\. (a teacher|a kind neighbor) ", lambda m: f". {m.group(1).capitalize()} ", story)


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


def description(char: Character) -> str:
    return f"{' '.join(char.traits)} {char.intro_noun}".strip()


def choose_pair() -> tuple[Character, Character, Place]:
    for _ in range(80):
        first = choose_character(random.choice(("girl", "boy", "dog", "bunny", "cat")))
        second = choose_character(random.choice(("girl", "boy", "dog", "rabbit", "bear")), avoid=first.name)
        place = random.choice(PLACES)
        if first.name != second.name:
            return first, second, place
    return Character("Lily", "girl", ("creative", "kind"), "girl"), Character("Sam", "boy", ("curious", "friendly"), "boy"), PLACES[0]


def intro(first: Character, second: Character, place: Place) -> str:
    f_desc = description(first)
    s_desc = description(second)
    return (
        f"Once upon a time, there was {article(f_desc)} {f_desc} named {first.name}. "
        f"There was also {article(s_desc)} {s_desc} named {second.name}. "
        f"They spent the day {place.phrase}."
    )


def ending(world: ConflictWorld, fallback: str) -> str:
    if "resolved" in world.facts:
        if "sharing" in world.facts:
            return f"{world.first.name} and {world.second.name} learned that sharing can make play better."
        if "damage" in world.facts:
            return f"{world.first.name} and {world.second.name} learned that saying sorry helps repair hurt feelings."
        if "opinion" in world.facts:
            return f"{world.first.name} and {world.second.name} learned that different ideas can both matter."
        if "rough" in world.facts:
            return f"{world.first.name} and {world.second.name} learned that taking turns is kinder than grabbing."
        if "helper" in world.facts:
            return f"{world.first.name} and {world.second.name} learned that taking turns is kinder than grabbing."
        return f"{world.first.name} and {world.second.name} learned that {random.choice(LESSONS)}."
    return fallback


def sharing_conflict_story() -> str:
    first, second, place = choose_pair()
    world = ConflictWorld(first, second, place)
    thing = random.choice(("favorite chair", "shiny stone", "toy truck", "soft blanket"))

    story = f"""
{intro(first, second, place)}

{first.name} loved the {thing} and wanted to keep it close. Then {second.name} asked for a turn.

{first.name} said, "No, it is mine." {second.name} felt hurt, and a conflict began.

After a quiet moment, {first.name} saw {second.name}'s sad face. {first.name} moved over and said, "We can share it."

They took turns with the {thing}, and the game became more fun for both of them.
"""
    world.resolve()
    world.mark("sharing")
    return polish_text(clean(story + "\n" + ending(world, "The conflict was resolved.")))


def accidental_damage_story() -> str:
    first, second, place = choose_pair()
    world = ConflictWorld(first, second, place)
    thing = random.choice(("clay ball", "paper crown", "block tower", "painted card"))

    story = f"""
{intro(first, second, place)}

They were {random.choice(ACTIVITIES)} when {second.name} picked up {first.name}'s {thing}. By accident, it broke.

{first.name} felt sad and angry. {cap(first.subject)} said, "That was mine!"

{second.name} looked sorry and said, "I did not mean to break it." Then {second.name} helped repair it.

Together they {random.choice(REPAIRS)}.
"""
    world.resolve()
    world.mark("damage")
    return polish_text(clean(story + "\n" + ending(world, "The repair helped them feel better.")))


def opinion_conflict_story() -> str:
    first, second, place = choose_pair()
    world = ConflictWorld(first, second, place)
    first_choice, second_choice = random.choice((("red sun", "yellow sun"), ("blue house", "green house"), ("fast game", "slow game"), ("round tower", "tall tower")))

    story = f"""
{intro(first, second, place)}

{first.name} wanted a {first_choice}, but {second.name} wanted a {second_choice}. Each one thought only one idea could be right.

They argued for a little while. The conflict made the game feel smaller.

Then {first.name} said, "Maybe we can use both ideas." {second.name} nodded.

They made space for the {first_choice} and the {second_choice}. The work looked different, but it belonged to both of them.
"""
    world.resolve()
    world.mark("opinion")
    return polish_text(clean(story + "\n" + ending(world, "Both ideas mattered.")))


def rough_play_story() -> str:
    first, second, place = choose_pair()
    world = ConflictWorld(first, second, place)
    toy = random.choice(("ball", "truck", "stone", "kite", "toy car"))

    story = f"""
{intro(first, second, place)}

They were playing with a {toy}. Suddenly, {second.name} grabbed it and ran.

{first.name} shouted, and {second.name} shouted back. The conflict grew loud.

Then {second.name} stopped. {second.name} gave back the {toy} and said, "I got too rough."

{first.name} accepted the apology. They made a rule to ask before taking turns.
"""
    world.resolve()
    world.mark("rough")
    return polish_text(clean(story + "\n" + ending(world, "The game became gentle again.")))


def outside_helper_story() -> str:
    first, second, place = choose_pair()
    world = ConflictWorld(first, second, place)
    helper = random.choice(("Mom", "Dad", "a teacher", "a kind neighbor"))
    issue = random.choice(("who should go first", "which toy to use", "how to share the supplies", "where to build the tower"))

    story = f"""
{intro(first, second, place)}

{first.name} and {second.name} disagreed about {issue}. Both of them wanted to decide.

The argument made them stop playing. {helper} noticed and asked them to explain.

After listening, {helper} said, "You can solve this by taking turns and listening."

{first.name} and {second.name} tried again. This time, each one got a turn to choose.
"""
    world.resolve()
    world.mark("helper")
    return polish_text(clean(story + "\n" + ending(world, "Listening helped the conflict end.")))


STORY_SHAPES = (
    sharing_conflict_story,
    accidental_damage_story,
    opinion_conflict_story,
    rough_play_story,
    outside_helper_story,
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


def build_questions(story: str) -> list[QA]:
    questions: list[QA] = []
    names = re.findall(r"named ([A-Z][A-Za-z]+)", story)
    first = names[0] if names else "the first character"
    second = names[1] if len(names) > 1 else "the other character"

    if names:
        questions.append(QA("Who were the main characters in the conflict?", " and ".join(names[:2])))

    desc = re.search(r"there was (?:a|an) ([^.]+?) named " + re.escape(first), story)
    if desc:
        questions.append(QA(f"What kind of character was {first}?", desc.group(1)))

    place = re.search(r"They spent the day ([^.]+)\.", story)
    if place:
        questions.append(QA("Where did the conflict happen?", place.group(1)))

    cause_patterns = [
        (r"([A-Z][A-Za-z]+ said, \"No, it is mine\.\" [A-Z][A-Za-z]+ felt hurt)", None),
        (r"They were ([^.]+) when ([A-Z][A-Za-z]+) picked up ([A-Z][A-Za-z]+)'s ([^.]+)\. By accident, it broke\.", "the {thing} broke after {actor} picked it up during {activity}"),
        (r"(Each one thought only one idea could be right)\.", None),
        (r"Suddenly, ([A-Z][A-Za-z]+) grabbed it and ran\.", "{actor} grabbed the toy and ran"),
        (r"([A-Z][A-Za-z]+ and [A-Z][A-Za-z]+ disagreed about [^.]+)\.", None),
    ]
    for pattern, template in cause_patterns:
        cause = re.search(pattern, story)
        if cause:
            if template:
                answer = template.format(
                    activity=cause.group(1),
                    actor=cause.group(2) if cause.lastindex and cause.lastindex >= 2 else cause.group(1),
                    thing=cause.group(4) if cause.lastindex and cause.lastindex >= 4 else "toy",
                )
            else:
                answer = cause.group(1)
            questions.append(QA("What caused the conflict?", answer))
            break

    feeling = re.search(re.escape(first) + r" felt ([^.!?\n]+)[.!?]", story)
    if feeling:
        questions.append(QA(f"How did {first} feel?", feeling.group(1)))

    apology = re.search(r"(?:Then )?([A-Z][A-Za-z]+) (?:looked sorry and |gave back [^.]+ and )?said, \"([^\"]*(?:sorry|rough|mean)[^\"]*)\"", story)
    if apology:
        questions.append(QA("Who apologized or repaired the problem?", apology.group(1)))

    repair_patterns = [
        (r"They took turns with the ([^,]+),", "they took turns with the \\1"),
        (r"Together they ([^.]+)\.", "they \\1"),
        (r"They made space for the ([^.]+)\.", "they made space for the \\1"),
        (r"They made a rule to ([^.]+)\.", "they made a rule to \\1"),
        (r"This time, each one got ([^.]+)\.", "each one got \\1"),
    ]
    for pattern, template in repair_patterns:
        repair = re.search(pattern, story)
        if repair:
            questions.append(QA("How was the conflict resolved?", repair.expand(template)))
            break

    lesson = re.search(r"learned that ([^.]+)\.", story)
    if lesson:
        questions.append(QA("What lesson did the characters learn?", lesson.group(1)))

    return enrich_questions(first, second, questions[:6])


def full_answer(first: str, second: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if "main characters" in lower:
        return f"The main characters are {answer}. The conflict story follows how they disagree and then repair the problem."
    if "what kind of character" in lower:
        return f"{first} was {article(answer)} {answer}. That description helps show who {first} is before the conflict starts."
    if "where did" in lower:
        return f"The conflict happened {answer}. The setting gives the disagreement a clear place."
    if "what caused" in lower:
        cause = answer
        return f"The conflict started because {cause}. That moment created hurt feelings or disagreement."
    if "how did" in lower and "feel" in lower:
        return f"{first} felt {answer}. That feeling shows why the conflict mattered."
    if "who apologized" in lower:
        return f"{answer} apologized or helped repair the problem. That response moved the story toward reconciliation."
    if "how was" in lower and "resolved" in lower:
        return f"The conflict was resolved when {answer}. The repair gave both characters a way back into play."
    if "lesson" in lower:
        return f"They learned that {answer}. The lesson gives meaning to the disagreement."
    return f"The answer is {answer}. This detail comes directly from the conflict story."


def follow_up_for(first: str, second: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main characters" in lower:
        return (
            "How does their relationship change?",
            f"{first} and {second} move from disagreement toward repair. The story shows that conflict does not have to end the friendship.",
        )
    if "caused" in lower or "feel" in lower:
        return (
            "Why does the conflict matter?",
            "The conflict matters because it shows a real feeling or need. The characters have to notice the hurt before they can repair it.",
        )
    if "apologized" in lower or "resolved" in lower:
        return (
            "What does the repair show?",
            "The repair shows that someone chose kindness after the disagreement. It turns the conflict into a chance to learn.",
        )
    if "lesson" in lower:
        return (
            "How does the lesson complete the story?",
            "The lesson completes the story by naming what changed. It helps the disagreement become useful instead of only upsetting.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain the people, place, cause, or repair. It keeps the answer grounded in the story.",
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
    parser = argparse.ArgumentParser(description="Generate scripted conflict tales.")
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
