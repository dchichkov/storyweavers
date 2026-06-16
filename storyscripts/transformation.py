#!/usr/bin/env python3
"""
Transformation Tales Generator

Generate short scripted Transformation/Transform/Metamorphosis-style stories
with no runtime LLMs and no external dependencies. The story shapes are inspired
by TinyStories kernels like:

    Transformation(OldMan, into=Wizard, cause=wand)
    Transform(caterpillar, into=butterfly)
    Metamorphosis(caterpillar, into=butterfly)
    Transformation(Robot, state=Calm+Trust)

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
class TransformationWorld:
    hero: Character
    place: Place
    before: str = ""
    after: str = ""
    catalyst: str = ""
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


BOY_NAMES = ("Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn", "Theo", "Owen", "Remy")
GIRL_NAMES = ("Lily", "Mia", "Sara", "Anna", "Ruby", "Zoe", "Clara", "Lucy", "Ivy", "Nina", "Ella", "Sophie")
ANIMAL_NAMES = ("Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo", "Snowy")

CHILD_TRAITS = ("kind", "curious", "playful", "careful", "hopeful", "creative", "gentle", "brave", "patient")
ANIMAL_TRAITS = ("small", "curious", "gentle", "playful", "tired", "bright", "friendly", "quiet", "furry")
KINDS = ("dog", "cat", "mouse", "bunny", "bear", "frog")

PLACES = (
    Place("park", "at the", frozenset({"outside", "public"})),
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("forest", "in the", frozenset({"outside", "wild"})),
    Place("beach", "on the", frozenset({"outside", "water"})),
    Place("bedroom", "in the", frozenset({"inside", "home"})),
    Place("playroom", "in the", frozenset({"inside", "play"})),
    Place("little cave", "in the", frozenset({"inside", "hidden"})),
    Place("small house", "in the", frozenset({"inside", "home"})),
    Place("store", "at the", frozenset({"inside", "public"})),
)

MAGIC_OBJECTS = ("glowing bracelet", "silver wand", "shiny toy", "blue shell", "gold button", "tiny bell")
CATERPILLAR_COLORS = ("green", "striped", "soft brown", "yellow", "tiny blue", "fuzzy")
OBJECTS_TO_CHANGE = (
    ("big cabinet", "small cabinet"),
    ("plain box", "painted treasure chest"),
    ("dull stone", "sparkly stone"),
    ("empty jar", "glowing jar"),
    ("old hat", "flower hat"),
)
RESTORATIONS = (
    ("old lonely tree", "healthy tree"),
    ("dry flower patch", "bright flower patch"),
    ("dull shell", "shiny shell"),
    ("tired little pond", "clear little pond"),
)
FEELING_CHANGES = (
    ("troubled and lonely", "calm and trusting"),
    ("worried and hidden", "brave enough to ask for help"),
    ("selfish about the ball", "ready to share"),
    ("sad and quiet", "hopeful and open"),
)
KIND_ACTS = ("helped reach a box", "shared a snack", "gave fresh water", "made a soft bed", "listened carefully")
LESSONS = (
    "change can be gentle and surprising",
    "small things can become amazing",
    "kindness can break a lonely spell",
    "help can turn worry into trust",
    "sharing can change a selfish heart",
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
    if kind == "robot":
        return Character("Robot", "robot", ("troubled", "lonely"))
    if kind == "toy":
        return Character(random.choice(("MrBear", "Button", "Patch", "Tinny")), "toy", ("selfish", "learning"))
    name = random.choice([n for n in ANIMAL_NAMES if n != avoid])
    return Character(name, kind, tuple(random.sample(ANIMAL_TRAITS, 2)))


def description(char: Character) -> str:
    return f"{' '.join(char.traits)} {char.intro_noun}".strip()


def intro(char: Character, place: Place) -> str:
    desc = description(char)
    return f"Once upon a time, there was {article(desc)} {desc} named {char.name}. {char.name} spent the day {place.phrase}."


def ending(world: TransformationWorld, fallback: str) -> str:
    wonder = world.hero.memes.get("Wonder", 0.0)
    trust = world.hero.memes.get("Trust", 0.0)
    generosity = world.hero.memes.get("Generosity", 0.0)
    care = world.hero.memes.get("Care", 0.0)
    if generosity >= 0.9:
        return f"{world.hero.name} learned that a changed heart can make everyone happier."
    if trust >= 0.9:
        return f"{world.hero.name} learned that asking for help can change loneliness into trust."
    if care >= 0.9 and wonder >= 0.9:
        return f"{world.hero.name} remembered that small lives can grow into something amazing."
    if wonder >= 0.9:
        return f"{world.hero.name} learned that {random.choice(LESSONS)}."
    return fallback


def spell_breaking_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"park", "store", "garden"}])
    hidden = random.choice(("tired dog", "grumpy old man", "quiet cat", "sleepy bunny"))
    after = random.choice(("friendly princess", "kind wizard", "laughing fairy", "gentle prince"))
    object_name = random.choice(MAGIC_OBJECTS)
    act = random.choice(KIND_ACTS)
    world = TransformationWorld(hero, place, before=hidden, after=after, catalyst=object_name)

    story = f"""
{intro(hero, place)}

One day, {hero.name} met {article(hidden)} {hidden}. The {hidden} looked lonely, so {hero.name} {act}.

Then the {object_name} began to glow. The {hidden} smiled and said, "Your kind heart broke the spell."

In a shimmer of light, the {hidden} transformed into {article(after)} {after}. {hero.name} was surprised but not afraid.

The {after} thanked {hero.name}, and they spent the rest of the day as friends.
"""
    world.embed(hero.name, Memeplex("Wonder", 1.0))
    world.embed(hero.name, Memeplex("Care", 0.8))
    return clean(story + "\n" + ending(world, "The transformation made the ordinary day feel magical."))


def caterpillar_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"garden", "bedroom", "forest"}])
    color = random.choice(CATERPILLAR_COLORS)
    shelter = random.choice(("jar with air holes", "leafy box", "little branch house", "safe corner by the window"))
    world = TransformationWorld(hero, place, before=f"{color} caterpillar", after="beautiful butterfly", catalyst="time and care")

    story = f"""
{intro(hero, place)}

{hero.name} found {article(color)} {color} caterpillar and picked it up carefully. {cap(hero.subject)} made a {shelter} and gave it fresh leaves.

For many days, {hero.name} watched and waited. The caterpillar grew quiet, and {hero.name} wondered what would happen.

One morning, the caterpillar had transformed into a beautiful butterfly. Its wings opened like tiny painted fans.

{hero.name} carried it outside and let it fly away. {cap(hero.subject)} felt proud and amazed.
"""
    world.embed(hero.name, Memeplex("Care", 1.0))
    world.embed(hero.name, Memeplex("Wonder", 1.0))
    return clean(story + "\n" + ending(world, "The butterfly showed that patient care can reveal hidden beauty."))


def emotional_transformation_story() -> str:
    hero = choose_character("robot")
    helper = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"little cave", "bedroom", "forest"}])
    before, after = random.choice(FEELING_CHANGES[:2])
    world = TransformationWorld(hero, place, before=before, after=after, catalyst=f"{helper.name}'s help")

    story = f"""
{intro(hero, place)} There was also {article(description(helper))} {description(helper)} named {helper.name}.

Robot felt {before}, so it tried to hide. {helper.name} found Robot and asked, "Why are you hiding?"

Robot said, "I do not know what to do." {helper.name} answered, "Sometimes asking for help is the first brave step."

They worked together and found a small solution. Robot's feelings transformed from {before} into {after}.

Robot trusted {helper.name} and did not feel alone anymore.
"""
    world.embed(hero.name, Memeplex("Trust", 1.0))
    return clean(story + "\n" + ending(world, "The quiet talk changed the way Robot felt inside."))


def sharing_toy_story() -> str:
    child = choose_character(random.choice(("girl", "boy")))
    toy = choose_character("toy")
    place = random.choice([p for p in PLACES if p.name in {"bedroom", "playroom", "small house"}])
    thing = random.choice(("red ball", "blue train", "soft blanket", "sparkly block", "little drum"))
    world = TransformationWorld(toy, place, before="selfish toy", after="sharing friend", catalyst=f"{child.name}'s lesson")

    story = f"""
{intro(child, place)} There was also {article(description(toy))} {description(toy)} named {toy.name}.

{toy.name} grabbed the {thing} and said, "This is mine." {child.name} felt sad because the other toys wanted a turn.

{child.name} spoke gently and said, "Sharing makes play happier." {toy.name} grew quiet and thought about the words.

Then {toy.name}'s heart transformed. The toy rolled the {thing} to everyone and said, "You can play too."

The room felt cheerful, and {toy.name} became a sharing friend.
"""
    world.embed(toy.name, Memeplex("Generosity", 1.0))
    return clean(story + "\n" + ending(world, "The transformation made play kinder for everyone."))


def object_change_story() -> str:
    hero = choose_character(random.choice(("cat", "dog", "mouse", "girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"small house", "bedroom", "playroom"}])
    before, after = random.choice(OBJECTS_TO_CHANGE)
    tool = random.choice(MAGIC_OBJECTS)
    world = TransformationWorld(hero, place, before=before, after=after, catalyst=tool)

    story = f"""
{intro(hero, place)}

{hero.name} found {article(tool)} {tool}. The {tool} hummed softly, as if it could change things.

Nearby stood {article(before)} {before}. {hero.name} touched it carefully with the {tool}.

The {before} transformed into {article(after)} {after}. {hero.name} clapped with surprise.

{hero.name} used the changed object gently and promised not to change things without thinking first.
"""
    world.embed(hero.name, Memeplex("Wonder", 1.0))
    return clean(story + "\n" + ending(world, "The magic taught that change needs care."))


def restoration_story() -> str:
    hero = choose_character(random.choice(("mouse", "bunny", "girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"forest", "garden", "beach"}])
    before, after = random.choice(RESTORATIONS)
    work = random.choice(("cleaned carefully", "brought water", "moved dry leaves away", "worked a little each morning"))
    world = TransformationWorld(hero, place, before=before, after=after, catalyst=work)

    story = f"""
{intro(hero, place)}

{hero.name} found {article(before)} {before}. It looked forgotten, and {hero.name} wanted to help.

Every day, {hero.name} {work}. The work was slow, but {hero.subject} did not give up.

At last, the {before} transformed into {article(after)} {after}. Other animals came to look and smiled.

They wanted to give {hero.name} a prize, but {hero.name} only wanted to see the place restored.
"""
    world.embed(hero.name, Memeplex("Care", 1.0))
    world.embed(hero.name, Memeplex("Wonder", 0.9))
    return clean(story + "\n" + ending(world, "The best reward was seeing something lonely become beautiful again."))


STORY_SHAPES = (
    spell_breaking_story,
    caterpillar_story,
    emotional_transformation_story,
    sharing_toy_story,
    object_change_story,
    restoration_story,
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

    before_patterns = [
        r"met (?:a|an) ([^.]+?)\. The",
        r"found (?:a|an) ([^.]+? caterpillar)",
        r"Robot felt ([^,]+),",
        r"([A-Z][A-Za-z]+) grabbed the ([^ ]+(?: [^ ]+)?) and said",
        r"Nearby stood (?:a|an) ([^.]+)\.",
        r"found (?:a|an) ([^.]+?)\. It looked forgotten",
    ]
    for pattern in before_patterns:
        match = re.search(pattern, story)
        if match:
            if "grabbed" in pattern:
                questions.append(QA("What needed to change?", f"{match.group(1)} was selfish with the {match.group(2)}"))
            else:
                questions.append(QA("What was the before-state?", match.group(1)))
            break

    catalyst_patterns = [
        r"Then the ([^.]+?) began to glow\.",
        r"made a ([^.]+?) and gave it fresh leaves\.",
        r"([A-Z][A-Za-z]+) found Robot and asked",
        r"([A-Z][A-Za-z]+) spoke gently and said",
        r"found (?:a|an) ([^.]+?)\. The [^.]+ hummed softly",
        r"Every day, " + re.escape(hero) + r" ([^.]+)\.",
    ]
    for pattern in catalyst_patterns:
        match = re.search(pattern, story)
        if match:
            answer = match.group(1)
            if "found Robot" in pattern:
                answer = f"{answer} found Robot and offered help"
            elif "spoke gently" in pattern:
                answer = f"{answer} gave a gentle lesson about sharing"
            questions.append(QA("What caused or helped the transformation?", answer))
            break

    change_patterns = [
        r"had transformed into (?:a|an) ([^.]+)\.",
        r"the ([^.]+?) transformed into (?:a|an) ([^.]+)\.",
        r"feelings transformed from ([^.]+?) into ([^.]+)\.",
        r"heart transformed\.",
    ]
    for pattern in change_patterns:
        match = re.search(pattern, story)
        if match:
            if pattern == r"heart transformed\.":
                questions.append(QA("How did the transformation happen?", "the toy's heart changed after a gentle lesson"))
            elif match.lastindex == 1:
                questions.append(QA("What changed in the transformation?", f"the caterpillar became {match.group(1)}"))
            else:
                questions.append(QA("What changed in the transformation?", f"{match.group(1)} became {match.group(2)}"))
            break

    surprise = re.search(re.escape(hero) + r" (?:was surprised but not afraid|clapped with surprise|felt proud and amazed)", story)
    if surprise:
        questions.append(QA(f"How did {hero} react?", surprise.group(0).replace(hero + " ", "")))

    helper = re.search(r"There was also (?:a|an) [^.]+ named ([A-Z][A-Za-z]+)\.", story)
    if helper:
        questions.append(QA("Who helped or joined the transformation?", helper.group(1)))

    lesson_match = list(re.finditer(re.escape(hero) + r" (learned|remembered) that ([^.]+)\.", story))
    if lesson_match:
        final = lesson_match[-1]
        verb = "learn" if final.group(1) == "learned" else "remember"
        questions.append(QA(f"What did {hero} {verb}?", final.group(2)))
    elif re.search(r"best reward was ([^.]+)\.", story):
        reward = re.search(r"best reward was ([^.]+)\.", story)
        questions.append(QA("What was the best reward?", reward.group(1)))

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
        return f"The main character is {answer}. The transformation story follows how something or someone changes during the plot."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description gives the transformation a starting point."
    if "where did" in lower:
        return f"{hero} spent the day {answer}. The setting grounds the change in a concrete place."
    if "before-state" in lower:
        phrase = answer if answer.startswith(("a ", "an ", "the ")) else f"{article(answer)} {answer}"
        return f"The before-state was {phrase}. This is what existed before the transformation changed the story."
    if "needed to change" in lower:
        return f"What needed to change was that {answer}. The story uses that problem to make the transformation meaningful."
    if "caused or helped" in lower:
        catalyst = answer if answer.startswith(("a ", "an ", "the ", "time ", "patience ", "Robot ", "Sara ", "Lily ", "Nina ", "Ben ", "Tim ", "Theo ", "Max ", "Mia ", "Zoe ", "Ruby ", "Clara ", "Lucy ", "Ivy ", "Ella ", "Sophie ", "Owen ", "Remy ")) else f"{article(answer)} {answer}"
        return f"The transformation was helped by {catalyst}. That catalyst starts or supports the change."
    if "what changed" in lower:
        parts = answer.split(" became ", 1)
        if len(parts) == 2:
            before, after = parts
            before_phrase = before if before.startswith(("a ", "an ", "the ")) else f"the {before}"
            after_phrase = after if after.startswith(("a ", "an ", "the ")) else f"{article(after)} {after}"
            return f"The transformation changed when {before_phrase} became {after_phrase}. The answer names both the earlier state and the later state."
        return f"The transformation changed when {answer}. The answer names both the earlier state and the later state."
    if "what did the character" in lower or "creature become" in lower:
        return f"The character or creature became {article(answer)} {answer}. That new form is the visible result of the transformation."
    if "how did the transformation happen" in lower:
        return f"The transformation happened because {answer}. The change is emotional rather than only magical or physical."
    if "react" in lower:
        return f"{hero} {answer}. That reaction shows wonder without turning the moment into fear."
    if "who helped" in lower or "joined" in lower:
        return f"{answer} helped or joined the transformation. The second character gives the change a relationship, not just an event."
    if "what did" in lower and ("learn" in lower or "remember" in lower):
        verb = "remembered" if "remember" in lower else "learned"
        return f"{hero} {verb} that {answer}. The lesson turns the transformation into something lasting."
    if "best reward" in lower:
        return f"The best reward was {answer}. That ending shows that restoration mattered more than a prize."
    return f"The answer is {answer}. This detail comes directly from the transformation story."


def follow_up_for(hero: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes around {hero}?",
            f"{hero} begins in an ordinary situation and then sees or causes a change. The story becomes about what that change means.",
        )
    if "before-state" in lower or "needed to change" in lower:
        return (
            "Why does the starting state matter?",
            "The starting state matters because transformation needs contrast. Without a before-state, the later change would feel less important.",
        )
    if "caused or helped" in lower:
        return (
            "Why is the catalyst important?",
            "The catalyst is important because it gives the change a reason. It can be magic, kindness, patience, help, or steady work.",
        )
    if "changed" in lower or "become" in lower or "happen" in lower:
        return (
            "How does the change affect the story?",
            "The change moves the story from one state to another. After it happens, the characters understand the world or themselves differently.",
        )
    if "react" in lower:
        return (
            "Why does the reaction matter?",
            "The reaction matters because it tells us how the character receives the unexpected change. Wonder, pride, or calm acceptance shapes the ending.",
        )
    if "helped" in lower or "joined" in lower:
        return (
            "What does the relationship add?",
            "The relationship makes the transformation warmer. Someone notices, helps, teaches, or shares the changed moment.",
        )
    if "learn" in lower or "remember" in lower or "reward" in lower:
        return (
            "How does the ending complete the transformation?",
            "The ending completes the transformation by naming its meaning. The change becomes a lesson, friendship, or new way to act.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain the character, setting, starting state, catalyst, or result. It keeps the answer grounded in the text.",
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
    parser = argparse.ArgumentParser(description="Generate scripted transformation tales.")
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
