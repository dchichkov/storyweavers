#!/usr/bin/env python3
"""
A small ghost-story world about curiosity, a spooky twist, and a harmless
school mystery involving alum and a very rude smell.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    place: str
    object: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class Location:
    id: str
    label: str
    eerie: bool
    echo: bool
    hidey: bool
    smells: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    short: str
    reveals: str
    is_spooky: bool = False


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    clues: dict[str, Clue] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(location=self.location)
        w.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes), traits=list(v.traits))
                       for k, v in self.entities.items()}
        w.clues = {k: replace(v) for k, v in self.clues.items()}
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


LOCATIONS = {
    "attic": Location("attic", "the old attic", eerie=True, echo=True, hidey=True, smells={"dust", "wood"}),
    "hall": Location("hall", "the school hall", eerie=False, echo=True, hidey=False, smells={"chalk"}),
    "closet": Location("closet", "the supply closet", eerie=True, echo=False, hidey=True, smells={"paper", "soap"}),
}

OBJECTS = {
    "lantern": Clue("lantern", "a small lantern", "small lantern", "the room shine yellow", is_spooky=False),
    "alum": Clue("alum", "a jar of alum", "jar of alum", "calm the water and make crystals", is_spooky=False),
    "bell": Clue("bell", "a tiny bell", "tiny bell", "ring when touched", is_spooky=False),
}

HELPERS = {
    "cat": "a quiet cat",
    "friend": "a brave friend",
    "teacher": "the teacher",
}

GHOST_WORDS = {"ghost", "haunt", "whisper", "cold", "echo"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly ghost-story world with curiosity, a twist, and dialogue.")
    ap.add_argument("--place", choices=sorted(LOCATIONS))
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
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


def _check(params: StoryParams) -> None:
    if params.object == "alum" and params.place == "hall":
        return
    if params.place == "hall" and params.object != "alum":
        raise StoryError("This hall story needs alum so the twist has a gentle scientific answer.")
    if params.place == "attic" and params.object == "bell":
        return
    if params.place == "closet" and params.object in {"alum", "lantern"}:
        return


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(LOCATIONS))
    obj = args.object or ("alum" if place == "hall" else rng.choice(list(OBJECTS)))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(["Mina", "Nora", "Toby", "Lena", "Iris", "Owen"])
    params = StoryParams(name=name, place=place, object=obj, helper=helper)
    _check(params)
    return params


def _do_gain(world: World, who: Entity, what: str, amount: float = 1.0) -> None:
    who.meters[what] = who.meters.get(what, 0.0) + amount


def _do_mood(world: World, who: Entity, what: str, amount: float = 1.0) -> None:
    who.memes[what] = who.memes.get(what, 0.0) + amount


def _haunt_level(world: World) -> float:
    hero = world.entities["hero"]
    return hero.memes.get("curiosity", 0.0) + (1.0 if world.location.eerie else 0.0) + (1.0 if "ghost" in world.location.smells else 0.0)


def simulate(world: World) -> None:
    hero = world.add(Entity("hero", "character", world.facts["name"], traits=["curious", "small"]))
    helper = world.add(Entity("helper", "character", world.facts["helper"]))
    item = world.clues[world.facts["object"]]

    world.say(f"{hero.label} went into {world.location.label} because {hero.label.lower()} was curious about the strange quiet there.")
    world.say(f"On a shelf sat {item.short}, and {hero.label} whispered, \"What does it do?\"")
    _do_mood(world, hero, "curiosity", 1.0)

    if world.location.eerie:
        _do_mood(world, hero, "spook", 1.0)
        world.say(f"The air felt cold, and every little sound made an echo like a ghost trying to copy the room.")

    if world.facts["object"] == "alum":
        _do_gain(world, hero, "knowledge", 1.0)
        world.say(f"{hero.label} opened the jar and saw that alum could make the water turn into shiny crystals.")
        world.say(f"\"So that is the trick,\" {helper.label} said. \"It is not magic. It is just alum doing its work.\"")
    else:
        world.say(f"{item.label.capitalize()} flashed once in the light, and {hero.label} thought it might be haunted.")

    if world.location.id == "attic":
        world.say("Then came a loud, rude fart from behind the boxes.")
        _do_mood(world, hero, "alarm", 1.0)
        world.facts["fart"] = True
        world.say(f"{hero.label} gasped, but the fart only made the old cat blink from under a blanket.")
    elif world.location.id == "closet":
        world.say("Then a sneaky fart drifted out of the dark corner.")
        _do_mood(world, hero, "alarm", 1.0)
        world.facts["fart"] = True
        world.say(f"{hero.label} laughed nervously, because the smell was spooky but not scary once {helper.label} opened the door.")
    else:
        world.say("A windy puff made the papers flutter like a ghost's skirt.")
        world.facts["fart"] = False

    world.para()
    _do_mood(world, hero, "relief", 1.0)
    world.say(f"{helper.label.capitalize()} pointed to the jar and said, \"Look again.\"")
    world.say(f"{hero.label} looked, thought hard, and had a twist of an idea: the mystery was a smell, a shadow, and a shiny clue all at once.")
    if world.facts["object"] == "alum":
        world.say(f"Together they used the alum safely, and the little crystals sparkled while the scary feeling faded away.")
    else:
        world.say(f"Together they found the hidden trick and turned the odd thing into an ordinary one.")

    world.para()
    world.say(f"By the end, {hero.label} was smiling instead of shivering, and the room felt less like a ghost story and more like a puzzle story.")
    world.facts["resolved"] = True
    world.facts["hero"] = hero
    world.facts["helper_ent"] = helper
    world.facts["item"] = item


def tell(params: StoryParams) -> World:
    world = World(location=LOCATIONS[params.place])
    world.clues[params.object] = OBJECTS[params.object]
    world.facts.update(name=params.name, place=params.place, object=params.object, helper=HELPERS[params.helper])
    simulate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short ghost story for a child about {world.facts['name']} exploring {world.location.label} with {world.facts['helper']}, including the word alum.",
        f"Tell a spooky but gentle story with dialogue, curiosity, and a twist where a fart turns out not to be a real ghost.",
        f"Write a child-friendly mystery in which a curious child notices alum, hears a strange fart, and learns what is really happening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper_ent"]
    item = world.facts["item"]
    return [
        QAItem(
            question=f"Why did {hero.label} go into {world.location.label}?",
            answer=f"{hero.label} went there because {hero.label.lower()} was curious about the quiet and wanted to see what the strange place was hiding.",
        ),
        QAItem(
            question=f"What did {hero.label} find on the shelf?",
            answer=f"{hero.label} found {item.short} on the shelf and asked what it could do.",
        ),
        QAItem(
            question=f"How did {helper.label} help solve the spooky problem?",
            answer=f"{helper.label} helped by pointing out the clue and explaining that the eerie feeling was a twist, not a real ghost.",
        ),
        QAItem(
            question="What made the story feel spooky at first?",
            answer="The cold air, the echoes, and the strange fart made the room feel like it might be haunted.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is alum used for?",
            answer="Alum is a substance that can help crystals form, and it is often used for simple science experiments.",
        ),
        QAItem(
            question="Why can a fart be funny instead of scary?",
            answer="A fart is a silly body sound, so it can surprise people but usually does not mean danger.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask questions, and learn more.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"location: {world.location.label} eerie={world.location.eerie} echo={world.location.echo}")
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
place(attic). place(hall). place(closet).
object(alum). object(lantern). object(bell).
helper(cat). helper(friend). helper(teacher).

eerie(attic). echo(attic). hidey(attic).
echo(hall).
eerie(closet). hidey(closet).

interesting(P,O) :- place(P), object(O), P = hall, O = alum.
interesting(P,O) :- place(P), object(O), P = closet, (O = alum; O = lantern).
interesting(P,O) :- place(P), object(O), P = attic, O = bell.

twist(P,O) :- interesting(P,O).
dialogue(P,O) :- twist(P,O).
curiosity_story(P,O,H) :- twist(P,O), helper(H).

#show twist/2.
#show dialogue/2.
#show curiosity_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in LOCATIONS:
        lines.append(asp.fact("place", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for pid, loc in LOCATIONS.items():
        if loc.eerie:
            lines.append(asp.fact("eerie", pid))
        if loc.echo:
            lines.append(asp.fact("echo", pid))
        if loc.hidey:
            lines.append(asp.fact("hidey", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show twist/2.\n#show dialogue/2.\n#show curiosity_story/3."))
    twists = asp.atoms(model, "twist")
    dialogs = asp.atoms(model, "dialogue")
    cur = asp.atoms(model, "curiosity_story")
    return sorted(set(twists + dialogs + cur))


def asp_verify() -> int:
    ok = set(asp_valid())
    py = {
        ("attic", "bell"),
        ("hall", "alum"),
        ("closet", "alum"),
        ("closet", "lantern"),
    }
    if ok == {(a, b) for (a, b) in py if len((a, b)) == 2}:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(ok))
    print("PY :", sorted(py))
    return 1


CURATED = [
    StoryParams(name="Mina", place="hall", object="alum", helper="teacher"),
    StoryParams(name="Toby", place="attic", object="bell", helper="cat"),
    StoryParams(name="Lena", place="closet", object="lantern", helper="friend"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        print(asp_program("#show twist/2.\n#show dialogue/2.\n#show curiosity_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show twist/2.\n#show dialogue/2.\n#show curiosity_story/3."))
        print(sorted(set(asp.atoms(model, "twist"))))
        print(sorted(set(asp.atoms(model, "dialogue"))))
        print(sorted(set(asp.atoms(model, "curiosity_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place}, {p.object}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
