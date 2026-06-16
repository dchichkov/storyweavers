#!/usr/bin/env python3
"""
Surprise Tales Generator

Generate short scripted Surprise/Reveal/Secret-style stories with no runtime LLMs
and no external dependencies. The story shapes are inspired by TinyStories
kernels like:

    Surprise(Butterfly, nose)
    Open(box) + Surprise(cake)
    Reveal(fan)
    Secret(Bug, reveal=HiddenDoor)

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
class SurpriseWorld:
    hero: Character
    place: Place
    ordinary: str = ""
    surprise: str = ""
    reaction: str = ""
    facts: set[str] = field(default_factory=set)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str = ""
    follow_up_answer: str = ""


BOY_NAMES = ("Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn", "Theo", "Owen", "Remy")
GIRL_NAMES = ("Lily", "Mia", "Sue", "Anna", "Ruby", "Zoe", "Clara", "Lucy", "Ivy", "Nina", "Ella", "Molly")
ANIMAL_NAMES = ("Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo", "Snowy")

CHILD_TRAITS = ("curious", "playful", "careful", "excited", "kind", "patient", "brave", "gentle", "hopeful")
ANIMAL_TRAITS = ("soft", "playful", "curious", "small", "friendly", "patient", "happy", "quick", "gentle")
KINDS = ("cow", "cat", "dog", "duck", "mouse", "bunny")

PLACES = (
    Place("meadow", "in the", frozenset({"outside", "wild"})),
    Place("park", "at the", frozenset({"outside", "public"})),
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("bedroom", "in the", frozenset({"inside", "home"})),
    Place("playroom", "in the", frozenset({"inside", "play"})),
    Place("yard", "in the", frozenset({"outside", "home"})),
    Place("shop", "at the", frozenset({"inside", "public"})),
    Place("creek", "by the", frozenset({"outside", "water"})),
)

BOX_ITEMS = ("big cake", "pretty fan", "toy bird", "map to a secret room", "bag of bright beads", "tiny music box")
SECRET_PLACES = ("secret playroom", "hidden door", "tiny room in a tree", "magical garden", "little cave full of toys")
MISTAKEN_SIGHTS = (
    ("red balloon", "emergency in the sky"),
    ("kite tail", "snake in the tree"),
    ("shadow of a hat", "strange animal"),
    ("round red ball", "fire in the clouds"),
)
SKILLS = ("sew", "make paper boats", "weigh shiny stones", "bake tiny cakes", "tie safe knots", "paint flowers")
MAGIC_IDENTITIES = (
    ("talking duck", "magic bird that could grant wishes"),
    ("sleepy dog", "princess under a spell"),
    ("tiny bug", "guide to a hidden world"),
    ("quiet shell", "fairy house with a tiny door"),
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


def intro(char: Character, place: Place) -> str:
    desc = description(char)
    return f"Once upon a time, there was {article(desc)} {desc} named {char.name}. {char.name} spent the day {place.phrase}."


def ending(world: SurpriseWorld, fallback: str) -> str:
    joy = world.hero.memes.get("Joy", 0.0)
    caution = world.hero.memes.get("Caution", 0.0)
    wonder = world.hero.memes.get("Wonder", 0.0)
    if caution >= 0.8:
        return f"{world.hero.name} learned that a surprise is easier to understand after looking closely."
    if wonder >= 0.8:
        return f"{world.hero.name} remembered that ordinary places can hide wonderful secrets."
    if joy >= 0.8:
        return f"{world.hero.name} learned that happy surprises are even better when they are shared."
    return fallback


def animal_surprise_story() -> str:
    hero = choose_character(random.choice(("cow", "cat", "dog", "bunny")))
    place = random.choice([p for p in PLACES if p.name in {"meadow", "garden", "park"}])
    visitor = random.choice(("butterfly", "ladybug", "blue bird", "tiny frog"))
    spot = random.choice(("nose", "tail", "hat", "front paw"))
    world = SurpriseWorld(hero, place, ordinary=f"trying to catch a {visitor}", surprise=f"{visitor} landed on {hero.name}'s {spot}", reaction="happy")

    story = f"""
{intro(hero, place)}

{hero.name} saw {article(visitor)} {visitor} and tried to catch it. The {visitor} moved away each time.

{hero.name} felt a little frustrated and stopped to rest. Suddenly, the {visitor} landed on {hero.name}'s {spot}.

The surprise made {hero.name} laugh and jump. {cap(hero.subject)} stayed still so the tiny visitor would not be scared.

After that, {hero.name} smiled whenever {hero.subject} saw a {visitor}.
"""
    hero.add(Memeplex("Joy", 1.0))
    return clean(story + "\n" + ending(world, "The tiny surprise made the whole day bright."))


def box_reveal_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "cat", "dog")))
    friend = choose_character(random.choice(("girl", "boy", "cat", "dog")), avoid=hero.name)
    place = random.choice([p for p in PLACES if p.name in {"park", "yard", "playroom"}])
    item = random.choice(BOX_ITEMS)
    world = SurpriseWorld(hero, place, ordinary="a closed box", surprise=item, reaction="delighted")

    story = f"""
{intro(hero, place)} There was also {article(description(friend))} {description(friend)} named {friend.name}.

{hero.name} and {friend.name} found a closed box while they were playing. They did not know what was inside.

{friend.name} asked, "Should we open it?" {hero.name} nodded and opened the box carefully.

Inside, they found {article(item)} {item}. The surprise made both friends gasp and smile.

They shared what they found and played together until the day felt special.
"""
    hero.add(Memeplex("Joy", 1.0))
    return clean(story + "\n" + ending(world, "The surprise in the box became a shared memory."))


def secret_door_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    guide = choose_character(random.choice(("bug", "duck", "mouse", "bunny")))
    place = random.choice([p for p in PLACES if p.name in {"yard", "park", "garden"}])
    secret_place = random.choice(SECRET_PLACES)
    world = SurpriseWorld(hero, place, ordinary="an ordinary walk", surprise=secret_place, reaction="amazed")

    story = f"""
{intro(hero, place)} There was also {article(description(guide))} {description(guide)} named {guide.name}.

{hero.name} was walking and looking at ordinary things. Then {guide.name} whispered, "I have a secret to show you."

{hero.name} followed {guide.name} to a small hidden door. Behind it was {article(secret_place)} {secret_place}.

{hero.name} felt amazed because the ordinary place was not ordinary at all.

From that day on, {hero.name} and {guide.name} visited the secret together.
"""
    hero.add(Memeplex("Wonder", 1.0))
    return clean(story + "\n" + ending(world, "The secret made the familiar place feel new."))


def mistaken_emergency_story() -> str:
    hero = choose_character(random.choice(("cat", "dog", "duck", "boy", "girl")))
    friend = choose_character(random.choice(("cat", "dog", "duck", "boy", "girl")), avoid=hero.name)
    place = random.choice([p for p in PLACES if p.name in {"park", "yard", "meadow"}])
    real, mistaken = random.choice(MISTAKEN_SIGHTS)
    helper = random.choice(("a little girl", "a kind man", "Mom", "a park helper"))
    world = SurpriseWorld(hero, place, ordinary=f"seeing {article(real)} {real}", surprise=f"it was not {mistaken}", reaction="relieved")

    story = f"""
{intro(hero, place)} There was also {article(description(friend))} {description(friend)} named {friend.name}.

{hero.name} and {friend.name} saw {article(real)} {real} far away. At first, they thought it was {article(mistaken)} {mistaken}.

They felt confused and worried. Then {helper} came over and said, "Look closely. It is just {article(real)} {real}."

The reveal made {hero.name} feel silly but relieved. {friend.name} laughed too.

They went back to playing, glad that the surprise was not an emergency.
"""
    hero.add(Memeplex("Caution", 1.0))
    return clean(story + "\n" + ending(world, "Looking closely turned worry into relief."))


def new_skill_surprise_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    teacher = random.choice(("Mom", "Dad", "Grandma", "Teacher"))
    place = random.choice([p for p in PLACES if p.name in {"bedroom", "playroom", "shop"}])
    skill = random.choice(SKILLS)
    project = random.choice(("doll dress", "tiny boat", "painted card", "little cake", "paper hat", "safe rope knot"))
    world = SurpriseWorld(hero, place, ordinary="ordinary play", surprise=f"learning to {skill}", reaction="proud")

    story = f"""
{intro(hero, place)}

{hero.name} thought it would be an ordinary day of play. Then {teacher} smiled and said, "I have a surprise. Today you can learn to {skill}."

{hero.name} felt excited and a little unsure. {teacher} showed each step slowly.

After some practice, {hero.name} made {article(project)} {project}. The surprise was not a toy; it was a new skill.

{hero.name} felt proud and wanted to try again tomorrow.
"""
    hero.add(Memeplex("Joy", 1.0))
    return clean(story + "\n" + ending(world, "The surprise became something the child could keep practicing."))


def magic_identity_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"creek", "park", "garden"}])
    disguised, identity = random.choice(MAGIC_IDENTITIES)
    wish = random.choice(("be friends forever", "play together every day", "find a kind adventure", "make the creek sparkle"))
    world = SurpriseWorld(hero, place, ordinary=f"meeting a {disguised}", surprise=identity, reaction="wonder")

    story = f"""
{intro(hero, place)}

{hero.name} met {article(disguised)} {disguised} and started to play. The {disguised} seemed ordinary at first.

Then it spoke clearly and said, "I have a secret." {hero.name} listened closely.

The {disguised} revealed that it was really {article(identity)} {identity}. {hero.name} was surprised and full of wonder.

{hero.name} made a wish to {wish}, and the magical friend smiled.
"""
    hero.add(Memeplex("Wonder", 1.0))
    return clean(story + "\n" + ending(world, "The revealed secret turned into a new friendship."))


STORY_SHAPES = (
    animal_surprise_story,
    box_reveal_story,
    secret_door_story,
    mistaken_emergency_story,
    new_skill_surprise_story,
    magic_identity_story,
)


def generate_story() -> str:
    return random.choice(STORY_SHAPES)()


def generate_unique_stories(count: int) -> list[str]:
    stories: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(stories) < count and attempts < count * 80:
        attempts += 1
        story = generate_story()
        if story not in seen:
            seen.add(story)
            stories.append(story)
    if len(stories) < count:
        raise RuntimeError(f"Only generated {len(stories)} unique stories after {attempts} attempts")
    return stories


def names_in_story(story: str) -> list[str]:
    return re.findall(r"named ([A-Z][A-Za-z]+)", story)


def build_questions(story: str) -> list[QA]:
    questions: list[QA] = []
    names = names_in_story(story)
    if not names:
        return questions
    hero = names[0]

    questions.append(QA("Who is the main character in the story?", hero))

    desc = re.search(r"there was (?:a|an) ([^.]+?) named " + re.escape(hero), story)
    if desc:
        questions.append(QA(f"What kind of character was {hero}?", desc.group(1)))

    place = re.search(re.escape(hero) + r" spent the day ([^.]+)\.", story)
    if place:
        questions.append(QA(f"Where did {hero} spend the day?", place.group(1)))

    surprise_patterns = [
        r"Suddenly, the ([^.]+)\.",
        r"Inside, they found (?:a|an) ([^.]+)\.",
        r"Behind it was (?:a|an) ([^.]+)\.",
        r"The reveal made [^.]+\. ",
        r"The surprise was not a toy; it was ([^.]+)\.",
        r"revealed that it was really (?:a|an) ([^.]+)\.",
    ]
    for pattern in surprise_patterns:
        match = re.search(pattern, story)
        if match:
            answer = "the distant thing was just ordinary" if pattern.startswith("The reveal") else match.group(1)
            questions.append(QA("What was the surprise or reveal?", answer))
            break

    setup_patterns = [
        r"tried to catch it\. The ([^.]+) moved away",
        r"found a closed box",
        r"whispered, \"I have a secret to show you\.\"",
        r"thought it was (?:a|an) ([^.]+)\.",
        r"Today you can learn to ([^.]+)\.",
        r"Then it spoke clearly and said, \"I have a secret\.\"",
    ]
    for pattern in setup_patterns:
        match = re.search(pattern, story)
        if match:
            answer = match.group(1) if match.lastindex else "someone hinted that a secret was nearby"
            if "closed box" in pattern:
                answer = "they found a closed box"
            elif "learn to" in pattern:
                answer = f"learning to {answer}"
            elif "spoke clearly" in pattern:
                answer = "the ordinary friend said it had a secret"
            questions.append(QA("What made the surprise possible?", answer))
            break

    reaction_patterns: list[tuple[str, str]] = [
        (re.escape(hero) + r" laugh and jump", "laughed and jumped"),
        (r"both friends gasp and smile", "gasped and smiled with a friend"),
        (re.escape(hero) + r" felt amazed", "felt amazed"),
        (re.escape(hero) + r" feel silly but relieved", "felt silly but relieved"),
        (re.escape(hero) + r" felt proud", "felt proud"),
        (re.escape(hero) + r" was surprised and full of wonder", "was surprised and full of wonder"),
    ]
    for pattern, answer in reaction_patterns:
        match = re.search(pattern, story)
        if match:
            questions.append(QA(f"How did {hero} react?", answer))
            break

    helper = re.search(r"There was also (?:a|an) [^.]+ named ([A-Z][A-Za-z]+)\.", story)
    if helper:
        questions.append(QA("Who shared the surprise?", helper.group(1)))
    else:
        teacher = re.search(r"Then ([A-Z][A-Za-z]+|Mom|Dad|Grandma|Teacher) smiled and said", story)
        if teacher:
            questions.append(QA("Who shared the surprise?", teacher.group(1)))

    lesson_match = list(re.finditer(re.escape(hero) + r" (learned|remembered) that ([^.]+)\.", story))
    if lesson_match:
        final = lesson_match[-1]
        verb = "learn" if final.group(1) == "learned" else "remember"
        questions.append(QA(f"What did {hero} {verb}?", final.group(2)))

    if len(questions) > 6:
        base = questions[:3]
        extras = questions[3:]
        pivot = sum(ord(ch) for ch in story) % len(extras)
        questions = base + (extras[pivot:] + extras[:pivot])[:3]

    return enrich_questions(hero, questions[:6])


def full_answer(hero: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if lower.startswith("who is the main character"):
        return f"The main character is {answer}. The surprise story follows {answer} as something unexpected changes an ordinary moment."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description gives the surprise a clear point of view."
    if "where did" in lower:
        return f"{hero} spent the day {answer}. The setting shows where the ordinary day begins."
    if "surprise or reveal" in lower:
        if " landed " in answer:
            subject, rest = answer.split(" landed ", 1)
            subject_phrase = subject if subject.startswith(("a ", "an ", "the ")) else f"{article(subject)} {subject}"
            phrase = f"that {subject_phrase} landed {rest}"
        else:
            phrase = answer if answer.startswith(("a ", "an ", "the ")) else f"{article(answer)} {answer}"
        return f"The surprise or reveal was {phrase}. It is the moment that turns the story away from the expected path."
    if "made the surprise possible" in lower:
        if answer.startswith(("they ", "someone ", "the ordinary friend ")):
            return f"The surprise became possible because {answer}. That setup gives the reveal a reason to happen."
        setup = answer if answer.startswith(("a ", "an ", "the ", "learning ")) else f"{article(answer)} {answer}"
        return f"The surprise became possible because of {setup}. That setup gives the reveal a reason to happen."
    if "react" in lower:
        return f"{hero} {answer}. The reaction shows whether the surprise felt funny, joyful, relieving, or wonderful."
    if "shared the surprise" in lower:
        return f"{answer} shared the surprise with {hero}. Sharing makes the reveal feel social instead of private."
    if "what did" in lower and ("learn" in lower or "remember" in lower):
        verb = "remembered" if "remember" in lower else "learned"
        return f"{hero} {verb} that {answer}. The lesson turns the surprise into something useful after the moment passes."
    return f"The answer is {answer}. This detail comes directly from the surprise story."


def follow_up_for(hero: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes for {hero}?",
            f"{hero} begins in an ordinary situation and then meets something unexpected. The surprise changes what {hero} notices, feels, or understands.",
        )
    if "surprise or reveal" in lower:
        return (
            "Why is the reveal important?",
            "The reveal is important because it creates the main turn in the story. It changes confusion, routine, or curiosity into a new understanding.",
        )
    if "made the surprise possible" in lower:
        return (
            "Why does the setup matter?",
            "The setup matters because a surprise works best when it grows from something already in the scene. It keeps the reveal from feeling random.",
        )
    if "react" in lower:
        return (
            "What does the reaction show?",
            "The reaction shows how the character handles the unexpected. It tells whether the surprise becomes joy, relief, wonder, or learning.",
        )
    if "shared" in lower:
        return (
            "How does sharing change the surprise?",
            "Sharing changes the surprise by making it part of a relationship. The unexpected moment becomes something the characters can enjoy together.",
        )
    if "learn" in lower or "remember" in lower:
        return (
            "How does the ending complete the surprise?",
            "The ending completes the surprise by naming what remains afterward. The reveal becomes a lesson, memory, habit, or friendship.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain the character, setting, setup, reveal, or result. It keeps the answer grounded in the text.",
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
    parser = argparse.ArgumentParser(description="Generate scripted surprise tales.")
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
