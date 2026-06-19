#!/usr/bin/env python3
"""
storyworlds/worlds/whispering_rock_misunderstanding.py
======================================================

A standalone storyworld for a seed prompt:

    Words: whispering rock
    Features: Conflict, Misunderstanding
    Style: Slice of Life

Two children hear a phrase through a "whispering rock" that echoes only part of
what was said. The world refuses variants where the place cannot echo, the phrase
is not ambiguous, or the repair does not address the misunderstanding.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    echo: bool
    rock: str
    activity: str
    cozy_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Phrase:
    id: str
    full: str
    heard: str
    fear: str
    truth: str
    object: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    method: str
    action: str
    qa: str
    covers: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_echo_truncates(world: World) -> list[str]:
    rock = world.get("rock")
    if rock.meters["spoken_near"] < THRESHOLD or not world.place.echo:
        return []
    sig = ("echo", world.facts.get("phrase_id"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rock.meters["whispering"] += 1
    hearer = world.get("hearer")
    hearer.memes["worry"] += 1
    return ["__echo__"]


def _r_worry_becomes_conflict(world: World) -> list[str]:
    hearer = world.get("hearer")
    speaker = world.get("speaker")
    if hearer.memes["worry"] < THRESHOLD or hearer.memes["asked_angrily"] < THRESHOLD:
        return []
    sig = ("conflict", hearer.id, speaker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hearer.memes["conflict"] += 1
    speaker.memes["hurt"] += 1
    speaker.memes["conflict"] += 1
    return ["__conflict__"]


def _r_truth_clears_conflict(world: World) -> list[str]:
    hearer = world.get("hearer")
    speaker = world.get("speaker")
    rock = world.get("rock")
    if rock.meters["tested"] < THRESHOLD or hearer.memes["apology"] < THRESHOLD:
        return []
    sig = ("cleared", hearer.id, speaker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hearer.memes["conflict"] = 0.0
    speaker.memes["conflict"] = 0.0
    hearer.memes["trust"] += 1
    speaker.memes["trust"] += 1
    rock.meters["understood"] += 1
    return ["__cleared__"]


CAUSAL_RULES = [
    Rule("echo_truncates_phrase", "physical", _r_echo_truncates),
    Rule("worry_becomes_conflict", "social", _r_worry_becomes_conflict),
    Rule("truth_clears_conflict", "social", _r_truth_clears_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def phrase_can_mislead(phrase: Phrase) -> bool:
    return phrase.id != "plain_weather" and bool(phrase.heard) and phrase.heard != phrase.full


def repair_fits(phrase: Phrase, repair: Repair) -> bool:
    return phrase.id in repair.covers


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for phrase_id, phrase in PHRASES.items():
            for repair_id, repair in REPAIRS.items():
                if place.echo and phrase_can_mislead(phrase) and repair_fits(phrase, repair):
                    out.append((place_id, phrase_id, repair_id))
    return out


def predict_misunderstanding(world: World, phrase: Phrase) -> dict:
    sim = world.copy()
    sim.facts["phrase_id"] = phrase.id
    sim.get("rock").meters["spoken_near"] += 1
    propagate(sim, narrate=False)
    sim.get("hearer").memes["asked_angrily"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("hearer").memes["worry"],
        "conflict": sim.get("hearer").memes["conflict"],
    }


def phrase_text(text: str, speaker: Entity, hearer: Entity) -> str:
    return text.format(speaker=speaker.id, hearer=hearer.id)


def introduce(world: World, speaker: Entity, hearer: Entity) -> None:
    speaker.memes["friendship"] += 1
    hearer.memes["friendship"] += 1
    world.say(
        f"{speaker.id} and {hearer.id} spent Saturday at {world.place.label}. "
        f"They were {world.place.activity}, and {world.place.cozy_detail}."
    )
    world.say(
        f"Beside the path sat {world.place.rock}. Everyone in the neighborhood "
        f"called it the whispering rock because voices bounced around it in funny pieces."
    )


def speak_near_rock(world: World, speaker: Entity, phrase: Phrase) -> None:
    rock = world.get("rock")
    rock.meters["spoken_near"] += 1
    world.facts["phrase_id"] = phrase.id
    world.say(
        f"When {speaker.id} thought {world.facts['object']} had rolled away, "
        f"{speaker.pronoun()} leaned near the rock and told a grown-up, "
        f'"{phrase_text(phrase.full, speaker, world.get("hearer"))}"'
    )
    propagate(world, narrate=False)


def overhear(world: World, hearer: Entity, phrase: Phrase) -> None:
    if world.get("rock").meters["whispering"] >= THRESHOLD:
        speaker = world.get("speaker")
        world.say(
            f"But the rock sent only a piece of the sentence around the corner: "
            f'"{phrase_text(phrase.heard, speaker, hearer)}" {hearer.id} heard it and felt a hot worry in '
            f"{hearer.pronoun('possessive')} chest."
        )


def confront(world: World, hearer: Entity, speaker: Entity, phrase: Phrase) -> None:
    hearer.memes["asked_angrily"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Why would you say that about me?" {hearer.id} asked. '
        f"{speaker.id} blinked, surprised and hurt."
    )
    world.say(
        f"{hearer.id} thought {phrase_text(phrase.fear, speaker, hearer)}, "
        f"but {speaker.id} had meant something different."
    )


def adult_guides(world: World, adult: Entity, phrase: Phrase) -> None:
    pred = predict_misunderstanding(world, phrase)
    if pred["conflict"] >= THRESHOLD:
        world.facts["predicted_conflict"] = pred["conflict"]
        world.say(
            f"{adult.id} did not scold them. \"The rock may have chopped the "
            f"sentence in half,\" {adult.pronoun()} said. \"Let's check before "
            f"we decide what anyone meant.\""
        )


def test_rock(world: World, speaker: Entity, hearer: Entity, repair: Repair) -> None:
    rock = world.get("rock")
    rock.meters["tested"] += 1
    speaker.memes["explaining"] += 1
    world.say(f"{repair.action}")
    world.say(
        f"When they tried the sentence by the rock once more, the same thing "
        f"happened: the rock caught the first half and lost the rest."
    )


def apologize(world: World, hearer: Entity, speaker: Entity, phrase: Phrase) -> None:
    hearer.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am sorry I got angry before I asked," {hearer.id} said. '
        f"{speaker.id} smiled a little and explained the whole sentence: "
        f"{phrase_text(phrase.truth, speaker, hearer)}"
    )
    world.say(
        f"They found {world.facts['object']} together and agreed that the "
        f"whispering rock was interesting, but not a very good messenger."
    )


def closing(world: World, speaker: Entity, hearer: Entity) -> None:
    if world.get("rock").meters["understood"] >= THRESHOLD:
        world.say(
            f"After that, {speaker.id} and {hearer.id} sat on the warm path and "
            f"shared a snack. When the rock whispered again, they laughed and "
            f"asked each other what they really meant."
        )


def tell(place: Place, phrase: Phrase, repair: Repair,
         speaker_name: str = "Mia", speaker_gender: str = "girl",
         hearer_name: str = "Ben", hearer_gender: str = "boy",
         adult_name: str = "Nana", adult_gender: str = "woman",
         trait: str = "careful") -> World:
    world = World(place)
    speaker = world.add(Entity(id=speaker_name, kind="character", type=speaker_gender,
                               label=speaker_name, role="speaker", traits=[trait]))
    hearer = world.add(Entity(id=hearer_name, kind="character", type=hearer_gender,
                              label=hearer_name, role="hearer", traits=["sensitive"]))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender,
                             label=adult_name, role="adult"))
    world.add(Entity(id="rock", type="rock", label="whispering rock"))
    world.facts["object"] = phrase.object

    introduce(world, speaker, hearer)
    world.para()
    speak_near_rock(world, speaker, phrase)
    overhear(world, hearer, phrase)
    confront(world, hearer, speaker, phrase)

    world.para()
    adult_guides(world, adult, phrase)
    test_rock(world, speaker, hearer, repair)
    apologize(world, hearer, speaker, phrase)
    closing(world, speaker, hearer)

    world.facts.update(
        speaker=speaker, hearer=hearer, adult=adult, place=place,
        phrase=phrase, repair=repair,
        resolved=world.get("rock").meters["understood"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden": Place("garden", "the community garden", True,
                    "a flat gray rock under the lilac bush",
                    "watering tomato pots", "bees hummed softly over the flowers",
                    tags={"garden", "echo"}),
    "courtyard": Place("courtyard", "the apartment courtyard", True,
                       "a smooth rock beside the brick wall",
                       "drawing chalk roads", "someone upstairs was playing quiet music",
                       tags={"courtyard", "echo"}),
    "playground": Place("playground", "the playground", True,
                        "a speckled rock by the tunnel slide",
                        "building a tiny pebble town", "the afternoon sun warmed the bench",
                        tags={"playground", "echo"}),
    "open_field": Place("open_field", "the open field", False,
                        "a small rock in the grass",
                        "flying a paper kite", "there was nothing nearby for voices to bounce from",
                        tags={"field"}),
}

PHRASES = {
    "not_ben": Phrase(
        "not_ben", "I did not mean {hearer} should be left out; I meant the blue bucket was not {hearer}'s.",
        "{hearer} should be left out", "{speaker} wanted to leave {hearer} out",
        "{speaker} was only saying the blue bucket belonged to someone else.",
        "the blue bucket", tags={"sharing", "listening"}),
    "hide_card": Phrase(
        "hide_card", "Hide the card so {hearer} will be surprised after lunch.",
        "Hide the card from {hearer}", "{speaker} was keeping something unkind from {hearer}",
        "{speaker} was hiding a surprise card for {hearer}, not being unkind.",
        "the surprise card", tags={"surprise", "listening"}),
    "broken_truck": Phrase(
        "broken_truck", "The truck is not {hearer}'s fault; the wheel was loose already.",
        "{hearer}'s fault", "someone was blaming {hearer}",
        "{speaker} was saying {hearer} was not to blame because the wheel had already been loose.",
        "the toy truck", tags={"toy", "forgiveness"}),
    "plain_weather": Phrase(
        "plain_weather", "It might rain later, so bring the blanket inside.",
        "bring the blanket inside", "someone was worried about rain",
        "The sentence was plain and did not accuse anyone.",
        "the picnic blanket", tags={"weather"}),
}

REPAIRS = {
    "repeat_test": Repair(
        "repeat_test", "repeat",
        "They stood on opposite sides of the rock and repeated the sentence slowly, then listened to which words came back.",
        "tested the echo by repeating the full sentence slowly",
        covers={"not_ben", "broken_truck"}, tags={"listening", "echo"}),
    "ask_full": Repair(
        "ask_full", "ask",
        "They asked for the whole sentence again, this time face to face, and then tried saying it once through the rock.",
        "asked for the whole sentence face to face",
        covers={"not_ben", "hide_card", "broken_truck"}, tags={"listening"}),
    "show_object": Repair(
        "show_object", "show",
        "They looked at the thing together and let the object explain the missing part of the sentence.",
        "looked at the object together to understand the missing words",
        covers={"hide_card", "broken_truck"}, tags={"evidence"}),
}

GIRL_NAMES = ["Mia", "Ava", "Nora", "Lily", "Zoe", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Max", "Theo", "Finn"]
TRAITS = ["careful", "quiet", "kind", "thoughtful", "curious", "patient"]


@dataclass
class StoryParams:
    place: str
    phrase: str
    repair: str
    speaker: str
    speaker_gender: str
    hearer: str
    hearer_gender: str
    adult: str
    adult_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "echo": [("What is an echo?",
              "An echo is a sound that bounces off a hard surface and comes back to your ears.")],
    "garden": [("What happens in a community garden?",
                "People share a garden space to grow plants, water them, and take care of them together.")],
    "courtyard": [("Why do courtyards make sounds bounce?",
                   "A courtyard can have walls around it, and hard walls can bounce voices back as echoes.")],
    "playground": [("Why is it important to listen carefully on a playground?",
                    "Playgrounds can be noisy, so it is easy to hear only part of what someone says.")],
    "sharing": [("Why can sharing be confusing?",
                 "People may think something is being taken away, so it helps to explain whose turn or object it is.")],
    "surprise": [("Can a secret be kind?",
                  "Yes. Some secrets, like a surprise card, are meant to make someone happy later.")],
    "toy": [("Why should you check before blaming someone for a broken toy?",
             "A toy might have been loose or cracked already, so checking helps you be fair.")],
    "listening": [("What should you do if you only hear part of a sentence?",
                   "Ask the person to say the whole sentence again before deciding what they meant.")],
    "forgiveness": [("What does it mean to forgive someone?",
                     "Forgiving means you let go of anger after someone is sorry and tries to make things right.")],
    "evidence": [("What is evidence?",
                  "Evidence is something you can check that helps show what really happened.")],
}
KNOWLEDGE_ORDER = ["echo", "garden", "courtyard", "playground", "sharing", "surprise",
                   "toy", "listening", "forgiveness", "evidence"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a slice-of-life story for young children that includes the words "whispering rock" and centers on a misunderstanding.',
        f"Tell a gentle story where {f['hearer'].id} hears only part of what {f['speaker'].id} says near a whispering rock and the friends fix the conflict by listening.",
        "Write a realistic playground or garden story where an echo turns a sentence into a hurt feeling, and the children learn to ask what was really meant.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    speaker, hearer, adult = f["speaker"], f["hearer"], f["adult"]
    phrase, repair = f["phrase"], f["repair"]
    return [
        ("Who is the story about?",
         f"It is about {speaker.id} and {hearer.id} at {world.place.label}, with {adult.id} helping them listen."),
        ("Why was the rock called the whispering rock?",
         "Voices bounced around it in funny pieces, so it sometimes carried only part of a sentence."),
        (f"What did {hearer.id} hear?",
         f"{hearer.id} heard only \"{phrase_text(phrase.heard, speaker, hearer)}.\" "
         f"That made {hearer.pronoun('object')} worry that {phrase_text(phrase.fear, speaker, hearer)}."),
        ("What was the full truth?",
         phrase_text(phrase.truth, speaker, hearer)),
        ("How did they solve the misunderstanding?",
         f"They {repair.qa}. Then {hearer.id} apologized for getting angry before asking."),
        ("How did the story end?",
         f"The conflict cleared, and {speaker.id} and {hearer.id} stayed friends. They learned to ask for the whole sentence when the rock whispered."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"echo", "listening"} | set(world.place.tags) | set(world.facts["phrase"].tags) | set(world.facts["repair"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    seen: set[int] = set()
    for ent in world.entities.values():
        if id(ent) in seen:
            continue
        seen.add(id(ent))
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "not_ben", "ask_full", "Mia", "girl", "Ben", "boy", "Nana", "woman", "careful"),
    StoryParams("courtyard", "hide_card", "show_object", "Sam", "boy", "Ava", "girl", "Dad", "man", "kind"),
    StoryParams("playground", "broken_truck", "repeat_test", "Nora", "girl", "Leo", "boy", "Miss June", "woman", "patient"),
]


def explain_rejection(place: Place, phrase: Phrase, repair: Repair) -> str:
    if not place.echo:
        return f"(No story: {place.label} has no echoing surface, so the rock would not whisper a chopped sentence.)"
    if not phrase_can_mislead(phrase):
        return f"(No story: the phrase '{phrase.full}' is not ambiguous enough when shortened, so it should not create a fair misunderstanding.)"
    return f"(No story: repair '{repair.id}' does not address the misunderstanding in phrase '{phrase.id}'.)"


ASP_RULES = r"""
echo_place(P) :- place(P), echoes(P).
ambiguous(Ph) :- phrase(Ph), truncated(Ph), meaningful(Ph).
fixes(Ph, R) :- phrase(Ph), repair(R), covers(R, Ph).
valid(P, Ph, R) :- echo_place(P), ambiguous(Ph), fixes(Ph, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.echo:
            lines.append(asp.fact("echoes", pid))
    for pid, phrase in PHRASES.items():
        lines.append(asp.fact("phrase", pid))
        if phrase_can_mislead(phrase):
            lines.append(asp.fact("truncated", pid))
            lines.append(asp.fact("meaningful", pid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for phrase_id in sorted(repair.covers):
            lines.append(asp.fact("covers", rid, phrase_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: whispering rock misunderstanding. Unspecified choices are randomized.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--phrase", choices=PHRASES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--speaker")
    ap.add_argument("--speaker-gender", choices=["girl", "boy"])
    ap.add_argument("--hearer")
    ap.add_argument("--hearer-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice([n for n in pool if n != avoid])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.phrase and args.repair:
        place, phrase, repair = PLACES[args.place], PHRASES[args.phrase], REPAIRS[args.repair]
        if not (place.echo and phrase_can_mislead(phrase) and repair_fits(phrase, repair)):
            raise StoryError(explain_rejection(place, phrase, repair))
    if args.place and not PLACES[args.place].echo:
        phrase = PHRASES[args.phrase] if args.phrase else next(iter(PHRASES.values()))
        repair = REPAIRS[args.repair] if args.repair else next(iter(REPAIRS.values()))
        raise StoryError(explain_rejection(PLACES[args.place], phrase, repair))
    if args.phrase and not phrase_can_mislead(PHRASES[args.phrase]):
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        repair = REPAIRS[args.repair] if args.repair else next(iter(REPAIRS.values()))
        raise StoryError(explain_rejection(place, PHRASES[args.phrase], repair))
    if args.phrase and args.repair and not repair_fits(PHRASES[args.phrase], REPAIRS[args.repair]):
        place = PLACES[args.place] if args.place else next(p for p in PLACES.values() if p.echo)
        raise StoryError(explain_rejection(place, PHRASES[args.phrase], REPAIRS[args.repair]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.phrase is None or c[1] == args.phrase)
              and (args.repair is None or c[2] == args.repair)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, phrase, repair = rng.choice(sorted(combos))
    sg = args.speaker_gender or rng.choice(["girl", "boy"])
    hg = args.hearer_gender or rng.choice(["girl", "boy"])
    speaker = args.speaker or _pick_name(rng, sg)
    hearer = args.hearer or _pick_name(rng, hg, avoid=speaker)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult = args.adult or ("Nana" if adult_gender == "woman" else "Dad")
    return StoryParams(place, phrase, repair, speaker, sg, hearer, hg,
                       adult, adult_gender, rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PHRASES[params.phrase], REPAIRS[params.repair],
                 params.speaker, params.speaker_gender, params.hearer,
                 params.hearer_gender, params.adult, params.adult_gender,
                 params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, phrase, repair) combos:\n")
        for place, phrase, repair in combos:
            print(f"  {place:10} {phrase:14} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.speaker} and {p.hearer}: {p.phrase} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
