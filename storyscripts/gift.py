#!/usr/bin/env python3
"""
Gift Tales Generator

Generate short scripted Gift/Gratitude-style stories with no runtime LLMs and no
external dependencies. The story shapes are inspired by TinyStories kernels like:

    Gift(Fairy, Wish)
    Grant(Mommy, to=Lily, gift=GreenVelvetPillow)
    Gift(vase_new) + Guidance(Use(gently), Place(table))
    Gratitude(helper, receiver) + Friendship(...)

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
class GiftWorld:
    hero: Character
    place: Place
    giver: str = ""
    receiver: str = ""
    gift: str = ""
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


BOY_NAMES = ("Timmy", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn", "Theo", "Remy", "Owen")
GIRL_NAMES = ("Lily", "Mia", "Sue", "Olive", "Ruby", "Zoe", "Clara", "Lucy", "Ivy", "Nina", "Ella", "Sara")
ANIMAL_NAMES = ("Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo", "Snowy")

CHILD_TRAITS = ("kind", "curious", "playful", "careful", "hopeful", "creative", "gentle", "eager", "patient")
ANIMAL_TRAITS = ("small", "quick", "gentle", "playful", "curious", "sleepy", "loyal", "bright", "friendly")
KINDS = ("bunny", "dog", "cat", "mouse", "bird", "bear", "frog")

PLACES = (
    Place("kitchen", "in the", frozenset({"inside", "home"})),
    Place("bedroom", "in the", frozenset({"inside", "home"})),
    Place("garden", "in the", frozenset({"outside", "plants"})),
    Place("park", "at the", frozenset({"outside", "public"})),
    Place("playroom", "in the", frozenset({"inside", "play"})),
    Place("meadow", "in the", frozenset({"outside", "wild"})),
    Place("little store", "at the", frozenset({"inside", "public"})),
    Place("sunny yard", "in the", frozenset({"outside", "home"})),
)

GROWNUPS = ("Mom", "Dad", "Mommy", "Grandma", "Grandpa", "Aunt May", "a kind neighbor")
FRIEND_KINDS = ("girl", "boy", "bunny", "dog", "mouse", "bird")
GIFTS = (
    "blue kite with a long tail",
    "green velvet pillow",
    "little paint box",
    "soft yellow scarf",
    "red toy truck",
    "storybook with shiny stars",
    "tiny drum",
    "wooden boat",
    "bag of bright beads",
    "purple cup",
    "warm blanket",
    "silver bell",
)
HANDMADE_GIFTS = (
    "painted stone",
    "paper crown",
    "card with a sunny heart",
    "clay turtle",
    "string bracelet",
    "tiny flower basket",
    "paper boat",
    "picture of the whole family",
)
MAGIC_GIFTS = (
    "wish for more colors",
    "glowing shell",
    "flying little boat",
    "song that made flowers open",
    "silver key to a secret garden",
    "warm sparkle for cold days",
)
REPAIR_GIFTS = (
    "plain vase from the kitchen",
    "safe wooden cup",
    "new little bowl",
    "soft practice blanket",
    "sturdy toy basket",
)
HELPED_FRIENDS = (
    "lost bird",
    "cold kitten",
    "tired puppy",
    "little turtle",
    "shy fairy",
    "sad bunny",
)
WANTS = (
    "something shiny",
    "a toy that looked bigger",
    "a gift exactly like a friend's",
    "a treat right away",
    "the most colorful thing in the store",
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


def choose_friend(hero: Character) -> Character:
    return choose_character(random.choice(FRIEND_KINDS), avoid=hero.name)


def description(char: Character) -> str:
    return f"{' '.join(char.traits)} {char.intro_noun}".strip()


def intro(char: Character, place: Place) -> str:
    desc = description(char)
    return f"Once upon a time, there was {article(desc)} {desc} named {char.name}. {char.name} spent the day {place.phrase}."


def ending(world: GiftWorld, fallback: str) -> str:
    gratitude = world.hero.memes.get("Gratitude", 0.0)
    generosity = world.hero.memes.get("Generosity", 0.0)
    care = world.hero.memes.get("Care", 0.0)
    if generosity >= 0.8:
        return f"{world.hero.name} learned that a gift can grow bigger when it is shared."
    if gratitude >= 0.8 and care >= 0.8:
        return f"{world.hero.name} learned that saying thank you is part of taking care of a gift."
    if gratitude >= 0.8:
        return f"{world.hero.name} remembered that a kind gift carries love with it."
    return fallback


def birthday_gift_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if "home" in p.tags or p.name == "little store"])
    giver = random.choice(GROWNUPS)
    gift = random.choice(GIFTS)
    world = GiftWorld(hero, place, giver=giver, receiver=hero.name, gift=gift)

    story = f"""
{intro(hero, place)}

{hero.name} had tried to be patient all morning, but {hero.subject} kept wondering what was wrapped in bright paper.

{giver} smiled and gave {hero.name} {article(gift)} {gift}. The gift was {article(gift)} {gift}.

{hero.name} held it carefully and said, "Thank you, {giver}." Then {hero.subject} used it gently so it would stay special.

Later, {hero.name} showed the gift to a friend and let the friend have a turn.
"""
    world.embed(hero.name, Memeplex("Gratitude", 1.0))
    world.embed(hero.name, Memeplex("Care", 0.9))
    world.embed(hero.name, Memeplex("Generosity", 0.5))
    return clean(story + "\n" + ending(world, "The gift made the day feel bright."))


def handmade_gift_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bunny", "mouse")))
    receiver = random.choice([g for g in GROWNUPS if not g.startswith("a ")])
    place = random.choice([p for p in PLACES if p.name in {"kitchen", "bedroom", "garden", "playroom"}])
    gift = random.choice(HANDMADE_GIFTS)
    problem = random.choice(("the glue would not stick", "one corner bent", "the ribbon fell off", "the paint made a smudge"))
    world = GiftWorld(hero, place, giver=hero.name, receiver=receiver, gift=gift)

    story = f"""
{intro(hero, place)}

{hero.name} wanted to make something kind for {receiver}. The handmade gift was {article(gift)} {gift}.

At first, {problem}, and {hero.name} almost felt upset. {cap(hero.subject)} took a slow breath and fixed it the best way {hero.subject} could.

When {receiver} came in, {hero.name} gave {receiver} the gift. {receiver} said, "Thank you, {hero.name}. I can see you worked hard."

{hero.name} felt warm inside because the gift carried careful work and love.
"""
    world.embed(hero.name, Memeplex("Generosity", 1.0))
    world.embed(hero.name, Memeplex("Care", 0.8))
    return clean(story + "\n" + ending(world, "The gift became a happy memory."))


def repair_gift_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    friend = choose_friend(hero)
    place = random.choice([p for p in PLACES if p.name in {"kitchen", "playroom", "sunny yard"}])
    old_item = random.choice(("blue vase", "small cup", "flower bowl", "wooden tray"))
    gift = random.choice(REPAIR_GIFTS)
    grownup = random.choice(("Mom", "Dad", "Grandma"))
    world = GiftWorld(hero, place, giver=grownup, receiver=hero.name, gift=gift)

    story = f"""
{intro(hero, place)} There was also {article(description(friend))} {description(friend)} named {friend.name}.

{hero.name} and {friend.name} were pretending to hunt for treasure. They reached for a {old_item}, but it slipped and broke.

{hero.name} felt scared, and {friend.name} looked sorry. {grownup} came over and helped them clean the pieces safely.

Then {grownup} gave them {article(gift)} {gift} to use gently. The new gift was {article(gift)} {gift}.

{hero.name} said, "Thank you, {grownup}." {friend.name} said thank you too, and they kept the new gift on the table where it was safe.
"""
    world.embed(hero.name, Memeplex("Gratitude", 1.0))
    world.embed(hero.name, Memeplex("Care", 1.0))
    return clean(story + "\n" + ending(world, "They learned that gifts need careful hands."))


def magic_reward_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "bunny", "dog")))
    place = random.choice([p for p in PLACES if "outside" in p.tags])
    helped = random.choice(HELPED_FRIENDS)
    gift = random.choice(MAGIC_GIFTS)
    giver = "the fairy" if "fairy" not in helped else "the little fairy"
    world = GiftWorld(hero, place, giver=giver, receiver=hero.name, gift=gift)

    story = f"""
{intro(hero, place)}

One day, {hero.name} found a {helped} who needed help. {cap(hero.subject)} made a safe place and stayed nearby.

The {helped} smiled, and a tiny light began to shine. It was really {giver}, and {giver} wanted to thank {hero.name}.

{giver.capitalize()} gave {hero.name} {article(gift)} {gift}. The surprise gift was {article(gift)} {gift}.

{hero.name} said, "Thank you." {cap(hero.subject)} used the gift to make the day brighter for everyone nearby.
"""
    world.embed(hero.name, Memeplex("Gratitude", 1.0))
    world.embed(hero.name, Memeplex("Generosity", 1.0))
    return clean(story + "\n" + ending(world, "Kindness had turned into a wonderful surprise."))


def unwanted_gift_story() -> str:
    hero = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"bedroom", "little store", "kitchen"}])
    giver = random.choice(("Mommy", "Dad", "Grandma", "Grandpa"))
    want = random.choice(WANTS)
    gift = random.choice(("simple book", "plain red hat", "small wooden train", "soft socks", "quiet puzzle", "little blue cup"))
    world = GiftWorld(hero, place, giver=giver, receiver=hero.name, gift=gift)

    story = f"""
{intro(hero, place)}

{hero.name} wanted {want}. Instead, {giver} gave {hero.name} {article(gift)} {gift}. The gift was {article(gift)} {gift}.

At first, {hero.name} made a small frown. Then {hero.subject} noticed how carefully {giver} had chosen it.

{hero.name} said, "Thank you, {giver}. I will try it." Soon {hero.subject} found a gentle way to enjoy the gift.

By bedtime, {hero.name} felt glad because the gift had been given with love.
"""
    world.embed(hero.name, Memeplex("Gratitude", 1.0))
    return clean(story + "\n" + ending(world, "The simple gift felt important after all."))


def sharing_gift_story() -> str:
    hero = choose_character(random.choice(("girl", "boy", "cat", "dog", "bunny")))
    friend = choose_friend(hero)
    place = random.choice(PLACES)
    giver = random.choice(GROWNUPS)
    gift = random.choice(("big brown ball", "box of crayons", "bag of cookies", "toy boat", "bright ribbon", "little bell"))
    world = GiftWorld(hero, place, giver=giver, receiver=hero.name, gift=gift)

    story = f"""
{intro(hero, place)} There was also {article(description(friend))} {description(friend)} named {friend.name}.

{giver} gave {hero.name} {article(gift)} {gift}. The gift was {article(gift)} {gift}.

{hero.name} loved it so much that {hero.subject} wanted to keep it all alone. Then {friend.name} watched quietly from nearby.

{hero.name} thought for a moment and said, "You can have a turn too." {friend.name} smiled and said, "Thank you, {hero.name}."

They shared the gift until the whole place felt happier.
"""
    world.embed(hero.name, Memeplex("Generosity", 1.0))
    world.embed(hero.name, Memeplex("Gratitude", 0.7))
    return clean(story + "\n" + ending(world, "The gift became more fun because it was shared."))


STORY_SHAPES = (
    birthday_gift_story,
    handmade_gift_story,
    repair_gift_story,
    magic_reward_story,
    unwanted_gift_story,
    sharing_gift_story,
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

    gift_patterns = [
        r"The gift was (?:a|an) ([^.]+)\.",
        r"The handmade gift was (?:a|an) ([^.]+)\.",
        r"The new gift was (?:a|an) ([^.]+)\.",
        r"The surprise gift was (?:a|an) ([^.]+)\.",
    ]
    for pattern in gift_patterns:
        gift = re.search(pattern, story)
        if gift:
            questions.append(QA("What gift appeared in the story?", gift.group(1)))
            break

    gave_patterns = [
        (r"([A-Z][A-Za-z]+|Mommy|Mom|Dad|Grandma|Grandpa|Aunt May|a kind neighbor) smiled and gave " + re.escape(hero), "gave"),
        (r"([A-Z][A-Za-z]+|Mommy|Mom|Dad|Grandma|Grandpa|Aunt May|a kind neighbor) gave " + re.escape(hero), "gave"),
        (r"(the fairy|the little fairy) gave " + re.escape(hero), "gave"),
    ]
    for pattern, role in gave_patterns:
        giver = re.search(pattern, story)
        if giver:
            if role == "received":
                questions.append(QA("Who received the gift?", giver.group(1)))
            else:
                questions.append(QA(f"Who gave {hero} the gift?", giver.group(1)))
            break

    recipient = re.search(re.escape(hero) + r" wanted to make something kind for (Aunt May|[A-Z][A-Za-z]+)", story)
    if recipient:
        questions.append(QA("Who was the handmade gift for?", recipient.group(1)))

    response = re.search(
        re.escape(hero) + r" said, \"Thank you(?:, (Aunt May|Mommy|Mom|Dad|Grandma|Grandpa|[A-Z][A-Za-z]+))?",
        story,
    )
    if response:
        thanked = response.group(1) or "the giver"
        questions.append(QA(f"How did {hero} respond to the gift?", f"{hero} thanked {thanked}"))

    sharing = re.search(re.escape(hero) + r" thought for a moment and said, \"You can have a turn too\.\" ([A-Z][A-Za-z]+) smiled", story)
    if sharing:
        questions.append(QA("Who shared the gift?", hero))
        questions.append(QA("Who got a turn with the gift?", sharing.group(1)))
    elif "showed the gift to a friend" in story:
        questions.append(QA("How did the gift get shared?", f"{hero} showed it to a friend and let the friend have a turn"))

    lesson = re.search(re.escape(hero) + r" (learned|remembered) that ([^.]+)\.", story)
    if lesson:
        verb, answer = lesson.group(1), lesson.group(2)
        if verb == "learned":
            questions.append(QA(f"What did {hero} learn?", answer))
        else:
            questions.append(QA(f"What did {hero} remember?", answer))
    else:
        feeling = re.search(r"By bedtime, " + re.escape(hero) + r" felt ([^.]+)\.", story)
        if feeling:
            questions.append(QA(f"How did {hero} feel by bedtime?", feeling.group(1)))

    return enrich_questions(hero, questions[:6])


def full_answer(hero: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if lower.startswith("who is the main character"):
        return f"The main character is {answer}. The gift story follows {answer} as a present, reward, or act of kindness changes the day."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description shows who {hero} is before the gift becomes important."
    if "where did" in lower:
        return f"{hero} spent the day {answer}. The setting gives the gift a clear place in the story."
    if "what gift" in lower:
        return f"The gift was {article(answer)} {answer}. It matters because the characters have to receive it, care for it, or share it."
    if "who gave" in lower:
        return f"{answer} gave {hero} the gift. The giver's kindness starts the gratitude part of the story."
    if "who received" in lower or "handmade gift for" in lower:
        return f"The gift was for {answer}. That makes the gift an act of care from one character to another."
    if "respond" in lower:
        return f"{hero} responded by saying thank you. In the text, {answer}, which shows gratitude instead of grabbing."
    if "who shared" in lower:
        return f"{answer} shared the gift. Sharing turns the present into something that helps more than one character."
    if "who got a turn" in lower:
        return f"{answer} got a turn with the gift. That moment shows the gift being opened outward to someone else."
    if "how did the gift get shared" in lower:
        return f"The gift was shared when {answer}. The story uses sharing to make the gift feel warmer."
    if "what did" in lower and "learn" in lower:
        return f"{hero} learned that {answer}. The lesson connects the gift with gratitude, care, or generosity."
    if "remember" in lower:
        return f"{hero} remembered that {answer}. That memory gives the gift meaning beyond the object itself."
    if "feel by bedtime" in lower:
        return f"{hero} felt {answer} by bedtime. The feeling shows that the gift became meaningful after some thought."
    return f"The answer is {answer}. This detail comes directly from the gift story."


def follow_up_for(hero: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes for {hero}?",
            f"{hero} has to decide how to receive, use, or share the gift. The story turns that decision into a small lesson.",
        )
    if "gift" in lower and "what" in lower:
        return (
            "Why is the gift important?",
            "The gift is important because it carries more than an object. It carries kindness, repair, reward, or love from one character to another.",
        )
    if "gave" in lower or "received" in lower or "for" in lower:
        return (
            "What relationship does the gift show?",
            "The gift shows a caring relationship between giver and receiver. It gives the characters a reason to notice each other's feelings.",
        )
    if "respond" in lower:
        return (
            "Why does the response matter?",
            "The response matters because gratitude is the action that completes the gift. Without that response, the present would be only an object.",
        )
    if "shared" in lower or "turn" in lower:
        return (
            "How does sharing change the gift?",
            "Sharing changes the gift by making it part of a friendship. The joy spreads instead of staying with only one character.",
        )
    if "learn" in lower or "remember" in lower or "feel" in lower:
        return (
            "How does the ending complete the story?",
            "The ending completes the story by showing what the gift taught or changed. The present becomes connected to gratitude, care, or generosity.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain the giver, receiver, object, or lesson. It keeps the answer grounded in the text.",
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
    parser = argparse.ArgumentParser(description="Generate scripted gift tales.")
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
