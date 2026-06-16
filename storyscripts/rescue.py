#!/usr/bin/env python3
"""
Rescue Tales Generator

Generate short scripted Rescue/Kindness-style stories with no runtime LLMs and
no external dependencies. The story shapes are inspired by TinyStories kernels:

    Rescue(Emily, Max) + Apology(Emily) + Affection(Max)
    Rescue(Bear, process=PickUp(Bird)+Return(Bird,nest))
    Rescue(Mom, item=blanket) + Joy + Sleep
    Resolution(Kindness, gift=Bread, result=Gratitude+Safety)

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
class RescueWorld:
    helper: Character
    place: Place
    rescued: str = ""
    trouble: str = ""
    action: str = ""
    facts: set[str] = field(default_factory=set)
    carriers: dict[str, dict[str, float]] = field(default_factory=dict)

    def mark(self, fact: str) -> None:
        self.facts.add(fact)

    def embed(self, carrier: str, meme: Memeplex) -> None:
        self.carriers.setdefault(carrier, {})
        self.carriers[carrier][meme.name] = self.carriers[carrier].get(meme.name, 0.0) + meme.weight
        if carrier == self.helper.name:
            self.helper.add(meme)


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str = ""
    follow_up_answer: str = ""


BOY_NAMES = ("Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Milo", "Noah", "Finn", "Theo", "Owen", "Remy")
GIRL_NAMES = ("Lily", "Mia", "Sara", "Anna", "Ruby", "Zoe", "Clara", "Lucy", "Ivy", "Nina", "Ella", "Sophie")
ANIMAL_NAMES = ("Spot", "Pip", "Nibbles", "Ted", "Coco", "Pebble", "Poppy", "Daisy", "Bobo", "Snowy")

CHILD_TRAITS = ("kind", "curious", "careful", "brave", "gentle", "playful", "hopeful", "patient", "quick")
ANIMAL_TRAITS = ("small", "gentle", "quick", "friendly", "curious", "loyal", "furry", "playful", "bright")
ADULT_TRAITS = ("helpful", "caring", "calm", "wise", "protective", "kind")
KINDS = ("bear", "dog", "bunny", "cat", "mouse", "frog")

PLACES = (
    Place("farm", "on the", frozenset({"outside", "animals"})),
    Place("forest", "in the", frozenset({"outside", "wild"})),
    Place("park", "at the", frozenset({"outside", "public"})),
    Place("barn", "in the", frozenset({"inside", "animals"})),
    Place("bedroom", "in the", frozenset({"inside", "home"})),
    Place("playroom", "in the", frozenset({"inside", "home"})),
    Place("meadow", "in the", frozenset({"outside", "wild"})),
    Place("factory doorway", "by the", frozenset({"inside", "shelter"})),
    Place("big room", "in the", frozenset({"inside", "home"})),
)

HURT_ANIMALS = ("little bird", "baby bunny", "small kitten", "tiny duck", "young squirrel", "tired puppy")
STUCK_PLACES = ("tree", "muddy hole", "fence", "slide rope", "big bush", "snowy ditch")
LOST_ITEMS = ("thick blanket", "red mitten", "small bell", "favorite scarf", "blue toy boat", "soft bear")
RAIN_GROUPS = ("duck family", "three little mice", "two kittens", "small bird friends", "bunny friends")
FAMILY_PROBLEMS = ("a big fight", "angry silence", "a messy argument", "a loud disagreement", "hurt feelings")
KIND_ACTIONS = (
    "made warm bread",
    "set the table",
    "brought everyone water",
    "drew a kind picture",
    "made a quiet corner",
    "shared a soft blanket",
)
RESCUE_ACTIONS = (
    "lifted the little one gently",
    "called for a calm grown-up",
    "made a safe path",
    "held out both hands",
    "untied the knot slowly",
    "carried the lost thing back",
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
    if kind == "adult":
        name = random.choice(("Mom", "Dad", "Ranger", "Emily", "Grandma", "Teacher"))
        return Character(name, "adult", tuple(random.sample(ADULT_TRAITS, 2)))
    name = random.choice([n for n in ANIMAL_NAMES if n != avoid])
    return Character(name, kind, tuple(random.sample(ANIMAL_TRAITS, 2)))


def description(char: Character) -> str:
    return f"{' '.join(char.traits)} {char.intro_noun}".strip()


def intro(char: Character, place: Place) -> str:
    desc = description(char)
    return f"Once upon a time, there was {article(desc)} {desc} named {char.name}. {char.name} spent the day {place.phrase}."


def ending(world: RescueWorld, fallback: str) -> str:
    care = world.helper.memes.get("Care", 0.0)
    courage = world.helper.memes.get("Courage", 0.0)
    safety = world.helper.memes.get("Safety", 0.0)
    gratitude = world.helper.memes.get("Gratitude", 0.0)
    if safety >= 0.9 and care >= 0.9:
        return f"{world.helper.name} learned that careful help can turn fear back into safety."
    if courage >= 0.9:
        return f"{world.helper.name} remembered that bravery works best when it stays gentle."
    if gratitude >= 0.9:
        return f"{world.helper.name} felt glad because kindness had brought everyone closer."
    return fallback


def hurt_animal_rescue_story() -> str:
    helper = choose_character(random.choice(("girl", "boy", "bear", "dog")))
    place = random.choice([p for p in PLACES if p.name in {"farm", "forest", "barn", "meadow"}])
    rescued = random.choice(HURT_ANIMALS)
    action = random.choice(("made a soft nest", "carried it to a safe box", "called Mom for help", "put it back in its nest"))
    world = RescueWorld(helper, place, rescued=rescued, trouble=f"{rescued} was hurt", action=action)

    story = f"""
{intro(helper, place)}

One day, {helper.name} found {article(rescued)} {rescued}. The {rescued} was hurt and could not get home.

{helper.name} felt worried, but {helper.subject} stayed gentle. {cap(helper.subject)} {action} and waited quietly.

Soon the {rescued} was safe. It made a tiny happy sound, as if it were saying thank you.

{helper.name} smiled because the rescue had helped someone small.
"""
    world.embed(helper.name, Memeplex("Care", 1.0))
    world.embed(helper.name, Memeplex("Safety", 1.0))
    return clean(story + "\n" + ending(world, "The day felt softer after the rescue."))


def stuck_pet_rescue_story() -> str:
    pet = choose_character(random.choice(("dog", "cat", "bunny", "mouse")))
    rescuer = random.choice(("Emily", "Mom", "Dad", "Ranger", "Grandma"))
    place = random.choice([p for p in PLACES if p.name in {"park", "forest", "meadow"}])
    stuck_place = random.choice(STUCK_PLACES)
    world = RescueWorld(pet, place, rescued=pet.name, trouble=f"{pet.name} was stuck in a {stuck_place}", action=f"{rescuer} lifted {pet.name} down")

    story = f"""
{intro(pet, place)}

{pet.name} saw something interesting and ran after it. Then {pet.subject} got stuck in a {stuck_place}.

{pet.name} called for help and felt scared. {rescuer} heard the sound and came quickly.

{rescuer} spoke softly, reached carefully, and lifted {pet.name} down. The rescue was slow and safe.

{pet.name} licked {rescuer}'s hand and stayed close for the rest of the day.
"""
    world.embed(pet.name, Memeplex("Gratitude", 1.0))
    world.embed(pet.name, Memeplex("Safety", 1.0))
    return clean(story + "\n" + ending(world, f"{pet.name} learned to stay close when the world felt exciting."))


def stuck_children_rescue_story() -> str:
    first = choose_character("boy")
    second = choose_character(random.choice(("boy", "girl")), avoid=first.name)
    place = random.choice([p for p in PLACES if p.name in {"park", "playroom"}])
    trouble = random.choice(("a rope knot held them in the air", "the slide ladder felt too high", "a big box tipped around them", "the swing chain tangled"))
    rescuer = random.choice(("Ranger", "Teacher", "Dad", "Mom"))
    world = RescueWorld(first, place, rescued=f"{first.name} and {second.name}", trouble=trouble, action=f"{rescuer} helped them down")

    story = f"""
{intro(first, place)} There was also {article(description(second))} {description(second)} named {second.name}.

{first.name} and {second.name} were playing a wild game. Suddenly, {trouble}.

They stopped laughing and called for help. {rescuer} came over with a calm voice.

{rescuer} helped them down and checked that nobody was hurt. Then {rescuer} said, "Next time, ask before you try a tricky game."

{first.name} and {second.name} said thank you and promised to play more safely.
"""
    world.embed(first.name, Memeplex("Safety", 1.0))
    world.embed(first.name, Memeplex("Care", 0.8))
    return clean(story + "\n" + ending(world, "The rescue turned the scary game into a careful lesson."))


def lost_item_rescue_story() -> str:
    child = choose_character(random.choice(("girl", "boy")))
    helper_name = random.choice(("Mom", "Dad", "Grandma", "Big Sister", "Teacher"))
    item = random.choice(LOST_ITEMS)
    place = random.choice([p for p in PLACES if p.name in {"bedroom", "playroom", "park"}])
    hiding = random.choice(("under the chair", "behind the pillows", "near the door", "inside a basket", "beside the little bed"))
    world = RescueWorld(child, place, rescued=item, trouble=f"the {item} was lost", action=f"{helper_name} found it {hiding}")

    story = f"""
{intro(child, place)}

{child.name} could not find {child.possessive} {item}. Without it, {child.subject} felt sad and worried.

{helper_name} helped search slowly instead of rushing. At last, {helper_name} found the {item} {hiding}.

{helper_name} gave it back, and {child.name} hugged the {item} tightly. The rescue made bedtime feel peaceful again.

{child.name} said, "Thank you, {helper_name}." Then {child.subject} put the {item} in a safe place.
"""
    world.embed(child.name, Memeplex("Gratitude", 1.0))
    world.embed(child.name, Memeplex("Safety", 0.8))
    return clean(story + "\n" + ending(world, f"{child.name} learned to keep special things close."))


def rain_shelter_kindness_story() -> str:
    helper = choose_character(random.choice(("girl", "boy", "dog", "bear")))
    group = random.choice(RAIN_GROUPS)
    place = random.choice([p for p in PLACES if p.name in {"park", "factory doorway", "meadow"}])
    gift = random.choice(("bread", "a warm cloth", "dry leaves", "a little snack", "a safe corner"))
    world = RescueWorld(helper, place, rescued=group, trouble=f"{group} was wet and scared", action=f"{helper.name} shared {gift}")

    story = f"""
{intro(helper, place)}

Rain started to fall, and {helper.name} saw the {group} looking wet and scared. They needed a dry place.

{helper.name} led them under shelter and shared {gift}. The kindness made the {group} feel safe.

At first, everyone was quiet. Then the {group} relaxed and thanked {helper.name}.

{helper.name} felt happy because a small rescue had made the rainy day easier.
"""
    world.embed(helper.name, Memeplex("Care", 1.0))
    world.embed(helper.name, Memeplex("Gratitude", 1.0))
    return clean(story + "\n" + ending(world, "Kindness had become a shelter of its own."))


def family_kindness_rescue_story() -> str:
    child = choose_character(random.choice(("girl", "boy")))
    place = random.choice([p for p in PLACES if p.name in {"big room", "kitchen", "playroom"}])
    problem = random.choice(FAMILY_PROBLEMS)
    action = random.choice(KIND_ACTIONS)
    world = RescueWorld(child, place, rescued="the family", trouble=problem, action=action)

    story = f"""
{intro(child, place)}

The family had {problem}, and the room felt too quiet afterward. {child.name} wished everyone could talk kindly again.

{child.name} remembered that kindness could help when words felt hard. So {child.subject} {action} for everyone.

When the family saw what {child.name} had done, they sat together and started to talk. The kind action rescued the evening from staying sad.

{child.name} felt proud because care had brought the family back together.
"""
    world.embed(child.name, Memeplex("Care", 1.0))
    world.embed(child.name, Memeplex("Courage", 1.0))
    return clean(story + "\n" + ending(world, "One gentle action had helped everyone begin again."))


STORY_SHAPES = (
    hurt_animal_rescue_story,
    stuck_pet_rescue_story,
    stuck_children_rescue_story,
    lost_item_rescue_story,
    rain_shelter_kindness_story,
    family_kindness_rescue_story,
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

    trouble_patterns = [
        r"The ([^.]+?) was hurt and could not get home\.",
        r"Then (?:he|she|it) got stuck in a ([^.]+)\.",
        re.escape(hero) + r" got stuck in a ([^.]+)\.",
        r"Suddenly, ([^.]+)\.",
        r"Without it, [^.]+ felt sad and worried\.",
        r"Rain started to fall, and " + re.escape(hero) + r" saw the ([^.]+?) looking wet and scared\.",
        r"The family had ([^,]+),",
    ]
    for pattern in trouble_patterns:
        trouble = re.search(pattern, story)
        if trouble:
            if pattern.startswith("Without"):
                lost = re.search(re.escape(hero) + r" could not find (?:his|her|its) ([^.]+)\.", story)
                answer = f"the {lost.group(1)} was lost" if lost else "a special thing was lost"
            elif "was hurt" in pattern:
                answer = f"the {trouble.group(1)} was hurt and could not get home"
            elif "wet and scared" in pattern:
                answer = f"the {trouble.group(1)} were wet and scared"
            elif "family had" in pattern:
                answer = f"the family had {trouble.group(1)}"
            elif "got stuck" in pattern:
                answer = f"{hero} got stuck in a {trouble.group(1)}"
            else:
                answer = trouble.group(1)
            questions.append(QA("What trouble needed a rescue?", answer))
            break

    helper_patterns = [
        r"([A-Z][A-Za-z]+|Mom|Dad|Grandma|Ranger|Teacher|Emily|Big Sister) heard the sound and came quickly\.",
        r"([A-Z][A-Za-z]+|Mom|Dad|Grandma|Ranger|Teacher) came over with a calm voice\.",
        r"([A-Z][A-Za-z]+|Mom|Dad|Grandma|Teacher|Big Sister) helped search slowly",
        re.escape(hero) + r" led them under shelter",
        re.escape(hero) + r" remembered that kindness could help",
        re.escape(hero) + r" felt worried, but",
    ]
    for pattern in helper_patterns:
        helper = re.search(pattern, story)
        if helper:
            answer = helper.group(1) if helper.lastindex else hero
            questions.append(QA("Who helped with the rescue?", answer))
            break

    action_patterns = [
        (re.escape(hero) + r" felt worried, but [^.]+\. [^.]+? ([^.]+) and waited quietly\.", lambda m: m.group(1)),
        (r"([A-Z][A-Za-z]+|Mom|Dad|Grandma|Ranger|Teacher|Emily) spoke softly, reached carefully, and lifted " + re.escape(hero) + r" down\.", lambda m: f"{m.group(1)} lifted {hero} down carefully"),
        (r"([A-Z][A-Za-z]+|Mom|Dad|Grandma|Ranger|Teacher) helped them down and checked that nobody was hurt\.", lambda m: f"{m.group(1)} helped them down and checked that nobody was hurt"),
        (r"At last, ([A-Z][A-Za-z]+|Mom|Dad|Grandma|Teacher|Big Sister) found the ([^.]+)\.", lambda m: f"{m.group(1)} found the {m.group(2)}"),
        (re.escape(hero) + r" led them under shelter and shared ([^.]+)\.", lambda m: f"{hero} led them under shelter and shared {m.group(1)}"),
        (r"So (?:he|she|it) ([^.]+ for everyone)\.", lambda m: f"{hero} {m.group(1)}"),
    ]
    for pattern, build in action_patterns:
        action = re.search(pattern, story)
        if action:
            questions.append(QA("How did the rescue happen?", build(action)))
            break

    rescued_patterns = [
        r"the rescue had helped ([^.]+)\.",
        r"lifted " + re.escape(hero) + r" down",
        r"gave it back, and " + re.escape(hero) + r" hugged the ([^.]+) tightly\.",
        r"made the ([^.]+?) feel safe\.",
        r"rescued the evening from staying sad\.",
    ]
    for pattern in rescued_patterns:
        rescued = re.search(pattern, story)
        if rescued:
            if "lifted" in pattern:
                answer = hero
            elif "gave it back" in pattern:
                answer = rescued.group(1)
            elif "rescued the evening" in pattern:
                answer = "the family"
            else:
                answer = rescued.group(1)
            questions.append(QA("Who or what was rescued?", answer))
            break

    thanks = re.search(r"([A-Z][A-Za-z]+) said, \"Thank you, ([A-Z][A-Za-z ]+)\"", story)
    if thanks:
        questions.append(QA("Who showed gratitude?", thanks.group(1)))
    elif re.search(r"thanked " + re.escape(hero), story):
        questions.append(QA("Who showed gratitude?", f"the characters helped by {hero}"))
    elif re.search(r"as if it were saying thank you", story):
        questions.append(QA("Who showed gratitude?", "the rescued animal"))

    ending_match = list(re.finditer(re.escape(hero) + r" (learned|remembered|felt) ([^.]+)\.", story))
    if ending_match:
        final = ending_match[-1]
        verb, answer = final.group(1), final.group(2)
        if verb == "learned":
            questions.append(QA(f"What did {hero} learn?", answer))
        elif verb == "remembered":
            questions.append(QA(f"What did {hero} remember?", answer))
        else:
            questions.append(QA(f"How did {hero} feel at the end?", answer))

    chosen = questions
    if len(questions) > 6:
        base = questions[:3]
        extras = questions[3:]
        pivot = sum(ord(ch) for ch in story) % len(extras)
        chosen = base + (extras[pivot:] + extras[:pivot])[:3]

    return enrich_questions(hero, chosen[:6])


def full_answer(hero: str, question: str, answer: str) -> str:
    answer = answer.strip()
    lower = question.lower()
    if lower.startswith("who is the main character"):
        return f"The main character is {answer}. The rescue story follows {answer} as someone becomes unsafe, worried, or separated and then receives help."
    if "what kind of character" in lower:
        return f"{hero} was {article(answer)} {answer}. That description helps explain why the rescue can become a kindness story."
    if "where did" in lower:
        return f"{hero} spent the day {answer}. The setting gives the rescue a concrete place to happen."
    if "what trouble" in lower:
        return f"The trouble was that {answer}. This problem created the need for rescue or kindness."
    if "who helped" in lower:
        return f"{answer} helped with the rescue. The helper noticed the problem and chose a careful response."
    if "how did the rescue" in lower:
        return f"The rescue happened when {answer}. That action moved the story from danger or sadness toward safety."
    if "who or what was rescued" in lower:
        subject = answer if answer.startswith(("the ", "The ")) else f"the {answer}"
        subject = subject[:1].upper() + subject[1:]
        verb = "were" if answer.endswith(("friends", "mice", "kittens")) else "was"
        return f"{subject} {verb} rescued. The story centers on bringing that person, animal, object, or evening back to safety."
    if "gratitude" in lower:
        subject = answer[:1].upper() + answer[1:]
        return f"{subject} showed gratitude. The thank-you moment proves that the help was received and understood."
    if "what did" in lower and "learn" in lower:
        return f"{hero} learned that {answer}. The lesson connects rescue with care and caution."
    if "remember" in lower:
        memory = answer[5:] if answer.startswith("that ") else answer
        return f"{hero} remembered that {memory}. That memory turns the rescue into guidance for next time."
    if "feel at the end" in lower:
        return f"At the end, {hero} felt {answer}. The feeling shows that kindness changed the emotional direction of the story."
    return f"The answer is {answer}. This detail comes directly from the rescue story."


def follow_up_for(hero: str, question: str) -> tuple[str, str]:
    lower = question.lower()
    if "main character" in lower:
        return (
            f"What changes for {hero}?",
            f"{hero} moves from ordinary activity into a moment that needs care. By the end, the rescue changes what {hero} understands or feels.",
        )
    if "trouble" in lower:
        return (
            "Why does the trouble matter?",
            "The trouble matters because it gives the kindness a real purpose. The story needs danger, worry, or sadness before rescue can mean something.",
        )
    if "who helped" in lower or "how did the rescue" in lower:
        return (
            "What makes the help careful?",
            "The help is careful because it is slow, gentle, and aimed at safety. The rescuer does not just act quickly; the rescuer pays attention.",
        )
    if "rescued" in lower:
        return (
            "How does the rescue change the story?",
            "The rescue changes the story by moving someone or something out of trouble. After that, the characters can feel safe, grateful, or closer.",
        )
    if "gratitude" in lower:
        return (
            "Why does gratitude matter here?",
            "Gratitude matters because it completes the rescue emotionally. It shows that the kindness was noticed, not just performed.",
        )
    if "learn" in lower or "remember" in lower or "feel" in lower:
        return (
            "How does the ending complete the rescue?",
            "The ending completes the rescue by showing its meaning. The event becomes a lesson about safety, kindness, courage, or care.",
        )
    return (
        "Why is that detail important?",
        "That detail helps explain the character, setting, trouble, helper, or result. It keeps the answer grounded in the text.",
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
    parser = argparse.ArgumentParser(description="Generate scripted rescue tales.")
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
