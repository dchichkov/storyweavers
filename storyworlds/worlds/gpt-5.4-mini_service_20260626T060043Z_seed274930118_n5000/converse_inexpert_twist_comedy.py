#!/usr/bin/env python3
"""
Standalone storyworld: converse, inexpert, Twist, Comedy.

Premise:
A small comedy about a character who tries to have a proper conversation but
keeps doing it in an inexpert way. The twist is that the awkward conversation
accidentally solves a little problem, turning embarrassment into a happy laugh.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    topics: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity | ObjectThing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def characters(self):
        return [e for e in self.entities.values() if getattr(e, "kind", "") == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", cozy=True, topics={"tea", "toast", "spoon"}),
    "porch": Place(id="porch", label="the porch", cozy=True, topics={"tea", "birds", "chair"}),
    "library": Place(id="library", label="the library nook", cozy=True, topics={"book", "whisper", "ladder"}),
}

REASONS = {
    "tea": "make tea",
    "book": "find the missing book",
    "toaster": "fix the toaster",
}

TOOLS = {
    "spoon": ObjectThing(id="spoon", label="spoon", phrase="a very shiny spoon"),
    "guidebook": ObjectThing(id="guidebook", label="guidebook", phrase="an overly serious little guidebook"),
    "manual": ObjectThing(id="manual", label="manual", phrase="a crinkly appliance manual"),
}

CHAR_NAMES = ["Milo", "Nia", "Toby", "Pia", "Arlo", "June", "Otto", "Luna"]
CHAR_TYPES = ["boy", "girl", "person"]
TRAITS = ["cheerful", "bouncy", "careful", "curious", "dramatic", "earnest"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    hero_trait: str
    partner_name: str
    partner_type: str
    reason: str
    twist: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _noun(ent) -> str:
    if getattr(ent, "label", ""):
        return ent.label
    return ent.id


def _subject_name(ent) -> str:
    return ent.id


def _need_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _setting_line(place: Place, reason: str) -> str:
    if reason == "tea":
        return f"The {place.label.removeprefix('the ')} smelled warm and a little like honey."
    if reason == "book":
        return f"Quiet corners hid under soft light in {place.label}."
    return f"{place.label.capitalize()} looked ready for a tiny problem and a silly fix."


def _twist_line(twist: str, reason: str) -> str:
    if twist == "mistaken_order":
        return "The twist was that one wrong word turned the whole talk upside down."
    if twist == "secret_help":
        return "The twist was that the clumsy talking was secretly helping all along."
    if twist == "echo_reply":
        return "The twist was that every careful reply came back a little too loudly and funnily."
    return f"The twist was that the {reason} problem had a very funny answer."


def _prediction(world: World, reason: str) -> dict:
    if reason == "tea":
        return {"spill": True, "fix": True}
    if reason == "book":
        return {"spill": False, "fix": True}
    return {"spill": False, "fix": True}


def _do_converse(world: World, hero: Entity, partner: Entity, reason: str, twist: str) -> None:
    hero.memes["nervous"] = hero.memes.get("nervous", 0) + 1
    hero.memes["eager"] = hero.memes.get("eager", 0) + 1
    world.say(
        f"{_subject_name(hero)} wanted to converse in a proper way, but {hero.pronoun('possessive')} words came out inexpert and crooked."
    )
    if reason == "tea":
        world.say(
            f'{_subject_name(hero)} pointed at the kettle and said, "I would like the tea, please, and perhaps a spoon for my big important thinking."'
        )
    elif reason == "book":
        world.say(
            f'{_subject_name(hero)} whispered, "Excuse me, I am searching for the lost book with the blue cover and the tiny moon."'
        )
    else:
        world.say(
            f'{_subject_name(hero)} announced, "I am here to fix the toaster, which is currently behaving like a tiny grumpy dragon."'
        )


def _response(world: World, partner: Entity, hero: Entity, reason: str, twist: str) -> None:
    partner.memes["surprise"] = partner.memes.get("surprise", 0) + 1
    if twist == "mistaken_order":
        world.say(
            f"{_subject_name(partner)} blinked, then laughed, because {hero.id} had accidentally ordered the funniest thing in the room."
        )
    elif twist == "secret_help":
        world.say(
            f"{_subject_name(partner)} noticed the awkward sentence was actually exactly what was needed."
        )
    else:
        world.say(
            f"{_subject_name(partner)} answered kindly, and the answer came back with a bright little bounce."
        )


def _turn(world: World, hero: Entity, partner: Entity, reason: str, twist: str) -> None:
    hero.memes["embarrassed"] = hero.memes.get("embarrassed", 0) + 1
    if twist == "mistaken_order":
        world.say(
            f"Before {hero.id} could explain, the room had already imagined a very different story, and everybody giggled."
        )
        world.say(
            f"Then {partner.id} pointed at the real problem, and it turned out {hero.id} had only mixed up two words."
        )
    elif twist == "secret_help":
        world.say(
            f"{hero.id}'s inexpert way of talking made the right clue stick out like a trumpet in a pillow fort."
        )
        world.say(
            f"{partner.id} followed that clue and found the answer hiding in plain sight."
        )
    else:
        world.say(
            f"The conversation wobbled, swerved, and then landed exactly where it needed to be."
        )


def _resolution(world: World, hero: Entity, partner: Entity, reason: str, twist: str) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    partner.memes["joy"] = partner.memes.get("joy", 0) + 1
    if reason == "tea":
        world.say(
            f"In the end, {hero.id} and {partner.id} shared tea, and the spoon looked proud to have started the whole joke."
        )
    elif reason == "book":
        world.say(
            f"In the end, the missing book was found, and {hero.id} laughed at how a shy question had led the way."
        )
    else:
        world.say(
            f"In the end, the toaster stopped sulking, and everyone agreed it was a very silly machine."
        )
    if twist == "mistaken_order":
        world.say(
            f"{hero.id} grinned at the accident, because the wrong order had turned into the right laugh."
        )
    elif twist == "secret_help":
        world.say(
            f"{hero.id} learned that even inexpert conversation can be clever when it is honest and kind."
        )
    else:
        world.say(
            f"{partner.id} smiled as the room settled, bright and cozy, after the funny little twist."
        )


def tell(place: Place, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_type))
    tool = world.add(Entity(id="tool", kind="thing", type="thing", label="tool", phrase=REASONS[params.reason]))

    world.facts.update(hero=hero, partner=partner, tool=tool, reason=params.reason, twist=params.twist, place=place)

    world.say(f"{hero.id} was {params.hero_trait} and loved to converse, even when {hero.pronoun('possessive')} words came out inexpert.")
    world.say(f"{partner.id} was nearby, ready to listen, because something small and funny was about to happen.")
    world.para()
    world.say(_setting_line(place, params.reason))
    _do_converse(world, hero, partner, params.reason, params.twist)
    _response(world, partner, hero, params.reason, params.twist)
    world.para()
    world.say(_twist_line(params.twist, params.reason))
    _turn(world, hero, partner, params.reason, params.twist)
    _resolution(world, hero, partner, params.reason, params.twist)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for reason in REASONS:
            for twist in {"mistaken_order", "secret_help", "echo_reply"}:
                if place_id == "library" and reason == "tea":
                    continue
                combos.append((place_id, reason, twist))
    return combos


def explain_rejection(place: str, reason: str) -> str:
    if place == "library" and reason == "tea":
        return "(No story: tea is too clattery for the library nook's calm mood. Try the kitchen or porch.)"
    return "(No story: that combination does not make a clear comedy twist.)"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    reason = f["reason"]
    twist = f["twist"]
    return [
        f'Write a short comedy story for a small child about a very inexpert conversation that leads to a funny {twist.replace("_", " ")}.',
        f"Tell a gentle story where {hero.id} tries to converse carefully with {partner.id}, but the talk goes awkwardly and then turns into a happy surprise.",
        f'Write a funny TinyStories-style tale that includes the word "converse" and ends with a cheerful twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    reason = f["reason"]
    twist = f["twist"]
    place = f["place"].label
    return [
        QAItem(
            question=f"Who was trying to converse in the story?",
            answer=f"{hero.id} was trying to converse, but {hero.pronoun('possessive')} way of talking was inexpert and funny.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"The story happened at {place}, which gave the conversation a cozy stage.",
        ),
        QAItem(
            question=f"What made the conversation a twist instead of a simple chat?",
            answer=f"The twist was {twist.replace('_', ' ')}, so the awkward talk turned into a funny surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to converse?",
            answer="To converse means to talk with someone, usually by taking turns speaking and listening.",
        ),
        QAItem(
            question="What does inexpert mean?",
            answer="Inexpert means not very skilled yet, like when someone is still learning how to do something.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you thought would happen.",
        ),
        QAItem(
            question="Why can comedy be funny?",
            answer="Comedy can be funny when ordinary things go a little wrong and make people laugh in a harmless way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(kitchen). place(porch). place(library).
reason(tea). reason(book). reason(toaster).
twist(mistaken_order). twist(secret_help). twist(echo_reply).

valid(P,R,T) :- place(P), reason(R), twist(T), not bad(P,R).
bad(library,tea).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid in REASONS:
        lines.append(asp.fact("reason", rid))
    for tid in {"mistaken_order", "secret_help", "echo_reply"}:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about inexpert conversation and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--reason", choices=sorted(REASONS))
    ap.add_argument("--twist", choices=["mistaken_order", "secret_help", "echo_reply"])
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--gender", choices=["girl", "boy", "person"])
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.reason:
        combos = [c for c in combos if c[1] == args.reason]
    if args.twist:
        combos = [c for c in combos if c[2] == args.twist]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, reason, twist = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(CHAR_TYPES)
    hero_name = args.name or rng.choice(CHAR_NAMES)
    partner = args.partner or rng.choice([n for n in CHAR_NAMES if n != hero_name])
    hero_trait = rng.choice(TRAITS)
    partner_type = rng.choice([t for t in CHAR_TYPES if t != hero_type] or CHAR_TYPES)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        hero_trait=hero_trait,
        partner_name=partner,
        partner_type=partner_type,
        reason=reason,
        twist=twist,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if getattr(e, "label", ""):
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({getattr(e, 'kind', 'thing')}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="kitchen", hero_name="Milo", hero_type="boy", hero_trait="cheerful", partner_name="Nia", partner_type="girl", reason="tea", twist="mistaken_order"),
            StoryParams(place="porch", hero_name="June", hero_type="girl", hero_trait="curious", partner_name="Otto", partner_type="boy", reason="book", twist="secret_help"),
            StoryParams(place="library", hero_name="Arlo", hero_type="boy", hero_trait="dramatic", partner_name="Luna", partner_type="girl", reason="toaster", twist="echo_reply"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
