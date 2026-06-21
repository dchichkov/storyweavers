#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/silica_moral_value_twist_fairy_tale.py
======================================================================

A tiny fairy-tale storyworld about a child, a glittering silica discovery, a
moral choice, and a twist ending that changes what the shine means.

Premise
-------
A child finds a bright white patch of silica near a fairy ring and thinks it is
a treasure. The child wants to keep it, but a wise helper explains that the
sparkling sand can help make glass, mend a lamp, or save a window for the
village.

Moral value
-----------
The story rewards sharing, honesty, and patient help. Hoarding the silica or
using it carelessly causes trouble; offering it to repair the village's window
or lantern creates a warm ending.

Twist
-----
The silica is not treasure to keep. It is the very thing the village needed to
restore a clear lamp-glass or chapel window, so the "pretty stone" becomes a
gift to everyone.

This file follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a forward-chained simulation
- a Python reasonableness gate
- an inline ASP twin
- three separate QA sets
- --verify smoke-tests a normal story generation path
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
SILICA_SHINE = 1.0
MORAL_GOOD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    glitter: bool = False
    fragile: bool = False
    helpful: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    scene: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ShinyThing:
    id: str
    label: str
    phrase: str
    use: str
    moral: str
    glitter: bool = True
    fragile: bool = False
    helpful: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Offer:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    if world.get("lantern").meters["broken"] < THRESHOLD:
        return out
    sig = ("mend", "lantern")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("lantern").meters["glow"] += 1
    world.get("child").memes["hope"] += 1
    out.append("__mend__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.get("silica").meters["given"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["pride"] += 1
    world.get("helper").memes["joy"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [
    Rule("mend", "physical", _r_mend),
    Rule("share", "moral", _r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(place: Place, shiny: ShinyThing, offer: Offer) -> bool:
    return place.id in PLACES and shiny.id in SHINIES and offer.id in OFFERS


def is_reasonable_story(place: Place, shiny: ShinyThing) -> bool:
    return place.id in {"field", "riverbank", "cottage"} and shiny.id == "silica"


def predict_moral(world: World) -> dict:
    sim = world.copy()
    sim.get("silica").meters["given"] += 1
    propagate(sim, narrate=False)
    return {
        "mended": sim.get("lantern").meters["glow"] >= THRESHOLD,
        "hope": sim.get("child").memes["hope"],
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Once in a small fairy-tale morning, {child.id} wandered to {place.name}. "
        f"{place.scene}"
    )


def discover(world: World, child: Entity, shiny: ShinyThing, place: Place) -> None:
    world.say(
        f"By the roots of an old tree, {child.id} saw a bright white patch that "
        f"looked like treasure. It was {shiny.phrase}, and it glittered like "
        f"powdered moonlight."
    )
    child.meters["carried"] += 1
    child.memes["greed"] += 1


def warn(world: World, helper: Entity, child: Entity, shiny: ShinyThing) -> None:
    helper.memes["wisdom"] += 1
    pred = predict_moral(world)
    world.facts["predicted_mended"] = pred["mended"]
    world.say(
        f'{helper.id} touched the ground with a twig and smiled softly. '
        f'"That is not just a pretty stone," {helper.pronoun()} said. '
        f'"It is silica. It can help make clear glass, and clear glass can mend '
        f'a broken lamp or window."'
    )


def choose(world: World, child: Entity, helper: Entity, shiny: ShinyThing, good: bool) -> None:
    if good:
        child.memes["kindness"] += 1
        world.say(
            f"{child.id} blinked, then nodded. \"If it can help everyone, I should "
            f"share it,\" {child.pronoun()} said."
        )
    else:
        child.memes["greed"] += 1
        world.say(
            f"{child.id} hugged the shining silica close. \"I found it first,\" "
            f"{child.pronoun()} muttered, and kept it hidden in {child.pronoun('possessive')} pouch."
        )


def twist(world: World, child: Entity, helper: Entity, shiny: ShinyThing, place: Place) -> None:
    world.say(
        f"Then the twist came. The village lantern by the lane had lost its clear "
        f"glass in the wind, and the broken piece was waiting for exactly this kind "
        f"of sand."
    )
    world.say(
        f"The silica was not a jewel at all. It was the missing part of the village's "
        f"repair, and the child had found it at just the right time."
    )


def mend_and_end(world: World, child: Entity, helper: Entity, shiny: ShinyThing) -> None:
    world.get("silica").meters["given"] += 1
    world.get("lantern").meters["broken"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{child.id} carried the silica to {helper.id}, and together they brought it "
        f"to the little workshop. Soon the lantern was mended, and a warm golden light "
        f"bloomed in the window."
    )
    world.say(
        f"{helper.id} laughed, and {child.id} felt lighter than any bag of treasure. "
        f"The sparkle that had looked selfish became a shared glow for the whole lane."
    )


def moral_lesson(world: World, child: Entity, helper: Entity) -> None:
    child.memes["greed"] = 0.0
    child.memes["kindness"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{helper.id} bowed a little and said, \"A true treasure is what you can help "
        f"others with.\" {child.id} nodded, because the brightest thing in the tale "
        f"wasn't the silica itself, but the good that came from giving it away."
    )


PLACES = {
    "field": Place(
        id="field",
        name="the sunlit field",
        scene="The grass was soft, the daisies nodded, and a fairy ring shimmered near the fence.",
        mood="bright",
        affords={"find"},
    ),
    "riverbank": Place(
        id="riverbank",
        name="the riverbank",
        scene="The water sang against the stones, and silver reeds whispered in the breeze.",
        mood="gentle",
        affords={"find"},
    ),
    "cottage": Place(
        id="cottage",
        name="the old cottage yard",
        scene="The cottage windows flashed like sleepy eyes, and the path was edged with thyme.",
        mood="warm",
        affords={"find"},
    ),
}

SHINIES = {
    "silica": ShinyThing(
        id="silica",
        label="silica",
        phrase="a glittering patch of silica sand",
        use="make clear glass",
        moral="share what can help the village",
        glitter=True,
        fragile=False,
        helpful=True,
        tags={"silica", "glass", "moral"},
    ),
    "pearl": ShinyThing(
        id="pearl",
        label="pearl",
        phrase="a round pearl",
        use="keep as a pretty bead",
        moral="be careful with delicate things",
        glitter=True,
        fragile=True,
        helpful=False,
        tags={"pearl"},
    ),
}

OFFERS = {
    "share": Offer(
        id="share",
        sense=3,
        power=3,
        text="brought the silica to the workshop and helped the glassmaker mend the lantern",
        fail="tried to hide the silica, but the village lantern stayed broken",
        tags={"moral", "help"},
    ),
    "hoard": Offer(
        id="hoard",
        sense=1,
        power=1,
        text="kept the silica in a pouch and admired it alone",
        fail="kept the silica hidden, and the workshop had nothing to mend the lantern",
        tags={"selfish"},
    ),
    "gift": Offer(
        id="gift",
        sense=3,
        power=2,
        text="gave the silica to the helper at once",
        fail="wanted to give it away, but changed their mind too late",
        tags={"moral", "help"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Asha", "Iris", "Nora"]
BOY_NAMES = ["Owen", "Bram", "Eli", "Rafe", "Noel", "Jasper"]


@dataclass
class StoryParams:
    place: str
    shiny: str
    offer: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="field", shiny="silica", offer="share", child_name="Mina", child_gender="girl", helper_name="Grandma", helper_gender="woman"),
    StoryParams(place="riverbank", shiny="silica", offer="gift", child_name="Owen", child_gender="boy", helper_name="Moss", helper_gender="man"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for shiny in SHINIES:
            for offer in OFFERS:
                if reasonableness_gate(PLACES[place], SHINIES[shiny], OFFERS[offer]) and shiny == "silica":
                    combos.append((place, shiny, offer))
    return combos


def explain_rejection(place: Place, shiny: ShinyThing) -> str:
    if shiny.id != "silica":
        return "(No story: this tale is built around silica, not a different shiny thing.)"
    return "(No story: this place cannot support the silica fairy-tale twist.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale silica storyworld with a moral twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shiny", choices=SHINIES)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.shiny and args.shiny != "silica":
        raise StoryError("(No story: the seed world is specifically about silica.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.shiny is None or c[1] == args.shiny)
              and (args.offer is None or c[2] == args.offer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, shiny, offer = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(["the old miller", "the wise grandmother", "the glassmaker"])
    helper_gender = "woman" if "grandmother" in helper_name or "glassmaker" in helper_name else "man"
    return StoryParams(place=place, shiny=shiny, offer=offer, child_name=name, child_gender=gender, helper_name=helper_name, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    shiny = SHINIES[params.shiny]
    offer = OFFERS[params.offer]

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    silica = world.add(Entity(id="silica", kind="thing", type="thing", label="silica", glitter=True, helpful=True))
    lantern = world.add(Entity(id="lantern", kind="thing", type="thing", label="lantern", fragile=True))
    lantern.meters["broken"] = 1.0
    world.facts.update(place=place, shiny=shiny, offer=offer, child=child, helper=helper, silica=silica, lantern=lantern)

    introduce(world, child, place)
    discover(world, child, shiny, place)
    world.para()
    warn(world, helper, child, shiny)
    good = offer.id in {"share", "gift"}
    choose(world, child, helper, shiny, good)
    world.para()
    twist(world, child, helper, shiny, place)
    mend_and_end(world, child, helper, shiny)
    moral_lesson(world, child, helper)
    world.facts["outcome"] = "mended"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, shiny, offer = f["place"], f["shiny"], f["offer"]
    return [
        f'Write a fairy-tale story for a young child that includes the word "silica" and ends with a moral lesson.',
        f"Tell a story where {f['child'].id} finds silica at {place.name}, thinks it is treasure, and learns to share it for the good of the village.",
        f"Write a magical story with a twist: the glittering silica is not a keepsake but something the village needs to mend its lantern.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, place, shiny, offer = f["child"], f["helper"], f["place"], f["shiny"], f["offer"]
    return [
        QAItem(
            question="What did the child find?",
            answer=f"{child.id} found silica, which looked like a tiny treasure because it glittered like moonlight."
        ),
        QAItem(
            question="Why did the helper want the child to share it?",
            answer=f"The helper knew silica could be used to make clear glass for repairs. That meant it could help the village, not just sit in a pouch."
        ),
        QAItem(
            question="What was the twist?",
            answer="The shiny thing was not a jewel to keep. It was the missing material needed to mend the village lantern, so the child's discovery became a gift."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with a warm lantern glow and a moral lesson about sharing. The child learned that the best treasure is the good it can do for others."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is silica?",
            answer="Silica is a kind of sand or mineral used to make glass. People use it to create clear, strong glass for windows and lamps."
        ),
        QAItem(
            question="Why is glass useful in a fairy tale village?",
            answer="Glass can make windows and lantern covers clear, so light can shine safely. That is why a story might treat silica as a helpful treasure."
        ),
        QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson a story teaches. It often reminds readers to be kind, honest, or generous."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.glitter:
            bits.append("glitter")
        if e.fragile:
            bits.append("fragile")
        if e.helpful:
            bits.append("helpful")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,O) :- place(P), shiny(S), offer(O), silica_story(S), reasonable(P,S).
moral_twist(S) :- silica_story(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SHINIES:
        lines.append(asp.fact("shiny", sid))
        if sid == "silica":
            lines.append(asp.fact("silica_story", sid))
    for oid in OFFERS:
        lines.append(asp.fact("offer", oid))
    for pid in PLACES:
        lines.append(asp.fact("reasonable", pid, "silica"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: story generation smoke test failed: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.shiny not in SHINIES:
        raise StoryError(f"Unknown shiny thing: {params.shiny}")
    if params.offer not in OFFERS:
        raise StoryError(f"Unknown offer: {params.offer}")

    world = tell(params)
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
        print(asp_program(show="#show valid/3.\n#show moral_twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program(show="#show valid/3."))
        print("ASP valid combos:", asp_valid_combos())
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
