#!/usr/bin/env python3
"""
A standalone story world for a tiny fairy-tale domain about a peeve
that grows into a moral choice, then softens through kindness.
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

MORAL_VALUES = {
    "kindness": "kindness",
    "honesty": "honesty",
    "sharing": "sharing",
    "patience": "patience",
    "courage": "courage",
    "generosity": "generosity",
}

PLACES = {
    "cottage": ("the cottage at the edge of the wood", {"garden", "kitchen", "lane"}),
    "wood": ("the whispering wood", {"clearing", "path", "oak"}),
    "village": ("the little village square", {"square", "well", "bakery"}),
    "castle": ("the old castle courtyard", {"courtyard", "hall", "tower"}),
}

ACTORS = {
    "girl": {"type": "girl", "names": ["Mina", "Lina", "Tessa", "Elin", "Nora"]},
    "boy": {"type": "boy", "names": ["Robin", "Pip", "Theo", "Bram", "Finn"]},
    "fox": {"type": "fox", "names": ["Fenn", "Sable", "Ember"]},
    "mouse": {"type": "mouse", "names": ["Midge", "Nip", "Pipkin"]},
    "owl": {"type": "owl", "names": ["Orin", "Wren", "Hush"]},
}

PEEVES = {
    "crumbs": "crumbs on the table",
    "noise": "loud laughter at the wrong time",
    "teasing": "teasing words that prick like thorns",
    "mess": "a muddy trail through a clean room",
    "waiting": "waiting and waiting with no answer",
}

MORAL_CHOICES = {
    "kindness": "share the warm bread",
    "honesty": "tell the truth about the broken cup",
    "sharing": "divide the honey cake fairly",
    "patience": "wait for the lantern to be lit",
    "courage": "speak gently to the worried king",
    "generosity": "give the last apple to a friend",
}

MORAL_TURNS = {
    "kindness": "a kind heart can mend a small hurt",
    "honesty": "truth may sting for a moment, but it keeps trust strong",
    "sharing": "sharing makes one feast feel like two",
    "patience": "waiting can be wise when rush would spoil the plan",
    "courage": "soft courage can be louder than a shout",
    "generosity": "a gift given freely often returns as joy",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place_id: str
    place_phrase: str
    mood: str = "quiet"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_kind: str
    hero_name: str
    peer_kind: str
    peer_name: str
    peeve: str
    moral: str
    seed: Optional[int] = None


def _subject_name(e: Entity) -> str:
    return e.label or e.id


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _capitalize_sentence(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _pronoun_pair(entity: Entity) -> tuple[str, str, str]:
    return entity.pronoun("subject"), entity.pronoun("object"), entity.pronoun("possessive")


def _mood_from_peeve(peeve: str) -> tuple[str, str]:
    if peeve == "crumbs":
        return ("cross", "crumbs")
    if peeve == "noise":
        return ("startled", "noise")
    if peeve == "teasing":
        return ("wounded", "teasing")
    if peeve == "mess":
        return ("bothered", "mess")
    return ("restless", "waiting")


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place for this fairy tale.")
    if params.hero_kind not in ACTORS or params.peer_kind not in ACTORS:
        raise StoryError("Unknown character kind for this fairy tale.")
    if params.peeve not in PEEVES:
        raise StoryError("Unknown peeve.")
    if params.moral not in MORAL_VALUES:
        raise StoryError("Unknown moral value.")
    if params.hero_kind == params.peer_kind and params.hero_name == params.peer_name:
        raise StoryError("The hero and the peer must be different characters.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    place_phrase, _ = PLACES[params.place]
    world = World(place_id=params.place, place_phrase=place_phrase)

    hero_type = ACTORS[params.hero_kind]["type"]
    peer_type = ACTORS[params.peer_kind]["type"]
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=params.hero_name))
    peer = world.add(Entity(id="peer", kind="character", type=peer_type, label=params.peer_name))

    peeve_label = PEEVES[params.peeve]
    moral_verb = MORAL_CHOICES[params.moral]
    moral_truth = MORAL_TURNS[params.moral]

    world.facts.update(
        hero=hero,
        peer=peer,
        peeve_id=params.peeve,
        peeve_label=peeve_label,
        moral_key=params.moral,
        moral_verb=moral_verb,
        moral_truth=moral_truth,
        place=params.place,
        place_phrase=place_phrase,
        hero_kind=params.hero_kind,
        peer_kind=params.peer_kind,
    )

    noise, tag = _mood_from_peeve(params.peeve)

    world.say(
        f"Once in {place_phrase}, there lived {hero.label}, "
        f"{_article(hero.type)} {hero.type} with a gentle heart."
    )
    world.say(
        f"{hero.label} often crossed paths with {peer.label}, "
        f"{_article(peer.type)} {peer.type} who liked to keep busy."
    )
    world.say(
        f"But {hero.label} had one small peeve: {peeve_label}. "
        f"It made {hero.pronoun('object')} feel {noise}."
    )

    world.para()
    world.say(
        f"One day, the {place_phrase.split('the ', 1)[1]} was full of golden light, "
        f"and {peer.label} reached for {moral_verb}."
    )
    if params.peeve == "teasing":
        world.say(
            f"A few sharp words floated through the air, and {hero.label}'s cheeks grew warm."
        )
    elif params.peeve == "mess":
        world.say(
            f"A muddy trail crossed the floor, and the clean stones looked sadly smudged."
        )
    elif params.peeve == "crumbs":
        world.say(
            f"Little crumbs dotted the table like tiny brown stars."
        )
    elif params.peeve == "noise":
        world.say(
            f"The laughter rose higher and higher, until the birds in the eaves went quiet."
        )
    else:
        world.say(
            f"The promise of help was late, and waiting began to feel heavy."
        )

    world.say(
        f"{hero.label} wanted to complain, but {hero.pronoun('possessive')} "
        f"mama-bird wisdom remembered that a small hurt can grow larger if it is fed."
    )

    world.para()
    world.say(
        f"So {hero.label} took a breath and chose {moral_verb} instead."
    )
    if params.moral == "kindness":
        world.say(f"{hero.label} offered a smile and shared the warm bread.")
    elif params.moral == "honesty":
        world.say(f"{hero.label} said the truth about the broken cup, softly and plainly.")
    elif params.moral == "sharing":
        world.say(f"{hero.label} divided the honey cake fairly, so no one had too much or too little.")
    elif params.moral == "patience":
        world.say(f"{hero.label} waited beside the door until the lantern was lit.")
    elif params.moral == "courage":
        world.say(f"{hero.label} spoke gently to the worried king, even while {hero.pronoun('possessive')} knees shook.")
    else:
        world.say(f"{hero.label} gave the last apple to {peer.label} with open hands.")

    world.say(
        f"{peer.label} looked surprised, then grateful."
    )
    world.say(
        f"At once, the air in {place_phrase} felt softer."
    )

    world.para()
    world.say(
        f"By dusk, the little peeve was no longer a thorn in {hero.pronoun('possessive')} mind."
    )
    world.say(
        f"{moral_truth.capitalize()}, and that was the truer treasure in the end."
    )

    world.mood = "soft"
    world.facts["resolved"] = True
    world.facts["ending_image"] = f"{hero.label} and {peer.label} in {place_phrase} at dusk"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a small child about a "{f["peeve_label"]}" that is solved with {f["moral_key"]}.',
        f"Tell a gentle story set in {f['place_phrase']} where {f['hero'].label} learns that {f['moral_truth']}.",
        f"Write a short fairy tale about {f['hero'].label} and {f['peer'].label} that includes the word \"peeve\" and ends kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    peer: Entity = f["peer"]
    return [
        QAItem(
            question=f"Who had the small peeve in the story?",
            answer=f"{hero.label} had the small peeve. It made {hero.pronoun('object')} feel uneasy at first.",
        ),
        QAItem(
            question=f"What did {hero.label} choose instead of complaining?",
            answer=f"{hero.label} chose {f['moral_verb']} instead of complaining.",
        ),
        QAItem(
            question=f"What happened to the mood in {f['place_phrase']} after that choice?",
            answer=f"The mood grew softer, and {peer.label} became grateful.",
        ),
        QAItem(
            question=f"What lesson ended the fairy tale?",
            answer=f"{f['moral_truth'].capitalize()} was the lesson that closed the tale.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    qa = [
        QAItem(
            question="What is a peeve?",
            answer="A peeve is a small annoyance that bothers someone more than it probably should.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle actions that help or comfort someone else.",
        ),
        QAItem(
            question="Why do fairy tales often end with a lesson?",
            answer="Fairy tales often end with a lesson so children can remember the good choice that solved the problem.",
        ),
    ]
    if f["moral_key"] == "honesty":
        qa.append(QAItem(
            question="Why is honesty important?",
            answer="Honesty helps people trust each other, because the truth keeps a friendship strong.",
        ))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


@dataclass
class StoryWorldModel:
    world: World

    def trace(self) -> str:
        lines = [f"place={self.world.place_phrase}", f"mood={self.world.mood}"]
        for e in self.world.entities.values():
            lines.append(f"{e.id}:{e.type}:{e.label}")
        return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, (phrase, _) in PLACES.items():
        lines.append(asp.fact("place", pid))
        for token in phrase.split():
            pass
    for key in MORAL_VALUES:
        lines.append(asp.fact("moral", key))
    for key in PEEVES:
        lines.append(asp.fact("peeve", key))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, V, H, C) :- place(P), peeve(V), moral(C), hero_kind(H), peer_kind(H), H != C.
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (p, v, h, c)
        for p in PLACES
        for v in PEEVES
        for h in ACTORS
        for c in ACTORS
        if h != c
    }
    clingo_set = set(asp_valid())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


GIRL_NAMES = ACTORS["girl"]["names"]
BOY_NAMES = ACTORS["boy"]["names"]
OTHER_NAMES = {
    "fox": ACTORS["fox"]["names"],
    "mouse": ACTORS["mouse"]["names"],
    "owl": ACTORS["owl"]["names"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale moral-value storyworld about a small peeve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-kind", choices=ACTORS)
    ap.add_argument("--peer-kind", choices=ACTORS)
    ap.add_argument("--peeve", choices=PEEVES)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--hero-name")
    ap.add_argument("--peer-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero_kind = args.hero_kind or rng.choice(list(ACTORS))
    peer_kind = args.peer_kind or rng.choice([k for k in ACTORS if k != hero_kind])
    peeve = args.peeve or rng.choice(list(PEEVES))
    moral = args.moral or rng.choice(list(MORAL_VALUES))

    hero_name = args.hero_name or rng.choice(ACTORS[hero_kind]["names"])
    peer_pool = ACTORS[peer_kind]["names"]
    peer_name = args.peer_name or rng.choice(peer_pool)
    if hero_name == peer_name and hero_kind == peer_kind:
        peer_name = rng.choice([n for n in peer_pool if n != hero_name])

    return StoryParams(
        place=place,
        hero_kind=hero_kind,
        hero_name=hero_name,
        peer_kind=peer_kind,
        peer_name=peer_name,
        peeve=peeve,
        moral=moral,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=StoryWorldModel(world),
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="wood", hero_kind="girl", hero_name="Mina", peer_kind="fox", peer_name="Fenn", peeve="teasing", moral="kindness"),
    StoryParams(place="village", hero_kind="boy", hero_name="Robin", peer_kind="mouse", peer_name="Midge", peeve="noise", moral="patience"),
    StoryParams(place="cottage", hero_kind="owl", hero_name="Wren", peer_kind="girl", peer_name="Lina", peeve="crumbs", moral="sharing"),
    StoryParams(place="castle", hero_kind="boy", hero_name="Theo", peer_kind="owl", peer_name="Orin", peeve="waiting", moral="honesty"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_valid()
        print(f"{len(items)} compatible stories:")
        for item in items:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} ({p.peeve} / {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
