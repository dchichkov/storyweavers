#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/railing_boob_bottom_bravery_tall_tale.py
=======================================================================

A tiny tall-tale storyworld about a brave child, a high railing, one foolish
boob of a mistake, and a sore bottom that learns a sensible lesson.

Seed words:
- railing
- boob
- bottom

Feature:
- Bravery

Style:
- Tall Tale

The world is deliberately small and state-driven: a child climbs a barn loft,
ignores a safe warning, makes one silly boob of a mistake, slides down to an
embarrassed bottom, then chooses a braver and wiser act on the next try.
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
BRAVERY_MIN = 3.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    height: str
    landing: str
    features: set[str] = field(default_factory=set)
    safe: bool = True


@dataclass
class Dare:
    id: str
    label: str
    verb: str
    motion: str
    risk: str
    funny: str
    land_on: str
    requires: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    power: int
    sense: int
    text: str
    fail: str
    qa_text: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("wobble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["alarm"] += 1
        out.append("__wobble__")
    return out


CAUSAL_RULES = [Rule("wobble", "motion", _r_wobble)]


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
        for s in produced:
            world.say(s)
    return produced


def tall_style_opening(hero: Entity, place: Place) -> str:
    return (
        f"{hero.id} was a little tall-tale kid with a brave heart and a bigger grin. "
        f"One bright day {hero.pronoun()} climbed up to {place.label}, where the {place.height} "
        f"looked as wide as a wagon road and the {place.landing} waited below."
    )


def predict_fall(world: World, dare: Dare) -> dict:
    sim = world.copy()
    _do_dare(sim, sim.get("hero"), dare, narrate=False)
    bottom = sim.get("hero").meters["bottom"]
    return {"bumped": bottom >= THRESHOLD, "wobble": sim.get("hero").meters["wobble"]}


def _do_dare(world: World, hero: Entity, dare: Dare, narrate: bool = True) -> None:
    hero.meters["wobble"] += 1
    hero.meters["brushed"] += 1
    hero.memes["boldness"] += 1
    propagate(world, narrate=narrate)


def warn(world: World, companion: Entity, hero: Entity, dare: Dare, place: Place) -> None:
    pred = predict_fall(world, dare)
    world.facts["predicted_bump"] = pred["bumped"]
    world.say(
        f'{companion.id} pointed at the {place.label} and said, "Easy now. One careless boob '
        f'can send a fellow right to the bottom."'
    )


def brag(world: World, hero: Entity, dare: Dare) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'{hero.id} laughed like a barn-cat in a thunderstorm. "{dare.label}? I can do that, '
        f'and I can do it with one hand on the railing!"'
    )


def slip(world: World, hero: Entity, dare: Dare, place: Place) -> None:
    hero.meters["wobble"] += 1
    hero.meters["bottom"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f"That was the boob of it. {hero.id} leaned too far on the railing, the boots skidded, "
        f"and down {hero.pronoun()} went to the bottom with a soft thump."
    )
    world.say(
        f"The dust puffed up like a gray little cloud, and even the {place.landing} seemed to blink."
    )


def rescue(world: World, helper: Entity, hero: Entity, response: Response, place: Place) -> None:
    body = response.text
    hero.meters["bottom"] = 0.0
    hero.meters["wobble"] = 0.0
    hero.memes["fear"] += 0.5
    world.say(
        f"{helper.id} came over in a hurry and {body}."
    )
    world.say(
        f"The rough tumble was over, and the {place.label} stood quiet again."
    )


def lesson(world: World, helper: Entity, hero: Entity, dare: Dare) -> None:
    hero.memes["lesson"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f'"A brave heart is good," {helper.id} said, "but a brave heart that thinks first is better."'
    )
    world.say(
        f'{hero.id} nodded, rubbed {hero.pronoun("possessive")} sore bottom, and promised not to make '
        f'one more boob with the railing.'
    )


def second_try(world: World, hero: Entity, companion: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"The next try was a different sort of tall tale. {hero.id} kept one hand on the railing, "
        f"stepped careful as a cat, and came down laughing instead of falling."
    )
    world.say(
        f"{companion.id} grinned, and together they went on with their day as proud as parade drummers."
    )


def tell(place: Place, dare: Dare, response: Response,
         hero_name: str = "Milo", hero_gender: str = "boy",
         companion_name: str = "June", companion_gender: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    helper = world.add(Entity(id="Grandpa", kind="character", type="man", role="helper", label="Grandpa"))
    railing = world.add(Entity(id="railing", type="thing", label="railing"))
    bottom = world.add(Entity(id="bottom", type="thing", label="bottom"))
    world.add(Entity(id="place", type="thing", label=place.label))

    hero.memes["bravery"] = 4.0
    companion.memes["caution"] = 3.0
    world.facts["railing"] = railing.id
    world.facts["bottom"] = bottom.id

    world.say(tall_style_opening(hero, place))
    world.say(
        f"{hero.id} and {companion.id} had turned the place into a little frontier of daring. "
        f"{hero.id} wanted to {dare.verb} because {dare.funny}."
    )
    world.para()
    warn(world, companion, hero, dare, place)
    brag(world, hero, dare)
    world.say(
        f"{hero.id} reached for the railing and tried to {dare.motion}, but the boards answered with a wobbly creak."
    )
    slip(world, hero, dare, place)
    world.para()
    rescue(world, helper, hero, response, place)
    lesson(world, helper, hero, dare)
    world.para()
    second_try(world, hero, companion, place)

    world.facts.update(
        hero=hero,
        companion=companion,
        helper=helper,
        place=place,
        dare=dare,
        response=response,
        fell=hero.meters["bottom"] >= THRESHOLD,
        lessoned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


PLACES = {
    "barn_loft": Place(
        id="barn_loft",
        label="the barn loft",
        height="loft wall",
        landing="hay-bottom",
        features={"railing", "hay"},
        safe=True,
    ),
    "porch": Place(
        id="porch",
        label="the front porch",
        height="porch rail",
        landing="bottom step",
        features={"railing", "steps"},
        safe=True,
    ),
}

DARES = {
    "climb": Dare(
        id="climb",
        label="climb the high railing",
        verb="test the high railing",
        motion="climb over the railing",
        risk="a tumble to the bottom",
        funny="the view from up there looked as grand as a king's hill",
        land_on="the bottom",
        requires={"railing"},
    ),
    "balance": Dare(
        id="balance",
        label="balance on the railing",
        verb="balance on the railing",
        motion="balance on the railing",
        risk="a slip to the bottom",
        funny="the railing looked like a skinny fence line made for daredevils",
        land_on="the bottom",
        requires={"railing"},
    ),
}

RESPONSES = {
    "catch": Response(
        id="catch",
        power=2,
        sense=3,
        text="caught {hero} by the sleeve before the bump grew worse",
        fail="tried to catch {hero}, but the tumble had already kissed the bottom",
        qa_text="caught the child by the sleeve before the bump grew worse",
    ),
    "lift": Response(
        id="lift",
        power=3,
        sense=3,
        text="helped {hero} up, dusted off the boots, and checked for scrapes",
        fail="helped {hero} up, but the tumble had already done its work",
        qa_text="helped the child up and dusted off the boots",
    ),
}


GIRL_NAMES = ["June", "Mara", "Lily", "Nora", "Mina"]
BOY_NAMES = ["Milo", "Otis", "Bram", "Theo", "Finn"]
TRAITS = ["brave", "quick", "reckless", "bright", "cheerful"]


@dataclass
class StoryParams:
    place: str
    dare: str
    response: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, d) for p in PLACES for d in DARES if "railing" in PLACES[p].features and "railing" in DARES[d].requires]


def explain_rejection(place: Place, dare: Dare) -> str:
    if "railing" not in place.features or "railing" not in dare.requires:
        return "(No story: this tale needs a railing under the brave feet, or there is no tall-tale tumble to tell.)"
    return "(No story: this combination is not sturdy enough for a brave tall-tale.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is too ordinary for this tall-tale world, sense={r.sense}.)"


ASP_RULES = r"""
valid(P,D) :- place(P), dare(D), has_railing(P), needs_railing(D).
brave(H) :- hero(H), bravery(H,B), B >= bravery_min.
fell(H) :- brave(H), attempt(H), wobble(H).
lesson(H) :- fell(H), helper(Hl), helper_ready(Hl).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "railing" in p.features:
            lines.append(asp.fact("has_railing", pid))
    for did, d in DARES.items():
        lines.append(asp.fact("dare", did))
        if "railing" in d.requires:
            lines.append(asp.fact("needs_railing", did))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("bravery_min", int(BRAVERY_MIN)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        if sample.story.strip():
            print("OK: generate smoke test produced a story.")
        else:
            rc = 1
            print("MISMATCH: empty story from smoke test.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate smoke test crashed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about railing bravery and a bottom bump.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--dare", choices=DARES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if args.dare and args.place:
        if (args.place, args.dare) not in valid_combos():
            raise StoryError(explain_rejection(PLACES[args.place], DARES[args.dare]))
    place = args.place or rng.choice(sorted(PLACES))
    dare = args.dare or rng.choice(sorted(DARES))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    companion_pool = BOY_NAMES if companion_gender == "boy" else GIRL_NAMES
    hero = args.hero or rng.choice([n for n in hero_pool if n != args.companion])
    companion = args.companion or rng.choice([n for n in companion_pool if n != hero])
    return StoryParams(
        place=place,
        dare=dare,
        response=response,
        hero=hero,
        hero_gender=hero_gender,
        companion=companion,
        companion_gender=companion_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a 3-to-5-year-old that includes the words "railing", "boob", and "bottom".',
        f"Tell a brave story where {f['hero'].id} learns not to make a silly boob with the railing and ends up safe at the bottom of the story.",
        f"Write a story with a giant-hearted helper, a railing, and a bottom bump, where bravery turns into wisdom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    helper = f["helper"]
    place = f["place"]
    lines = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, {companion.id}, and {helper.id}, with {hero.id} at the center of the tall-tale trouble.",
        ),
        QAItem(
            question="What did the child do near the railing?",
            answer=f"{hero.id} tried to balance on the railing and make a brave-looking move. That choice led to a silly boob and then a bump to the bottom.",
        ),
        QAItem(
            question="Who helped after the tumble?",
            answer=f"{helper.id} helped right away. {helper.id} steadied {hero.id}, checked for scrapes, and turned the mishap into a safer lesson.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} using the railing carefully and coming down safely. The bottom bump became a lesson instead of the ending.",
        ),
    ]
    if f.get("fell"):
        lines.append(
            QAItem(
                question=f"Why did {hero.id} end up at the bottom?",
                answer=(
                    f"{hero.id} leaned too far on the railing and made one silly boob of a mistake. "
                    f"The body turned wobbly, the feet slipped, and the child landed on the bottom with a thump."
                ),
            )
        )
    if f.get("lessoned"):
        lines.append(
            QAItem(
                question=f"What did bravery mean in this story?",
                answer=(
                    f"Bravery meant trying again after the tumble, but doing it the smart way. "
                    f"{hero.id} kept the brave heart and added careful feet."
                ),
            )
        )
    return lines


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a railing?",
            answer="A railing is a support bar people hold onto to keep from slipping off a high place.",
        ),
        QAItem(
            question="What does the word bravery mean?",
            answer="Bravery means being willing to do something hard or scary. A brave person can still be careful.",
        ),
        QAItem(
            question="What is a bottom?",
            answer="A bottom is the lower part of something, or the place you land when you sit down or fall down.",
        ),
        QAItem(
            question="What is a boob as a word?",
            answer="In a tall-tale story, a boob can mean a silly mistake. It is the kind of funny blunder that makes trouble before it makes sense.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="barn_loft", dare="climb", response="catch", hero="Milo", hero_gender="boy", companion="June", companion_gender="girl"),
    StoryParams(place="porch", dare="balance", response="lift", hero="Nora", hero_gender="girl", companion="Bram", companion_gender="boy"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.dare not in DARES or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    world = tell(PLACES[params.place], DARES[params.dare], RESPONSES[params.response],
                 hero_name=params.hero, hero_gender=params.hero_gender,
                 companion_name=params.companion, companion_gender=params.companion_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, d in combos:
            print(f"  {p} {d}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
