#!/usr/bin/env python3
"""
Encounter Tales Generator

Generate short scripted Encounter-style stories with no runtime LLMs and no
external dependencies. The story shapes are inspired by TinyStories kernels like:

    Encounter(hero, stranger)
    Encounter(place)
    Encounter(Vendor, cart)
    Journey(hero, catalyst=Encounter(...), process=..., insight=...)

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
class EncounterWorld:
    hero: Character
    place: Place
    facts: set[str] = field(default_factory=set)
    links: dict[str, float] = field(default_factory=dict)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)

    def bond(self, other: Character, amount: float) -> None:
        self.links[other.name] = self.links.get(other.name, 0.0) + amount
        self.hero.add(Memeplex("Trust", amount))
        other.add(Memeplex("Trust", amount))


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str = ""
    follow_up_answer: str = ""


# =============================================================================
# VOCABULARY
# =============================================================================


BOY_NAMES = ("Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn", "Theo", "Ty")
GIRL_NAMES = ("Lily", "Mia", "Sue", "Ruby", "Zoe", "Clara", "Lucy", "Ivy", "Nina", "Ella")
ANIMAL_NAMES = ("Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo", "Flame")

CHILD_TRAITS = ("curious", "helpful", "careful", "excited", "kind", "shy", "playful", "gentle", "brave")
ANIMAL_TRAITS = ("friendly", "small", "quick", "happy", "curious", "gentle", "playful", "sleepy", "loyal")
KINDS = ("dog", "cat", "bird", "bunny", "frog", "bear", "mouse", "puppy")

PLACES = (
    Place("park", "at the", frozenset({"outside", "public", "play"})),
    Place("muddy yard", "in the", frozenset({"outside", "mud"})),
    Place("ship", "on the", frozenset({"public", "search"})),
    Place("backyard", "in the", frozenset({"outside", "home"})),
    Place("zoo", "at the", frozenset({"public", "animals"})),
    Place("market", "at the", frozenset({"public", "vendor"})),
    Place("forest path", "on the", frozenset({"outside", "wild"})),
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("quiet street", "on the", frozenset({"public"})),
)

ENCOUNTER_OBJECTS = (
    "pretty door", "ice cream cart", "lost toy", "muddy shape",
    "tiny bunny", "big ship", "friendly vendor", "new animal",
    "mysterious box", "little bird",
)
NEEDS = (
    "find a lost toy", "carry a heavy bag", "reach a high branch",
    "clean mud from a face", "look for a safe path", "open a stuck door",
)
ANIMALS = ("elephant", "giraffe", "zebra", "penguin", "seal", "monkey", "flamingo", "turtle")
TREATS = ("strawberry ice cream", "warm bun", "sweet apple", "tiny cake", "cold lemonade")
LESSONS = (
    "new friends can appear in surprising places",
    "gentle greetings work better than rushing",
    "helping someone can turn an encounter into friendship",
    "asking questions can make a strange moment feel safe",
    "not every surprise is scary once it is understood",
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


def description(char: Character) -> str:
    return f"{' '.join(char.traits)} {char.intro_noun}".strip()


def intro(char: Character, place: Place) -> str:
    desc = description(char)
    return f"Once upon a time, there was {article(desc)} {desc} named {char.name}. {char.name} spent the day {place.phrase}."


def compatible(hero: Character, other: Character, place: Place) -> bool:
    if hero.name == other.name:
        return False
    if "mud" in place.tags and (hero.kind == "bird" or other.kind == "bird"):
        return False
    if "animals" in place.tags and hero.kind in {"cat", "dog"}:
        return False
    return True


def choose_pair(place: Place | None = None) -> tuple[Character, Character, Place]:
    for _ in range(80):
        place = place or random.choice(PLACES)
        hero = choose_character()
        other = choose_character(avoid=hero.name)
        if compatible(hero, other, place):
            return hero, other, place
    place = Place("park", "at the", frozenset({"outside", "public", "play"}))
    return Character("Tim", "boy", ("curious", "helpful"), "boy"), Character("Sue", "girl", ("shy", "kind"), "girl"), place


def ending(world: EncounterWorld, default: str) -> str:
    trust = world.hero.memes.get("Trust", 0.0)
    care = world.hero.memes.get("Care", 0.0)
    wonder = world.hero.memes.get("Wonder", 0.0)
    if care >= 0.8:
        return f"{world.hero.name} felt glad because the encounter became a chance to help."
    if trust >= 0.9:
        return f"{world.hero.name} learned that {random.choice(LESSONS)}."
    if wonder >= 0.8:
        return f"{world.hero.name} remembered that a strange meeting can become a good surprise."
    return default


# =============================================================================
# STORY SHAPES
# =============================================================================


def hidden_friend_story() -> str:
    place = random.choice([p for p in PLACES if p.name in {"muddy yard", "garden", "backyard", "park"}])
    hero, other, place = choose_pair(place)
    world = EncounterWorld(hero, place)
    disguise = random.choice(("muddy shape", "quiet bundle", "still shadow", "lumpy blanket"))

    story = f"""
{intro(hero, place)} {cap(hero.subject)} wanted someone to play with.

Nearby, {hero.name} encountered {article(disguise)} {disguise}. It did not move or answer.

{hero.name} talked to it anyway and gently brushed some dirt away. Suddenly, the shape blinked.

It was {other.name}, {article(description(other))} {description(other)}. {other.name} had only been covered up and shy.

Soon {hero.name} and {other.name} were playing together.
"""
    world.bond(other, 1.0)
    return clean(story + "\n" + ending(world, "The encounter became a friendship."))


def lost_helper_story() -> str:
    place = random.choice([p for p in PLACES if p.name in {"ship", "park", "market", "quiet street"}])
    hero, other, place = choose_pair(place)
    world = EncounterWorld(hero, place)
    lost_item = random.choice(("toy", "red hat", "small bag", "blue ball", "paper boat"))
    helper = random.choice(("a bird", "a kind worker", "a little dog", "a tall child"))

    story = f"""
{intro(hero, place)} Then {hero.subject} encountered {other.name}, who looked sad.

{hero.name} asked, "What happened?" {other.name} whispered, "I lost my {lost_item}."

They searched together in big places and small places. For a while, they could not find it.

Then {helper} appeared with the {lost_item}. {other.name} smiled and thanked {hero.name}.

After that, {hero.name} and {other.name} played with the {lost_item} together.
"""
    world.bond(other, 1.0)
    world.hero.add(Memeplex("Care", 0.9))
    return clean(story + "\n" + ending(world, "They became friends after the search."))


def gentle_animal_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    animal_kind = random.choice(("bunny", "cat", "dog", "bird"))
    other = choose_character(animal_kind, avoid=hero.name)
    place = random.choice([p for p in PLACES if "outside" in p.tags])
    world = EncounterWorld(hero, place)

    story = f"""
{intro(hero, place)} {cap(hero.subject)} felt excited and wanted to explore.

All at once, {hero.name} encountered {other.name}, {article(description(other))} {description(other)}.

{hero.name} wanted to rush forward, but the animal stepped back. So {hero.name} stopped and took a slow breath.

Then {hero.name} waved gently and waited. Little by little, {other.name} came closer.

The meeting felt calmer when {hero.name} moved slowly.
"""
    world.bond(other, 0.9)
    return clean(story + "\n" + ending(world, "Gentleness made the encounter safe."))


def vendor_treat_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if "public" in p.tags])
    world = EncounterWorld(hero, place)
    vendor = random.choice(("ice cream vendor", "fruit seller", "kind baker", "lemonade seller"))
    treat = random.choice(TREATS)

    story = f"""
{intro(hero, place)} {cap(hero.subject)} heard a cheerful bell.

By a small cart, {hero.name} encountered {article(vendor)} {vendor}. The vendor smiled and asked what {hero.name} would like.

{hero.name} asked politely for {treat}. The vendor handed it over and said, "Enjoy."

{hero.name} sat nearby and tasted the treat while watching the day go by.

The encounter made the trip feel special.
"""
    world.hero.add(Memeplex("Wonder", 0.9))
    return clean(story + "\n" + ending(world, "The small meeting became a happy memory."))


def strange_door_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "mouse", "bear")))
    place = random.choice([p for p in PLACES if p.name in {"forest path", "garden", "quiet street", "backyard"}])
    world = EncounterWorld(hero, place)
    surprise = random.choice(("a party of friendly animals", "a room full of soft lights", "a tiny garden", "a circle of singing toys"))

    story = f"""
{intro(hero, place)} {cap(hero.subject)} went for a slow walk.

Beside the path, {hero.name} encountered a pretty door that {hero.subject} had never seen before.

{hero.name} knocked first and waited. When nothing scary happened, {hero.subject} opened the door.

Inside was {surprise}. Everyone inside welcomed {hero.name}.

{hero.name} stayed for a little while, then went home smiling.
"""
    world.hero.add(Memeplex("Wonder", 1.0))
    return clean(story + "\n" + ending(world, "The strange door became a wonderful encounter."))


def zoo_animals_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = Place("zoo", "at the", frozenset({"public", "animals"}))
    world = EncounterWorld(hero, place)
    animals = random.sample(ANIMALS, 3)

    story = f"""
{intro(hero, place)} {cap(hero.subject)} had wanted to see animals from far away.

First, {hero.name} encountered {article(animals[0])} {animals[0]}. Then {hero.subject} saw {article(animals[1])} {animals[1]} and {article(animals[2])} {animals[2]}.

{hero.name} watched quietly so the animals would feel safe. Each animal moved in its own special way.

By the end of the visit, {hero.name} felt happy and thankful.
"""
    world.hero.add(Memeplex("Wonder", 1.0))
    return clean(story + "\n" + ending(world, "The animal encounters made the day feel big."))


STORY_SHAPES = (
    hidden_friend_story,
    lost_helper_story,
    gentle_animal_story,
    vendor_treat_story,
    strange_door_story,
    zoo_animals_story,
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

    names = list(dict.fromkeys(re.findall(r"named ([A-Z][A-Za-z]+)|encountered ([A-Z][A-Za-z]+)|and ([A-Z][A-Za-z]+) played", story)))
    flat_names = []
    for group in names:
        for name in group:
            if name and name not in flat_names:
                flat_names.append(name)
    other = flat_names[1] if len(flat_names) > 1 else "the other character"

    if named:
        questions.append(QA("Who is the main character in the story?", hero))

    desc = re.search(r"there was (?:a|an) ([^.]+?) named " + re.escape(hero), story)
    if desc:
        questions.append(QA(f"What kind of character was {hero}?", desc.group(1)))

    place = re.search(re.escape(hero) + r" spent the day ([^.]+)\.", story)
    if place:
        questions.append(QA(f"Where did {hero} spend the day?", place.group(1)))

    encounter = re.search(re.escape(hero) + r" encountered ([^.]+)\.", story)
    if encounter:
        questions.append(QA(f"What did {hero} encounter?", encounter.group(1)))

    sad = re.search(r"encountered ([A-Z][A-Za-z]+), who looked sad", story)
    if sad:
        questions.append(QA("Who needed help?", sad.group(1)))

    lost = re.search(r'I lost my ([^"]+)', story)
    if lost:
        questions.append(QA("What was lost?", lost.group(1)))

    response_patterns = [
        (re.escape(hero) + r" talked to it anyway and gently brushed some dirt away\.", "by talking gently and brushing some dirt away"),
        (r"They searched together in big places and small places\.", "by searching together in big places and small places"),
        (re.escape(hero) + r" stopped and took a slow breath\.", "by stopping and taking a slow breath"),
        (re.escape(hero) + r" asked politely for ([^.]+)\.", "by asking politely for \\1"),
        (re.escape(hero) + r" knocked first and waited\.", "by knocking first and waiting"),
        (re.escape(hero) + r" watched quietly so the animals would feel safe\.", "by watching quietly so the animals would feel safe"),
    ]
    for pattern, template in response_patterns:
        match = re.search(pattern, story)
        if match:
            questions.append(QA(f"How did {hero} respond?", match.expand(template)))
            break

    endings = list(re.finditer(re.escape(hero) + r" (learned|remembered|felt) ([^.]+)\.", story))
    if endings:
        final = endings[-1]
        verb, answer = final.group(1), final.group(2)
        if verb == "learned":
            questions.append(QA(f"What did {hero} learn?", answer))
        elif verb == "remembered":
            questions.append(QA(f"What did {hero} remember?", answer))
        else:
            questions.append(QA(f"How did {hero} feel at the end?", answer))

    return enrich_questions(hero, other, questions[:6])


def full_answer(hero: str, other: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if lower.startswith("who is the main character"):
        return f"The main character is {answer}. The encounter story follows {answer} as a meeting changes the day."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description helps show how {hero} enters the encounter."
    if "where did" in lower:
        return f"{hero} spent the day {answer}. This setting gives the encounter a clear place to happen."
    if "what did" in lower and "encounter" in lower:
        return f"{hero} encountered {answer}. That meeting is the turn that makes the story move."
    if "who needed help" in lower:
        return f"{answer} needed help. {hero} notices that sadness and chooses to respond."
    if "what was lost" in lower:
        item = answer[:-1] if answer.endswith(".") else answer
        return f"The lost thing was the {item}. Looking for it gives the characters a reason to work together."
    if "how did" in lower and "respond" in lower:
        response = answer if answer.startswith("by ") else f"by {answer}"
        return f"{hero} responded {response}. The response shows whether the encounter becomes safe, helpful, or friendly."
    if "what did" in lower and "learn" in lower:
        lesson = answer if answer.startswith("that ") else f"that {answer}"
        return f"{hero} learned {lesson}. The lesson explains what the encounter taught."
    if "remember" in lower:
        memory = answer[5:] if answer.startswith("that ") else answer
        return f"{hero} remembered that {memory}. This makes the meeting feel meaningful after it ends."
    if "feel" in lower:
        return f"{hero} felt {answer}. That feeling shows the result of the encounter."
    return f"The answer is {answer}. This detail comes directly from the encounter story."


def follow_up_for(hero: str, other: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes for {hero}?",
            f"{hero} starts in an ordinary moment and then meets someone or something new. The encounter gives {hero} a choice about curiosity, kindness, or care.",
        )
    if "encounter" in lower or "needed help" in lower:
        return (
            "Why is the meeting important?",
            "The meeting is important because it creates the story's main change. A stranger, object, animal, or surprise gives the character something to understand.",
        )
    if "lost" in lower or "respond" in lower:
        return (
            "What does the response show?",
            f"The response shows how {hero} handles the meeting. A careful response can turn confusion into help or friendship.",
        )
    if "learn" in lower or "remember" in lower or "feel" in lower:
        return (
            "How does the ending complete the encounter?",
            "The ending completes the encounter by showing what remains after the meeting. It gives the story a lesson, memory, or feeling.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain the setting, the meeting, or the result. It keeps the answer grounded in the story.",
    )


def enrich_questions(hero: str, other: str, questions: list[QA]) -> list[QA]:
    enriched: list[QA] = []
    for item in questions:
        answer = full_answer(hero, other, item.question, item.answer)
        follow_question, follow_answer = follow_up_for(hero, other, item.question)
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
    parser = argparse.ArgumentParser(description="Generate scripted encounter tales.")
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
