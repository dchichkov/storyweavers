#!/usr/bin/env python3
"""
Apology generator for standalone storyscript output.

This file focuses on a single kernel-style family: conflict, apology, and repair.
It generates deterministic story text with follow-up Q&A and optional JSONL output.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple


BOY_NAMES = [
    "Ben",
    "Eli",
    "Finn",
    "Jack",
    "Kai",
    "Leo",
    "Liam",
    "Max",
    "Noah",
    "Sam",
    "Zane",
]

GIRL_NAMES = [
    "Ava",
    "Emma",
    "Ivy",
    "Lena",
    "Lily",
    "Maya",
    "Mia",
    "Noa",
    "Nora",
    "Zoe",
    "Ruby",
]

SUPPORTING_NAMES = [
    "Amy",
    "Ben",
    "Cora",
    "Dad",
    "Grandpa",
    "Mom",
    "Mum",
    "Nora",
    "Omar",
    "Sam",
    "Tina",
]

LOCATIONS = [
    "the backyard",
    "the kitchen",
    "the bedroom",
    "the park",
    "the classroom",
    "the living room",
    "the library",
    "the playground",
    "the playground",
    "the store",
]

ARTIFACTS = [
    "a toy car",
    "her art supplies",
    "his red flashlight",
    "the puzzle",
    "the blue marker",
    "a small kite",
    "the cookie jar",
    "the board game",
    "the soccer ball",
    "the birthday card",
    "the science notebook",
]

LESSONS = [
    "always ask before taking",
    "speak gently, even when upset",
    "own a mistake before fixing it",
    "think before you act when you are angry",
    "be honest when you hurt someone",
    "listen before you defend yourself",
    "take responsibility when someone is upset",
    "repair trust with a clear apology",
]


@dataclass(frozen=True)
class Character:
    name: str
    age_label: str
    role: str

    @property
    def pronoun(self) -> str:
        return "he" if self.age_label == "boy" else "she"

    @property
    def pronoun_obj(self) -> str:
        return "him" if self.age_label == "boy" else "her"

    @property
    def pronoun_possessive(self) -> str:
        return "his" if self.age_label == "boy" else "her"

    @property
    def descriptor(self) -> str:
        return f"little {self.age_label} with a {self.role} heart" if self.role else f"little {self.age_label}"


@dataclass(frozen=True)
class QA:
    question: str
    answer: str
    follow_up_question: str
    follow_up_answer: str
    turns: list[Dict[str, str]]


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tidy_stories(story: str) -> str:
    story = re.sub(r"\s{2,}", " ", story).strip()
    return re.sub(r"\s+\.", ".", story)


def make_char(gender: str) -> Character:
    if gender == "boy":
        name = random.choice(BOY_NAMES)
        role = random.choice(["thoughtful", "curious", "mischievous", "careful", "shy"])
    else:
        name = random.choice(GIRL_NAMES)
        role = random.choice(["bright", "brave", "gentle", "playful", "careful"])
    return Character(name, gender, role)


def make_supporting() -> str:
    return random.choice(SUPPORTING_NAMES)


def mk_sentence(*parts: str) -> str:
    parts = [part.strip() for part in parts if part and part.strip()]
    if not parts:
        return ""
    return " ".join(
        part if part.endswith((".", "!", "?")) else f"{part}."
        for part in parts
    )


def mk_apology_qas(meta: Dict[str, str]) -> List[QA]:
    main = meta["main"]
    friend = meta["friend"]
    place = meta["place"]
    mistake = meta["mistake"]
    harm = meta["harm"]
    apology = meta["apology"]
    repair = meta["repair"]
    lesson = meta["lesson"]
    apology_sentence = apology if apology.endswith((".", "!", "?")) else f"{apology}."

    qas = [
        (
            f"Who is the main character in the story?",
            f"{main} is the center of the story, so everything starts from what {main} decided. "
            f"The story follows {main}'s emotion, the mistake, and the way {main} fixed it.",
            f"What does that make the story about?",
            f"It becomes a story about responsibility and repair, because {main} has to face a mistake and make it right. "
            f"That is what turns a small conflict into a useful lesson.",
        ),
        (
            f"Where did the main event happen?",
            f"The main event happened {place}. That place gave the story a clear scene where everyone could see what happened. "
            f"It also made the apology feel specific and meaningful.",
            f"Why is the place important?",
            f"The setting matters because it shows this was real, everyday behavior. "
            f"Being in a familiar place makes the lesson feel easy to remember.",
        ),
        (
            f"What did {main} do wrong?",
            f"{main} {mistake}. That action created a real problem with {friend}. "
            f"The mistake was not about being mean on purpose, but it still caused pain.",
            f"How did {friend} feel right after that?",
            f"{friend} felt hurt and surprised, and the scene changed quickly. "
            f"That emotional change is why an apology became necessary.",
        ),
        (
            f"How did the apology happen?",
            f"{main} said, \"{apology_sentence}\" Then {main} explained the mistake and made a repair by {repair}. "
            f"The exact apology line helps everyone trust each other again.",
            f"What made the apology feel sincere?",
            f"{main} did not argue first, and {main} named the problem clearly. "
            f"That gave {friend} confidence that the apology was real.",
        ),
        (
            f"What was the main consequence after the conflict?",
            f"The immediate result was tension and {harm}. It showed that careless actions have quick effects. "
            f"At first, the relationship was awkward, then the apology changed that.",
            f"What fixed the situation?",
            f"Making a clear apology and a concrete repair action made the tension resolve. "
            f"Repair turned a moment of blame into a better next moment.",
        ),
        (
            f"What lesson do we learn?",
            f"The lesson is that {lesson}, and that is important for everyday life. "
            f"It shows that repair only works when the person accepts responsibility first.",
            f"How can a child remember this lesson?",
            f"They can pause before reacting, admit the impact, and offer a specific fix. "
            f"That pattern is easy to practice in real moments too.",
        ),
        (
            f"What was the final feeling at the end?",
            f"The ending feels calm and relieved because {main} apologized with care. "
            f"After that, the two became more careful with each other and kept their friendship strong.",
            f"Who changed the most by the end?",
            f"{main} changed the most, because {main} moved from a defensive feeling to accountable action. "
            f"That shift is visible in the tone of the final scene.",
        ),
    ]

    output = []
    for q, a, fu, fa in qas:
        output.append(
            QA(
                question=q,
                answer=mk_sentence(a.replace(main, main)),
                follow_up_question=fu,
                follow_up_answer=mk_sentence(fa.replace(main, main)),
                turns=[
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": mk_sentence(a.replace(main, main))},
                    {"role": "user", "content": fu},
                    {"role": "assistant", "content": mk_sentence(fa.replace(main, main))},
                ],
            )
        )
    return output


def story_no_asking(meta: Dict[str, str]) -> str:
    meta["mistake"] = "took a toy without asking first"
    meta["harm"] = "frustration"
    meta["apology"] = "I'm sorry. I should have asked first."
    meta["repair"] = "bringing the item back, cleaning up the space, and offering to share the next game"
    meta["lesson"] = "asking first is always kinder"
    main = meta["main"]
    friend = meta["friend"]
    place = meta["place"]
    thing = meta["thing"]
    return tidy_stories(
        f"Once upon a time, there was a thoughtful {meta['gender']} named {main}. {main} and {friend} were in {place} and had a good time together. "
        f"One day, {main} took {thing} from {friend} without asking, because {main} was excited and wanted to play now. "
        f"That tiny rule mistake changed everything. {friend} came back and said, \"Where is {thing}?\" and felt worried. "
        f"{main} stopped and answered honestly, then said, \"I'm sorry. I should have asked first.\" "
        f"{main} brought the item back, cleaned up the space, and offered to share the next game so things felt fair. "
        f"They apologized again before going home, and both smiled. {main} later remembered that asking first is always kinder."
    )


def story_hurtful_words(meta: Dict[str, str]) -> str:
    meta["mistake"] = "said words that were too hard to hear"
    meta["harm"] = "hurt feelings"
    meta["apology"] = "I should not have said that."
    meta["repair"] = f"calming down, explaining the frustration, and inviting {meta['friend']} to restart the game"
    meta["lesson"] = "speak gently, even when upset"
    main = meta["main"]
    friend = meta["friend"]
    place = meta["place"]
    thing = meta["thing"]
    return tidy_stories(
        f"Once upon a time, there was a careful {meta['gender']} named {main}. "
        f"{main} was known for being competitive, and one afternoon in {place}, a small game between {main} and {friend} became tense. "
        f"When {main} lost, {main} said words that were too hard and too sharp. {friend} turned quiet and stepped away. "
        f"{main} noticed the hurt right away and said, \"I should not have said that.\" "
        f"{main} took time to calm down, then explained that it was frustration, not the person, and offered a real apology. "
        f"To repair the day, {main} invited {friend} to split a snack and play again with {thing}. "
        f"The two laughed at the restart, and {main} kept the lesson close after that."
    )


def story_broken_item(meta: Dict[str, str]) -> str:
    meta["mistake"] = "handled a favorite item too roughly"
    meta["harm"] = "disappointment"
    meta["apology"] = "I broke it by accident, and I am sorry."
    meta["repair"] = f"helping {meta['friend']} find repair tools and promising to help replace it"
    meta["lesson"] = "care is stronger than blame"
    main = meta["main"]
    friend = meta["friend"]
    place = meta["place"]
    thing = meta["thing"]
    return tidy_stories(
        f"Once upon a time, there was a patient {meta['gender']} named {main}. "
        f"In {place}, {main} borrowed {thing} to try a new game and made a mistake while handling it. "
        f"The {thing.split()[-1]} cracked, and {friend} felt sad because it was special. "
        f"{main} said nothing at first, then took a breath and admitted, \"I broke it by accident, and I am sorry.\" "
        f"To make it right, {main} helped {friend} find repair tools and promised to pay for a replacement with savings. "
        f"They worked together to fix it, then shared a clean room and a good cup of water. "
        f"The apology ended with action, and both understood that care is stronger than blame."
    )


def story_bedtime(meta: Dict[str, str]) -> str:
    meta["mistake"] = "changed the evening plan without checking"
    meta["harm"] = "a shaken bedtime rhythm"
    meta["apology"] = "I am sorry for breaking our rhythm; I wanted to be in control for a moment."
    meta["repair"] = "returning the remote and helping set the story timer"
    meta["lesson"] = "being fair in small moments is a quiet kind of strength"
    main = meta["main"]
    friend = meta["friend"]
    place = meta["place"]
    return tidy_stories(
        f"Once upon a time, there was a brave {meta['gender']} named {main}. "
        f"{main} and {friend} had a plan for bedtime stories in {place}, but {main} interrupted, grabbed the remote, and changed the channel repeatedly. "
        f"{friend} was startled and said it ruined the calm moment. "
        f"{main} listened to the complaint, paused, and apologized with a clear sentence: \"I am sorry for breaking our rhythm; I wanted to be in control for a moment.\" "
        f"{main} then returned the remote and helped set the story timer so the night stayed gentle. "
        f"The room became quiet, and {friend} even asked {main} to read the first page. "
        f"By the end, {main} learned that being fair in small moments is a quiet kind of strength."
    )


def story_team_mistake(meta: Dict[str, str]) -> str:
    meta["mistake"] = "blamed a teammate before listening"
    meta["harm"] = "a strained team mood"
    meta["apology"] = "I said something unfair. I'm sorry for putting the blame on you."
    meta["repair"] = f"owning the full story, correcting the chalkboard, and inviting {meta['friend']} to explain first"
    meta["lesson"] = "honesty protects trust better than being quick to defend yourself"
    main = meta["main"]
    friend = meta["friend"]
    place = meta["place"]
    return tidy_stories(
        f"Once upon a time, there was a curious {meta['gender']} named {main}. "
        f"In {place}, a class activity was split into teams, and {main} accidentally blamed {friend} for a wrong answer. "
        f"The team fell silent. The teacher noticed and asked everyone to pause. "
        f"{main} realized the mistake and said, \"I said something unfair. I'm sorry for putting the blame on you.\" "
        f"Then {main} owned the full story, corrected the chalkboard, and invited {friend} to explain first. "
        f"The teacher thanked both for courage, and their team finished the task together. "
        f"That moment taught {main} that honesty protects trust better than being quick to defend yourself."
    )


def build_context() -> Dict[str, str]:
    gender = random.choice(["boy", "girl"])
    primary = make_char(gender)
    secondary = make_char("girl" if gender == "boy" else "boy")
    friend = secondary.name if secondary != primary else random.choice(SUPPORTING_NAMES)
    place = random.choice(LOCATIONS)
    thing = random.choice(ARTIFACTS)
    thing_word = "it" if thing.split()[-1] in {"car", "ball", "book", "kettle", "car"} else "the thing"
    lesson = random.choice(LESSONS)

    return {
        "main": primary.name,
        "friend": friend,
        "gender": gender,
        "place": place,
        "thing": thing,
        "thing_pronoun": thing_word,
        "lesson": lesson,
        "mistake": "",
        "harm": "",
        "apology": "",
        "repair": "",
    }


def make_story() -> Tuple[str, Dict[str, str]]:
    builders: List[Tuple[str, Callable[[Dict[str, str]], str]]] = [
        ("no_asking", story_no_asking),
        ("hurtful_words", story_hurtful_words),
        ("broken_item", story_broken_item),
        ("bedtime", story_bedtime),
        ("team", story_team_mistake),
    ]

    context = build_context()
    _, story_fn = random.choice(builders)
    story = story_fn(context)
    return story, context


def render_story(story: str, qas: List[QA], with_qa: bool, as_json: bool) -> str:
    if not with_qa:
        return story

    if as_json:
        record = {"story": story, "questions": [qa.__dict__ for qa in qas]}
        return json.dumps(record, ensure_ascii=False)

    lines = [story, "\nQuestions:"]
    for idx, qa in enumerate(qas, 1):
        lines.append(f"{idx}. {qa.question}")
        lines.append(f"Answer: {qa.answer}")
        lines.append(f"Follow-up: {qa.follow_up_question}")
        lines.append(f"Answer: {qa.follow_up_answer}")
    return "\n".join(lines)


def sample_with_meta() -> Tuple[str, List[QA]]:
    story, meta = make_story()
    qas = mk_apology_qas(meta)
    # Keep Q&A diverse without requiring heavy filtering.
    if len(qas) > 6:
        random.shuffle(qas)
        qas = qas[:6]
    return story, qas


def generate(n: int) -> List[Tuple[str, List[QA]]]:
    seen = set()
    records: List[str] = []
    attempts = 0
    while len(records) < n and attempts < n * 6:
        attempts += 1
        story, qas = sample_with_meta()
        if story not in seen:
            seen.add(story)
            records.append((story, qas))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate standalone apology stories.")
    parser.add_argument("-n", "--num", type=int, default=1000, help="Number of stories to generate.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for deterministic output.")
    parser.add_argument("--with-qa", action="store_true", help="Include question-answer pairs.")
    parser.add_argument("--format", choices=["text", "jsonl"], default="text", help="Output format.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    stories = generate(args.num)

    as_json = args.format == "jsonl"
    include_qa = args.with_qa or as_json
    for story, qas in stories:
        text = render_story(story, qas, with_qa=include_qa, as_json=as_json)
        print(text)
        print("\n\n\n\n" if not as_json else "")


if __name__ == "__main__":
    main()
